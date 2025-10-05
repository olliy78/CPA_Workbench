#!/usr/bin/env python3

# # Copyright (c) 2025 by olliy78
# SPDX-License-Identifier: MIT
"""
Projektname: CPA-Workbench
Autor: olliy78

Dieses Skript steuert den gesamten Konfigurations- und Build-Workflow für das CPA-Workbench-Projekt.
Es führt den Nutzer durch die Konfigurationsmenüs (Systemtyp, Hardware, Build-Format), synchronisiert Konfigurationswerte zwischen .config und BIOS und startet den Build-Prozess gemäß der gewählten Optionen.

Aufbau:
- merge_config: Mischen von Konfigurationswerten mit relevanten Präfixen
- run_menu: Startet das interaktive Konfigurationsmenü
- run_patch_bios_mac: Synchronisiert BIOS-Werte mit externer Datei
- run_build: Führt den Build-Prozess aus
- generate_kconfig_variant: Erstellt Kconfig.variante dynamisch
- main: Ablaufsteuerung des gesamten Workflows

Verwendung:
Das Skript wird als Hauptskript für die Konfiguration und den Build des CPA-Workbench-Projekts verwendet. Es kann direkt über die Kommandozeile ausgeführt werden:
    python cpa_menuconfig.py
Das Skript führt alle notwendigen Schritte zur Konfiguration und zum Build in der richtigen Reihenfolge aus.
"""

import subprocess
import sys
import os
import shutil
import glob
import re

# Hilfsfunktion: Lese alle Zeilen mit bestimmtem Präfix aus einer Datei in ein Dict
def read_config_section(config_path, prefix):
    section = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^(# )?(' + re.escape(prefix) + r'[A-Za-z0-9_]+)', line)
                if m:
                    key = m.group(2)
                    section[key] = line.rstrip("\n")
    return section

# Hilfsfunktion: Schreibe mehrere Konfig-Dicts in Reihenfolge in die Datei (Datei wird geleert)
def write_config_sections(config_path, *sections):
    with open(config_path, "w", encoding="utf-8") as f:
        for section in sections:
            for line in section.values():
                f.write(line + "\n")

# Hilfsfunktion: Ermittelt die gewählte Systemvariante aus dem variant_section-Dict
def get_selected_variant(variant_section):
    """Gibt die gewählte Systemvariante (ohne Prefix) zurück oder None."""
    for key, val in variant_section.items():
        if key.startswith("CONFIG_VARIANT_") and val.endswith("=y"):
            return key[len("CONFIG_VARIANT_"):]
    return None

## Merge-Logik: Nach jedem Menü die neuen Werte in die bestehende .config übernehmen
# Die Funktion erhält die Liste der relevanten Präfixe beim Aufruf als Argument (z.B. ["CONFIG_SYSTEM_", "CONFIG_DEV_", ...]).
# Welche Präfixe relevant sind, entscheidet der aufrufende Code – die Funktion selbst ist davon unabhängig und übernimmt nur die Keys,
# die mit einem der übergebenen Präfixe beginnen.
def merge_config(old_config, new_config, relevant_prefixes):
    """
    Mische nur die Werte mit den relevanten Prefixen aus new_config in old_config.
    Die relevanten Präfixe werden beim Aufruf als drittes Argument übergeben und bestimmen, welche Konfigurationsoptionen übernommen werden.
    """
    import re
    def parse_config(path):
        vals = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    m = re.match(r'^(# )?(CONFIG_[A-Za-z0-9_\-]+)', line)
                    if m:
                        key = m.group(2)
                        vals[key] = line.rstrip("\n")
        return vals
    old_vals = parse_config(old_config)
    new_vals = parse_config(new_config)
    # Nur relevante Keys übernehmen, alle anderen entfernen
    merged = {}
    for key, val in new_vals.items():
        if any(key.startswith(prefix) for prefix in relevant_prefixes):
            merged[key] = val
    # Schreibe gemergte .config (nur relevante Keys, Reihenfolge wie new_config)
    with open(old_config, "w") as f:
        for key in merged:
            f.write(merged[key] + "\n")

## Startet das externe menuconfig für eine bestimmte Kconfig-Datei und speichert die Auswahl in config_file.
# Ablauf:
# - Setzt die Umgebungsvariable KCONFIG_CONFIG auf die gewünschte Konfigurationsdatei.
# - Ruft das Python-Skript menuconfig.py mit der Kconfig-Datei als Argument auf.
# - Das Menü läuft interaktiv und schreibt die Auswahl in die angegebene Datei.
# - Bei Fehler wird eine Meldung ausgegeben und das Programm beendet.
def run_menu(kconfig_file, config_file):
    """
    Starte menuconfig für eine bestimmte Kconfig-Datei.
    Setzt die Umgebung und ruft das externe Menü auf, das die Konfiguration interaktiv ermöglicht.
    """
    try:
        env = os.environ.copy()
        env["KCONFIG_CONFIG"] = config_file
        subprocess.run([
            sys.executable, os.path.join("config", "menuconfig.py"), kconfig_file
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] menuconfig für {kconfig_file} fehlgeschlagen: {e}")
        sys.exit(1)

## Führt das externe Skript patch_mac.py aus, um Konfigurationswerte zu synchronisieren.
# Ablauf:
# - Ruft patch_mac.py mit <mode> <config> <systemvariante> auf.
# - Im Modus "extract" werden Werte aus bios.mac ausgelesen und in die Konfiguration geschrieben.
# - Im Modus "patch" werden Werte aus der Konfiguration zurück in bios.mac geschrieben.
# - Bei Fehler wird eine Meldung ausgegeben und das Programm beendet.
def run_patch_mac(config_file, system_variant, mode):
    """
    Führe patch_mac.py im Modus 'extract' oder 'patch' aus.
    Synchronisiert die Konfigurationswerte zwischen Datei und BIOS.
    """
    try:
        subprocess.run([
            sys.executable, os.path.join("config", "patch_mac.py"), mode, config_file, system_variant
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] patch_mac.py fehlgeschlagen: {e}")
        sys.exit(1)

## Diese Funktion erzeugt die Datei Kconfig.variante dynamisch neu.
# Ablauf:
# - Liest die vorhandene Kconfig.variante ein und sucht den choice-Block.
# - Ersetzt den choice-Block durch einen neuen Block, der alle Systemvarianten aus den src-Unterordnern auflistet.
# - Für jede Variante wird der Name und (falls vorhanden) der Inhalt der about.txt als Hilfetext übernommen.
# - So wird das Menü zur Systemauswahl automatisch an die vorhandenen Systemvarianten angepasst.
def generate_kconfig_variant(kconfig_path, src_dir):
    """Erzeuge Kconfig.variante dynamisch aus sich selbst und src-Unterordnern."""
    # Lese aktuelle Kconfig.variante ein
    with open(kconfig_path, "r") as f:
        lines = f.readlines()

    # Finde choice-Block
    choice_start = None
    choice_end = None
    for i, line in enumerate(lines):
        if line.strip().startswith("choice"):
            choice_start = i
        if line.strip() == "endchoice":
            choice_end = i
            break
    if choice_start is None or choice_end is None:
        raise RuntimeError("choice-Block in Kconfig.variante nicht gefunden!")

    # Systemvarianten aus src-Unterordnern
    variants = []
    for entry in sorted(glob.glob(os.path.join(src_dir, "*"))):
        if os.path.isdir(entry):
            name = os.path.basename(entry)
            about_path = os.path.join(entry, "about.txt")
            if os.path.isfile(about_path):
                with open(about_path, "r") as af:
                    helptext = af.read().strip()
            else:
                helptext = "keine Hilfe vorhanden, da keine about.txt im Ordner gefunden"
            variants.append((name, helptext))

    # Baue neuen choice-Block
    choice_lines = []
    choice_lines.append("choice\n")
    choice_lines.append("    prompt \"Systemvariante\"\n")
    if variants:
        choice_lines.append(f"    default VARIANT_{variants[0][0]}\n")
    choice_lines.append("    help\n")
    choice_lines.append("        Mit [?] kann zu jeder Systemvariante der Inhalt der about.txt Datei\n")
    choice_lines.append("        aus dem jeweiligen src Ordner angezeigt werden.\n")
    for name, helptext in variants:
        choice_lines.append(f"config VARIANT_{name}\n")
        choice_lines.append(f"    bool \"{name}\"\n")
        choice_lines.append("    help\n")
        for line in helptext.splitlines():
            choice_lines.append(f"        {line}\n")
    choice_lines.append("endchoice\n")

    # Überschreibe Kconfig.variante direkt
    with open(kconfig_path, "w") as f:
        f.writelines(lines[:choice_start])
        f.writelines(choice_lines)
        f.writelines(lines[choice_end+1:])

## Diese Funktion steuert den gesamten Konfigurations-Workflow für das CPA-Projekt.
# Ablauf:
# 1. Erstellt die Datei Kconfig.variante dynamisch aus den vorhandenen Systemvarianten.
# 2. Sichert die aktuelle .config als Backup.
# 3. Startet das erste Menü zur Auswahl des Systemtyps und übernimmt die Auswahl in die Konfiguration.
# 4. Ermittelt die gewählte Systemvariante und synchronisiert die BIOS-Konfigurationswerte (extract).
# 5. Startet das zweite Menü für Hardware und Laufwerke, übernimmt die Auswahl und patcht die BIOS-Konfiguration (patch).
# 6. Startet das dritte Menü für Build- und Diskettenformat, übernimmt die Auswahl.
# 7. Führt abschließend den Build-Prozess gemäß der Konfiguration aus.
# Kurz: main führt die Nutzer durch alle Konfigurationsmenüs, übernimmt und synchronisiert die Einstellungen und startet am Ende den Build.
def main():
    config_file = ".config"
    src_dir = "src"
    kconfig_path = os.path.join("config", "Kconfig.variante")

    # Erzeuge dynamische Kconfig.variante direkt aus sich selbst
    generate_kconfig_variant(kconfig_path, src_dir)


    # Menü 1: vor Systemtyp-Auswahl: Sichere VARIANT- und BUILD-Einträge, leere .config und schreibe nur diese zurück
    variant_section = read_config_section(config_file, "CONFIG_VARIANT_")
    build_section = read_config_section(config_file, "CONFIG_BUILD_")
    write_config_sections(config_file, variant_section, build_section)
    run_menu(kconfig_path, config_file)
    # Nach Menü 1: Sichere VARIANT-Einträge, leere .config und schreibe VARIANT und BUILD zurück
    variant_section = read_config_section(config_file, "CONFIG_VARIANT_")
    write_config_sections(config_file, variant_section, build_section)
    # Jetzt Systemvariante direkt aus variant_section bestimmen (Hilfsfunktion)
    system_variant = get_selected_variant(variant_section)
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus variant_section ermitteln!")
        sys.exit(1)

    # Vor Hardwaremenü: bios.mac parsen (extract)
    run_patch_mac(config_file, system_variant, "extract")

    # Menü 2: Systemmenü (Kconfig.system, systemspezifisch)
    run_menu(os.path.join("config", system_variant, "Kconfig.system"), config_file)
    # Nach Menü 2: Sichere SYSTEM-Parameter, schreibe .config neu mit VARIANT, SYSTEM, BUILD (VARIANT zuerst!)
    system_section = read_config_section(config_file, "CONFIG_SYSTEM_")
    write_config_sections(config_file, variant_section, system_section, build_section)

    # Jetzt Systemvariante direkt aus variant_section bestimmen (Hilfsfunktion)
    system_variant = get_selected_variant(variant_section)
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus variant_section ermitteln!")
        sys.exit(1)
    # Nach Hardwaremenü: bios.mac patchen (patch)
    run_patch_mac(config_file, system_variant, "patch")


    # Menü 3: Build-Ausgabeformat
    run_menu(os.path.join("config", "Kconfig.build"), config_file)
    # Nach Menü 3: Sichere BUILD-Parameter, schreibe .config neu mit VARIANT, SYSTEM, BUILD
    build_section = read_config_section(config_file, "CONFIG_BUILD_")
    write_config_sections(config_file, variant_section, system_section, build_section)

    # Build-Target aus CONFIG_BUILD_* bestimmen und explizit an run_build übergeben
    # Build-Target direkt aus build_section bestimmen
    # überprüfen, ob CLEAN gesetzt ist
    if build_section.get("CONFIG_BUILD_CLEAN") == "CONFIG_BUILD_CLEAN=y":
        cmd = ["make", "clean"]
        print(f"[DEBUG] Starte make clean")
        subprocess.run(cmd, check=True)

    build_target = None
    for key, val in build_section.items():
        if key.startswith("CONFIG_BUILD_TARGET_") and val.endswith("=y"):
            build_target = key[len("CONFIG_BUILD_TARGET_"):].lower()
            print(f"[INFO] Gewähltes Build-Target: {build_target}")
            break
    if build_target:
        cmd = ["make", "config", build_target]
        print(f"[DEBUG] Starte make config {build_target}")
        subprocess.run(cmd, check=False)
    else:
        print("[INFO] Kein Build-Target in .config gefunden. Build wird übersprungen.")

if __name__ == "__main__":
    main()
