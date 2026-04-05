#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
writeDiskUI.py - GUI zum Erstellen und Schreiben von CP/M-Disketten

Dieses Modul stellt eine grafische Benutzeroberfläche (Tkinter) bereit,
mit der aus einem Ordner voller Dateien ein CP/M-Disketten-Image erstellt
und optional auf eine physische Diskette geschrieben werden kann.

Funktionalität:
  - Auswahl eines Quellverzeichnisses mit den zu schreibenden Dateien
  - Auswahl des Diskettenformats (cpa800, cpa780 etc. aus diskdefs)
  - Ausgabe als IMG-, HFE- oder SCP-Datei oder direkt auf Diskette (Greaseweazle)
  - Vorschau der Quelldateien mit Größenangaben
  - Temporäres Image wird mit 0xE5 gefüllt (CP/M-Standard für leere Sektoren)
  - Automatische Installation von Greaseweazle in virtuelle Umgebung

Benötigte externe Tools:
  - cpmcp / cpmls (im tools/-Verzeichnis)
  - Greaseweazle 'gw' (optional, für HFE/SCP-Konvertierung und Diskettenschreiben)

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)

Verwendung:
    python3 tools/writeDiskUI.py
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

def _parse_diskdefs(diskdefs_path):
    """Formate mit ihren Größen aus der diskdefs-Datei auslesen.

    Berechnet für jedes Format die Image-Größe in Kilobyte aus den
    Parametern seclen, sectrk und tracks: size_kb = seclen * sectrk * tracks / 1024.

    Returns:
        list: Liste von Tupeln (name, size_kb), z.B. [('cpa800', 800), ('cpa780', 780)]
    """
    formats = []
    if not os.path.isfile(diskdefs_path):
        return formats
    name = None
    seclen = sectrk = tracks = 0
    with open(diskdefs_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            m = re.match(r'^diskdef\s+(\S+)', line)
            if m:
                if name is not None:
                    size_kb = (seclen * sectrk * tracks) // 1024
                    formats.append((name, size_kb))
                name = m.group(1)
                seclen = sectrk = tracks = 0
                continue
            if name is None:
                continue
            m = re.match(r'^seclen\s+(\d+)', line)
            if m:
                seclen = int(m.group(1))
            m = re.match(r'^sectrk\s+(\d+)', line)
            if m:
                sectrk = int(m.group(1))
            m = re.match(r'^tracks\s+(\d+)', line)
            if m:
                tracks = int(m.group(1))
            if line == 'end':
                pass
    # Letztes Format in der Datei abschließen
    if name is not None:
        size_kb = (seclen * sectrk * tracks) // 1024
        formats.append((name, size_kb))
    return formats


# ============================================================================
# WriteDiskApp - Hauptklasse der Schreib-GUI
# ============================================================================

class WriteDiskApp:
    """GUI-Anwendung zum Erstellen von CP/M-Disketten-Images.

    Stellt eine Benutzeroberfläche bereit mit:
    - Quellverzeichnis-Auswahl (Ordner mit den zu schreibenden Dateien)
    - Formatauswahl mit Größenangabe (aus diskdefs-Datei)
    - Ausgabemedium: IMG, HFE, SCP oder direkt auf Diskette (Greaseweazle)
    - Quelldatei-Vorschau und Image-Erstellung
    - Scrollbarem Log-Bereich mit farbiger Ausgabe

    Die Disk-Operationen laufen in separaten Threads, damit die GUI
    während der Verarbeitung responsiv bleibt.
    """

    def __init__(self):
        """Fenster initialisieren, Tools konfigurieren, Formate laden und UI aufbauen."""
        self.root = tk.Tk()
        self.root.title('CP/M Disketten-Schreiber')
        self.root.geometry('900x650')
        self.root.minsize(700, 500)

        self.log_queue = queue.Queue()  # Thread-sichere Log-Warteschlange
        self.running = False             # Flag: läuft gerade eine Operation?
        self.gw_cmd = None               # Pfad zum Greaseweazle-Kommando

        # Plattformspezifische cpmtools-Pfade (relativ zum Projektverzeichnis)
        if platform.system() == 'Linux':
            self.cpmcp = os.path.join('tools', 'cpmcp')
            self.cpmls = os.path.join('tools', 'cpmls')
        else:
            self.cpmcp = os.path.join('tools', 'cpmcp.exe')
            self.cpmls = os.path.join('tools', 'cpmls.exe')

        # Verfügbare Diskettenformate mit Größenangaben laden
        diskdefs_path = os.path.join(PROJECT_DIR, 'diskdefs')
        self.disk_formats = _parse_diskdefs(diskdefs_path)
        self.format_names = [name for name, _ in self.disk_formats]  # Nur Namen für Combobox
        self.format_sizes = {name: size for name, size in self.disk_formats}  # Name → Größe
        if not self.format_names:
            self.format_names = ['cpa800', 'cpa780']  # Fallback-Formate
            self.format_sizes = {'cpa800': 800, 'cpa780': 780}

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

        # Quellverzeichnis
        ttk.Label(settings_frame, text='Quellverzeichnis:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(settings_frame, textvariable=self.source_var)
        self.source_entry.grid(row=row, column=1, sticky='ew', pady=4)
        ttk.Button(settings_frame, text='Durchsuchen...',
                   command=self._choose_source).grid(row=row, column=2,
                                                      padx=(5, 0), pady=4)
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
                                 values=self.format_names, state='readonly', width=25)
        fmt_combo.grid(row=row, column=1, sticky='w', pady=4)
        row += 1

        # Separator
        ttk.Separator(settings_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky='ew', pady=8)
        row += 1

        # Ausgabemedium: IMG, HFE, SCP oder Greaseweazle (Radiobuttons)
        ttk.Label(settings_frame, text='Ausgabe:',
                  font=('', 10, 'bold')).grid(row=row, column=0, sticky='w', pady=(0, 8))
        row += 1

        self.output_var = tk.StringVar(value='img')
        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=row, column=0, columnspan=3, sticky='w', pady=(0, 5))

        ttk.Radiobutton(output_frame, text='Image-Datei (.img)',
                        variable=self.output_var, value='img',
                        command=self._on_output_change).pack(side='left', padx=(0, 10))
        ttk.Radiobutton(output_frame, text='HFE-Datei (.hfe)',
                        variable=self.output_var, value='hfe',
                        command=self._on_output_change).pack(side='left', padx=(0, 10))
        ttk.Radiobutton(output_frame, text='SCP-Datei (.scp)',
                        variable=self.output_var, value='scp',
                        command=self._on_output_change).pack(side='left', padx=(0, 10))
        ttk.Radiobutton(output_frame, text='Greaseweazle (Diskette schreiben)',
                        variable=self.output_var, value='gw',
                        command=self._on_output_change).pack(side='left')
        row += 1

        # Ausgabedatei
        ttk.Label(settings_frame, text='Ausgabedatei:').grid(
            row=row, column=0, sticky='e', padx=(0, 8), pady=4)
        self.outfile_var = tk.StringVar(value='cpadisk.img')
        self.outfile_entry = ttk.Entry(settings_frame, textvariable=self.outfile_var)
        self.outfile_entry.grid(row=row, column=1, sticky='ew', pady=4)
        self.outfile_btn = ttk.Button(settings_frame, text='Durchsuchen...',
                                      command=self._choose_outfile)
        self.outfile_btn.grid(row=row, column=2, padx=(5, 0), pady=4)
        row += 1

        # Initial: Ausgabefelder je nach Medium aktualisieren
        self._on_output_change()

        # --- Unterer Bereich: Aktions-Buttons und Log ---
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=1)

        # Button-Leiste
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        self.btn_preview = ttk.Button(btn_frame, text='Quelldateien anzeigen',
                                      command=self._do_preview)
        self.btn_preview.pack(side='left', padx=2)

        self.btn_write = ttk.Button(btn_frame, text='Diskette schreiben',
                                    command=self._do_write)
        self.btn_write.pack(side='left', padx=2)

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
    # Ausgabemedium-Steuerung und Dateiauswahl-Dialoge
    # -----------------------------------------------------------------------

    def _on_output_change(self):
        """Felder je nach Ausgabemedium aktualisieren.

        Bei 'gw': Ausgabedatei-Feld deaktivieren (direkt auf Diskette).
        Sonst: Dateiendung automatisch an Medium anpassen (.img/.hfe/.scp).
        """
        output = self.output_var.get()
        if output == 'gw':
            self.outfile_entry.config(state='disabled')
            self.outfile_btn.config(state='disabled')
        else:
            self.outfile_entry.config(state='normal')
            self.outfile_btn.config(state='normal')
            # Dateiendung automatisch an gewähltes Ausgabemedium anpassen
            current = self.outfile_var.get()
            stem = Path(current).stem if current else 'cpadisk'
            ext_map = {'img': '.img', 'hfe': '.hfe', 'scp': '.scp'}
            self.outfile_var.set(f"{stem}{ext_map[output]}")

    def _choose_source(self):
        """Verzeichnisauswahl-Dialog für Quellordner."""
        path = filedialog.askdirectory(
            title='Quellverzeichnis auswählen',
            initialdir=self.source_var.get() or PROJECT_DIR
        )
        if path:
            self.source_var.set(path)

    def _choose_outfile(self):
        """Dateiauswahl-Dialog für Ausgabedatei."""
        output = self.output_var.get()
        ext_map = {'img': '.img', 'hfe': '.hfe', 'scp': '.scp'}
        ext = ext_map.get(output, '.img')
        path = filedialog.asksaveasfilename(
            title='Ausgabedatei wählen',
            initialdir=PROJECT_DIR,
            defaultextension=ext,
            filetypes=[
                (f'{ext.upper()}-Dateien', f'*{ext}'),
                ('Alle Dateien', '*.*')
            ]
        )
        if path:
            self.outfile_var.set(path)

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

    def _relpath(self, path):
        """Pfad relativ zum Projektverzeichnis zurückgeben."""
        try:
            return os.path.relpath(path, PROJECT_DIR)
        except ValueError:
            return path

    # -----------------------------------------------------------------------
    # Quelldateien anzeigen - Dateiliste mit Größenangaben
    # -----------------------------------------------------------------------

    def _do_preview(self):
        """Dateien im Quellverzeichnis auflisten mit Namen und Größenangaben."""
        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning('Eingabe fehlt',
                                   'Bitte ein Quellverzeichnis auswählen.')
            return
        if not os.path.isdir(source):
            messagebox.showerror('Verzeichnis nicht gefunden',
                                 f'Das Verzeichnis wurde nicht gefunden:\n{source}')
            return

        files = sorted(f for f in os.listdir(source)
                       if os.path.isfile(os.path.join(source, f)))
        if not files:
            self._log(f"[INFO] Keine Dateien in {self._relpath(source)} gefunden.")
            return

        self._log(f"[STEP] Dateien in {self._relpath(source)}:")
        total_size = 0
        for fname in files:
            fsize = os.path.getsize(os.path.join(source, fname))
            total_size += fsize
            self._log(f"    {fname:<20s} {fsize:>8d} Bytes")
        self._log(f"[INFO] {len(files)} Dateien, {total_size:,d} Bytes gesamt")

    # -----------------------------------------------------------------------
    # Diskette schreiben - Image erstellen und ausgeben
    # -----------------------------------------------------------------------

    def _do_write(self):
        """Image erstellen und ggf. auf Diskette schreiben (in separatem Thread).

        Prüft Eingaben (Quellverzeichnis, Ausgabedatei) und startet den Worker-Thread.
        """
        if self.running:
            return

        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning('Eingabe fehlt',
                                   'Bitte ein Quellverzeichnis auswählen.')
            return
        if not os.path.isdir(source):
            messagebox.showerror('Verzeichnis nicht gefunden',
                                 f'Das Verzeichnis wurde nicht gefunden:\n{source}')
            return

        output = self.output_var.get()
        if output != 'gw':
            outfile = self.outfile_var.get().strip()
            if not outfile:
                messagebox.showwarning('Eingabe fehlt',
                                       'Bitte eine Ausgabedatei angeben.')
                return

        # Quelldateien prüfen (leeres Verzeichnis ergibt leeres Image)
        files = sorted(f for f in os.listdir(source)
                       if os.path.isfile(os.path.join(source, f)))
        if not files:
            messagebox.showwarning('Keine Dateien',
                                   'Das Quellverzeichnis enthält keine Dateien.')
            return

        self.running = True
        self.btn_write.config(state='disabled')
        self.btn_preview.config(state='disabled')
        self.status_var.set('Schreibe ...')

        thread = threading.Thread(target=self._write_worker, daemon=True)
        thread.start()

    def _write_worker(self):
        """Worker-Thread für Image-Erstellung und Schreiben.

        Ablauf:
        1. Leeres Image erzeugen (mit 0xE5 gefüllt, CP/M-Standard)
        2. Alle Dateien aus dem Quellverzeichnis mit cpmcp ins Image kopieren
        3. Disketteninhalt mit cpmls zur Kontrolle anzeigen
        4. Je nach Ausgabemedium: IMG kopieren / HFE-SCP konvertieren / auf Diskette schreiben
        5. Temporäres Image aufräumen
        """
        try:
            source = self.source_var.get().strip()
            fmt = self.format_var.get()
            output = self.output_var.get()

            # Image-Größe aus der Formatdefinition ermitteln (in Kilobyte)
            size_kb = self.format_sizes.get(fmt, 800)

            # Quelldateien sammeln
            files = sorted(f for f in os.listdir(source)
                           if os.path.isfile(os.path.join(source, f)))
            self._log(f"[STEP] Erstelle Image mit {len(files)} Dateien (Format: {fmt}, {size_kb}k)")

            # Temporäres Image im build/-Verzeichnis (Name ohne .tmp-Suffix für GW-Kompatibilität)
            build_abs = os.path.join(PROJECT_DIR, 'build')
            os.makedirs(build_abs, exist_ok=True)
            tmp_image = os.path.join('build', 'writedisk_tmp.img')
            tmp_image_abs = os.path.join(PROJECT_DIR, tmp_image)

            # STEP 1: Leeres Image erzeugen (0xE5 = gelöschter Sektor im CP/M)
            self._log(f"[STEP] Erzeuge leeres Image ({size_kb}k)")
            data = bytes([0xE5]) * (size_kb * 1024)  # Gesamte Image-Größe
            with open(tmp_image_abs, 'wb') as f:
                f.write(data)

            # STEP 2: Jede Datei einzeln mit cpmcp ins Image kopieren
            self._log(f"[STEP] Kopiere {len(files)} Dateien ins Image ...")
            for fname in files:
                fpath = os.path.join(source, fname)
                rel_fpath = self._relpath(fpath)
                self._run([
                    self.cpmcp, '-f', fmt,
                    '-T', 'raw(diskdefs)',
                    tmp_image, rel_fpath, f'0:{fname}'
                ])

            # STEP 3: Disketteninhalt zur Kontrolle anzeigen
            self._log("[STEP] Dateien im Image:")
            self._run([
                self.cpmls, '-Ff', fmt,
                '-T', 'raw(diskdefs)',
                tmp_image
            ])

            # STEP 4: Ausgabe je nach gewähltem Medium
            if output == 'img':
                # IMG: Temporäres Image direkt als Ausgabedatei kopieren
                outfile = self.outfile_var.get().strip()
                out_abs = self._resolve_outpath(outfile)
                shutil.copy2(tmp_image_abs, out_abs)
                self._log(f"[DONE] Image erstellt: {self._relpath(out_abs)}")

            elif output in ('hfe', 'scp'):
                # HFE/SCP: Über Greaseweazle konvertieren
                self._ensure_gw()
                outfile = self.outfile_var.get().strip()
                out_abs = self._resolve_outpath(outfile)
                out_rel = self._relpath(out_abs)
                self._log(f"[STEP] Konvertiere nach {output.upper()} (Format: {fmt})")
                self._run([
                    self.gw_cmd, 'convert',
                    '--diskdefs=cpaFormates.cfg', f'--format={fmt}',
                    tmp_image, out_rel
                ])
                self._log(f"[DONE] {output.upper()}-Image erstellt: {out_rel}")

            elif output == 'gw':
                # GW: Image direkt auf physische Diskette schreiben
                self._ensure_gw()
                self._log(f"[STEP] Schreibe Image auf Diskette (Format: {fmt})")
                self._run([
                    self.gw_cmd, 'write',
                    '--diskdefs=cpaFormates.cfg', f'--format={fmt}',
                    tmp_image
                ])
                self._log("[DONE] Image auf Diskette geschrieben.")

            # Temporäres Image im build/-Verzeichnis aufräumen
            if os.path.isfile(tmp_image_abs):
                os.remove(tmp_image_abs)

            self._set_status('Fertig')

        except Exception as e:
            self._log(f"[ERROR] {e}")
            self._set_status('Fehler')
        finally:
            self.running = False
            self.root.after(0, lambda: (
                self.btn_write.config(state='normal'),
                self.btn_preview.config(state='normal')
            ))

    def _resolve_outpath(self, outfile):
        """Ausgabedatei-Pfad auflösen: absolut belassen oder relativ zum Projektverzeichnis machen."""
        if os.path.isabs(outfile):
            return outfile
        return os.path.join(PROJECT_DIR, outfile)

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
    app = WriteDiskApp()
    app.run()
