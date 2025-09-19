# CP/A ein CP/M80 2.2 kompatibles Betriebssystem für Rechner der K1520-Reihe

CP/A ist ein am Institut für Informatik und Rechentechnik der AdW der DDR entwickeltes, zu CP/M kompatibles Betriebssystem für Bürocomputer A5120, A5130, K8924, K8927 und PC1715. Es unterstützt 32–64 KB RAM, verschiedene Bildschirm- und Tastaturtypen, zahlreiche Diskettenformate und flexible Druckeranbindung.
Dieses Projekt enthält den Quellcode der BIOS Komponente sowie einige öffentlich verfügbare Erweiterungen, die in der Zwischenzeit gemacht wurden.

## Verzeichnisstruktur

- `src/`         – Quelltexte für BIOS, Makros und Systemteile
- `prebuilt/`    – Vorgefertigte Systemteile (z.B. BDOS.ERL, CCP.ERL, CPABAS.ERL)
- `tools/`       – Build-Tools (m80.com, linkmt.com, cpm.exe, ...)
- `build/`       – Build-Produkte und temporäre Dateien (wird bei jedem Build neu befüllt)
- `examples/`    – Eigene kleine Programme und Beispiel-Makefiles (z.B. hello.mac, name.mac)
- `doc/`         – Dokumentation (z.B. cpa_doc.pdf, cpa_doc.txt)

## Systemüberblick

Das System besteht aus drei Hauptteilen:

- **BIOS** (Quelltext, konfigurierbar)
- **BDOS** (vorgefertigt, Link-Eingabe)
- **CCP** (vorgefertigt, Link-Eingabe)

## Build-Anleitung

### Voraussetzungen

- Linux oder Windows
- Wine (unter Linux, um CP/M-Tools auszuführen)
- Die Tools m80.com, linkmt.com und cpm.exe müssen im Verzeichnis `tools/` liegen

### BIOS und System bauen

Im Hauptverzeichnis:
```sh
make
```
Das erzeugte System befindet sich dann als `build/@OS.com`.

### Beispielprogramme bauen

Im jeweiligen Unterverzeichnis (z.B. `examples/`):
```sh
make -f Makefile.hello
make -f Makefile.name
```
Die Tools werden automatisch aus `../tools/` kopiert und nach dem Build wieder entfernt.

### Aufräumen

```sh
make clean
```
Entfernt alle Build-Produkte und temporäre Dateien.

## Konfigurationsmöglichkeiten (BIOS)

Das BIOS ist hochgradig konfigurierbar. Die wichtigsten Optionen werden direkt im Quelltext (`src/bios.mac`) über sogenannte "equates" (Konstanten-Definitionen mit dem Assembler-Befehl `equ`) gesetzt. Die häufigsten Konfigurationsmöglichkeiten und typische Werte sind:

- **RAM-Größe:** `ramkb` (z.B. 64)
- **RAM-Floppy/Erweiterungen:** `oss`, `em256`, `mkd256`, `raf`, `rna` (0/1)
- **Bildschirm (crt):**
 - `K7024` (0): Standard-Bildschirmkarte
 - `DSY5` (1): Invers-Karte 
 - `B1715` (7): PC1715-Bildschirm
- **Tastatur:**
 - `typ80`: 3454 (K7634.54), 36 (K7636-Familie)
 - `kbdotp`: 0 (K7606), 1 (K7604), 2 (DEG-Spezial), 3 (K7633)
- **Laufwerke (diskA, diskB, ...):**
 - 10540: DD, SS, 5", 40 Tracks
 - 10580: DD, SS, 5", 80 Tracks
 - 11580: DD, DS, 5", 80 Tracks
 - 00877: SD, SS, 8", 77 Tracks
 - 10877: DD, SS, 8", 77 Tracks
 - 0: Laufwerk nicht vorhanden
- **Diskettenpuffer:** `dbufsz` (Exponent von 2, z.B. 10 für 1024 Bytes)
- **Weitere Schalter:**
 - `monitor`, `stpvar`, `mprot`, `cpastz`, `errvar`, `uhrvar`, `iobvar`, `costu` (jeweils 0/1)

Die Kommentare im Quelltext geben zu jedem Parameter weitere Hinweise und erlaubte Werte.

- **RAM-Größe:** 
	`ramkb` – RAM in KB (z.B. 64)
- **RAM-Floppy:**  
	`oss`, `em256`, `mkd256`, `raf`, `rna` – Unterstützung verschiedener RAM-Floppy- und Erweiterungskarten
- **Bildschirm:**  
	`crt` – Typ der Bildschirmkarte (z.B. K7024)
	Automatische Erkennung von 24x80 oder 16x64 Zeichen
- **Tastatur:**  
	`typ80`, `kbdotp` – Auswahl und automatische Erkennung verschiedener Tastaturtypen
- **Diskettenlaufwerke:**  
	`diskA`, `diskB`, `diskC`, `diskD` – Typ und Format der unterstützten Laufwerke (5¼", 8", DD/SS/DS)
	`format` – Automatische Formaterkennung aktivieren/deaktivieren
- **Drucker:**  
	`iobtty`, `ioblpt`, `iobuc1` – Konfiguration der Drucker- und Kopplungsschnittstellen
- **Puffergrößen:**  
	`dbufsz` – Größe des Diskettenpuffers (Exponent von 2, z.B. 10 für 1024 Bytes)
- **Sonderfunktionen:**  
	- `monitor` – BIOS-Monitor ein/aus
	- `stpvar` – STOP-Funktion (z.B. für Abbruch)
	- `mprot` – Speicherschutz
	- `cpastz` – Statuszeile
	- `errvar` – BIOS-Fehlermeldungen
	- `uhrvar` – BCD-Uhr
	- `iobvar` – IOBYTE-Unterstützung (flexible Gerätezuordnung)
	- `costu` – Nutzerdefinierte Stringtasten
	- u.v.m.

**Hinweis:**  
Die BIOS-Größe und damit die TPA (Transient Program Area) für Anwenderprogramme hängt direkt von den gewählten Optionen ab. Je mehr Features aktiviert werden, desto kleiner wird die TPA.

### Systemvarianten

- **Kaltstart:**  
	System wird von @OS.COM auf Diskette geladen, Hardware wird automatisch erkannt (RAM, Bildschirm, Tastatur, Laufwerke).
- **Warmstart:**  
	CCP wird aus dem BIOS kopiert (schneller, keine Systemspuren auf Disketten nötig).
- **Minimal-/Maximal-Konfiguration:**  
	Für Spezialzwecke kann ein sehr kleines BIOS (maximale TPA) oder ein voll ausgestattetes System generiert werden.


### Anpassung

Die Konfiguration erfolgt durch Anpassen der entsprechenden `equ`-Zeilen in `src/bios.mac` vor dem Build. Nach Änderungen einfach erneut `make` ausführen.

## Hinweise

- Die CP/M-Tools können keine Verzeichnisse verarbeiten. Deshalb werden alle benötigten Dateien vor dem Build ins Arbeitsverzeichnis kopiert.
- Die Makefiles sind ausführlich kommentiert und zeigen die einzelnen Schritte.
- Beispielprogramme und eigene Tools liegen in `examples/` und sind klar von den Systemquellen getrennt.
- Die Systemadresse für das Linken wird automatisch aus der M80-Ausgabe extrahiert.

## Systemdiskette erstellen und schreiben

Um eine lauffähige Systemdiskette für CP/A zu erstellen, gehe wie folgt vor:

1. **Systemdisk-Image bauen:**
   
   Im Verzeichnis `systemDisk/` befindet sich ein Makefile, das alle nötigen Schritte automatisiert:
   
   ```sh
   cd systemDisk
   make diskImage
   ```
   
   Dadurch wird ein Diskettenimage (`build/cpadisk.img`) erzeugt, das das Betriebssystem und alle Zusatztools enthält.

2. **Zusatztools:**
   
   Im Verzeichnis `additions/` liegen verschiedene Tools und Hilfsprogramme, die automatisch mit auf die Systemdiskette kopiert werden. Diese Werkzeuge erleichtern die Arbeit mit dem Betriebssystem und stehen nach dem Booten direkt zur Verfügung.

3. **Systemdiskette auf physikalisches Laufwerk schreiben:**
   
   Mit dem Ziel `writeImage` im selben Verzeichnis kann das erzeugte Image auf ein echtes Laufwerk geschrieben werden (z.B. mit dem Tool `gw`):
   
   ```sh
   make writeImage
   ```
   
   Das Makefile nutzt dazu die passenden Parameter und Konfigurationsdateien. Details siehe Kommentare im `systemDisk/Makefile`.

**Hinweis:**
- Die Systemdiskette enthält nach dem Build alle im additions-Ordner befindlichen Tools.
- Für den Schreibvorgang werden ggf. Administratorrechte benötigt.

## Lizenz
Bitte beachte die Lizenzhinweise in den Quelldateien und Dokumenten.

---

Fragen und Beiträge sind willkommen!
