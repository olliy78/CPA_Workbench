# EM256 – 16-Bit-Erweiterungskarte des BC A5120

**Stand der Analyse:** April 2026  
**Quellen:**
- `src/bc_a5120/bios.mac`, `src/bc_a5120/biosrem.mac`, `src/bc_a5120/biosremc.mac` (CP/A-BIOS)
- `16bitTest/docs/Auszug_Handbuch.md` (Handbuch A 5120.16 Erweiterungsmodul)
- `16bitTest/docs/rfe83-10-629ff-16BitZRE-KartezumK1520.txt` (TH Karl-Marx-Stadt, Z8001 ZRE-Karte)

---

## 1. Übersicht

Die **EM256** ist eine Erweiterungskarte für den DDR-Bürocomputer **BC A5120** (und hardwareäquivalente Systeme wie K8924, K8927, A5130). Sie wertet den A 5120 zum **A 5120.16** auf – einem 16-Bit-Programmentwicklungsplatz, der unter dem UNIX-kompatiblen Betriebssystem **MUTOS 8000** arbeiten kann.

Die Karte besteht aus zwei Steckeinheiten im K1520-Format (215 × 170 mm):
- **Steuerkarte** mit U8001-Mikroprozessor, PIO (U855D), Taktgenerator (DS 8127, 16 MHz Quarz → 4 MHz Systemtakt), Statusdecoder, Segment-/Adressumschalter, Steuer-/Statusregistern, I/O-Decoder und Eigenrefreshgenerator
- **Speicherkarte** mit 256 KB DRAM (36 × KM 565 RU 5G à 64 KBit, 4 Blöcke × 9 Chips inkl. Parität), Ablaufsteuerung, RAS-Decoder und eigenem Refreshzähler

Wesentliche Merkmale:
- **256 KB DRAM** – gemeinsam genutzt von U880 und U8001, aufgeteilt in 4 Segmente à 64 KB
- **U8001** – DDR-Derivat des **Zilog Z8001** (segmentierter 16-Bit-Prozessor), 4 MHz Systemtakt
- **PIO (U855D, Bauteil A32)** – einzige I/O-Komponente vom K1520-Bus aus, im Bitmode konfiguriert
- **16×4-Bit-Konfigurationsregister (Attributspeicher, Bauteil A22)** – steuert RAM-Paging
- **Steuer-/Statusregister (A33, A34, A35, A36)** – Interprozesskommunikation U880 ↔ U8001
- **Kein EPROM** – der U8001 bezieht seinen Startcode ausschließlich aus dem DRAM

> **Wichtige Korrektur:** Der Prozessor auf der EM256 ist ein **U8001** (= Z8001), die **segmentierte** Variante des Z8000-Prozessors. Der Z8001 verwendet 23-Bit-Adressen (7-Bit-Segment + 16-Bit-Offset) und hat ein anderes Reset-Vektor-Format als der unsegmentierte Z8002. Die EM064-Variante kann wahlweise mit U8001 oder U8002 bestückt sein.

> **Stromaufnahme:** Steuerkarte 1,1 A bei 5 V, Speicherkarte 950 mA bei 5 V.

### 1.1 Betriebsarten

Der EM arbeitet in zwei Betriebsarten, die durch Software umgeschaltet werden:

- **8-Bit-Mode:** Der Speicher des EM steht vollständig dem U880-K1520-System zur Verfügung. Der U8001 ist im Reset. Dies ist der Standardzustand nach dem Einschalten (durch automatisches RESET-16). Im CP/A-BIOS wird die Karte ausschließlich als **RAM-Floppy „M:"** in diesem Modus betrieben.
- **16-Bit-Mode:** Der U8001 hat das alleinige Zugriffsrecht auf die Speicherkarte. Der U880 arbeitet in seinem eigenen K1520-Speicher weiter und übernimmt periphere Aufgaben (Floppy, Bildschirm, Tastatur).

### 1.2 Historischer Kontext

Die EM256 folgt dem Konzept der an der TH Karl-Marx-Stadt entwickelten 16-Bit-ZRE-Karte für das K1520-System (Rehm/Fey, 1983). Diese nutzte ebenfalls einen Z8001 mit 4 MHz und demonstrierte die Integration in das K1520-Bussystem mit gemeinsamer Nutzung bestehender 8-Bit-Speicher- und E/A-Baugruppen. Die EM256 geht über dieses Konzept hinaus, indem sie einen eigenen 256-KB-Speicher mitbringt und die Kommunikation über dedizierte Register statt über geteilten K1520-Bus abwickelt.

---

## 2. I/O-Adressen

Die EM256 belegt 8 aufeinanderfolgende Portadressen im I/O-Raum des U880. Die Basisadresse (MODADR) ist über Wickelbrücken X10/X11 auf der Steuerkarte konfigurierbar; beim A 5120.16 auf `0xA8` eingestellt.

| Name | Adresse | Richtung | Beschreibung |
|------|---------|----------|--------------|
| `modadr+0` | `0xA8` | Lesen | **PIO Port A Daten** – Statuseingänge (TREN, INT16, N/S, 8/16, VI, Kennung) |
| `modadr+1` | `0xA9` | Lesen/Schreiben | **PIO Port B Daten** – Steuerausgänge (RESET16, RAMEN, STOP, SG0/1, TRQ8, PR) + Eingabe Bit 7 (PER) |
| `modadr+2` | `0xAA` | Schreiben | **PIO Port A Steuerregister** – Konfiguration via OTIR |
| `modadr+3` | `0xAB` | Schreiben | **PIO Port B Steuerregister** – Konfiguration via OTIR |
| `modadr+4` | `0xAC` | Schreiben | **Status-8-Register (A36)** – Statusbyte an U8001 (wird bei VI-ack als High-Byte gelesen) |
| `modadr+5` | `0xAD` | Schreiben | **Vektor-8-Register (A34)** – Interruptvektor an U8001; Schreiben löst VI aus |
| `modadr+6` | `0xAE` | Lesen | **Status-16-Register (A35) lesen** – vom U8001 geschriebener Status |
| `modadr+7` | `0xAF` | Lesen/Schreiben | **Attributspeicher (16×4-RAM, A22)** – Page/Write-Enable, Adresssubstitution; Schreiben = Konfigurieren, Lesen = negierter Inhalt |

> **ACHTUNG – I/O-Zugriff auf PIO-Datenports:** Der Z80-Befehl `OUT (n), A` legt den Akkumulator-Wert auf die Adressleitungen A8–A15. Die EM256 dekodiert A8–A15 als Subadresse des Attributspeichers (16×4-RAM). Dadurch können PIO-Datenschreibzugriffe fehlschlagen, wenn der Akkumulator bestimmte Werte enthält. **Lösung:** Für alle PIO-Datenportzugriffe `OUT (C), A` / `IN A, (C)` mit **B=0** verwenden. Dies erzeugt die saubere Adresse `0x00nn` mit A8–A15 = 0x00. Für OTIR-basierte Steuerwort-Initialisierung ist dies kein Problem, da OTIR die Adresse aus B:C bildet und B als Zähler auf 0 dekrementiert.

> **Quelle:** `src/bc_a5120/biosremc.mac` Z. 10–52, `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.7.1

---

## 3. PIO-Port-Belegung (U855D, Bauteil A32)

Die PIO ist in der Interruptprioritätenkette des K1520 eingebunden und wird vom U880 programmiert. Beide Tore arbeiten im **Bit-E/A-Modus (Mode 3)**. Die unnegiert dargestellten Signale sind high-aktiv, die negierten low-aktiv.

### PIO Port A – `modadr+0` = `0xA8` (alle 8 Bits **Eingabe**)

| Bit | Name | Funktion |
|-----|------|----------|
| 0 | `pioa_0` | Kennung vom U8001 (Bit 0) – aus Register A33, Bedeutung durch Software festgelegt |
| 1 | `pioa_1` | Kennung vom U8001 (Bit 1) – aus Register A33 |
| 2 | `pioa_2` | Kennung vom U8001 (Bit 2) – aus Register A33 |
| 3 | `n_vi` | VI-Anforderung (negiert) – low = Interruptvektor in A34 wurde noch nicht gelesen |
| 4 | `int16` | **Interrupt vom U8001 an U880** – low-Pegel löst Interrupt aus (aus A33 Bit 4) |
| 5 | `n_s` | Normal-(1) oder Systemmode-(0) des U8001 |
| 6 | `m8_16` | 8-Bit-(1) oder 16-Bit-Modus-(0) – aus FF A29/09 (Betriebsartensteuerung) |
| 7 | `tren` | **Transfer Enable** – U8001 hat Speicherzugriff abgegeben (= µ0-Ausgang des U8001) |

Der PIO Port A wird im BIOS mit `0xCF` (Bit-E/A-Modus) und `0xFF` (alle Bits Eingabe) initialisiert, Interrupts sind verboten.

### PIO Port B – `modadr+1` = `0xA9` (Bits 0–6 **Ausgabe**, Bit 7 **Eingabe**)

| Bit | Name | Funktion |
|-----|------|----------|
| 0 | `sg0p` | Segment-Bit 0 für U880-Speicherzugriff auf EM256 |
| 1 | `sg1b` | Segment-Bit 1 für U880-Speicherzugriff auf EM256 |
| 2 | `n_ramen` | RAM-Enable (negiert) – 0 = Speicher für U880 zugänglich (schaltet MEMDI) |
| 3 | `n_stop` | U8001-Stop (negiert) – 0 = anhalten (steuert STOP-Eingang des U8001) |
| 4 | `reset16` | **U8001-Reset** – 1 = in Reset halten; setzt FF A29, LED V2 leuchtet |
| 5 | `n_trq8` | Transfer-Request U880→U8001 (negiert) – 0 = 8-Bit-Mode anfordern (→ µI am U8001) |
| 6 | `prreset` | Reset Paritätsfehler-Latch (Flanke 0→1→0 nötig) |
| 7 | `n_pe` | Paritätsfehler (negiert, **Eingabe**) – 0 = Fehler aufgetreten, löst Interrupt aus |

> **Quelle:** `src/bc_a5120/biosremc.mac` Z. 10–27, `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.7.2

---

## 3a. Steuer- und Statusregister (Interprozesskommunikation)

Die Kommunikation zwischen U880 und U8001 erfolgt über vier 8-Bit-Register auf der Steuerkarte, zusätzlich zur PIO. Die Register sind **nicht** rücklesbar durch den Prozessor, der sie beschreibt.

### Vom U8001 beschriebene Register

**A33 – Steuer-16-Register** (beschrieben über Low-Byte des U8001-AD-Busses):

| Bit | Signal | Funktion |
|-----|--------|----------|
| 0 | PIOA-0 | → PIO Port A Bit 0 (Kennung, durch Software definierbar) |
| 1 | PIOA-1 | → PIO Port A Bit 1 |
| 2 | PIOA-2 | → PIO Port A Bit 2 |
| 3 | | Freigabe Einzelbefehlsabarbeitung (TRACE-Funktion) |
| 4 | INT-16 | → PIO Port A Bit 4 (Interrupt-Auslösung an U880) |
| 5 | AD5* | Segmentmode-Festlegung (Bit 0) |
| 6 | AD6* | Segmentmode-Festlegung (Bit 1) |
| 7 | AD7* | Segmentmode-Festlegung (Bit 2) |

Wird durch RESET OUT beim Einschalten in Grundstellung gesetzt.

**A35 – Status-16-Register** (beschrieben über High-Byte des U8001-AD-Busses):
- Vom U880 lesbar über Port `0xAE` (`modadr+6`, READ STATUS-16)
- 8 Bit frei definierbar durch U8001-Software

### Vom U880 beschriebene Register

**A36 – Status-8-Register** (Port `0xAC`, `modadr+4`):
- Nicht rücklesbar
- Wird im VI-Bestätigungszyklus des U8001 als High-Byte des Interruptvektors gelesen

**A34 – Vektor-8-Register** (Port `0xAD`, `modadr+5`):
- **Schreiben löst Vektorinterrupt (VI) am U8001 aus!**
- Im VI-Bestätigungszyklus wird der Vektor als Low-Byte des AD-Busses gelesen
- Vor erneutem Beschreiben muss über PIO-A Bit 3 (`n_vi`) geprüft werden, ob der vorherige Vektor bereits gelesen wurde (n_vi = high → bereit für neuen Vektor)

### Sequenz: U880 unterbricht U8001 per Vektorinterrupt

```z80
; 1. Prüfen ob U8001 bereit für neuen Vektor
wait_vi:
    LD   B, 0
    LD   C, 0A8h          ; Port A Daten
    IN   A, (C)
    BIT  3, A             ; n_vi: 1 = bereit
    JR   Z, wait_vi

; 2. Status-Byte schreiben (wird High-Byte des Vektors)
    LD   A, status_byte
    OUT  (0ACh), A        ; modadr+4

; 3. Vektor schreiben (löst VI aus!)
    LD   A, vektor_byte
    OUT  (0ADh), A        ; modadr+5
```

> **Quelle:** `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.6

---

## 3b. Betriebsartensteuerung (8/16-Bit-Umschaltung)

Das FF A29 (Ausgang = Signal **8/16**) bestimmt, welcher Prozessor Speicherzugriff hat:

### Einschaltzustand → 8-Bit-Mode
Nach dem Einschalten sind die PIO-Ausgänge hochohmig. Über Pullup R4:2 ist RESET-16 high. Der Taktgenerator DS 8127 (A55) hält den U8001 im Reset. FF A29 wird gesetzt → 8/16 = high → LED V2 leuchtet.

### Wechsel 8-Bit → 16-Bit-Mode
1. U880 hebt RESET-16 auf: `reset16 = 0` in PIO Port B
2. FF A29 wird rückgesetzt → 8/16 = low
3. U8001 startet (liest Reset-Vektor aus Adresse 0x0000)
4. U8001 hat alleiniges Zugriffsrecht auf EM256-Speicher

### Wechsel 16-Bit → 8-Bit-Mode (kooperativ)
1. U880 setzt `n_trq8 = 0` (TRQ8 aktiv) über PIO Port B Bit 5
2. U8001 sieht µI = 0, antwortet mit µ0 = 0
3. **TREN = 1** wird an PIO Port A Bit 7 sichtbar
4. BUSRQ = 0 wird an U8001 angelegt
5. U8001 quittiert mit BUSAK = 0
6. FF A29 wird im nächsten M1-Zyklus des U880 gesetzt → 8/16 = high
7. U880 hat wieder Speicherzugriff

### Wechsel 16-Bit → 8-Bit-Mode (erzwungen)
```z80
; RESET-16 setzen: erzwingt sofortigen 8-Bit-Mode + U8001-Reset
LD   A, 1 SHL reset16 OR 1 SHL n_ramen
LD   B, 0
LD   C, 0A9h
OUT  (C), A
```

> **Hinweis:** Die Abgabe des Speicherzugriffs vom U8001 kann auch über INT-16 (PIO-A Bit 4) dem U880 per Interrupt gemeldet werden.

> **Quelle:** `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.7.3

---

## 3c. Segmentweiche (256 KB → 4 × 64 KB)

Der 256-KB-Speicher ist in 4 Segmente à 64 KB unterteilt. Die Segmentauswahl erfolgt unterschiedlich je nachdem, ob der U880 oder U8001 zugreift:

### U880-Zugriff (8-Bit-Mode)
Die Segmentbits kommen von PIO Port B: `sg0p` (Bit 0) und `sg1b` (Bit 1).

### U8001-Zugriff (16-Bit-Mode)
Die Segmentweiche A42 bietet drei Modi, umschaltbar über das Steuer-16-Register A33 (Bits AD6\* und AD7\*):

| AD7\* | AD6\* | Modus | SG0 kommt von | SG1 kommt von |
|:-----:|:-----:|:-----:|---------------|---------------|
| 0 | 0/1 | **Mode 0** | AD5\* (A33 Bit 5) | AD6\* (A33 Bit 6) |
| 1 | 0 | **Mode 1** | INSTR (Programm/Daten) | N/S (Normal/System) |
| 1 | 1 | **Mode 2** | SN0 (CPU-Segmentleitung) | SN1 (CPU-Segmentleitung) |

**Mode 0** – Direktwahl durch U8001-Software:
| AD5\* | AD6\* | Segment |
|:-----:|:-----:|---------|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 0 | 1 | 2 |
| 1 | 1 | 3 |

**Mode 1** – Automatische Zuordnung nach Zugriffsart und Betriebsart:
| INSTR | N/S | Segment | Zuordnung |
|:-----:|:---:|:-------:|-----------|
| 0 | 0 | 0 | System Data |
| 1 | 0 | 1 | System Instruction |
| 0 | 1 | 2 | Normal Data |
| 1 | 1 | 3 | Normal Instruction |

**Mode 2** – Hardware-Segmentierung des Z8001:
| SN0 | SN1 | Segment |
|:---:|:---:|:-------:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 0 | 1 | 2 |
| 1 | 1 | 3 |

> **Für einfache Programme:** Mode 0 mit AD5\*=AD6\*=AD7\*=0 (Grundstellung nach Reset) → alle Zugriffe gehen in Segment 0.

> **Quelle:** `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.4

---

## 4. Der Attributspeicher (16×4-RAM, Bauteil A22) und die B-Register-Adressierung

Der 256-KB-Speicher wird für den U880-Zugriff durch einen 16×4-Bit-Attributspeicher gesteuert, der auf Port `0xAF` (= `modadr+7`) liegt. Er ermöglicht die seitenweise Einblendung von EM256-Speicherbereichen in den Z80-Adressraum.

### Adressierungsprinzip

Beim Schreiben auf `modadr+7` wird die Subadresse aus den **oberen 4 Bits der I/O-Adresse** (A12–A15, entspricht B[7:4] bei `OUT (C), A`) entnommen:

```
Volle 16-Bit I/O-Adresse = B:C
  B[7:4] = Subadresse (0x0–0xF) → wählt den 4KB-Z80-Adressbereich
  B[3:0] = Don't care
  C      = 0xAF (Basisadresse des Attributspeichers)
```

**Beim Lesen** (Speicherzugriff durch U880 auf EM-Bereich) wird automatisch über AB12–AB15 die Subadresse gebildet. Der Inhalt des RAM ist über den Treiber A12 **negiert** rücklesbar.

Die 16 Subadress-Einträge entsprechen den 16 möglichen 4KB-Fenstern im Z80-Adressraum:

| B-Wert | Portadresse | Kontrolliert Z80-Fenster |
|--------|------------|--------------------------|
| `0x00` | `0x00AF`   | `0x0000–0x0FFF`          |
| `0x10` | `0x10AF`   | `0x1000–0x1FFF`          |
| `0x40` | `0x40AF`   | `0x4000–0x4FFF` ← EM256-Fenster (`em256adr`) |
| `0xF0` | `0xF0AF`   | `0xF000–0xFFFF`          |

Der **Datenwert** im `OUT (C), A`-Befehl konfiguriert das Mapping:

```
Datenbyte-Format:
  Bit 0 = PEN      : Page enable – 1 = Speicherzugriff durch U880 erlaubt
                      (gleichzeitig wird MDO/MEMDI aktiv → K1520-Speicher gesperrt)
  Bit 1 = WE       : Write enable – 1 = Schreiben erlaubt (0 = Schreibschutz)
  Bit 2 = /A14-8   : Ersetzt Adressbit AB14 für physische Adresse (negiert)
  Bit 3 = /A15-8   : Ersetzt Adressbit AB15 für physische Adresse (negiert)
```

> **Hinweis:** Die Bits PEN und WE sind im Handbuch **positiv-logisch** definiert (1 = aktiv), während sie im BIOS-Quellcode als `n_pagen` und `n_write` (negiert, 0 = aktiv) bezeichnet werden. Der BIOS-Code schreibt `1 SHL n_pagen OR 1 SHL n_write` (= 0x03) zum **Deaktivieren**, und `0x00` mit passenden Adressbits zum **Aktivieren**. Das Handbuch sagt: PEN=1 erlaubt Zugriff, WE=0 sperrt Schreiben.

Die Bits 3:2 bestimmen, welche physische 16KB-Region des EM256-DRAM erscheint:

| Datenbits 3:2 | EM256-Seite | EM256-Adressbereich |
|--------------|-------------|---------------------|
| `11` (Datenbyte `0x0C` + enable) | Seite 0 | `0x00000–0x03FFF` |
| `10` (Datenbyte `0x08` + enable) | Seite 1 | `0x04000–0x07FFF` |
| `01` (Datenbyte `0x04` + enable) | Seite 2 | `0x08000–0x0BFFF` |
| `00` (Datenbyte `0x00` + enable) | Seite 3 | `0x0C000–0x0FFFF` |

> **Für Seite 0 (U8001-Startcode):** `B=0x4C`, `C=0xAF`, Datenbyte=`0x0C`  
> (Subadresse 4 → Z80-Fenster 0x4000; Bits 3:2=11 → EM256 A15:A14=00 → Seite 0; PEN=0, WE=0 → Zugriff + Schreiben gesperrt lt. BIOS-Konvention, aber EM256 erkennt sich selbst auf em256adr)

> **Quelle:** `src/bc_a5120/biosremc.mac` Z. 30–52, `src/bc_a5120/biosrem.mac` Z. 68–113, `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.5

---

## 5. Adressierung des RAM durch den U880

### Einblenden einer 16-KB-Page (Funktion `ramon`)

Die Zuordnung von CP/A-„Track"-Nummer zu physischer Speicheradresse:

```
Track-Byte:  Bit 7..4 = Page (P3-P0)
             Bit 3..2 = reserviert (0)
             Bit 1..0 = Segment (S1-S0)
```

**Schritt 1** – Segment und Page aus Track-Nummer extrahieren:
```z80
; A = Track-Nummer: 0 0 S1 S0 P3 P2 P1 P0
LD D, A
RRCA \ RRCA \ RRCA \ RRCA  ; A = P3 P2 P1 P0  0  0 S1 S0
AND 3Fh                     ; A =  0  0 P1 P0  0  0 S1 S0
OR high(hbemadr)             ; A = H3 H2 P1 P0  0  0 S1 S0  (hbemadr = 0x4000 → H3H2=01)
LD B, A
LD A, D
CPL
AND 0Ch                     ; A =  0  0  0  0 /P3/P2  0  0
OR B                        ; A = H3 H2 P1 P0 /P3/P2 S1 S0
LD B, A
```

**Schritt 2** – 16×4-RAM einblenden:
```z80
LD C, modadr+7              ; C = 0xAF (Basisadresse des RAM-Registers)
AND 0Ch                     ; nur /P3/P2 für RAM-Register verwenden
OUT (C), A                  ; Page einschalten, Write-Enable setzen
```

**Schritt 3** – Segment in PIO Port B setzen, U8000 bleibt in Reset:
```z80
LD A, B
AND 3                       ; Segmentnummer (sg0p, sg1b)
OR 1 SHL reset16            ; Bit 4 setzen → U8000 bleibt in RESET
OUT (modadr+1), A           ; RAM scharf (n_ramen=0 implizit durch Segment-Bits)
```

**Schritt 4** – Z80-Adresse des Sektors berechnen:
```z80
LD A, B
AND 0F0h
LD D, A                     ; Höheres Nibble = Page → Adresse im 0x4000-Fenster
XOR A
LD E, A                     ; DE = Basisadresse des 16KB-Blocks in U880-Adressraum
; + Sektor-Offset:
LD A, (dsectr) \ DEC A      ; Sektor 1-basiert → 0-basiert
LD H, A \ LD L, 0
SRL H \ RR L                ; HL = (Sektor-1) * 128
ADD HL, DE                  ; HL = absolute Z80-Adresse des Sektors
```

> **Quelle:** `src/bc_a5120/biosrem.mac`, Zeilen 68–113

### Ausblenden (`ramoff`)
```z80
LD A, B
AND 0Ch
OR 1 SHL n_pagen OR 1 SHL n_write  ; Page und Write-Enable deaktivieren
OUT (C), A
LD A, 1 SHL reset16 OR 1 SHL n_ramen  ; RAM deaktivieren, U8000 bleibt in Reset
OUT (modadr+1), A
```

---

## 6. PIO-Initialisierungssequenz (BIOS-Kaltstart)

Die folgende Sequenz führt das CP/A-BIOS beim Kaltstart aus (`src/bc_a5120/biosremc.mac`, `emina`):

```z80
; Interruptvektor für Paritätsfehler eintragen
LD HL, parrou
LD (intvec+ivpar), HL

; PIO Port A initialisieren (3 Bytes via OTIR an Steuerregister 0xAA)
LD B, 3
LD HL, painit          ; 0CFh, 0FFh, 07h
LD C, modadr+2         ; 0xAA = PIO Port A Steuerregister
OTIR

; PIO Port B initialisieren (5 Bytes via OTIR an Steuerregister 0xAB)
LD B, 5
LD HL, pbinit          ; ivpar, 0CFh, 80h, 97h, 80h
LD C, modadr+3         ; 0xAB = PIO Port B Steuerregister
OTIR

; Paritäts-Latch zurücksetzen, dann Ruhezustand herstellen
LD A, 1 SHL prreset OR 1 SHL reset16 OR 1 SHL n_ramen
OUT (modadr+1), A      ; Port B Daten: Parity-Reset-Impuls (0x54)
LD A, 1 SHL n_ramen OR 1 SHL reset16  ; RAM aus, U8001 in Reset
OUT (modadr+1), A      ; Port B Daten: Idle-Zustand (0x14)
```

> **Hinweis:** Das BIOS verwendet hier `OUT (modadr+1), A` (= `OUT (n), A`). Bei diesen Werten legt der Akkumulator 0x54 bzw. 0x14 auf A8–A15. Im Kontext des Kaltstarts (direkt nach OTIR-Initialisierung) funktioniert dies, da die PIO bereits konfiguriert ist. Für Eigenprogramme ist `OUT (C), A` mit B=0 sicherer (siehe Abschnitt 2).

**Initialisierungsdaten:**

```
painit (Port A, 3 Bytes):
  0CFh  = Bit-E/A-Modus (Mode 3)
  0FFh  = alle 8 Bits Eingabe
  07h   = Interrupts verboten, keine Maske

pbinit (Port B, 5 Bytes):
  ivpar = Interruptvektor für Paritätsfehler (gerade Adresse)
  0CFh  = Bit-E/A-Modus (Mode 3)
  80h   = Bit 7 Eingabe (n_pe), Bits 0–6 Ausgabe
  97h   = Maske folgt (Bit4=1), 0-Pegel löst INT aus (Bit3=0), INT Enable (Bit7=1)
  80h   = Bit 7 (n_pe) löst Interrupt aus (Paritätsfehler-Erkennung)
```

> **Hinweis für Eigenprogramme:** Port B wird mit nur 3 Bytes initialisiert wenn keine
> Paritätsfehler-Interrupts benötigt werden: `0CFh, 80h, 07h` (wie in em256tst.mac).

---

## 7. Erkennung der EM256-Karte (BIOS-Methode)

Die korrekte EM256-Erkennung nutzt die **physische Trennung** zwischen Z80-RAM und EM256-DRAM.
Die Methode stammt direkt aus `src/bc_a5120/biosremc.mac`:

```
1. Aktuellen Z80-RAM-Inhalt an em256adr (0x4000) sichern
2. Z80-RAM mit 0x0000 überschreiben (bekannter Zustand)
3. EM256 Seite 0 einblenden  (B=0x4C, C=0xAF, Daten=0x0C, PIO-B n_ramen=0)
4. Muster 0xA55A in EM256 schreiben (= Z80-Adresse 0x4000)
5. Rücklesen: muss 0xA55A sein (Schreib-Test)
6. EM256 ausblenden (RAMOFF)
7. Z80-RAM lesen:
   → 0x0000 : EM256 war aktiv → Schreiben ging in EM256-DRAM ✓
   → 0xA55A : EM256 war NICHT aktiv → Schreiben ging in Z80-RAM ✗
```

**Warum nicht Seiten-Vergleich?** Zwei EM256-Seiten können zufällig gleichen Inhalt
haben (z.B. beide uninitialisiert gleich 0xFF). Die BIOS-Methode ist eindeutig, weil
Z80-RAM und EM256-DRAM **physisch getrennte** Speicherbereiche sind.

---

## 8. Starten des U8001 und Ausführen von 16-Bit-Code

### 8.1 Voraussetzungen

Der U8001 (Z8001-Derivat) arbeitet im **segmentierten Modus** und holt seinen **Reset-Vektor** aus Adresse `0x0000` des **EM256-DRAM**. Da die Karte **keinen EPROM** hat, muss der U880 zuerst Code in den Shared-DRAM schreiben, bevor der U8001 freigegeben wird.

Im Einschaltzustand steht das Steuer-16-Register A33 in Grundstellung (alle Bits 0), was **Mode 0** der Segmentweiche mit AD5\*=AD6\*=0 ergibt → alle U8001-Zugriffe gehen in **Segment 0**. Für einfache Programme reicht dies aus.

> **Z8001 Reset-Vektor (segmentierter Modus, 4 Bytes):**  
> - Bytes 0–1: FCW (Flag and Control Word) – z.B. 0x0000 für Normal Mode  
> - Bytes 2–3: PC (Startadresse des Codes im Segment 0)  
> Der Code muss sich in Segment 0 des EM256-DRAM befinden (= Z80-Fenster `em256adr` = 0x4000 bei Seite 0).

### 8.2 Startsequenz (U880-Assembler-Code)

> **Alle PIO-Datenportzugriffe verwenden `OUT (C), A` / `IN A, (C)` mit B=0!**  
> Siehe Abschnitt 2 für die Begründung.

```z80
;==============================================================
; Schritt 1: U8001-Code in Shared-DRAM laden (U8001 noch in Reset)
;==============================================================

; Seite 0 einblenden (B=0x4C, C=0xAF, Daten=0x0C)
LD B, 04Ch
LD C, modadr+7
LD A, 0Ch                    ; /A15=1, /A14=1 → Seite 0, PEN+WE aktiv
OUT (C), A

; RAM für U880 freigeben (n_ramen=0, reset16=1)
LD A, 1 SHL reset16          ; 0x10
LD B, 0
LD C, modadr+1               ; 0xA9 = Port B Daten
OUT (C), A

; U8001-Code kopieren: Z80-Adresse 0x4000 = U8001-Adresse 0x0000 (Segment 0)
LD HL, u8001_code
LD DE, em256adr              ; 0x4000
LD BC, u8001_code_len
LDIR

; RAM ausblenden
LD B, 04Ch
LD C, modadr+7
LD A, 0Fh                    ; /A15=1, /A14=1, PEN=1 (disabled), WE=1 (disabled)
OUT (C), A
LD A, 1 SHL reset16 OR 1 SHL n_ramen   ; 0x14
LD B, 0
LD C, modadr+1
OUT (C), A

;==============================================================
; Schritt 2: U8001 freigeben (Reset aufheben)
;==============================================================

; n_ramen=1, n_stop=1 (läuft), reset16=0 (freigeben!)
LD A, 1 SHL n_stop OR 1 SHL n_ramen    ; 0x0C
LD B, 0
LD C, modadr+1
OUT (C), A
; U8001 startet jetzt und liest Reset-Vektor von seiner Adresse 0x0000

;==============================================================
; Schritt 3: Auf Fertigmeldung des U8001 warten
;==============================================================
; TREN (Bit 7): wird high wenn U8001 Bus freigibt (via µ0)
; INT16 (Bit 4): wird low wenn U8001 es über Register A33 setzt
; HALT: Der Z8001-HALT-Befehl hält die CPU an, setzt aber
;       NICHT automatisch TREN oder INT16!
wait_u8:
    LD   B, 0
    LD   C, modadr             ; 0xA8 = Port A Daten
    IN   A, (C)
    BIT  tren, A               ; Bit 7: Transfer Enable?
    JR   NZ, ready
    BIT  int16, A              ; Bit 4: Interrupt?
    JR   Z, wait_u8
ready:
; Bei Timeout: U8001 stoppen (reset16=1), Ergebnis aus RAM lesen

;==============================================================
; Schritt 4: U8001 anhalten, Ergebnis aus Shared-RAM lesen
;==============================================================
; Reset setzen
LD A, 1 SHL reset16 OR 1 SHL n_ramen   ; 0x14
LD B, 0
LD C, modadr+1
OUT (C), A

; Seite 0 einblenden, Ergebnis lesen, ausblenden
; (wie Schritt 1)
```

### 8.3 U8001-seitige Adressbelegung und Speicherarchitektur

Der U8001 sieht den EM256-Speicher über seinen eigenen AD-Bus (AD0–AD15) + Segmentleitungen (SN0, SN1). Die 256-KB-Speichermatrix ist in 4 Blöcke aus je 9 RAM-Chips (8 Daten + 1 Parität) organisiert, angesteuert über RAS0–RAS3.

**Wortorganisation (16-Bit-Zugriff):**
- RAS0/RAS1 → unteres Datenbyte (AD0–AD7)
- RAS2/RAS3 → oberes Datenbyte (AD8–AD15)
- Bei Wortzugriffen (B/W=0) werden zwei RAS-Signale gleichzeitig aktiv

**Byteordnung (Big-Endian, Z8001-Konvention):**
- Geradzahlige Adresse (A0=0) → höherwertiges Byte
- Folgende ungerade Adresse (A0=1) → niederwertiges Byte
- Worte werden durch die geradzahlige Adresse ihres MSB adressiert

| U8001-Adresse | Inhalt |
|---------------|--------|
| `0x0000–0x0001` | Reset-Vektor FCW (Flag and Control Word) |
| `0x0002–0x0003` | Reset-Vektor PC (Startadresse im Segment 0) |
| `0x0004–0x0007` | NMI-Vektor (FCW + PC) |
| ab `0x0008` | frei für Anwendungscode |

Der **Z8001 Reset-Vektor** im segmentierten Modus:
- Byte 0–1: FCW (z.B. `0x0000` für Normal Mode ohne Interrupts)
- Byte 2–3: PC (z.B. `0x0008` für Code ab Offset 8)

### 8.4 U8001 anhalten und zurücksetzen

```z80
; Erzwungener Reset (sofort, auch aus laufendem 16-Bit-Mode):
LD A, 1 SHL reset16 OR 1 SHL n_ramen   ; 0x14
LD B, 0
LD C, modadr+1
OUT (C), A

; Kooperativer Stop (hält nach aktuellem Befehl an):
LD A, 1 SHL n_ramen                     ; 0x04, n_stop=0 → Stop aktiv
LD B, 0
LD C, modadr+1
OUT (C), A
; Dann auf TREN warten, dann Reset:
LD A, 1 SHL reset16 OR 1 SHL n_ramen   ; 0x14
OUT (C), A
```

### 8.5 Hinweis zu HALT und Fertigmeldung

Der Z8001-**HALT**-Befehl stoppt die Befehlsausführung, aber der U8001 gibt den Bus **nicht** frei. TREN wird nicht gesetzt, INT16 wird nicht ausgelöst. Für eine einfache Fertigmeldung gibt es zwei Ansätze:

1. **Timeout + Ergebnisprüfung:** U880 wartet eine definierte Zeit, stoppt dann den U8001 per Reset und liest das Ergebnis aus dem Shared-RAM. Wenn der erwartete Wert dort steht, hat der U8001 den Code ausgeführt.

2. **Aktive Signalisierung durch U8001-Code:** Der U8001-Code schreibt über einen I/O-Zugriff auf das Steuer-16-Register A33, setzt dort INT-16 (Bit 4) und löst damit einen Interrupt am U880 aus. Dies erfordert allerdings I/O-Unterstützung auf dem EM256. Alternativ kann über TRQ8/TREN-Handshake umgeschaltet werden.

---

## 9. Kommunikationsprotokoll U880 ↔ U8001

Die Kommunikation nutzt drei Mechanismen:

### 9.1 Shared-DRAM (Datenaustausch)

Beide CPUs greifen auf denselben 256-KB-DRAM zu – **niemals gleichzeitig**. Im 8-Bit-Mode hat der U880 Exklusivzugriff, im 16-Bit-Mode der U8001. Die Umschaltung erfolgt über die Betriebsartensteuerung (siehe Abschnitt 3b).

### 9.2 PIO-Signale (Steuerleitungen)

| Signal | Port | Bit | Richtung | Beschreibung |
|--------|------|-----|----------|--------------|
| `n_trq8` | B | 5 | U880 → U8001 | Transfer-Request: U880 fordert 8-Bit-Mode an (0 = aktiv, → µI am U8001) |
| `tren` | A | 7 | U8001 → U880 | Transfer Enable: U8001 hat Bus freigegeben (= µ0 Ausgang) |
| `int16` | A | 4 | U8001 → U880 | Interrupt: U8001 meldet Ereignis (aus A33 Bit 4) |
| `n_vi` | A | 3 | U8001 → U880 | Vektorinterrupt-Anforderung (low=aktiv, aus Register A34) |
| `pioa_0..2` | A | 0–2 | U8001 → U880 | 3-Bit-Kennung (aus A33 Bits 0–2, frei definierbar) |
| `n_s` | A | 5 | U8001 → U880 | Normal/System-Mode des U8001 |
| `m8_16` | A | 6 | Hardware | Aktueller Betriebsmodus (FF A29) |

### 9.3 Register (Interprozesskommunikation)

| Register | Port | Richtung | Funktion |
|----------|------|----------|----------|
| Status-8 (A36) | `0xAC` | U880 → U8001 | Statusbyte, gelesen bei VI-ack als High-Byte |
| Vektor-8 (A34) | `0xAD` | U880 → U8001 | Interruptvektor, **Schreiben löst VI aus** |
| Status-16 (A35) | `0xAE` | U8001 → U880 | Statusbyte, vom U880 lesbar |
| Steuer-16 (A33) | – | U8001 intern | Segmentmode, INT-16, Kennung, Debug |

### 9.4 Empfohlene Ablaufsequenz (16-Bit-Betrieb)

```
1. U880: Code in Shared-DRAM laden (8-Bit-Mode, RAMON/RAMOFF)
2. U880: Reset-16 aufheben → U8001 startet (16-Bit-Mode)
3. U8001: Arbeitet autonom im EM256-Speicher
4. U8001: Schreibt Ergebnis, setzt INT-16 oder Kennung in A33
5. U880: Erkennt INT16/TREN über PIO-A Polling oder Interrupt
6. U880: Fordert 8-Bit-Mode an (TRQ8 oder Reset-16)
7. U880: Liest Ergebnis aus Shared-RAM (RAMON/RAMOFF)
```

---

## 10. Paritätsfehler-Behandlung

Der EM256-RAM hat Paritätsbits (9. Chip pro Block). Ein Paritätsfehler:
1. Setzt `n_pe` (PIO Port B Bit 7) auf 0
2. Löst einen Interrupt am U880 aus (über PIO Port B Interruptvektor `ivpar`)
3. Im 16-Bit-Mode: löst zusätzlich NMI am U8001 aus (PER → NMI=0 auf Speicherkarte)
4. LED V1 auf der Speicherkarte leuchtet

**Paritätsfehler-Latch zurücksetzen (BIOS-Methode):**
```z80
IN  A, (modadr+1)      ; Aktuellen Port-B-Zustand lesen
SET prreset, A          ; Bit 6 setzen
OUT (modadr+1), A       ; Flanke ↑ (Reset-Impuls)
RES prreset, A          ; Bit 6 löschen
OUT (modadr+1), A       ; Flanke ↓ → Latch zurückgesetzt
```

> **Hinweis:** Die BIOS-ISR nutzt `IN A, (modadr+1)` / `OUT (modadr+1), A` (= `IN/OUT (n), A`). Für Eigenprogramme besser `IN A, (C)` / `OUT (C), A` mit B=0, C=modadr+1 verwenden.

> **Quelle:** `src/bc_a5120/biosrem.mac` Z. 117–127 (`parrou`-ISR)

---

## 11. Kapazitätsvarianten

Das BIOS erkennt beim Kaltstart die tatsächliche Bestückung der Karte und passt den DPB entsprechend an:

| Bestückung | Kapazität | Erkennung |
|------------|-----------|-----------|
| Voll (4 Segmente) | 256 KB | Kennung nur in Segment 0 |
| Halb | 128 KB | Kennung auch in Segment 2 (Track 32) |
| Viertel | 64 KB | Kennung auch in Segment 1 (Track 16) |

> **Quelle:** `src/bc_a5120/biosremc.mac` Z. 155–192

---

## 12. RAM-Floppy DPB (Disk Parameter Block)

Wenn der U8001 nicht genutzt wird und die Karte als RAM-Floppy dient:

```
dpbem (aus biosrem.mac):
  Recs/Track:    32    (32 × 128 = 4 KB pro „Spur"/Page)
  Block-Shift:   3
  Block-Mask:    7     → 1-KB-BDOS-Blöcke
  Extent-Mask:   0
  Disk-Size:     255   (256 × 1 KB = 256 KB)
  Dir-Count:     63    (64 Verzeichniseinträge)
  Alloc0:        0xC0
  Alloc1:        0x00
  Check-Size:    0     (kein Check-Vektor → kein Schreibschutz-Check)
  Offset:        0     (keine Systemspuren)
  Disk-Type:     0x80  (kein physisches Laufwerk)
```

---

## 13. Taktgenerator und Reset-Logik

Der Taktgenerator basiert auf dem Schaltkreis **DS 8127 (A55)** mit 16-MHz-Quarz:
- Grundtakt: 16 MHz (extern, Quarz an X1/X2)
- Systemtakt: 4 MHz (Teilung Faktor 4, Ausgang ZCK)
- RESET-Steuerung: Das Signal **RESET-16** (PIO Port B Bit 4) wird über Gatter A31 an den RESET-IN-Eingang des DS 8127 geführt. Der DS 8127 synchronisiert das Reset-Signal mit der steigenden Flanke von ZCK und gibt RESET-OUT an den U8001.
- Im Einschaltzustand: PIO-Ausgänge hochohmig → Pullup R4:2 → RESET-16 = high → U8001 bleibt im Reset

> **Quelle:** `16bitTest/docs/Auszug_Handbuch.md` Abschnitt III.1.2

---

## 14. Eigenrefreshgenerator

Die Speicherkarte besitzt einen eigenen RFSH-Zähler, unabhängig von den Refresh-Adressen der CPUs. Dies garantiert vollständigen Refresh auch beim Betriebsartenwechsel.

- Im Normalbetrieb: Refresh durch aktive CPU (U880 oder U8001)
- Bei Timeout des Zählers (Signal RU): Eigenrefreshgenerator auf der Steuerkarte erzeugt Refresh-Impulse mit doppelter Taktlänge
- Während Eigenrefresh: **Beide** CPUs erhalten WAIT (WAIT für U880, WAIT-16 für U8001)

> **Quelle:** `16bitTest/docs/Auszug_Handbuch.md` Abschnitte III.1.11 und III.2.6

---

## 15. Konstanten-Übersicht

```z80
; Aus bios.mac (nur gültig wenn em256 = 1):
em256adr  EQU 4000h   ; U880-Fensteradresse des eingeblendeten RAM
modadr    EQU 0A8h    ; Basisadresse EM256 (PIO + Register + Attributspeicher)

; I/O-Portadressen:
; modadr+0  = 0xA8 : PIO Port A Daten (Lesen: Statuseingänge)
; modadr+1  = 0xA9 : PIO Port B Daten (Lesen/Schreiben: Steuerausgänge + n_pe)
; modadr+2  = 0xAA : PIO Port A Steuerregister
; modadr+3  = 0xAB : PIO Port B Steuerregister
; modadr+4  = 0xAC : Status-8-Register (A36) schreiben
; modadr+5  = 0xAD : Vektor-8-Register (A34) schreiben → löst VI aus!
; modadr+6  = 0xAE : Status-16-Register (A35) lesen
; modadr+7  = 0xAF : Attributspeicher (16×4-RAM, A22) lesen/schreiben

; PIO Port A (modadr+0 = 0xA8, alle Eingabe):
pioa_0    EQU 0       ; Kennung Bit 0 (aus A33)
pioa_1    EQU 1       ; Kennung Bit 1 (aus A33)
pioa_2    EQU 2       ; Kennung Bit 2 (aus A33)
n_vi      EQU 3       ; Vektorinterrupt-Status (neg., aus A34)
int16     EQU 4       ; Interrupt U8001→U880 (aus A33 Bit 4)
n_s       EQU 5       ; Normal(1)/System(0)-Mode
m8_16     EQU 6       ; 8-Bit(1)/16-Bit(0)-Mode (FF A29)
tren      EQU 7       ; Transfer Enable (= µ0 Ausgang U8001)

; PIO Port B (modadr+1 = 0xA9, Bits 0–6 Ausgabe, Bit 7 Eingabe):
sg0p      EQU 0       ; Segment-Bit 0 (für U880-Zugriff)
sg1b      EQU 1       ; Segment-Bit 1
n_ramen   EQU 2       ; RAM-Enable (neg.)
n_stop    EQU 3       ; U8001-Stop (neg.)
reset16   EQU 4       ; U8001-Reset (1 = in Reset, setzt FF A29)
n_trq8    EQU 5       ; Transfer-Request U880→U8001 (neg., → µI)
prreset   EQU 6       ; Paritätsfehler-Latch-Reset (Flanke)
n_pe      EQU 7       ; Paritätsfehler (neg., Eingabe)

; Attributspeicher (modadr+7 = 0xAF, Subadresse in B[7:4]):
n_pagen   EQU 0       ; Page enable (neg.) – BIOS-Konvention; Handbuch: PEN positiv
n_write   EQU 1       ; Write enable (neg.) – BIOS-Konvention; Handbuch: WE positiv
; Bits 2-3: /A14-8 und /A15-8 (neg. Adressbits für physische Adresse)
; B[7:4] = Subadresse = 4KB-Page im Z80-Adressraum (0–15)

; Interruptvektor (aus bios.mac):
ivpar     EQU intvsy+00h  ; Paritätsfehler EM256-RAM

; Häufig benötigte Port-B-Zustände:
; Idle (U8001 Reset, RAM aus): 1 SHL reset16 OR 1 SHL n_ramen = 0x14
; RAMON (U8001 Reset, RAM ein): 1 SHL reset16 = 0x10
; RUN (U8001 läuft, RAM aus): 1 SHL n_stop OR 1 SHL n_ramen = 0x0C
```

---

## 16. Quellcode-Referenzen

| Datei | Inhalt |
|-------|--------|
| `src/bc_a5120/bios.mac` Z. 223–237 | Konfigurationsparameter (`em256`, `em256adr`, `modadr`) |
| `src/bc_a5120/bios.mac` Z. 1072 | Interruptvektor `ivpar` |
| `src/bc_a5120/bios.mac` Z. 1500–1539 | Bedingte Includes für `biosrem.mac` / `biosremc.mac` |
| `src/bc_a5120/biosrem.mac` Z. 1–55 | `wrramf`, `rdramf` (RAM-Floppy I/O) |
| `src/bc_a5120/biosrem.mac` Z. 68–113 | `ramon` – RAM einblenden, Adresse berechnen |
| `src/bc_a5120/biosrem.mac` Z. 115–127 | `ramoff`, `parrou` (ISR) |
| `src/bc_a5120/biosrem.mac` Z. 134–149 | DPB `dpbem` |
| `src/bc_a5120/biosremc.mac` Z. 1–52 | Bit-Definitionen, RAM-Konfigurationskommentar |
| `src/bc_a5120/biosremc.mac` Z. 55–110 | PIO-Initialisierung, Kaltstart-Code (`emina`) |
| `src/bc_a5120/biosremc.mac` Z. 111–192 | Präsenzerkennung, Kapazitätserkennung |
| `src/bc_a5120/biosremc.mac` Z. 196–223 | PIO-Initialisierungsdaten, `tstkng`, Kennung |
| `16bitTest/docs/Auszug_Handbuch.md` | Handbuch A 5120.16: Blockschaltbild, Taktgenerator, Statusdecoder, Segmentweiche, Attributspeicher, Steuerregister, I/O-Decoder, PIO, Betriebsartensteuerung, Speichermatrix, Ablaufsteuerung, Refresh, Paritätssteuerung |
| `16bitTest/docs/rfe83-10-629ff-...txt` | TH Karl-Marx-Stadt: 16-Bit-ZRE-Karte für K1520 mit Z8001, Hintergrundinformation zur Z8001-Architektur, K1520-Signalgenerierung, RETI-Sequenz für U880-kompatible PIOs |
| `16bitTest/src/em256tst.mac` | Testprogramm: EM256-Erkennung, PIO-Diagnose, U8001-Codeausführung |
