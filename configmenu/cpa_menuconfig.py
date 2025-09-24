#!/usr/bin/env python3
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
- generate_kconfig_system: Erstellt Kconfig.system dynamisch
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

## Merge-Logik: Nach jedem Menü die neuen Werte in die bestehende .config übernehmen
# Die Funktion erhält die Liste der relevanten Präfixe beim Aufruf als Argument (z.B. ["CONFIG_SYSTEM_", "CONFIG_DEV_", ...]).
# Welche Präfixe relevant sind, entscheidet der aufrufende Code – die Funktion selbst ist davon unabhängig und übernimmt nur die Keys,
# die mit einem der übergebenen Präfixe beginnen.
def merge_config(old_config, new_config, relevant_prefixes):
    """
    Mische nur die Werte mit den relevanten Prefixen aus new_config in old_config.
    Die relevanten Präfixe werden beim Aufruf als drittes Argument übergeben und bestimmen, welche Konfigurationsoptionen übernommen werden.
    """
    def parse_config(path):
        vals = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("CONFIG_") or line.startswith("# CONFIG_"):
                        key = line.split()[1] if line.startswith("# ") else line.split("=")[0]
                        vals[key] = line.rstrip("\n")
        return vals
    old_vals = parse_config(old_config)
    new_vals = parse_config(new_config)
    # Überschreibe nur relevante Keys
    for key, val in new_vals.items():
        if any(key.startswith(prefix) for prefix in relevant_prefixes):
            old_vals[key] = val
    # Schreibe gemergte .config
    with open(old_config, "w") as f:
        for val in old_vals.values():
            f.write(val + "\n")
#!/usr/bin/env python3
"""
CPA Konfigurations-Workflow-Wrapper
- Menü 1: Systemtyp-Auswahl (Kconfig.system)
- Menü 2: Hardwarevariante & Diskettenlaufwerke (Kconfig.hardware)
- Menü 3: Build-Ausgabeformat (Kconfig.build)
- Nach jedem Schritt: ggf. patch_bios_mac.py und Build starten
"""

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
            sys.executable, os.path.join("configmenu", "menuconfig.py"), kconfig_file
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] menuconfig für {kconfig_file} fehlgeschlagen: {e}")
        sys.exit(1)

## Führt das externe Skript patch_bios_mac.py aus, um BIOS-Konfigurationswerte zu synchronisieren.
# Ablauf:
# - Ruft patch_bios_mac.py mit bios_mac_path, config_file und mode ("extract" oder "patch") auf.
# - Im Modus "extract" werden Werte aus bios.mac ausgelesen und in die Konfiguration geschrieben.
# - Im Modus "patch" werden Werte aus der Konfiguration zurück in bios.mac geschrieben.
# - Bei Fehler wird eine Meldung ausgegeben und das Programm beendet.
def run_patch_bios_mac(bios_mac_path, config_file, mode):
    """
    Führe patch_bios_mac.py im Modus 'extract' oder 'patch' aus.
    Synchronisiert die BIOS-Konfigurationswerte zwischen Datei und Konfiguration.
    """
    try:
        subprocess.run([
            sys.executable, os.path.join("configmenu", "patch_bios_mac.py"), bios_mac_path, config_file, mode
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] patch_bios_mac.py fehlgeschlagen: {e}")
        sys.exit(1)

## Diese Funktion steuert den Build-Prozess basierend auf der aktuellen Konfiguration (.config).
# Ablauf:
# - Liest die .config und ermittelt das gewählte Build-Target (z.B. OS, Diskettenformat).
# - Falls CONFIG_BUILD_CLEAN=y gesetzt ist, wird zuerst "make clean" ausgeführt.
# - Es darf nur ein Build-Target ausgewählt sein, sonst Abbruch mit Fehlermeldung.
# - Falls kein Target gewählt ist, wird der Build übersprungen.
# - Führt dann "make config <target>" aus, um das Projekt zu bauen.
# - Bei Fehlern im Build-Prozess wird eine Fehlermeldung ausgegeben und das Programm beendet.
def run_build(target):
    """Starte den Build-Prozess mit make <target>."""
    try:
        # Ermittle das Build-Target (nur eines erlaubt)
        build_targets = []
        clean_first = False
        config_file = ".config"
        if os.path.exists(config_file):
            with open(config_file) as f:
                for line in f:
                    if line.strip() == "CONFIG_BUILD_CLEAN=y":
                        clean_first = True
                    elif line.strip().startswith("CONFIG_BUILD_") and line.strip().endswith("=y") and not line.strip().startswith("CONFIG_BUILD_CLEAN"):
                        # z.B. CONFIG_BUILD_OS=y -> os
                        build_targets.append(line.strip()[len("CONFIG_BUILD_"):-2].lower())
        if len(build_targets) > 1:
            print("[FEHLER] Es darf nur EIN Build-Target ausgewählt werden!")
            sys.exit(1)
        if not build_targets:
            print("[INFO] Kein Build-Target ausgewählt. Es wird nichts gebaut.")
            return
        build_target = build_targets[0]
        if clean_first:
            print("[INFO] Führe vor dem Build: make clean aus...")
            subprocess.run(["make", "clean"], check=True)
        cmd = ["make", "config", build_target]
        print(f"[DEBUG] Starte Build mit: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] Build fehlgeschlagen: {e}")
        sys.exit(1)


## Diese Funktion erzeugt die Datei Kconfig.system dynamisch neu.
# Ablauf:
# - Liest die vorhandene Kconfig.system ein und sucht den choice-Block.
# - Ersetzt den choice-Block durch einen neuen Block, der alle Systemvarianten aus den src-Unterordnern auflistet.
# - Für jede Variante wird der Name und (falls vorhanden) der Inhalt der about.txt als Hilfetext übernommen.
# - So wird das Menü zur Systemauswahl automatisch an die vorhandenen Systemvarianten angepasst.
def generate_kconfig_system(kconfig_path, src_dir):
    """Erzeuge Kconfig.system dynamisch aus sich selbst und src-Unterordnern."""
    # Lese aktuelle Kconfig.system ein
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
        raise RuntimeError("choice-Block in Kconfig.system nicht gefunden!")

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
        choice_lines.append(f"    default SYSTEM_{variants[0][0]}\n")
    choice_lines.append("    help\n")
    choice_lines.append("        Mit [?] kann zu jeder Systemvariante der Inhalt der about.txt Datei\n")
    choice_lines.append("        aus dem jeweiligen src Ordner angezeigt werden.\n")
    for name, helptext in variants:
        choice_lines.append(f"config SYSTEM_{name}\n")
        choice_lines.append(f"    bool \"{name}\"\n")
        choice_lines.append("    help\n")
        for line in helptext.splitlines():
            choice_lines.append(f"        {line}\n")
    choice_lines.append("endchoice\n")

    # Überschreibe Kconfig.system direkt
    with open(kconfig_path, "w") as f:
        f.writelines(lines[:choice_start])
        f.writelines(choice_lines)
        f.writelines(lines[choice_end+1:])

## Diese Funktion steuert den gesamten Konfigurations-Workflow für das CPA-Projekt.
# Ablauf:
# 1. Erstellt die Datei Kconfig.system dynamisch aus den vorhandenen Systemvarianten.
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
    kconfig_path = os.path.join("configmenu", "Kconfig.system")

    # Erzeuge dynamische Kconfig.system direkt aus sich selbst
    generate_kconfig_system(kconfig_path, src_dir)

    # Backup der Startkonfiguration
    if os.path.exists(config_file):
        shutil.copyfile(config_file, config_file + ".bak")


    # Menü 1: Systemtyp-Auswahl
    run_menu(kconfig_path, config_file)
    # Nach Menü 1: Systemtyp-Optionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_SYSTEM_"])
        shutil.move(config_file+".old", config_file)

    # Systemvariante aus .config ermitteln
    system_variant = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                m = None
                if line.startswith("CONFIG_SYSTEM_") and line.strip().endswith("=y"):
                    m = line.strip().split("=")[0]
                if m:
                    # z.B. CONFIG_SYSTEM_pc_1715 -> pc_1715
                    system_variant = m[len("CONFIG_SYSTEM_"):]
                    break
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus .config ermitteln!")
        sys.exit(1)

    bios_mac_path = os.path.join("src", system_variant, "bios.mac")
    if not os.path.exists(bios_mac_path):
        print(f"[FEHLER] bios.mac nicht gefunden: {bios_mac_path}")
        sys.exit(1)

    # Vor Hardwaremenü: bios.mac parsen (extract)
    run_patch_bios_mac(bios_mac_path, config_file, "extract")

    # Menü 2: Hardwarevariante & Diskettenlaufwerke
    run_menu(os.path.join("configmenu", "Kconfig.hardware"), config_file)
    # Nach Menü 2: Hardware- und Laufwerksoptionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_DEV_", "CONFIG_CPUCLK_", "CONFIG_CPU_", "CONFIG_FDC_", "CONFIG_CRT_", "CONFIG_RAM_", "CONFIG_DRIVE_", "CONFIG_RAMDISK_"])
        shutil.move(config_file+".old", config_file)

    # Nach Hardwaremenü: bios.mac patchen
    # Systemvariante ggf. erneut aus .config ermitteln (falls geändert)
    system_variant = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                m = None
                if line.startswith("CONFIG_SYSTEM_") and line.strip().endswith("=y"):
                    m = line.strip().split("=")[0]
                if m:
                    system_variant = m[len("CONFIG_SYSTEM_" ):]
                    break
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus .config ermitteln!")
        sys.exit(1)
    bios_mac_path = os.path.join("src", system_variant, "bios.mac")
    if not os.path.exists(bios_mac_path):
        print(f"[FEHLER] bios.mac nicht gefunden: {bios_mac_path}")
        sys.exit(1)
    run_patch_bios_mac(bios_mac_path, config_file, "patch")


    # Menü 3: Build-Ausgabeformat
    run_menu(os.path.join("configmenu", "Kconfig.build"), config_file)
    # Nach Menü 3: Build- und Diskettenformat-Optionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_BUILD_", "CONFIG_DISKTYPE_"])
        shutil.move(config_file+".old", config_file)

    # Build nur über .config steuern, nicht explizit Target übergeben
    run_build(None)

if __name__ == "__main__":
    main()
