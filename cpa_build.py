#!/usr/bin/env python3
# Copyright (c) 2025 by olliy78
# SPDX-License-Identifier: MIT
"""
CP/A Workbench - Grafisches Konfigurations- und Build-System

Ersetzt das konsolenbasierte menuconfig und die Makefiles durch eine
grafische Tkinter-Oberfläche mit Mausbedienung.

Verwendung:
    python cpa_build.py

Funktionalität:
  - Tab 1: Auswahl der Systemvariante (aus src/ Unterordnern)
  - Tab 2: Systemkonfiguration (Hardware, RAM-Disk, Laufwerke, Schnittstellen)
  - Tab 3: Build-Optionen (Ausgabeformat, Diskettentyp)
  - Build-Steuerung mit Echtzeit-Log-Ausgabe
"""

import os
import sys
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Projektverzeichnis ermitteln
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_DIR, 'config'))

from cpa_kconfig_parser import parse_kconfig, KconfigConfig, KconfigChoice, KconfigMenu
from cpa_builder import CPABuilder


CONFIG_FILE = os.path.join(PROJECT_DIR, '.config')


class ScrollableFrame(ttk.Frame):
    """Frame mit vertikalem Scrollbalken für lange Konfigurationsseiten."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind('<Configure>', self._on_inner_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mausrad-Scrolling
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)

    def _on_inner_configure(self, event):
        """Scrollbereich aktualisieren wenn sich der innere Frame ändert."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Inneren Frame auf Canvas-Breite anpassen wenn Canvas skaliert wird."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, 'units')
        elif event.num == 5:
            self.canvas.yview_scroll(3, 'units')
        elif event.delta:
            self.canvas.yview_scroll(int(-event.delta / 120), 'units')


class CPAWorkbenchApp:
    """Hauptanwendung für das CP/A Workbench GUI."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('CP/A Workbench - Konfigurations- und Build-System')
        self.root.geometry('1200x900')
        self.root.minsize(900, 600)

        self.config = {}                # Aktuelle Konfiguration
        self.variant_var = tk.StringVar()
        self.system_widgets = {}        # name → tk.Variable für System-Configs
        self.build_widgets = {}         # name → tk.Variable für Build-Configs
        self.log_queue = queue.Queue()
        self.build_running = False

        self.builder = CPABuilder(PROJECT_DIR, log_callback=self._queue_log)

        self._create_ui()
        self._load_config()
        self._poll_log()

    # --- UI aufbauen ---

    def _create_ui(self):
        """Hauptoberfläche erstellen."""
        # Menüleiste
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Beenden', command=self._on_close)
        menubar.add_cascade(label='Datei', menu=file_menu)

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

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=3)

        # Tab 1: Systemvariante
        self.variant_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.variant_tab, text='  Systemvariante  ')
        self._create_variant_tab()

        # Tab 2: Systemkonfiguration (wird dynamisch geladen)
        self.system_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.system_tab, text='  Systemkonfiguration  ')

        # Tab 3: Build-Optionen
        self.build_tab = ScrollableFrame(self.notebook)
        self.notebook.add(self.build_tab, text='  Build-Optionen  ')
        self._create_build_tab()

        # Unterer Bereich: Buttons + Log
        bottom_frame = ttk.Frame(main_pane)
        main_pane.add(bottom_frame, weight=2)

        # Button-Leiste
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        self.btn_save = ttk.Button(btn_frame, text='Speichern', command=self._save_config)
        self.btn_save.pack(side='left', padx=2)

        self.btn_clean = ttk.Button(btn_frame, text='Clean', command=self._do_clean)
        self.btn_clean.pack(side='left', padx=2)

        self.btn_build = ttk.Button(btn_frame, text='Bauen', command=self._do_build,
                                    style='Accent.TButton')
        self.btn_build.pack(side='left', padx=2)

        self.btn_clear_log = ttk.Button(btn_frame, text='Log löschen',
                                        command=self._clear_log)
        self.btn_clear_log.pack(side='right', padx=2)

        # Status
        self.status_var = tk.StringVar(value='Bereit')
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='right', padx=10)

        # Log
        self.log_text = scrolledtext.ScrolledText(
            bottom_frame, height=12, state='disabled',
            font=('Consolas', 9) if sys.platform == 'win32' else ('monospace', 9),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)

        # Help-Fenster-Info
        self.help_var = tk.StringVar()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    # --- Tab 1: Systemvariante ---

    def _create_variant_tab(self):
        """Varianten-Auswahl-Tab aufbauen."""
        frame = self.variant_tab.inner

        ttk.Label(frame, text='Systemvariante auswählen:',
                  font=('', 11, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        ttk.Label(frame, text='Wähle die gewünschte Hardwarevariante. '
                  'Die Konfiguration wird aus src/<variante>/ geladen.',
                  wraplength=800).pack(anchor='w', padx=10, pady=(0, 10))

        self.variants = self.builder.get_available_variants()
        self.variant_radios = []

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

        if self.variants:
            self.variant_var.set(self.variants[0][0])

    # --- Tab 2: Systemkonfiguration ---

    def _refresh_system_tab(self):
        """System-Tab für die gewählte Variante neu aufbauen."""
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

        # Items rendern in eigenem Frame für Grid-Layout
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
        """Kconfig-Elemente als tabellarisches Grid rendern."""
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
        """choice...endchoice als Label + Combobox mit Hilfetext rendern."""
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

        # Combobox-Werte: (config_name, label_text)
        options = []
        option_configs = []
        for cfg in choice.configs:
            if cfg.name.startswith('HINT_'):
                continue
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

        # Hilfetext-Map aufbauen (ohne source= Zeilen)
        help_map = {}
        for (cfg_name, display), cfg in zip(options, option_configs):
            ht = self._display_help_text(cfg.help_text)
            if ht:
                help_map[display] = ht

        def update_help(event=None):
            sel = var.get()
            help_label.config(text=help_map.get(sel, ''))

        combo.bind('<<ComboboxSelected>>', update_help)
        update_help()  # Initialen Hilfetext setzen

        # Widget speichern: alle Config-Namen dieser Choice → gleiche Variable
        choice_data = {'var': var, 'options': options, 'combo': combo,
                       'update_help': update_help}
        for cfg_name, _ in options:
            widgets_dict[prefix + cfg_name] = ('choice', choice_data)

        row[0] += 1

    def _render_config(self, parent, cfg, widgets_dict, prefix, row):
        """Einzelnes config-Element als Checkbox oder Entry mit Hilfetext rendern."""
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
        else:
            # Bool: Checkbox über Spalte 0+1
            var = tk.BooleanVar(value=(cfg.default == 'y'))
            cb = ttk.Checkbutton(parent, text=cfg.label or cfg.name, variable=var)
            cb.grid(row=row[0], column=0, columnspan=2, sticky='w', padx=5, pady=2)
            widgets_dict[config_key] = ('bool', var)

        # Spalte 2: Hilfetext
        if help_text:
            ttk.Label(parent, text=help_text, wraplength=400,
                      foreground='#555555', font=('', 9)).grid(
                row=row[0], column=2, sticky='nw', padx=(10, 5), pady=2)

        row[0] += 1

    # --- Tab 3: Build-Optionen ---

    def _create_build_tab(self):
        """Build-Optionen-Tab aufbauen."""
        kconfig_path = os.path.join(PROJECT_DIR, 'config', 'Kconfig.build')
        if not os.path.isfile(kconfig_path):
            ttk.Label(self.build_tab.inner,
                      text='Kconfig.build nicht gefunden.').pack(padx=10, pady=10)
            return

        kconfig = parse_kconfig(kconfig_path)

        if kconfig.title:
            ttk.Label(self.build_tab.inner, text=kconfig.title,
                      font=('', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))

        # Items rendern in eigenem Frame für Grid-Layout
        content = ttk.Frame(self.build_tab.inner)
        content.pack(fill='x', padx=0, pady=0)
        self._render_kconfig_items(content, kconfig.children,
                                   self.build_widgets, 'CONFIG_')

    # --- Hilfe anzeigen ---

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

    def _show_readme(self):
        """README.md mit einfacher Markdown-Formatierung anzeigen."""
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
        """Einfache Markdown-Formatierung in ein Text-Widget rendern."""
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
                # Inline-Formatierung: **bold**, *italic*, `code`
                pos = 0
                remaining = line
                while remaining:
                    # Inline-Code
                    m = re.search(r'`([^`]+)`', remaining)
                    m_bold = re.search(r'\*\*([^*]+)\*\*', remaining)
                    m_italic = re.search(r'(?<!\*)\*([^*]+)\*(?!\*)', remaining)

                    # Frühestes Match finden
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
    # --- Konfiguration laden/speichern ---

    def _load_config(self):
        """Konfiguration aus .config laden und GUI aktualisieren."""
        self.config = CPABuilder.load_config(CONFIG_FILE)
        self._config_to_gui()
        self._on_variant_changed(save=False)
        self.log_msg('[INFO] Konfiguration geladen.')

    def _save_config(self):
        """GUI-Werte in .config speichern."""
        self._gui_to_config()
        CPABuilder.save_config(self.config, CONFIG_FILE)
        self.log_msg('[INFO] Konfiguration gespeichert.')

    def _config_to_gui(self):
        """Config-Dict → GUI-Widgets."""
        # Variante
        variant = self.builder.get_variant(self.config)
        if variant:
            self.variant_var.set(variant)

        # Build-Widgets
        self._apply_config_to_widgets(self.build_widgets)

    def _apply_config_to_widgets(self, widgets_dict):
        """Config-Werte auf Widget-Dict anwenden."""
        applied_choices = set()
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
                # Hilfetext aktualisieren
                if 'update_help' in wdata:
                    wdata['update_help']()

    def _gui_to_config(self):
        """GUI-Widgets → Config-Dict."""
        # Variante
        variant = self.variant_var.get()
        # Alte VARIANT_ Einträge entfernen
        keys_to_remove = [k for k in self.config if k.startswith('CONFIG_VARIANT_')]
        for k in keys_to_remove:
            del self.config[k]
        # Neue Variante setzen
        for name, _ in self.variants:
            key = f'CONFIG_VARIANT_{name}'
            self.config[key] = 'y' if name == variant else None

        # System-Widgets
        self._collect_widgets_to_config(self.system_widgets)

        # Build-Widgets
        self._collect_widgets_to_config(self.build_widgets)

    def _collect_widgets_to_config(self, widgets_dict):
        """Widget-Werte ins Config-Dict übernehmen."""
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

    # --- Variante gewechselt ---

    def _on_variant_changed(self, save=True):
        """Wird aufgerufen, wenn die Systemvariante geändert wird."""
        variant = self.variant_var.get()
        if not variant:
            return

        if save:
            # Aktuelle Werte sichern, bevor System-Tab neu geladen wird
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

        # System-Tab neu aufbauen
        self._refresh_system_tab()

        # System-Widgets mit geladenen Werten füllen
        self._apply_config_to_widgets(self.system_widgets)

        self.log_msg(f'[INFO] Variante gewechselt: {variant}')

    # --- Build-Aktionen ---

    def _get_build_target(self):
        """Build-Target aus den Build-Widgets ermitteln."""
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
        """Build starten (in separatem Thread)."""
        if self.build_running:
            messagebox.showwarning('Warnung', 'Build läuft bereits!')
            return

        # Konfiguration speichern
        self._save_config()

        variant = self.variant_var.get()
        if not variant:
            messagebox.showerror('Fehler', 'Keine Systemvariante gewählt!')
            return

        # patch_mac.py patch ausführen
        kconfig_sys = os.path.join(PROJECT_DIR, 'config', variant, 'Kconfig.system')
        if os.path.isfile(kconfig_sys):
            try:
                self.builder.run_patch_mac(CONFIG_FILE, variant, 'patch')
            except Exception as e:
                self.log_msg(f'[FEHLER] patch_mac patch: {e}')
                return

        # Clean wenn gewünscht
        if self.config.get('CONFIG_BUILD_CLEAN') == 'y':
            self.builder.clean()

        # Build-Target ermitteln
        target = self._get_build_target()

        # Build in separatem Thread starten
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

    # --- Logging ---

    def _queue_log(self, msg):
        """Log-Nachricht in Queue einreihen (thread-safe)."""
        self.log_queue.put(msg)

    def log_msg(self, msg):
        """Log-Nachricht direkt ausgeben (nur vom Main-Thread)."""
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _poll_log(self):
        """Log-Queue abfragen und Nachrichten anzeigen (Timer-basiert)."""
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

    # --- Beenden ---

    def _on_close(self):
        """Anwendung beenden."""
        if self.build_running:
            if not messagebox.askyesno('Beenden',
                                       'Build läuft noch. Trotzdem beenden?'):
                return
        self.root.destroy()

    # --- Starten ---

    def run(self):
        """Hauptschleife starten."""
        self.root.mainloop()


def main():
    app = CPAWorkbenchApp()
    app.run()


if __name__ == '__main__':
    main()
