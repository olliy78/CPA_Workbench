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
    found = { 'cpu': False, 'fdc': False, 'crt': False, 'ramkb': False, 'dev': False, 'cpuclk': False }
    with open(bios_path) as f:
        for line in f:
            m = BIOS_PATTERN.match(line.strip())
            if m:
                drv = m.group(2)
                val = m.group(3)
                if val not in DRIVE_VALS:
                    val = '0'
                for v in DRIVE_VALS:
                    key = f'CONFIG_DRIVE_{drv}_{v}'
                    config[key] = 'y' if v == val else 'n'
            # Hardwarevariante
            l = line.strip().lower()
            if l.startswith('cpu\tequ'):
                cpu = l.split()[-1]
                found['cpu'] = True
            if l.startswith('fdc\tequ'):
                fdc = l.split()[-1]
                found['fdc'] = True
            if l.startswith('crt\tequ'):
                crt = l.split()[-1]
                found['crt'] = True
            if l.startswith('ramkb\tequ'):
                ramkb = l.split()[-1]
                found['ramkb'] = True
            if l.startswith('dev\tequ'):
                dev = l.split()[-1]
                found['dev'] = True
            if l.startswith('cpuclk\tequ'):
                cpuclk = l.split()[-1]
                found['cpuclk'] = True
    # Schreibe .config
    with open(config_path, 'w') as f:
        # Diskettenlaufwerke
        for drv in BIOS_DRIVES:
            for v in DRIVE_VALS:
                key = f'CONFIG_DRIVE_{drv}_{v}'
                if key in config:
                    f.write(f'{key}={config[key]}\n')
        # Hardwarevariante: nur schreiben, wenn in bios.mac gefunden
        if found['cpu']:
            for k, v in REVERSE_CPU_MAP.items():
                f.write(f'CONFIG_CPU_{k}={"y" if cpu==k else "n"}\n')
        if found['fdc']:
            for k, v in REVERSE_FDC_MAP.items():
                f.write(f'CONFIG_FDC_{k}={"y" if fdc==k else "n"}\n')
        if found['crt']:
            for k, v in REVERSE_CRT_MAP.items():
                f.write(f'CONFIG_CRT_{k}={"y" if crt==k else "n"}\n')
        if found['ramkb']:
            for k, v in REVERSE_RAM_MAP.items():
                f.write(f'CONFIG_RAM_{k}={"y" if ramkb==k else "n"}\n')
        if found['dev']:
            for k, v in REVERSE_DEV_MAP.items():
                f.write(f'CONFIG_DEV_{k}={"y" if dev==k else "n"}\n')
        if found['cpuclk']:
            for k, v in REVERSE_CPUCLK_MAP.items():
                f.write(f'CONFIG_CPUCLK_{k}={"y" if cpuclk==k else "n"}\n')


def patch_bios_mac(bios_path, config_path):
    """Patches bios.mac gemäß .config"""
    # Lese Auswahl aus .config
    chosen = {}
    cpu = fdc = crt = ramkb = dev = cpuclk = None
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
    # Patch bios.mac
    out = []
    with open(bios_path, 'r', newline='') as f:
        for line in f:
            l = line.strip().lower()
            m = BIOS_PATTERN.match(l)
            if m:
                drv = m.group(2)
                val = chosen.get(drv, m.group(3))
                out.append(f'disk{drv}\tequ\t{val}\r\n')
            elif l.startswith('cpu\tequ') and cpu:
                out.append(f'cpu\tequ\t{cpu}\r\n')
            elif l.startswith('fdc\tequ') and fdc:
                out.append(f'fdc\tequ\t{fdc}\r\n')
            elif l.startswith('crt\tequ') and crt:
                out.append(f'crt\tequ\t{crt}\r\n')
            elif l.startswith('ramkb\tequ') and ramkb:
                out.append(f'ramkb\tequ\t{ramkb}\r\n')
            elif l.startswith('dev\tequ') and dev:
                out.append(f'dev\tequ\t{dev}\r\n')
            elif l.startswith('cpuclk\tequ') and cpuclk:
                out.append(f'cpuclk\tequ\t{cpuclk}\r\n')
            else:
                # Stelle sicher, dass alle Zeilen mit CRLF enden
                l2 = line.rstrip('\r\n')
                out.append(l2 + '\r\n')
    with open(bios_path, 'w', newline='') as f:
        f.writelines(out)


def main():
    if len(sys.argv) < 3:
        print("Usage: config_bios_drives.py bios.mac .config [extract|patch]")
        sys.exit(1)
    bios_path = sys.argv[1]
    config_path = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'extract'
    if mode == 'extract':
        extract_bios_config(bios_path, config_path)
    elif mode == 'patch':
        patch_bios_mac(bios_path, config_path)
    else:
        print("Unknown mode")
        sys.exit(1)

if __name__ == "__main__":
    main()
