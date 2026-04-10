#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
patch_mac.py - Bidirektionaler Konfigurationspatcher für Z80-Assembler-Quellen

Dieses Skript synchronisiert die Konfiguration (.config im Kconfig-Format)
bidirektional mit den Z80-Assembler-Quelldateien (.mac):

  - Modus 'extract': Liest aktuelle Konfigurationswerte aus den .mac-Dateien
    und schreibt sie in die .config-Datei. Wird beim Variantenwechsel in der
    GUI aufgerufen, um die aktuellen Quellwerte zu erfassen.

  - Modus 'patch': Schreibt die Werte aus der .config-Datei in die .mac-Dateien
    zurück. Wird vor dem Build aufgerufen, um die Assembler-Quellen mit den
    gewählten Optionen zu aktualisieren.

Das Mapping zwischen Kconfig-Optionen und Assembler-Labels wird in den
Kconfig.system-Dateien der jeweiligen Systemvariante definiert. Jeder
konfigurierbare Parameter hat einen help-Block mit einer source=-Zeile:

    config SYSTEM_OPTION_1
        bool "Beschreibung"
        help
            source=bios.mac LABEL1=1 LABEL2=0

Unterstützte Parametertypen:
  - bool: EQU-Werte (0/1, mit Invertierung bei 'is not set')
  - string: DB-Strings (z.B. db 'text',0)
  - hexstring: EQU-Hex-Werte (z.B. 0E800h)

Die .mac-Dateien werden mit CRLF-Zeilenenden geschrieben, da der M80-Assembler
dies erwartet.

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)

Verwendung:
    python patch_mac.py <extract|patch> <config> <systemvariante> [loglevel=debug|loglevel=info]

Beispiel:
    python patch_mac.py extract .config bc_a5120 loglevel=debug
    python patch_mac.py patch .config bc_a5120 loglevel=info
"""
import sys
import os
import re

# ============================================================================
# Kconfig.system-Parser - Mapping zwischen Config-Optionen und .mac-Dateien
# ============================================================================

def parse_kconfig_system(path):
    """Alle konfigurierbaren Parameter aus Kconfig.system und deren Mapping extrahieren.

    Durchsucht die Kconfig.system nach 'config'-Blöcken mit zugehörigen
    help-Abschnitten, die eine 'source='-Zeile enthalten. Diese Zeilen
    definieren das Mapping: welche Datei (.mac), welche Labels und Werte.

    Args:
        path: Pfad zur Kconfig.system-Datei

    Returns:
        list: Liste von Dicts mit den Schlüsseln:
            - config_name: Name der Kconfig-Option (ohne CONFIG_-Präfix)
            - source: Ziel-.mac-Datei (z.B. 'bios.mac')
            - key_values: Dict der Label→Wert-Zuordnungen (z.B. {'RDTYP': '3'})
    """
    results = []
    if not os.path.exists(path):
        print(f"[WARN] Kconfig.system nicht gefunden: {path}")
        return results
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("config "):
            config_name = line.split()[1]
            # Suche nach dem zugehörigen help-Block mit source=-Zeile
            help_source = None
            key_values = {}
            j = i + 1
            while j < len(lines):
                l2 = lines[j].strip()
                if l2.startswith("help"):
                    # Suche nach source=... key=value ...
                    k = j + 1
                    while k < len(lines):
                        l3 = lines[k].strip()
                        if l3.startswith("source="):
                            # source=-Zeile parsen: 'source=datei.mac KEY1=val1 KEY2=val2'
                            source_line = l3[len("source="):].strip()
                            source_parts = source_line.split()
                            src = source_parts[0] if source_parts else None
                            kvs = {}
                            for part in source_parts[1:]:
                                if "=" in part:
                                    kv = part.split("=",1)
                                    kvs[kv[0]] = kv[1]
                            help_source = src
                            key_values = kvs
                            break
                        if l3 == "" or l3.startswith("bool") or l3.startswith("config "):
                            break
                        k += 1
                    break
                if l2.startswith("config "):
                    break
                j += 1
            if help_source and key_values:
                results.append({
                    "config_name": config_name,
                    "source": help_source,
                    "key_values": key_values
                })
        i += 1
    return results

# ============================================================================
# Extract-Modus - Werte aus .mac-Dateien in .config schreiben
# ============================================================================

def extract_mac_config(mac_path, config_path, param_mappings, loglevel="info"):
    """Konfigurationswerte aus einer .mac-Datei extrahieren und in .config schreiben.

    Für jeden Parameter wird geprüft, ob die im Mapping definierten Bedingungen
    in der .mac-Datei erfüllt sind. Es werden drei Parametertypen unterstützt:

    - bool: Prüft ob alle key=value-Paare in EQU-Zeilen übereinstimmen.
            Bei Übereinstimmung: CONFIG_KEY=y, sonst: # CONFIG_KEY is not set
    - string: Liest den DB-String-Wert aus der .mac-Datei.
    - hexstring: Liest den EQU-Hex-Wert aus der .mac-Datei.

    Die bestehende .config wird dabei erhalten - nur die betroffenen
    Schlüssel werden aktualisiert oder hinzugefügt.
    """
    if not os.path.exists(mac_path):
        print(f"[ERROR] *.mac Datei nicht gefunden: {mac_path}")
        sys.exit(1)
    with open(mac_path, encoding="utf-8") as f:
        mac_lines = f.readlines()

        if loglevel == "debug":
            print(f"[DEBUG] Extrahiere aus Datei: {mac_path}")
    # Bestehende .config-Werte laden (für Merge beim Zurückschreiben)
    config_vals = {}
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line)
                if m:
                    config_vals[m.group(2)] = line.rstrip('\n')

    # Neue Konfigurationswerte für jeden Parameter extrahieren
    new_config = {}
    for entry in param_mappings:
        if loglevel == "debug":
            print(f"[DEBUG] Extrahiere Element: {entry['config_name']} aus {mac_path}")
        key_values = entry["key_values"]
        config_name = entry["config_name"]
        config_key = f"CONFIG_{config_name}"
        # Hexstring-Optionen erkennen und EQU-Wert auslesen
        if any(v == "hexstring" for v in key_values.values()):
            for key, v in key_values.items():
                if v == "hexstring":
                    istwert = None
                    for line in mac_lines:
                        if line.lstrip().startswith(';'):
                            continue
                        m = re.match(rf'^{key}\s+equ\s+([0-9A-Fa-f]+h?|[0-9A-Fa-f]+)', line.strip())
                        if m:
                            istwert = m.group(1)
                            break
                    if istwert is not None:
                        new_config[config_key] = f'{config_key}="{istwert}"'
                    else:
                        new_config[config_key] = f'# {config_key} is not set'
        # String-Optionen: DB-Wert aus der .mac-Datei auslesen
        elif any(v == "string" for v in key_values.values()):
            for key, v in key_values.items():
                if v == "string":
                    istwert = None
                    for line in mac_lines:
                        if line.lstrip().startswith(';'):
                            continue
                        # Match with ,0 and optional comment
                        m = re.match(rf'^{key}:\s+db\s+([\'"])(.*?)([\'"]),0(.*)$', line.strip())
                        if m:
                            istwert = m.group(2)
                            break
                        # Match without ,0, but with optional comment
                        m2 = re.match(rf'^{key}:\s+db\s+([\'"])(.*?)([\'"])(.*)$', line.strip())
                        if m2:
                            istwert = m2.group(2)
                            break
                    if istwert is not None:
                        new_config[config_key] = f'{config_key}="{istwert}"'
                    else:
                        new_config[config_key] = f'# {config_key} is not set'
        else:
            # Bool-Optionen: Prüfe ob alle key=value-Paare in EQU-Zeilen übereinstimmen
            aktiv_bedingung = True
            for key, sollwert in key_values.items():
                istwert = None
                for line in mac_lines:
                    if line.lstrip().startswith(';'):
                        continue
                    m = re.match(rf'^{key}\s+equ\s+(\w+)', line.strip())
                    if m:
                        istwert = m.group(1)
                        break
                if istwert != sollwert:
                    aktiv_bedingung = False
            if aktiv_bedingung:
                new_config[config_key] = f"{config_key}=y"
            else:
                new_config[config_key] = f"# {config_key} is not set"

    # .config-Datei aktualisieren: Bestehende Einträge ersetzen, neue anhängen
    out_lines = []
    written = set()
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line)
                if m and m.group(2) in new_config:
                    out_lines.append(new_config[m.group(2)] + "\n")
                    written.add(m.group(2))
                else:
                    out_lines.append(line)
    # Noch nicht geschriebene neue Einträge anhängen
    for k, v in new_config.items():
        if k not in written:
            out_lines.append(v + "\n")
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"[INFO] .config aktualisiert (extract)")

# ============================================================================
# Patch-Modus - Werte aus .config in .mac-Dateien schreiben
# ============================================================================

def patch_mac_file(mac_path, config_path, param_mappings, loglevel="info"):
    """Assembler-Quelldatei (.mac) gemäß .config-Werten patchen.

    Aktualisiert EQU- und DB-Zeilen in der .mac-Datei entsprechend den
    Konfigurationswerten. Unterstützt drei Parametertypen:

    - bool: Setzt EQU-Werte (bei 'is not set' wird der invertierte Wert geschrieben)
    - string: Ändert DB-Strings (z.B. db 'neuer text',0)
    - hexstring: Ändert EQU-Hex-Werte (bei 'is not set' wird 0 geschrieben)

    Die Datei wird mit CRLF-Zeilenenden geschrieben (M80-Assembler-Kompatibilität).
    """
    # Aktive und deaktivierte Config-Optionen aus .config lesen
    config_set = set()       # Optionsnamen mit =y
    config_not_set = set()   # Optionsnamen mit 'is not set'
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            for line in f:
                m_y = re.match(r'^CONFIG_(\w+)=(y)', line.strip())
                m_n = re.match(r'^# CONFIG_(\w+) is not set', line.strip())
                if m_y:
                    config_set.add(m_y.group(1))
                elif m_n:
                    config_not_set.add(m_n.group(1))

    if not os.path.exists(mac_path):
        print(f"[ERROR] *.mac Datei nicht gefunden: {mac_path}")
        sys.exit(1)
    with open(mac_path, encoding="utf-8") as f:
        mac_lines = f.readlines()

    original_lines = list(mac_lines)  # Kopie für Debug-Diff

    def patch_key_in_line(line, key, value, is_string=False, is_hexstring=False):
        """Einzelne Zeile mit dem gegebenen Schlüssel und Wert patchen.

        Erkennt EQU-Zeilen (für bool/hexstring) und DB-Zeilen (für string).
        Kommentarzeilen (beginnend mit ;) werden übersprungen.

        Returns:
            str: Gepatchte Zeile oder None falls Zeile nicht zum Schlüssel passt
        """
        # Kommentare am Zeilenanfang nicht patchen (Assembler-Kommentar ;)
        if line.lstrip().startswith(';'):
            return None
        if is_string:
            # Mit ,0 und Kommentar
            m = re.match(rf'^({key}:\s+db\s+)([\'"])(.*?)([\'"]),0(.*)$', line.strip())
            if m:
                # Ersetze nur den String, Rest bleibt erhalten
                return f"{m.group(1)}'{value}',0{m.group(5)}\n"
            # Ohne ,0, aber mit Kommentar
            m2 = re.match(rf'^({key}:\s+db\s+)([\'"])(.*?)([\'"])(.*)$', line.strip())
            if m2:
                return f"{m2.group(1)}'{value}'{m2.group(5)}\n"
            return None
        # Standardfall: EQU-Zeile patchen (für bool und hexstring)
        m = re.match(rf'^({key}\s+equ\s+)([^;\s]+)(.*)$', line.strip())
        if m:
            val = value
            # Anführungszeichen für hexstring/textstring-Werte entfernen
            if (is_hexstring or (val and re.match(r'^".*"$', val))):
                val = val.strip('"')
            return f"{m.group(1)}{val}{m.group(3)}\n"
        return None

    # Schritt 1: Alle 'is not set'-Optionen patchen (invertierte Werte einsetzen)
    # Bei Bool-Optionen wird der invertierte Wert geschrieben (0→1, 1→0)
    # Bei Hexstring wird 0 geschrieben, bei String ein leerer String
    for entry in param_mappings:
        config_name = entry["config_name"]
        key_values = entry["key_values"]
        is_string = any(v == "string" for v in key_values.values())
        is_hexstring = any(v == "hexstring" for v in key_values.values())
        if config_name in config_not_set:
            for idx, line in enumerate(mac_lines):
                for key, value in key_values.items():
                    if is_hexstring:
                        # Nicht gesetzter Wert -> equ 0
                        patched = patch_key_in_line(line, key, "0", is_hexstring=True)
                    elif is_string:
                        patched = patch_key_in_line(line, key, "", is_string=True)
                    else:
                        try:
                            if value.isdigit():
                                inv = str(1 - int(value)) if value in ("0", "1") else "0"
                            else:
                                inv = "0"
                        except Exception:
                            inv = "0"
                        patched = patch_key_in_line(line, key, inv)
                    if patched and mac_lines[idx] != patched:
                        mac_lines[idx] = patched

    # Schritt 2: Alle aktiven Optionen ('=y', String, Hexstring) patchen
    # Hier werden die tatsächlichen Werte aus der .config geschrieben
    for entry in param_mappings:
        config_name = entry["config_name"]
        key_values = entry["key_values"]
        is_string = any(v == "string" for v in key_values.values())
        is_hexstring = any(v == "hexstring" for v in key_values.values())
        config_val = None
        string_in_config = False
        hexstring_in_config = False
        if is_hexstring:
            # Suche nach CONFIG_XYZ=...
            with open(config_path, encoding="utf-8") as f:
                for line in f:
                    m = re.match(rf'^CONFIG_{config_name}=(.+)', line.strip())
                    if m:
                        config_val = m.group(1)
                        hexstring_in_config = True
                        break
        elif is_string:
            with open(config_path, encoding="utf-8") as f:
                for line in f:
                    m = re.match(rf'^CONFIG_{config_name}="(.*)"', line.strip())
                    if m:
                        config_val = m.group(1)
                        string_in_config = True
                        break
        if (is_hexstring and hexstring_in_config) or (is_string and string_in_config) or (not is_string and not is_hexstring and config_name in config_set):
            for idx, line in enumerate(mac_lines):
                for key, value in key_values.items():
                    if is_hexstring:
                        # Patche immer Wert aus .config, auch wenn "0"
                        patched = patch_key_in_line(line, key, config_val if config_val is not None else "0", is_hexstring=True)
                    elif is_string:
                        patched = patch_key_in_line(line, key, config_val if config_val is not None else "", is_string=True)
                    else:
                        patched = patch_key_in_line(line, key, value)
                    if patched and mac_lines[idx] != patched:
                        mac_lines[idx] = patched

    # Debug-Ausgabe: Geänderte Zeilen anzeigen (Vorher/Nachher-Vergleich)
    if loglevel == "debug":
        for idx, (before, after) in enumerate(zip(original_lines, mac_lines)):
            if before != after:
                print(f"[DEBUG] Zeile {idx+1} vor Patch: {before.rstrip()}")
                print(f"[DEBUG] Zeile {idx+1} nach Patch: {after.rstrip()}")

    # Datei mit CRLF-Zeilenenden schreiben (\r\n für M80-Assembler-Kompatibilität)
    with open(mac_path, "w", encoding="utf-8", newline="") as f:
        f.write("".join(line.rstrip("\r\n") + "\r\n" for line in mac_lines))
    print(f"[INFO] *.mac Datei gepatcht (patch, CRLF enforced)")

# ============================================================================
# Hauptfunktion - Argumente parsen und Modus-Routing
# ============================================================================

def main():
    """Hauptfunktion: Argumente parsen, Parameter auslesen und extract/patch ausführen.

    Gruppiert die Parameter nach Zieldatei (source) und führt den gewählten
    Modus (extract/patch) für jede Zieldatei separat aus.
    """
    if len(sys.argv) < 4:
        print("Usage: patch_mac.py <extract|patch> <config> <systemvariante> [loglevel=debug|loglevel=info]")
        sys.exit(1)
    mode = sys.argv[1]
    config_path = sys.argv[2]
    system_variant = sys.argv[3]
    # Loglevel: Kommandozeile hat Vorrang, sonst Umgebungsvariable, Standard: info
    loglevel = "info"
    # Suche nach loglevel=... in den Argumenten
    for arg in sys.argv[4:]:
        if arg.startswith("loglevel="):
            loglevel = arg.split("=",1)[1].lower()
    # Fallback auf Umgebungsvariable
    if loglevel == "info" and os.environ.get("LOGLEVEL"):
        loglevel = os.environ["LOGLEVEL"].lower()

    # Kconfig.system der gewählten Systemvariante parsen
    kconfig_path = os.path.join("config", system_variant, "Kconfig.system")
    param_mappings = parse_kconfig_system(kconfig_path)

    # Parameter nach Zieldatei (source) gruppieren, damit jede .mac-Datei
    # nur einmal gelesen/geschrieben werden muss
    source_map = {}
    for entry in param_mappings:
        src = entry["source"] if entry["source"] else "bios.mac"
        if src not in source_map:
            source_map[src] = []
        source_map[src].append(entry)

    # Für jede Zieldatei den gewählten Modus (extract/patch) ausführen
    for src, mappings in source_map.items():
        # Vollständigen Pfad zur .mac-Datei zusammenbauen
        mac_path = os.path.join("src", system_variant, src)
        if mode == "extract":
            extract_mac_config(mac_path, config_path, mappings, loglevel=loglevel)
        elif mode == "patch":
            patch_mac_file(mac_path, config_path, mappings, loglevel=loglevel)
        else:
            print("Unknown mode")
            sys.exit(1)

if __name__ == "__main__":
    main()
