#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
build.py  –  Build-Skript fuer EM256-Testprogramme
===================================================

Baut EM256-Testprogramme aus dem Assembler-Quellcode in src/ mithilfe des
CP/M-Assemblers M80 und des Linkers LINKMT, die beide ueber den CP/M-Emulator
cparun ausgefuehrt werden.

Unterstuetzte Quelldateien:
  - em256tst.mac  (Original-Test, direkt assemblierbar)
  - em256full.mac (Volltest, enthaelt ;%INCLUDE-Direktiven fuer Z8001-Firmware)

Arbeitsweise
------------
1. Ergebnisverzeichnis 16bitTest/build/ anlegen (falls noetig)
2. Z8001-Firmware assemblieren (fw_*.s aus src/ -> .bin/.inc in build/)
3. Quelldatei vorverarbeiten: ;%INCLUDE-Direktiven durch .inc-Dateien ersetzen
4. Vorverarbeitete Datei nach build/ kopieren (mit CRLF-Konvertierung)
5. M80-Tools (m80.com, linkmt.com) aus tools/ nach build/ kopieren
6. M80 assemblieren
7. LINKMT linken (Ladeadresse 0x100)
8. Temporaere Dateien aufraeumen
9. .COM nach additions/bc_a5120/ kopieren

Voraussetzungen
---------------
- tools/cparun (Linux) oder tools/cparun.exe (Windows)
- tools/m80.com, tools/linkmt.com
- Python 3.6+

Aufruf
------
  cd /pfad/zu/CPA_Workbench
  python3 16bitTest/build.py                    # em256full (Standard)
  python3 16bitTest/build.py em256tst            # Original-Test
  python3 16bitTest/build.py em256full           # Volltest (explizit)
"""

import glob
import os
import platform
import re
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# Pfade (relativ zum CPA_Workbench-Root-Verzeichnis)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)          # CPA_Workbench/
ADDITIONS_DIR = os.path.join(PROJECT_DIR, 'additions', 'bc_a5120')  # Ziel fuer .COM
SRC_DIR     = os.path.join(SCRIPT_DIR, 'src')      # 16bitTest/src/
BUILD_DIR   = os.path.join(SCRIPT_DIR, 'build')    # 16bitTest/build/
TOOLS_DIR   = os.path.join(PROJECT_DIR, 'tools')   # tools/
Z8001_ASM   = os.path.join(SCRIPT_DIR, 'z8001asm.py')  # 16bitTest/z8001asm.py

# Standard-Quelle (ueber Kommandozeile aenderbar)
DEFAULT_SOURCE = 'em256ful'

# Ladeadresse fuer CP/M .COM-Programme (immer 0x100)
LOAD_ADDR   = '100'

# ---------------------------------------------------------------------------
def log(msg):
    """Nachricht auf stdout ausgeben."""
    print(msg)


def run(cmd, cwd=None, check=True, timeout=60):
    """Externen Befehl ausfuehren und Ausgabe anzeigen.

    Args:
        cmd:     Befehlsliste
        cwd:     Arbeitsverzeichnis
        check:   Bei True: Fehler bei Exitcode != 0
        timeout: Timeout in Sekunden
    """
    cwd = cwd or BUILD_DIR
    log(f"  > {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd,
            capture_output=True, text=True,
            timeout=timeout, errors='replace'
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                log(f"    {line}")
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines():
                log(f"    {line}")
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Befehl fehlgeschlagen (exit {result.returncode}): {' '.join(cmd)}"
            )
        return result
    except FileNotFoundError:
        raise RuntimeError(f"Programm nicht gefunden: {cmd[0]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout nach {timeout}s: {' '.join(cmd)}")


def find_cparun():
    """cparun-Pfad plattformabhaengig ermitteln."""
    if platform.system() == 'Windows':
        name = 'cparun.exe'
    else:
        name = 'cparun'
    path = os.path.join(TOOLS_DIR, name)
    if not os.path.isfile(path):
        raise RuntimeError(
            f"cparun nicht gefunden: {path}\n"
            "Bitte sicherstellen, dass das tools/-Verzeichnis vollstaendig ist."
        )
    return path


def preprocess_includes(src_content, inc_dir):
    """Ersetzt ;%INCLUDE-Direktiven durch den Inhalt der referenzierten .inc-Dateien.

    Args:
        src_content: Quelltext als String
        inc_dir:     Verzeichnis mit .inc-Dateien

    Returns:
        Vorverarbeiteter Quelltext
    """
    include_re = re.compile(r'^;\s*%INCLUDE\s+(\S+)', re.IGNORECASE | re.MULTILINE)

    def replace_include(match):
        filename = match.group(1)
        inc_path = os.path.join(inc_dir, filename)
        if not os.path.isfile(inc_path):
            raise RuntimeError(
                f"Include-Datei nicht gefunden: {inc_path}\n"
                "Bitte zuerst Z8001-Firmware assemblieren."
            )
        with open(inc_path, 'r', encoding='utf-8') as f:
            content = f.read().rstrip('\n')
        log(f"    Eingefuegt: {filename} ({len(content)} Zeichen)")
        return content

    return include_re.sub(replace_include, src_content)


def clean():
    """Build-Verzeichnis leeren."""
    if os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
        log(f"    Geloescht: {BUILD_DIR}")
    else:
        log(f"    Bereits leer.")


def assemble_z8001_firmware():
    """Z8001-Firmware-Quelldateien assemblieren (alle .s-Dateien in src/).

    Quellen liegen in src/, Ausgaben (.bin, .inc) landen in build/.
    """
    if not os.path.isfile(Z8001_ASM):
        raise RuntimeError(f"Z8001-Assembler nicht gefunden: {Z8001_ASM}")

    s_files = sorted(glob.glob(os.path.join(SRC_DIR, 'fw_*.s')))
    if not s_files:
        raise RuntimeError(f"Keine fw_*.s-Dateien in {SRC_DIR} gefunden.")

    log(f"    {len(s_files)} Firmware-Dateien gefunden")
    for s_file in s_files:
        basename = os.path.basename(s_file)
        stem = os.path.splitext(basename)[0]
        bin_path = os.path.join(BUILD_DIR, stem + '.bin')
        inc_path = os.path.join(BUILD_DIR, stem + '.inc')
        # Label-Prefix: fw_add -> FW_ADD, damit .inc FW_ADD_CODE / FW_ADD_CODE_LEN erzeugt
        label_prefix = stem.upper()
        result = run(
            [sys.executable, Z8001_ASM, s_file,
             '-o', bin_path, '--inc', inc_path,
             '--label', label_prefix],
            cwd=BUILD_DIR, check=True
        )
        log(f"    Assembliert: {basename} (Label: {label_prefix}_CODE)")


def main():
    # --- Quellname aus Kommandozeile oder Standard ---
    if len(sys.argv) > 1:
        source_name = sys.argv[1].lower().replace('.mac', '')
    else:
        source_name = DEFAULT_SOURCE

    # CP/M 8.3-Format pruefen
    if len(source_name) > 8:
        raise RuntimeError(
            f"Dateiname '{source_name}' zu lang (max. 8 Zeichen fuer CP/M 8.3)"
        )

    source_name_up = source_name.upper()
    source_mac     = source_name + '.mac'
    source_mac_up  = source_name_up + '.MAC'
    source_erl     = source_name_up + '.ERL'
    target_com     = source_name + '.com'
    needs_preprocessing = (source_name != 'em256tst')

    log("=" * 50)
    log(f"EM256 Test Build  –  {source_name}")
    log("=" * 50)

    # --- Schritt 1: Build-Verzeichnis anlegen ---
    log("\n[STEP 1] Build-Verzeichnis anlegen")
    os.makedirs(BUILD_DIR, exist_ok=True)
    log(f"    {BUILD_DIR}")

    # --- Schritt 2: Z8001-Firmware assemblieren (nur fuer em256full) ---
    if needs_preprocessing:
        log("\n[STEP 2] Z8001-Firmware assemblieren")
        assemble_z8001_firmware()
    else:
        log("\n[STEP 2] Z8001-Firmware (uebersprungen)")

    # --- Schritt 3: Quellcode vorverarbeiten und kopieren ---
    log(f"\n[STEP 3] Quelldatei vorverarbeiten und nach build/ kopieren")
    src_mac = os.path.join(SRC_DIR, source_mac)
    dst_mac = os.path.join(BUILD_DIR, source_mac_up)
    if not os.path.isfile(src_mac):
        raise RuntimeError(f"Quelldatei nicht gefunden: {src_mac}")

    with open(src_mac, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    if needs_preprocessing:
        log("    Include-Direktiven verarbeiten...")
        content = preprocess_includes(content, BUILD_DIR)

    # CRLF-Konvertierung
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = content.replace('\n', '\r\n')
    with open(dst_mac, 'wb') as f:
        f.write(content.encode('ascii', errors='replace'))
    log(f"    Geschrieben: {source_mac_up} ({os.path.getsize(dst_mac)} Bytes)")

    # --- Schritt 4: Tools kopieren ---
    log("\n[STEP 4] Build-Tools nach build/ kopieren")
    for tool in ['m80.com', 'linkmt.com']:
        src_tool = os.path.join(TOOLS_DIR, tool)
        if not os.path.isfile(src_tool):
            raise RuntimeError(f"Tool nicht gefunden: {src_tool}")
        shutil.copy2(src_tool, BUILD_DIR)
        log(f"    Kopiert: {tool}")

    # --- Schritt 5: Assemblieren mit M80 ---
    cparun = find_cparun()
    log(f"\n[STEP 5] Assemblieren mit M80 ({source_mac_up} -> {source_erl})")
    result = run(
        [cparun, 'm80', f'{source_erl}={source_name_up}'],
        cwd=BUILD_DIR, check=True
    )

    # ERL erzeugt? (cparun erstellt auf Linux lowercase Dateinamen)
    erl_upper = os.path.join(BUILD_DIR, source_erl)
    erl_lower = os.path.join(BUILD_DIR, source_erl.lower())
    if os.path.isfile(erl_lower) and not os.path.isfile(erl_upper):
        os.rename(erl_lower, erl_upper)
    if not os.path.isfile(erl_upper):
        raise RuntimeError(
            f"M80 hat keine {source_erl} erzeugt. Bitte Assembler-Ausgabe pruefen."
        )

    # --- Schritt 6: Linken mit LINKMT ---
    target_com_up = source_name_up + '.COM'
    log(f"\n[STEP 6] Linken mit LINKMT ({source_erl} -> {target_com_up})")
    log(f"    Ladeadresse: 0x{LOAD_ADDR} (CP/M .COM-Standard)")
    run(
        [cparun, 'linkmt',
         f'{source_name_up}={source_name_up}/p:{LOAD_ADDR}'],
        cwd=BUILD_DIR, check=True
    )
    # Ggf. Gross->Klein umbenennen
    com_upper = os.path.join(BUILD_DIR, target_com_up)
    com_lower = os.path.join(BUILD_DIR, target_com)
    com_lowercase_from_cparun = os.path.join(BUILD_DIR, target_com_up.lower())
    if os.path.isfile(com_lowercase_from_cparun) and not os.path.isfile(com_lower):
        os.rename(com_lowercase_from_cparun, com_lower)
    elif os.path.isfile(com_upper) and not os.path.isfile(com_lower):
        os.rename(com_upper, com_lower)

    com_path = os.path.join(BUILD_DIR, target_com)
    com_path_up = os.path.join(BUILD_DIR, target_com_up)
    if not os.path.isfile(com_path) and not os.path.isfile(com_path_up):
        raise RuntimeError(
            f"LINKMT hat keine {target_com} erzeugt. Ausgabe pruefen."
        )
    if not os.path.isfile(com_path):
        com_path = com_path_up

    # --- Schritt 7: Aufraeuemen ---
    log("\n[STEP 7] Temporaere Dateien loeschen")
    for pattern in ['*.mac', '*.MAC', '*.erl', '*.ERL', '*.prn', '*.PRN',
                    '*.rel', '*.REL', '*.syp', '*.SYP',
                    '*.bin', '*.inc',
                    'm80.com', 'linkmt.com']:
        for f in glob.glob(os.path.join(BUILD_DIR, pattern)):
            basename = os.path.basename(f).lower()
            if basename != target_com.lower():
                os.remove(f)
                log(f"    Geloescht: {os.path.basename(f)}")

    # --- Fertig ---
    com_size = os.path.getsize(com_path)
    log("\n" + "=" * 50)
    log(f"FERTIG: {target_com} ({com_size} Bytes)")
    log(f"Pfad:   {com_path}")
    log("=" * 50)

    # --- Schritt 8: Nach additions/bc_a5120/ kopieren ---
    log(f"\n[STEP 8] Kopiere nach additions/bc_a5120/")
    os.makedirs(ADDITIONS_DIR, exist_ok=True)
    dest = os.path.join(ADDITIONS_DIR, target_com)
    shutil.copy2(com_path, dest)
    log(f"    {dest}")
    log(f"\nStarten mit:        {source_name}")


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'clean':
            log("Build-Verzeichnis leeren...")
            clean()
        else:
            main()
    except RuntimeError as e:
        print(f"\nFEHLER: {e}", file=sys.stderr)
        sys.exit(1)
