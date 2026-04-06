#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
build.py  --  Build-Skript fuer den CPA780 SYL-Bootlader (bootsec.bin)
=======================================================================

Baut den Bootlader aus der Assembler-Quelle bootsec.mac mithilfe des
CP/M-Assemblers M80 (ueber cparun) und erzeugt die fertige bootsec.bin
im SYL-Mixed-Geometry-Format (15104 Bytes).

Arbeitsweise
------------
1. Ergebnisverzeichnis bootsec/build/ anlegen (falls noetig)
2. Quelldatei src/bootsec.mac nach build/ kopieren (CRLF-Konvertierung)
3. M80-Tool (m80.com) aus tools/ nach build/ kopieren
4. M80 assemblieren: BOOTSEC.REL und BOOTSEC.PRN erzeugen
5. PRN-Listing parsen: Binaerdaten extrahieren (Adressen 0000H-19FFH)
6. bootsec.bin konstruieren:
   - Track 0: RAM 0000H-0CFFH (3328 Bytes)
   - Track 1: Fuellung 53H (3328 Bytes)
   - Track 2: RAM 0D00H-19FFH (3328 Bytes)
   - Track 3: Fuellung 53H (5120 Bytes)
7. Vergleich mit Original (prebuilt/bc_a5120/bootsec.bin)
8. Temporaere Dateien aufraeumen

Voraussetzungen
---------------
- tools/cparun (Linux) oder tools/cparun.exe (Windows)
- tools/m80.com
- Python 3.6+

Aufruf
------
  cd /pfad/zu/CPA_Workbench
  python3 bootsec/build.py

Das fertige bootsec.bin liegt danach in bootsec/build/bootsec.bin.
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
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)           # CPA_Workbench/
SRC_DIR     = os.path.join(SCRIPT_DIR, 'src')       # bootsec/src/
BUILD_DIR   = os.path.join(SCRIPT_DIR, 'build')     # bootsec/build/
TOOLS_DIR   = os.path.join(PROJECT_DIR, 'tools')    # tools/
PREBUILT    = os.path.join(PROJECT_DIR, 'prebuilt', 'bc_a5120', 'bootsec.bin')

# CP/M-Dateinamen: max 8.3
SOURCE_NAME    = 'bootsec'
SOURCE_NAME_UP = SOURCE_NAME.upper()
SOURCE_MAC     = SOURCE_NAME + '.mac'
SOURCE_MAC_UP  = SOURCE_NAME_UP + '.MAC'

# Track-Konstanten
TRACK_SYS_SIZE   = 3328         # Systemspur: 26 Sektoren x 128 Bytes
TRACK_DATA_SIZE  = 5120         # Datenspur:   5 Sektoren x 1024 Bytes
FILL_BYTE        = 0x53         # 'S' -- SYL-Fuellbyte
TOTAL_SIZE       = 15104        # 3 x 3328 + 1 x 5120

# RAM-Bereiche fuer Code
TRACK0_RAM_START = 0x0000
TRACK0_RAM_END   = 0x0D00       # exklusiv
TRACK2_RAM_START = 0x0D00
TRACK2_RAM_END   = 0x1A00       # exklusiv


# ---------------------------------------------------------------------------
def log(msg):
    """Nachricht auf stdout ausgeben."""
    print(msg)


def run(cmd, cwd=None, check=True, timeout=60):
    """Externen Befehl ausfuehren und Ausgabe anzeigen."""
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
    """Quelldatei kopieren und Zeilenenden zu CRLF konvertieren (M80 erwartet CRLF)."""
    with open(src_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = content.replace('\n', '\r\n')
    with open(dst_path, 'wb') as f:
        f.write(content.encode('ascii', errors='replace'))
    log(f"    Kopiert (CRLF): {os.path.basename(src_path)} -> {os.path.basename(dst_path)}")


def find_cparun():
    """cparun-Pfad plattformabhaengig ermitteln."""
    name = 'cparun.exe' if platform.system() == 'Windows' else 'cparun'
    path = os.path.join(TOOLS_DIR, name)
    if not os.path.isfile(path):
        raise RuntimeError(
            f"cparun nicht gefunden: {path}\n"
            "Bitte sicherstellen, dass das tools/-Verzeichnis vollstaendig ist."
        )
    return path


def parse_prn_listing(prn_path):
    """M80-Listing (.PRN) parsen und Binaerdaten extrahieren.

    Das PRN-Format von M80 (MACRO-80 V3.50) hat pro Zeile:
      __AAAA'  BB BB BB BB  <tab><quellentext>
    wobei AAAA die Adresse (hex), ' der Segment-Marker (ASEG) und
    BB die assemblierten Bytes sind. Lange DB-Zeilen werden auf
    Folgezeilen mit weiteren Bytes fortgesetzt.

    Gibt ein dict {adresse: byte_value} zurueck.
    """
    memory = {}
    # M80 PRN Format (MACRO-80 V3.50):
    #   Cols 0-1:  2 Leerzeichen
    #   Cols 2-5:  4-stellige Hex-Adresse
    #   Col  6:    Segment-Marker (' fuer ASEG) oder Leerzeichen
    #   Cols 7-9:  Leerzeichen
    #   Cols 10+:  Hex-Daten (maximal ~12 Zeichen)
    #   Cols 24+:  Quelltext (Mnemonics, Direktiven, Labels)
    #
    # Hex-Daten-Format:
    #   - Einzelbytes: 2 Hex-Digits (z.B. "3E 29")
    #   - 16-Bit-Operanden: 4 Hex-Digits in Big-Endian-Anzeige (z.B. "C3 0140")
    #     -> muessen als Little-Endian (Z80-Speicherreihenfolge) gespeichert werden
    #
    # WICHTIG: Hex-Daten nur aus Spalten 8-23 extrahieren, um Label-Namen
    # (z.B. "FDC_INIT:" -> "FD") und Direktiv-Schluesse (z.B. "DB" -> 0xDB)
    # nicht faelschlich als Daten zu interpretieren.
    addr_re = re.compile(r'^\s{2}([0-9A-Fa-f]{4})[\'` ]?')

    with open(prn_path, 'r', errors='replace') as f:
        for line in f:
            m = addr_re.match(line)
            if m:
                addr = int(m.group(1), 16)
                # Hex-Daten aus fixem Spaltenbereich (Cols 8-23)
                hex_area = line[8:24] if len(line) > 8 else ''
                # 4-Digit-Werte zuerst matchen (16-Bit LE), dann 2-Digit (Einzelbytes)
                byte_vals = re.findall(r'[0-9A-Fa-f]{4}|[0-9A-Fa-f]{2}', hex_area)
                for bv in byte_vals:
                    v = int(bv, 16)
                    if len(bv) <= 2:
                        memory[addr] = v
                        addr += 1
                    else:
                        # 16-Bit-Wert: Little-Endian speichern (Low-Byte zuerst)
                        memory[addr] = v & 0xFF
                        memory[addr + 1] = (v >> 8) & 0xFF
                        addr += 2

    return memory


def memory_to_binary(memory, start, end):
    """Speicherabbild in Bytearray umwandeln.

    Fehlende Adressen werden mit 0x00 gefuellt.
    """
    result = bytearray(end - start)
    for addr in range(start, end):
        if addr in memory:
            result[addr - start] = memory[addr]
    return bytes(result)


def build_bootsec_bin(track0_data, track2_data):
    """Zusammensetzen der 4-Track bootsec.bin.

    Args:
        track0_data: 3328 Bytes (RAM 0000H-0CFFH)
        track2_data: 3328 Bytes (RAM 0D00H-19FFH)

    Returns:
        15104 Bytes: Track0 + Fill_Track1 + Track2 + Fill_Track3
    """
    assert len(track0_data) == TRACK_SYS_SIZE, \
        f"Track 0 Groesse falsch: {len(track0_data)} != {TRACK_SYS_SIZE}"
    assert len(track2_data) == TRACK_SYS_SIZE, \
        f"Track 2 Groesse falsch: {len(track2_data)} != {TRACK_SYS_SIZE}"

    track1_fill = bytes([FILL_BYTE] * TRACK_SYS_SIZE)
    track3_fill = bytes([FILL_BYTE] * TRACK_DATA_SIZE)

    result = track0_data + track1_fill + track2_data + track3_fill
    assert len(result) == TOTAL_SIZE, \
        f"Gesamtgroesse falsch: {len(result)} != {TOTAL_SIZE}"
    return result


def compare_with_original(built_data, original_path):
    """Vergleich des gebauten Images mit dem Original.

    Returns:
        True wenn identisch, False sonst.
    """
    if not os.path.isfile(original_path):
        log(f"    WARNUNG: Original nicht gefunden: {original_path}")
        return False

    with open(original_path, 'rb') as f:
        original = f.read()

    if built_data == original:
        log(f"    IDENTISCH mit Original ({len(original)} Bytes)")
        return True
    else:
        # Unterschiede finden
        min_len = min(len(built_data), len(original))
        diffs = []
        for i in range(min_len):
            if built_data[i] != original[i]:
                diffs.append(i)
        if len(built_data) != len(original):
            log(f"    UNTERSCHIEDLICH: Groesse {len(built_data)} vs. {len(original)}")
        if diffs:
            log(f"    UNTERSCHIEDLICH: {len(diffs)} Byte(s) weichen ab")
            for offset in diffs[:20]:
                log(f"      Offset {offset:04X}H: gebaut={built_data[offset]:02X}H "
                    f"original={original[offset]:02X}H")
            if len(diffs) > 20:
                log(f"      ... und {len(diffs) - 20} weitere")
        return False


def main():
    log("=" * 60)
    log("CPA780 SYL-Bootlader  --  Build-Skript")
    log("=" * 60)

    # --- Schritt 1: Build-Verzeichnis anlegen ---
    log("\n[STEP 1] Build-Verzeichnis anlegen")
    os.makedirs(BUILD_DIR, exist_ok=True)
    log(f"    {BUILD_DIR}")

    # --- Schritt 2: Quellcode kopieren ---
    log("\n[STEP 2] Quelldatei nach build/ kopieren (CRLF, Grossbuchstaben)")
    src_mac = os.path.join(SRC_DIR, SOURCE_MAC)
    dst_mac = os.path.join(BUILD_DIR, SOURCE_MAC_UP)
    if not os.path.isfile(src_mac):
        raise RuntimeError(f"Quelldatei nicht gefunden: {src_mac}")
    convert_to_crlf(src_mac, dst_mac)

    # --- Schritt 3: M80 kopieren ---
    log("\n[STEP 3] M80 nach build/ kopieren")
    m80_src = os.path.join(TOOLS_DIR, 'm80.com')
    if not os.path.isfile(m80_src):
        raise RuntimeError(f"M80 nicht gefunden: {m80_src}")
    shutil.copy2(m80_src, BUILD_DIR)
    log(f"    Kopiert: m80.com")

    # --- Schritt 4: Assemblieren mit M80 ---
    cparun = find_cparun()
    log(f"\n[STEP 4] Assemblieren mit M80 ({SOURCE_MAC_UP} -> PRN + REL)")

    # M80 Aufruf: Listing + Objektdatei
    # Format: M80 objfile,lstfile=source
    # Wir wollen PRN-Listing UND REL-Datei
    result = run(
        [cparun, '-dir', BUILD_DIR, 'm80',
         f'{SOURCE_NAME_UP},{SOURCE_NAME_UP}={SOURCE_NAME_UP}'],
        cwd=BUILD_DIR, check=False
    )

    # PRN erzeugt? (cparun erstellt lowercase Dateinamen auf Linux)
    prn_path = None
    for name in [SOURCE_NAME_UP + '.PRN', SOURCE_NAME + '.prn',
                 SOURCE_NAME_UP + '.prn', SOURCE_NAME + '.PRN']:
        p = os.path.join(BUILD_DIR, name)
        if os.path.isfile(p):
            prn_path = p
            break

    if not prn_path:
        # Versuche alternativen M80-Aufruf
        log("    PRN nicht gefunden, versuche alternativen Aufruf...")
        result = run(
            [cparun, '-dir', BUILD_DIR, 'm80',
             f'={SOURCE_NAME_UP}/L'],
            cwd=BUILD_DIR, check=False
        )
        for name in [SOURCE_NAME_UP + '.PRN', SOURCE_NAME + '.prn',
                     SOURCE_NAME_UP + '.prn', SOURCE_NAME + '.PRN']:
            p = os.path.join(BUILD_DIR, name)
            if os.path.isfile(p):
                prn_path = p
                break

    if not prn_path:
        raise RuntimeError(
            "M80 hat kein PRN-Listing erzeugt. Bitte Assembler-Ausgabe pruefen.\n"
            "Vorhandene Dateien: " +
            ", ".join(os.listdir(BUILD_DIR))
        )
    log(f"    Listing: {os.path.basename(prn_path)}")

    # --- Schritt 5: PRN-Listing parsen ---
    log(f"\n[STEP 5] PRN-Listing parsen: Binaerdaten extrahieren")
    memory = parse_prn_listing(prn_path)

    if not memory:
        raise RuntimeError("Keine Binaerdaten im PRN-Listing gefunden!")

    min_addr = min(memory.keys())
    max_addr = max(memory.keys())
    log(f"    Adressbereich: {min_addr:04X}H - {max_addr:04X}H")
    log(f"    Bytes gefunden: {len(memory)}")

    # Erwarteter Bereich: 0000H-0CFFH und 0D00H-19FFH
    expected_bytes = (TRACK0_RAM_END - TRACK0_RAM_START) + \
                     (TRACK2_RAM_END - TRACK2_RAM_START)
    if len(memory) < expected_bytes * 0.95:
        log(f"    WARNUNG: Nur {len(memory)} von {expected_bytes} erwarteten Bytes!")

    # Extrahiere Track-Daten
    track0_data = memory_to_binary(memory, TRACK0_RAM_START, TRACK0_RAM_END)
    track2_data = memory_to_binary(memory, TRACK2_RAM_START, TRACK2_RAM_END)

    # --- Schritt 6: bootsec.bin zusammensetzen ---
    log(f"\n[STEP 6] bootsec.bin zusammensetzen (4-Track-Format)")
    log(f"    Track 0: {len(track0_data)} Bytes (Code 0000H-0CFFH)")
    log(f"    Track 1: {TRACK_SYS_SIZE} Bytes (Fuellung 53H)")
    log(f"    Track 2: {len(track2_data)} Bytes (Code 0D00H-19FFH)")
    log(f"    Track 3: {TRACK_DATA_SIZE} Bytes (Fuellung 53H)")

    bootsec = build_bootsec_bin(track0_data, track2_data)
    output_path = os.path.join(BUILD_DIR, 'bootsec.bin')
    with open(output_path, 'wb') as f:
        f.write(bootsec)
    log(f"    Geschrieben: {output_path} ({len(bootsec)} Bytes)")

    # --- Schritt 7: Vergleich mit Original ---
    log(f"\n[STEP 7] Vergleich mit Original")
    match = compare_with_original(bootsec, PREBUILT)

    # --- Schritt 8: Aufraeumen ---
    log("\n[STEP 8] Temporaere Dateien loeschen")
    for pattern in ['*.MAC', '*.mac', '*.REL', '*.rel', '*.PRN', '*.prn',
                    '*.SYM', '*.sym', 'm80.com', 'M80.COM']:
        for f in glob.glob(os.path.join(BUILD_DIR, pattern)):
            os.remove(f)
            log(f"    Geloescht: {os.path.basename(f)}")

    # --- Fertig ---
    log("\n" + "=" * 60)
    if match:
        log("FERTIG: bootsec.bin ist IDENTISCH mit dem Original!")
    else:
        log("FERTIG: bootsec.bin erzeugt (weicht vom Original ab)")
    log(f"Pfad:   {output_path}")
    log(f"Groesse: {len(bootsec)} Bytes")
    log("=" * 60)

    return 0 if match else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"\nFEHLER: {e}", file=sys.stderr)
        sys.exit(2)
