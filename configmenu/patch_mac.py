#!/usr/bin/env python3
"""
Generisches Konfigurations- und Patch-Tool für beliebige *.mac Dateien

Dieses Skript liest die Kconfig.system einer Systemvariante und extrahiert die konfigurierbaren Parameter
sowie deren Mapping zu Zieldateien und Werten. Es kann im Modus 'extract' die aktuelle Konfiguration aus
*.mac auslesen und in die .config schreiben, oder im Modus 'patch' die *.mac Datei gemäß .config patchen.

Verwendung:
    python patch_mac.py <extract|patch> <config> <systemvariante>
Beispiel:
    python patch_mac.py extract .config bc_a5120
    python patch_mac.py patch .config bc_a5120
"""
import sys
import os
import re

# Grundgerüst: Argumente parsen
# sys.argv[1]: Modus (extract|patch)
# sys.argv[2]: Pfad zur .config
# sys.argv[3]: Name der Systemvariante (z.B. bc_a5120)
def main():
    if len(sys.argv) < 4:
        print("Usage: patch_mac.py <extract|patch> <config> <systemvariante>")
        sys.exit(1)
    mode = sys.argv[1]
    config_path = sys.argv[2]
    system_variant = sys.argv[3]

    # Pfade ermitteln
    kconfig_path = os.path.join("configmenu", system_variant, "Kconfig.system")
    mac_path = os.path.join("src", system_variant, "bios.mac")  # TODO: generisch machen


    # --- Generisches Parsing der Kconfig.system ---
    def parse_kconfig_system(path):
        """
        Extrahiere alle konfigurierbaren Parameter aus Kconfig.system und deren Mapping.
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

    # Test: Parameter extrahieren
    param_mappings = parse_kconfig_system(kconfig_path)
    #print("[DEBUG] Gefundene Parameter-Mappings:")
    #for entry in param_mappings:
    #    print(entry)


    # --- Extract-Modus ---
    if mode == "extract":
        # Lese *.mac Datei
        if not os.path.exists(mac_path):
            print(f"[ERROR] *.mac Datei nicht gefunden: {mac_path}")
            sys.exit(1)
        with open(mac_path, encoding="utf-8") as f:
            mac_lines = f.readlines()

        # Lese bestehende .config
        config_vals = {}
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                for line in f:
                    m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line)
                    if m:
                        config_vals[m.group(2)] = line.rstrip('\n')

        # Für jeden Parameter Mapping: Werte aus *.mac extrahieren
        new_config = {}
        for entry in param_mappings:
            key_values = entry["key_values"]
            match = True
            for key, expected_value in key_values.items():
                found_value = None
                for line in mac_lines:
                    m = re.match(rf'^{key}\s+equ\s+(\w+)', line.strip())
                    if m:
                        found_value = m.group(1)
                        break
                if found_value != expected_value:
                    match = False
                    break
            config_name = entry["config_name"]
            config_key = f"CONFIG_{config_name}"
            if match:
                new_config[config_key] = f"{config_key}=y"
            else:
                new_config[config_key] = f"# {config_key} is not set"

        # Schreibe neue .config (nur relevante Keys)
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

    # --- Patch-Modus ---
    elif mode == "patch":
        # Lese .config
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

        # Lese *.mac Datei
        if not os.path.exists(mac_path):
            print(f"[ERROR] *.mac Datei nicht gefunden: {mac_path}")
            sys.exit(1)
        with open(mac_path, encoding="utf-8") as f:
            mac_lines = f.readlines()

        # Patch: Zuerst alle "is not set" configs, dann alle "=y" configs
        # Wir patchen Zeilen in mac_lines entsprechend
        # 1. "is not set" configs: Setze alle zugehörigen key-values auf die Werte aus Kconfig.system
        # 2. "=y" configs: Setze alle zugehörigen key-values auf die Werte aus Kconfig.system

        # Hilfsfunktion: Patch key-value in Zeile
        def patch_key_in_line(line, key, value):
            m = re.match(rf'^({key}\s+equ\s+)(\w+)(.*)$', line.strip())
            if m:
                return f"{m.group(1)}{value}{m.group(3)}\n"
            return None

        # 1. "is not set" configs
        for entry in param_mappings:
            config_name = entry["config_name"]
            if config_name in config_not_set:
                key_values = entry["key_values"]
                for idx, line in enumerate(mac_lines):
                    for key, value in key_values.items():
                        patched = patch_key_in_line(line, key, value)
                        if patched:
                            mac_lines[idx] = patched

        # 2. "=y" configs
        for entry in param_mappings:
            config_name = entry["config_name"]
            if config_name in config_set:
                key_values = entry["key_values"]
                for idx, line in enumerate(mac_lines):
                    for key, value in key_values.items():
                        patched = patch_key_in_line(line, key, value)
                        if patched:
                            mac_lines[idx] = patched

        # Schreibe gepatchte *.mac Datei
        with open(mac_path, "w", encoding="utf-8") as f:
            f.writelines(mac_lines)
        print(f"[INFO] *.mac Datei gepatcht (patch)")
    else:
        print("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()
