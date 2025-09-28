#!/usr/bin/env python3
"""
Konfigurations-Tool für Diskettenlaufwerke in bios.mac

Dieses Skript automatisiert die Synchronisation zwischen einer Kconfig-basierten .config und einer Z80-Assemblerdatei (bios.mac).
Es kann sowohl die aktuelle Konfiguration aus bios.mac extrahieren und in .config schreiben (extract),
als auch bios.mac gemäß einer .config patchen (patch).

Funktionen:
- Extrahiert Hardware-, Laufwerks- und RAMDISK-Einstellungen aus bios.mac und schreibt sie in .config
- Patcht bios.mac nach Auswahl in menuconfig

Wichtige Besonderheiten:
- Boolesche Optionen werden invertiert, d.h. der Wert in bios.mac ist 1, wenn die Option aktiv ist, und 0, wenn sie nicht aktiv ist – oder umgekehrt, je nach Kconfig.system.
- Bei mehreren bool-Optionen (z.B. RAMDISK) werden alle zugehörigen Variablen in der richtigen Reihenfolge gesetzt: erst alle "is not set" (invertiert), dann alle "=y" (Zielwert).
- String-Optionen werden als db '...' in bios.mac geschrieben. Ist die Option nicht gesetzt, wird ein leerer String geschrieben.
- Die Mappings werden dynamisch aus Kconfig.system extrahiert, keine Hardcodierung im Skript.

Verwendung:
    python patch_bios_mac.py <bios.mac|auto> .config [extract|patch]
    # bios.mac|auto: Pfad zur bios.mac oder 'auto' für automatische Erkennung anhand .config
    # .config: Kconfig-Konfigurationsdatei
    # extract|patch: Modus (default: extract)
"""
import sys
import re
import os

# --- Schritt 1: Kconfig Mapping-Extraktion ---
import collections

def parse_kconfig_mappings(kconfig_path):
        """
        Parst die Kconfig.system und extrahiert alle relevanten Mappings.
        Jede Kconfig-Option, die eine source=bios.mac ... Zeile im help-Block hat, wird erkannt.
        Liefert eine Liste von Dicts mit:
            - config_name: Name der Kconfig-Option (z.B. SYSTEM_AUTOEXEC_STR)
            - bios_var: Name der Variable in bios.mac (z.B. kltbef)
            - type: Typ (z.B. string, int, ...)
            - value: (optional) Zielwert für bool/int-Optionen
        Die Funktion ist generisch und erkennt auch Multi-Parameter-Optionen (z.B. RAMDISK).
        """
    mappings = []
    current_config = None
    in_help = False
    help_lines = []
    with open(kconfig_path, encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if l.startswith("config "):
                if current_config and help_lines:
                    # Auswerten
                    for hl in help_lines:
                        m = _parse_source_line(hl)
                        if m:
                            for entry in m:
                                entry['config_name'] = current_config
                                mappings.append(entry)
                current_config = l.split()[1]
                in_help = False
                help_lines = []
            elif l == "help":
                in_help = True
                help_lines = []
            elif in_help:
                if l.startswith("source=bios.mac"):
                    help_lines.append(l)
                elif l == '' or l.startswith('source='):
                    help_lines.append(l)
                elif l.startswith("config ") or l.startswith("menu ") or l.startswith("choice"):
                    in_help = False
            elif l.startswith("menu ") or l.startswith("choice"):
                in_help = False
        # Letztes config auswerten
        if current_config and help_lines:
            for hl in help_lines:
                m = _parse_source_line(hl)
                if m:
                    for entry in m:
                        entry['config_name'] = current_config
                        mappings.append(entry)
    return mappings

def _parse_source_line(line):
    """
    Parst eine Zeile wie 'source=bios.mac kltbef=string' oder 'source=bios.mac cpu=k2521'.
    Gibt eine Liste von Dicts mit bios_var und type zurück.
    - Ist der Wert ein Typ (string/int/hex), wird type gesetzt.
    - Ist der Wert ein konkreter Wert (z.B. cpu=k2521), wird value gesetzt (für bool/int).
    """
    if not line.startswith("source=bios.mac"):
        return None
    parts = line.split()
    result = []
    for p in parts[1:]:
        if '=' in p:
            k, v = p.split('=', 1)
            # Typen: string, int, ...
            if v in ("string", "int", "hex"):
                result.append({'bios_var': k, 'type': v})
            else:
                # Wert ist ein Wert, Typ ist int (default)
                result.append({'bios_var': k, 'type': 'int', 'value': v})
    return result if result else None


## Liest die Datei bios.mac aus und extrahiert die aktuellen Hardware-, Laufwerks- und RAMDISK-Einstellungen.
# Erstellt bzw. aktualisiert die .config-Datei so, dass alle relevanten Optionen (z.B. CPU, FDC, CRT, RAM, DEV, CPUCLK, Laufwerke, RAMDISK) im Kconfig-Format abgebildet werden.
# Bestehende Einträge in .config werden überschrieben, fehlende ergänzt.
def extract_bios_config(bios_path, config_path):
    """Liest bios.mac und schreibt .config mit aktuellen Einstellungen"""
    # --- Dynamische Extraktion: ---
    # Kconfig-Mappings laden: Kconfig.system im gleichen System-Ordner wie bios.mac
    # Die Mappings bestimmen, welche Variablen/Optionen in bios.mac und .config synchronisiert werden.
    bios_dir = os.path.dirname(os.path.abspath(bios_path))
    kconfig_path = os.path.join(bios_dir, "Kconfig.system")
    mappings = parse_kconfig_mappings(kconfig_path)

    # bios.mac einlesen und alle relevanten Variablen extrahieren
    # Es werden sowohl equ-Zuweisungen (int/bool) als auch db-Zuweisungen (string) erkannt.
    bios_vars = {}
    with open(bios_path, encoding="utf-8") as f:
        for line in f:
            line_nocomment = line.split(';', 1)[0].strip()
            # equ: optionales @ am Anfang
            m_equ = re.match(r'^@?(\w+)\s+equ\s+(.+)', line_nocomment, re.IGNORECASE)
            if m_equ:
                var = m_equ.group(1)
                val = m_equ.group(2).strip()
                bios_vars[var] = val
            # String-Konstanten (z.B. kltbef db ...)
            m_db = re.match(r'^@?(\w+)\s+db\s+"([^"]*)"', line_nocomment, re.IGNORECASE)
            if m_db:
                var = m_db.group(1)
                val = m_db.group(2)
                bios_vars[var] = val

    # .config-Einträge generieren
    # Für jede Kconfig-Option wird geprüft, ob der aktuelle Wert in bios.mac dem Zielwert entspricht.
    # - Für bool-Optionen: y, wenn Wert wie in Kconfig.system, sonst n
    # - Für String-Optionen: Wert in "...", leerer String → not set
    patch_keys = {}
    for m in mappings:
        config_name = m['config_name']
        bios_var = m['bios_var']
        typ = m.get('type', 'int')
        value = bios_vars.get(bios_var)
        if value is None:
            continue
        # String-Optionen
        if typ == 'string':
            if value == '':
                patch_keys[f'CONFIG_{config_name}'] = None  # wird später als 'not set' geschrieben
            else:
                patch_keys[f'CONFIG_{config_name}'] = f'"{value}"'
        # Int/hex Optionen mit Wert
        elif 'value' in m:
            # z.B. cpu=k2521 → Wert vergleichen
            patch_keys[f'CONFIG_{config_name}'] = 'y' if value == m['value'] else 'n'
        else:
            # Int/hex ohne Vergleichswert: Wert direkt übernehmen
            patch_keys[f'CONFIG_{config_name}'] = value

    # .config patchen (bestehende Zeilen ersetzen, fehlende ergänzen)
    # Bestehende .config wird Zeile für Zeile aktualisiert, neue Optionen werden ergänzt.
    # not set wird als '# CONFIG_X is not set' geschrieben, Strings als 'CONFIG_X="..."'.
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []
    new_lines = []
    seen_keys = set()
    for line in lines:
        m = re.match(r'^(# )?(CONFIG_\w+) ?(=.+|is not set)?', line, re.IGNORECASE)
        if m:
            key = m.group(2).upper()
            if key in patch_keys:
                val = patch_keys[key]
                if val == 'y':
                    new_lines.append(f'{key}=y\n')
                elif val == 'n':
                    new_lines.append(f'# {key} is not set\n')
                else:
                    new_lines.append(f'{key}={val}\n')
                seen_keys.add(key)
                continue
        new_lines.append(line)
    for key, val in patch_keys.items():
        if key not in seen_keys:
            if val == 'y':
                new_lines.append(f'{key}=y\n')
            elif val == 'n' or val is None:
                new_lines.append(f'# {key} is not set\n')
            else:
                new_lines.append(f'{key}={val}\n')
    with open(config_path, 'w', encoding="utf-8") as f:
        f.writelines(new_lines)


## Patcht die Datei bios.mac anhand der aktuellen Auswahl in der .config.
# Für alle relevanten Hardware-, Laufwerks- und RAMDISK-Parameter werden die Werte aus der .config übernommen und in bios.mac eingetragen.
# Die Funktion sucht die passenden Zeilen in bios.mac und ersetzt sie entsprechend der Konfiguration.
def patch_bios_mac(bios_path, config_path):
    """Patches bios.mac gemäß .config"""
    # --- Dynamische Patch-Logik ---
    # Ziel: bios.mac gemäß .config patchen, sodass alle relevanten Optionen korrekt gesetzt sind.
    # Die Reihenfolge ist entscheidend: erst alle "is not set" (invertiert), dann alle "=y" (Zielwert).
    # Dadurch werden Mehrfachzuweisungen (z.B. RAMDISK) korrekt überschrieben.
    bios_dir = os.path.dirname(os.path.abspath(bios_path))
    kconfig_path = os.path.join(bios_dir, "Kconfig.system")
    mappings = parse_kconfig_mappings(kconfig_path)

    # .config auswerten: Listen für y- und not-set-Optionen
    # config_y: alle gesetzten Optionen (CONFIG_X=y)
    # config_notset: alle nicht gesetzten Optionen (# CONFIG_X is not set)
    # config_strvals: Stringwerte aus .config
    config_y = set()
    config_notset = set()
    config_strvals = {}
    with open(config_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'CONFIG_(\w+)=(.+)', line.strip())
            if m:
                config_name = m.group(1)
                val = m.group(2)
                if val == 'y':
                    config_y.add(config_name)
                elif val.startswith('"') and val.endswith('"'):
                    config_strvals[config_name] = val[1:-1]
            m2 = re.match(r'# (CONFIG_\w+) is not set', line.strip())
            if m2:
                config_name = m2.group(1)[7:]
                config_notset.add(config_name)

    # Hilfsfunktion: invertiere Wert (nur für int/hex, 0<->1, sonst 0<->Wert)
    # Wird für "is not set" verwendet, um den Zielwert zu invertieren (z.B. 1→0, 0→1, 10877→0, ...)
    def invert_value(val):
        if val == '1':
            return '0'
        if val == '0':
            return '1'
        try:
            ival = int(val)
            return '0' if ival != 0 else '1'
        except Exception:
            return '0'

    # Hilfsfunktion: invertiere alle Werte in einer source-Zeile (z.B. oss=1 em256=0 ...)
    # Für Multi-Parameter-Optionen (RAMDISK): alle Zielwerte invertieren
    def invert_source_dict(srcdict):
        return {k: invert_value(v) for k, v in srcdict.items()}

    # Hilfsfunktion: parse source=bios.mac ... Zeile in dict
    # Wandelt ein Mapping-Objekt in ein {bios_var: value}-Dict um
    def parse_source_dict(m):
        # m: Mapping-Objekt aus parse_kconfig_mappings
        # Kann mehrere Variablen enthalten, z.B. oss=1 em256=0 ...
        if 'value' in m:
            return {m['bios_var']: m['value']}
        # Für RAMDISK: alle keys aus bios_var/value
        if isinstance(m['bios_var'], str) and ' ' in m['bios_var']:
            # nicht genutzt, aber fallback
            return dict(x.split('=') for x in m['bios_var'].split())
        return {m['bios_var']: m.get('value', None)}

    # Hilfsfunktion: für RAMDISK und ähnliche: source=bios.mac ... mehrere key=val
    # Parst eine source=bios.mac ... Zeile mit mehreren key=val Paaren in ein Dict
    def parse_source_line_multi(line):
        # z.B. 'source=bios.mac oss=0 em256=1 mkd256=0 raf=0 rna=0'
        d = {}
        for part in line.split()[1:]:
            if '=' in part:
                k, v = part.split('=', 1)
                d[k] = v
        return d

    # Mapping: config_name -> alle zugehörigen source-Zeilen (für RAMDISK etc.)
    # Für jede Option werden alle zugehörigen Variablen gesammelt (z.B. RAMDISK: oss, em256, ...)
    config_to_sources = {}
    for m in mappings:
        config_name = m['config_name']
        if 'source_line' in m:
            # Noch nicht implementiert, aber für spätere Erweiterung
            pass
        if 'value' in m:
            config_to_sources.setdefault(config_name, []).append({m['bios_var']: m['value']})
        elif m['type'] == 'string':
            config_to_sources.setdefault(config_name, []).append({'_string': m['bios_var']})
        else:
            # Fallback: nur Variable, kein Wert
            config_to_sources.setdefault(config_name, []).append({m['bios_var']: None})

    # Für RAMDISK und ähnliche: alle source=bios.mac ... Zeilen aus Kconfig parsen
    # (Wir nehmen alle Zeilen aus Kconfig.system, die mit source=bios.mac ... beginnen und '=' enthalten)
    # Dadurch werden auch Multi-Parameter-Optionen korrekt erkannt.
    kconfig_path = os.path.join(bios_dir, "Kconfig.system")
    ramdisk_source_lines = []
    with open(kconfig_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith('source=bios.mac') and '=' in line:
                ramdisk_source_lines.append(line.strip())

    # Patch bios.mac: erst alle not set, dann alle y
    # Wir gehen bios.mac zweimal durch:
    # 1. Durchlauf: alle "is not set" Optionen → Variablen werden auf invertierten Wert gesetzt
    # 2. Durchlauf: alle "=y" Optionen → Variablen werden auf Zielwert gesetzt
    # Dadurch wird garantiert, dass am Ende die zuletzt aktivierte Option den Wert bestimmt (z.B. RAMDISK)
    out = []
    with open(bios_path, 'r', encoding="utf-8", newline='') as f:
        lines = [l.rstrip('\r\n') for l in f]

    # 1. Alle "is not set" Optionen: schreibe invertierte Werte
    # Für jede Variable, die zu einer nicht gesetzten Option gehört, wird der Wert invertiert.
    # Bei String-Optionen wird ein leerer String geschrieben (db '').
    for idx, l in enumerate(lines):
        replaced = False
    # RAMDISK und ähnliche: mehrere Variablen in einer Zeile
    # Für jede RAMDISK-Option (Multi-Parameter) werden alle zugehörigen Variablen invertiert.
        for src in ramdisk_source_lines:
            srcdict = parse_source_line_multi(src)
            for config_name in config_notset:
                if config_name in config_to_sources:
                    for bios_var in srcdict:
                        m_var = re.match(rf'^(\s*@?){bios_var}\s+equ\s+.*$', l, re.IGNORECASE)
                        if m_var:
                            prefix = m_var.group(1)
                            inv = invert_value(srcdict[bios_var])
                            out.append(f'{prefix}{bios_var} equ {inv}\r\n')
                            replaced = True
                    # String-Optionen: nicht relevant für RAMDISK
    # Einzelne bool/int Optionen
    # Für jede einzelne Option (bool/int/string) wird die zugehörige Variable gesetzt.
    # String-Optionen: db ''
    # Bool/Int: invertierter Wert
        for m in mappings:
            config_name = m['config_name']
            bios_var = m['bios_var']
            typ = m.get('type', 'int')
            if config_name in config_notset:
                m_var = re.match(rf'^(\s*@?){bios_var}\s+equ\s+.*$', l, re.IGNORECASE)
                if typ == 'string' and re.match(rf'^@?{bios_var}\s+db\s+"', l, re.IGNORECASE):
                    prefix = '@' if l.strip().startswith('@') else ''
                    out.append(f"{prefix}{bios_var} db ''\r\n")
                    replaced = True
                elif 'value' in m and m_var:
                    prefix = m_var.group(1)
                    inv = invert_value(m['value'])
                    out.append(f'{prefix}{bios_var} equ {inv}\r\n')
                    replaced = True
        if not replaced:
            out.append(l + '\r\n')

    # 2. Alle =y Optionen: schreibe Zielwerte
    # (Nochmal Zeilen durchgehen, damit =y am Ende steht und ggf. vorherige Werte überschreibt)
    # Für jede gesetzte Option werden die Zielwerte aus Kconfig.system übernommen.
    # String-Optionen: Wert aus .config (db '...')
    # Bool/Int: Zielwert
    lines2 = out
    out = []
    for idx, l in enumerate(lines2):
        replaced = False
    # RAMDISK und ähnliche: mehrere Variablen in einer Zeile
    # Für jede RAMDISK-Option (Multi-Parameter) werden alle zugehörigen Variablen auf Zielwert gesetzt.
        for src in ramdisk_source_lines:
            srcdict = parse_source_line_multi(src)
            for config_name in config_y:
                if config_name in config_to_sources:
                    for bios_var in srcdict:
                        m_var = re.match(rf'^(\s*@?){bios_var}\s+equ\s+.*$', l, re.IGNORECASE)
                        if m_var:
                            prefix = m_var.group(1)
                            out.append(f'{prefix}{bios_var} equ {srcdict[bios_var]}\r\n')
                            replaced = True
    # Einzelne bool/int Optionen
    # Für jede einzelne Option (bool/int/string) wird die zugehörige Variable gesetzt.
    # String-Optionen: Wert aus .config (db '...')
    # Bool/Int: Zielwert
        for m in mappings:
            config_name = m['config_name']
            bios_var = m['bios_var']
            typ = m.get('type', 'int')
            if config_name in config_y:
                m_var = re.match(rf'^(\s*@?){bios_var}\s+equ\s+.*$', l, re.IGNORECASE)
                if typ == 'string' and re.match(rf'^@?{bios_var}\s+db\s+"', l, re.IGNORECASE):
                    prefix = '@' if l.strip().startswith('@') else ''
                    sval = config_strvals.get(config_name, '')
                    out.append(f"{prefix}{bios_var} db '{sval}'\r\n")
                    replaced = True
                elif 'value' in m and m_var:
                    prefix = m_var.group(1)
                    out.append(f'{prefix}{bios_var} equ {m["value"]}\r\n')
                    replaced = True
        if not replaced:
            out.append(l + '\r\n')

    with open(bios_path, 'w', encoding="utf-8", newline='') as f:
        f.writelines(out)


## Hauptfunktion des Skripts.
# Liest die Kommandozeilenargumente aus und steuert den Ablauf:
# - bios.mac und .config werden als Eingabe erwartet
# - Modus 'extract': Einstellungen aus bios.mac werden in .config übernommen
# - Modus 'patch': bios.mac wird gemäß .config gepatcht
# - Bei 'auto' als bios.mac wird die passende Datei anhand der Systemauswahl in .config automatisch gewählt
def main():
    if len(sys.argv) < 3:
        print("Usage: patch_bios_mac.py <bios.mac|auto> .config [extract|patch]")
        sys.exit(1)
    bios_path = sys.argv[1]
    config_path = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'extract'

    # Automatische Auswahl der passenden bios.mac anhand des Systemtyps in .config
    # Wenn 'auto' gewählt ist, wird anhand der gesetzten System-Option in .config der Pfad zur bios.mac bestimmt.
    # Fallback: src/bc_a5120/bios.mac
    if bios_path == 'auto':
        # Default-Mapping: Symbolname -> Pfad
        system_map = {
            'CONFIG_SYSTEM_BC_A5120': 'src/bc_a5120/bios.mac',
            'CONFIG_SYSTEM_PC_1715': 'src/pc_1715/bios.mac',
            'CONFIG_SYSTEM_PC_1715_870330': 'src/pc_1715_870330/bios.mac',
        }
        selected = None
        if os.path.exists(config_path):
            with open(config_path) as f:
                for line in f:
                    for key, path in system_map.items():
                        if line.strip() == f'{key}=y':
                            print(f"[DEBUG] Gefundener Systemtyp: {key} -> {path}")
                            selected = path
                            break
                    if selected:
                        break
        if not selected:
            print("[WARN] Konnte Systemtyp nicht aus .config erkennen. Fallback: src/bc_a5120/bios.mac")
            selected = 'src/bc_a5120/bios.mac'
        bios_path = selected

    if mode == 'extract':
        # Extrahiere aktuelle Werte aus bios.mac und schreibe sie in .config
        extract_bios_config(bios_path, config_path)
    elif mode == 'patch':
        # Patche bios.mac gemäß .config (bool, int, string, Multi-Parameter)
        patch_bios_mac(bios_path, config_path)
    else:
        print("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()
