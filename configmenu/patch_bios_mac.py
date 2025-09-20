#!/usr/bin/env python3
"""
Konfigurations-Tool für Diskettenlaufwerke in bios.mac
- Liest bios.mac und erzeugt eine .config mit den aktuellen Einstellungen
- Patcht bios.mac nach Auswahl in menuconfig
"""
import sys
import re
import os


# Mapping: Auswahltext <-> Wert für Diskettenlaufwerke
DRIVE_MAP = {
    '10540': 'DD, SS, 5", 40 Tracks (K5600.10)',
    '10580': 'DD, SS, 5", 80 Tracks (K5600.20)',
    '11580': 'DD, DS, 5", 80 Tracks (K5601 !!!)',
    '00877': 'SD, SS, 8", 77 Tracks (MF3200)',
    '10877': 'DD, SS, 8", 77 Tracks (K5602.10, MF6400)',
    '0':     'Nicht vorhanden',
}
DRIVE_VALS = list(DRIVE_MAP.keys())
BIOS_DRIVES = ['A', 'B', 'C', 'D']
CONFIG_CHOICES = {
    'A': 'DRIVE_A_',
    'B': 'DRIVE_B_',
    'C': 'DRIVE_C_',
    'D': 'DRIVE_D_',
}
BIOS_PATTERN = re.compile(r'^(disk([A-D])\s+equ\s+)([0-9]+)$')


# Hardwarevariante: Mapping für Kconfig <-> bios.mac
CPU_MAP = {
    'CPU_K2521': 'k2521',
    'CPU_K2526': 'k2526',
    'CPU_C1715': 'c1715',
}
FDC_MAP = {
    'FDC_K5120': 'k5120',
    'FDC_K5122': 'k5122',
    'FDC_K5126': 'k5126',
    'FDC_F1715': 'f1715',
    'FDC_FDC3':  'fdc3',
}
CRT_MAP = {
    'CRT_K7024': 'k7024',
    'CRT_DSY5': 'dsy5',
    'CRT_B1715': 'b1715',
}
RAM_MAP = {
    'RAM_64': '64',
    'RAM_32': '32',
}
DEV_MAP = {
    'DEV_OEM': 'oem',
    'DEV_CPD': 'cpd',
    'DEV_K8915': 'k8915',
}
CPUCLK_MAP = {
    'CPUCLK_25': '25',
    'CPUCLK_40': '40',
}
# Mapping für RAM-Disk-Optionen (Kconfig -> bios.mac)
RAMDISK_MAP = {
    'RAMDISK_NONE':  {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_OSS':   {'oss': '1', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_EM256': {'oss': '0', 'em256': '1', 'mkd256': '0', 'raf': '0', 'rna': '0'},
    'RAMDISK_MKD256':{'oss': '0', 'em256': '0', 'mkd256': '1', 'raf': '0', 'rna': '0'},
    'RAMDISK_RAF':   {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '1', 'rna': '0'},
    'RAMDISK_NANOS': {'oss': '0', 'em256': '0', 'mkd256': '0', 'raf': '0', 'rna': '1'},
}
REVERSE_CPU_MAP = {v: k for k, v in CPU_MAP.items()}
REVERSE_FDC_MAP = {v: k for k, v in FDC_MAP.items()}
REVERSE_CRT_MAP = {v: k for k, v in CRT_MAP.items()}
REVERSE_RAM_MAP = {v: k for k, v in RAM_MAP.items()}
REVERSE_DEV_MAP = {v: k for k, v in DEV_MAP.items()}
REVERSE_CPUCLK_MAP = {v: k for k, v in CPUCLK_MAP.items()}


def extract_bios_config(bios_path, config_path):
    """Liest bios.mac und schreibt .config mit aktuellen Einstellungen"""
    config = {}
    cpu = fdc = crt = ramkb = dev = cpuclk = None
    # RAM-Disk: Werte initialisieren
    ramdisk_vals = {'oss': None, 'em256': None, 'mkd256': None, 'raf': None, 'rna': None}
    found = { 'cpu': False, 'fdc': False, 'crt': False, 'ramkb': False, 'dev': False, 'cpuclk': False }
    with open(bios_path) as f:
        for line in f:
            # Kommentar abtrennen (alles nach einem Semikolon ignorieren)
            line_nocomment = line.split(';', 1)[0].strip()
            # --- RAM-Disk-Parameter extrahieren ---
            for ramkey in ramdisk_vals.keys():
                m_ram = re.match(rf'^{ramkey}\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
                if m_ram:
                    ramdisk_vals[ramkey] = m_ram.group(1)

            # --- Laufwerkskonfiguration extrahieren ---
            # Erkenne Zeilen wie: diskA equ 10540 (beliebige Leerzeichen/Tabs)
            m_drive = re.match(r'^disk([A-D])\s+equ\s+(\d+)', line_nocomment, re.IGNORECASE)
            if m_drive:
                drv = m_drive.group(1).upper()  # A, B, C, D
                val = m_drive.group(2)
                # Fallback auf '0' falls Wert nicht bekannt
                if val not in DRIVE_VALS:
                    val = '0'
                # Setze für alle möglichen Werte das passende Flag
                for v in DRIVE_VALS:
                    key = f'CONFIG_DRIVE_{drv}_{v}'
                    config[key] = 'y' if v == val else 'n'

            # --- Hardwarevariante robust extrahieren ---
            # Erkenne Zeilen wie: cpu equ k2526 (beliebige Leerzeichen/Tabs)
            m_cpu = re.match(r'^cpu\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_cpu:
                cpu = m_cpu.group(1)
                found['cpu'] = True
            m_fdc = re.match(r'^fdc\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_fdc:
                fdc = m_fdc.group(1)
                found['fdc'] = True
            m_crt = re.match(r'^crt\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_crt:
                crt = m_crt.group(1)
                found['crt'] = True
            m_ramkb = re.match(r'^ramkb\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_ramkb:
                ramkb = m_ramkb.group(1)
                found['ramkb'] = True
            m_dev = re.match(r'^dev\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_dev:
                dev = m_dev.group(1)
                found['dev'] = True
            m_cpuclk = re.match(r'^cpuclk\s+equ\s+(\w+)', line_nocomment, re.IGNORECASE)
            if m_cpuclk:
                cpuclk = m_cpuclk.group(1)
                found['cpuclk'] = True
    # Schreibe .config
    # --- Patch .config im Kconfig-Stil: Nur relevante Werte ändern/ergänzen ---
    # 1. Alle relevanten Keys und Zielwerte sammeln
    patch_keys = {}
    # Laufwerke
    for drv in BIOS_DRIVES:
        for v in DRIVE_VALS:
            key = f'CONFIG_DRIVE_{drv}_{v}'.upper()
            if key in config:
                patch_keys[key] = config[key]
    # Hardware
    if found['cpu']:
        for k, v in REVERSE_CPU_MAP.items():
            patch_keys[f'CONFIG_CPU_{k}'.upper()] = 'y' if cpu == k else 'n'
    if found['fdc']:
        for k, v in REVERSE_FDC_MAP.items():
            patch_keys[f'CONFIG_FDC_{k}'.upper()] = 'y' if fdc == k else 'n'
    if found['crt']:
        for k, v in REVERSE_CRT_MAP.items():
            patch_keys[f'CONFIG_CRT_{k}'.upper()] = 'y' if crt == k else 'n'
    if found['ramkb']:
        for k, v in REVERSE_RAM_MAP.items():
            patch_keys[f'CONFIG_RAM_{k}'.upper()] = 'y' if ramkb == k else 'n'
    if found['dev']:
        for k, v in REVERSE_DEV_MAP.items():
            patch_keys[f'CONFIG_DEV_{k}'.upper()] = 'y' if dev == k else 'n'
    if found['cpuclk']:
        for k, v in REVERSE_CPUCLK_MAP.items():
            patch_keys[f'CONFIG_CPUCLK_{k}'.upper()] = 'y' if cpuclk == k else 'n'

    # RAM-Disk: Aus bios.mac extrahieren und Mapping auf CONFIG_RAMDISK_*
    # Nur wenn alle Werte (oss, em256, mkd256, raf, rna) gefunden wurden
    if all(v is not None for v in ramdisk_vals.values()):
        # Finde das passende Mapping
        ramdisk_config = None
        for k, v in RAMDISK_MAP.items():
            if all(str(ramdisk_vals[key]) == str(val) for key, val in v.items()):
                ramdisk_config = k
                break
        # Setze alle RAMDISK-Optionen
        for k in RAMDISK_MAP.keys():
            patch_keys[f'CONFIG_{k}'] = 'y' if k == ramdisk_config else 'n'

    # 2. Bestehende .config einlesen und Zeilen gezielt ersetzen
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
                # Schreibe Wert im Kconfig-Stil
                if patch_keys[key] == 'y':
                    new_lines.append(f'{key}=y\n')
                else:
                    new_lines.append(f'# {key} is not set\n')
                seen_keys.add(key)
                continue
        new_lines.append(line)
    # 3. Fehlende Keys am Ende ergänzen
    for key, val in patch_keys.items():
        if key not in seen_keys:
            if val == 'y':
                new_lines.append(f'{key}=y\n')
            else:
                new_lines.append(f'# {key} is not set\n')
    # 4. Schreibe neue .config
    with open(config_path, 'w') as f:
        f.writelines(new_lines)


def patch_bios_mac(bios_path, config_path):
    """Patches bios.mac gemäß .config"""
    # Lese Auswahl aus .config
    chosen = {}
    cpu = fdc = crt = ramkb = dev = cpuclk = None
    ramdisk_choice = None
    with open(config_path) as f:
        for line in f:
            m = re.match(r'CONFIG_DRIVE_([A-D])_([0-9]+)=(y|n)', line)
            if m and m.group(3) == 'y':
                chosen[m.group(1)] = m.group(2)
            m = re.match(r'CONFIG_CPU_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                cpu = CPU_MAP.get('CPU_' + m.group(1))
            m = re.match(r'CONFIG_FDC_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                fdc = FDC_MAP.get('FDC_' + m.group(1))
            m = re.match(r'CONFIG_CRT_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                crt = CRT_MAP.get('CRT_' + m.group(1))
            m = re.match(r'CONFIG_RAM_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                ramkb = RAM_MAP.get('RAM_' + m.group(1))
            m = re.match(r'CONFIG_DEV_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                dev = DEV_MAP.get('DEV_' + m.group(1))
            m = re.match(r'CONFIG_CPUCLK_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                cpuclk = CPUCLK_MAP.get('CPUCLK_' + m.group(1))
            m = re.match(r'CONFIG_RAMDISK_(\w+)=(y|n)', line)
            if m and m.group(2) == 'y':
                ramdisk_choice = 'RAMDISK_' + m.group(1)
    # Patch bios.mac
    out = []
    # Patterns for hardware config lines (preserve comments)
    hw_patterns = {
        'cpu':   (re.compile(r'^(cpu\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), cpu),
        'fdc':   (re.compile(r'^(fdc\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), fdc),
        'crt':   (re.compile(r'^(crt\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), crt),
        'ramkb': (re.compile(r'^(ramkb\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), ramkb),
        'dev':   (re.compile(r'^(dev\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), dev),
        'cpuclk':(re.compile(r'^(cpuclk\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), cpuclk),
        # RAM-Disk Optionen
        'oss':   (re.compile(r'^(oss\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), None),
        'em256': (re.compile(r'^(em256\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), None),
        'mkd256':(re.compile(r'^(mkd256\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), None),
        'raf':   (re.compile(r'^(raf\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), None),
        'rna':   (re.compile(r'^(rna\s+equ\s+)(\w+)(.*)$', re.IGNORECASE), None),
    }
    # Werte für RAM-Disk aus Kconfig übernehmen
    ramdisk_vals = None
    if ramdisk_choice and ramdisk_choice in RAMDISK_MAP:
        ramdisk_vals = RAMDISK_MAP[ramdisk_choice]
    with open(bios_path, 'r', newline='') as f:
        for line in f:
            l = line.rstrip('\r\n')
            # Robustly match diskA..diskD lines, preserving comments and formatting
            m_drive = re.match(r'^(disk([A-D])\s+equ\s+)([0-9]+)(.*)$', l, re.IGNORECASE)
            if m_drive:
                drv = m_drive.group(2).upper()
                orig_val = m_drive.group(3)
                rest = m_drive.group(4)
                # Use value from .config if present, else keep original
                val = chosen.get(drv, orig_val)
                out.append(f'{m_drive.group(1)}{val}{rest}\r\n')
                continue
            replaced = False
            for key, (pat, value) in hw_patterns.items():
                m_hw = pat.match(l)
                # RAM-Disk: Wert aus Mapping nehmen
                if key in ('oss','em256','mkd256','raf','rna') and m_hw and ramdisk_vals is not None:
                    out.append(f"{m_hw.group(1)}{ramdisk_vals[key]}{m_hw.group(3)}\r\n")
                    replaced = True
                    break
                elif m_hw and value is not None:
                    out.append(f"{m_hw.group(1)}{value}{m_hw.group(3)}\r\n")
                    replaced = True
                    break
            if not replaced:
                out.append(l + '\r\n')
    with open(bios_path, 'w', newline='') as f:
        f.writelines(out)


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
                        if line.strip().startswith(f'{key}=y'):
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
