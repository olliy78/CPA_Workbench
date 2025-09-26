#!/usr/bin/env python3
"""
Generisches Konfigurations- und Patch-Tool für beliebige *.mac Dateien

Dieses Skript liest die Kconfig.system einer Systemvariante und extrahiert die konfigurierbaren Parameter
sowie deren Mapping zu Zieldateien und Werten. Es kann im Modus 'extract' die aktuelle Konfiguration aus
*.mac auslesen und in die .config schreiben, oder im Modus 'patch' die *.mac Datei gemäß .config patchen.

Verwendung:
    python patch_mac.py <extract|patch> <config> <systemvariante> [loglevel=debug|loglevel=info]

Optionale Argumente:
    loglevel=debug   Aktiviere ausführliche Debug-Ausgaben
    loglevel=info    Standard, weniger Ausgaben

Beispiel:
    python patch_mac.py extract .config bc_a5120 loglevel=debug
    python patch_mac.py patch .config bc_a5120 loglevel=info
"""
import sys
import os
import re

# --- Funktionsdefinitionen ---
def parse_kconfig_system(path):
    """
    Extrahiert alle konfigurierbaren Parameter aus Kconfig.system und deren Mapping.
    Liefert Liste von Dicts: {config_name, source, key, value}
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
            # Suche nach help block
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
                            parts = l3.split()
                            src = None
                            kvs = {}
                            for part in parts:
                                if part.startswith("source="):
                                    src = part.split("=",1)[1]
                                elif "=" in part:
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

def extract_mac_config(mac_path, config_path, param_mappings, loglevel="info"):
    """
    Extrahiert Werte aus *.mac und schreibt sie in .config. Bei loglevel="debug" werden alle Prüfungen und Ergebnisse ausgegeben.
    """
    if not os.path.exists(mac_path):
        print(f"[ERROR] *.mac Datei nicht gefunden: {mac_path}")
        sys.exit(1)
    with open(mac_path, encoding="utf-8") as f:
        mac_lines = f.readlines()

    config_vals = {}
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line)
                if m:
                    config_vals[m.group(2)] = line.rstrip('\n')

    new_config = {}
    for entry in param_mappings:
        key_values = entry["key_values"]
        config_name = entry["config_name"]
        config_key = f"CONFIG_{config_name}"
        match = True
        debug_info = []
        for key, expected_value in key_values.items():
            found_value = None
            for line in mac_lines:
                m = re.match(rf'^{key}\s+equ\s+(\w+)', line.strip())
                if m:
                    found_value = m.group(1)
                    break
            if loglevel == "debug":
                debug_info.append(f"  - Parameter: {key}, erwartet: {expected_value}, gefunden: {found_value}")
            if found_value != expected_value:
                match = False
        if match:
            new_config[config_key] = f"{config_key}=y"
            if loglevel == "debug":
                print(f"[DEBUG] {config_key}: ALLE Werte stimmen überein → =y")
                for info in debug_info:
                    print(info)
                print("  Ergebnis: OK\n")
        else:
            new_config[config_key] = f"# {config_key} is not set"
            if loglevel == "debug":
                print(f"[DEBUG] {config_key}: Mindestens ein Wert stimmt nicht → is not set")
                for info in debug_info:
                    print(info)
                print("  Ergebnis: NICHT OK\n")

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
    for k, v in new_config.items():
        if k not in written:
            out_lines.append(v + "\n")
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"[INFO] .config aktualisiert (extract)")

def patch_mac_file(mac_path, config_path, param_mappings, loglevel="info"):
    """
    Patche *.mac Datei gemäß .config.
    """
    config_set = set()
    config_not_set = set()
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

    def patch_key_in_line(line, key, value):
        m = re.match(rf'^({key}\s+equ\s+)(\w+)(.*)$', line.strip())
        if m:
            return f"{m.group(1)}{value}{m.group(3)}\n"
        return None

    # Helper for debug output
    def print_debug_patch(idx, before, after):
        print(f"[DEBUG] Zeile {idx+1} vor Patch: {before.rstrip()}")
        print(f"[DEBUG] Zeile {idx+1} nach Patch: {after.rstrip()}")

    # 1. "is not set" configs
    for entry in param_mappings:
        config_name = entry["config_name"]
        if config_name in config_not_set:
            key_values = entry["key_values"]
            for idx, line in enumerate(mac_lines):
                for key, value in key_values.items():
                    patched = patch_key_in_line(line, key, value)
                    if patched and mac_lines[idx] != patched:
                        if loglevel == "debug":
                            print_debug_patch(idx, mac_lines[idx], patched)
                        mac_lines[idx] = patched

    # 2. "=y" configs
    for entry in param_mappings:
        config_name = entry["config_name"]
        if config_name in config_set:
            key_values = entry["key_values"]
            for idx, line in enumerate(mac_lines):
                for key, value in key_values.items():
                    patched = patch_key_in_line(line, key, value)
                    if patched and mac_lines[idx] != patched:
                        if loglevel == "debug":
                            print_debug_patch(idx, mac_lines[idx], patched)
                        mac_lines[idx] = patched

    with open(mac_path, "w", encoding="utf-8") as f:
        f.writelines(mac_lines)
    print(f"[INFO] *.mac Datei gepatcht (patch)")

def main():
    """
    Hauptfunktion: Argumente parsen, Modus wählen, loglevel setzen und Routing.
    """
    if len(sys.argv) < 4:
        print("Usage: patch_mac.py <extract|patch> <config> <systemvariante> [loglevel=debug|loglevel=info]")
        sys.exit(1)
    mode = sys.argv[1]
    config_path = sys.argv[2]
    system_variant = sys.argv[3]
    loglevel = "info"
    # Suche nach loglevel=... in den Argumenten
    for arg in sys.argv[4:]:
        if arg.startswith("loglevel="):
            loglevel = arg.split("=",1)[1].lower()
    # Fallback auf Umgebungsvariable
    if loglevel == "info" and os.environ.get("LOGLEVEL"):
        loglevel = os.environ["LOGLEVEL"].lower()

    kconfig_path = os.path.join("configmenu", system_variant, "Kconfig.system")
    mac_path = os.path.join("src", system_variant, "bios.mac")

    param_mappings = parse_kconfig_system(kconfig_path)

    if mode == "extract":
        extract_mac_config(mac_path, config_path, param_mappings, loglevel=loglevel)
    elif mode == "patch":
        patch_mac_file(mac_path, config_path, param_mappings, loglevel=loglevel)
    else:
        print("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()
