#!/usr/bin/env python3
# Copyright (c) 2025 by olliy78
# SPDX-License-Identifier: MIT
"""
Kconfig-Parser für das CP/A Workbench Projekt.

Parst Kconfig-Dateien (Kconfig.variante, Kconfig.system, Kconfig.build)
in eine Baumstruktur, die von der GUI zur Darstellung der Konfigurationsoptionen
verwendet wird.

Unterstützte Kconfig-Konstrukte:
  - mainmenu "Titel"
  - menu "Titel" ... endmenu
  - choice ... endchoice (mit prompt, default)
  - config NAME (bool/string, mit help, default)
"""

import re
import os


class KconfigConfig:
    """Ein einzelnes 'config'-Element mit Name, Typ, Label, Hilfetext und Default."""
    def __init__(self, name):
        self.name = name
        self.config_type = 'bool'   # 'bool' oder 'string'
        self.label = ''
        self.help_text = ''
        self.default = None         # 'y', 'n', None oder String-Wert


class KconfigChoice:
    """Ein 'choice...endchoice'-Block mit Prompt, Default und Config-Einträgen."""
    def __init__(self):
        self.prompt = ''
        self.default = None
        self.help_text = ''
        self.configs = []           # Liste von KconfigConfig


class KconfigMenu:
    """Ein 'menu...endmenu'-Block mit Titel und Kind-Elementen."""
    def __init__(self, title=''):
        self.title = title
        self.children = []          # Liste von KconfigConfig, KconfigChoice, KconfigMenu


class KconfigFile:
    """Gesamte geparste Kconfig-Datei mit Titel und Top-Level-Elementen."""
    def __init__(self):
        self.title = ''
        self.children = []


class _KconfigParser:
    """Interner rekursiver Parser für Kconfig-Dateien."""

    def __init__(self, lines):
        self.lines = lines
        self.pos = 0

    def _peek_stripped(self):
        """Nächste nicht-leere, nicht-Kommentar-Zeile zurückgeben (ohne Position zu ändern)."""
        saved = self.pos
        result = self._next_stripped()
        self.pos = saved
        return result

    def _next_stripped(self):
        """Nächste nicht-leere, nicht-Kommentar-Zeile lesen und Position vorrücken."""
        while self.pos < len(self.lines):
            line = self.lines[self.pos].strip()
            if not line or line.startswith('#'):
                self.pos += 1
                continue
            return line
        return None

    def _first_word(self, line):
        """Erstes Wort einer Zeile extrahieren."""
        return line.split()[0] if line else ''

    def _extract_quoted(self, line):
        """String in Anführungszeichen extrahieren."""
        m = re.search(r'"([^"]*)"', line)
        return m.group(1) if m else ''

    def _parse_help_text(self):
        """Hilfetext-Block nach 'help'-Schlüsselwort parsen (einrückungsbasiert)."""
        text_lines = []
        base_indent = None
        while self.pos < len(self.lines):
            raw = self.lines[self.pos]
            stripped = raw.strip()
            if not stripped:
                if base_indent is not None:
                    text_lines.append('')
                self.pos += 1
                continue
            indent = len(raw) - len(raw.lstrip())
            if base_indent is None:
                base_indent = indent
            elif indent < base_indent:
                break
            text_lines.append(raw[base_indent:].rstrip() if len(raw) >= base_indent else stripped)
            self.pos += 1
        while text_lines and not text_lines[-1]:
            text_lines.pop()
        return '\n'.join(text_lines)

    def _parse_config(self):
        """Ein 'config NAME'-Element mit allen Eigenschaften parsen."""
        line = self._next_stripped()
        parts = line.split()
        name = parts[1] if len(parts) > 1 else ''
        cfg = KconfigConfig(name)
        self.pos += 1
        while self.pos < len(self.lines):
            line = self._peek_stripped()
            if line is None:
                break
            word = self._first_word(line)
            if word in ('config', 'choice', 'menu', 'endchoice', 'endmenu'):
                break
            self._next_stripped()
            self.pos += 1
            if word == 'bool':
                cfg.config_type = 'bool'
                cfg.label = self._extract_quoted(line)
            elif word == 'string':
                cfg.config_type = 'string'
                cfg.label = self._extract_quoted(line)
            elif word == 'default':
                val = line.split(None, 1)
                cfg.default = val[1].strip() if len(val) > 1 else None
            elif word == 'help':
                cfg.help_text = self._parse_help_text()
            elif word == 'prompt':
                cfg.label = self._extract_quoted(line)
        return cfg

    def _parse_choice(self):
        """Ein 'choice...endchoice'-Block parsen."""
        self._next_stripped()
        self.pos += 1  # 'choice' überspringen
        choice = KconfigChoice()
        while self.pos < len(self.lines):
            line = self._peek_stripped()
            if line is None:
                break
            word = self._first_word(line)
            if word == 'endchoice':
                self._next_stripped()
                self.pos += 1
                break
            if word == 'prompt':
                self._next_stripped()
                self.pos += 1
                choice.prompt = self._extract_quoted(line)
            elif word == 'default':
                self._next_stripped()
                self.pos += 1
                val = line.split(None, 1)
                choice.default = val[1].strip() if len(val) > 1 else None
            elif word == 'help':
                self._next_stripped()
                self.pos += 1
                choice.help_text = self._parse_help_text()
            elif word == 'config':
                choice.configs.append(self._parse_config())
            else:
                self._next_stripped()
                self.pos += 1
        return choice

    def _parse_menu(self):
        """Ein 'menu...endmenu'-Block parsen."""
        line = self._next_stripped()
        self.pos += 1
        menu = KconfigMenu(self._extract_quoted(line))
        menu.children = self._parse_items(['endmenu'])
        peek = self._peek_stripped()
        if peek and self._first_word(peek) == 'endmenu':
            self._next_stripped()
            self.pos += 1
        return menu

    def _parse_items(self, end_tokens):
        """Liste von Kconfig-Elementen parsen bis ein End-Token erreicht wird."""
        items = []
        while self.pos < len(self.lines):
            line = self._peek_stripped()
            if line is None:
                break
            word = self._first_word(line)
            if word in end_tokens:
                break
            if word == 'config':
                items.append(self._parse_config())
            elif word == 'choice':
                items.append(self._parse_choice())
            elif word == 'menu':
                items.append(self._parse_menu())
            else:
                self._next_stripped()
                self.pos += 1
        return items

    def parse(self):
        """Gesamte Kconfig-Datei parsen."""
        result = KconfigFile()
        line = self._peek_stripped()
        if line and self._first_word(line) == 'mainmenu':
            self._next_stripped()
            self.pos += 1
            result.title = self._extract_quoted(line)
        result.children = self._parse_items([])
        return result


def parse_kconfig(filepath):
    """
    Kconfig-Datei einlesen und in eine Baumstruktur (KconfigFile) parsen.

    Args:
        filepath: Pfad zur Kconfig-Datei

    Returns:
        KconfigFile mit title und children
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    parser = _KconfigParser(lines)
    return parser.parse()
