# EM256 Comprehensive Test Program – Design Document

**Version:** 1.2  
**Datum:** 2026-04-09  
**Autor:** Olaf Krieger  
**Zielplattform:** BC A5120 mit EM256-Karte (U8001, 256 KB DRAM)

---

## 1. Überblick

Umfassendes Testprogramm für die EM256 16-Bit-Erweiterungskarte.
Prüft alle Hardwarekomponenten in fünf Gruppen (A–E) mit kompakter, übersichtlicher
Konsolenausgabe. Ein Z80-Masterprogramm (CP/M .COM) steuert den gesamten Ablauf und
lädt bei Bedarf Z8001-Firmware in das Shared-DRAM, die der U8001 autonom ausführt.

Das fertige Programm `em256ful.com` umfasst ~6016 Bytes und enthält:
- 2002 Zeilen Z80-Assembler (em256ful.mac, M80-Syntax)
- 9 eingebettete Z8001-Firmware-Blöcke (96–230 Bytes je Firmware)
- 30 Einzeltests in 5 Gruppen (A–E)
- Automatische Seitensteuerung, Fehlerstatistik und Debug-Diagnose bei Timeout

### 1.1 Anforderungen

- Alle Tests laufen als **einzelne .COM-Datei** unter CP/A (CP/M 2.2)
- **Gruppenweise Ausführung** mit Seitenpause nach ~23 Zeilen (PAGELEN=23)
- **Kompakte Ausgabe:** Status rechts ausgerichtet: `[OK]`, `[FEHLER]`, `[INFO]`, `[TIMEOUT]`
- Bei Fehler: Detailzeile(n) mit Soll/Ist-Werten
- Bei Timeout: Debug-Ausgabe mit PIO-A-Status, Mailbox-STATUS, RESULT1, Reset-Vektor und Opcode
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
| 0x0000 | 2 | (reserviert) | Vom Z8001 bei Reset ignoriert |
| 0x0002 | 2 | FCW | Flag and Control Word (0xC000: Segmented + System Mode) |
| 0x0004 | 2 | PC Segment | Segmentnummer (0x0000 = Segment 0) |
| 0x0006 | 2 | PC Offset | Startadresse (0x0040 = Code-Beginn) |
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

> **Hinweis zum Reset-Vektor (Bytes 0x0000–0x0007):** Der Z8001 liest beim Reset
> das FCW von Adresse 0x0002 und den PC (segmentiert) von Adresse 0x0004–0x0007.
> Adresse 0x0000–0x0001 ist reserviert und wird ignoriert. Quelle: Z8000 CPU
> User's Reference Manual, Abschnitt 7.4, und MAME z8000.cpp (`RDMEM_W(m_program, 2)`
> für FCW, `segmented_addr(RDMEM_L(m_program, 4))` für PC).

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

| Nr  | Test | U8001-Code (fw_*.s) | Erwartung |
|-----|------|---------------------|-----------|
| C1 | Addition 1234+5678 | LD R1,#1234; ADD R1,#5678 → Mailbox | RESULT1 = 0x68AC |
| C2 | Subtraktion 8000-0001 | LD R1,#8000; SUB R1,#0001 → Mailbox | RESULT1 = 0x7FFF |
| C3 | Logik AND/OR/XOR | 0xFF00 AND 0x0F0F → OR → XOR → 0x1234 | RESULT1 = 0x1234 |
| C4 | Speicher-R/W | 4 Muster (A55A/5AA5/FFFF/0000) + Cross | STATUS = 0x0001 |
| C5 | Schleifentest (DJNZ) | R1=0, R2=256, LOOP: INC+DEC+CP+JR NZ | RESULT1 = 0x0100 |
| C6 | Stack-Test | PUSH 0xBEEF, PUSH 0xCAFE, POP×2 (LIFO) | RESULT1 = 0xBEEF |
| C7 | 32-Bit-Addition | ADDL RR2(0x00010000) + RR4(0x0000FFFF) | RES1=0x0001, RES2=0xFFFF |
| C8 | Byte-Operationen | CLR R1; LDB RH1,#0x75; LDB RL1,#0x10 | RESULT1 = 0x7510 |

**Allgemeiner Ablauf pro C-Test (Z80-seitig, via RUN_FW_TEST):**

```z80
; Aufruf:
;   LD HL, FW_ADD_CODE        ; Adresse des Firmware-Blobs
;   LD BC, FW_ADD_CODE_LEN    ; Länge des Firmware-Blobs
;   CALL RUN_FW_TEST          ; CF=0: OK, CF=1: Timeout

; RUN_FW_TEST intern:
CALL RAMON_S0                 ; Shared-DRAM einblenden
LD DE, EM256ADR               ; = 0x4000
LDIR                          ; Firmware kopieren (Resetvektor + Code)
XOR A
LD (EM256ADR + 10h), A        ; STATUS High = 0
LD (EM256ADR + 11h), A        ; STATUS Low = 0
CALL RAMOFF                   ; DRAM ausblenden
CALL START_U8000              ; OUT PIOB_RUN (0x2C): n_stop=1, n_ramen=1, n_trq8=1
; ... kurze Verzögerung (DJNZ-Schleife) ...
CALL WAIT_READY               ; PIOB_TRQ senden, TREN/INT16 pollen
JR C, TIMEOUT                 ; CF=1: kein TREN erkannt
CALL STOP_U8000               ; OUT PIOB_IDLE (0x14): reset16=1
CALL RAMON_S0                 ; DRAM wieder einblenden
CALL READ_MAILBOX             ; STATUS + RESULT1-3 in lokalen Puffer lesen
CALL RAMOFF
; CF=0: Ergebnis in MB_STATUS_xx und MB_RESx_xx verfügbar
```

> **Bei Timeout** wird `DBG_TOUT` aufgerufen, das PIO-A-Status, Mailbox-Inhalt,
> Resetvektor-PC und ersten Opcode bei 0x0040 als Diagnose ausgibt.

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
    DW  0x0000          ; Reserviert (vom Z8001 ignoriert)
    DW  0xC000          ; FCW = Segmented + System Mode (Bit 15 + Bit 14)
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
    ; Bus freigeben und Endlosschleife:
    MSET                ; Multi-Micro-Bit setzen (MO-Pin → TREN)
    JR  T, $            ; Wartet bis Z80 µI-Reset auslöst
```

**Wichtige Erkenntnisse zum FCW:**

| FCW-Bit | Wert | Bedeutung |
|---------|------|-----------|
| Bit 15 (F_SEG) | 0x8000 | Segmentierter Modus (erforderlich für Z8001-Busprotokoll) |
| Bit 14 (F_S/N) | 0x4000 | System Mode (erforderlich für privilegierte Befehle wie MSET) |
| **FCW = 0xC000** | | **Segmented + System Mode** |

> **Warum FCW = 0xC000?**
>
> 1. **System Mode (Bit 14)** ist zwingend erforderlich, weil `MSET` ein privilegierter
>    Befehl ist. Im Normal Mode (FCW=0x0000) löst MSET eine Privilege Violation Trap aus,
>    statt den MO-Pin zu setzen → TREN wird nie HIGH → Z80 wartet endlos → TIMEOUT.
>
> 2. **Segmented Mode (Bit 15)** ist erforderlich, weil die EM256-Hardware für den
>    segmentierten Z8001-Bus ausgelegt ist. Die Adressleitungen SN0–SN6 erwarten gültige
>    Segmentnummern. Im Non-Segmented Mode könnte das Busprotokoll nicht korrekt
>    funktionieren.

**MSET und JR T, $ – Terminierungsprotokoll:**

```
U8001-Seite:                    Z80-Seite:
  MSET → MO-Pin HIGH             WAIT_READY:
  JR T, $ (Endlosschleife)         OUT PIOB_TRQ (n_trq8=0, Bus-Request)
                                    Poll PIO-A Bit 7 (TREN) + Bit 4 (INT16)
                                    → TREN HIGH erkannt → CF=0 (bereit)
                                  STOP_U8000 (PIOB_IDLE, Reset)
                                  RAMON_S0 → READ_MAILBOX → RAMOFF
```

`MSET` muss vor jedem `JR T, $` stehen. Ohne MSET bleibt der MO-Pin LOW,
und der Z80 erkennt nie, dass die Firmware fertig ist.

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
; Register-Konventionen (wie in fw_march.s):
; R1  = Testmuster (Soll-Wert)
; R2  = aktuelle Adresse
; R3  = Anfangsadresse (0x0100)
; R4  = Endadresse (0xFFFE)
; R5  = gelesener Wert
; R6  = Hilfsregister (neues Muster)
; R7-R8 = Mailbox-Hilfsregister (bei FAIL)
; R15 = SP (0x00FE, knapp unter Testbereich)

MARCH_C:
    LD  R15, #0x00FE        ; SP unter Testbereich
    LD  R3, #0x0100         ; Start (hinter Code+Mailbox)
    LD  R4, #0xFFFE         ; Ende (letzte Wortadresse)
    LD  R1, #0x0000         ; Muster Phase 1

; Phase 1: Aufwärts mit 0x0000 füllen
+   LD  R2, R3
P1_LOOP:
    LD  @R2, R1
    INC R2, #2
    CP  R2, R4
    JR  ULE, P1_LOOP
    LD  @R2, R1             ; Auch letzte Adresse

; Phase 2: Aufwärts: 0x0000 lesen, 0xFFFF schreiben
    LD  R1, #0x0000         ; Erwartung
    LD  R6, #0xFFFF         ; neues Muster
    LD  R2, R3
P2_LOOP:
    LD  R5, @R2
    CP  R5, R1              ; Sollte 0x0000 sein
    JR  NZ, FAIL
    LD  @R2, R6             ; 0xFFFF schreiben
    INC R2, #2
    CP  R2, R4
    JR  ULE, P2_LOOP
    ; letzte Adresse
    LD  R5, @R2
    CP  R5, R1
    JR  NZ, FAIL
    LD  @R2, R6

; Phase 3: Aufwärts: 0xFFFF lesen
    LD  R1, #0xFFFF
    LD  R2, R3
P3_LOOP:
    LD  R5, @R2
    CP  R5, R1
    JR  NZ, FAIL
    INC R2, #2
    CP  R2, R4
    JR  ULE, P3_LOOP
    LD  R5, @R2
    CP  R5, R1
    JR  NZ, FAIL

; Phase 4: Abwärts: 0xFFFF lesen, 0x0000 schreiben
    LD  R1, #0xFFFF
    LD  R6, #0x0000
    LD  R2, R4              ; von Ende
P4_LOOP:
    LD  R5, @R2
    CP  R5, R1              ; Sollte 0xFFFF sein
    JR  NZ, FAIL
    LD  @R2, R6             ; 0x0000 schreiben
    DEC R2, #2
    CP  R2, R3
    JR  UGE, P4_LOOP

; Phase 5: Abwärts: 0x0000 lesen
    LD  R1, #0x0000
    LD  R2, R4
P5_LOOP:
    LD  R5, @R2
    CP  R5, R1
    JR  NZ, FAIL
    DEC R2, #2
    CP  R2, R3
    JR  UGE, P5_LOOP

; Erfolg
    LD  R1, #0x0001         ; STATUS = OK
    LD  R2, #0x0010
    LD  @R2, R1
    MSET                    ; MO-Pin setzen → TREN → Z80 erkennt "fertig"
    JR  T, $                ; Fertig

FAIL:
    ; R2 = Fehleradresse, R5 = gelesener Wert, R1 = erwarteter Wert
    LD  R7, #0x0010
    LD  R8, #0x0002         ; STATUS = FEHLER
    LD  @R7, R8
    INC R7, #2
    LD  @R7, R1             ; RESULT1 = Soll-Wert
    INC R7, #2
    LD  @R7, R5             ; RESULT2 = Ist-Wert
    INC R7, #2
    LD  @R7, R2             ; RESULT3 = Fehleradresse
    MSET
    JR  T, $
```

---

## 6. Programmstruktur (Z80-Seite)

### 6.1 Dateistruktur

```
16bitTest/
├── build.py                 ← Build-Script (z8001asm + Präprozessor + M80 + LINKMT)
├── z8001asm.py              ← Z8001 Cross-Assembler (Python, 2075 Zeilen)
├── src/
│   ├── em256ful.mac         ← Volltest (Z80-Assembler, M80-Syntax, 2002 Zeilen)
│   ├── em256tst.mac         ← Original-Test (bestehend, nur Grundfunktionstest)
│   ├── fw_add.s             ← C1: Additionstest (96 Bytes)
│   ├── fw_sub.s             ← C2: Subtraktionstest (96 Bytes)
│   ├── fw_logic.s           ← C3: Logiktest (108 Bytes)
│   ├── fw_memrw.s           ← C4: Speicher-R/W (186 Bytes)
│   ├── fw_loop.s            ← C5: Schleifentest (106 Bytes)
│   ├── fw_stack.s           ← C6: Stacktest (138 Bytes)
│   ├── fw_add32.s           ← C7: 32-Bit-Arithmetik (106 Bytes)
│   ├── fw_byte.s            ← C8: Byte-Operationen (106 Bytes)
│   └── fw_march.s           ← D1: March-C DRAM-Test (230 Bytes)
├── build/
│   └── em256ful.com         ← Fertiges CP/M-Programm (~6016 Bytes)
└── docs/
    ├── em256test_design.md  ← Dieses Dokument
    ├── Auszug_Handbuch.md   ← Handbuch A 5120.16
    └── Z8000 CPU User's Reference Manual.md  ← Z8000 Referenz
```

> **Hinweis:** Der Z8001-Assembler `z8001asm.py` liegt direkt im 16bitTest/-Verzeichnis
> (nicht in einem Unterordner), da er sowohl vom Build-Script als auch eigenständig
> aufgerufen werden kann. Die Firmware-Quelldateien (fw_*.s) liegen zusammen mit der
> Z80-Quelle in `src/`.

### 6.2 Build-Prozess

Der Build erfolgt über `build.py` (Standard: `em256ful`, alternativ `em256tst`):

```
cd /pfad/zu/CPA_Workbench
python3 16bitTest/build.py                    # baut em256ful.com (Standard)
python3 16bitTest/build.py em256tst           # baut em256tst.com (Original)
python3 16bitTest/build.py clean              # build/ leeren
```

**Ablauf für em256ful (8 Schritte):**
```
1. Build-Verzeichnis 16bitTest/build/ anlegen
2. z8001asm.py assembliert alle fw_*.s aus src/ → .bin + .inc in build/
3. Präprozessor ersetzt ;%INCLUDE-Direktiven in em256ful.mac
   durch den Inhalt der .inc-Dateien aus build/
4. CRLF-Konvertierung der vorverarbeiteten .mac-Datei → build/EM256FUL.MAC
5. M80 + LINKMT Build-Tools (tools/) nach build/ kopieren
6. M80 assembliert EM256FUL.MAC → EM256FUL.ERL (über cparun CP/M-Emulator)
7. LINKMT linkt EM256FUL.ERL → em256ful.com (Ladeadresse 0x100)
8. Temporäre Dateien (.mac, .erl, .bin, .inc, m80.com, linkmt.com) aufräumen
   + em256ful.com nach additions/bc_a5120/ kopieren
```

**Abhängigkeiten:**
- `tools/cparun` – CP/M-Emulator (Linux) zum Ausführen von M80 und LINKMT
- `tools/m80.com` – Microsoft Macro Assembler für Z80
- `tools/linkmt.com` – Linker für M80-ERL-Dateien
- Python 3.6+

> **Hinweis:** M80 hat keine INCLUDE/MACLIB-Unterstützung für Roh-DB-Blöcke.
> Daher verwendet em256ful.mac `;%INCLUDE datei.inc`-Markerkommentare,
> die der build.py-Präprozessor vor der M80-Assemblierung textuell ersetzt.
> Beispiel: `;%INCLUDE fw_add.inc` wird durch den vollständigen DB-Block ersetzt.

### 6.3 Z80-Codestruktur

```z80
; em256ful.mac - Hauptprogramm (2002 Zeilen)
;
; Sektionen:
;   1. Konstanten & Equates (CP/M, PIO, RAM16, Mailbox, Timeouts)
;   2. Hauptprogramm (MAIN: Testschleife pro Gruppe)
;   3. Testgruppe A: PIO-Tests (A1-A9)
;   4. Testgruppe B: Speicherfenster-Tests (B1-B10)
;   5. Testgruppe C: Kooperative CPU-Tests (C1-C8)
;   6. Testgruppe D: Autonomer DRAM-Test (D1)
;   7. Testgruppe E: Paritätstests (E1-E2)
;   8. Gesamtzusammenfassung (Bestanden/Fehlerliste/Kapazität)
;   9. Hilfsfunktionen (INIT_PIO, DETECT_EM256, DETECT_CAPACITY,
;      RAMON_S0..S3, RAMOFF)
;  10. U8001-Steuerung (START/STOP_U8000, WAIT_READY, WAIT_READY_LONG,
;      RUN_FW_TEST, RUN_FW_TEST_LONG, READ_MAILBOX, CHECK_RESULT1)
;  11. Ausgabefunktionen (PUTS, PUTHEX, PUTHEX16, PUTDEC, PUTC,
;      PRINT_OK/FAIL/INFO/TIMEOUT, PRINT_DETAIL_HEX, PRINT_RES1_DETAIL,
;      PRINT_MARCH_DETAIL, PAGE_PAUSE)
;  12. Debug-Diagnose (DBG_TOUT: PIO-A, Mailbox, Resetvektor, Opcode)
;  13. Statistik-Management (COUNT_PASS/INFO/FAIL_xx, PRINT_GRP_SUMMARY)
;  14. Meldungstexte
;  15. Z8001-Code-Blöcke (;%INCLUDE fw_*.inc)
;  16. Variablen, Mailbox-Puffer & Stack
```

### 6.4 Hilfsroutinen

| Routine | Funktion |
|---------|----------|
| `PUTS` | String ausgeben mit Seitenpause (LF-Zählung, PAGELEN=23) |
| `PUTHEX` | Byte als HEX ausgeben (2 Zeichen) |
| `PUTHEX16` | Wort als HEX ausgeben (4 Zeichen, Big-Endian-Reihenfolge) |
| `PUTDEC` | Byte als Dezimalzahl (ohne Vornullen, 0–255) |
| `PUTC` | Einzelnes Zeichen ausgeben (E=Zeichen) |
| `PRINT_COLON` | " 0x" ausgeben (für [INFO]-Werte) |
| `PRINT_OK` | `[OK]` + CRLF |
| `PRINT_FAIL` | `[FEHLER]` + CRLF |
| `PRINT_INFO` | `[INFO]` + CRLF |
| `PRINT_TIMEOUT` | `[TIMEOUT]` + CRLF |
| `PRINT_DETAIL_HEX` | Eingerückte Detailzeile `Soll: 0xXX  Ist: 0xXX` (Byte) |
| `PRINT_RES1_DETAIL` | Zeigt Mailbox-RESULT1 als Detail `Ergebnis: 0xXXXX` |
| `PRINT_MARCH_DETAIL` | Zeigt March-Fehlerdetails (Adresse/Soll/Ist als Word) |
| `PAGE_PAUSE` | Warten auf Tastendruck bei voller Seite (BDOS 6, blockierend) |
| `RAMON_S0` | Segment 0, Seite 0 einblenden (RAM16=0x0C, PIOB=RAMON) |
| `RAMON_S0_P1..P3` | Segment 0, Seiten 1–3 einblenden |
| `RAMON_S1..S3` | Segmente 1–3, Seite 0 einblenden (über SG0P/SG1B) |
| `RAMOFF` | RAM ausblenden (RAM16=0x0F, PIOB=IDLE) |
| `INIT_PIO` | PIO initialisieren (3-Byte-OTIR für Port A + B, Parity-Reset, RAM16 aus) |
| `DETECT_EM256` | EM256-Erkennung (atomar: Write/Read-Test, setzt EM256_OK-Flag) |
| `DETECT_CAPACITY` | Segmentzahl erkennen (Alias-Prüfung Seg 0 vs. 1/2/3, → A=1..4) |
| `START_U8000` | U8001 freigeben: OUT PIOB_RUN (0x2C = n_stop + n_ramen + n_trq8) |
| `STOP_U8000` | U8001 stoppen: OUT PIOB_IDLE (0x14 = reset16 + n_ramen) |
| `WAIT_READY` | TRQ8 senden → TREN pollen (kurzer Timeout ~2s, Doppelschleife) |
| `WAIT_READY_LONG` | TRQ8 senden → TREN pollen (langer Timeout ~16s, für March-C) |
| `READ_MAILBOX` | STATUS + RESULT1–3 (Big-Endian) aus EM256-RAM in lokalen Puffer |
| `CHECK_RESULT1` | Vergleicht RESULT1 (Hi/Lo) mit DE-Register, ZF=1 bei Übereinstimmung |
| `RUN_FW_TEST` | Gesamtablauf: RAMON_S0 → LDIR → STATUS nullen → RAMOFF → START → Delay → WAIT_READY → STOP → RAMON_S0 → READ_MAILBOX → RAMOFF |
| `RUN_FW_TEST_LONG` | Wie RUN_FW_TEST mit langer Vor-Verzögerung (~4s) + langem Timeout |
| `DBG_TOUT` | Debug bei Timeout: PIO-A + Mailbox + Resetvektor + Opcode ausgeben |
| `COUNT_PASS` | Bestanden-Zähler (global + Gruppe) inkrementieren |
| `COUNT_INFO` | Info-Zähler (global + Gruppe) inkrementieren |
| `COUNT_FAIL_xx` | Fehler-Zähler + Test-ID (2 Bytes) in FAIL_LIST eintragen |
| `PRINT_GRP_SUMMARY` | `--- N/M bestanden, K Fehler ---` pro Gruppe |

### 6.5 Statistik und Variablen

```z80
; Statistik-Zähler
PASS_CNT:   DB  0       ; Bestandene Tests (global)
FAIL_CNT:   DB  0       ; Fehlgeschlagene Tests (global)
INFO_CNT:   DB  0       ; Info-Ausgaben (global)
TOTAL_CNT:  DB  0       ; Gesamtanzahl (global)
GRP_PASS:   DB  0       ; Gruppenweise: bestanden (wird pro Gruppe zurückgesetzt)
GRP_FAIL:   DB  0       ; Gruppenweise: fehlgeschlagen
GRP_TOTAL:  DB  0       ; Gruppenweise: gesamt
FAIL_LIST:  DS  40      ; IDs fehlgeschlagener Tests (max. 20 × 2 Bytes)
FAIL_LPTR:  DB  0       ; Schreibzeiger in FAIL_LIST
LINECNT:    DB  0       ; Zeilenzähler für Seitensteuerung

; Mailbox-Ergebnispuffer (vom EM256-RAM gelesen, Big-Endian-Reihenfolge)
MB_STATUS_HI: DB 0      ; STATUS High-Byte
MB_STATUS_LO: DB 0      ; STATUS Low-Byte
MB_RES1_HI:   DB 0      ; RESULT1 High
MB_RES1_LO:   DB 0      ; RESULT1 Low
MB_RES2_HI:   DB 0      ; RESULT2 High
MB_RES2_LO:   DB 0      ; RESULT2 Low
MB_RES3_HI:   DB 0      ; RESULT3 High
MB_RES3_LO:   DB 0      ; RESULT3 Low

; Debug-Variablen (gefüllt von DBG_TOUT bei Timeout)
DBG_PA:     DB  0       ; PIO-A Status zum Zeitpunkt des Timeouts
DBG_V6:     DB  0       ; Reset-Vektor Byte 6 (PC Offset High)
DBG_V7:     DB  0       ; Reset-Vektor Byte 7 (PC Offset Low)
DBG_C0:     DB  0       ; Erster Opcode-Byte bei 0x0040
DBG_C1:     DB  0       ; Zweites Opcode-Byte bei 0x0041

; Sonstige
SAVED_SP:   DW  0       ; Gesicherter SP für sauberes RET nach CP/M
SAVE_WORD:  DW  0       ; Zwischenspeicher für RAM-Test
TMP_BYTE:   DB  0       ; Temporär
TMP_WORD:   DW  0       ; Temporär
TMP_WORD2:  DW  0       ; Temporär
EM256_OK:   DB  0       ; Flag: EM256 erkannt (1) oder nicht (0)
DET_SEGS:   DB  0       ; Erkannte Segmentanzahl (1–4)
CUR_GROUP:  DB  'A'     ; Aktuelle Testgruppe
TOUT_VAL:   DB  020H    ; Aktueller Timeout-Wert
            DS  128     ; Stack
STACK_TOP:
```

### 6.6 Debug-Diagnose bei Timeout

Wenn `WAIT_READY` oder `WAIT_READY_LONG` mit Timeout zurückkehrt, wird `DBG_TOUT`
aufgerufen. Diese Routine gibt eine kompakte Diagnosezeile aus:

```
   PA=xx ST=xxxx R1=xxxx
   VEC=xxxx CD=xxxx
```

| Feld | Bedeutung |
|------|-----------|
| PA | PIO-A Registerwert (Bit 7=TREN, Bit 4=INT16) |
| ST | Mailbox-STATUS (0x0000=nicht gestartet, 0x0001=OK, 0x0002=FEHLER) |
| R1 | Mailbox-RESULT1 |
| VEC | Reset-Vektor PC-Offset (Bytes 6–7, erwartet 0x0040) |
| CD | Erster Opcode bei 0x0040 (erwartet 0x21xx für LD R15,#imm) |

**Diagnose-Beispiel (vor dem FCW-Fix):**
```
   PA=28 ST=0000 R1=0000
   VEC=0040 CD=210F
```
PA=0x28 → Bit 7=0 (TREN nicht gesetzt) → MSET hat MO-Pin nicht assertiert.
Ursache: FCW=0x0000 (Normal Mode), MSET ist privilegiert → Privilege Violation Trap.

---

## 7. Z8001 Cross-Assembler (z8001asm.py)

Der Assembler ist in Python implementiert (2075 Zeilen), arbeitet als 2-Pass-Assembler
und erzeugt Z8001-Maschinencode. Er unterstützt ca. 90 Encoder-Methoden für den
vollständigen Befehlssatz, der für die EM256-Testfirmwares benötigt wird.

### 7.1 Unterstützte Instruktionen

**Lade/Speicher (Word, Byte, Long):**
- `LD Rd, #imm16` / `LD Rd, Rs` / `LD Rd, @Rs` / `LD @Rd, Rs` / `LD @Rd, #imm16`
- `LDB Rbd, #imm8` / `LDB Rbd, Rbs` / `LDB Rbd, @Rs` / `LDB @Rd, Rbs`
- `LDL RRd, #imm32` / `LDL RRd, RRs`
- `LDK Rd, #n` – Kurzwert (0–15)
- `CLR Rd` / `CLRB Rbd`

**Arithmetik (Word, Byte, Long):**
- `ADD Rd, #imm16` / `ADD Rd, Rs` / `ADD Rd, @Rs` / `ADDB Rbd, #imm8` / `ADDB Rbd, Rbs`
- `ADDL RRd, RRs` / `ADDL RRd, #imm32` / `ADDL RRd, @Rs`
- `SUB Rd, #imm16` / `SUB Rd, Rs` / `SUB Rd, @Rs` / `SUBB Rbd, #imm8` / `SUBB Rbd, Rbs`
- `SUBL RRd, RRs` / `SUBL RRd, #imm32` / `SUBL RRd, @Rs`
- `CP Rd, #imm16` / `CP Rd, Rs` / `CP Rd, @Rs` / `CPB Rbd, #imm8` / `CPB Rbd, Rbs`
- `CPL RRd, RRs` / `CPL RRd, #imm32` / `CPL RRd, @Rs`
- `INC Rd, #n` / `DEC Rd, #n` (n = 1..16)
- `NEG Rd` / `NEGB Rbd`
- `MULT RRd, Rs` / `MULT RRd, #imm16` / `MULT RRd, @Rs`
- `MULTL RQd, RRs` / `MULTL RQd, #imm32` / `MULTL RQd, @Rs`
- `DIV RRd, Rs` / `DIV RRd, #imm16` / `DIV RRd, @Rs`
- `DIVL RQd, RRs` / `DIVL RQd, #imm32` / `DIVL RQd, @Rs`
- `DAB Rbd`
- `EXTSB Rd` / `EXTS RRd` / `EXTSL RQd`

**Logik:**
- `AND Rd, #imm16` / `AND Rd, Rs` / `ANDB Rbd, #imm8`
- `OR Rd, #imm16` / `OR Rd, Rs` / `ORB Rbd, #imm8`
- `XOR Rd, #imm16` / `XOR Rd, Rs` / `XORB Rbd, #imm8`
- `COM Rd` / `COMB Rbd`
- `TEST Rd` / `TESTB Rbd` / `TESTL RRd`
- `TSET Rd` / `TSETB Rbd`

**Bit-Operationen:**
- `BIT Rd, #b` / `BITB Rbd, #b`
- `SET Rd, #b` / `SETB Rbd, #b`
- `RES Rd, #b` / `RESB Rbd, #b`

**Shift/Rotation:**
- `SLA Rd, #n` / `SLAB Rbd, #n` – Shift Left Arithmetic
- `SRA Rd, #n` / `SRAB Rbd, #n` – Shift Right Arithmetic
- `SLL Rd, #n` / `SLLB Rbd, #n` – Shift Left Logical
- `SRL Rd, #n` / `SRLB Rbd, #n` – Shift Right Logical
- `RL Rd, #n` / `RLB Rbd, #n` – Rotate Left
- `RR Rd, #n` / `RRB Rbd, #n` – Rotate Right
- `RLC Rd, #n` / `RLCB Rbd, #n` – Rotate Left through Carry
- `RRC Rd, #n` / `RRCB Rbd, #n` – Rotate Right through Carry
- `SDAL Rd, #n` / `SDALB Rbd, #n` / `SDLL Rd, #n` / `SDLLB Rbd, #n`

**Sprünge und Subroutinen:**
- `JR cc, label` – Relativ (dsp8, ±256 Bytes, Displacement wird durch 2 geteilt)
- `JP cc, #addr` – Absolut (Nonsegmented-Adresse)
- `DJNZ Rd, label` – Decrement & Jump if Not Zero (dsp7)
- `DBJNZ Rbd, label` – Decrement Byte & Jump if Not Zero (dsp7)
- `CALL #addr` / `CALL @Rs` – Subroutine-Aufruf
- `CALR label` – Relativer Subroutine-Aufruf (dsp12)
- `RET cc` – Bedingter/Unbedingter Return

**Stack:**
- `PUSH @Rd, Rs` / `PUSH @Rd, #imm16` / `POP Rd, @Rs`
- `PUSHL @Rd, RRs` / `POPL RRd, @Rs`

**Register-Transfer:**
- `EX Rd, Rs` / `EXB Rbd, Rbs` – Register-Austausch
- `LDCTL` – Control-Register laden/speichern (FCW, REFRESH, PSAPSEG, PSAPOFF)
- `TCC cc, Rd` / `TCCB cc, Rbd` – Test Condition Code

**Flag-Operationen:**
- `SETFLG flags` / `RESFLG flags` / `COMFLG flags`

**I/O:**
- `IN Rd, @Rs` / `INB Rbd, @Rs` – I/O-Eingang (indirekt)
- `IN Rd, #port` / `INB Rbd, #port` – I/O-Eingang (direkt)
- `OUT @Rd, Rs` / `OUTB @Rd, Rbs` – I/O-Ausgang (indirekt)
- `OUT #port, Rs` / `OUTB #port, Rbs` – I/O-Ausgang (direkt)

**System/Privilegiert:**
- `NOP` / `HALT`
- `SC #imm` – System Call
- `DI` / `EI` – Interrupts sperren/freigeben (VI/NVI)
- `IRET` – Interrupt Return
- `MSET` – Multi-Micro-Bit setzen (setzt MO-Pin, **privilegiert**)
- `MRES` – Multi-Micro-Bit zurücksetzen (**privilegiert**)
- `MBIT` – Multi-Micro-Bit testen

**Pseudo-Instruktionen:**
- `ORG addr` – Assembler-PC setzen
- `DW value[, value...]` – 16-Bit-Wörter ausgeben (Big-Endian)
- `DB value[, value...]` – Bytes ausgeben
- `DS count` – Platz reservieren (mit 0x00)
- `EQU name, value` – Konstante definieren
- `label:` – Label definieren (mit oder ohne Doppelpunkt)

### 7.2 Register-Encoding

| Syntax | 4-Bit-Feld | Typ | Erklärung |
|--------|------------|-----|-----------|
| R0–R15 | 0–15 | 16-Bit-Wortregister | Direkte Zuordnung |
| RH0–RH7 | 0–7 | High-Byte | RHn → Feld = n |
| RL0–RL7 | 8–15 | Low-Byte | RLn → Feld = n + 8 |
| RR0, RR2, ..., RR14 | 0,2,...,14 | 32-Bit-Paare | Gerade Nummern |
| RQ0, RQ4, RQ8, RQ12 | 0,4,8,12 | 64-Bit-Quadrupel | Vielfache von 4 |

> **Wichtig: Byte-Register-Encoding.** Die Zuordnung RHn=n und RLn=n+8 folgt dem
> Split-Schema (obere/untere Hälfte im 4-Bit-Feld), NICHT dem Interleaved-Schema
> (2n/2n+1). Verifiziert gegen den MAME-Emulator (Makro `RB(n) = m_regs.B[n ^ 1]`
> in z8000.h) und das Z8000 CPU Reference Manual.

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

### 7.4 Besonderheiten der Codeerzeugung

**JR-Displacement (dsp8):**
Der Z8001 speichert den JR-Displacement als Wort-Offset. Die CPU multipliziert
den gespeicherten Wert intern mit 2, bevor er auf den PC addiert wird. Deshalb
muss der Assembler die Byte-Distanz (target − (PC + 2)) **durch 2 teilen**.

```python
# z8001asm.py - JR-Encoding
byte_disp = target - (self.pc + 2)
disp = byte_disp // 2   # CPU multipliziert dsp8 intern × 2
```

Beispiel: `JR T, $` bei PC=0x004C → target=0x004C, byte_disp=−2, disp=−1 → `E8 FF`.

**CALR und DJNZ** verwenden ein analoges Schema (dsp12 bzw. dsp7, ebenfalls ÷2).

### 7.5 Ausgabeformat

Der Cross-Assembler erzeugt:
1. **Binärdatei** (.bin): Rohbytes ab ORG-Adresse
2. **M80-Include** (.inc): DB-Zeilen mit Kommentaren für direktes Einfügen (M80-Syntax)
3. **Listing** (.lst): Adresse | Hex | Quellzeile (optional, mit `--lst`)

Beispiel .inc-Ausgabe:
```
; Generated by z8001asm.py from fw_add.s
; Origin: 0x0000, Size: 96 bytes
FW_ADD_CODE:
	DB	000H, 000H, 0C0H, 000H		; 0000: DW 0x0000, 0xC000
	DB	000H, 000H, 000H, 040H		; 0004: DW 0x0000, 0x0040
	; ... (56 Bytes Mailbox) ...
	DB	021H, 00FH, 0FFH, 0F0H		; 0040: LD R15, #0xFFF0
	DB	021H, 001H, 012H, 034H		; 0044: LD R1, #0x1234
	DB	001H, 001H, 056H, 078H		; 0048: ADD R1, #0x5678
	; ...
	DB	07BH, 008H                  ; 005C: MSET
	DB	0E8H, 0FFH                  ; 005E: JR T, $
FW_ADD_CODE_LEN	EQU	$ - FW_ADD_CODE
```

> **Hinweis:** Das Label-Prefix (z.B. `FW_ADD_`) wird vom Build-Script automatisch
> aus dem Dateinamen abgeleitet (fw_add.s → FW_ADD_CODE / FW_ADD_CODE_LEN).
> Die Firmware-Blöcke werden im Z80-Quelltext über `LD HL, FW_ADD_CODE` /
> `LD BC, FW_ADD_CODE_LEN` referenziert.

### 7.6 Assembler-Aufbau (Python)

```python
# z8001asm.py - Minimal Z8001 Cross-Assembler (2075 Zeilen)
#
# Aufbau:
#   CC_TABLE      - Condition-Code-Tabelle (16 Einträge + Aliase)
#   parse_register() - Register-Parser (R, RH, RL, RR, RQ)
#   parse_indirect() - Indirekt-Adressierung (@Rn, @RRn)
#   eval_expr()      - Ausdrucksauswertung mit Labels und $
#   Encoder       - 90 statische Methoden für Instruktions-Encoding
#   AsmError      - Fehlerklasse mit Datei/Zeile
#   Assembler     - 2-Pass-Assembly (Pass 1: Labels sammeln, Pass 2: Code erzeugen)
#
# Aufruf:
#   python z8001asm.py input.s [-o output.bin] [--inc output.inc] [--lst]
#                              [--label PREFIX]
```

---

## 8. Zeitplan und Prioritäten

### Phase 1: Grundgerüst ✅
1. Z8001 Cross-Assembler (z8001asm.py) – 90 Encoder-Methoden, 2075 Zeilen
2. Firmware fw_add.s (= bestehender em256tst.mac Z8K-Code, zur Validierung)
3. Z80-Rahmenprogramm mit Gruppe A + B + C1

### Phase 2: Vollständig ✅
4. Alle C-Firmwares (C1–C8) – 8 kooperative CPU-Tests
5. March-C-Firmware (D1) – Segment 0 DRAM-Test (230 Bytes Z8001-Code)
6. Paritätstests (E1–E2)
7. Zusammenfassung und Gesamtstatistik mit Fehlerliste
8. Debug-Diagnose (DBG_TOUT) mit PIO-A, Mailbox, Resetvektor und Opcode-Ausgabe

### Phase 3: Geplant (noch nicht implementiert)
9. D2–D4: DRAM-Test für Segmente 1–3 (erfordert Klärung A33-Programmierung)
10. D5: Adressleitung-Test
11. E3: Paritätsfehler-Provokation (erfordert sichere Methode)
12. Optionale Gruppen-Auswahl per Kommandozeile
13. Schnelltest-Modus (nur kritische Tests)

---

## 9. Bekannte Einschränkungen

1. **U8001-I/O:** Unklar ob/wie der U8001 auf A33 schreiben kann (I/O-Decoder-
   Adressierung). Für Segment-Umschaltung durch U8001-Software muss dies geklärt
   werden. Workaround: Z80 wechselt Segment über PIO-B (sg0p/sg1b).

2. **DRAM-Test Segment 0:** Der Bereich 0x0000–0x00FF enthält Reset-Vektor, Mailbox
   und Firmware-Code. Dieser Bereich wird beim March-C-Test übersprungen
   (Testbereich: 0x0100–0xFFFE wortweise).

3. **MSET vor JR T,$:** Zwingend erforderlich. Ohne MSET bleibt der MO-Pin LOW,
   TREN wird nie gesetzt, und der Z80 wartet endlos (TIMEOUT). Alle 9 Firmwares
   enthalten `MSET` direkt vor jedem `JR T, $`.

4. **FCW = 0xC000:** Segmented + System Mode ist zwingend. System Mode (Bit 14)
   ist nötig weil MSET ein privilegierter Befehl ist. Segmented Mode (Bit 15)
   ist nötig weil die EM256-Hardware segmentierte Busprotokolle erwartet.

5. **Paritätsfehler-Provokation (E3):** Möglicherweise nicht sicher durchführbar.
   Erfordert Byte-Schreiben mit falschem Paritätsbit, was nur über die
   Hardware-Ebene möglich ist.

6. **Segmentweiche-Testen durch U8001:** Erfordert U8001-I/O-Zugriff auf A33 –
   wenn nicht möglich, fällt dies weg.

---

## 10. Gefundene Bugs und Korrekturen

Während der Entwicklung und beim Testen auf der realen EM256-Hardware wurden
folgende Bugs im Z8001-Cross-Assembler und in den Firmware-Dateien gefunden und
behoben:

### Bug 1: Fehlender MSET-Befehl

**Symptom:** Alle C-Tests enden mit TIMEOUT. PIO-A Bit 7 (TREN) bleibt 0.

**Ursache:** Die Firmwares endeten nur mit `JR T, $`, ohne vorher den MO-Pin
zu setzen. Der Z80 erkennt die Fertigstellung der U8001-Firmware über TREN
(Multi-Micro Transfer Enable), das an den MO-Pin des Z8001 gekoppelt ist.
Ohne `MSET` wird MO nie HIGH.

**Fix:** `MSET` vor jedes `JR T, $` in allen 9 Firmware-Dateien eingefügt.

### Bug 2: JR-Displacement nicht durch 2 geteilt

**Symptom:** Schleifen (C5, March-C) erzeugen falsche Ergebnisse. JR springt
doppelt so weit wie erwartet.

**Ursache:** Die Z8001-CPU speichert den JR-Displacement als **Wort-Offset**
und multipliziert ihn intern mit 2. Der Assembler gab den Byte-Offset direkt
aus → Sprungdistanz verdoppelt.

**Fix:** `disp = (target - (self.pc + 2)) // 2` in z8001asm.py.

### Bug 3: Byte-Register-Encoding falsch (Interleaved statt Split)

**Symptom:** C8 (Byte-Operationen) liefert falsche Ergebnisse. `LDB RH1, #0x75`
schreibt in das falsche Byte.

**Ursache:** Anfänglich wurde das Interleaved-Schema verwendet (RHn=2n, RLn=2n+1).
Das korrekte Schema ist das Split-Schema: RHn=n (0–7), RLn=n+8 (8–15).

**Verifizierung:** MAME z8000.h Makro `RB(n)` bestätigt das Split-Schema:
```cpp
uint8_t& RB(int n) { return m_regs.B[n ^ 1]; }
// n=0..7: RH0..RH7, n=8..15: RL0..RL7
```

**Fix:** `parse_register()` gibt für RLn jetzt `n + 8` zurück (statt `2*n + 1`).

**Beispiel (korrektes Encoding):**
```
LDB RH1, #0x75  →  C1 75   (Byte-Reg Feld = 1 = RH1)
LDB RL1, #0x10  →  C9 10   (Byte-Reg Feld = 9 = RL1)
```

### Bug 4: FCW = 0x0000 (Normal Mode) statt 0xC000

**Symptom:** Alle C-Tests TIMEOUT, auch nachdem MSET eingefügt wurde.
Diagnose: PA=0x28 → TREN=0, trotz MSET im Code.

**Ursache:** FCW=0x0000 setzt den Z8001 in den **Normal Mode**. MSET ist ein
**privilegierter Befehl** und darf nur im System Mode (FCW Bit 14 = 1) ausgeführt
werden. Im Normal Mode löst MSET eine **Privilege Violation Trap** aus, statt den
MO-Pin zu setzen. Ohne PSAP-Vektortabelle im DRAM hängt sich der Z8001 auf.

**Verifizierung:**
- Z8000 CPU User's Reference Manual, Abschnitt 7.4, Zeile 4389:
  *"In the Z8001, the first cycle reads the FCW from location 0002 of segment 0"*
- MAME z8000.cpp: `CHANGE_FCW(RDMEM_W(m_program, 2))`
- Beides bestätigt: FCW wird aus Adresse **0x0002** gelesen (nicht 0x0000).

**Fix:** FCW von 0x0000 auf **0xC000** geändert (Bit 15 = Segmented, Bit 14 = System).
In allen 9 Firmware-Dateien:
```z8001
; Vorher (falsch):
DW  0x0000, 0x0000, 0x0000, 0x0040  ; FCW=0x0000: Normal Mode

; Nachher (korrekt):
DW  0x0000, 0xC000, 0x0000, 0x0040  ; FCW=0xC000: Segmented + System Mode
```

---

## 11. Referenzen

- [doc/16bit.md](../../doc/16bit.md) – EM256 Hardwaredokumentation
- [16bitTest/docs/Auszug_Handbuch.md](Auszug_Handbuch.md) – Handbuch A 5120.16
- [16bitTest/docs/Z8000 CPU User's Reference Manual.md](Z8000%20CPU%20User%27s%20Reference%20Manual.md) – Befehlssatz-Referenz (4875 Zeilen)
- [16bitTest/src/em256tst.mac](../src/em256tst.mac) – Funktionierender Basistest (Original)
- [MAME z8000.cpp](https://github.com/mamedev/mame/blob/master/src/devices/cpu/z8000/z8000.cpp) – Referenz-Implementierung des Z8000 CPU-Emulators
