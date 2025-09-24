#!/usr/bin/env python3
"""
Konfigurations-Tool für Diskettenlaufwerke in bios.mac

Dieses Skript liest bios.mac und erzeugt eine .config mit den aktuellen Einstellungen.
Nach Auswahl in menuconfig kann bios.mac gemäß der Konfiguration gepatcht werden.

Funktionen:
- Extrahiert Hardware-, Laufwerks- und RAMDISK-Einstellungen aus bios.mac und schreibt sie in .config
- Patcht bios.mac nach Auswahl in menuconfig

Verwendung:
    python patch_bios_mac.py <bios.mac|auto> .config [extract|patch]
"""
import sys
import re
import os




# PARAMS: Liste von Hardware-Parametern, die zwischen Kconfig (.config) und bios.mac gemappt werden.
# Jeder Eintrag besteht aus:
#   - Kconfig-Prefix (z.B. "CPU")
#   - bios.mac-Key (z.B. "cpu")
#   - Mapping-Dictionary: Kconfig-Option -> Wert in bios.mac
PARAMS = [
    ("CPU",    "cpu",    { 'CPU_K2521': 'k2521', 'CPU_K2526': 'k2526', 'CPU_C1715': 'c1715' }),
    ("FDC",    "fdc",    { 'FDC_K5120': 'k5120', 'FDC_K5122': 'k5122', 'FDC_K5126': 'k5126', 'FDC_F1715': 'f1715', 'FDC_FDC3': 'fdc3' }),
    ("CRT",    "crt",    { 'CRT_K7024': 'k7024', 'CRT_DSY5': 'dsy5', 'CRT_B1715': 'b1715' }),
    ("RAM",    "ramkb",  { 'RAM_64': '64', 'RAM_32': '32' }),
    ("DEV",    "dev",    { 'DEV_OEM': 'oem', 'DEV_CPD': 'cpd', 'DEV_K8915': 'k8915' }),
    ("CPUCLK", "cpuclk", { 'CPUCLK_25': '25', 'CPUCLK_40': '40' }),
]

# DRIVE_MAP: Dictionary mit allen unterstützten Laufwerks-Typen.
# Key: Wert in bios.mac (z.B. "10540"), Value: Beschreibung des Laufwerks.
DRIVE_MAP = {
    '10540': 'DD, SS, 5", 40 Tracks (K5600.10)',
    '10580': 'DD, SS, 5", 80 Tracks (K5600.20)',
    '11580': 'DD, DS, 5", 80 Tracks (K5601 !!!)',
    '00877': 'SD, SS, 8", 77 Tracks (MF3200)',
    '10877': 'DD, SS, 8", 77 Tracks (K5602.10, MF6400)',
    '0':     'Nicht vorhanden',
}

# DRIVE_VALS: Liste aller Laufwerks-Keys, wie sie in bios.mac vorkommen können.
DRIVE_VALS = list(DRIVE_MAP.keys())

# BIOS_DRIVES: Liste der unterstützten Laufwerksbuchstaben (A-D).
BIOS_DRIVES = ['A', 'B', 'C', 'D']

# RAMDISK_MAP: Mapping für RAMDISK-Konfigurationen.
# Key: Kconfig-Option (z.B. "RAMDISK_OSS")
# Value: Dictionary mit den einzelnen RAMDISK-Parametern und deren Wert in bios.mac
RAMDISK_MAP = {
    'RAMDISK_NONE':  {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_OSS':   {'oss': '1', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_EM256': {'oss': '0', 'em256': '1', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_MKD256':{'oss': '0', 'em256': '0', 'mkd256': '1', 'raf': '0', 'rna': '0'},
    'RAMDISK_RAF':   {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '1', 'rna': '0'},
    'RAMDISK_NANOS': {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '1'},
}

## Erzeugt ein invertiertes Dictionary aus einem Mapping.
# Wandelt die Zuordnung von key->value in value->key um.
# Wird im Skript verwendet, um aus den Mapping-Tabellen (z.B. für Hardware-Parameter) die Rückrichtung zu erzeugen:
# So kann man aus einem Wert in bios.mac den passenden Kconfig-Schlüssel ableiten und umgekehrt.
def reverse_map(mapping):
    return {v: k for k, v in mapping.items()}


## Liest die Datei bios.mac aus und extrahiert die aktuellen Hardware-, Laufwerks- und RAMDISK-Einstellungen.
# Erstellt bzw. aktualisiert die .config-Datei so, dass alle relevanten Optionen (z.B. CPU, FDC, CRT, RAM, DEV, CPUCLK, Laufwerke, RAMDISK) im Kconfig-Format abgebildet werden.
# Bestehende Einträge in .config werden überschrieben, fehlende ergänzt.
def extract_bios_config(bios_path, config_path):
    """Liest bios.mac und schreibt .config mit aktuellen Einstellungen"""
    config = {}
    # Hardware- und RAMDISK-Parameter initialisieren
    param_vals = {p[1]: None for p in PARAMS}
    found = {p[1]: False for p in PARAMS}
    ramdisk_vals = {k: None for k in RAMDISK_MAP['RAMDISK_NONE'].keys()}
    with open(bios_path) as f:
        for line in f:
            line_nocomment = line.split(';', 1)[0].strip()
            # RAMDISK-Parameter
            for ramkey in ramdisk_vals:
                m = re.match(rf'^{ramkey}\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
                if m:
                    ramdisk_vals[ramkey] = m.group(1)
            # Laufwerke
            m_drive = re.match(r'^disk([A-D])\s+equ\s+(\d+)', line_nocomment, re.IGNORECASE)
            if m_drive:
                drv = m_drive.group(1).upper()
                val = m_drive.group(2) if m_drive.group(2) in DRIVE_VALS else '0'
                for v in DRIVE_VALS:
                    config[f'CONFIG_DRIVE_{drv}_{v}'] = 'y' if v == val else 'n'
            # Hardware-Parameter generisch extrahieren
            for kconf, bioskey, mapping in PARAMS:
                m = re.match(rf'^{bioskey}\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
                if m:
                    param_vals[bioskey] = m.group(1)
                    found[bioskey] = True
    # Patch-Keys für .config generieren
    patch_keys = {k: v for k, v in config.items()}
    # Hardware-Parameter generisch
    for kconf, bioskey, mapping in PARAMS:
        if found[bioskey]:
            rev = reverse_map(mapping)
            for k, v in rev.items():
                patch_keys[f'CONFIG_{kconf}_{k}'] = 'y' if param_vals[bioskey] == k else 'n'
    # RAMDISK
    if all(v is not None for v in ramdisk_vals.values()):
        ramdisk_config = None
        for k, v in RAMDISK_MAP.items():
            if all(str(ramdisk_vals[key]) == str(val) for key, val in v.items()):
                ramdisk_config = k
                break
        for k in RAMDISK_MAP.keys():
            patch_keys[f'CONFIG_{k}'] = 'y' if k == ramdisk_config else 'n'
    # .config patchen (bestehende Zeilen ersetzen, fehlende ergänzen)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    new_lines = []
    seen_keys = set()
    for line in lines:
        m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line, re.IGNORECASE)
        if m:
            key = m.group(2).upper()
            if key in patch_keys:
                new_lines.append(f'{key}=y\n' if patch_keys[key] == 'y' else f'# {key} is not set\n')
                seen_keys.add(key)
                continue
        new_lines.append(line)
    for key, val in patch_keys.items():
        if key not in seen_keys:
            new_lines.append(f'{key}=y\n' if val == 'y' else f'# {key} is not set\n')
    with open(config_path, 'w') as f:
        f.writelines(new_lines)


## Patcht die Datei bios.mac anhand der aktuellen Auswahl in der .config.
# Für alle relevanten Hardware-, Laufwerks- und RAMDISK-Parameter werden die Werte aus der .config übernommen und in bios.mac eingetragen.
# Die Funktion sucht die passenden Zeilen in bios.mac und ersetzt sie entsprechend der Konfiguration.
def patch_bios_mac(bios_path, config_path):
    """Patches bios.mac gemäß .config"""
    # Lese Auswahl aus .config
    chosen = {}
    param_vals = {p[1]: None for p in PARAMS}
    ramdisk_choice = None
    with open(config_path) as f:
        for line in f:
            m = re.match(r'CONFIG_DRIVE_([A-D])_([0-9]+)=(y|n)', line)
            if m and m.group(3) == 'y':
                chosen[m.group(1)] = m.group(2)
            for kconf, bioskey, mapping in PARAMS:
                m2 = re.match(rf'CONFIG_{kconf}_(\w+)=(y|n)', line)
                if m2 and m2.group(2) == 'y':
                    val = mapping.get(f'{kconf}_{m2.group(1)}')
                    if val:
                        param_vals[bioskey] = val
            m = re.match(r'CONFIG_RAMDISK_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                ramdisk_choice = 'RAMDISK_' + m.group(1)
    # Patch bios.mac
    out = []
    # Patterns für Hardware-Parameter generisch erzeugen
    hw_patterns = {bioskey: re.compile(rf'^({bioskey}\s+equ\s+)(\w+)(.*)$', re.IGNORECASE) for _, bioskey, _ in PARAMS}
    # RAM-Disk Patterns
    for ramkey in RAMDISK_MAP['RAMDISK_NONE'].keys():
        hw_patterns[ramkey] = re.compile(rf'^({ramkey}\s+equ\s+)(\w+)(.*)$', re.IGNORECASE)
    # RAM-Disk Werte aus Kconfig übernehmen
    ramdisk_vals = None
    if ramdisk_choice and ramdisk_choice in RAMDISK_MAP:
        ramdisk_vals = RAMDISK_MAP[ramdisk_choice]
    with open(bios_path, 'r', newline='') as f:
        for line in f:
            l = line.rstrip('\r\n')
            # diskA..diskD
            m_drive = re.match(r'^(disk([A-D])\s+equ\s+)([0-9]+)(.*)$', l, re.IGNORECASE)
            if m_drive:
                drv = m_drive.group(2).upper()
                orig_val = m_drive.group(3)
                rest = m_drive.group(4)
                val = chosen.get(drv, orig_val)
                out.append(f'{m_drive.group(1)}{val}{rest}\r\n')
                continue
            replaced = False
            # Hardware-Parameter generisch patchen
            for kconf, bioskey, mapping in PARAMS:
                pat = hw_patterns[bioskey]
                m_hw = pat.match(l)
                if m_hw and param_vals[bioskey] is not None:
                    out.append(f"{m_hw.group(1)}{param_vals[bioskey]}{m_hw.group(3)}\r\n")
                    replaced = True
                    break
            if not replaced:
                # RAMDISK generisch patchen
                for ramkey in RAMDISK_MAP['RAMDISK_NONE'].keys():
                    pat = hw_patterns[ramkey]
                    m_hw = pat.match(l)
                    if m_hw and ramdisk_vals is not None:
                        out.append(f"{m_hw.group(1)}{ramdisk_vals[ramkey]}{m_hw.group(3)}\r\n")
                        replaced = True
                        break
            if not replaced:
                out.append(l + '\r\n')
    with open(bios_path, 'w', newline='') as f:
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
        extract_bios_config(bios_path, config_path)
    elif mode == 'patch':
        patch_bios_mac(bios_path, config_path)
    else:
        print("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()
