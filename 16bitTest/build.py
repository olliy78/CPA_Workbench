#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
build.py  –  Build-Skript fuer em256test.com
=============================================

Baut das EM256 U8000-Testprogramm (em256test.com) aus dem Assembler-Quellcode
in src/em256test.mac mithilfe des CP/M-Assemblers M80 und des Linkers LINKMT,
die beide ueber den CP/M-Emulator cparun ausgefuehrt werden.

Arbeitsweise
------------
1. Ergebnisverzeichnis 16bitTest/build/ anlegen (falls noetig)
2. Quelldatei src/em256test.mac nach build/ kopieren (mit CRLF-Konvertierung)
3. M80-Tools (m80.com, linkmt.com) aus tools/ nach build/ kopieren
4. M80 assemblieren: em256test.erl=em256test
5. LINKMT linken:    em256test=em256test/p:100
   (Ladeadresse 0x100 = Standard fuer CP/M .COM-Programme)
6. Temporaere Dateien aufraeumen, em256test.com bleibt

Voraussetzungen
---------------
- tools/cparun (Linux) oder tools/cparun.exe (Windows)
- tools/m80.com
- tools/linkmt.com
- Python 3.6+

Aufruf
------
  cd /pfad/zu/CPA_Workbench
  python3 16bitTest/build.py

Das fertige em256test.com liegt danach in 16bitTest/build/em256test.com.
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
SRC_DIR     = os.path.join(SCRIPT_DIR, 'src')      # 16bitTest/src/
BUILD_DIR   = os.path.join(SCRIPT_DIR, 'build')    # 16bitTest/build/
TOOLS_DIR   = os.path.join(PROJECT_DIR, 'tools')   # tools/

# CP/M-Dateinamen: max. 8 Zeichen (8.3-Format!)  em256tst = 8 Zeichen
SOURCE_NAME    = 'em256tst'                         # ohne Endung (Kleinbuchstaben, max. 8!)
SOURCE_NAME_UP = SOURCE_NAME.upper()               # M80 sucht Dateinamen in Grossbuchstaben
SOURCE_MAC     = SOURCE_NAME + '.mac'              # Quelldatei (Kleinbuchstaben)
SOURCE_MAC_UP  = SOURCE_NAME_UP + '.MAC'           # Zieldatei fuer M80 (Grossbuchstaben)
SOURCE_ERL     = SOURCE_NAME_UP + '.ERL'           # M80 erzeugt ERL in Grossbuchstaben
TARGET_COM     = SOURCE_NAME + '.com'              # Endprodukt

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


def convert_to_crlf(src_path, dst_path):
    """Quelldatei nach dst_path kopieren und Zeilenenden zu CRLF konvertieren.

    Der M80-Assembler erwartet Windows-Zeilenenden (CRLF = \\r\\n).
    """
    with open(src_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    # Einheitliche Normalisierung: alle Varianten -> LF, dann LF -> CRLF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = content.replace('\n', '\r\n')
    with open(dst_path, 'wb') as f:
        f.write(content.encode('ascii', errors='replace'))
    log(f"    Kopiert (CRLF): {os.path.basename(src_path)} -> {dst_path}")


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


def main():
    log("=" * 50)
    log("EM256 U8000 Test  –  Build-Skript")
    log("=" * 50)

    # --- Schritt 1: Build-Verzeichnis anlegen ---
    log("\n[STEP 1] Build-Verzeichnis anlegen")
    os.makedirs(BUILD_DIR, exist_ok=True)
    log(f"    {BUILD_DIR}")

    # --- Schritt 2: Quellcode kopieren (CRLF, Grossbuchstaben-Name fuer M80) ---
    log("\n[STEP 2] Quelldatei nach build/ kopieren (CRLF, Grossbuchstaben fuer M80)")
    src_mac = os.path.join(SRC_DIR, SOURCE_MAC)
    dst_mac = os.path.join(BUILD_DIR, SOURCE_MAC_UP)  # M80 sucht EM256TEST.MAC
    if not os.path.isfile(src_mac):
        raise RuntimeError(f"Quelldatei nicht gefunden: {src_mac}")
    convert_to_crlf(src_mac, dst_mac)

    # --- Schritt 3: Tools kopieren ---
    log("\n[STEP 3] Build-Tools nach build/ kopieren")
    for tool in ['m80.com', 'linkmt.com']:
        src_tool = os.path.join(TOOLS_DIR, tool)
        if not os.path.isfile(src_tool):
            raise RuntimeError(f"Tool nicht gefunden: {src_tool}")
        shutil.copy2(src_tool, BUILD_DIR)
        log(f"    Kopiert: {tool}")

    # --- Schritt 4: Assemblieren mit M80 ---
    # M80 sucht die Quelldatei im aktuellen Verzeichnis unter GROSSEM Namen.
    # Aufruf: m80 EM256TEST.ERL=EM256TEST
    cparun = find_cparun()
    log(f"\n[STEP 4] Assemblieren mit M80 ({SOURCE_MAC_UP} -> {SOURCE_ERL})")
    result = run(
        [cparun, '-dir', BUILD_DIR, 'm80', f'{SOURCE_ERL}={SOURCE_NAME_UP}'],
        cwd=BUILD_DIR, check=True
    )

    # ERL erzeugt? (cparun erstellt auf Linux lowercase Dateinamen)
    erl_upper = os.path.join(BUILD_DIR, SOURCE_ERL)           # EM256TST.ERL
    erl_lower = os.path.join(BUILD_DIR, SOURCE_ERL.lower())   # em256tst.erl
    if os.path.isfile(erl_lower) and not os.path.isfile(erl_upper):
        os.rename(erl_lower, erl_upper)  # Fuer LINKMT auf Uppercase umbenennen
    if not os.path.isfile(erl_upper):
        raise RuntimeError(
            f"M80 hat keine {SOURCE_ERL} erzeugt. Bitte Assembler-Ausgabe pruefen."
        )

    # --- Schritt 5: Linken mit LINKMT ---
    # LINKMT: Ausgabedatei=Eingabemodul/p:Ladeadresse
    # Ausgabe: EM256TEST.COM (Grossbuchstaben), dann umbenennen
    TARGET_COM_UP = SOURCE_NAME_UP + '.COM'
    log(f"\n[STEP 5] Linken mit LINKMT ({SOURCE_ERL} -> {TARGET_COM_UP})")
    log(f"    Ladeadresse: 0x{LOAD_ADDR} (CP/M .COM-Standard)")
    run(
        [cparun, '-dir', BUILD_DIR, 'linkmt',
         f'{SOURCE_NAME_UP}={SOURCE_NAME_UP}/p:{LOAD_ADDR}'],
        cwd=BUILD_DIR, check=True
    )
    # Ggf. Gross->Klein umbenennen fuer Uebersichtlichkeit
    # cparun erstellt auf Linux lowercase Dateinamen
    com_upper = os.path.join(BUILD_DIR, TARGET_COM_UP)
    com_lower = os.path.join(BUILD_DIR, TARGET_COM)
    com_lowercase_from_cparun = os.path.join(BUILD_DIR, TARGET_COM_UP.lower())
    if os.path.isfile(com_lowercase_from_cparun) and not os.path.isfile(com_lower):
        os.rename(com_lowercase_from_cparun, com_lower)
    elif os.path.isfile(com_upper) and not os.path.isfile(com_lower):
        os.rename(com_upper, com_lower)

    # COM erzeugt? (Klein- oder Grossbuchstaben akzeptieren)
    com_path = os.path.join(BUILD_DIR, TARGET_COM)
    com_path_up = os.path.join(BUILD_DIR, SOURCE_NAME_UP + '.COM')
    if not os.path.isfile(com_path) and not os.path.isfile(com_path_up):
        raise RuntimeError(
            f"LINKMT hat keine {TARGET_COM} erzeugt. Ausgabe pruefen."
        )
    if not os.path.isfile(com_path):
        com_path = com_path_up

    # --- Schritt 6: Aufraeuemen ---
    log("\n[STEP 6] Temporaere Dateien loeschen")
    for pattern in ['*.mac', '*.MAC', '*.erl', '*.ERL', '*.prn', '*.PRN',
                    '*.rel', '*.REL', '*.syp', '*.SYP',
                    'm80.com', 'linkmt.com']:
        for f in glob.glob(os.path.join(BUILD_DIR, pattern)):
            basename = os.path.basename(f).lower()
            if basename != TARGET_COM.lower():
                os.remove(f)
                log(f"    Geloescht: {os.path.basename(f)}")

    # --- Fertig ---
    com_size = os.path.getsize(com_path)
    log("\n" + "=" * 50)
    log(f"FERTIG: {TARGET_COM} ({com_size} Bytes)")
    log(f"Pfad:   {com_path}")
    log("=" * 50)
    log("\nKopiere em256test.com auf eine CP/A-Diskette und starte es")
    log("mit dem Befehl:  em256test")


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(f"\nFEHLER: {e}", file=sys.stderr)
        sys.exit(1)
