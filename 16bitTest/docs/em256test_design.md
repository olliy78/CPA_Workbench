# EM256 Comprehensive Test Program – Design Document

**Version:** 1.1  
**Datum:** 2026-04-07  
**Autor:** Olaf Krieger  
**Zielplattform:** BC A5120 mit EM256-Karte (U8001, 256 KB DRAM)

---

## 1. Überblick

Umfassendes Testprogramm für die EM256 16-Bit-Erweiterungskarte.
Prüft alle Hardwarekomponenten in fünf Gruppen (A–E) mit kompakter, übersichtlicher
Konsolenausgabe. Ein Z80-Masterprogramm (CP/M .COM) steuert den gesamten Ablauf und
lädt bei Bedarf Z8001-Firmware in das Shared-DRAM, die der U8001 autonom ausführt.

### 1.1 Anforderungen

- Alle Tests laufen als **einzelne .COM-Datei** unter CP/A (CP/M 2.2)
- **Gruppenweise Ausführung** mit Seitenpause nach ~10 Tests
- **Kompakte Ausgabe:** Status rechts ausgerichtet: `[OK]`, `[FEHLER]`, `[INFO]`
- Bei Fehler: Detailzeile(n) mit Soll/Ist-Werten
- **Kapazitätserkennung:** 64/128/256 KB automatisch bestimmen
- **Z8001-Firmware:** Als DB-Blöcke im Z80-Programm, erzeugt durch Python-Cross-Assembler

---

## 2. Architektur

```
┌──────────────────────────────┐
│  Z80 Masterprogramm (CP/M)  │
│  - Testlogik & Ausgabe       │
│  - PIO-Steuerung             │
│  - RAM-Fenster-Zugriffe      │
│  - Z8001-Code laden          │
│  - Ergebnis auswerten        │
└───────┬──────────────────────┘
        │ PIO Port B + Attributspeicher
        ▼
┌──────────────────────────────┐
│  EM256 Hardware              │
│  - PIO U855D (A32)           │
│  - 16×4 Attributspeicher     │
│  - Steuerregister A33–A36    │
│  - Segmentweiche A42         │
│  - 256 KB DRAM               │
│  - U8001 CPU (4 MHz)         │
└──────────────────────────────┘
        │ Shared DRAM (Mailbox ab Offset 0x0010)
        ▼
┌──────────────────────────────┐
│  U8001-Firmware (Z8001-Code) │
│  - Reset-Vektor @ 0x0000     │
│  - Testcode ab 0x0040        │
│  - Ergebnis → Mailbox        │
│  - JR T,$ (wartet auf µI)    │
└──────────────────────────────┘
```

### 2.1 Mailbox-Protokoll (Shared-DRAM)

Die Kommunikation zwischen Z80 und U8001 erfolgt über eine feste Speicherstruktur
am Anfang von Segment 0 (= Z80-Fenster `0x4000` bei Page 0):

| Offset | Größe | Inhalt | Beschreibung |
|--------|-------|--------|--------------|
| 0x0000 | 8 | Reset-Vektor | FCW + PC (segmentiert, Z8001) |
| 0x0008 | 2 | CMD | Kommando-Code (vom Z80 geschrieben) |
| 0x000A | 2 | PARAM1 | Parameter 1 |
| 0x000C | 2 | PARAM2 | Parameter 2 |
| 0x000E | 2 | PARAM3 | Parameter 3 |
| 0x0010 | 2 | STATUS | Ergebnisstatus (vom U8001 geschrieben) |
| 0x0012 | 2 | RESULT1 | Ergebniswort 1 |
| 0x0014 | 2 | RESULT2 | Ergebniswort 2 |
| 0x0016 | 2 | RESULT3 | Ergebniswort 3 |
| 0x0018 | 2 | RESULT4 | Ergebniswort 4 |
| 0x001A | 38 | (reserviert) | |
| 0x0040 | ... | CODE | U8001-Programmcode ab hier |

> **Hinweis:** Fehlerdetails (Adresse, Soll/Ist) werden in RESULT1–RESULT3 gemeldet,
> nicht in separaten Feldern. Die Firmware schreibt: RESULT1=Soll, RESULT2=Ist,
> RESULT3=Fehleradresse.

**STATUS-Codes** (vom U8001 geschrieben):

| Wert | Bedeutung |
|------|-----------|
| 0x0000 | Nicht gestartet / läuft noch |
| 0x0001 | OK – Test bestanden |
| 0x0002 | FEHLER – Test fehlgeschlagen (Details in RESULTx) |
| 0x00FF | Bereit (Firmware initialisiert, wartet auf Kommando) |

**Ablauf:**
1. Z80 schreibt Z8001-Code (Reset-Vektor + Firmware) in Seite 0
2. Z80 schreibt CMD + Parameter in Mailbox
3. Z80 gibt U8001 frei (reset16=0, n_stop=1, n_trq8=1)
4. U8001 startet, liest CMD, führt Test aus
5. U8001 schreibt STATUS + RESULTx in Mailbox
6. U8001 geht in JR T,$ Schleife (reagiert auf µI)
7. Z80 fordert Bus an (n_trq8=0), wartet auf TREN
8. Z80 liest STATUS + Ergebnisse aus Mailbox

---

## 3. Ausgabeformat

### 3.1 Gruppenüberschrift

```
=== Gruppe A: PIO-Tests ===
```

### 3.2 Einzeltest

```
A1 PIO-A BIOS-Zustand lesen             [OK]
A2 PIO-B Schreiben/Lesen 0x14           [OK]
A3 PIO-B Schreiben/Lesen 0x10           [OK]
A4 PIO-B Reinit (OTIR)                  [OK]
A5 PIO-B nach Reinit lesen              [FEHLER]
   Soll: 0x94  Ist: 0xD7
```

**Formatierung:**
- Spalte 1–2: Testkennung (Gruppe + Nummer)
- Spalte 4–40: Testbeschreibung (max. 37 Zeichen)
- Spalte 42–49: Status, rechts ausgerichtet auf Spalte 49
- Ergibt 49 Zeichen pro Zeile (passt in 80-Spalten-Terminal)
- Bei FEHLER: eine oder mehrere Detailzeilen eingerückt (3 Leerzeichen)

### 3.3 Gruppenzusammenfassung

```
--- A: 8/9 bestanden, 1 Fehler ---
```

### 3.4 Gesamtzusammenfassung

```
=========================================
Ergebnis: 42/45 Tests bestanden
Fehler in: A5 B3 C1
Kapazitaet: 256 KB (4 Segmente)
=========================================
```

### 3.5 Seitenpause

Nach jeweils ~20 Ausgabezeilen (PAGELEN=23 abzgl. Überschriften):

```
--- Taste druecken ---
```

Per BDOS 6 (DCIO, E=0xFF) blockierend warten, Zeile danach löschen (CR + Leerzeichen + CR).

---

## 4. Testgruppen

### Gruppe A: PIO- und Basishardware-Tests (9 Tests)

Testet die PIO-Konfiguration und grundlegende I/O-Zugriffe. Keine RAM-Zugriffe nötig.

| Nr  | Test | Methode | Erwartung |
|-----|------|---------|-----------|
| A1 | PIO-A BIOS-Zustand | IN A,(C) auf 0xA8 | Wert anzeigen [INFO] |
| A2 | PIO-B BIOS-Zustand | IN A,(C) auf 0xA9 | Wert anzeigen [INFO] |
| A3 | PIO-B Write 0x14 | OUT (C),A=0x14, IN A,(C) | Read = 0x94 (Bit7=PE=1) |
| A4 | PIO-B Write 0x10 | OUT (C),A=0x10, IN A,(C) | Read = 0x90 |
| A5 | PIO-B Write 0x14 | OUT (C),A=0x14, IN A,(C) | Read = 0x94 |
| A6 | PIO Reinit (OTIR) | 3 Bytes Port A + 3 Bytes Port B | Kein Fehler |
| A7 | PIO-B nach Reinit | OUT (C),A=0x14, IN A,(C) | Read = 0x94 |
| A8 | PIO-B Toggle | Write 0x10, read, write 0x14, read | 0x90, 0x94 |
| A9 | Parity-Latch Reset | Flanke auf prreset, Bit 7 prüfen | n_pe = 1 (kein Fehler) |

> Alle PIO-Datenportzugriffe über OUT (C),A / IN A,(C) mit B=0.

### Gruppe B: Speicherfenster- und Paging-Tests (10 Tests)

Testet den Attributspeicher (16×4-RAM) und die RAM-Einblendung aller Segmente/Seiten.

| Nr  | Test | Methode | Erwartung |
|-----|------|---------|-----------|
| B1 | EM256 Erkennung | BIOS-Methode (Write A55A, Check Z80-RAM) | EM256 vorhanden |
| B2 | Seite 0 R/W | Ramon S0, Write/Read Muster 0xA55A | Muster korrekt |
| B3 | Seite 0 Isolation | Ramon S0-Write 0xBEEF, Ramoff, Z80-Read | Z80-RAM unverändert (=0) |
| B4 | Seg 0: 4 Seiten | 4× Write (0x11/0x22/0x33/0x44), Rücklesen | 4 verschiedene Werte |
| B5 | Seg 1 R/W | Ramon Seg 1, Write/Read 0x5A5A | Seg 1 erreichbar |
| B6 | Seg 2 R/W | Ramon Seg 2, Write/Read 0x6666 | Seg 2 erreichbar |
| B7 | Seg 3 R/W | Ramon Seg 3, Write/Read 0x7777 | Seg 3 erreichbar |
| B8 | Kapazitätserkennung | Alias-Prüfung (Seg 1/2/3 vs. Seg 0) | 64/128/256 KB [INFO] |
| B9 | Seg-Isolation 0↔1 | 0xAAAA in Seg 0, 0x5555 in Seg 1, Seg 0 prüfen | Seg 0 = 0xAAAA |
| B10 | Walking-1 RAM-Test (Z80) | 8 Bitmuster (0x01–0x80) Write/Read | Alle Bits schaltbar |

> **Nicht implementiert (v1.0):** Attributspeicher-Reset-Test und Schreibschutz-Test
> (ehemals B10–B12). Diese erfordern weitere Klärung der 16×4-RAM-Semantik.

**Kapazitätserkennung (B8) – Algorithmus:**

```
1. Seg 0, Seite 0: Muster 0xBEEF schreiben
2. Seg 1 einblenden: gleiche physische Adresse lesen
   → 0xBEEF? → Seg 0 = Seg 1 (Alias) → max 64 KB
3. Seg 2 einblenden: gleiche physische Adresse lesen
   → 0xBEEF? → Seg 0 = Seg 2 (Alias) → max 128 KB
4. Seg 3 einblenden: gleiche physische Adresse lesen
   → 0xBEEF? → Seg 0 = Seg 3 → max 192 KB (unwahrscheinlich)
5. Kein Alias → 256 KB
```

### Gruppe C: Kooperative CPU-Tests (8 Tests)

Testet die U8001-Ausführung mit Z80-generierten Z8001-Firmware-Blöcken.
Jeder Test lädt anderen U8001-Code, startet ihn und prüft das Ergebnis im Shared-RAM.

| Nr  | Test | U8001-Code | Erwartung |
|-----|------|------------|-----------|
| C1 | Addition 1234+5678 | LD R1,#1234; ADD R1,#5678; LD @R2,R1 | RESULT1 = 0x68AC |
| C2 | Subtraktion 8000-0001 | LD R1,#8000; SUB R1,#0001; LD @R2,R1 | RESULT1 = 0x7FFF |
| C3 | Logik AND/OR/XOR | AND, OR, XOR Kette → 0x1234 | RESULT1 = 0x1234 |
| C4 | Speicher-R/W | 5 Muster (A55A/5AA5/FFFF/0000/Cross) | STATUS = OK |
| C5 | Schleifentest (256×INC) | R1=0, 256× INC R1 | RESULT1 = 0x0100 |
| C6 | Stack-Test | PUSH 0xBEEF, PUSH 0xCAFE, POP×2 (LIFO) | RESULT1 = 0xBEEF |
| C7 | 32-Bit-Addition | ADDL 0x00010000 + 0x0000FFFF | RES1=0x0001, RES2=0xFFFF |
| C8 | Byte-Operationen | CLR R1; LDB RH1,#75; LDB RL1,#10 | RESULT1 = 0x7510 |

**Allgemeiner Ablauf pro C-Test:**

```z80
; Z80-seitig:
CALL RAMON_S0
; Z8K-Code + Mailbox-CMD schreiben
LD HL, Cx_CODE
LD DE, EM256ADR
LD BC, Cx_CODE_LEN
LDIR
; Ergebnis-Bereich nullen
XOR A
LD HL, EM256ADR + 10h
LD (HL), A
LD DE, EM256ADR + 11h
LD BC, 15
LDIR
CALL RAMOFF
; U8001 starten
CALL START_U8000
CALL WAIT_READY       ; TRQ8 → TREN pollen
; Falls Timeout → FEHLER
CALL STOP_U8000
; Ergebnis lesen
CALL RAMON_S0
LD A, (EM256ADR + 10h) ; STATUS high
LD B, A
LD A, (EM256ADR + 11h) ; STATUS low
; ... prüfen ...
CALL RAMOFF
```

### Gruppe D: Autonomer DRAM-Test (U8001) (1 Test)

Der U8001 testet selbstständig den EM256-Speicher in Segment 0.
Das Z80-Programm lädt die Testfirmware, startet den U8001 und wartet auf das Ergebnis
mit verlängertem Timeout (~16 Sekunden).

| Nr  | Test | U8001-Firmware | Erwartung |
|-----|------|----------------|----------|
| D1 | Seg 0: March-C | 5-Phasen March-C, 0x0100–0xFFFE wortweise | STATUS = OK |

> **Nicht implementiert (v1.0):** D2–D4 (Segmente 1–3) und D5 (Adressleitung-Test).
> Die Segment-Umschaltung vom U8001 aus erfordert Klärung der A33-Programmierung
> (siehe §5.2). Für den Z80-seitigen Segmentzugriff werden die Segmente in Gruppe B
> bereits getestet.

**March-C-Algorithmus (auf U8001):**

```
; Testet Speicherbereich 0x0100 bis 0xFFFE (wortweise)
; Phase 1: Aufwärts alle Worte mit 0x0000 füllen
; Phase 2: Aufwärts jedes Wort lesen (soll 0x0000), überschreiben mit 0xFFFF
; Phase 3: Aufwärts lesen 0xFFFF (verifiziert Phase-2-Schreiben)
; Phase 4: Abwärts lesen 0xFFFF, schreiben 0x0000
; Phase 5: Abwärts lesen 0x0000 (verifiziert Phase-4-Schreiben)
; Code+Mailbox (0x0000-0x00FF) wird übersprungen!
```

Der U8001-Firmware-Block ist größer als bei Gruppe C (~226 Bytes Z8001-Code)
und enthält die gesamte March-C-Logik.

**Timeout:** Die DRAM-Tests dauern länger (je Segment ca. 0.5–1 Sek. bei 4 MHz).
Der Z80 verwendet `WAIT_READY_LONG` mit erweitertem Timeout (~16 Sekunden).

### Gruppe E: Paritätstests (2 Tests)

Testet die Paritätsfehler-Erkennung und das Latch. Diese Tests werden zuletzt
ausgeführt.

| Nr  | Test | Methode | Erwartung |
|-----|------|---------|----------|
| E1 | Parity-Latch lesen | PIO-A Bit 7 (n_pe) | n_pe = 1 (kein Fehler) |
| E2 | Parity-Latch Reset | PRRESET-Flanke auf PIO-B, PIO-A Bit 7 prüfen | n_pe = 1 nach Reset |

> **Nicht implementiert (v1.0):** E3 (Paritätsfehler-Provokation). Zu riskant:
> Bei falschen Bits im Paritäts-RAM könnte der Latch dauerhaft gesetzt bleiben.
> Nur implementieren wenn eine sichere Methode über U8001-Byte-Schreiben
> mit absichtlich falschem Paritätsbit verifiziert wurde.

---

## 5. U8001-Firmware-Design

### 5.1 Gemeinsamer Startcode (alle Firmwares)

Jede U8001-Firmware beginnt mit dem segmentierten Reset-Vektor und einem
gemeinsamen Prolog:

```z8001
; Offset 0x0000: Z8001 Reset-Vektor (segmentierter Modus)
    DW  0x0000          ; Reserviert
    DW  0x0000          ; FCW = Normal Mode, keine Interrupts
    DW  0x0000          ; PC Segment = 0
    DW  0x0040          ; PC Offset = 0x0040 (Code ab hier)

; Offset 0x0008-0x003F: Mailbox (siehe Abschnitt 2.1)

; Offset 0x0040: Firmware-Einstieg
    LD  R15, #0xFFF0    ; Stack-Pointer initialisieren (Ende Segment 0)
    ; ... testspezifischer Code ...
    ; Ergebnis in Mailbox schreiben:
    LD  R1, #0x0001     ; STATUS = OK
    LD  R2, #0x0010     ; Mailbox-Offset STATUS
    LD  @R2, R1
    ; Endlosschleife (wartet auf µI):
    JR  T, $            ; E8 FE
```

### 5.2 Segment-Umschaltung (für Gruppe D)

Im Grundzustand (nach Reset) ist die Segmentweiche in Mode 0 mit AD5\*=AD6\*=AD7\*=0,
d.h. alle Zugriffe gehen in Segment 0. Für Zugriff auf andere Segmente muss der
U8001 über einen Special-I/O-Zugriff das Steuer-16-Register A33 programmieren.

Allerdings ist die genaue I/O-Adresse und Methode für A33 aus dem Handbuch zu
ermitteln. Der U8001 nutzt dafür den **RESET OUT**-Befehl beim Einschalten bzw.
schreibt über seinen AD-Bus Daten in Register A33.

> **Offene Frage:** Wie genau schreibt der U8001 in Register A33? Das muss aus dem
> Handbuch oder durch Experiment geklärt werden. Für den ersten Prototyp testen
> wir nur **Segment 0** (Mode 0, Grundstellung) und den Z80-seitigen Segmentzugriff.

### 5.3 DRAM-Test-Firmware (Gruppe D – March-C)

Pseudo-Code für den March-C-Test eines Segments:

```z8001
; R1 = Testmuster (0x0000 oder 0xFFFF)
; R2 = aktuelle Adresse
; R3 = End-Adresse
; R4 = gelesener Wert
; R5 = Mailbox-Basis (0x0010)
; R15 = SP

MARCH_C:
    LD  R2, #0x0100         ; Start (hinter Code-Bereich)
    LD  R3, #0xFFFE         ; Ende (letzte Wortadresse)
    LD  R1, #0x0000         ; Muster Phase 1

; Phase 1: Aufwärts mit 0x0000 füllen
P1_LOOP:
    LD  @R2, R1
    INC R2, #2
    CP  R2, R3
    JR  ULE, P1_LOOP

; Phase 2: Aufwärts: 0x0000 lesen, 0xFFFF schreiben
    LD  R2, #0x0100
P2_LOOP:
    LD  R4, @R2
    CP  R4, R1              ; Sollte 0x0000 sein
    JR  NZ, FAIL
    LD  R1, #0xFFFF
    LD  @R2, R1
    LD  R1, #0x0000         ; Vergleichswert für nächste Zelle
    INC R2, #2
    CP  R2, R3
    JR  ULE, P2_LOOP

; Phase 3: Aufwärts: 0xFFFF lesen
    LD  R2, #0x0100
    LD  R1, #0xFFFF
P3_LOOP:
    LD  R4, @R2
    CP  R4, R1
    JR  NZ, FAIL
    INC R2, #2
    CP  R2, R3
    JR  ULE, P3_LOOP

; Phase 4: Abwärts: 0xFFFF lesen, 0x0000 schreiben
    LD  R2, R3              ; Ende
P4_LOOP:
    LD  R4, @R2
    CP  R4, R1              ; Sollte 0xFFFF sein
    JR  NZ, FAIL
    LD  R1, #0x0000
    LD  @R2, R1
    LD  R1, #0xFFFF         ; Vergleichswert
    DEC R2, #2
    CP  R2, R3              ; Start-Adresse (R3)
    JR  UGE, P4_LOOP

; Phase 5: Abwärts: 0x0000 lesen
    LD  R2, R4              ; Ende
    LD  R1, #0x0000
P5_LOOP:
    LD  R5, @R2
    CP  R5, R1
    JR  NZ, FAIL
    DEC R2, #2
    CP  R2, R3
    JR  UGE, P5_LOOP

; Erfolg
    LD  R1, #0x0001         ; STATUS = OK
    LD  R5, #0x0010
    LD  @R5, R1
    JR  T, $                ; Fertig

FAIL:
    ; R2 = Fehleradresse, R4 = gelesener Wert, R1 = erwarteter Wert
    LD  R5, #0x0010
    LD  R6, #0x0002         ; STATUS = FEHLER
    LD  @R5, R6
    INC R5, #2
    LD  @R5, R1             ; RESULT1 = Soll-Wert
    INC R5, #2
    LD  @R5, R4             ; RESULT2 = Ist-Wert
    INC R5, #2
    LD  @R5, R2             ; RESULT3 = Fehleradresse
    JR  T, $
```

---

## 6. Programmstruktur (Z80-Seite)

### 6.1 Dateistruktur

```
16bitTest/
├── src/
│   ├── em256ful.mac         ← Volltest (Z80-Assembler, M80-Syntax, 8.3-konform)
│   └── em256tst.mac         ← Original-Test (bestehend, nur Grundfunktionstest)
├── z8001/
│   ├── z8001asm.py          ← Z8001 Cross-Assembler (Python)
│   ├── fw_add.s / .inc      ← C1: Additionstest (94 Bytes)
│   ├── fw_sub.s / .inc      ← C2: Subtraktionstest (94 Bytes)
│   ├── fw_logic.s / .inc    ← C3: Logiktest (106 Bytes)
│   ├── fw_memrw.s / .inc    ← C4: Speicher-R/W (182 Bytes)
│   ├── fw_loop.s / .inc     ← C5: Schleifentest (104 Bytes)
│   ├── fw_stack.s / .inc    ← C6: Stacktest (134 Bytes)
│   ├── fw_add32.s / .inc    ← C7: 32-Bit-Arithmetik (104 Bytes)
│   ├── fw_byte.s / .inc     ← C8: Byte-Operationen (104 Bytes)
│   └── fw_march.s / .inc    ← D1: March-C DRAM-Test (226 Bytes)
├── build.py                 ← Build-Script (z8001asm + Präprozessor + M80 + LINKMT)
├── build/
│   └── em256ful.com         ← Fertiges CP/M-Programm (5888 Bytes)
└── docs/
    └── em256test_design.md  ← Dieses Dokument
```

### 6.2 Build-Prozess

Der Build erfolgt über `build.py` (Standard: `em256ful`, alternativ `em256tst`):

```
python3 16bitTest/build.py              # baut em256ful.com (Standard)
python3 16bitTest/build.py em256tst      # baut em256tst.com (Original)
```

**Ablauf für em256ful:**
```
1. z8001asm.py assembliert jede .s-Datei → .bin + .inc (DB-Zeilen, M80-Syntax)
2. build.py Präprozessor ersetzt ;%INCLUDE-Direktiven in em256ful.mac
   durch den Inhalt der .inc-Dateien
3. CRLF-Konvertierung der vorverarbeiteten .mac-Datei
4. M80 assembliert → .ERL
5. LINKMT linkt → .COM (Ladeadresse 0x100)
6. Kopiert .COM nach additions/bc_a5120/
```

> **Hinweis:** M80 hat keine INCLUDE/MACLIB-Unterstützung für Roh-DB-Blöcke.
> Daher verwendet em256ful.mac `;%INCLUDE datei.inc`-Markerkommentare,
> die der build.py-Präprozessor vor der M80-Assemblierung textuell ersetzt.

### 6.3 Z80-Codestruktur

```z80
; em256full.mac - Hauptprogramm
;
; Sektionen:
;   1. Konstanten & Equates
;   2. Hauptprogramm (Testschleife pro Gruppe)
;   3. Testgruppe A: PIO-Tests
;   4. Testgruppe B: Speicherfenster-Tests
;   5. Testgruppe C: Kooperative CPU-Tests
;   6. Testgruppe D: Autonome DRAM-Tests
;   7. Testgruppe E: Paritätstests
;   8. Hilfsfunktionen (PUTS, PUTHEX, RAMON, RAMOFF, etc.)
;   9. Ausgabefunktionen (PRINT_OK, PRINT_FAIL, PRINT_INFO, etc.)
;  10. U8001-Steuerung (START/STOP/WAIT)
;  11. Z8001-Code-Blöcke (DB)
;  12. Meldungstexte
;  13. Variablen & Stack
```

### 6.4 Hilfsroutinen

| Routine | Funktion |
|---------|----------|
| `PUTS` | String ausgeben mit Seitenpause (LF-Zählung) |
| `PUTHEX` | Byte als HEX ausgeben (2 Zeichen) |
| `PUTHEX16` | Wort als HEX ausgeben (4 Zeichen, Big-Endian-Reihenfolge) |
| `PRINT_OK` | `[OK]` rechts ausgerichtet ausgeben + CRLF |
| `PRINT_FAIL` | `[FEHLER]` rechts ausgerichtet + CRLF |
| `PRINT_INFO` | `[INFO]` rechts ausgerichtet + CRLF |
| `PRINT_DETAIL_HEX` | Eingerückte Detailzeile mit Soll/Ist (Byte) |
| `PRINT_RES1_DETAIL` | Zeigt RESULT1 als Detail (Word) |
| `PRINT_MARCH_DETAIL` | Zeigt March-Fehlerdetails (Adresse/Soll/Ist) |
| `PRINT_TIMEOUT` | `[TIMEOUT]` ausgeben + CRLF |
| `PUTDEC` | Byte als Dezimalzahl (ohne Vornullen) |
| `PUTC` | Einzelnes Zeichen ausgeben |
| `PAGE_PAUSE` | Warten auf Tastendruck bei voller Seite |
| `RAMON_S0` | Segment 0, Seite 0 einblenden |
| `RAMON_S0_P1..P3` | Segment 0, Seiten 1–3 einblenden |
| `RAMON_S1..S3` | Segmente 1–3, Seite 0 einblenden |
| `RAMOFF` | RAM ausblenden |
| `INIT_PIO` | PIO initialisieren (OTIR, wie BIOS) |
| `DETECT_EM256` | EM256-Erkennung (atomar, setzt EM256_OK-Flag) |
| `DETECT_CAPACITY` | Segmentzahl erkennen (Alias-Prüfung, → A) |
| `START_U8000` | U8001 aus Reset freigeben (PIOB_RUN) |
| `STOP_U8000` | U8001 in Reset setzen (PIOB_IDLE) |
| `WAIT_READY` | TRQ8 → TREN pollen (kurzer Timeout ~2s) |
| `WAIT_READY_LONG` | TRQ8 → TREN pollen (langer Timeout ~16s) |
| `READ_MAILBOX` | Mailbox-Ergebnisse in lokalen Puffer lesen |
| `CHECK_RESULT1` | RESULT1 (Big-Endian) mit DE vergleichen |
| `RUN_FW_TEST` | Gesamtablauf: LDIR → starten → warten → lesen |
| `RUN_FW_TEST_LONG` | Wie RUN_FW_TEST mit langem Timeout |
| `COUNT_PASS` | Bestanden-Zähler inkrementieren |
| `COUNT_INFO` | Info-Zähler inkrementieren |
| `COUNT_FAIL_xx` | Fehler-Zähler + Test-ID in Fehlerliste |
| `PRINT_GRP_SUMMARY` | Gruppenresultat ausgeben |

### 6.5 Statistik

```z80
; Zähler
PASS_CNT:   DB  0       ; Bestandene Tests
FAIL_CNT:   DB  0       ; Fehlgeschlagene Tests
INFO_CNT:   DB  0       ; Info-Ausgaben
TOTAL_CNT:  DB  0       ; Gesamtanzahl
GRP_PASS:   DB  0       ; Gruppenweise: bestanden
GRP_FAIL:   DB  0       ; Gruppenweise: fehlgeschlagen
GRP_TOTAL:  DB  0       ; Gruppenweise: gesamt
FAIL_LIST:  DS  40      ; IDs fehlgeschlagener Tests (max. 20 × 2 Bytes)
FAIL_LPTR:  DB  0       ; Zeiger in FAIL_LIST
; Mailbox-Ergebnispuffer (vom EM256-RAM gelesen)
MB_STATUS_HI: DB 0      ; STATUS High-Byte
MB_STATUS_LO: DB 0      ; STATUS Low-Byte
MB_RES1_HI:   DB 0      ; RESULT1 High (Big-Endian)
MB_RES1_LO:   DB 0      ; RESULT1 Low
MB_RES2_HI:   DB 0      ; RESULT2 High
MB_RES2_LO:   DB 0      ; RESULT2 Low
MB_RES3_HI:   DB 0      ; RESULT3 High
MB_RES3_LO:   DB 0      ; RESULT3 Low
```

---

## 7. Z8001 Cross-Assembler (z8001asm.py)

### 7.1 Unterstützte Instruktionen

Minimaler Befehlssatz für die Test-Firmwares:

**Lade/Speicher:**
- `LD Rd, #imm16` – Register mit Wert laden
- `LD Rd, Rs` – Register kopieren
- `LD Rd, @Rs` – Indirekt laden
- `LD @Rd, Rs` – Indirekt speichern
- `LDB Rbd, #imm8` – Byte-Register laden (Kurzform)
- `LDB Rbd, Rbs` – Byte-Register kopieren
- `LDL RRd, #imm32` – Langwort laden
- `LDL RRd, RRs` – Langwort kopieren
- `LDK Rd, #n` – Kurzwert (0-15)

**Arithmetik:**
- `ADD Rd, #imm16` / `ADD Rd, Rs` / `ADDB Rbd, #imm8`
- `ADDL RRd, RRs`
- `SUB Rd, #imm16` / `SUB Rd, Rs` / `SUBB Rbd, #imm8`
- `CP Rd, #imm16` / `CP Rd, Rs` / `CPB Rbd, #imm8`
- `INC Rd, #n` / `DEC Rd, #n` (n = 1..16)
- `NEG Rd`

**Logik:**
- `AND Rd, #imm16` / `AND Rd, Rs`
- `OR Rd, #imm16` / `OR Rd, Rs`
- `XOR Rd, #imm16` / `XOR Rd, Rs`
- `COM Rd`

**Bit-Operationen:**
- `BIT Rd, #b` / `SET Rd, #b` / `RES Rd, #b`

**Shift/Rotation:**
- `SLA Rd, #n` / `SRA Rd, #n` / `SLL Rd, #n` / `SRL Rd, #n`
- `RL Rd, #n` / `RR Rd, #n`

**Sprünge:**
- `JR cc, label` – Relativ (±128)
- `JP cc, #addr` – Absolut (Nonsegmented-Adresse)
- `DJNZ Rd, label` – Decrement & Jump if Not Zero
- `CALL #addr` / `RET cc`
- `CALR label` – Relativ

**Stack:**
- `PUSH @Rd, Rs` / `POP Rd, @Rs`
- `PUSHL @Rd, RRs` / `POPL RRd, @Rs`

**System:**
- `NOP`
- `HALT`
- `SC #imm`
- `DI` / `EI`

**Pseudo-Instruktionen:**
- `ORG addr` – Assembler-PC setzen
- `DW value` – 16-Bit-Wort ausgeben (Big-Endian)
- `DB value` – Byte ausgeben
- `DS count` – Platz reservieren (mit 0x00)
- `EQU name, value` – Konstante definieren
- `label:` – Label definieren

### 7.2 Register-Bezeichner

| Syntax | Encoding | Typ |
|--------|----------|-----|
| R0–R15 | 0–15 | 16-Bit-Wortregister |
| RH0–RH7 | 0–7 | High-Byte der Register R0–R7 |
| RL0–RL7 | 0–7 | Low-Byte der Register R0–R7 |
| RR0, RR2, ..., RR14 | 0,2,...,14 | 32-Bit-Registerpaare |
| RQ0, RQ4, RQ8, RQ12 | 0,4,8,12 | 64-Bit-Registerquadrupel |

### 7.3 Condition-Codes

| Syntax | Code | Beschreibung |
|--------|------|--------------|
| F | 0000 | False (nie) |
| T | 1000 | True (immer) |
| Z / EQ | 0110 | Zero / Equal |
| NZ / NE | 1110 | Not Zero / Not Equal |
| C / ULT | 0111 | Carry / Unsigned Less Than |
| NC / UGE | 1111 | No Carry / Unsigned Greater or Equal |
| PL | 1101 | Plus (Vorzeichen positiv) |
| MI | 0101 | Minus (Vorzeichen negativ) |
| OV | 0100 | Overflow |
| NOV | 1100 | No Overflow |
| GT | 1010 | Greater Than (signed) |
| GE | 1001 | Greater or Equal (signed) |
| LT | 0001 | Less Than (signed) |
| LE | 0010 | Less or Equal (signed) |
| UGT | 1011 | Unsigned Greater Than |
| ULE | 0011 | Unsigned Less or Equal |

### 7.4 Ausgabeformat

Der Cross-Assembler erzeugt:
1. **Binärdatei** (.bin): Rohbytes ab ORG-Adresse
2. **M80-Include** (.inc): DB-Zeilen mit Kommentaren für direktes Einfügen
3. **Listing** (.lst): Adresse | Hex | Quellzeile

Beispiel .inc-Ausgabe:
```
; Generated by z8001asm.py from fw_add.s
; Origin: 0x0000, Size: 26 bytes
C1_CODE:
	DB	000H, 000H, 000H, 000H		; 0000: DW 0x0000, 0x0000  ; Reset-Vektor
	DB	000H, 000H, 000H, 040H		; 0004: DW 0x0000, 0x0040
	; ...
	DB	021H, 001H, 012H, 034H		; 0040: LD R1, #0x1234
	DB	001H, 001H, 056H, 078H		; 0044: ADD R1, #0x5678
	DB	0E8H, 0FEH			; 004C: JR T, $
C1_CODE_LEN	EQU	$ - C1_CODE
```

### 7.5 Assembler-Aufbau (Python)

```python
# z8001asm.py - Minimal Z8001 Cross-Assembler
#
# Klassen:
#   Lexer       - Tokenisierung einer Quellzeile
#   Parser      - Erkennung von Instruktionen und Operanden
#   Encoder     - Erzeugung der Binärbytes pro Instruktion
#   Assembler   - 2-Pass-Assemblierung (Pass 1: Labels, Pass 2: Bytes)
#
# Aufruf:
#   python z8001asm.py input.s [-o output.bin] [--inc output.inc] [--lst]
```

---

## 8. Zeitplan und Prioritäten

### Phase 1: Grundgerüst
1. Z8001 Cross-Assembler (z8001asm.py) – Mindestbefehlssatz
2. Firmware fw_add.s (= bestehender em256tst.mac Z8K-Code, zur Validierung)
3. Z80-Rahmenprogramm mit Gruppe A + B + C1

### Phase 2: Vollständig
4. Alle C-Firmwares (C2–C8)
5. March-C-Firmware (D1–D4)
6. Adressleitung-Test (D5)
7. Paritätstests (E1–E3)
8. Zusammenfassung und Gesamtstatistik

### Phase 3: Optimierung
9. Fehlerliste in Zusammenfassung
10. Optionale Gruppen-Auswahl per Kommandozeile
11. Schnelltest-Modus (nur kritische Tests)

---

## 9. Bekannte Einschränkungen

1. **U8001-I/O:** Unklar ob/wie der U8001 auf A33 schreiben kann (I/O-Decoder-
   Adressierung). Für Segment-Umschaltung durch U8001-Software muss dies geklärt
   werden. Workaround: Z80 wechselt Segment über PIO-B (sg0p/sg1b).

2. **DRAM-Test Segment 0:** Der Bereich 0x0000–0x003F enthält Reset-Vektor, Mailbox
   und Firmware-Code. Dieser Bereich wird beim March-C-Test übersprungen.

3. **Timeout:** U8001-Code ohne Endlosschleife (HALT statt JR T,$) führt zu
   TREN-Timeout. Alle Firmwares enden mit `JR T, $`.

4. **Paritätsfehler-Provokation (E3):** Möglicherweise nicht sicher durchführbar.
   Erfordert Byte-Schreiben mit falschem Paritätsbit, was nur über die
   Hardware-Ebene möglich ist.

5. **Segmentweiche-Testen durch U8001:** Erfordert U8001-I/O-Zugriff auf A33 –
   wenn nicht möglich, fällt dies weg.

---

## 10. Referenzen

- [doc/16bit.md](../../doc/16bit.md) – EM256 Hardwaredokumentation
- [16bitTest/docs/Auszug_Handbuch.md](Auszug_Handbuch.md) – Handbuch A 5120.16
- [16bitTest/src/em256tst.mac](../src/em256tst.mac) – Funktionierender Basistest (v3)
- Zilog Z8000 CPU User's Reference Manual – Befehlssatz-Referenz
