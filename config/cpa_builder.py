#!/usr/bin/env python3
# Copyright (c) 2025 by olliy78
# SPDX-License-Identifier: MIT
"""
Build-Engine für das CP/A Workbench Projekt.

Ersetzt alle Makefiles durch reines Python. Steuert:
  - Assemblierung mit M80 (via CPM-Emulator / Wine)
  - Linken mit LINKMT
  - Erzeugung von Diskettenimages (IMG, HFE, SCP)
  - Schreiben auf physikalische Laufwerke

Die Build-Engine arbeitet plattformübergreifend (Linux mit Wine, Windows nativ).
"""

import os
import re
import sys
import glob
import shutil
import platform
import subprocess


class CPABuilder:
    """Build-Engine für das CP/A Betriebssystem."""

    # Konstanten
    BUILD_DIR = 'build'
    ADDITIONS_DIR = 'additions'
    TOOLS_DIR = 'tools'
    GW_CMD = 'gw'
    CFG_FILE = 'cpaFormates.cfg'

    # Default Diskettenformat
    DEFAULT_FORMAT = 'cpa780'
    DEFAULT_IMAGE_SIZE = 780
    DEFAULT_DISKDEF = 'cpa780_withoutBoot'

    def __init__(self, project_dir, log_callback=None):
        """
        Args:
            project_dir: Absoluter Pfad zum Projektverzeichnis
            log_callback: Optionale Funktion für Log-Ausgaben (z.B. GUI-Log)
        """
        self.project_dir = project_dir
        self.log_callback = log_callback or (lambda msg: print(msg))
        self._setup_platform()

    def _setup_platform(self):
        """Plattformspezifische Pfade und Kommandos ermitteln."""
        is_linux = platform.system() == 'Linux'
        tools = os.path.join(self.project_dir, self.TOOLS_DIR)

        if is_linux:
            self.cpm_cmd = ['wine', 'cpm.exe']
            self.cpmcp = os.path.join(tools, 'cpmcp')
            self.cpmls = os.path.join(tools, 'cpmls')
        else:
            self.cpm_cmd = ['cpm.exe']
            self.cpmcp = os.path.join(tools, 'cpmcp.exe')
            self.cpmls = os.path.join(tools, 'cpmls.exe')

    def log(self, msg):
        """Log-Nachricht ausgeben."""
        self.log_callback(msg)

    def _run(self, cmd, cwd=None, check=True):
        """Externen Befehl ausführen und Ausgabe loggen."""
        cwd = cwd or self.project_dir
        self.log(f"  > {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                timeout=120, errors='replace'
            )
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    self.log(f"    {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    self.log(f"    {line}")
            if check and result.returncode != 0:
                raise RuntimeError(
                    f"Befehl fehlgeschlagen (exit {result.returncode}): {' '.join(cmd)}"
                )
            return result
        except FileNotFoundError:
            raise RuntimeError(f"Programm nicht gefunden: {cmd[0]}")

    # --- Konfigurationsdatei ---

    @staticmethod
    def load_config(config_path):
        """
        .config-Datei lesen und als Dict zurückgeben.
        Format: CONFIG_KEY=value oder # CONFIG_KEY is not set
        """
        config = {}
        if not os.path.exists(config_path):
            return config
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'^(CONFIG_\w+)=(.+)$', line)
                if m:
                    key, val = m.group(1), m.group(2)
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    config[key] = val
                    continue
                m = re.match(r'^# (CONFIG_\w+) is not set$', line)
                if m:
                    config[m.group(1)] = None
        return config

    @staticmethod
    def save_config(config, config_path):
        """
        Dict als .config-Datei schreiben.
        Sortiert nach Präfix: VARIANT_, SYSTEM_, BUILD_
        """
        # Sortierung: VARIANT zuerst, dann SYSTEM, dann BUILD, dann Rest
        def sort_key(key):
            if 'VARIANT_' in key:
                return (0, key)
            if 'SYSTEM_' in key:
                return (1, key)
            if 'BUILD_' in key:
                return (2, key)
            return (3, key)

        with open(config_path, 'w', encoding='utf-8') as f:
            for key in sorted(config.keys(), key=sort_key):
                val = config[key]
                if val is None:
                    f.write(f"# {key} is not set\n")
                elif val == 'y' or val == 'n':
                    f.write(f"{key}={val}\n")
                else:
                    f.write(f'{key}="{val}"\n')

    # --- Systemvariante ---

    def get_variant(self, config):
        """Gewählte Systemvariante aus Config-Dict ermitteln."""
        for key, val in config.items():
            if key.startswith('CONFIG_VARIANT_') and val == 'y':
                return key[len('CONFIG_VARIANT_'):]
        return None

    def get_available_variants(self):
        """Alle verfügbaren Systemvarianten aus src/ ermitteln."""
        src_dir = os.path.join(self.project_dir, 'src')
        variants = []
        if not os.path.isdir(src_dir):
            return variants
        for name in sorted(os.listdir(src_dir)):
            path = os.path.join(src_dir, name)
            if os.path.isdir(path):
                about = ''
                about_path = os.path.join(path, 'about.txt')
                if os.path.isfile(about_path):
                    with open(about_path, 'r', encoding='utf-8', errors='replace') as f:
                        about = f.read().strip()
                variants.append((name, about))
        return variants

    # --- Quell-Erkennung ---

    def detect_main_source(self, variant):
        """
        Haupt-Assemblerdatei für eine Variante erkennen (z.B. 'bios' oder 'biop').
        Prüft zuerst die Kconfig.system auf source= Einträge, dann Dateisystem.
        """
        # Methode 1: Kconfig.system parsen für source= Einträge
        kconfig_path = os.path.join(
            self.project_dir, 'config', variant, 'Kconfig.system'
        )
        if os.path.isfile(kconfig_path):
            sources = {}
            with open(kconfig_path, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.search(r'source=(\S+)', line.strip())
                    if m:
                        src = m.group(1)
                        sources[src] = sources.get(src, 0) + 1
            if sources:
                # Häufigste Quelldatei ist die Hauptdatei
                main_src = max(sources, key=sources.get)
                return main_src.replace('.mac', '')

        # Methode 2: Dateisystem prüfen (case-insensitive)
        src_dir = os.path.join(self.project_dir, 'src', variant)
        if os.path.isdir(src_dir):
            files_lower = {f.lower(): f for f in os.listdir(src_dir)}
            # biop hat Priorität vor bios
            for target in ['biop.mac', 'bios.mac']:
                if target in files_lower:
                    return target.replace('.mac', '')
        return None

    # --- Build-Pfade ---

    def _paths(self, variant):
        """Alle relevanten Pfade für einen Build ermitteln."""
        return {
            'build_dir': os.path.join(self.project_dir, self.BUILD_DIR),
            'src_dir': os.path.join(self.project_dir, 'src', variant),
            'src_common': os.path.join(self.project_dir, 'src'),
            'prebuilt_dir': os.path.join(self.project_dir, 'prebuilt', variant),
            'config_dir': os.path.join(self.project_dir, 'config', variant),
            'additions_dir': os.path.join(self.project_dir, self.ADDITIONS_DIR),
            'tools_dir': os.path.join(self.project_dir, self.TOOLS_DIR),
            'os_target': os.path.join(self.project_dir, self.BUILD_DIR, '@os.com'),
            'bootsector': os.path.join(self.project_dir, 'prebuilt', variant, 'bootsec.bin'),
        }

    # --- Disk-Format ---

    def _get_disk_format(self, config):
        """Diskettenformat aus Config ermitteln."""
        if config.get('CONFIG_BUILD_DISKTYPE_800K') == 'y':
            return 'cpa800', 800, 'cpa800'
        return 'cpa780', 780, 'cpa780_withoutBoot'

    # --- Patch-Integration ---

    def run_patch_mac(self, config_path, variant, mode):
        """patch_mac.py im Modus 'extract' oder 'patch' ausführen."""
        script = os.path.join(self.project_dir, 'config', 'patch_mac.py')
        if not os.path.isfile(script):
            self.log(f"[WARNUNG] patch_mac.py nicht gefunden: {script}")
            return
        self.log(f"[INFO] patch_mac.py {mode} für {variant}")
        self._run([sys.executable, script, mode, config_path, variant])

    # --- Clean ---

    def clean(self):
        """Build-Verzeichnis aufräumen."""
        build_dir = os.path.join(self.project_dir, self.BUILD_DIR)
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir, exist_ok=True)
        self.log("[INFO] Aufräumen abgeschlossen.")

    # --- OS bauen ---

    def build_os(self, config):
        """
        Betriebssystem @OS.COM bauen.
        Entspricht dem os-Target des Makefiles.
        """
        variant = self.get_variant(config)
        if not variant:
            raise RuntimeError("Keine Systemvariante gewählt!")

        main_src = self.detect_main_source(variant)
        if not main_src:
            raise RuntimeError(
                f"Keine Haupt-Quelldatei (bios.mac/biop.mac) für Variante '{variant}' gefunden!"
            )

        paths = self._paths(variant)
        build_dir = paths['build_dir']
        os.makedirs(build_dir, exist_ok=True)

        # STEP 1: .mac-Dateien kopieren (gemeinsame + variantenspezifische)
        self.log("[STEP 1] Kopiere .mac-Dateien nach build/")
        for mac in glob.glob(os.path.join(paths['src_common'], '*.mac')):
            shutil.copy2(mac, build_dir)
        for mac in glob.glob(os.path.join(paths['src_dir'], '*.mac')):
            shutil.copy2(mac, build_dir)
        # Auch variantenspezifische .mac mit Großbuchstaben kopieren
        for mac in glob.glob(os.path.join(paths['src_dir'], '*.MAC')):
            dst = os.path.join(build_dir, os.path.basename(mac).lower())
            shutil.copy2(mac, dst)

        # STEP 2: ERL-Dateien aus prebuilt kopieren
        self.log("[STEP 2] Kopiere ERL-Dateien aus prebuilt/")
        for erl in glob.glob(os.path.join(paths['prebuilt_dir'], '*.erl')):
            shutil.copy2(erl, build_dir)
        for erl in glob.glob(os.path.join(paths['prebuilt_dir'], '*.ERL')):
            dst = os.path.join(build_dir, os.path.basename(erl).lower())
            if not os.path.exists(dst):
                shutil.copy2(erl, dst)

        # STEP 3: Tools kopieren
        self.log("[STEP 3] Kopiere Build-Tools nach build/")
        for tool in ['m80.com', 'linkmt.com', 'cpm.exe']:
            src = os.path.join(paths['tools_dir'], tool)
            if os.path.isfile(src):
                shutil.copy2(src, build_dir)

        # STEP 4: Assemblieren mit M80 (Listing erzeugen)
        self.log("[STEP 4] Assemblieren mit M80")
        result = self._run(
            self.cpm_cmd + ['m80', f'={main_src}/L'],
            cwd=build_dir, check=False
        )

        # STEP 5: Assemblieren (ERL erzeugen)
        self.log(f"[STEP 5] Assembliere {main_src}.erl")
        self._run(
            self.cpm_cmd + ['m80', f'{main_src}.erl={main_src}'],
            cwd=build_dir
        )

        # STEP 6: /p:-Wert aus Assembler-Ausgabe extrahieren und Linken
        asm_output = (result.stdout or '') + (result.stderr or '')
        p_value = self._extract_p_value(asm_output)
        if not p_value:
            raise RuntimeError("Kein /p:-Wert in der M80-Ausgabe gefunden!")
        self.log(f"[STEP 6] Linken mit /p:{p_value}")
        self._run(
            self.cpm_cmd + ['linkmt', f'@OS=cpabas,ccp,bdos,{main_src}/p:{p_value}'],
            cwd=build_dir
        )

        # STEP 7: Temporäre Dateien aufräumen
        self.log("[STEP 7] Aufräumen temporärer Dateien")
        for pattern in ['*.syp', '*.rel', '*.mac', '*.MAC', '*.erl',
                        'cpm.exe', 'm80.com', 'linkmt.com']:
            for f in glob.glob(os.path.join(build_dir, pattern)):
                basename = os.path.basename(f).lower()
                if basename != '@os.com':
                    os.remove(f)

        self.log("[FERTIG] @OS.COM wurde erfolgreich erzeugt.")

    @staticmethod
    def _extract_p_value(asm_output):
        """
        /p:-Linkwert direkt aus der M80-Assembler-Ausgabe extrahieren.
        Sucht nach '/p:' gefolgt vom Hex-Wert.
        Steuerzeichen (z.B. Backspace \x08) zwischen /p: und dem Wert werden toleriert.
        """
        # Steuerzeichen (0x00-0x1F außer \n\r\t) entfernen
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', asm_output)
        m = re.search(r'/p:\s*([0-9A-Fa-f]{4,})', cleaned)
        return m.group(1) if m else None

    # --- Diskettenimage ---

    def build_diskimage(self, config):
        """
        Diskettenimage erstellen (IMG-Format).
        Entspricht dem diskimage-Target des Makefiles.
        """
        variant = self.get_variant(config)
        if not variant:
            raise RuntimeError("Keine Systemvariante gewählt!")

        paths = self._paths(variant)
        fmt, size, diskdef = self._get_disk_format(config)
        build_dir = paths['build_dir']
        tmp_image = os.path.join(build_dir, 'cpadisk.img.tmp')
        final_image = os.path.join(build_dir, 'cpadisk.img')
        bootsector = paths['bootsector']
        os_target = paths['os_target']

        if not os.path.isfile(os_target):
            raise RuntimeError("@OS.COM nicht gefunden! Zuerst 'os' bauen.")

        # STEP 1: Leeres Image erzeugen (mit 0xE5 gefüllt)
        self.log(f"[STEP 1] Erzeuge leeres Image ({size}k, Format: {fmt})")
        data = bytes([0xE5]) * (size * 1024)
        with open(tmp_image, 'wb') as f:
            f.write(data)

        if fmt == 'cpa800' and os.path.isfile(bootsector):
            # Pseudo-Bootblock am Anfang der Dateizuordnungstabelle
            self.log("[STEP 1b] Erzeuge pseudo-Bootblock")
            with open(bootsector, 'rb') as bs:
                boot_data = bs.read(32)
            with open(tmp_image, 'r+b') as f:
                f.write(boot_data)

        # STEP 2: @os.com ins Image kopieren
        self.log(f"[STEP 2] Kopiere @os.com ins Image (Format: {fmt})")
        self._run([self.cpmcp, '-f', diskdef, tmp_image, os_target, '0:@os.com'])

        if fmt == 'cpa800' and os.path.isfile(bootsector):
            # Spur 0 bootfähig machen
            self.log("[STEP 2b] Fixe Spur 0 für Bootfähigkeit")
            with open(bootsector, 'rb') as bs:
                boot_data = bs.read(128)  # 4 × 32 bytes
            with open(tmp_image, 'r+b') as f:
                f.write(boot_data)

        # STEP 3: Dateien aus additions/ kopieren
        additions_sys = os.path.join(paths['additions_dir'], variant)
        if os.path.isdir(additions_sys):
            self.log(f"[STEP 3a] Kopiere Dateien aus 'additions/{variant}'")
            for fname in sorted(os.listdir(additions_sys)):
                fpath = os.path.join(additions_sys, fname)
                if os.path.isfile(fpath):
                    self.log(f"  [ADD] {fname} (system-specifisch)")
                    self._run([self.cpmcp, '-f', diskdef, tmp_image, fpath, f'0:{fname}'])

        self.log(f"[STEP 3b] Kopiere Dateien aus 'additions/'")
        for fname in sorted(os.listdir(paths['additions_dir'])):
            fpath = os.path.join(paths['additions_dir'], fname)
            if os.path.isfile(fpath):
                self.log(f"  [ADD] {fname}")
                self._run([self.cpmcp, '-f', diskdef, tmp_image, fpath, f'0:{fname}'])

        # STEP 4: Dateien im Image anzeigen
        self.log("[STEP 4] Dateien im Image:")
        self._run([self.cpmls, '-Ff', diskdef, tmp_image])

        # STEP 5: Bootsektor behandeln
        if fmt == 'cpa780' and os.path.isfile(bootsector):
            self.log(f"[STEP 5] Füge Bootsektor aus {os.path.basename(bootsector)} hinzu")
            with open(bootsector, 'rb') as bs:
                boot_data = bs.read()
            with open(tmp_image, 'rb') as tmp:
                image_data = tmp.read()
            with open(final_image, 'wb') as out:
                out.write(boot_data)
                out.write(image_data)
        elif fmt == 'cpa780':
            self.log("[WARNUNG] Bootsektor nicht gefunden!")
            shutil.copy2(tmp_image, final_image)
        else:
            self.log("[STEP 5] Bootsektor nicht nötig (im Image enthalten)")
            shutil.copy2(tmp_image, final_image)

        # Aufräumen
        if os.path.isfile(tmp_image):
            os.remove(tmp_image)
        self.log(f"[DONE] Diskettenimage erstellt: {final_image}")

    # --- HFE/SCP-Image ---

    def build_hfe_image(self, config):
        """Diskettenimage in HFE-Format konvertieren."""
        build_dir = os.path.join(self.project_dir, self.BUILD_DIR)
        final_image = os.path.join(build_dir, 'cpadisk.img')
        hfe_image = os.path.join(build_dir, 'cpadisk.hfe')
        cfg_file = os.path.join(self.project_dir, self.CFG_FILE)
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(final_image):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log(f"[STEP] Konvertiere nach HFE (Format: {fmt})")
        self._run([
            self.GW_CMD, 'convert',
            f'--diskdefs={cfg_file}', f'--format={fmt}',
            final_image, hfe_image
        ])
        self.log(f"[DONE] HFE-Image erstellt: {hfe_image}")

    def build_scp_image(self, config):
        """Diskettenimage in SCP-Format konvertieren."""
        build_dir = os.path.join(self.project_dir, self.BUILD_DIR)
        final_image = os.path.join(build_dir, 'cpadisk.img')
        scp_image = os.path.join(build_dir, 'cpadisk.scp')
        cfg_file = os.path.join(self.project_dir, self.CFG_FILE)
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(final_image):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log(f"[STEP] Konvertiere nach SCP (Format: {fmt})")
        self._run([
            self.GW_CMD, 'convert',
            f'--diskdefs={cfg_file}', f'--format={fmt}',
            final_image, scp_image
        ])
        self.log(f"[DONE] SCP-Image erstellt: {scp_image}")

    def write_image(self, config):
        """Diskettenimage auf physikalisches Laufwerk schreiben."""
        build_dir = os.path.join(self.project_dir, self.BUILD_DIR)
        final_image = os.path.join(build_dir, 'cpadisk.img')
        cfg_file = os.path.join(self.project_dir, self.CFG_FILE)
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(final_image):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log("[STEP] Schreibe Diskettenimage auf Laufwerk")
        self._run([
            self.GW_CMD, 'write',
            f'--diskdefs={cfg_file}', f'--format={fmt}',
            final_image
        ])
        self.log("[DONE] Diskettenimage auf Laufwerk geschrieben.")

    # --- Gesamt-Build ---

    def build(self, target, config):
        """
        Vollständigen Build für ein bestimmtes Target ausführen.

        Args:
            target: 'os', 'diskimage', 'diskimagehfe', 'diskimagescp', 'writeimage'
            config: Config-Dict
        """
        self.log(f"[START] Build-Target: {target}")

        if target in ('os', 'diskimage', 'diskimagehfe', 'diskimagescp', 'writeimage'):
            self.build_os(config)

        if target in ('diskimage', 'diskimagehfe', 'diskimagescp', 'writeimage'):
            self.build_diskimage(config)

        if target == 'diskimagehfe':
            self.build_hfe_image(config)

        if target == 'diskimagescp':
            self.build_scp_image(config)

        if target == 'writeimage':
            self.write_image(config)

        self.log(f"[ENDE] Build-Target '{target}' abgeschlossen.")
