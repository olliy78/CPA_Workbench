; fw_march.s - March-C DRAM-Test mit Segment-Parameter
;
; Z8001-Firmware fuer EM256 Testprogramm
; Testet den DRAM im angegebenen Segment per segmentierter Adressierung.
;
; March-C Algorithmus (5 Phasen):
;   Phase 1: Aufwaerts alle Worte mit 0x0000 fuellen
;   Phase 2: Aufwaerts lesen (soll 0x0000), dann 0xFFFF schreiben
;   Phase 3: Aufwaerts lesen (soll 0xFFFF)
;   Phase 4: Abwaerts lesen (soll 0xFFFF), dann 0x0000 schreiben
;   Phase 5: Abwaerts lesen (soll 0x0000)
;
; Erkennt: Stuck-At-Fehler, Koppelfehler zwischen benachbarten Zellen
;
; Eingabe (Mailbox):
;   MB_PARAM1 (0x000A) = Ziel-Segment im Z8001-Format:
;     0x0000=Seg0, 0x0100=Seg1, 0x0200=Seg2, 0x0300=Seg3
;
; Testbereich:
;   Segment 0: 0x0100 bis 0xFFFE (0x0000-0x00FF = Code+Mailbox)
;   Segment 1-3: 0x0000 bis 0xFFFE (komplett, 64 KB)
;
; Segmentierte Adressierung:
;   RR8 = {R8=Segment, R9=Offset} -> LD @RR8, Rn adressiert
;   das Ziel-Segment, waehrend Code+Mailbox in Segment 0 bleiben.
;   Mailbox-Zugriff erfolgt ueber ungerade Register (R7, R11)
;   im non-segmented Modus (= immer Segment 0).
;
; Mailbox-Ergebnis:
;   STATUS  = 0x0001 (OK) oder 0x0002 (FEHLER)
;   RESULT1 = Sollwert bei Fehler
;   RESULT2 = Istwert bei Fehler
;   RESULT3 = Fehleradresse (Offset im Segment)
;
; (c) 2026 Olaf Krieger - MIT Lizenz

    ORG  0x0000

    ; Z8001 Reset-Vektor (FCW=0xC000: Segmented + System Mode)
    DW   0x0000, 0xC000, 0x0000, 0x0040

    ; Mailbox (0x0008 - 0x003F)
    DS   56

; === Code ab 0x0040 ===

START:
    LD   R15, #0x00FE       ; SP knapp unter Testbereich

    ; Segment-Parameter aus Mailbox lesen (non-segmented, Segment 0)
    LD   R11, #0x000A       ; R11 ungerade -> non-segmented -> liest aus Seg 0
    LD   R8, @R11           ; R8 = Ziel-Segment (z.B. 0x0000, 0x0100, ...)

    ; Startadresse bestimmen
    CP   R8, #0x0000        ; Segment 0?
    JR   NE, OTHER_SEG
    LD   R3, #0x0100        ; Seg 0: ab 0x0100 (Code+Mailbox ueberspringen)
    JR   T, SETUP_OK
OTHER_SEG:
    LD   R3, #0x0000        ; Seg 1-3: ab 0x0000 (komplett)
SETUP_OK:
    LD   R4, #0xFFFE        ; Endadresse (letztes Wort)

    ; Register-Konventionen:
    ; R1  = Testmuster (Soll-Wert)
    ; RR8 = Segmentierte Adresse (R8=Segment, R9=Offset)
    ;        R8 bleibt konstant (Ziel-Segment)
    ;        R9 wird als Offset-Zaehler verwendet
    ; R3  = Startoffset
    ; R4  = Endoffset (0xFFFE)
    ; R5  = gelesener Wert
    ; R6  = Hilfregister

; ---------------------------------------------------------------
; Phase 1: Aufwaerts mit 0x0000 fuellen
; ---------------------------------------------------------------
    LD   R1, #0x0000
    LD   R9, R3
P1_LOOP:
    LD   @RR8, R1
    CP   R9, R4
    JR   EQ, P1_DONE
    INC  R9, #2
    JR   T, P1_LOOP
P1_DONE:

; ---------------------------------------------------------------
; Phase 2: Aufwaerts lesen 0x0000, schreiben 0xFFFF
; ---------------------------------------------------------------
    LD   R1, #0x0000        ; Erwartung
    LD   R6, #0xFFFF        ; neues Muster
    LD   R9, R3
P2_LOOP:
    LD   R5, @RR8
    CP   R5, R1
    JR   NZ, FAIL
    LD   @RR8, R6
    CP   R9, R4
    JR   EQ, P2_DONE
    INC  R9, #2
    JR   T, P2_LOOP
P2_DONE:

; ---------------------------------------------------------------
; Phase 3: Aufwaerts lesen 0xFFFF
; ---------------------------------------------------------------
    LD   R1, #0xFFFF
    LD   R9, R3
P3_LOOP:
    LD   R5, @RR8
    CP   R5, R1
    JR   NZ, FAIL
    CP   R9, R4
    JR   EQ, P3_DONE
    INC  R9, #2
    JR   T, P3_LOOP
P3_DONE:

; ---------------------------------------------------------------
; Phase 4: Abwaerts lesen 0xFFFF, schreiben 0x0000
; ---------------------------------------------------------------
    LD   R1, #0xFFFF
    LD   R6, #0x0000
    LD   R9, R4             ; von Ende
P4_LOOP:
    LD   R5, @RR8
    CP   R5, R1
    JR   NZ, FAIL
    LD   @RR8, R6
    DEC  R9, #2
    CP   R9, R3
    JR   UGE, P4_LOOP

; ---------------------------------------------------------------
; Phase 5: Abwaerts lesen 0x0000
; ---------------------------------------------------------------
    LD   R1, #0x0000
    LD   R9, R4
P5_LOOP:
    LD   R5, @RR8
    CP   R5, R1
    JR   NZ, FAIL
    DEC  R9, #2
    CP   R9, R3
    JR   UGE, P5_LOOP

; ---------------------------------------------------------------
; Erfolg (Mailbox in Segment 0 per non-segmented Zugriff)
; ---------------------------------------------------------------
    LD   R7, #0x0010
    LD   R1, #0x0001
    LD   @R7, R1
    JR   T, $

; ---------------------------------------------------------------
; Fehler: R1=Soll, R5=Ist, R9=Adresse (Offset)
; ---------------------------------------------------------------
FAIL:
    LD   R7, #0x0010        ; STATUS offset (non-segmented -> Seg 0)
    LD   R11, #0x0002       ; STATUS = FEHLER
    LD   @R7, R11
    INC  R7, #2
    LD   @R7, R1            ; RESULT1 = Soll
    INC  R7, #2
    LD   @R7, R5            ; RESULT2 = Ist
    INC  R7, #2
    LD   @R7, R9            ; RESULT3 = Adresse (Offset)
    JR   T, $
