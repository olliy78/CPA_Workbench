#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
CP/A Workbench - Grafisches Konfigurations- und Build-System

Dieses Modul bildet die Hauptanwendung der CP/A Workbench. Es stellt eine
grafische Benutzeroberfläche (GUI) auf Basis von Tkinter bereit, die das
konsolenbasierte menuconfig und die Makefiles vollständig ersetzt.

Die Anwendung ermöglicht:
  - Tab 1: Auswahl der Systemvariante (aus src/ Unterordnern, z.B. bc_a5120, pc_1715)
  - Tab 2: Dynamische Systemkonfiguration (Hardware, RAM-Disk, Laufwerke, Schnittstellen)
           basierend auf Kconfig.system der gewählten Variante
  - Tab 3: Build-Optionen (Ausgabeformat: OS, IMG, HFE, SCP, Diskette schreiben)
  - Build-Steuerung mit Echtzeit-Log-Ausgabe in separatem Thread
  - Tools-Menü zum Starten von ReadDisk und WriteDisk
  - Hilfe-Menü mit README-Anzeige (Markdown-Rendering) und CP/A-Dokumentation

Die Konfiguration wird im Kconfig-Format (.config) gespeichert und über
patch_mac.py bidirektional mit den Assembler-Quelldateien (.mac) synchronisiert.

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)

Verwendung:
    python cpa_build.py
"""

import os
import sys
import re
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ---------------------------------------------------------------------------
# Projektverzeichnis ermitteln und config/-Verzeichnis in den Importpfad
# aufnehmen, damit cpa_kconfig_parser und cpa_builder importiert werden können
# ---------------------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_DIR, 'config'))

# Kconfig-Parser für die hierarchische Konfigurationsstruktur
from cpa_kconfig_parser import parse_kconfig, KconfigConfig, KconfigChoice, KconfigMenu
# Build-Engine für Assemblierung, Linken und Image-Erzeugung
from cpa_builder import CPABuilder

# Pfad zur zentralen Konfigurationsdatei (.config im Kconfig-Format)
CONFIG_FILE = os.path.join(PROJECT_DIR, '.config')


# ============================================================================
# ScrollableFrame - Scrollbarer Frame für lange Konfigurationsseiten
# ============================================================================

class ScrollableFrame(ttk.Frame):
    """Frame mit vertikalem Scrollbalken für lange Konfigurationsseiten.

    Wird für die Tabs Systemvariante, Systemkonfiguration und Build-Optionen
    verwendet, damit auch umfangreiche Konfigurationen vollständig angezeigt
    werden können. Der innere Frame (self.inner) passt sich automatisch an
    die Canvas-Breite an und unterstützt Mausrad-Scrolling.
    """

    def __init__(self, parent):
        super().__init__(parent)
        # Canvas als Scroll-Container
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        # Innerer Frame, der die eigentlichen Widgets enthält
        self.inner = ttk.Frame(self.canvas)

        # Events: Scrollbereich und Breitenanpassung bei Größenänderung
        self.inner.bind('<Configure>', self._on_inner_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        # Inneren Frame als Fenster im Canvas einbetten (oben links verankert)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mausrad-Scrolling: nur aktiv wenn Maus über dem Canvas ist
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)

    def _on_inner_configure(self, event):
        """Scrollbereich aktualisieren wenn sich der innere Frame ändert."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Inneren Frame auf Canvas-Breite anpassen wenn Canvas skaliert wird."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        """Mausrad-Events global binden (bei Maus-Enter über Canvas)."""
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)   # Linux: Hoch
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)   # Linux: Runter

    def _unbind_mousewheel(self, event):
        """Mausrad-Events global entbinden (bei Maus-Leave)."""
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _on_mousewheel(self, event):
        """Mausrad-Scrolling verarbeiten (Linux Button-4/5 und Windows/macOS delta)."""
        if event.num == 4:          # Linux: Mausrad hoch
            self.canvas.yview_scroll(-3, 'units')
        elif event.num == 5:        # Linux: Mausrad runter
            self.canvas.yview_scroll(3, 'units')
        elif event.delta:           # Windows/macOS: delta-Wert
            self.canvas.yview_scroll(int(-event.delta / 120), 'units')


# ============================================================================
# CPAWorkbenchApp - Hauptanwendung der CP/A Workbench
# ============================================================================

class CPAWorkbenchApp:
    """Hauptanwendung für das CP/A Workbench GUI.

    Verwaltet die gesamte Benutzeroberfläche mit drei Tabs:
    - Systemvariante: Auswahl des Ziel-Hardwaresystems (z.B. A5120, PC1715)
    - Systemkonfiguration: Dynamisch aus Kconfig.system erzeugte Optionen
    - Build-Optionen: Ausgabeformat und Diskettentyp

    Die Klasse steuert außerdem den Build-Prozess (in separatem Thread),
    die Konfigurationsverwaltung (.config Datei) und die Integration mit
    patch_mac.py für die bidirektionale Synchronisation der Assembler-Quellen.
    """

    def __init__(self):
        """Fenster initialisieren, Builder erstellen, UI aufbauen und Config laden."""
        self.root = tk.Tk()
        self.root.title('CP/A Workbench - Konfigurations- und Build-System')
        self.root.geometry('1200x900')
        self.root.minsize(900, 600)

        self.config = {}                # Aktuelle Konfiguration (Dict: CONFIG_KEY → Wert)
        self.variant_var = tk.StringVar()  # Gewählte Systemvariante als String
        self.system_widgets = {}        # CONFIG_KEY → (Typ, tk.Variable) für System-Configs
        self.build_widgets = {}         # CONFIG_KEY → (Typ, tk.Variable) für Build-Configs
        self.log_queue = queue.Queue()  # Thread-sichere Warteschlange für Log-Nachrichten
        self.build_running = False      # Flag: läuft gerade ein Build?
        self._loading = False           # Flag: UI-Aufbau läuft, Auto-Save unterdrücken

        # Build-Engine mit Callback für Log-Ausgaben in die GUI
        self.builder = CPABuilder(PROJECT_DIR, log_callback=self._queue_log)

        self._loading = True            # Auto-Save während UI-Aufbau unterdrücken
        self._create_ui()               # Oberfläche aufbauen
        self._load_config()             # Konfiguration aus .config laden
        self._poll_log()                # Log-Polling-Timer starten

    # -----------------------------------------------------------------------
    # UI aufbauen - Menüleiste, Tabs und Log-Bereich
    # -----------------------------------------------------------------------

    def _create_ui(self):
        """Hauptoberfläche erstellen mit Menüleiste, Notebook-Tabs und Log-Bereich."""
        # --- Menüleiste ---
        menubar = tk.Menu(self.root)

        # Datei-Menü mit Beenden-Eintrag
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Beenden', command=self._on_close)
        menubar.add_cascade(label='Datei', menu=file_menu)

        # Tools-Menü zum Starten externer Werkzeuge (ReadDisk/WriteDisk)
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label='ReadDisk (Diskette einlesen)',
                               command=self._launch_readdisk)
        tools_menu.add_command(label='WriteDisk (Diskette schreiben)',
                               command=self._launch_writedisk)
        menubar.add_cascade(label='Tools', menu=tools_menu)

        # Hilfe-Menü mit README und CP/A-Dokumentation
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label='README anzeigen',
                             command=lambda: self._show_readme())
        help_menu.add_command(label='CP/A Dokumentation (cpa_doc.txt)',
                             command=lambda: self._show_document(
                                 os.path.join(PROJECT_DIR, 'doc', 'cpa_doc.txt'),
                                 'CP/A Dokumentation'))
        menubar.add_cascade(label='Hilfe', menu=help_menu)

        self.root.config(menu=menubar)

        # Hauptlayout: Oben Notebook, unten Log + Buttons
        main_pane = ttk.PanedWindow(self.root, orient='vertical')
        main_pane.pack(fill='both', expand=True, padx=5, pady=5)

        # Notebook (Tabs) für die drei Konfigurationsbereiche
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=3)

        # Tab 1: Systemvariante (welche Hardware soll gebaut werden?)
        self.variant_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.variant_tab, text='  Systemvariante  ')
        self._create_variant_tab()

        # Tab 2: Systemkonfiguration (wird dynamisch bei Variantenwechsel geladen)
        self.system_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.system_tab, text='  Systemkonfiguration  ')

        # Tab 3: Build-Optionen (Ausgabeformat, Diskettentyp)
        self.build_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.build_tab, text='  Build-Optionen  ')
        self._create_build_tab()

        # --- Unterer Bereich: Aktions-Buttons und scrollbarer Log-Bereich ---
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=2)

        # Button-Leiste: Speichern, Clean, Bauen, Log löschen
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        self.btn_save = ttk.Button(btn_frame, text='Patch .mac', command=self._do_patch_mac)
        self.btn_save.pack(side='left', padx=2)

        self.btn_clean = ttk.Button(btn_frame, text='Clean', command=self._do_clean)
        self.btn_clean.pack(side='left', padx=2)

        self.btn_build = ttk.Button(btn_frame, text='Bauen', command=self._do_build,
                                    style='Accent.TButton')
        self.btn_build.pack(side='left', padx=2)

        self.btn_clear_log = ttk.Button(btn_frame, text='Log löschen',
                                        command=self._clear_log)
        self.btn_clear_log.pack(side='right', padx=2)

        # Status-Anzeige rechts in der Button-Leiste
        self.status_var = tk.StringVar(value='Bereit')
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='right', padx=10)

        # Scrollbarer Log-Bereich mit Monospace-Schrift
        self.log_text = scrolledtext.ScrolledText(
            bottom_frame, height=12, state='disabled',
            font=('Consolas', 9) if sys.platform == 'win32' else ('monospace', 9),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)

        # Variable für optionale Hilfe-Anzeige
        self.help_var = tk.StringVar()

        # Fenster-Schließen-Event abfangen (für Build-Abbruch-Warnung)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    # -----------------------------------------------------------------------
    # Tab 1: Systemvariante - Auswahl der Ziel-Hardware
    # -----------------------------------------------------------------------

    def _create_variant_tab(self):
        """Varianten-Auswahl-Tab aufbauen.

        Liest alle verfügbaren Systemvarianten aus dem src/-Verzeichnis
        (z.B. bc_a5120, pc_1715) und erstellt Radiobuttons mit optionaler
        Beschreibung aus about.txt.
        """
        frame = self.variant_tab.inner

        ttk.Label(frame, text='Systemvariante auswählen:',
                  font=('', 11, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        ttk.Label(frame, text='Wähle die gewünschte Hardwarevariante. '
                  'Die Konfiguration wird aus src/<variante>/ geladen.',
                  wraplength=800).pack(anchor='w', padx=10, pady=(0, 10))

        # Verfügbare Varianten ermitteln (Name + Beschreibung aus about.txt)
        self.variants = self.builder.get_available_variants()
        self.variant_radios = []

        # Für jede Variante einen Radiobutton mit optionalem Beschreibungstext erstellen
        for name, about in self.variants:
            var_frame = ttk.Frame(frame)
            var_frame.pack(fill='x', padx=10, pady=2)

            rb = ttk.Radiobutton(
                var_frame, text=name, variable=self.variant_var, value=name,
                command=self._on_variant_changed
            )
            rb.pack(side='left')
            self.variant_radios.append(rb)

            if about:
                ttk.Label(var_frame, text=f'  — {about}',
                          foreground='gray').pack(side='left', padx=(5, 0))

        # Erste Variante als Vorgabe auswählen
        if self.variants:
            self.variant_var.set(self.variants[0][0])

    # -----------------------------------------------------------------------
    # Tab 2: Systemkonfiguration - dynamisch aus Kconfig.system erzeugt
    # -----------------------------------------------------------------------

    def _refresh_system_tab(self):
        """System-Tab für die gewählte Variante neu aufbauen.

        Löscht alle vorhandenen Widgets, parst die zugehörige Kconfig.system
        und rendert die Konfigurationsoptionen (Choice, Config, Menu, Hint)
        als interaktive GUI-Elemente.
        """
        # Alte Widgets entfernen
        for w in self.system_tab.inner.winfo_children():
            w.destroy()
        self.system_widgets.clear()

        variant = self.variant_var.get()
        if not variant:
            ttk.Label(self.system_tab.inner,
                      text='Keine Variante gewählt.').pack(padx=10, pady=10)
            return

        kconfig_path = os.path.join(PROJECT_DIR, 'config', variant, 'Kconfig.system')
        if not os.path.isfile(kconfig_path):
            ttk.Label(self.system_tab.inner,
                      text=f'Keine Kconfig.system für "{variant}" vorhanden.\n'
                           f'Systemkonfiguration nicht verfügbar.',
                      foreground='gray').pack(padx=10, pady=10)
            return

        # Kconfig parsen
        kconfig = parse_kconfig(kconfig_path)

        # Titel
        if kconfig.title:
            ttk.Label(self.system_tab.inner, text=kconfig.title,
                      font=('', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))

        # Items im tabellarischen Grid-Layout rendern
        content = ttk.Frame(self.system_tab.inner)
        content.pack(fill='x', padx=0, pady=0)
        self._render_kconfig_items(content, kconfig.children,
                                   self.system_widgets, 'CONFIG_')

    @staticmethod
    def _display_help_text(text):
        """Hilfetexte aufbereiten: source= Zeilen entfernen."""
        if not text:
            return ''
        lines = text.strip().split('\n')
        filtered = [l for l in lines if not l.strip().startswith('source=')]
        return '\n'.join(filtered).strip()

    def _render_kconfig_items(self, parent, items, widgets_dict, prefix):
        """Kconfig-Elemente als tabellarisches Grid rendern.

        Jedes Element wird je nach Typ (Menu, Choice, Config, Hint) in
        ein dreispaltiges Grid-Layout eingesetzt:
        Spalte 0: Label, Spalte 1: Widget (Checkbox/Combobox/Entry), Spalte 2: Hilfetext.
        """
        parent.columnconfigure(0, weight=0)   # Label-Spalte
        parent.columnconfigure(1, weight=0)   # Widget-Spalte
        parent.columnconfigure(2, weight=1)   # Hilfetext-Spalte

        row = [0]  # Mutable Zeilenzähler
        for item in items:
            if isinstance(item, KconfigMenu):
                self._render_menu(parent, item, widgets_dict, prefix, row)
            elif isinstance(item, KconfigChoice):
                self._render_choice(parent, item, widgets_dict, prefix, row)
            elif isinstance(item, KconfigConfig):
                if item.name.startswith('HINT_'):
                    self._render_hint(parent, item, row)
                else:
                    self._render_config(parent, item, widgets_dict, prefix, row)

    def _render_menu(self, parent, menu, widgets_dict, prefix, row):
        """menu...endmenu als LabelFrame rendern."""
        lf = ttk.LabelFrame(parent, text=menu.title, padding=10)
        lf.grid(row=row[0], column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        row[0] += 1
        self._render_kconfig_items(lf, menu.children, widgets_dict, prefix)

    def _render_hint(self, parent, cfg, row):
        """HINT_-Eintrag als Infobox mit Hilfetext rendern."""
        help_text = self._display_help_text(cfg.help_text)
        if not help_text:
            return
        info_frame = ttk.LabelFrame(parent, text=cfg.label or 'Hinweis', padding=8)
        info_frame.grid(row=row[0], column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        row[0] += 1
        ttk.Label(info_frame, text=help_text, wraplength=800,
                  foreground='#555555', font=('', 9)).pack(anchor='w')

    def _render_choice(self, parent, choice, widgets_dict, prefix, row):
        """choice...endchoice als Label + Combobox mit dynamischem Hilfetext rendern.

        Eine Choice-Gruppe stellt eine Exklusiv-Auswahl dar (z.B. RAM-Disk-Typ).
        Alle Optionen werden in einer Combobox zusammengefasst. Der Hilfetext
        rechts neben der Combobox aktualisiert sich bei Auswahländerung.
        """
        if not choice.configs:
            return

        # Choice-level Hilfetext anzeigen (z.B. bei RAM Disk Typ)
        choice_help = self._display_help_text(choice.help_text)
        if choice_help:
            info_label = ttk.Label(parent, text=choice_help, wraplength=800,
                                  foreground='#555555', font=('', 9))
            info_label.grid(row=row[0], column=0, columnspan=3, sticky='ew',
                           padx=15, pady=(0, 3))
            row[0] += 1

        # Combobox-Werte aus den Config-Einträgen zusammenstellen (HINT_ ausfiltern)
        options = []
        option_configs = []
        for cfg in choice.configs:
            if cfg.name.startswith('HINT_'):
                continue  # Hinweis-Einträge nicht als Auswahl anzeigen
            display = cfg.label or cfg.name
            options.append((cfg.name, display))
            option_configs.append(cfg)

        if not options:
            return

        # Combobox-Breite an längsten Eintrag anpassen (max 55 Zeichen,
        # Dropdown zeigt immer den vollen Text)
        max_len = max(len(display) for _, display in options)
        combo_width = min(max(max_len + 2, 20), 55)

        # Spalte 0: Label
        label_text = choice.prompt or 'Auswahl'
        ttk.Label(parent, text=label_text + ':', anchor='w').grid(
            row=row[0], column=0, sticky='w', padx=(5, 10), pady=3)

        # Spalte 1: Combobox
        display_values = [o[1] for o in options]
        var = tk.StringVar()
        combo = ttk.Combobox(parent, textvariable=var, values=display_values,
                             state='readonly', width=combo_width)
        combo.grid(row=row[0], column=1, sticky='w', padx=5, pady=3)

        # Default setzen
        default_name = choice.default
        default_idx = 0
        for i, (name, _) in enumerate(options):
            if name == default_name:
                default_idx = i
                break
        combo.current(default_idx)

        # Spalte 2: dynamischer Hilfetext der gewählten Option
        help_label = ttk.Label(parent, text='', wraplength=400,
                               foreground='#555555', font=('', 9))
        help_label.grid(row=row[0], column=2, sticky='nw', padx=(10, 5), pady=3)

        # Hilfetext-Map aufbauen: Anzeigename → bereinigter Hilfetext (ohne source= Zeilen)
        help_map = {}
        for (cfg_name, display), cfg in zip(options, option_configs):
            ht = self._display_help_text(cfg.help_text)
            if ht:
                help_map[display] = ht

        def update_help(event=None):
            """Hilfetext rechts neben der Combobox bei Auswahländerung aktualisieren."""
            sel = var.get()
            help_label.config(text=help_map.get(sel, ''))

        def on_combo_selected(event=None):
            update_help(event)
            self._auto_save_config()

        combo.bind('<<ComboboxSelected>>', on_combo_selected)
        update_help()  # Initialen Hilfetext für die Vorgabe-Auswahl setzen

        # Widget speichern: Alle Config-Namen dieser Choice-Gruppe teilen sich
        # die gleiche Variable (nur eine Option kann aktiv sein)
        choice_data = {'var': var, 'options': options, 'combo': combo,
                       'update_help': update_help}
        for cfg_name, _ in options:
            widgets_dict[prefix + cfg_name] = ('choice', choice_data)

        row[0] += 1

    def _render_config(self, parent, cfg, widgets_dict, prefix, row):
        """Einzelnes config-Element als Checkbox (bool) oder Entry (string) mit Hilfetext rendern.

        Bool-Optionen werden als Checkbox dargestellt, String-Optionen als Eingabefeld.
        In Spalte 2 erscheint ggf. ein erklärender Hilfetext aus der Kconfig-Datei.
        """
        config_key = prefix + cfg.name
        help_text = self._display_help_text(cfg.help_text)

        if cfg.config_type == 'string':
            # Spalte 0: Label
            ttk.Label(parent, text=(cfg.label or cfg.name) + ':', anchor='w').grid(
                row=row[0], column=0, sticky='w', padx=(5, 10), pady=2)
            # Spalte 1: Entry
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var, width=20)
            entry.grid(row=row[0], column=1, sticky='w', padx=5, pady=2)
            if cfg.default and cfg.default not in ('n', 'y'):
                default_val = cfg.default.strip('"').strip("'")
                var.set(default_val)
            widgets_dict[config_key] = ('string', var)
            # Auto-Sync bei Fokusverlust
            entry.bind('<FocusOut>', self._auto_save_config)
        else:
            # Bool: Checkbox über Spalte 0+1
            var = tk.BooleanVar(value=(cfg.default == 'y'))
            cb = ttk.Checkbutton(parent, text=cfg.label or cfg.name, variable=var)
            cb.grid(row=row[0], column=0, columnspan=2, sticky='w', padx=5, pady=2)
            widgets_dict[config_key] = ('bool', var)
            # Auto-Sync bei Klick
            var.trace_add('write', self._auto_save_config)

        # Spalte 2: Hilfetext
        if help_text:
            ttk.Label(parent, text=help_text, wraplength=400,
                      foreground='#555555', font=('', 9)).grid(
                row=row[0], column=2, sticky='nw', padx=(10, 5), pady=2)

        row[0] += 1

    # -----------------------------------------------------------------------
    # Tab 3: Build-Optionen - Ausgabeformat und Diskettentyp
    # -----------------------------------------------------------------------

    def _create_build_tab(self):
        """Build-Optionen-Tab aufbauen.

        Lädt die Kconfig.build-Datei und rendert die darin definierten
        Build-Ziele (OS, Diskimage, HFE, SCP, Schreiben) und Diskettentyp-Optionen.
        """
        kconfig_path = os.path.join(PROJECT_DIR, 'config', 'Kconfig.build')
        if not os.path.isfile(kconfig_path):
            ttk.Label(self.build_tab.inner,
                      text='Kconfig.build nicht gefunden.').pack(padx=10, pady=10)
            return

        kconfig = parse_kconfig(kconfig_path)

        if kconfig.title:
            ttk.Label(self.build_tab.inner, text=kconfig.title,
                      font=('', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))

        # Items im tabellarischen Grid-Layout rendern
        content = ttk.Frame(self.build_tab.inner)
        content.pack(fill='x', padx=0, pady=0)
        self._render_kconfig_items(content, kconfig.children,
                                   self.build_widgets, 'CONFIG_')

    # -----------------------------------------------------------------------
    # Hilfe-Anzeige - Popup-Fenster, Textdateien, README mit Markdown
    # -----------------------------------------------------------------------

    def _show_help(self, text):
        """Hilfetext in einem Popup-Fenster anzeigen."""
        win = tk.Toplevel(self.root)
        win.title('Hilfe')
        win.geometry('500x300')
        win.transient(self.root)
        txt = scrolledtext.ScrolledText(win, wrap='word', font=('', 10))
        txt.pack(fill='both', expand=True, padx=5, pady=5)
        txt.insert('1.0', text)
        txt.config(state='disabled')
        ttk.Button(win, text='Schließen', command=win.destroy).pack(pady=5)
    def _show_document(self, filepath, title):
        """Textdatei in einem neuen Fenster anzeigen."""
        if not os.path.isfile(filepath):
            messagebox.showerror('Fehler', f'Datei nicht gefunden:\n{filepath}')
            return
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry('800x600')
        txt = scrolledtext.ScrolledText(win, wrap='word',
                                        font=('Consolas', 10) if sys.platform == 'win32'
                                        else ('monospace', 10))
        txt.pack(fill='both', expand=True, padx=5, pady=5)
        txt.insert('1.0', content)
        txt.config(state='disabled')
        ttk.Button(win, text='Schlie\u00dfen', command=win.destroy).pack(pady=5)

    # -----------------------------------------------------------------------
    # Externe Tools starten (ReadDisk / WriteDisk)
    # -----------------------------------------------------------------------

    def _launch_readdisk(self):
        """ReadDisk-Tool als separaten Prozess starten (tools/readDiskUI.py)."""
        script = os.path.join(PROJECT_DIR, 'tools', 'readDiskUI.py')
        subprocess.Popen([sys.executable, script], cwd=PROJECT_DIR)

    def _launch_writedisk(self):
        """WriteDisk-Tool als separaten Prozess starten (tools/writeDiskUI.py)."""
        script = os.path.join(PROJECT_DIR, 'tools', 'writeDiskUI.py')
        subprocess.Popen([sys.executable, script], cwd=PROJECT_DIR)

    def _show_readme(self):
        """README.md mit einfacher Markdown-Formatierung in einem Fenster anzeigen.

        Unterstützt Überschriften (h1-h3), Fettdruck, Kursiv, Inline-Code,
        Code-Blöcke und Aufzählungslisten.
        """
        filepath = os.path.join(PROJECT_DIR, 'README.md')
        if not os.path.isfile(filepath):
            messagebox.showerror('Fehler', f'Datei nicht gefunden:\n{filepath}')
            return
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        win = tk.Toplevel(self.root)
        win.title('README - CP/A Workbench')
        win.geometry('900x700')
        txt = scrolledtext.ScrolledText(win, wrap='word', font=('', 10),
                                        padx=15, pady=10)
        txt.pack(fill='both', expand=True, padx=5, pady=5)

        # Markdown-Tags konfigurieren
        txt.tag_configure('h1', font=('', 16, 'bold'), spacing3=8)
        txt.tag_configure('h2', font=('', 14, 'bold'), spacing1=12, spacing3=6)
        txt.tag_configure('h3', font=('', 12, 'bold'), spacing1=10, spacing3=4)
        txt.tag_configure('bold', font=('', 10, 'bold'))
        txt.tag_configure('italic', font=('', 10, 'italic'))
        txt.tag_configure('code', font=('Consolas', 9) if sys.platform == 'win32'
                          else ('monospace', 9), background='#f0f0f0')
        txt.tag_configure('codeblock', font=('Consolas', 9) if sys.platform == 'win32'
                          else ('monospace', 9), background='#f0f0f0',
                          lmargin1=20, lmargin2=20, spacing1=4, spacing3=4)
        txt.tag_configure('bullet', lmargin1=20, lmargin2=35)

        self._render_markdown(txt, content)
        txt.config(state='disabled')
        ttk.Button(win, text='Schlie\u00dfen', command=win.destroy).pack(pady=5)

    @staticmethod
    def _render_markdown(txt, content):
        """Einfache Markdown-Formatierung in ein Text-Widget rendern.

        Verarbeitet zeilenweise: Code-Blöcke (```), Überschriften (#, ##, ###),
        Aufzählungen (- / *) und Inline-Formatierungen (**bold**, *italic*, `code`).
        """
        in_code_block = False
        for line in content.split('\n'):
            # Code-Block Start/Ende
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                txt.insert('end', line + '\n', 'codeblock')
                continue

            # Überschriften
            if line.startswith('### '):
                txt.insert('end', line[4:] + '\n', 'h3')
            elif line.startswith('## '):
                txt.insert('end', line[3:] + '\n', 'h2')
            elif line.startswith('# '):
                txt.insert('end', line[2:] + '\n', 'h1')
            elif line.startswith('- ') or line.startswith('* '):
                # Aufzählung
                txt.insert('end', '\u2022 ' + line[2:] + '\n', 'bullet')
            elif line.startswith('  - ') or line.startswith('  * '):
                txt.insert('end', '    \u2022 ' + line[4:] + '\n', 'bullet')
            else:
                # Inline-Formatierung: **bold**, *italic*, `code` erkennen
                # und mit entsprechenden Tags einfügen
                pos = 0
                remaining = line
                while remaining:
                    # Inline-Code
                    m = re.search(r'`([^`]+)`', remaining)
                    m_bold = re.search(r'\*\*([^*]+)\*\*', remaining)
                    m_italic = re.search(r'(?<!\*)\*([^*]+)\*(?!\*)', remaining)

                    # Frühestes Inline-Match finden (Position im String)
                    matches = []
                    if m:
                        matches.append(('code', m))
                    if m_bold:
                        matches.append(('bold', m_bold))
                    if m_italic:
                        matches.append(('italic', m_italic))

                    if not matches:
                        txt.insert('end', remaining)
                        break

                    matches.sort(key=lambda x: x[1].start())
                    tag, match = matches[0]

                    # Text vor dem Match
                    if match.start() > 0:
                        txt.insert('end', remaining[:match.start()])
                    txt.insert('end', match.group(1), tag)
                    remaining = remaining[match.end():]

                txt.insert('end', '\n')

    # -----------------------------------------------------------------------
    # Konfiguration laden/speichern - Synchronisation zwischen GUI und .config
    # -----------------------------------------------------------------------

    def _load_config(self):
        """Konfiguration aus .config laden und alle GUI-Widgets aktualisieren."""
        self._loading = True
        self.config = CPABuilder.load_config(CONFIG_FILE)
        self._config_to_gui()           # Config-Werte in GUI-Widgets übertragen
        self._on_variant_changed(save=False)  # System-Tab für gewählte Variante laden
        self._loading = False
        self.log_msg('[INFO] Konfiguration geladen.')

    def _auto_save_config(self, *args):
        """GUI-Werte automatisch in .config synchronisieren (Callback für Traces/Events)."""
        if self._loading:
            return
        self._gui_to_config()
        CPABuilder.save_config(self.config, CONFIG_FILE)

    def _save_config(self):
        """GUI-Werte sammeln und als .config-Datei speichern."""
        self._gui_to_config()           # GUI-Werte ins Config-Dict übernehmen
        CPABuilder.save_config(self.config, CONFIG_FILE)
        self.log_msg('[INFO] Konfiguration gespeichert.')

    def _do_patch_mac(self):
        """Aktuelle Konfiguration in die .mac-Quelldateien patchen."""
        self._auto_save_config()
        variant = self.variant_var.get()
        if not variant:
            messagebox.showerror('Fehler', 'Keine Systemvariante gewählt!')
            return
        kconfig_sys = os.path.join(PROJECT_DIR, 'config', variant, 'Kconfig.system')
        if os.path.isfile(kconfig_sys):
            try:
                self.builder.run_patch_mac(CONFIG_FILE, variant, 'patch')
                self.log_msg('[INFO] Konfiguration in .mac-Dateien geschrieben.')
            except Exception as e:
                self.log_msg(f'[FEHLER] patch_mac patch: {e}')

    def _config_to_gui(self):
        """Config-Dict → GUI-Widgets: Variante und Build-Optionen setzen."""
        # Variante aus Config ermitteln und Radiobutton setzen
        variant = self.builder.get_variant(self.config)
        if variant:
            self.variant_var.set(variant)

        # Build-Widgets mit gespeicherten Werten füllen
        self._apply_config_to_widgets(self.build_widgets)

    def _apply_config_to_widgets(self, widgets_dict):
        """Config-Werte auf ein Widget-Dict anwenden.

        Unterstützt drei Widget-Typen:
        - bool: Checkbox (True/False aus '=y' / 'is not set')
        - string: Eingabefeld (Textwert)
        - choice: Combobox (exklusive Auswahl aus mehreren Optionen)
        """
        applied_choices = set()  # Bereits verarbeitete Choice-Gruppen (deduplizieren)
        for config_key, (wtype, wdata) in widgets_dict.items():
            val = self.config.get(config_key)

            if wtype == 'bool':
                wdata.set(val == 'y' if val else False)

            elif wtype == 'string':
                if val is not None and val != 'None':
                    wdata.set(val)

            elif wtype == 'choice':
                choice_id = id(wdata)
                if choice_id in applied_choices:
                    continue
                applied_choices.add(choice_id)
                # Finde aktive Option
                for cfg_name, display in wdata['options']:
                    full_key = 'CONFIG_' + cfg_name
                    if self.config.get(full_key) == 'y':
                        wdata['var'].set(display)
                        break
                # Hilfetext für die aktive Option aktualisieren
                if 'update_help' in wdata:
                    wdata['update_help']()

    def _gui_to_config(self):
        """GUI-Widgets → Config-Dict: Alle Werte aus der Oberfläche sammeln."""
        # Variante: Alte VARIANT_ Einträge entfernen und neue setzen
        variant = self.variant_var.get()
        keys_to_remove = [k for k in self.config if k.startswith('CONFIG_VARIANT_')]
        for k in keys_to_remove:
            del self.config[k]
        # Neue Variante: nur die gewählte auf 'y' setzen, alle anderen None
        for name, _ in self.variants:
            key = f'CONFIG_VARIANT_{name}'
            self.config[key] = 'y' if name == variant else None

        # System-Widgets
        self._collect_widgets_to_config(self.system_widgets)

        # Build-Widgets
        self._collect_widgets_to_config(self.build_widgets)

    def _collect_widgets_to_config(self, widgets_dict):
        """Widget-Werte ins Config-Dict übernehmen.

        Durchläuft alle Widgets und schreibt deren aktuelle Werte
        in self.config. Bei Choice-Gruppen wird nur die gewählte
        Option auf 'y' gesetzt, alle anderen auf None.
        """
        processed_choices = set()
        for config_key, (wtype, wdata) in widgets_dict.items():
            if wtype == 'bool':
                self.config[config_key] = 'y' if wdata.get() else None

            elif wtype == 'string':
                val = wdata.get().strip()
                self.config[config_key] = val if val else None

            elif wtype == 'choice':
                choice_id = id(wdata)
                if choice_id in processed_choices:
                    continue
                processed_choices.add(choice_id)
                selected_display = wdata['var'].get()
                for cfg_name, display in wdata['options']:
                    full_key = 'CONFIG_' + cfg_name
                    self.config[full_key] = 'y' if display == selected_display else None

    # -----------------------------------------------------------------------
    # Variante gewechselt - System-Tab neu laden und Config synchronisieren
    # -----------------------------------------------------------------------

    def _on_variant_changed(self, save=True):
        """Wird aufgerufen, wenn die Systemvariante geändert wird.

        Führt patch_mac.py extract aus (um aktuelle Werte aus den
        .mac-Quellen zu lesen), lädt die Konfiguration neu und baut
        den System-Tab für die neue Variante auf.
        Die .config ist durch Auto-Sync bereits aktuell.
        """
        variant = self.variant_var.get()
        if not variant:
            return

        if save:
            # Aktuelle Werte sichern (Auto-Sync hat ggf. nicht alle erfasst)
            self._gui_to_config()

        # Alte SYSTEM_ Einträge entfernen
        keys_to_remove = [k for k in self.config if k.startswith('CONFIG_SYSTEM_')]
        for k in keys_to_remove:
            del self.config[k]

        # Config speichern für patch_mac extract
        CPABuilder.save_config(self.config, CONFIG_FILE)

        # patch_mac.py extract ausführen (liest aktuelle Werte aus den Quellen)
        kconfig_sys = os.path.join(PROJECT_DIR, 'config', variant, 'Kconfig.system')
        if os.path.isfile(kconfig_sys):
            try:
                self.builder.run_patch_mac(CONFIG_FILE, variant, 'extract')
                # Aktualisierte Config laden
                self.config = CPABuilder.load_config(CONFIG_FILE)
            except Exception as e:
                self.log_msg(f'[WARNUNG] patch_mac extract: {e}')

        # System-Tab neu aufbauen (Auto-Save unterdrücken während Widgets erstellt werden)
        self._loading = True
        self._refresh_system_tab()

        # System-Widgets mit geladenen Werten füllen
        self._apply_config_to_widgets(self.system_widgets)
        self._loading = False

        self.log_msg(f'[INFO] Variante gewechselt: {variant}')

    # -----------------------------------------------------------------------
    # Build-Aktionen - Clean und Build mit verschiedenen Targets
    # -----------------------------------------------------------------------

    def _get_build_target(self):
        """Build-Target aus den Build-Widgets ermitteln.

        Mappt die CONFIG_BUILD_TARGET_* Schlüssel auf die internen
        Target-Namen der Build-Engine (os, diskimage, diskimagehfe, etc.).
        """
        target_map = {
            'CONFIG_BUILD_TARGET_OS': 'os',
            'CONFIG_BUILD_TARGET_DISKIMAGE': 'diskimage',
            'CONFIG_BUILD_TARGET_DISKIMAGEHFE': 'diskimagehfe',
            'CONFIG_BUILD_TARGET_DISKIMAGESCP': 'diskimagescp',
            'CONFIG_BUILD_TARGET_WRITEIMAGE': 'writeimage',
        }
        for config_key, target in target_map.items():
            if self.config.get(config_key) == 'y':
                return target
        return 'os'

    def _do_clean(self):
        """Clean durchführen."""
        if self.build_running:
            messagebox.showwarning('Warnung', 'Build läuft bereits!')
            return
        self.builder.log_callback = self._queue_log
        self.builder.clean()

    def _do_build(self):
        """Build starten in einem separaten Thread.

        Ablauf: Config speichern → patch_mac patch (Assembler-Quellen aktualisieren)
        → optional Clean → Build-Engine für gewähltes Target aufrufen.
        Der Build läuft im Hintergrund-Thread, damit die GUI responsiv bleibt.
        """
        if self.build_running:
            messagebox.showwarning('Warnung', 'Build läuft bereits!')
            return

        # .mac-Dateien patchen (speichert auch .config)
        self._do_patch_mac()

        variant = self.variant_var.get()
        if not variant:
            messagebox.showerror('Fehler', 'Keine Systemvariante gewählt!')
            return

        # Clean wenn in den Build-Optionen aktiviert
        if self.config.get('CONFIG_BUILD_CLEAN') == 'y':
            self.builder.clean()

        # Build-Target ermitteln
        target = self._get_build_target()

        # Build in separatem Thread starten, damit die GUI nicht blockiert
        self.build_running = True
        self._set_buttons_state('disabled')
        self.status_var.set(f'Build läuft: {target}...')

        def build_thread():
            try:
                self.builder.build(target, self.config)
                self._queue_log('[INFO] Build erfolgreich abgeschlossen!')
            except Exception as e:
                self._queue_log(f'[FEHLER] Build fehlgeschlagen: {e}')
            finally:
                self.build_running = False
                self.root.after(0, lambda: self._set_buttons_state('normal'))
                self.root.after(0, lambda: self.status_var.set('Bereit'))

        thread = threading.Thread(target=build_thread, daemon=True)
        thread.start()

    def _set_buttons_state(self, state):
        """Alle Aktions-Buttons aktivieren/deaktivieren."""
        self.btn_build.config(state=state)
        self.btn_clean.config(state=state)
        self.btn_save.config(state=state)

    # -----------------------------------------------------------------------
    # Logging - Thread-sichere Log-Ausgabe in der GUI
    # -----------------------------------------------------------------------

    def _queue_log(self, msg):
        """Log-Nachricht thread-sicher in die Queue einreihen (für Build-Thread)."""
        self.log_queue.put(msg)

    def log_msg(self, msg):
        """Log-Nachricht direkt im GUI-Text-Widget ausgeben (nur vom Main-Thread)."""
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _poll_log(self):
        """Log-Queue periodisch abfragen und Nachrichten im GUI anzeigen.

        Wird alle 100ms per Timer aufgerufen, um Log-Nachrichten aus dem
        Build-Thread in das Text-Widget zu übertragen.
        """
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.log_msg(msg)
            except queue.Empty:
                break
        self.root.after(100, self._poll_log)

    def _clear_log(self):
        """Log-Bereich leeren."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    # -----------------------------------------------------------------------
    # Beenden - Fenster schließen mit Build-Abbruch-Warnung
    # -----------------------------------------------------------------------

    def _on_close(self):
        """Anwendung beenden."""
        if self.build_running:
            if not messagebox.askyesno('Beenden',
                                       'Build läuft noch. Trotzdem beenden?'):
                return
        self.root.destroy()

    # -----------------------------------------------------------------------
    # Starten - Hauptschleife und Einstiegspunkt
    # -----------------------------------------------------------------------

    def run(self):
        """Hauptschleife starten."""
        self.root.mainloop()


def main():
    app = CPAWorkbenchApp()
    app.run()


if __name__ == '__main__':
    main()
