# EM256 – 16-Bit-Erweiterungskarte des BC A5120

**Stand der Analyse:** April 2026  
**Quellen:** `src/bc_a5120/bios.mac`, `src/bc_a5120/biosrem.mac`, `src/bc_a5120/biosremc.mac`

---

## 1. Übersicht

Die **EM256** ist eine Erweiterungskarte für den DDR-Bürocomputer **BC A5120** (und hardwareäquivalente Systeme wie K8924, K8927, A5130). Sie enthält:

- **256 KB RAM** – aufgebaut aus 16×4-Bit-Speicherbausteinen (hence „16×4-RAM")
- **U8000** – ein DDR-Derivat des Zilog Z8000 (16-Bit-CPU)
- **PIO** – eine Parallel-I/O-Baugruppe zur Steuerung und Kommunikation

Im CP/A-BIOS wird die Karte ausschließlich als **RAM-Floppy „M:"** genutzt, wobei der U8000 permanent im Hardware-Reset gehalten wird. Dieser Abschnitt beschreibt die vollständige Hardware-Schnittstelle, um eigene Software zu entwickeln, die den U8000 tatsächlich startet und 16-Bit-Code darauf ausführt.

> **Quellen in bios.mac:**  
> Zeilen 223–237: Konfigurationskonstanten (`em256`, `em256adr`, `modadr`)  
> Zeile 1072: Interruptvektor `ivpar`  
> Zeile 1500/1539: bedingte Include-Anweisungen für `biosrem.mac` und `biosremc.mac`

---

## 2. I/O-Adressen

| Name | Adresse | Beschreibung |
|------|---------|--------------|
| `modadr` | `0xA8` | PIO Port B (Daten) – Steuerregister U8000 + RAM |
| `modadr+1` | `0xA9` | PIO Port B (Daten) – zweiter Zugriffspfad (gleicher Port) |
| `modadr+2` | `0xAA` | PIO Port A (Daten) – Status-/Kennung-Eingabe |
| `modadr+3` | `0xAB` | PIO Port A/B Steuerregister |
| `modadr+7` | `0xAF` | 16×4-RAM Konfigurationsregister (Page/Write-Enable) |

> **Quelle:** `src/bc_a5120/biosremc.mac`, Zeilen 10–52 (Bit-Definitionen und RAM-Kommentarblock)

---

## 3. PIO-Port-Belegung (Z80-PIO auf dem EM256)

### PIO Port A – `0xAA` (alle Bits **Eingabe**)

| Bit | Name | Funktion |
|-----|------|----------|
| 0 | `pioa_0` | Kennung vom U8000 (Bit 0) |
| 1 | `pioa_1` | Kennung vom U8000 (Bit 1) |
| 2 | `pioa_2` | Kennung vom U8000 (Bit 2) |
| 3 | `n_vi` | Vektorinterrupt U8000 (negiert) |
| 4 | `int16` | **Interrupt vom U8000 an U880** – U8000 signalisiert Fertig |
| 5 | `n_s` | Normal-(1) oder Systemmode-(0) des U8000 |
| 6 | `m8_16` | 8-Bit-(1) oder 16-Bit-Modus-(0) des U8000 |
| 7 | `tren` | **Transfer Enable** – U8000 ist bereit für Datenaustausch |

Der PIO Port A wird im BIOS mit `0xCF` (Bit-E/A-Modus) und `0xFF` (alle Bits Eingabe) initialisiert, Interrupts sind verboten.

### PIO Port B – `0xA8` (Bits 0–6 **Ausgabe**, Bit 7 **Eingabe**)

| Bit | Name | Funktion |
|-----|------|----------|
| 0 | `sg0p` | Für U880-Zugriff angewähltes Segment (Bit 0) |
| 1 | `sg1b` | Für U880-Zugriff angewähltes Segment (Bit 1) |
| 2 | `n_ramen` | RAM-Enable (negiert) – 0 = RAM für U880 zugänglich |
| 3 | `n_stop` | U8000-Stop (negiert) – 0 = anhalten, 1 = laufen |
| 4 | `reset16` | **U8000-Reset** – 1 = in Reset halten, 0 = laufen lassen |
| 5 | `n_trq8` | Transfer-Request des U880 an U8000 (negiert) |
| 6 | `prreset` | Reset Paritätsfehler-Latch |
| 7 | `n_pe` | Paritätsfehler (negiert, Eingabe) |

> **Quelle:** `src/bc_a5120/biosremc.mac`, Zeilen 10–27

---

## 4. Das 16×4-RAM-Konfigurationsregister (`0xAF`)

Der 256-KB-Speicher wird durch ein spezielles Register auf Port `0xAF` in das 16-KB-Fenster des U880-Adressraums bei `em256adr = 0x4000` eingeblendet. Das Besondere: die **oberen 4 Bit der Portadresse** bilden die Subadresse und wählen damit die **Page** (0–15) im gewählten Segment:

```
Portadresse:  | Sub |  Basisadresse |
              | 4 Bit | 0xAF       |
Datenbyte:    | x | x | x | x | /A15-8 | /A14-8 | n_write | n_pagen |
```

| Bit (Datenbyte) | Name | Funktion |
|-----------------|------|----------|
| 0 | `n_pagen` | Page enable (negiert) – **0 = eingeblendet** |
| 1 | `n_write` | Write enable (negiert) – **0 = schreibbar** |
| 2 | `/A14-8` | Adressbit 14 auf EM256-Seite (negiert) |
| 3 | `/A15-8` | Adressbit 15 auf EM256-Seite (negiert) |

Die Subadresse in den oberen 4 Bits der **Portadresse** (nicht des Datenbytes) wählt die Page. Also:
- `OUT (0x0F), A` → Page 0
- `OUT (0x1F), A` → Page 1
- `OUT (0xFF), A` → Page 15

Kombiniert mit den 2 Segment-Bits (sg0p, sg1b in Port B) ergibt sich:
- **4 Segmente × 16 Pages × 16 KB = 256 KB** Gesamtkapazität

> **Quelle:** `src/bc_a5120/biosremc.mac`, Zeilen 30–52 (Kommentar-Block zur RAM-Programmierung)  
> **Quelle:** `src/bc_a5120/biosrem.mac`, Zeilen 68–113 (`ramon`-Routine)

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

Die folgende Sequenz führt das CP/A-BIOS beim Kaltstart aus (`src/bc_a5120/biosremc.mac`, Zeilen 55–80):

```z80
; Interruptvektor für Paritätsfehler eintragen
LD HL, parrou
LD (intvec+ivpar), HL

; PIO Port A initialisieren (3 Bytes via OTIR)
LD B, 3
LD HL, painit          ; 0CFh, 0FFh, 07h
LD C, modadr+2         ; 0xAA = PIO Port A Steuerregister
OTIR

; PIO Port B initialisieren (5 Bytes via OTIR)
LD B, 5
LD HL, pbinit          ; ivpar, 0CFh, 80h, 97h, 80h
LD C, modadr+3         ; 0xAB = PIO Port B Steuerregister
OTIR

; Paritäts-Latch zurücksetzen, dann Ruhezustand herstellen
LD A, 1 SHL prreset OR 1 SHL reset16 OR 1 SHL n_ramen
OUT (modadr+1), A      ; Parity-Reset-Impuls
LD A, 1 SHL n_ramen OR 1 SHL reset16  ; RAM aus, U8000 in Reset
OUT (modadr+1), A
```

**Initialisierungsdaten:**

```
painit (Port A):
  0CFh  = Bit-E/A-Modus
  0FFh  = alle Bits Eingabe
  07h   = Interrupts verboten, keine Maske

pbinit (Port B):
  ivpar = Interruptvektor für Paritätsfehler (= intvsy + 0x00)
  0CFh  = Bit-E/A-Modus
  80h   = Bit 7 Eingabe (n_pe), Bits 0–6 Ausgabe
  97h   = Maske folgt, 0-Pegel löst INT aus, INT Enable
  80h   = Bit 7 (n_pe) löst Interrupt aus (Paritätsfehler)
```

---

## 7. Starten des U8000 und Ausführen von 16-Bit-Code

> **Hinweis:** Das CP/A-BIOS startet den U8000 **niemals**. Alle folgenden Informationen sind aus der Hardware-Beschreibung (Bit-Definitionen) in `biosremc.mac` abgeleitet.

### 7.1 Voraussetzungen

Der U8000 (Z8000-Derivat) startet im **Normal Sequential Mode** und holt seinen **Reset-Vektor** aus Adresse `0x0000` des **U8000-eigenen Adressraums**. Da die EM256-Karte keinen eigenen Boot-ROM hat, muss der U880 zuerst Code in den Shared-RAM schreiben, bevor der U8000 freigegeben wird.

Der U8000-Adressraum bei Adresse `0x0000` entspricht – durch das Paging-Schema – **Page 0, Segment 0** des EM256-RAM.

### 7.2 Startsequenz (U880-Assembler-Code)

```z80
;==============================================================
; Schritt 1: U8000-Code in Shared-RAM laden (U8000 noch in Reset)
;==============================================================

; Segment 0, Page 0 einblenden (Track 0 = S=0, P=0)
XOR A                       ; Track 0 = Page 0, Segment 0
CALL ramon                  ; RAM scharf, HL zeigt auf 0x4000

; U8000-Code nach 0x4000 (= U8000-Adresse 0x0000) kopieren
LD HL, u8000_code           ; Quellzeiger (U8000-Binärcode)
LD DE, em256adr             ; Ziel: 0x4000 im Z80-Adressraum
LD BC, u8000_code_len
LDIR

CALL ramoff                 ; RAM wieder auskoppeln

;==============================================================
; Schritt 2: PIO Port A/B korrekt aufsetzen (falls noch nicht done)
;==============================================================
; (Standard: wie im BIOS-Kaltstart, siehe Abschnitt 6)

;==============================================================
; Schritt 3: U8000 freigeben (Reset aufheben, Stop aufheben)
;==============================================================

; n_ramen=1 (RAM für U880 aus), n_stop=1, reset16=0
LD A, 1 SHL n_stop OR 1 SHL n_ramen
OUT (modadr+1), A
; U8000 startet jetzt und holt Reset-Vektor von Adresse 0x0000

;==============================================================
; Schritt 4: Auf Fertigmeldung des U8000 warten
;==============================================================
wait_u8:
    IN A, (modadr)          ; PIO Port A lesen (0xA8)
    BIT tren, A             ; Bit 7: Transfer Enable?
    JR Z, wait_u8           ; Noch nicht bereit → warten
; alternativ: auf int16 (Bit 4) als Interrupt reagieren lassen

;==============================================================
; Schritt 5: Daten austauschen via Shared-RAM
;==============================================================
; Daten in Shared-RAM schreiben:
XOR A
CALL ramon                  ; Page 0 einblenden
LD HL, ergebnis_buf
LD DE, em256adr + offset
LD BC, datalen
LDIR
CALL ramoff

; Transfer-Request an U8000 senden:
LD A, 1 SHL n_stop          ; n_stop=1, n_trq8=0 (aktiv), reset16=0
OUT (modadr+1), A

; Auf nächste Antwort warten (wie Schritt 4)
```

### 7.3 U8000-seitige Adressbelegung

| U8000-Adresse | Inhalt |
|---------------|--------|
| `0x0000` | Reset-Vektor (Z8000: 4 Byte – Segment-Deskriptor + PC) |
| `0x0004` ff. | NMI- und weitere Interrupt-Vektoren |
| ab `0x0010` | frei für Anwendungscode |

Der **Z8000-Reset-Vektor** ist 4 Byte groß:
- Byte 0–1: Segment-Selektionsdeskriptor (bei Normal-Sequential-Mode: `0x0000`)
- Byte 2–3: Startadresse des Codes

### 7.4 U8000 anhalten und zurücksetzen

```z80
; Sanftes Anhalten:
LD A, 1 SHL reset16 OR 1 SHL n_ramen   ; Reset setzen, RAM aus
OUT (modadr+1), A

; Alternativ: Stop (hält nach aktuellem Befehl an):
LD A, 1 SHL n_ramen                     ; n_stop=0 → Stop aktiv
OUT (modadr+1), A
; Dann Reset:
LD A, 1 SHL reset16 OR 1 SHL n_ramen
OUT (modadr+1), A
```

---

## 8. Kommunikationsprotokoll U880 ↔ U8000

Da beide CPUs auf denselben 256-KB-RAM zugreifen (nacheinander, nie gleichzeitig), ist der Shared-RAM das einzige Kommunikationsmedium. Das Protokoll über die Steuerleitungen:

| Signal | Richtung | Beschreibung |
|--------|----------|--------------|
| `n_trq8` (Bit 5, Port B) | U880 → U8000 | Transfer-Request: U880 hat Daten bereit (0 = aktiv) |
| `tren` (Bit 7, Port A) | U8000 → U880 | Transfer Enable: U8000 ist bereit (1 = bereit) |
| `int16` (Bit 4, Port A) | U8000 → U880 | Interrupt: U8000 hat Ergebnis bereit |
| `n_vi` (Bit 3, Port A) | U8000 → U880 | Vektorinterrupt-Anforderung des U8000 |

**Empfohlener Ablauf:**
1. U880 schreibt Daten in Shared-RAM (via `ramon`/`ramoff`)
2. U880 setzt `n_trq8 = 0` → Transfer-Request
3. U8000 liest Daten, verarbeitet sie
4. U8000 setzt `tren = 1` und/oder sendet `int16`-Interrupt
5. U880 liest Ergebnis aus Shared-RAM

---

## 9. Paritätsfehler-Behandlung

Der EM256-RAM hat Paritätsbits. Ein Paritätsfehler:
1. Setzt `n_pe` (Bit 7, Port A) auf 0
2. Löst einen Interrupt am Z80 aus (über PIO Port B, Interruptvektor `ivpar = intvsy + 0x00`)
3. BIOS-ISR `parrou` setzt Flag `parerr = 1`

**Paritätsfehler-Latch zurücksetzen:**
```z80
IN A, (modadr+1)
SET prreset, A              ; Bit 6 setzen
OUT (modadr+1), A
RES prreset, A              ; Bit 6 löschen → Flanke erzeugt Reset
OUT (modadr+1), A
```

> **Quelle:** `src/bc_a5120/biosrem.mac`, Zeilen 117–127 (`parrou`-ISR)

---

## 10. Kapazitätsvarianten

Das BIOS erkennt beim Kaltstart die tatsächliche Bestückung der Karte und passt den DPB entsprechend an:

| Bestückung | Kapazität | Erkennung |
|------------|-----------|-----------|
| Voll (4 Segmente) | 256 KB | Kennung nur in Segment 0 |
| Halb | 128 KB | Kennung auch in Segment 2 (Track 32) |
| Viertel | 64 KB | Kennung auch in Segment 1 (Track 16) |

> **Quelle:** `src/bc_a5120/biosremc.mac`, Zeilen 155–192

---

## 11. RAM-Floppy DPB (Disk Parameter Block)

Wenn der U8000 nicht genutzt wird und die Karte als RAM-Floppy dient:

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

## 12. Konstanten-Übersicht

```z80
; Aus bios.mac (nur gültig wenn em256 = 1):
em256adr  EQU 4000h   ; U880-Fensteradresse des eingeblendeten RAM
modadr    EQU 0A8h    ; PIO Port B Datenregister (= Basisadresse EM256)

; PIO Port A (modadr+0 = 0xA8 für Lesen, modadr+2 = 0xAA für Steuer):
pioa_0    EQU 0       ; Kennung Bit 0
pioa_1    EQU 1       ; Kennung Bit 1
pioa_2    EQU 2       ; Kennung Bit 2
n_vi      EQU 3       ; Vektorinterrupt U8000 (neg.)
int16     EQU 4       ; Interrupt U8000→U880
n_s       EQU 5       ; Normal(1)/System(0)-Mode
m8_16     EQU 6       ; 8-Bit(1)/16-Bit(0)-Mode
tren      EQU 7       ; Transfer Enable

; PIO Port B (modadr+1 = 0xA9):
sg0p      EQU 0       ; Segment-Bit 0 (für U880-Zugriff)
sg1b      EQU 1       ; Segment-Bit 1
n_ramen   EQU 2       ; RAM-Enable (neg.)
n_stop    EQU 3       ; U8000-Stop (neg.)
reset16   EQU 4       ; U8000-Reset (1 = in Reset)
n_trq8    EQU 5       ; Transfer-Request U880→U8000 (neg.)
prreset   EQU 6       ; Paritätsfehler-Latch-Reset
n_pe      EQU 7       ; Paritätsfehler (neg., Eingabe)

; 16×4-RAM-Register (modadr+7 = 0xAF, Subadresse in Port-Adress-Bits 7:4):
n_pagen   EQU 0       ; Page enable (neg.)
n_write   EQU 1       ; Write enable (neg.)
; Bits 2-3: /A14-8 und /A15-8 (neg. Adressbits für U880-Fenster)
; Bits 7:4 der Portadresse: Subadresse = Page-Nummer (0–15)

; Interruptvektor (aus bios.mac, Zeile 1072):
ivpar     EQU intvsy+00h  ; Paritätsfehler EM256-RAM
```

---

## 13. Quellcode-Referenzen

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
| `src/bc_a5120/biosremc.mac` Z. 55–110 | PIO-Initialisierung, Kaltstart-Code |
| `src/bc_a5120/biosremc.mac` Z. 111–192 | Präsenzerkennung, Kapazitätserkennung |
| `src/bc_a5120/biosremc.mac` Z. 196–223 | PIO-Initialisierungsdaten, `tstkng`, Kennung |
