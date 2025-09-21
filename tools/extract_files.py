#!/usr/bin/env python3
"""
extract_files.py
Extrahiert alle Dateien aus einem CP/M-Disketten-Image oder direkt von Diskette (Greaseweazle) in ein neues Verzeichnis unterhalb des Ordners Disketten.
Verwendung:
    python3 extract_files.py [-t FORMAT] -f <disk_image.img> | -g <DiskName>
    -t FORMAT   Dateisystemformat für cpmtools (Standard: cpa800)
    -f FILE     Image-Datei einlesen (z.B. foo.img)
    -g DiskName Diskette mit Greaseweazle einlesen (legt DiskName.img temporär an)
    -h          Zeigt diese Hilfe an

Das Zielverzeichnis und ggf. das temporäre Image werden immer unterhalb des Ordners Disketten/ angelegt.
Existiert Disketten/ nicht, wird es automatisch erzeugt.
Nach Extraktion wird ein temporär erzeugtes Image automatisch gelöscht.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

def show_help():
    print(__doc__)

def run(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei Befehl: {' '.join(cmd)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-t', metavar='FORMAT', default='cpa800', help='Dateisystemformat für cpmtools (Standard: cpa800)')
    parser.add_argument('-f', metavar='FILE', help='Image-Datei einlesen (z.B. foo.img)')
    parser.add_argument('-g', metavar='DISKNAME', help='Diskette mit Greaseweazle einlesen (legt DiskName.img an)')
    parser.add_argument('-h', action='store_true', help='Zeigt diese Hilfe an')
    args = parser.parse_args()

    if args.h or (not args.f and not args.g):
        show_help()
        sys.exit(0)

    CPMCP = 'cpmcp'
    CPMLS = 'cpmls'
    GW = 'gw'
    FORMAT = args.t
    DISKDIR = Path('Disketten')
    DISKDIR.mkdir(exist_ok=True)

    img_file = None
    temp_img = None
    # Greaseweazle: Diskette einlesen
    if args.g:
        img_file = DISKDIR / f"{args.g}.img"
        print(f"Lese Diskette mit Greaseweazle ein: {img_file} (Format: {FORMAT})")
        run([GW, 'read', '--diskdefs=cpaFormates.cfg', f'--format={FORMAT}', str(img_file)])
        temp_img = img_file
    elif args.f:
        orig_file = Path(args.f)
        basename_noext = orig_file.stem
        ext = orig_file.suffix.lower()
        if ext != '.img':
            img_file = DISKDIR / f"{basename_noext}.img"
            print(f"Konvertiere {orig_file} nach {img_file} (Format: {FORMAT}) ...")
            run([GW, 'convert', '--diskdefs=cpaFormates.cfg', f'--format={FORMAT}', str(orig_file), str(img_file)])
            temp_img = img_file
        else:
            img_file = orig_file
            if img_file.parent != DISKDIR:
                dest = DISKDIR / img_file.name
                shutil.copy2(img_file, dest)
                img_file = dest
    if not img_file or not img_file.exists():
        print("Kein gültiges Image angegeben.")
        show_help()
        sys.exit(1)

    # Zielverzeichnis bestimmen
    basename = img_file.stem
    new_dir = DISKDIR / basename
    count = 1
    while new_dir.exists():
        if new_dir.name.endswith(f"_{count-1}"):
            count += 1
            new_dir = DISKDIR / f"{basename}_{count}"
        else:
            new_dir = DISKDIR / f"{basename}_{count}"
    new_dir.mkdir()

    # Zeige Inhalt der Diskette
    run([CPMLS, '-Ff', FORMAT, str(img_file)])

    # Liste alle Dateien im Image auf (ohne Kopfzeile)
    result = subprocess.run([CPMLS, '-f', FORMAT, str(img_file)], capture_output=True, text=True, check=True)
    files = [line.split()[0] for line in result.stdout.strip().splitlines()[1:] if line.strip()]
    for fname in files:
        if fname:
            run([CPMCP, '-f', FORMAT, str(img_file), f'0:{fname}', str(new_dir)])

    # Zähle extrahierte Dateien
    count_files = sum(1 for _ in new_dir.glob('*') if _.is_file())
    print(f"Es wurden {count_files} Dateien in den Ordner {new_dir} extrahiert.")

    # Temporäres Image löschen
    if temp_img and temp_img.exists():
        temp_img.unlink()
        print(f"Temporäres Disketten-Image {temp_img} wurde gelöscht.")

if __name__ == '__main__':
    main()
