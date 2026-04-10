# II. Technische Daten

## 1. Allgemeine Charakteristik

### 1.1. Systemübersicht

**Beschreibung der Schaltung (Abb. 1 Systemübersicht):**
Das Blockschaltbild zeigt die Integration des Erweiterungsmoduls (EM) in das System des Bürocomputers A 5120.
- Das **Erweiterungsmodul** besteht aus der **Steuereinheit EM (16 Bit-Prozessor U 8000)** und dem **Speicher EM** (wahlweise EM 064 mit 64 KByte oder EM 256 mit 256 KByte). Diese sind über einen **internen Systembus des EM** verbunden.
- Der **Bürocomputer A 5120** enthält die **ZRE K 2526 (8 Bit-Prozessor U 880)**, den eigenen **Speicher** und die **Ansteuerung für Peripheriegeräte**.
- Die Verbindung beider Einheiten erfolgt über den **K 1520 - Bus**.
- Spezifische Leitungen zwischen den Prozessoreinheiten sind als **Kommunikationssteuerleitung** (zwischen ZRE und Steuereinheit EM) und **Speicherzugriff 8 Bit** (zwischen K 1520-Bus und Steuereinheit EM) gekennzeichnet.

---

Der Bürocomputer A 5120 wird um einen Erweiterungsmodul zum Bürocomputer A 5120.16 aufgewertet.
Der A 5120.16 ist ein 16 Bit-Programmentwicklungsplatz. Er nutzt ein UNIX-kompatibles Betriebssystem (MUTOS 8000), ist aber kein System zur universellen Anwendung als 16 Bit-Bürocomputer.
Der A 5120.16 dient der Vorbereitung des Einsatzes von U 8000-Mikrorechentechnik, speziell für Programmentwicklung und Implementierungsaufgaben.
- Erarbeitung von Software für Einsatz A 5120.16 unter MUTOS 8000.
- Entwicklung von in C-Sprache programmierte Software für andere Gerätetechnik.

Der Erweiterungsmodul besteht aus:
- EM 064: Steuerkarte mit U 8001- oder U 8002-Mikroprozessor 
  Speicherkarte mit 64 KByte-Kapazität (RAM)           083-6-140-080
- EM 256: Steuerkarte mit U 8001-Mikroprozessor 
  Speicherkarte mit 256 KByte-Kapazität (RAM)          083-6-140-081

Speicher- und Steuerkarte sind am K 1520-Systembus angeschlossen und sind über das Kabel 083-4-051-039 an der Griffseite miteinander verbunden.

---

Der K 1520-Erweiterungsmodul wird vom 8 Bit-Mikrorechner initialisiert, mit einem U 8000-Mikroprogramm geladen und gestartet. Steuert der U 8000 das System, hat der U 880 nur die Funktion eines Peripheriesteuerrechners.
Die Betriebsart, d. h. die Festlegung wer Master oder Slave ist, erfolgt durch die Software und kann auch durch sie jederzeit gewechselt werden.
Der Bürocomputer A 5120.16 arbeitet in zwei Betriebsarten:
- **8 Bit-Mode**
  In diesem Mode steht der Speicher des EM vollständig dem U 880-K 1520-System zur Verfügung.
- **16 Bit-Mode**
  In dieser Betriebsart arbeiten sowohl die Steuerkarte mit U 8000 als auch das U 880-K 1520-System. Die Steuerkarte hat dabei das alleinige Zugriffsrecht auf die Speicherkarte.
  Das U 880-System übernimmt inzwischen die Abarbeitung von peripheren Aufgaben und meldet deren Abarbeitung z. B. über Interrupt an.

Im 16 Bit-Betrieb werden die Modi zur Auswahl der vier möglichen 64 KByte-Speicherelemente wie folgt festgelegt:
- Mode 0: Das Segment wird durch zwei Bit bestimmt (siehe Segmentweiche AD5* und AD6*).
- Mode 1: Es erfolgt die Zuordnung
  - Segment 0 - Systemmode/Data
  - Segment 1 - Systemmode/Instruction
  - Segment 2 - Normalmode/Data
  - Segment 3 - Normalmode/Instruction
- Mode 2: Die Segmente werden festgelegt durch die Signale SN0 und SN1 des U 8000.

Die Steuerbaugruppe besitzt als zentrales Element den 16 Bit-Prozessor U 8000, der den Speicher mit einer Kapazität von 256 oder 64 KByte ansteuert und verwaltet.
Er hat keinen direkten Zugriff zum K 1520-Speicher (64 KByte) und der Peripherie des 8 Bit-Systems. Die Speicherbaugruppe kann wahlweise mit 16 KBit oder 64 KBit RAM-Bausteinen bestückt sein. Daraus ergeben sich für diese Baugruppe Kapazitäten von 64 KByte RAM oder 256 KByte RAM.
Der Speicher kann vom 8 Bit-System bzw. 16 Bit-System adressiert werden. Ohne Steuerkarte ist der Speicher jedoch nicht funktionsfähig.
Empfohlen wird für die Einbauvariante des EM folgende STE-Zuordnung:

`|  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  |  10  |  11  |`
`  ASS  ZRE16 EM064 ZRE   ABS   AFS   Speicher`
`             EM256 K2526`

Für die Nachrüstung sind die Steckplätze 7 und 8 bzw. 6 und 7 zu verwenden.
Zu beachten ist, daß die ZRE 16 unbedingt in die Prioritätenkette IEI/IEO eingebunden werden muß (siehe Montagevorschrift).

---

## 1.2. Gerätevarianten

**083-7-030-152**
- Grundgerät mit: Stromversorgung, Monitor 1920 Zeichen und
  Steuereinheit mit: ZRE K 2526, OPS K 3526, AFS K 5122,
  ABS K 7024, ASS K 8025, EM 256 und 1 x 8"-Floppy-Disk
- Beistellgerät mit 2 x 8"-Floppy-Disk
- Tastatur K 7637
- Drucker nach Spezifikation

**083-7-030-153**
- Grundgerät mit: Stromversorgung, Monitor 1920 Zeichen und
  Steuereinheit mit: ZRE K 2526, OPS K 3526, AFS K 5122, ABS K 7024,
  ASS K 8025, EM 064 und 3 x 5,25"-Floppy-Disk
- Tastatur K 7637
- Drucker nach Spezifikation

## 2. Technische Daten für den EM

| Parameter | EM 064 | EM 256 |
| :--- | :--- | :--- |
| Prozessortyp | U 8001 und U 8002 | U 8001 |
| Steckeinheitenformat | (215 x 170)mm | (215 x 170)mm |
| Steckplatzraster | 15 mm | 15 mm |
| Taktfrequenz | 16 MHz | 16 MHz |
| Systemtakt | 4 MHz | 4 MHz |
| **Stromaufnahme** | | |
| Steuerkarte 5 P | 1,1 A | 1,1 A |
| **Stromaufnahme** | | |
| Speicherkarte 5 P | 800 mA | 950 mA |
| 12 P | 85 mA | - |
| 5 N | 0,15 mA | - |

---

## 3. Belegungsplan - Baugruppen: EM 064 (083-6-140-080/-082) / EM 256 (083-6-140-081/-083)

| ESE - X1 Systembus | | | ESE - X2 (Koppelbus) | | |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **n** | **An** | **Cn** | **n** | **An** | **Cn** |
| 1 | 00 | 00 | 1 | 5 P | 5 P |
| 2 | 00 | 00 | 2 | | |
| 3 | | | 3 | | |
| 4 | DB7 | DB6 | 4 | | |
| 5 | DB5 | DB4 | 5 | | |
| 6 | DB3 | DB2 | 6 | | |
| 7 | DB1 | DB0 | 7 | | |
| 8 | WR | RD | 8 | | |
| 9 | MREQ | MEMDI | 9 | | |
| 10 | IEC | IEI | 10 | | |
| 11 | AB14 | AB15 | 11 | | |
| 12 | AB12 | AB13 | 12 | | |
| 13 | AB10 | AB11 | 13 | | |
| 14 | AB8 | AB9 | 14 | | |
| 15 | 5 N ") | 5 N ") | 15 | | |
| 16 | AB6 | AB7 | 16 | | |
| 17 | AB4 | AB5 | 17 | MDI ') | MDO ') |
| 18 | AB2 | AB3 | 18 | | |
| 19 | AB0 | AB1 | 19 | | |
| 20 | RESET | | 20 | | |
| 21 | TAKT | | 21 | | |
| 22 | IODI | | 22 | | |
| 23 | | INT | 23 | | |
| 24 | WAIT | IORQ | 24 | | |
| 25 | RFSH | RDY | 25 | | |
| 26 | M1 | | 26 | | |
| 27 | | | 27 | | |
| 28 | 12 P ") | 12 P ") | 28 | 00 | 00 |
| 29 | 5 P | 5 P | 29 | 00 | 00 |

| X3 | | | X4 | | |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **n** | **An** | **Bn** | **n** | **An** | **Bn** |
| 1 | 00 | AD2 | 1 | PER | AD15 |
| 2 | 00 | AD1 | 2 | 00 | AD14 |
| 3 | 00 | AD0 | 3 | 00 | AD13 |
| 4 | 00 | WRI | 4 | 00 | AD12 |
| 5 | 00 | MREQ-16 | 5 | 00 | AD11 |
| 6 | 00 | RDI | 6 | 00 | AD10 |
| 7 | 00 | AS | 7 | 00 | AD9 |
| 8 | SG0 | RFI | 8 | 00 | AD8 |
| 9 | 8/16 | MREQ-8 | 9 | 00 | AD7 |
| 10 | A15I | SG1 | 10 | 00 | AD6 |
| 11 | AOI | B/W | 11 | 00 | AD5 |
| 12 | A14-8 | RU | 12 | 00 | AD4 |
| 13 | PR | 00 | 13 | 00 | AD3 |

') z. Zt. nicht genutzt
") nur für EM 064

---

# III. Funktionsbeschreibung

## 1. Steuereinheit EM

### 1.1. Blockschaltbild

**Beschreibung der Schaltung (Abb. 2 Blockschaltbild Steuereinheiten):**
Das Blockschaltbild zeigt die internen Daten- und Steuerpfade der Steuereinheit.
- Der **U 8000** Mikroprozessor kommuniziert über einen 16-Bit-Adress-/Datenbus (**AD0..15**) mit dem System. Ein **AD-Treiber** puffert diese Signale.
- Ein **Taktgenerator** liefert den Basistakt an den Prozessor.
- Der **Statusdecoder** verarbeitet die Statusleitungen der CPU und erzeugt Steuersignale für Speicher- und I/O-Zugriffe.
- Für die Segmentierung werden eine **SG-Mode Weiche** und ein **Umschalter** verwendet, die Signale wie **SG0**, **SG1**, **AOI** und **A15I** an den EM-Speicher liefern.
- Die **Speicherzugriffsteuerung** koordiniert Signale wie **MREQ 8**, **MREQ 16**, **8/16**, **AS**, **B/W** und die internen Lese-/Schreibsignale (**RFI**, **WRI**, **RDI**).
- Ein **Attributspeicher (16 x 4)** ist vorhanden, um Speicherattribute für den Host-Zugriff zu speichern.
- Die Kommunikation mit dem K 1520-Bus erfolgt über den **I/O-Decoder**, eine **PIO** (A32) sowie verschiedene Register (**Status 8**, **Vektor**, **Status 16**, **Steuer 16**).
- Der **Eigen-RFSH-generator** verwaltet autark die Refresh-Zyklen des dynamischen Speichers über das Signal **RU**.

---

### 1.2. Taktgenerator

**Beschreibung der Schaltung (Abb. 3 Taktgenerator):**
Die Takterzeugung basiert auf dem Schaltkreis **A55** (DS 8127).
- Ein 16 MHz Quarz ist an den Pins **X1** (Pin 11) und **X2** (Pin 10) angeschlossen, stabilisiert durch **R1** und **C2**.
- Pin 15 (**RESET IN**) empfängt das Initialisierungssignal.
- Pin 8 (**RESET OUT**) liefert das synchronisierte Rücksetzsignal an den Prozessor (U 8001/U 8002).
- Der Taktausgang Pin 14 liefert den 4 MHz Arbeitstakt.
- Ein zusätzliches Logikgatter **A31** (Pin 01/02) verarbeitet das Signal **RESET 16**, welches über **R4:2** an **5P** vorgespannt ist.

---

Der Schaltkreis DS 8127 beinhaltet zahlreiche Funktionen zur Taktaufbereitung und RESET-WAIT- bzw. TIME OUT-Steuerung für die angeschlossenen Prozessortypen. Für den Anwendungsfall EM werden für den U 8000 folgende Funktionen genutzt:
- 16 MHz Grundtakterzeugung mit Hilfe eines extern angeschlossenen Quarzes über X1 und X2
- Teilung der Grundtaktfrequenz (Faktor 4) und Ausgabe des Prozessortaktes von 4 MHz für den U 8000 über Ausgang ZCK (A55/08). C1 zwischen Ausgang 07 und 08 des A55 bewirkt eine steilere Anstiegsflanke des Taktes.
- RESET-Steuerung der CPU über RESET IN und RESET OUT synchron zur steigenden Flanke von ZCK.
  Im Einschaltmoment der Anlage sind die Ausgänge des PIO A32 hochohmig. Über R4:2 ist der A32/31 high und bewirkt über A31/02 und dem Schaltkreis A55, daß der Prozessor im Zustand "RESET" verbleibt.
  Über dieses RESET-16-Signal kann die Freigabe bzw. ein erneutes Rücksetzen programmiert werden.

### 1.3. Statusdecoder für den U 8000

Der Prozessor U 8000 besitzt 4 Statusleitungen ST0 ... ST3 und damit 16 Statuszustände, die über die Statusdecoderbausteine A45 und A46 decodiert werden. Er erzeugt die erforderlichen Steuersignale für den I/O- und Speicherverkehr, Interruptbetrieb und Statusanzeige.

**Beschreibung der Schaltung (Abb. 4 Statusdecoder):**
Die Schaltung nutzt zwei Decoder-ICs (**A45** und **A46**), um die CPU-Zustände auszuwerten.
- Die Leitungen **ST0** bis **ST3** führen an die Adress-Eingänge (**A0**, **A1**, **A2**) und Enable-Eingänge (**E1**, **E2**, **E3**) der Decoder.
- **A45** erzeugt die Signale: **RF 16** (Refresh), **I/O** (Ein-/Ausgabe), **NMI-ack** (Non-maskable-Acknowledge), **NVI-ack** (Non-vectored-Acknowledge) und **VI-ack** (Vectored-Acknowledge).
- **A46** arbeitet parallel und erzeugt über zusätzliche Logikgatter (**A38**, **A39**) die Signale **STACK**, **INSTRn** und **INSTR1** sowie ein allgemeines Instruktionssignal (**INSTR**) und den Datennadel-Strobe (**DS**).

---

Folgende Steuerleitungen werden für den EM decodiert:

**Interruptsteuerung:**
- **NMI-ack** (NMI-acknowledge): zum Rücksetzen des Paritätsfehler-FF's A46/09 auf der Speicher-STE des EM
- **NVI-ack** (NVI-acknowledge): zum Laden des Zählers zur Einzelbefehlsabarbeitung
- **VI-ack** (VI-acknowledge): zum Lesen des Interruptvektors im Register A34 und des Statusregisters A36.

**Speichersteuerung:**
- **RF16**: Steuersignal zum Auffrischen des dynamischen Speichers im Aktivmode des U 8000
- **INSTRn** / **INST1**: zur Bildung der Segmentsteuersignale SG0, SG1 für den Speicherzugriff

---

**Systemsteuerung:**
- **STACK**: zum Laden des Zählers zur Einzelbefehlsabarbeitung
- **I/O**: zum Lesen und Schreiben der an den U 8000 angeschlossenen Steuer- und Statusregister (A33/A35)

### 1.4. Segmentweiche und Adreßumschalter

**Beschreibung der Schaltung (Abb. 5 Segmentweiche, Adreßumschalter):**
- **A42 (Segmentweiche):** Verarbeitet die Signale **SN0**, **INSTR**, **AD5***, **AD6***, **AD7***, **SN1** und **N/S**. Über Ausgänge **D1 (07)** und **D2 (09)** werden die vorläufigen Segmentwahlsignale **SG0'** und **SG1'** an den nächsten Baustein weitergegeben.
- **A41 (Adreßumschalter):** Fungiert als Multiplexer. Er empfängt an einem Eingangssatz die Signale des Host-Systems (**SG0P**, **SG1P**, **AB0**, **AB 15-8**) und am anderen die der CPU (**AD0***, **AD15***). Gesteuert durch das Signal **8/16** an Pin 01 (**WS**) und **S**, schaltet er die endgültigen Signale **SG0**, **SG1**, **AOI** und **A15I** für die Speicheradressierung durch.

---

Der 256 KByte-Speicher wird in 4 Segmente zu je 64 KByte eingeteilt, die mit den Steuersignalen SG0' und SG1' ausgewählt werden. Die Segmentweiche A42 realisiert die Einstellung der Segmente für den Speicher durch den U 8000.
Die Bildung dieses Auswahlsignals erfolgt durch 3 unterschiedliche Quellen. Die Quellen selbst werden durch die Ausgänge 19 und 21 des Registers A33 (Steuerregister-16) umgeschaltet (AD6* und AD7*), das vom U 8000 geladen werden kann.
1. Auswahl des Segments durch die Steuerleitungen SN0 und SN1.
2. Auswahl des Segments durch die Steuerleitungen INSTR (Programmspeicherzugriff) und N/S (Normal- und Systemmode).
3. Auswahl des Segments durch die Steuerleitungen AD5* und AD6* (A33 Ausgang 17 und 19) - gesteuert durch die CPU U 8000.

**SG-Mode-Weiche A42:**
| AD6* A42/14 | AD7* A42/02 | SG0' | SG1' | |
| :---: | :---: | :---: | :---: | :--- |
| 0 | 0 | AD5* | AD6* | } MODE 0 |
| 1 | 0 | AD5* | AD6* | |
| 0 | 1 | INSTR | N/S | MODE 1 |
| 1 | 1 | SN0 | SN1 | MODE 2 |

---

Segmentauswahl durch die Steuerleitungen aus Tabelle "SG-Mode-Weiche A42":

**MODE 0:**
| AD5* | AD6* | Auswahl |
| :---: | :---: | :--- |
| 0 | 0 | Segment 0 |
| 1 | 0 | Segment 1 |
| 0 | 1 | Segment 2 (gleichberechtigt) |
| 1 | 1 | Segment 3 |

**MODE 1:**
| INSTR | N/S | Auswahl |
| :---: | :---: | :--- |
| 0 | 0 | Segment 0 - System Data |
| 1 | 0 | Segment 1 - System Instruction |
| 0 | 1 | Segment 2 - Normal Data |
| 1 | 1 | Segment 3 - Normal Instruction |

**MODE 2:**
| SN0 | SN1 | Auswahl |
| :---: | :---: | :--- |
| 0 | 0 | Segment 0 |
| 1 | 0 | Segment 1 |
| 0 | 1 | Segment 2 (gleichberechtigt) |
| 1 | 1 | Segment 3 |

Der Adreßumschalter (A41) stellt die Segmentsteuersignale und die Adressen zum Byte- bzw. Worttransfer entsprechend der Betriebsart des Erweiterungsmoduls (8 Bit- oder 16 Bit-MODE) vom jeweiligen Rechner durch.
Zum Byte- und Worttransfer werden die Adressen AB0/AD0* und AB15-8/AB15* benutzt (siehe Speicherdokumentation) -> AOI und A15I.

### 1.5. Attributspeicher

Der Attributspeicher besteht aus dem Schaltkreis A13, dem 16 x 4 Bit-RAM A22 und dem Treiber A12.
Er wird vom U 880 programmiert. Seine Ausgangssignale sind nur wirksam bei Speicherzugriffen für einen 64 KByte-Bereich durch den U 880. Über den Treiber A12 ist der Inhalt des RAM durch den U 880 negiert rücklesbar.

**Programmierung des 16 x 4 Bit-RAM**
Im I/O-Zyklus wird bei der Portadresse MODADR+7 (siehe Punkt III, 1.7.1.) der Eingang W aktiv geschaltet und die Datenbits DB0 ... 3 über den Treiber A12 eingelesen.

U 880:
| AB15 ... AB08 | AB07 ... AB0 |
| :--- | :--- |
| Register A U 880 | Portadresse |
| Seiten-Nr. | MODADR+7 |
| 0 ... FH | x x x x |

| DB7 ... DB4 | DB3 ... DB0 |
| :--- | :--- |
| x x x x | A15-8 A14-8 WE PEN |

**Lesen des 16 x 4 Bit-RAM**
Bei einem Speicherzugriff durch den U 880 auf den EM wird über AB12 ... AB15 der RAM adressiert. Es können in allen 4 Segmenten (Segmentauswahl durch den PIO A32) jedes der 16 Pages (Speicherbereich von 4 KByte) eines 64 KByte-Bereiches programmiert werden.
Durch den Schaltkreis A13 wird die Adresse (^= Seiteninformation) bis zum nächsten Speicherzugriff zwischengespeichert.

---

Die Signale haben folgende Bedeutung:
- **PEN (page enable):** Dieses Signal steuert mit RAMEN und 8/16 den Zugriff auf den Speicherbereich des EM. (A310/12 -> MEN). Bei PEN = 1 wird der Speicherzugriff durch den U 880 erlaubt.
  Gleichzeitig werden die Signale MDO und MEMDI aktiv geschaltet (A311/10 und A17/11) und sperren den 64 KByte-Speicher des K 1520-Systems.
  PEN = 0 -> Sperrung des entsprechenden Speicherbereiches auf dem EM. Der Speicher im K 1520 wird freigegeben.
- **WE (write enable):** Mit diesem Signal kann für jedes Page des EM eine Freigabe oder Sperre des Speichers bei Schreibzyklen programmiert werden (Schreibschutz).
  WE = 0 -> über A26/06 wird die Bildung des Signals WRI = aktiv verhindert.
- **A14-8, A15-8:** Sie ersetzen die Adreßbits AB14 und AB15.
  Die logische Adresse des U 880 kann durch Bildung einer physischen Adresse für den Speicher des EM in einen günstigen Speicherbereich transformiert werden. Das kann nur in Sprüngen von 16 KByte geschehen.

### 1.6. Steuerregister

Die Steuer- bzw. Kommunikationsregister erfüllen die Funktion des Daten- bzw. Statusaustausches zwischen dem U 8000 und dem MRS K 1520.
Jeder Prozessor besitzt dafür zwei 8 Bit-Register.
Der AD-Bus des U 8000 beschreibt die beiden Register
- A35 (Status-16-Register) mit dem high-Teil des AD-Busses
- A33 (Steuer-16-Register) mit dem low-Teil des AD-Busses.
Sie sind nicht rücklesbar.
Adressiert werden die Register über die STB-Eingänge nach der Bedingung
STB = DS + R/W + AD7 + E/A .
Das Register A35 kann durch das Signal READ Status-16 (MODADR + 6) gelesen werden. Das Byte wird über den Treiber A11 direkt auf den K 1520-Bus geschaltet.
Das Register A33 wird durch RESET OUT beim Einschalten der Anlage (A33/14) in Grundstellung gesetzt.
Die Bits dieses Registers haben die Bedeutung:
- Bit 0: PIOA-0 } zum PIO A32; Bedeutung wird durch 
- Bit 1: PIOA-1 } Software festgelegt
- Bit 2: PIOA-2 }
- Bit 3: Freigabe für Einzelbefehlsabarbeitung
- Bit 4: INT-16 INT-Auslösung über PIO
- Bit 5: AD5* } 
- Bit 6: AD6* } Segmentmodefestlegung für Speicherzugriff
- Bit 7: AD7* }

Vom K 1520 werden die Register:
- A36 (Status-8-Register) mit MODADR + 4 } nicht rücklesbar beschrieben
- A34 (Vektor-8-Register) mit MODADR + 5 } (siehe I/O-Decoder).

Ist der Vektor ins Register A34 geladen, liegt Ausgang INT auf low. Er löst einen Vektorinterrupt des U 8000 (VI) aus. Die Ausgabe des Vektors wird durch den U 8000 über den PIO Port A Bit 3 vor dem erneuten Beschreiben des Registers überprüft. Damit ist eine interruptgesteuerte Unterbrechung des U 8000 vom K 1520 möglich. Im VI-Bestätigungszyklus wird der Vektor auf den low-Teil des AD-Busses des U 8000 gelesen (READ VEKTOR auf A34/13). Der high-Teil wird aus dem Status-8-Register gelesen (READ STATUS = 0 - A47/04 durch READ VEKTOR = 1).

---

### 1.7. Anpassung des EM an den K 1520-Bus

#### 1.7.1. I/O-Decoder

**Beschreibung der Schaltung (Abb. 6 I/O-Decoder):**
- Die Schaltung dient der Adressdekodierung für die I/O-Ports.
- Die Eingangsadressen **AB0..7** und Steuersignale (**M1/RST**, **IORQ***) werden durch Decoder-ICs (**A14**, **A24**) verarbeitet.
- Über Wickelbrückenfelder (**X10**, **X11**) kann die Basisadresse eingestellt werden.
- Dekodierte Signale aktivieren über Logikgatter (**A15**, **A16**, **A25**, **A27**, **A23**, **A21**) verschiedene Steuerausgänge wie **CS PIO**, **STB STATUS-8 'AC'**, **STB VEKTOR 'AD'**, **READ STATUS-16**, **W A22** (Write Attributspeicher) und **DIENA12** (Enable Treiber A12).

---

Der I/O-Decoder steuert den Ein-/Ausgabeverkehr des U 880-Systems. Von den 256 vorhandenen I/O-Portadressen belegt der EM 8 untereinanderliegende Adressen, die über die Wickelbrücken X10 und X11 einzustellen sind.
Es sind die Toradressen A8H ... AFH mit folgender Bedeutung:

| Portadresse | Funktion | |
| :--- | :--- | :--- |
| MODADR + 0 | A8H | Tor A Daten } |
| MODADR + 1 | A9H | Tor B Daten } PIO |
| MODADR + 2 | AAH | Tor A Control } |
| MODADR + 3 | ABH | Tor B Control } |
| MODADR + 4 | ACH | Status-8-Register schreiben |
| MODADR + 5 | ADH | Status-8-Register schreiben |
| MODADR + 6 | AEH | Status-16-Register lesen |
| MODADR + 7 | AFH | Attributspeicher schreiben und negiert lesen |

Um die genannten Portadressen decodieren zu können, werden beim A 5120.16 auf der Steuerkarte folgende Brücken gewickelt:
X10: 1 nach 2; 3 nach 6; 4 nach 5     und     X11: 3 nach 9

#### 1.7.2. Steuer-PIO A32

**Datenbustreiber**
Der Datenbustreiber A11 ist nur für den I/O-Verkehr zwischen U 880 und PIO des EM vorgesehen. Die Richtungsumschaltung wird durch die Bedingungen
- I/O-Lesezyklus
- Interruptbestätigungszyklus
gesteuert.

---

**Steuer-PIO**
Der PIO A32 ist in der Interruptprioritätenkette des K 1520 eingebunden und wird vom U 880 programmiert.
Portadressen: MODADR ... MODADR3 (A8H ... ABH) - siehe Punkt 1.7.1.
Beide Tore arbeiten im Bitmode. Interrupt lösen die Eingänge A4 (INT-16) und B7 (PER) aus. Die Ports sind wie folgt belegt:

| Bit | Port A | Port B |
| :---: | :--- | :--- |
| 0 | I PIOA-0 | O SG0P |
| 1 | I PIOA-1 | O SG1P |
| 2 | I PIOA-2 | O RAMEN |
| 3 | I VI | O STOP |
| 4 | I INT-16 | O RESET 16 |
| 5 | I N/S | O TRQ8 |
| 6 | I 8/16 | O PR |
| 7 | I TREN | I PER |

I: Eingabebit / O: Ausgabebit

- **PIOA-0 bis PIOA-2:** Vom Steuer-16 Register A33 (U 8000). Bits sind durch Software abfragbar (können auch als Interruptquellen benutzt werden).
- **VI:** Abfrage des Steuersignals INT vom Vektor-8-Register A34 bei Auslösung eines VI durch den U 8000. Im Register A33 wurde der INT-Vektor eingeschrieben. Die Leitung wird vor dem Einschreiben eines erneuten Vektors in das Register überprüft. VI = low heißt, vektorisierte Interruptanforderung durch den U 8000 wurde noch nicht bearbeitet (Interruptvektor wurde noch nicht gelesen).
- **INT-16:** Löst Interrupt beim U 880 aus (Ausgabe des Speichers an den U 880 oder Lesen des Status-16-Registers); INT-16 = low wird ins Bit 5 des Registers A33 eingeschrieben.
- **N/S:** Abfragesignal des U 880, ob der U 8000 im Normal- (high) oder Segmentmode (low) arbeitet.
- **8/16:** Abfragesignal des U 880, ob 8 Bit- oder 16 Bit-Mode des Systems eingeschaltet ist.
- **TREN:** Abfragesignal des U 880, ob der U 8000 seinen Speicherzugriff abgegeben hat (µ0-Ausgang des U 8000).
- **SG0P, SG1P:** Steuersignal für die Segmentierung des 256 KByte-RAM in 4 x 64 KByte Segmente (siehe Speicher-STE).
- **RAMEN:** Schaltet den Zugriff des U 880 auf den Speicher des EM ein.
- **STOP:** Steuert den STOP-Eingang des U 8000. Damit kann eine Einzelschrittsteuerung vom U 880 aus durchgeführt werden.
- **RESET 16:** Rücksetzen des 16 Bit-Mode. Das FF A29 wird gesetzt.
- **TRQ8:** Anforderung des 8 Bit-Mode vom U 880 (an µI-Eingang des U 8000).
- **PR:** Rücksetzen des Paritäts-FF auf der Speicher-STE bei aufgetretenem Paritätsfehler (PER = low).
- **PER:** Interruptauslösung zum U 880-System bei Paritätsfehler während des Speicherzugriffs.

Die unnegiert dargestellten Signale des PIO sind high aktiv, die negierten low aktiv.

---

#### 1.7.3. Betriebsartensteuerung

Die Zugriffssteuerung legt das Zugriffsrecht der Prozessoren U 880 und U 8000 auf den Speicher des EM fest. Das Signal 8/16 (FF A29/09) übernimmt dabei die Steuerung.

**8 Bit-Mode:**
Nach dem Einschalten ist der PIO A32 hochohmig. Ausgang B4 ist über R4:2 high. Das FF A29 wird gesetzt, die LED V2 leuchtet und zeigt das Einschalten des 8 Bit-Mode durch RESET 16 an. 8/16 ist high. Dieser Zustand ist vom U 880 über den PIO A32 Eingang B8 abfragbar. Gleichzeitig befindet sich der U 8000 im RESET durch RST16 (A55/14).
Ist der U 8000 aktiv muß der U 880 über TRQ8 = 0 (A32/32) den 8 Bit-Mode anfordern. Über µI = 0 am U 8000 wird µ0 = '0' und TREN = 1 (A38/12). Das bedeutet Freigabe des Nands A212/11 und Bildung von BUSRQ = 0 am U 8000, was gleichbedeutend ist mit Busanforderung durch den U 880. Der U 8000 quittiert die Anforderung mit BUSAK = 0 (A37/29, (24)). In das FF A29 wird high eingeschrieben, d. h. Umschaltung auf den 8 Bit-Mode (8/16 = 1) im nächsten M1-Zyklus des U 880.

**16 Bit-Mode:**
Nach Aufheben von RESET 16 oder TRQ8 inaktiv ist der 16 Bit-Mode eingeschaltet (U 8000: BUSRQ = 1; µI = 1).
Der U 8000 hat das Zugriffsrecht. Der U 880 arbeitet in seinem Systemspeicher weiter, kann aber nicht auf den RAM des EM zugreifen.

Die Umschaltung der Prozessoren ist nur durch die Software zu steuern. Die Initialisierung im Einschaltmoment erfolgt durch den U 880 im 8 Bit-Mode, der durch RESET 16 automatisch zugeschaltet ist.
Die Abgabe des Speicherzugriffs vom U 8000 (Anforderung der Übernahme vom U 880) wird über den PIO A32/A4 durch INT-16 dem U 880 gemeldet. Der nach der INT-Quittung folgende Ablauf der Umschaltung entspricht der 8 Bit-Mode-Anforderung.

**Beschreibung der Schaltung (Abb. 7 Betriebsartensteuerung):**
- Die Schaltung steuert die Bushoheit.
- Der **PIO A32** gibt über Ausgänge **B4** (**RESET 16**) und **B5** (**TRQ8**) Befehle an das Logiknetzwerk weiter.
- Das Gatter **A31** verarbeitet das Resetsignal, unterstützt durch ein Pull-up-Netzwerk (**5P**, **R4:2**).
- Das zentrale Steuerelement ist das Flip-Flop **A29**, dessen Ausgang (Pin 09) das Signal **8/16** für das Gesamtsystem bereitstellt.
- Die Interaktion mit der CPU U 8001/2 erfolgt über Signale wie **BUSAK**, **BUSRQ**, **µ0** (über Gatter **A311**) und **µI**.
- Die Signale **TREN** und **M1 RST** werden über Gatter wie **A310** und **A212** verknüpft, um den Umschaltzeitpunkt zu synchronisieren.

---

### 1.8. RDY-Bildung

Das Signal RDY wird aktiviert bei:
- einem freigegebenen Speicherzugriff auf den Speicher des EM durch die Bedingungen
  MEN = 0 (A310/12) - siehe Zugriffssteuerung
  MREQ = 0
  RFSH = 1
  MDI = 1 - siehe Speicherprioritätensteuerung
  die am Nand A26/12 verknüpft werden und das Speicherbereitschaftssignal MRDY aktiv bilden.
  MEN ist aktiv, wenn bei einem erlaubten Speicherzugriff (RAMEN = 0) im 8 Bit-Mode (8/16 = 1) der Seitenzugriff durch den Attributspeicher (PEN = 1) erlaubt ist (A310/12).
- einem I/O-Zugriff auf den EM (Portadressen A8H ... AFH), (A14/10 = 0 -> A15/08 -> A16/06)
  Am Nand A16/06 wird das I/O-Freigabesignal mit IORQ verknüpft zu IORDY.

Die beiden Signale MRDY und IORDY bilden RDY (A18/08 -> A17/03), das auf den Systembus des K 1520 geführt ist und vom U 880 über den Betriebssystem-PIO abfragbar ist.

### 1.9. Speicherprioritätensteuerung

Der Speicher des EM kann in die zusätzlich im K 1520-System vorhandene Speicherprioritätenkette eingeordnet werden. Die entsprechenden Signale sind:
- **MDI** (memory disable in) und
- **MDO** (memory disable out).
MDI = 0 sperrt den Speicher des EM, MDO wird low. MEMDI bleibt inaktiv (A311/10; A17/11). MDI ist, wenn nicht beschaltet, inaktiv. Damit besitzt der EM höhere Priorität. Alle anderen Speichereinheiten sind dann mit MEMDI abschaltbar (z. B. der 64 KByte-Speicher des K 1520-systems). Bei einem erlaubten I/O-Speicherzugriff auf den Speicher des EM wird MDO und MEMDI aktiv.

### 1.10. Adreß-Datenbustreiber

Die bidirektionalen Treiber A52 und A43 koppeln den Adreß-Datenbus des U 8000 mit dem Speicher des EM. Sie werden mit dem Signal 8/16 aktiviert, wenn im 16 Bit-Mode gearbeitet wird. Richtungsgesteuert sind die Treiber durch die Steuersignale des U 8000 DS * R/W (A39/03), MREQ (^= MDO = 0 -> Speicherlesen 16 Bit). Die Brücke W4:1 ist geschlossen.

### 1.11. Eigenrefreshgenerator

Das Refresh des Speichers des EM erfolgt durch die CPU, die aktiv geschaltet ist (8/16).
Im Normalfall ist der Eigenrefreshgenerator inaktiv, d. h. das Refreshumlaufsignal RU (siehe Speicherkarte) steuert einen Monoflop (A114) in einer vorgeschriebenen Zeit. Wird diese Zeit überschritten, erzeugt der Eigenrefreshgenerator A113/08/09 Refreshimpulse mit doppelter Taktlänge.
Ins FF A113/05 wird high eingeschrieben. Das so gebildete Signal ERF gibt das Nand A211/12 frei und damit die ERFI-Impulse für den Speicher des EM. Das erfolgt solange, bis ein kompletter RFSH-Adreßzyklus abgearbeitet ist und RU wieder neu triggert.
Durch das zweite Monoflop A114 über Nand A211/06 wird WAITI gebildet. Aus diesem Steuersignal entsteht
- WAIT 16 A27/12 für U 8000
- WAIT A17/06 für U 880
Beide CPU's befinden sich im WAIT-Zustand.

---

### 1.12. Einzelbefehlsabarbeitung

**Beschreibung der Schaltung (Abb. 8 Einzelbefehlsabarbeitung):**
- Die Schaltung ermöglicht das Debugging durch Einzelschrittbetrieb.
- Eingänge wie **DS**, **R/W** und **STATUS 6** (von der CPU) sowie das Signal von Register **A33/10** werden in einem Logikbaustein (**A54**) verknüpft.
- Ein Zählerbaustein (**A53**, Typ CT 2) ist über eine Programmierbrücke (**X12**) so konfiguriert, dass er die Instruktionszyklen zählt.
- Nach Ablauf der Zählung wird am Pin 07 das Signal **NVI** (Non-vectored Interrupt) an den **U 8000** ausgegeben, um den Trace-Interrupt auszulösen.
- Der Signalzustand **DS STATUS 9** wird zur Synchronisation des Zählers verwendet.

---

Die Einzelbefehlsabarbeitung unterstützt im Falle der Programmentwicklung bzw. beim Einsatz des EM in einem Entwicklungssystem die TRACE-Funktion eines Debuggers. Sie ermöglicht die Programmunterbrechung nach jedem Befehl, der nach einer RETURN-Anweisung abgearbeitet wird. Die Freigabe dieser Baugruppe erfolgt über den Ausgang 10 des Steuer-16-Registers A33. Dieser Ausgang muß vor der Abarbeitung eines RET-Befehls, also im Debuggerprogramm wieder rückgesetzt werden. Die Freigabe setzt voraus, daß in einer vorher geladenen speziellen Routine der Selbsthaltekreis A54 rückgesetzt wurde.
Erfolgt beim Übergang vom Debugger- in den Anwenderstatus eine Stackoperation (RET-Befehl), wird das mit STATUS 9 angezeigt und mit dem Signal DS getort. Der Zähler zählt rückwärts. Er muß über die Brücke X12 so eingestellt sein, daß entsprechend der Betriebsart und dem eingesetzten Prozessortyp der Ausgang A53/07 nach dem letzten STACK-Zugriff aktiv wird. Im anschließenden Befehlsaufruf wird das Signal NVI = 0 akzeptiert und das Programm verzweigt wieder in den Debuggerstatus. Damit wurde genau ein Anwenderbefehl abgearbeitet. Das Neuladen des Zählers wird in dem NVI-acknowledge-Zyklus (Status 6 und Torsignal DS * R/W) durchgeführt.

## 2. Speicher des Erweiterungsmoduls

### 2.1. Allgemeines

Der Speicher des EM kann wahlweise mit zwei unterschiedlichen Schaltkreistypen bestückt sein
- U 2164 D 20        16 KBit dynamisch RAM
- KM 565 RU 5G       64 KBit dynamisch RAM.

Durch unterschiedliche Bestückungsmöglichkeiten sind die Pins 1, 8, 9 wie folgt belegt:

| | U 256 | U 2164 |
| :--- | :---: | :--- |
| Pin 1 | 5 N | n.c. (ohne Anschluß) |
| Pin 8 | 12 P | 5 P |
| Pin 9 | 5 P | A7 |

Es ergeben sich die zwei Speicherkarten:
- Typ 062-9000
  1.62.519000.4; 083-4-710-093 - Gesamtkapazität 256 KByte
- Typ 062-9001
  1.62.519001.2; 083-4-710-094 - Gesamtkapazität 64 KByte

---

### 2.2. Blockschaltbild

**Beschreibung der Schaltung (Abb. 9 Blockschaltbild Speicher):**
Das Schaltbild zeigt den inneren Aufbau der Speicherkarte.
- Die Karte ist über den **K 1520 - Bus** (Adressen **AB1..13**, Daten **DB0..7**) angebunden.
- Der **DB-Treiber** regelt den bidirektionalen Datenfluss zwischen Bus und interner **Datensteuerung** (Leitungen **DD0..15**, **DI0..15**).
- Die **Adreßbussteuerung** empfängt externe Signale wie **A14-8**, **SG0**, **MREQ 8**, **A15I**, **AS** und bereitet diese für die Multiplexadressierung auf.
- Die **Ablaufsteuerung** generiert zeitrichtig die Signale **CAS**, **RASEN** (RAS-Enable) und **RFSH** (Refresh-Status).
- Ein **RAS Decoder** wertet die Segmentadressen (**SG1**, **A15I**, **B/W**) und den Instruktions-Strobe (**AOI**) aus, um eine der vier Leitungen **RAS0** bis **RAS3** zu aktivieren.
- Die **RAM-Matrix** ist in vier Blöcke unterteilt, jeder adressiert durch ein eigenes RAS-Signal. Sie enthält zudem ein **Paritätsbit** pro Datenwort.
- Der **Paritätscontroller** verarbeitet Fehlersignale (**PER**, **PR**).
- Ein autonomer **RFSH-Zähler** sorgt für den kontinuierlichen Refresh und liefert das Feedbacksignal **RU**.

---

### 2.3. Speichermatrix

Die Speichermatrix besteht aus 36 Schaltkreisen, die in 4 Blöcken zu je 9 Bausteinen eingeteilt ist. 8 Bausteine eines Blockes enthalten die Dateninformation, der 9. speichert das Paritätsbit des entsprechenden Datenbytes.
Die Blockauswahl erfolgt durch die Signale RAS0 ... RAS3, während CAS, WE und die Adreßleitungen A0 ... A7 bzw. A0 ... A6 direkt an alle Bausteine geführt sind.
Durch die Möglichkeit der Byte- oder Wortverarbeitung sind die Datenleitungen byteweise je zwei Blöcken zugeordnet, wobei sich folgende Verteilung der 16 Datenleitungen ergibt:
- **RAS0** AD0 ... AD7 unteres Datenbyte
- **RAS1** AD0 ... AD7 unteres Datenbyte
- **RAS2** AD8 ... AD15 oberes Datenbyte
- **RAS3** AD8 ... AD15 oberes Datenbyte
Im Refreshzyklus sind die Signale RAS0 ... RAS3 gleichzeitig aktiv.

### 2.3.1. Ansteuerung der Speichermatrix 64 KByte

Die 16 KBit-Speicherchips werden über 7 multiplex Adreßeingänge A0 ... A6 angesteuert.
Speicherzugriff vom U 880: Zeilenadresse über den Treiber A15 -> AB1 ... AB7
Spaltenadresse über den Treiber A16 -> AB8 ... AB13
AB14 wird als A14-8 gebildet (A16/07 - s. Attributspeicher auf Steuer-STE).
Die Segmentauswahlleitungen SG0 und SG1 werden nicht benötigt.

### Speicherzugriff vom U 8001/U 8002

Zeilenadresse über Treiber A13 AD1...AD7

Spaltenadresse über Treiber A14 AD8...AD14

In beiden Fälle erfolgt die Blockauswahl durch die Signale AOI und A15I. AOI steuert über den Selbsthaltkreis A33 und A34 die Auswahl der geraden und ungeraden Adreßbytes (RAS0 - RAS1 oder RAS2 - RAS3). A15I unterscheidet die zwei unteren von den zwei oberen Bytes.

# 2.3.2. Ansteuerung der Speichermatrix 256 KByte

Die 64 KBit Speicherchips werden über 8 multiplex AdreBeingänge (A0 ... A7) angesteuert.

Speicherzugriff vom U 880

Zeilenadresse über Treiber A15 AB1...AB7 Die AdreBleitung A7 des RAM-Chips wird mit dem Signal A15I (A15/0) belegt.

Spaltenadresse über Treiber A16 AB8...AB13 A6 wird aus dem Signal A14-8 (A16/7) gebildet A7 wird aus dem Signal SGO (A16/8) gebildet

Die Adreßleitungen A14-8 und A15I beinhalten die Zusatzadreßinformation des Attributspeichers. Die im 8 Bit-Mode verwendeten Segmentleitungen des PIO werden als

SGO für die 8. Adreßleitung der Spaltenadresse

SG1 für die Unterscheidung der zwei unteren von den zwei oberen Bytes verwendet und gehen direkt auf den RAS-Decoder A34/A35.

AOI steuert die Auswahl der geraden oder ungeraden Adressen und damit die Auswahl der entsprechenden Blöcke.

# Speicherzugriff vom U 8000

Die Adreßleitungen AD1 ... AD15 werden über die Treiber A13/A14 an die Speicherchips führt. Die Signale A14-8 und A15I sind unbenutzt. Die Segmentauswahl geschieht hier durch die Segmentleitungen des U 8000 (SG1).

In allen Fällen des Speicherzugriffs ist das Steuersignal B/W mit AOI verknüpf, d, h, bei Wortzugriffen wird AOI durch das Signal B/W gespehtt und zwei RAS-Signale werden aktiv geschaltet. Das entspricht der Datenverarbeitungsbreite von 16 Bit.

# 2.4.RAS-Decoder

Die Anzahl der zu aktivierenden RAS-Signale wird je nach Art des Speicherzugriffs im RAS-Decoder bestimmt.

<table><tr><td></td><td>RFIRFSH</td><td>B/W</td><td>AOI</td><td>A15ISG1</td><td>RASO</td><td>RAS1</td><td>RAS2</td><td>RAS3</td></tr><tr><td>RFSH-Zyklus</td><td>0</td><td>x</td><td>x</td><td>x</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td rowspan="2">Worttransfer</td><td>1</td><td>0</td><td>x</td><td>0</td><td>(0)</td><td>1</td><td>(0)</td><td>1</td></tr><tr><td>1</td><td>0</td><td>x</td><td>1</td><td>1</td><td>(0)</td><td>1</td><td>(0)</td></tr><tr><td rowspan="4">Bytetransfer</td><td>1</td><td>1</td><td>1</td><td>0</td><td>(0)</td><td>1</td><td>1</td><td>1</td></tr><tr><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>(0)</td><td>1</td><td>1</td></tr><tr><td>1</td><td>1</td><td>0</td><td>0</td><td>1</td><td>1</td><td>(0)</td><td>1</td></tr><tr><td>1</td><td>1</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>(0)</td></tr><tr><td>kein Zugriff</td><td>1</td><td>x</td><td>x</td><td>x</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>


# 256 KByte Speichermatrix

**A1-8 &nbsp;&nbsp;&nbsp; SG0 → A7**

### Speichermatrix-Layout

| RAS-Leitung | A2-Eingänge (Chip-Nummern) | SG0-Zustand |
| :--- | :--- | :--- |
| **RAS0** | 32 &nbsp; 31 &nbsp; 30 &nbsp; 29 &nbsp; 28 &nbsp; 27 &nbsp; 26 &nbsp; 25 | SG0 = 0 <br> SG0 = 1 |
| **RAS1** | 24 &nbsp; 23 &nbsp; 22 &nbsp; 21 &nbsp; 20 &nbsp; 19 &nbsp; 18 &nbsp; 17 | SG0 = 0 <br> SG0 = 1 |
| **RAS2** | 16 &nbsp; 15 &nbsp; 14 &nbsp; 13 &nbsp; 12 &nbsp; 11 &nbsp; 10 &nbsp; 9 | SG0 = 0 <br> SG0 = 1 |
| **RAS3** | 8 &nbsp;&nbsp; 7 &nbsp;&nbsp; 6 &nbsp;&nbsp; 5 &nbsp;&nbsp; 4 &nbsp;&nbsp; 3 &nbsp;&nbsp; 2 &nbsp;&nbsp; 1 | SG0 = 0 <br> SG0 = 1 |

---

## 8 Bit-Betrieb

### Adressübersicht

| Seg. Nr. | Adresse hex. | Adressierungs-Details |
| :---: | :--- | :--- |
| 0 | 0001, 0003, 0005, ..., FFFF | **SG1 = 0** <br> **A0 = 1** <br> **ungerade** |
| 1 | 0001, 0003, 0005, ..., FFFF | |
| 2 | 0001, 0003, 0005, ..., FFFF | **SG1 = 1** <br> **A0 = 1** <br> **ungerade** |
| 3 | 0001, 0003, 0005, ..., FFFF | |
| 0 | 0000, 0002, 0004, ..., FFFE | **SG1 = 1** <br> **A0 = 0** <br> **gerade** |
| 1 | 0000, 0002, 0004, ..., FFFE | |
| 2 | 0000, 0002, 0004, ..., FFFE | **SG1 = 1** <br> **A0 = 0** <br> **gerade** |
| 3 | 0000, 0002, 0004, ..., FFFE | |

**Abb. 11**
**Adreßübersicht 256 KByte-Matrix**


# 2.5. Ablaufsteuerung

Die Aufgabe dieser Baugruppe ist es, die genauen Zeitabläufe der dynamischen RAM-Bauelemente bei einem Speicher- bzw. Refreshzugriff zu steuern und die Treiber zur Adreß- bzw. Datendurchschaltung zeitrichtig zu schalten.

### Die Steuersignale sind:
*   **MREQ-8** (Low-aktiv)
*   **MREQ-16** (Low-aktiv)
*   **RFI** (Low-aktiv)
*   **RDI** (Low-aktiv)
*   **WRI** (Low-aktiv)

### Funktionsbeschreibung
Die Steuerung des Speicherzugriffs geschieht durch die Signale **MREQ-8** bzw. **MREQ-16** (A22/08).

*   **RAS-Bildung:** Freigabe der Nands A34/12, A35/06/08/12 für die Bildung des Zeilenauswahlimpulses **RAS0 ... RAS3**.
*   **Zeilenadresse:** Die Zeilenadresse, die über die Register A13 (U 880 über Systembus) oder A15 (U 8000 über Steckverbinder X4) an die Speicher geschaltet wird, wird durch das Signal **8/16** über die Mehrfachnands A32/06 und A32/08 (**CS-RA-8** für A15 und **CS-RA-16** für Treiber A13) nach Freigabe durch **MREQ-8** oder **MREQ-16** (A22/08) gesteuert.
*   **Spaltenadresse:** Bereitstellung der Spaltenadresse über die Register A14 oder A16 durch die Signale **CS-CA-8** bzw. **CS-CA-16**, die durch **MREQ-8** bzw. **MREQ-16** über A22/08 - A22/03 oder A22/06 gesteuert wird.
*   **CAS-Aktivierung:** Die Spaltenadresse ist nach dem verzögerten (R8/C1) Aktivieren vom Spaltenauswahlsignal **CAS = low** (A54/06, A54/08, A45/04, A54/12) wirksam.

Die U 8000-Adresse wird mit dem Signal **AS** gelatcht (siehe Steuerkarte). Der Ablauf ergibt sich entsprechend den geforderten Zeitabläufen an den dynamischen Speichern (Abb. 12).

Die Richtungssteuerung der Datentreiber A55 bis A58 übernimmt das Signal **RDI**. Die Funktion "Lesen oder Schreiben" der Speicher ist durch **WRI** gesteuert, das über Nor A54/02 die **WE**-Eingänge der Speicherchips belegt.

---

## Verbale Beschreibung der Schaltung (Logikplan)

Das dargestellte Blockschaltbild visualisiert die sequentielle Steuerung für den Zugriff auf den dynamischen RAM (DRAM). Die Schaltung stellt sicher, dass die Adresssignale und Steuersignale (RAS/CAS) in der exakt vorgeschriebenen zeitlichen Abfolge eintreffen.

### 1. Initialisierung (Eingangsstufe)
Der Vorgang startet mit den Signalen **MREQ8** oder **MREQ16**. Diese werden im Gatter **A22** verknüpft. Sobald eine Speicheranforderung eingeht, wird die gesamte Steuerkette in Gang gesetzt.

### 2. Zeilen-Pfad (Row Address)
*   **OE-RA (Output Enable Row Address):** Unmittelbar nach der Anforderung wird über das Gatter **A32** die Zeilenadresse auf den Bus des Speichers geschaltet.
*   **RAS-Generierung:** Gleichzeitig wird über die untere Gatterkette (**A34/35** und **A36**) das Signal **RAS0...3** erzeugt. Das Signal **RFI** (Refresh Interrupt) wirkt hier ein, um Refresh-Zyklen gegenüber normalen Zugriffen zu koordinieren.

### 3. Verzögerungsstufen (V1 und V2)
Da DRAMs erst die Zeilenadresse und danach die Spaltenadresse benötigen (Multiplex-Verfahren), enthält die Schaltung zwei Verzögerungsglieder:
*   **V1:** Verzögert das Signal so lange, bis die Zeilenadresse sicher vom Speicher übernommen wurde. Erst dann wird die Spaltenadresse freigeschaltet.
*   **V2:** Sorgt für die notwendige Haltezeit, bevor das finale CAS-Signal ausgelöst wird.

### 4. Spalten-Pfad (Column Address)
*   **OE-CA (Output Enable Column Address):** Nach der Verzögerung durch **V1** wird die Zeilenadresse abgeschaltet und die Spaltenadresse über **A22/A43** aktiviert.
*   **CAS-Generierung:** Nach einer weiteren Verzögerung durch **V2** und die Gatterkette **A54/A45** wird der **CAS**-Impuls (Column Address Strobe) erzeugt. Dieser signalisiert dem Speicherchip, dass die nun anliegende Adresse die Spalte ist.

### Zusammenfassung
Die Schaltung arbeitet als elektromechanisches "Schaltwerk":
1. **Anfrage** kommt rein.
2. **Zeilenadresse** raus + **RAS** Signal.
3. **Warten** (V1).
4. **Spaltenadresse** raus.
5. **Warten** (V2).
6. **CAS** Signal zur Bestätigung.

---
*Seite 21*

# 2.6. Refreshzähler

Die Speichersteckeinheit besitzt einen eigenen RFSH-Zähler, um auch bei einem Betriebsartenwechsel (8 Bit- und 16 Bit-Mode) immer einen fortlaufenden Refresh-Adressen-Umlauf zu gewährleisten. Die RFSH-Adressen der CPU U 880 und U 8000 bleiben unberücksichtigt.
Das interne Refreshsignal **RFI** taktiert den Zähler A24/A25, der wiederum mit dem Umlaufkontrollsignal **RU** die RFSH-Umläufe überwacht und zum Eigenrefreshgenerator der Steuerkarte meldet. Wenn alle Zellen aufgefrischt sind, der Adreßzähler also umgelaufen ist, wird **RU** die Zeitüberwachung im Eigenrefreshgenerator rücksetzen.
Ist das Signal **RU** aktiv, wird der Zähler A24/A25 in Grundstellung rückgesetzt.
Über den Treiber A26 werden 7 Bit als RFSH-Adresse an die Speicherchips geführt. Sie belegen den Adreßbus, wenn **RFI** = low ist. Das 8. Bit (A26/12) wird mit dem Signal **RFI** am A22/06 verknüpft und gibt die Nands A36 zur Bildung der Zeilenansteuersignale **RAS0 ... RAS3** frei. Alle 4 Signale werden gleichzeitig beim RFSH-Zyklus aktiv.

# 2.7. Paritätssteuerung

Zur Paritätskontrolle wird in einem zusätzlichen Speicherelement für jedes Datenbyte ein Paritätsbit als 9. Bit mit gespeichert (für jedes Wort 2 Paritätsbit). Das erfolgt bei jedem Schreibzyklus.
Bei jedem Lesezyklus wird das 9. Bit aus dem RAM gelesen und steuert über die Nands A43/08, A43/11 und Nors A44/08, A44/10 die Paritätsprüfer A60 (unteres Datenbyte) bzw. A61 (oberes Datenbyte) über die Eingänge W0 und W1. Gleichzeitig wird beim Lesevorgang in den Bausteinen A60/A61 erneut die Parität kontrolliert, da das gelesene Datenbyte an den Eingängen liegt. Die Ausgänge sind im Fehlerfall "low". Dieses Signal, verknüpft mit **AOI** (A45/01) bzw. **AOI** (A45/13) wird ins FF A46/09 bei **RDI** = 1 eingeschrieben. Die LED V1 leuchtet, das Signal **PER** = 0. Es führt zum Interrupt des Prozessors (**NMI** = 0 am U 8000).
Gelöscht wird das FF durch das Signal **PR** = 0 über den Setzeingang. V1 verlischt.

---

### Abb. 12: Prinzipschaltung Ablaufsteuerung (Timing-Diagramm)

**Verbale Beschreibung des Zeitablaufs:**
Das Diagramm zeigt die zeitliche Abfolge der Steuersignale für einen Speicherzugriff:
1.  **Start:** Der Zyklus beginnt mit der fallenden Flanke von **MREQ-16** oder **MREQ-8**.
2.  **Zeilenadresse:** Nahezu zeitgleich wird die Zeilenadresse (**OE RA-8** oder **RA-16**) aktiv geschaltet.
3.  **RAS:** Kurz darauf fällt das Zeilen-Strobe-Signal (**RASn**) auf "low".
4.  **Umschaltung (V1):** Nach einer Verzögerung von **> 20ns** (V1) wird die Zeilenadresse abgeschaltet und die Spaltenadresse (**OE CA-16** oder **CA-8**) aktiviert.
5.  **CAS (V2):** Nach einer Gesamtverzögerung von **> 50ns** (V2) ab Beginn wird das Spalten-Strobe-Signal (**CAS**) aktiv geschaltet.

---
*Seite 22*

\newpage

# IV. Kurzzeichenübersicht (EM-spezifische Signale)

| Signal | Bedeutung | English Meaning |
| :--- | :--- | :--- |
| **AOI** | Adreßleitung A0 intern | |
| **A15I** | Adreßleitung A15 intern | |
| **AS** | Gültigkeitssignal für U 8000 Adreßbus | address strobe |
| **AD0 ... AD15** | Adreßbus U 8000 | |
| **A14-8** | Adreßleitung 14 aus Attributspeicher | |
| **B/W** | Byte oder Wort | |
| **CAS** | Spaltenansteuersignal | column-address strobe |
| **CS-CA-8** | Freigabe Register für Spaltenadresse 8 Bit | |
| **CS-CA-16** | Freigabe Register für Spaltenadresse 16 Bit | |
| **CS-RA-8** | Freigabe Register für Zeilenadresse 8 Bit | |
| **CS-RA-16** | Freigabe Register für Zeilenadresse 16 Bit | |
| **DS** | Gültigkeitssignal für Schreib-/Lesedaten | data strobe |
| **ERF** | Eigenrefresh | |
| **INSTRn** | Operationscodeaufruf n-tes Wort | instruction n |
| **INSTR1** | Operationscodeaufruf 1. Wort | instruction 1 |
| **I/O** | Ein-/Ausgabestatus | |
| **IORDY** | I/O-Bereitschaft | I/O ready |
| **MRDY** | Speicherbereitschaft | memory ready |
| **MEN** | Speicherzugriffserlaubnis | memory enable |
| **MDI** | Speichersperre – Eingang | memory disable in |
| **MDO** | Speichersperre – Ausgang | memory disable out |
| **MRD-8** | Speicherlesen des 8 Bit-Systems | memory read 8 bit |
| **MRD-16** | Speicherlesen des 16 Bit-Systems | memory read 16 bit |
| **MREQ-8** | Speicheranforderung 8 Bit | memory request 8 bit |
| **MREQ-16** | Speicheranforderung 16 Bit | memory request 16 bit |
| **NMI** | nichtmaskierter Interrupt | |
| **NVI** | nichtvektorisierter Interrupt | |
| **N/S** | Betriebsart Normal/System | |
| **PR** | Paritätsfehler rücksetzen | parity error reset |
| **PER** | Paritätsfehler | parity error |
| **PEN** | Seitenauswahl | page enable |
| **RAMEN** | RAM-Auswahl | RAM enable |
| **RAS** | Zeilenansteuersignal | row address strobe |
| **RDI** | internes Lesesignal | read intern |
| **RFU** | Refreshumlaufsignal | |
| **RFI** | interner Refreshimpuls | |
| **R/W** | Lesen/Schreiben | read/write |
| **RESET 16** | Rücksetzen U 8000 | |
| **SG0** | Segment 0 | |
| **SG1** | Segment 1 | |
| **Stack** | Stackoperation | |
| **TREN** | Übertragungsfreigabe | transfer enable |
| **TRQ8** | Übertragungsanforderung | transfer request |
| **VI** | Vektorinterrupt | |
| **WAIT16** | WAIT-Anforderung U 8000 | |
| **WRI** | internes Schreibsignal | write intern |
| **8/16** | 8-/16-Bit-Status | |

---
*Seite 23*

