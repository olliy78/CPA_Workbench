#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
readDiskUI.py - GUI zum Einlesen von CP/M-Disketten

Dieses Modul stellt eine grafische Benutzeroberfläche (Tkinter) bereit,
mit der Dateien aus CP/M-Disketten-Images (.img, .hfe, .scp) extrahiert
oder direkt von physischen Disketten über einen Greaseweazle-Controller
eingelesen werden können.

Funktionalität:
  - Auswahl der Quelle: Image-Datei oder Greaseweazle (Diskette einlesen)
  - Auswahl des Diskettenformats (cpa800, cpa780 etc. aus diskdefs)
  - Anzeige des Disketteninhalts (cpmls)
  - Extraktion aller Dateien in ein Zielverzeichnis (cpmcp)
  - Automatische Konvertierung von HFE/SCP nach IMG (via Greaseweazle)
  - Automatische Installation von Greaseweazle in virtuelle Umgebung

Benötigte externe Tools:
  - cpmcp / cpmls (im tools/-Verzeichnis)
  - Greaseweazle 'gw' (optional, für HFE/SCP-Konvertierung und Diskettenzugriff)

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)

Verwendung:
    python3 tools/readDiskUI.py
"""
import os
import re
import sys
import shutil
import venv
import platform
import threading
import queue
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path

# ---------------------------------------------------------------------------
# Pfade und Konstanten
# ---------------------------------------------------------------------------

# Projektverzeichnis: eine Ebene über tools/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# URL für die automatische Greaseweazle-Installation via pip
GW_INSTALL_URL = 'git+https://github.com/keirf/greaseweazle@latest'


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _parse_diskdefs_formats(diskdefs_path):
    """Formatnamen aus der diskdefs-Datei auslesen.

    Durchsucht die Datei nach 'diskdef <name>' Einträgen und gibt eine
    Liste der gefundenen Formatnamen zurück (z.B. ['cpa200', 'cpa800', ...]).
    """
    formats = []
    if not os.path.isfile(diskdefs_path):
        return formats
    with open(diskdefs_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^diskdef\s+(\S+)', line)
            if m:
                formats.append(m.group(1))
    return formats


# ============================================================================
# ExtractApp - Hauptklasse der Extraktions-GUI
# ============================================================================

class ExtractApp:
    """GUI-Anwendung zum Extrahieren von CP/M-Disketten.

    Stellt eine Benutzeroberfläche bereit mit:
    - Quellauswahl (Image-Datei oder Greaseweazle)
    - Formatauswahl (aus diskdefs-Datei)
    - Zielverzeichnis-Auswahl
    - Buttons für Inhaltsanzeige und Extraktion
    - Scrollbarem Log-Bereich mit farbiger Ausgabe

    Die Disk-Operationen laufen in separaten Threads, damit die GUI
    während der Verarbeitung responsiv bleibt.
    """

    def __init__(self):
        """Fenster initialisieren, Tools konfigurieren, Formate laden und UI aufbauen."""
        self.root = tk.Tk()
        self.root.title('CP/M Disketten-Extraktor')
        self.root.geometry('900x650')
        self.root.minsize(700, 500)

        self.log_queue = queue.Queue()  # Thread-sichere Log-Warteschlange
        self.running = False             # Flag: läuft gerade eine Operation?
        self.gw_cmd = None               # Pfad zum Greaseweazle-Kommando (wird bei Bedarf gesetzt)

        # Plattformspezifische cpmtools-Pfade (relativ zum Projektverzeichnis)
        if platform.system() == 'Linux':
            self.cpmcp = os.path.join('tools', 'cpmcp')
            self.cpmls = os.path.join('tools', 'cpmls')
        else:
            self.cpmcp = os.path.join('tools', 'cpmcp.exe')
            self.cpmls = os.path.join('tools', 'cpmls.exe')

        # Verfügbare Diskettenformate aus der diskdefs-Datei laden
        diskdefs_path = os.path.join(PROJECT_DIR, 'diskdefs')
        self.formats = _parse_diskdefs_formats(diskdefs_path)
        if not self.formats:
            self.formats = ['cpa800', 'cpa780']  # Fallback-Formate

        self._create_ui()    # Oberfläche aufbauen
        self._poll_log()     # Log-Polling-Timer starten

    def _create_ui(self):
        """Hauptoberfläche erstellen: Menüleiste, Einstellungen und Log-Bereich."""
        # --- Menüleiste ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Beenden', command=self._on_close)
        menubar.add_cascade(label='Datei', menu=file_menu)
        self.root.config(menu=menubar)

        # Hauptlayout: Oben Einstellungen, unten Log
        main_pane = ttk.PanedWindow(self.root, orient='vertical')
        main_pane.pack(fill='both', expand=True, padx=5, pady=5)

        # --- Oberer Bereich: Einstellungsformular ---
        settings_frame = ttk.LabelFrame(main_pane, text=' Einstellungen ', padding=10)
        main_pane.add(settings_frame, weight=0)

        # 3-Spalten Grid: Label | Widget | Button
        settings_frame.columnconfigure(1, weight=1)

        row = 0

        # Quelltyp-Auswahl: Image-Datei oder Greaseweazle (Radiobuttons)
        ttk.Label(settings_frame, text='Quelle:',
                  font=('', 10, 'bold')).grid(row=row, column=0, sticky='w', pady=(0, 8))
        row += 1

        self.source_var = tk.StringVar(value='file')
        source_frame = ttk.Frame(settings_frame)
        source_frame.grid(row=row, column=0, columnspan=3, sticky='w', pady=(0, 5))

        ttk.Radiobutton(source_frame, text='Image-Datei (.img, .hfe, .scp)',
                        variable=self.source_var, value='file',
                        command=self._on_source_change).pack(side='left', padx=(0, 15))
        ttk.Radiobutton(source_frame, text='Greaseweazle (Diskette einlesen)',
                        variable=self.source_var, value='gw',
                        command=self._on_source_change).pack(side='left')
        row += 1

        # Image-Datei
        ttk.Label(settings_frame, text='Image-Datei:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(settings_frame, textvariable=self.file_var)
        self.file_entry.grid(row=row, column=1, sticky='ew', pady=4)
        self.file_btn = ttk.Button(settings_frame, text='Durchsuchen...',
                                   command=self._choose_file)
        self.file_btn.grid(row=row, column=2, padx=(5, 0), pady=4)
        row += 1

        # Diskettenname (für GW)
        ttk.Label(settings_frame, text='Diskettenname:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        self.diskname_var = tk.StringVar()
        self.diskname_entry = ttk.Entry(settings_frame, textvariable=self.diskname_var)
        self.diskname_entry.grid(row=row, column=1, sticky='ew', pady=4)
        self.diskname_label = ttk.Label(settings_frame,
                                        text='(Name für das eingelesene Image)')
        self.diskname_label.grid(row=row, column=2, padx=(5, 0), pady=4)
        row += 1

        # Separator
        ttk.Separator(settings_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', pady=8)
        row += 1

        # Diskettenformat
        ttk.Label(settings_frame, text='Diskettenformat:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        self.format_var = tk.StringVar(value='cpa800')
        fmt_combo = ttk.Combobox(settings_frame, textvariable=self.format_var,
                                 values=self.formats, state='readonly', width=25)
        fmt_combo.grid(row=row, column=1, sticky='w', pady=4)
        row += 1

        # Zielverzeichnis
        ttk.Label(settings_frame, text='Zielverzeichnis:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        default_dir = os.path.join(PROJECT_DIR, 'Disketten')
        self.target_var = tk.StringVar(value=default_dir)
        self.target_entry = ttk.Entry(settings_frame, textvariable=self.target_var)
        self.target_entry.grid(row=row, column=1, sticky='ew', pady=4)
        ttk.Button(settings_frame, text='Durchsuchen...',
                   command=self._choose_target).grid(row=row, column=2,
                                                      padx=(5, 0), pady=4)
        row += 1

        # Initial: GW-spezifische Felder deaktivieren (bis GW gewählt wird)
        self._on_source_change()

        # --- Unterer Bereich: Aktions-Buttons und Log ---
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=1)

        # Button-Leiste
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        self.btn_show = ttk.Button(btn_frame, text='Inhalt anzeigen',
                                    command=self._do_show_content)
        self.btn_show.pack(side='left', padx=2)

        self.btn_extract = ttk.Button(btn_frame, text='Diskette einlesen',
                                      command=self._do_extract)
        self.btn_extract.pack(side='left', padx=2)

        self.btn_clear_log = ttk.Button(btn_frame, text='Log löschen',
                                        command=self._clear_log)
        self.btn_clear_log.pack(side='right', padx=2)

        self.status_var = tk.StringVar(value='Bereit')
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='right', padx=10)

        # Log-Bereich
        self.log_text = scrolledtext.ScrolledText(
            bottom_frame, height=12, state='disabled',
            font=('Consolas', 9) if sys.platform == 'win32' else ('monospace', 9),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)

        # Log-Tags für farbige Ausgabe (blau=Schritt, grün=Fertig, rot=Fehler, grau=Info)
        self.log_text.tag_configure('step', foreground='#0066cc')
        self.log_text.tag_configure('done', foreground='#008800')
        self.log_text.tag_configure('error', foreground='#cc0000')
        self.log_text.tag_configure('info', foreground='#666666')

        # Fenster-Schließen-Event abfangen (warnt bei laufender Operation)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    # -----------------------------------------------------------------------
    # Quelltyp-Steuerung und Dateiauswahl-Dialoge
    # -----------------------------------------------------------------------

    def _on_source_change(self):
        """Felder je nach Quelltyp aktivieren/deaktivieren.

        Bei 'file': Image-Datei-Feld aktiv, Diskettenname deaktiviert.
        Bei 'gw': Image-Datei deaktiviert, Diskettenname aktiv.
        """
        if self.source_var.get() == 'file':
            self.file_entry.config(state='normal')
            self.file_btn.config(state='normal')
            self.diskname_entry.config(state='disabled')
        else:
            self.file_entry.config(state='disabled')
            self.file_btn.config(state='disabled')
            self.diskname_entry.config(state='normal')

    def _choose_file(self):
        """Dateiauswahl-Dialog für Image-Dateien (öffnet Systemdialog)."""
        path = filedialog.askopenfilename(
            title='Image-Datei auswählen',
            initialdir=PROJECT_DIR,
            filetypes=[
                ('Disk-Images', '*.img *.hfe *.scp'),  # Unterstützte Image-Formate
                ('Alle Dateien', '*.*')
            ]
        )
        if path:
            self.file_var.set(path)

    def _choose_target(self):
        """Verzeichnisauswahl-Dialog für Zielordner."""
        path = filedialog.askdirectory(
            title='Zielverzeichnis auswählen',
            initialdir=self.target_var.get()
        )
        if path:
            self.target_var.set(path)

    # -----------------------------------------------------------------------
    # Logging - Thread-sichere Ausgabe mit farbigen Tags
    # -----------------------------------------------------------------------

    def _log(self, msg):
        """Log-Nachricht thread-sicher in die Warteschlange legen."""
        self.log_queue.put(msg)

    def _poll_log(self):
        """Log-Warteschlange periodisch abarbeiten und GUI aktualisieren.

        Nachrichten werden anhand ihres Präfix ([STEP], [DONE], [ERROR], [INFO])
        farblich markiert. Wird alle 100ms per Timer aufgerufen.
        """
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_text.config(state='normal')
            tag = None
            if msg.startswith('[STEP]'):
                tag = 'step'
            elif msg.startswith('[DONE]'):
                tag = 'done'
            elif msg.startswith('[ERROR]') or msg.startswith('[FEHLER]'):
                tag = 'error'
            elif msg.startswith('[INFO]'):
                tag = 'info'
            self.log_text.insert('end', msg + '\n', tag)
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        self.root.after(100, self._poll_log)

    def _clear_log(self):
        """Log-Bereich leeren."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    # -----------------------------------------------------------------------
    # Greaseweazle - Automatische Installation und Verwaltung
    # -----------------------------------------------------------------------

    def _ensure_gw(self):
        """Greaseweazle (gw) sicherstellen.

        Prüft in drei Schritten:
        1. gw im System-PATH?
        2. gw im lokalen .venv vorhanden?
        3. Falls nicht: .venv erstellen und Greaseweazle per pip installieren.
        """
        if self.gw_cmd:
            return

        if shutil.which('gw'):
            self.gw_cmd = 'gw'
            self._log("[INFO] Greaseweazle gefunden: gw (System)")
            return

        venv_dir = os.path.join(PROJECT_DIR, '.venv')
        if platform.system() == 'Windows':
            gw_venv = os.path.join(venv_dir, 'Scripts', 'gw.exe')
        else:
            gw_venv = os.path.join(venv_dir, 'bin', 'gw')

        if os.path.isfile(gw_venv):
            self.gw_cmd = gw_venv
            self._log(f"[INFO] Greaseweazle gefunden: {gw_venv}")
            return

        self._log("[INFO] Greaseweazle nicht gefunden – wird automatisch installiert ...")
        self._log(f"[STEP] Erstelle virtuelle Umgebung: {venv_dir}")
        venv.create(venv_dir, with_pip=True)

        if platform.system() == 'Windows':
            pip_cmd = os.path.join(venv_dir, 'Scripts', 'pip')
        else:
            pip_cmd = os.path.join(venv_dir, 'bin', 'pip')

        self._log("[STEP] Installiere Greaseweazle ...")
        result = subprocess.run(
            [pip_cmd, 'install', GW_INSTALL_URL],
            capture_output=True, text=True, errors='replace'
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                self._log(f"    {line}")
        if result.returncode != 0:
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    self._log(f"    {line}")
            raise RuntimeError(
                "Greaseweazle-Installation fehlgeschlagen. "
                "Bitte manuell installieren: pip install greaseweazle"
            )

        if not os.path.isfile(gw_venv):
            raise RuntimeError("Greaseweazle-Installation fehlgeschlagen.")

        self.gw_cmd = gw_venv
        self._log(f"[DONE] Greaseweazle installiert: {gw_venv}")

    def _run(self, cmd):
        """Externen Befehl ausführen, Ausgabe loggen und Fehler werfen.

        Alle Befehle werden mit cwd=PROJECT_DIR ausgeführt, sodass
        relative Pfade korrekt aufgelöst werden.
        """
        self._log(f"  > {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=PROJECT_DIR, capture_output=True, text=True,
            timeout=300, errors='replace'
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                self._log(f"    {line}")
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines():
                self._log(f"    {line}")
        if result.returncode != 0:
            raise RuntimeError(
                f"Befehl fehlgeschlagen (exit {result.returncode}): {' '.join(cmd)}"
            )
        return result

    # -----------------------------------------------------------------------
    # Inhalt anzeigen - Disketteninhalt mit cpmls auflisten
    # -----------------------------------------------------------------------

    def _do_show_content(self):
        """Disketteninhalt anzeigen (nur für Image-Dateien verfügbar).

        Startet den Anzeige-Worker in einem separaten Thread.
        Bei HFE/SCP-Dateien wird zuerst nach IMG konvertiert.
        """
        if self.running:
            return

        source = self.source_var.get()
        if source == 'file':
            file_path = self.file_var.get().strip()
            if not file_path:
                messagebox.showwarning('Eingabe fehlt',
                                       'Bitte eine Image-Datei auswählen.')
                return
            if not os.path.isfile(file_path):
                messagebox.showerror('Datei nicht gefunden',
                                     f'Die Datei wurde nicht gefunden:\n{file_path}')
                return
        else:
            messagebox.showinfo('Hinweis',
                                'Inhalt anzeigen ist nur für Image-Dateien verfügbar.')
            return

        self.running = True
        self.btn_show.config(state='disabled')
        self.btn_extract.config(state='disabled')
        self.status_var.set('Lese Inhalt ...')

        thread = threading.Thread(target=self._show_content_worker, daemon=True)
        thread.start()

    def _relpath(self, path):
        """Pfad relativ zum Projektverzeichnis zurückgeben."""
        try:
            return os.path.relpath(path, PROJECT_DIR)
        except ValueError:
            return path

    def _show_content_worker(self):
        """Worker-Thread für Inhaltsanzeige.

        Bei HFE/SCP: Konvertiert zuerst nach IMG (temp. Datei in build/),
        führt dann cpmls aus und löscht das temporäre Image.
        """
        try:
            file_path = self.file_var.get().strip()
            fmt = self.format_var.get()

            orig = Path(file_path)
            ext = orig.suffix.lower()
            temp_img = None
            rel_file = self._relpath(file_path)

            if ext != '.img':
                # HFE/SCP erst nach IMG konvertieren
                self._ensure_gw()
                img_rel = os.path.join('build', f"{orig.stem}.img")
                os.makedirs(os.path.join(PROJECT_DIR, 'build'), exist_ok=True)
                self._log(f"[STEP] Konvertiere {orig.name} nach IMG ...")
                self._run([
                    self.gw_cmd, 'convert',
                    '--diskdefs=cpaFormates.cfg', f'--format={fmt}',
                    rel_file, img_rel
                ])
                temp_img = os.path.join(PROJECT_DIR, img_rel)
            else:
                img_rel = rel_file

            self._log(f"[STEP] Zeige Inhalt von {orig.name} (Format: {fmt})")
            self._run([
                self.cpmls, '-Ff', fmt,
                '-T', 'raw(diskdefs)',
                img_rel
            ])
            self._log("[DONE] Disketteninhalt angezeigt.")

            if temp_img and os.path.isfile(temp_img):
                os.remove(temp_img)

            self._set_status('Bereit')

        except Exception as e:
            self._log(f"[ERROR] {e}")
            self._set_status('Fehler')
        finally:
            self.running = False
            self.root.after(0, lambda: (
                self.btn_show.config(state='normal'),
                self.btn_extract.config(state='normal')
            ))

    # -----------------------------------------------------------------------
    # Extraktion - Alle Dateien von der Diskette in ein Verzeichnis kopieren
    # -----------------------------------------------------------------------

    def _do_extract(self):
        """Extraktion in einem separaten Thread starten.

        Prüft Eingaben (Datei bzw. Diskettenname) und startet den Worker-Thread.
        """
        if self.running:
            return

        source = self.source_var.get()

        if source == 'file':
            file_path = self.file_var.get().strip()
            if not file_path:
                messagebox.showwarning('Eingabe fehlt',
                                       'Bitte eine Image-Datei auswählen.')
                return
            if not os.path.isfile(file_path):
                messagebox.showerror('Datei nicht gefunden',
                                     f'Die Datei wurde nicht gefunden:\n{file_path}')
                return
        else:
            diskname = self.diskname_var.get().strip()
            if not diskname:
                messagebox.showwarning('Eingabe fehlt',
                                       'Bitte einen Diskettennamen angeben.')
                return

        self.running = True
        self.btn_extract.config(state='disabled')
        self.status_var.set('Einlesen ...')

        thread = threading.Thread(target=self._extract_worker, daemon=True)
        thread.start()

    def _extract_worker(self):
        """Worker-Thread für die Extraktion.

        Ablauf:
        1. Quelle einlesen (GW: Diskette direkt / Datei: ggf. HFE/SCP→IMG)
        2. Neues Unterverzeichnis im Zielordner anlegen
        3. Disketteninhalt mit cpmls auflisten
        4. Jede Datei einzeln mit cpmcp extrahieren
        5. Temporäres Image löschen
        """
        try:
            source = self.source_var.get()
            fmt = self.format_var.get()
            target_base = self._relpath(self.target_var.get().strip())

            os.makedirs(os.path.join(PROJECT_DIR, target_base), exist_ok=True)

            img_rel = None
            temp_img = None

            if source == 'gw':
                # Greaseweazle: Diskette direkt einlesen und als IMG speichern
                self._ensure_gw()
                diskname = self.diskname_var.get().strip()
                img_rel = os.path.join(target_base, f"{diskname}.img")
                self._log(f"[STEP] Lese Diskette mit Greaseweazle ein: {diskname}")
                self._run([
                    self.gw_cmd, 'read',
                    '--diskdefs=cpaFormates.cfg', f'--format={fmt}',
                    img_rel
                ])
                temp_img = os.path.join(PROJECT_DIR, img_rel)
            else:
                # Datei einlesen: bei HFE/SCP zuerst nach IMG konvertieren
                file_path = self.file_var.get().strip()
                orig = Path(file_path)
                ext = orig.suffix.lower()
                rel_file = self._relpath(file_path)

                if ext != '.img':
                    # HFE/SCP nach IMG konvertieren (via Greaseweazle)
                    self._ensure_gw()
                    img_rel = os.path.join(target_base, f"{orig.stem}.img")
                    self._log(f"[STEP] Konvertiere {orig.name} nach IMG ...")
                    self._run([
                        self.gw_cmd, 'convert',
                        '--diskdefs=cpaFormates.cfg', f'--format={fmt}',
                        rel_file, img_rel
                    ])
                    temp_img = os.path.join(PROJECT_DIR, img_rel)
                else:
                    # IMG direkt verwenden
                    target_abs = os.path.join(PROJECT_DIR, target_base)
                    if str(orig.parent) != target_abs:
                        dest = os.path.join(target_abs, orig.name)
                        shutil.copy2(file_path, dest)
                        img_rel = os.path.join(target_base, orig.name)
                    else:
                        img_rel = rel_file

            # Zielverzeichnis bestimmen: Diskname als Ordnername, bei Duplikat nummerieren
            basename = Path(img_rel).stem
            new_dir = os.path.join(target_base, basename)
            count = 1
            while os.path.exists(os.path.join(PROJECT_DIR, new_dir)):
                count += 1
                new_dir = os.path.join(target_base, f"{basename}_{count}")
            os.makedirs(os.path.join(PROJECT_DIR, new_dir))

            # Inhalt der Diskette anzeigen
            self._log("[STEP] Lese Disketteninhalt ...")
            self._run([
                self.cpmls, '-Ff', fmt,
                '-T', 'raw(diskdefs)',
                img_rel
            ])

            # Dateiliste holen (ohne Header-Zeile) für die einzelne Extraktion
            result = subprocess.run(
                [self.cpmls, '-f', fmt, '-T', 'raw(diskdefs)', img_rel],
                cwd=PROJECT_DIR, capture_output=True, text=True,
                errors='replace'
            )
            if result.returncode != 0:
                raise RuntimeError(f"cpmls fehlgeschlagen: {result.stderr}")

            files = []
            for line in result.stdout.strip().splitlines()[1:]:
                if line.strip():
                    files.append(line.split()[0])

            # Jede Datei einzeln mit cpmcp aus dem Image extrahieren
            self._log(f"[STEP] Extrahiere {len(files)} Dateien nach {new_dir} ...")
            for fname in files:
                if fname:
                    self._run([
                        self.cpmcp, '-f', fmt,
                        '-T', 'raw(diskdefs)',
                        img_rel, f'0:{fname}', new_dir
                    ])

            # Ergebnis: Anzahl extrahierter Dateien ausgeben
            new_dir_abs = os.path.join(PROJECT_DIR, new_dir)
            count_files = sum(1 for f in Path(new_dir_abs).glob('*') if f.is_file())
            self._log(f"[DONE] {count_files} Dateien in {new_dir} extrahiert.")

            # Temporäres Image löschen (nur bei GW-Einlesen oder HFE/SCP-Konvertierung)
            if temp_img and os.path.isfile(temp_img):
                os.remove(temp_img)
                self._log(f"[INFO] Temporäres Image gelöscht.")

            self._set_status('Fertig')

        except Exception as e:
            self._log(f"[ERROR] {e}")
            self._set_status('Fehler')
        finally:
            self.running = False
            self.root.after(0, lambda: self.btn_extract.config(state='normal'))

    def _set_status(self, text):
        """Status-Text thread-safe setzen."""
        self.root.after(0, lambda: self.status_var.set(text))

    def _on_close(self):
        """Anwendung beenden."""
        if self.running:
            if not messagebox.askokcancel('Beenden',
                                          'Ein Vorgang läuft noch. Wirklich beenden?'):
                return
        self.root.destroy()

    def run(self):
        """GUI-Hauptschleife starten."""
        self.root.mainloop()


if __name__ == '__main__':
    app = ExtractApp()
    app.run()
