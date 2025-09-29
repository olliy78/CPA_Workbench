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
    Liefert eine Liste von Dicts: {config_name, source, key_values}
    Args:
        path (str): Pfad zur Kconfig.system
    Returns:
        list: Liste der Parametermappings
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
    Extrahiert Werte aus *.mac und schreibt sie in .config.
    Für jede Option wird geprüft, ob die Aktiv-Bedingung laut Mapping erfüllt ist.
    Args:
        mac_path (str): Pfad zur .mac Datei
        config_path (str): Pfad zur .config Datei
        param_mappings (list): Liste der Parametermappings
        loglevel (str): "info" oder "debug"
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
        # Hexstring-Optionen erkennen (key=hexstring)
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
                        # Wert 0 in .mac -> # CONFIG_xxx is not set
                        if istwert == "0":
                            new_config[config_key] = f'# {config_key} is not set'
                        else:
                            new_config[config_key] = f'{config_key}="{istwert}"'
                    else:
                        new_config[config_key] = f'# {config_key} is not set'
        # String-Optionen (klassisch)
        elif any(v == "string" for v in key_values.values()):
            for key, v in key_values.items():
                if v == "string":
                    istwert = None
                    for line in mac_lines:
                        if line.lstrip().startswith(';'):
                            continue
                        m = re.match(rf'^{key}:\s+db\s+([\'\"])(.*?)([\'\"]),0.*$', line.strip())
                        if m:
                            istwert = m.group(2)
                            break
                    if istwert is not None:
                        new_config[config_key] = f'{config_key}="{istwert}"'
                    else:
                        new_config[config_key] = f'# {config_key} is not set'
        else:
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
    Args:
        mac_path (str): Pfad zur .mac Datei
        config_path (str): Pfad zur .config Datei
        param_mappings (list): Liste der Parametermappings
        loglevel (str): "info" oder "debug"
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

    original_lines = list(mac_lines)  # Save original for debug diff

    def patch_key_in_line(line, key, value, is_string=False, is_hexstring=False):
        """
        Patcht eine Zeile mit dem gegebenen Schlüssel und Wert.
        Args:
            line (str): Originalzeile
            key (str): Schlüssel
            value (str): Neuer Wert
            is_string (bool): String-Option
            is_hexstring (bool): Hexstring-Option
        Returns:
            str|None: Gepatchte Zeile oder None, falls nicht zutreffend
        """
        # Kommentare am Zeilenanfang überspringen
        if line.lstrip().startswith(';'):
            return None
        if is_hexstring:
            # Wert aus .config kann Quotes enthalten, diese müssen entfernt werden
            clean_value = value.strip('"').strip("'")
            m = re.match(rf'^({key}\s+equ\s+)(["\']?)([^"\';\s]+)(["\']?)(.*)$', line.strip())
            if m:
                # Schreibe Wert ohne Quotes in die .mac
                return f"{m.group(1)}{clean_value}{m.group(5)}\n"
            return None
        if is_string:
            # String mit Kommentar nach ,0 erhalten
            m = re.match(rf'^({key}:\s+db\s+)([\'\"])(.*?)([\'\"]),0(.*)$', line.strip())
            if m:
                # m.group(5) enthält alles nach ,0 (inkl. Kommentar)
                return f"{m.group(1)}'{value}',0{m.group(5)}\n"
            # Fallback: Zeile ohne Quotes, aber mit ,0 und Kommentar
            m2 = re.match(rf'^({key}:\s+db\s+)[^,]*,0(.*)$', line.strip())
            if m2:
                return f"{m2.group(1)}'{value}',0{m2.group(2)}\n"
            return None
        # Standardfall: equ-Zeile patchen
        m = re.match(rf'^({key}\s+equ\s+)([^;\s]+)(.*)$', line.strip())
        if m:
            return f"{m.group(1)}{value}{m.group(3)}\n"
        return None

    # 1. Alle "is not set" Optionen patchen (invertiert, falls nötig)
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

    # 2. Alle "=y" und String-Optionen patchen (direkt)
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
                        patched = patch_key_in_line(line, key, config_val if config_val is not None else "0", is_hexstring=True)
                    elif is_string:
                        patched = patch_key_in_line(line, key, config_val if config_val is not None else "", is_string=True)
                    else:
                        patched = patch_key_in_line(line, key, value)
                    if patched and mac_lines[idx] != patched:
                        mac_lines[idx] = patched

    # Debug-Ausgabe: Nur Zeilen, die sich zwischen original und final geändert haben
    if loglevel == "debug":
        for idx, (before, after) in enumerate(zip(original_lines, mac_lines)):
            if before != after:
                print(f"[DEBUG] Zeile {idx+1} vor Patch: {before.rstrip()}")
                print(f"[DEBUG] Zeile {idx+1} nach Patch: {after.rstrip()}")

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

    kconfig_path = os.path.join("config", system_variant, "Kconfig.system")
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
