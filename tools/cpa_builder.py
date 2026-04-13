#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
cpa_builder.py - Build-Engine für das CP/A Betriebssystem

Dieses Modul bildet den Kern des Build-Systems und ersetzt sämtliche Makefiles
durch reines Python. Es steuert den gesamten Build-Prozess:

  - Assemblierung der Z80-Quellen mit M80 (via cparun CP/M-Emulator)
  - Linken der erzeugten ERL-Module mit LINKMT zu @OS.COM
  - Erzeugung von Diskettenimages (IMG-Format, gefüllt mit 0xE5)
  - Konvertierung in HFE- und SCP-Formate (via Greaseweazle)
  - Schreiben auf physikalische Diskettenlaufwerke (via Greaseweazle)

Die Build-Engine arbeitet plattformübergreifend:
  - Linux: M80/LINKMT werden über cparun (eigener CP/M-Emulator) ausgeführt
  - Windows: M80/LINKMT laufen über cparun.exe

Die Klasse CPABuilder wird von der GUI (cpa_workbench.py) instanziiert und
über einen Log-Callback mit der Oberfläche verbunden.

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)
"""

import os
import re
import sys
import glob
import shutil
import venv
import platform
import subprocess


# ============================================================================
# CPABuilder - Zentrale Build-Engine
# ============================================================================

class CPABuilder:
    """Build-Engine für das CP/A Betriebssystem.

    Verwaltet den gesamten Build-Prozess von der Assemblierung über
    das Linken bis zur Image-Erzeugung. Alle Pfade werden relativ zum
    Projektverzeichnis verwaltet; absolute Pfade werden nur für
    Datei-I/O-Operationen (open, copy, exists) verwendet.
    """

    # Verzeichnis-Konstanten (relativ zum Projektverzeichnis)
    BUILD_DIR = 'build'               # Ausgabeverzeichnis für Build-Artefakte
    ADDITIONS_DIR = 'additions'        # Zusätzliche Dateien für die Diskette
    TOOLS_DIR = 'tools'                # cparun, cpmcp, cpmls, m80.com, linkmt.com
    GW_VERSION        = '1.23'
    GW_INSTALL_URL    = 'git+https://github.com/keirf/greaseweazle@latest'
    GW_WIN64_ZIP_URL  = f'https://github.com/keirf/greaseweazle/releases/download/v{GW_VERSION}/greaseweazle-{GW_VERSION}-win64.zip'
    GW_WIN64_EXE_PATH = f'greaseweazle-{GW_VERSION}/gw.exe'  # Pfad der exe im ZIP
    CFG_FILE = 'cpaFormates.cfg'       # Greaseweazle-Formatdefinitionen

    # Vorgabe-Diskettenformat (780k ohne separaten Bootsektor)
    DEFAULT_FORMAT = 'cpa780'
    DEFAULT_IMAGE_SIZE = 780
    DEFAULT_DISKDEF = 'cpa780_withoutBoot'

    # Bootsektor-Quellen (nach tools/bootsec verschoben)
    BOOTSEC_SRC_DIR = os.path.join('tools', 'bootsec', 'src')
    BOOTSEC_PREBUILT_FIXED = os.path.join('prebuilt', 'bc_a5120', 'bootsec.bin')

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
        """Plattformspezifische Pfade und Kommandos ermitteln.

        M80/LINKMT werden über cparun (eigener CP/M-Emulator) ausgeführt.
        cpmtools (cpmcp/cpmls) befinden sich im tools/-Verzeichnis.
        """
        is_linux = platform.system() == 'Linux'

        if is_linux:
            self.cparun = os.path.join('tools', 'cparun')
            self.cpmcp = os.path.join('tools', 'cpmcp')
            self.cpmls = os.path.join('tools', 'cpmls')
        else:
            self.cparun = os.path.join('tools', 'cparun.exe')
            self.cpmcp = os.path.join('tools', 'cpmcp.exe')
            self.cpmls = os.path.join('tools', 'cpmls.exe')

        self.gw_cmd = None  # Wird bei Bedarf durch _ensure_gw() gesetzt

    def _ensure_gw(self):
        """Greaseweazle (gw) sicherstellen.

        Prüft in drei Schritten:
        1. gw im System-PATH vorhanden?
        2. gw im lokalen .venv/Scripts/ (Windows) bzw. .venv/bin/ (Linux) vorhanden?
        3. Falls nicht: Auf Windows direkt das offizielle win64-Binär-ZIP herunterladen
           und gw.exe extrahieren (kein pip, kein git nötig). Auf Linux/macOS wird
           Greaseweazle per pip aus dem Git-Repository installiert.

        Nach erfolgreicher Prüfung/Installation wird self.gw_cmd gesetzt.
        """
        if self.gw_cmd:
            return

        # 1. System-PATH prüfen (gw global installiert?)
        if shutil.which('gw'):
            self.gw_cmd = 'gw'
            self.log("[INFO] Greaseweazle gefunden: gw (System)")
            return

        # 2. Bereits vorhandene lokale Installation prüfen
        venv_dir = os.path.join(self.project_dir, '.venv')
        if platform.system() == 'Windows':
            gw_venv = os.path.join(venv_dir, 'greaseweazle', 'gw.exe')
        else:
            gw_venv = os.path.join(venv_dir, 'bin', 'gw')

        if os.path.isfile(gw_venv):
            self.gw_cmd = gw_venv
            self.log(f"[INFO] Greaseweazle gefunden: {gw_venv}")
            return

        # 3. Installation
        self.log("[INFO] Greaseweazle nicht gefunden – wird automatisch installiert ...")
        os.makedirs(os.path.dirname(gw_venv), exist_ok=True)

        if platform.system() == 'Windows':
            # Auf Windows: Offizielles Binär-ZIP herunterladen und vollständig
            # entpacken. gw.exe benötigt python311.dll und weitere DLLs aus dem
            # Paket – nur die exe allein genügt nicht.
            import urllib.request
            import zipfile
            import tempfile
            gw_dir = os.path.join(venv_dir, 'greaseweazle')
            self.log(f"[STEP] Lade Greaseweazle {self.GW_VERSION} herunter ...")
            self.log(f"  > {self.GW_WIN64_ZIP_URL}")
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                urllib.request.urlretrieve(self.GW_WIN64_ZIP_URL, tmp_path)
                with zipfile.ZipFile(tmp_path) as zf:
                    # Alle Einträge in gw_dir entpacken, dabei das ZIP-Unterverzeichnis
                    # (greaseweazle-X.Y/) abschneiden
                    prefix = f'greaseweazle-{self.GW_VERSION}/'
                    for entry in zf.infolist():
                        if not entry.filename.startswith(prefix):
                            continue
                        rel = entry.filename[len(prefix):]
                        if not rel:  # Verzeichnis-Eintrag selbst
                            continue
                        dest = os.path.join(gw_dir, rel)
                        if entry.is_dir():
                            os.makedirs(dest, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            with zf.open(entry) as src, open(dest, 'wb') as dst:
                                dst.write(src.read())
            finally:
                os.unlink(tmp_path)
        else:
            # Auf Linux/macOS: per pip aus dem Git-Repository installieren.
            venv.create(venv_dir, with_pip=True)
            pip_cmd = os.path.join(venv_dir, 'bin', 'pip')
            self.log("[STEP] Installiere Greaseweazle via pip ...")
            self._run([pip_cmd, 'install', self.GW_INSTALL_URL])

        if not os.path.isfile(gw_venv):
            raise RuntimeError(
                "Greaseweazle-Installation fehlgeschlagen. "
                f"Bitte manuell installieren: pip install {self.GW_INSTALL_URL}"
            )

        self.gw_cmd = gw_venv
        self.log(f"[DONE] Greaseweazle installiert: {gw_venv}")

    def log(self, msg):
        """Log-Nachricht ausgeben."""
        self.log_callback(msg)

    def _run(self, cmd, cwd=None, check=True, timeout=120, stream=False):
        """Externen Befehl ausführen, Ausgabe loggen und optional Fehler werfen.

        Args:
            cmd: Befehl als Liste (z.B. ['tools/cparun', 'm80', ...])
                 cparun-Aufrufe benötigen kein '-dir'-Argument mehr – das
                 Arbeitsverzeichnis wird über den cwd-Parameter gesetzt.
            cwd: Arbeitsverzeichnis (Standard: self.project_dir)
            check: Bei True wird bei Rückgabewert != 0 ein RuntimeError geworfen
            timeout: Timeout in Sekunden (Standard: 120, None = kein Timeout)
            stream: Bei True wird die Ausgabe via Popen live angezeigt (kein Timeout).
                    stdout und stderr werden zusammengeführt – geeignet für
                    lange laufende Befehle wie 'gw write' (Diskette schreiben).
        Returns:
            subprocess.CompletedProcess Objekt mit stdout/stderr
        """
        cwd = cwd or self.project_dir
        self.log(f"  > {' '.join(cmd)}")
        try:
            if stream:
                # Streaming-Modus: Ausgabe Zeile für Zeile in Echtzeit anzeigen.
                # stderr wird nach stdout umgeleitet (gw schreibt Fortschritt auf stderr).
                # Kein Timeout – Befehl läuft bis zum natürlichen Ende.
                with subprocess.Popen(
                    cmd, cwd=cwd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, errors='replace', bufsize=1
                ) as proc:
                    for line in proc.stdout:
                        line = line.rstrip('\r\n')
                        if line:
                            self.log(f"    {line}")
                    returncode = proc.wait()
                if check and returncode != 0:
                    raise RuntimeError(
                        f"Befehl fehlgeschlagen (exit {returncode}): {' '.join(cmd)}"
                    )
                return subprocess.CompletedProcess(cmd, returncode, '', '')
            else:
                result = subprocess.run(
                    cmd, cwd=cwd, capture_output=True, text=True,
                    timeout=timeout, errors='replace'
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
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout nach {timeout}s: {' '.join(cmd)}")

    # -----------------------------------------------------------------------
    # Konfigurationsdatei - .config im Kconfig-Format lesen/schreiben
    # -----------------------------------------------------------------------

    @staticmethod
    def load_config(config_path):
        """Konfigurationsdatei (.config) lesen und als Dict zurückgeben.

        Erkennt zwei Formate:
        - CONFIG_KEY=value (aktive Option, bei Strings mit Anführungszeichen)
        - # CONFIG_KEY is not set (deaktivierte Option)
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
        """Config-Dict als .config-Datei schreiben.

        Sortierung: VARIANT_ zuerst, dann SYSTEM_, dann BUILD_, dann Rest.
        Werte None werden als '# CONFIG_KEY is not set' geschrieben.
        """
        # Sortierung: VARIANT zuerst (Variante), dann SYSTEM, dann BUILD, dann Rest
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

    # -----------------------------------------------------------------------
    # Systemvariante - Erkennung und Auswahl
    # -----------------------------------------------------------------------

    def get_variant(self, config):
        """Gewählte Systemvariante aus Config-Dict ermitteln (z.B. 'bc_a5120')."""
        for key, val in config.items():
            if key.startswith('CONFIG_VARIANT_') and val == 'y':
                return key[len('CONFIG_VARIANT_'):]
        return None

    def get_available_variants(self):
        """Alle verfügbaren Systemvarianten aus dem src/-Verzeichnis ermitteln.

        Jedes Unterverzeichnis in src/ ist eine Variante. Optional kann
        eine about.txt-Datei eine kurze Beschreibung enthalten.

        Returns:
            list: Liste von (name, about_text) Tupeln
        """
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

    # -----------------------------------------------------------------------
    # Quell-Erkennung - Haupt-Assembler-Datei identifizieren (bios/biop)
    # -----------------------------------------------------------------------

    def detect_main_source(self, variant):
        """Haupt-Assemblerdatei für eine Variante erkennen (z.B. 'bios' oder 'biop').

        Methode 1: Kconfig.system parsen - die häufigste source=-Datei ist die Hauptdatei.
        Methode 2: Dateisystem prüfen - biop.mac hat Priorität vor bios.mac.
        """
        # Methode 1: Kconfig.system parsen und häufigste source=-Datei suchen
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

        # Methode 2: Dateisystem durchsuchen (case-insensitive, biop vor bios)
        src_dir = os.path.join(self.project_dir, 'src', variant)
        if os.path.isdir(src_dir):
            files_lower = {f.lower(): f for f in os.listdir(src_dir)}
            # biop hat Priorität vor bios
            for target in ['biop.mac', 'bios.mac']:
                if target in files_lower:
                    return target.replace('.mac', '')
        return None

    # -----------------------------------------------------------------------
    # Build-Pfade und Diskettenformat
    # -----------------------------------------------------------------------

    def _abs(self, rel_path):
        """Relativen Pfad in absoluten Pfad umwandeln (für Datei-I/O-Operationen)."""
        return os.path.join(self.project_dir, rel_path)

    def _paths(self, variant):
        """Alle relevanten Build-Pfade für eine Variante ermitteln.

        Gibt ein Dict mit relativen Pfaden zurück (relativ zum Projektverzeichnis).
        Für Datei-I/O muss self._abs() verwendet werden.
        """
        return {
            'build_dir': self.BUILD_DIR,
            'src_dir': os.path.join('src', variant),
            'src_common': 'src',
            'prebuilt_dir': os.path.join('prebuilt', variant),
            'config_dir': os.path.join('config', variant),
            'additions_dir': self.ADDITIONS_DIR,
            'tools_dir': self.TOOLS_DIR,
            'os_target': os.path.join(self.BUILD_DIR, '@os.com'),
            # Fuer Diskettenbau immer die feste Prebuilt-Version verwenden
            'bootsector': self.BOOTSEC_PREBUILT_FIXED,
            'bootsector_prebuilt': os.path.join('prebuilt', variant, 'bootsec.bin'),
        }

    # --- Disk-Format ---

    def _get_disk_format(self, config):
        """Diskettenformat aus der Konfiguration ermitteln.

        Returns:
            tuple: (format_name, size_kb, diskdef_name)
            z.B. ('cpa800', 800, 'cpa800') oder ('cpa780', 780, 'cpa780_withoutBoot')
        """
        if config.get('CONFIG_BUILD_DISKTYPE_800K') == 'y':
            return 'cpa800', 800, 'cpa800'
        return 'cpa780', 780, 'cpa780_withoutBoot'

    # -----------------------------------------------------------------------
    # Bootsektor bauen - bootsec.bin ueber externes Skript erzeugen
    # -----------------------------------------------------------------------

    # Pfad zum Build-Skript (relativ zum Projektverzeichnis)
    BOOTSEC_BUILD_SCRIPT = os.path.join('tools', 'bootsec', 'build.py')

    def build_bootsec(self, config):
        """Bootsektor ueber tools/bootsec/build.py bauen.

        Das Build-Skript erzeugt bootsec.bin und aktualisiert
        prebuilt/bc_a5120/bootsec.bin.
        """
        variant = self.get_variant(config)
        if not variant:
            raise RuntimeError("Keine Systemvariante gewaehlt!")

        paths = self._paths(variant)
        build_abs = self._abs(paths['build_dir'])
        os.makedirs(build_abs, exist_ok=True)

        bootsec_out = self.BOOTSEC_PREBUILT_FIXED

        # Pruefen ob Quelldateien vorhanden sind
        src_dir = self._abs(self.BOOTSEC_SRC_DIR)
        has_sources = os.path.isdir(src_dir) and any(
            f.endswith('.mac') and f != 'bootsec.mac'
            for f in os.listdir(src_dir)
        )

        # --- Wenn keine Quellen vorhanden: ohne Build zurück ---
        if not has_sources:
            if os.path.isfile(self._abs(bootsec_out)):
                self.log(f"[INFO] Bootsektor bereits vorhanden: {bootsec_out}")
            else:
                self.log("[WARNUNG] Kein Bootsektor verfuegbar (Quelle fehlt und prebuilt/bc_a5120/bootsec.bin nicht vorhanden)")
            return

        # --- Aus Quelle bauen (externes Skript) ---
        self.log("[STEP] Bootsektor aus Quelle assemblieren (build.py)")

        script = self._abs(self.BOOTSEC_BUILD_SCRIPT)
        cmd = [
            sys.executable, script,
            '--build-dir', build_abs,
            '--project-dir', self.project_dir,
        ]

        self._run(cmd, cwd=self.project_dir, check=True)

        # Ergebnis pruefen
        if os.path.isfile(self._abs(bootsec_out)):
            size = os.path.getsize(self._abs(bootsec_out))
            self.log(f"    Bootsektor erzeugt: {bootsec_out} ({size} Bytes)")
        else:
            raise RuntimeError("build.py hat keine bootsec.bin erzeugt!")

    # --- Patch-Integration ---

    def run_patch_mac(self, config_path, variant, mode):
        """patch_mac.py im Modus 'extract' oder 'patch' als Unterprozess aufrufen.

        'extract': Liest aktuelle Werte aus den .mac-Dateien in die .config.
        'patch': Schreibt .config-Werte in die .mac-Dateien zurück.
        """
        script = os.path.join(self.project_dir, 'tools', 'patch_mac.py')
        if not os.path.isfile(script):
            self.log(f"[WARNUNG] patch_mac.py nicht gefunden: {script}")
            return
        self.log(f"[INFO] patch_mac.py {mode} für {variant}")
        self._run([sys.executable, script, mode, config_path, variant])

    # --- Clean ---

    def clean(self):
        """Build-Verzeichnis vollständig löschen und leer neu anlegen."""
        build_dir = os.path.join(self.project_dir, self.BUILD_DIR)
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir, exist_ok=True)
        self.log("[INFO] Aufräumen abgeschlossen.")

    # -----------------------------------------------------------------------
    # OS bauen - Z80-Assemblierung und Linken zu @OS.COM
    # -----------------------------------------------------------------------

    def _os_is_up_to_date(self, paths, os_target):
        """Prüft ob @OS.COM noch aktuell ist (wie Make: Ziel vs. Quelldateien).

        Vergleicht den Timestamp von build/@os.com mit allen relevanten
        Quelldateien in src/ und prebuilt/. Gibt True zurück wenn @os.com
        neuer ist als alle Quelldateien – ein Neu-Build ist dann nicht nötig.

        Geprüfte Quelldateien:
          - src/*.mac             (gemeinsame Quellen)
          - src/<variant>/*.mac   (variantenspezifische Quellen)
          - prebuilt/<variant>/*.erl  (vorkompilierte Module)
        """
        os_abs = self._abs(os_target)
        if not os.path.isfile(os_abs):
            return False
        os_mtime = os.path.getmtime(os_abs)

        source_patterns = [
            os.path.join(self._abs(paths['src_common']), '*.mac'),
            os.path.join(self._abs(paths['src_common']), '*.MAC'),
            os.path.join(self._abs(paths['src_dir']), '*.mac'),
            os.path.join(self._abs(paths['src_dir']), '*.MAC'),
            os.path.join(self._abs(paths['prebuilt_dir']), '*.erl'),
            os.path.join(self._abs(paths['prebuilt_dir']), '*.ERL'),
        ]
        for pattern in source_patterns:
            for src_file in glob.glob(pattern):
                if os.path.getmtime(src_file) > os_mtime:
                    self.log(f"  [NEU] {os.path.relpath(src_file, self.project_dir)}")
                    return False
        return True

    def build_os(self, config):
        """Betriebssystem @OS.COM bauen.

        Entspricht dem 'os'-Target des originalen Makefiles.
        Ablauf in 7 Schritten:
        1. .mac-Quelldateien nach build/ kopieren (gemeinsam + variantenspezifisch)
        2. Vorkompilierte .erl-Module aus prebuilt/ kopieren
        3. Build-Tools (m80.com, linkmt.com) nach build/ kopieren
        4. M80: Listing erzeugen (für /p:-Wert-Extraktion)
        5. M80: ERL-Datei assemblieren
        6. /p:-Wert extrahieren und mit LINKMT zu @OS.COM linken
        7. Temporäre Dateien aufräumen
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
        build_abs = self._abs(build_dir)
        os.makedirs(build_abs, exist_ok=True)

        # Aktualitätsprüfung: Build nur wenn Quelldateien neuer als @os.com sind
        if self._os_is_up_to_date(paths, paths['os_target']):
            self.log("[INFO] @OS.COM ist aktuell – Build übersprungen.")
            return

        # STEP 1: .mac-Dateien kopieren:
        # Zuerst gemeinsame Quellen aus src/, dann variantenspezifische aus src/<variante>/
        # (variantenspezifische überschreiben bei Namensgleichheit die gemeinsamen)
        self.log("[STEP 1] Kopiere .mac-Dateien nach build/")
        for mac in glob.glob(os.path.join(self._abs(paths['src_common']), '*.mac')):
            shutil.copy2(mac, build_abs)
        for mac in glob.glob(os.path.join(self._abs(paths['src_dir']), '*.mac')):
            shutil.copy2(mac, build_abs)
        # Auch .MAC (Großbuchstaben) kopieren und in Kleinbuchstaben umbenennen
        for mac in glob.glob(os.path.join(self._abs(paths['src_dir']), '*.MAC')):
            dst = os.path.join(build_abs, os.path.basename(mac).lower())
            shutil.copy2(mac, dst)

        # STEP 2: Vorkompilierte ERL-Module aus prebuilt/ kopieren
        # (bdos.erl, ccp.erl, cpabas.erl - diese werden nicht neu assembliert)
        self.log("[STEP 2] Kopiere ERL-Dateien aus prebuilt/")
        for erl in glob.glob(os.path.join(self._abs(paths['prebuilt_dir']), '*.erl')):
            shutil.copy2(erl, build_abs)
        for erl in glob.glob(os.path.join(self._abs(paths['prebuilt_dir']), '*.ERL')):
            dst = os.path.join(build_abs, os.path.basename(erl).lower())
            if not os.path.exists(dst):
                shutil.copy2(erl, dst)

        # STEP 3: Build-Tools (M80 Assembler, LINKMT Linker) nach build/ kopieren
        # cparun bleibt in tools/ und wird mit -dir auf build/ gelenkt
        self.log("[STEP 3] Kopiere Build-Tools nach build/")
        for tool in ['m80.com', 'linkmt.com']:
            src = os.path.join(self._abs(paths['tools_dir']), tool)
            if os.path.isfile(src):
                shutil.copy2(src, build_abs)

        # STEP 4: Assemblieren mit M80 - Listing erzeugen (für /p:-Wert-Extraktion)
        # Das Listing enthält den /p:-Wert, der für den Linker benötigt wird
        self.log("[STEP 4] Assemblieren mit M80")
        cparun_abs = self._abs(self.cparun)
        result = self._run(
            [cparun_abs, 'm80', f'={main_src}/L'],
            cwd=build_abs, check=False
        )

        # STEP 5: M80 Assemblierung - ERL-Datei (relocatable Objektcode) erzeugen
        self.log(f"[STEP 5] Assembliere {main_src}.erl")
        self._run(
            [cparun_abs, 'm80', f'{main_src}.erl={main_src}'],
            cwd=build_abs
        )

        # STEP 6: /p:-Wert (Load-Adresse) aus der M80-Ausgabe extrahieren
        # und alle Module mit LINKMT zu @OS.COM zusammenlinken
        asm_output = (result.stdout or '') + (result.stderr or '')
        p_value = self._extract_p_value(asm_output)
        if not p_value:
            raise RuntimeError("Kein /p:-Wert in der M80-Ausgabe gefunden!")
        self.log(f"[STEP 6] Linken mit /p:{p_value}")
        # Reihenfolge: cpabas (BIOS-Basis), ccp (Console Command Processor),
        # bdos (Basic Disk Operating System), bios/biop (BIOS der Variante)
        self._run(
            [cparun_abs, 'linkmt', f'@OS=cpabas,ccp,bdos,{main_src}/p:{p_value}'],
            cwd=build_abs
        )

        # STEP 7: Temporäre Dateien aufräumen (alles außer @os.com entfernen)
        self.log("[STEP 7] Aufräumen temporärer Dateien")
        for pattern in ['*.syp', '*.rel', '*.mac', '*.MAC', '*.erl',
                        'm80.com', 'linkmt.com']:
            for f in glob.glob(os.path.join(build_abs, pattern)):
                basename = os.path.basename(f).lower()
                if basename != '@os.com':
                    os.remove(f)

        self.log("[FERTIG] @OS.COM wurde erfolgreich erzeugt.")

    @staticmethod
    def _extract_p_value(asm_output):
        """/p:-Linkwert (Load-Adresse) aus der M80-Assembler-Ausgabe extrahieren.

        Der M80-Assembler gibt am Ende der Assemblierung eine Zeile wie
        '/p:E800' aus. Steuerzeichen (z.B. Backspace \x08) zwischen /p: und
        dem Hex-Wert werden toleriert und vorher entfernt.

        Returns:
            str: Hex-Wert (z.B. 'E800') oder None wenn nicht gefunden
        """
        # Steuerzeichen (0x00-0x1F außer \n\r\t) entfernen
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', asm_output)
        m = re.search(r'/p:\s*([0-9A-Fa-f]{4,})', cleaned)
        return m.group(1) if m else None

    # -----------------------------------------------------------------------
    # Diskettenimage - IMG-Format mit Bootsektor und Dateien
    # -----------------------------------------------------------------------

    def build_diskimage(self, config):
        """Diskettenimage im IMG-Format erstellen.

        Entspricht dem 'diskimage'-Target des originalen Makefiles.
        Ablauf in 5 Schritten:
        1. Leeres Image erzeugen (mit 0xE5 gefüllt, CP/M-Standard)
        2. @os.com ins Image kopieren (mit cpmcp)
        3. Dateien aus additions/ (variantenspezifisch + allgemein) hinzufügen
        4. Disketteninhalt zur Kontrolle anzeigen (cpmls)
        5. Bootsektor einfügen (je nach Format am Anfang oder als Präfix)
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

        if not os.path.isfile(self._abs(os_target)):
            raise RuntimeError("@OS.COM nicht gefunden! Zuerst 'os' bauen.")

        # STEP 1: Leeres Image erzeugen (mit 0xE5 gefüllt)
        self.log(f"[STEP 1] Erzeuge leeres Image ({size}k, Format: {fmt})")
        data = bytes([0xE5]) * (size * 1024)
        with open(self._abs(tmp_image), 'wb') as f:
            f.write(data)

        if fmt == 'cpa800' and os.path.isfile(self._abs(bootsector)):
            # Bootblock am Anfang der Dateizuordnungstabelle einfügen (cpa800)
            self.log("[STEP 1b] Erzeuge pseudo-Bootblock")
            with open(self._abs(bootsector), 'rb') as bs:
                boot_data = bs.read(32)
            with open(self._abs(tmp_image), 'r+b') as f:
                f.write(boot_data)

        # STEP 2: @os.com ins Image kopieren
        self.log(f"[STEP 2] Kopiere @os.com ins Image (Format: {fmt})")
        self._run([self.cpmcp, '-f', diskdef, tmp_image, os_target, '0:@os.com'])

        if fmt == 'cpa800' and os.path.isfile(self._abs(bootsector)):
            # Spur 0 bootfähig machen: vollständigen Bootsektor am Image-Anfang einfügen
            self.log("[STEP 2b] Fixe Spur 0 für Bootfähigkeit")
            with open(self._abs(bootsector), 'rb') as bs:
                boot_data = bs.read(128)  # 4 × 32 bytes
            with open(self._abs(tmp_image), 'r+b') as f:
                f.write(boot_data)

        # STEP 3: Dateien aus additions/ hinzufügen
        # Zuerst variantenspezifische (z.B. additions/bc_a5120/), dann allgemeine
        additions_sys = os.path.join(paths['additions_dir'], variant)
        if os.path.isdir(self._abs(additions_sys)):
            self.log(f"[STEP 3a] Kopiere variantenspezifische Dateien aus 'additions/{variant}'")
            for fname in sorted(os.listdir(self._abs(additions_sys))):
                fpath = os.path.join(additions_sys, fname)
                if os.path.isfile(self._abs(fpath)):
                    self.log(f"  [ADD] {fname} (variantenspezifisch)")
                    self._run([self.cpmcp, '-f', diskdef, tmp_image, fpath, f'0:{fname}'])

        self.log(f"[STEP 3b] Kopiere allgemeine Dateien aus 'additions/'")
        for fname in sorted(os.listdir(self._abs(paths['additions_dir']))):
            fpath = os.path.join(paths['additions_dir'], fname)
            if os.path.isfile(self._abs(fpath)):
                self.log(f"  [ADD] {fname}")
                self._run([self.cpmcp, '-f', diskdef, tmp_image, fpath, f'0:{fname}'])

        # STEP 4: Disketteninhalt zur Kontrolle anzeigen
        self.log("[STEP 4] Dateien im Image:")
        self._run([self.cpmls, '-Ff', diskdef, tmp_image])

        # STEP 5: Bootsektor einfügen
        # cpa780: Bootsektor wird als Präfix vorangestellt (separate Spur 0)
        # cpa800: Bootsektor ist bereits im Image enthalten
        if fmt == 'cpa780' and os.path.isfile(self._abs(bootsector)):
            self.log(f"[STEP 5] Füge Bootsektor als Präfix hinzu ({os.path.basename(bootsector)})")
            with open(self._abs(bootsector), 'rb') as bs:
                boot_data = bs.read()
            with open(self._abs(tmp_image), 'rb') as tmp:
                image_data = tmp.read()
            with open(self._abs(final_image), 'wb') as out:
                out.write(boot_data)
                out.write(image_data)
        elif fmt == 'cpa780':
            self.log("[WARNUNG] Bootsektor nicht gefunden!")
            shutil.copy2(self._abs(tmp_image), self._abs(final_image))
        else:
            self.log("[STEP 5] Bootsektor nicht nötig (im Image enthalten)")
            shutil.copy2(self._abs(tmp_image), self._abs(final_image))

        # Aufräumen: Temporäres Image löschen
        tmp_abs = self._abs(tmp_image)
        if os.path.isfile(tmp_abs):
            os.remove(tmp_abs)
        self.log(f"[DONE] Diskettenimage erstellt: {final_image}")

    # -----------------------------------------------------------------------
    # HFE/SCP-Konvertierung und Diskette schreiben
    # -----------------------------------------------------------------------

    def build_hfe_image(self, config):
        """Diskettenimage in HFE-Format konvertieren (für HxC Floppy-Emulator)."""
        self._ensure_gw()
        final_image = os.path.join(self.BUILD_DIR, 'cpadisk.img')
        hfe_image = os.path.join(self.BUILD_DIR, 'cpadisk.hfe')
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(os.path.join(self.project_dir, final_image)):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log(f"[STEP] Konvertiere nach HFE (Format: {fmt})")
        self._run([
            self.gw_cmd, 'convert',
            f'--diskdefs={self.CFG_FILE}', f'--format={fmt}',
            final_image, hfe_image
        ])
        self.log(f"[DONE] HFE-Image erstellt: {hfe_image}")

    def build_scp_image(self, config):
        """Diskettenimage in SCP-Format konvertieren (SuperCard Pro)."""
        self._ensure_gw()
        final_image = os.path.join(self.BUILD_DIR, 'cpadisk.img')
        scp_image = os.path.join(self.BUILD_DIR, 'cpadisk.scp')
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(os.path.join(self.project_dir, final_image)):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log(f"[STEP] Konvertiere nach SCP (Format: {fmt})")
        self._run([
            self.gw_cmd, 'convert',
            f'--diskdefs={self.CFG_FILE}', f'--format={fmt}',
            final_image, scp_image
        ])
        self.log(f"[DONE] SCP-Image erstellt: {scp_image}")

    def write_image(self, config):
        """Diskettenimage auf physikalisches Diskettenlaufwerk schreiben (via Greaseweazle)."""
        self._ensure_gw()
        final_image = os.path.join(self.BUILD_DIR, 'cpadisk.img')
        fmt, _, _ = self._get_disk_format(config)

        if not os.path.isfile(os.path.join(self.project_dir, final_image)):
            raise RuntimeError("cpadisk.img nicht gefunden! Zuerst Diskettenimage erstellen.")

        self.log("[STEP] Schreibe Diskettenimage auf Laufwerk")
        self._run([
            self.gw_cmd, 'write',
            f'--diskdefs={self.CFG_FILE}', f'--format={fmt}',
            final_image
        ], stream=True)
        self.log("[DONE] Diskettenimage auf Laufwerk geschrieben.")

    # -----------------------------------------------------------------------
    # Gesamt-Build - Orchestriert alle Build-Schritte für ein Target
    # -----------------------------------------------------------------------

    def build(self, target, config):
        """Vollständigen Build für ein bestimmtes Target ausführen.

        Die Targets sind kaskadierend aufgebaut:
        - 'os': Nur @OS.COM assemblieren und linken
        - 'diskimage': OS + Diskettenimage (IMG)
        - 'diskimagehfe': OS + IMG + HFE-Konvertierung
        - 'diskimagescp': OS + IMG + SCP-Konvertierung
        - 'writeimage': OS + IMG + auf Diskette schreiben

        Args:
            target: Build-Ziel (einer der oben genannten Strings)
            config: Config-Dict mit allen Konfigurationsoptionen
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
