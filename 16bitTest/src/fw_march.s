; fw_march.s - D1-D4: March-C DRAM-Test fuer ein Segment
;
; Testet den DRAM im aktuellen Segment (nach Reset = Segment 0).
; March-C Algorithmus: 5 Phasen, erkennt Stuck-At und Koppelfehler.
;
; Testbereich: 0x0100 bis 0xFFFE (wortweise, 0x0000-0x00FF = Mailbox+Code)
;
; Mailbox-Ergebnis:
;   STATUS  = 0x0001 (OK) oder 0x0002 (FEHLER)
;   RESULT1 = Sollwert bei Fehler
;   RESULT2 = Istwert bei Fehler
;   RESULT3 = Fehleradresse

    ORG  0x0000

    ; Z8001 Reset-Vektor (FCW=0x4000: System Mode fuer MSET)
    DW   0x0000, 0x4000, 0x0000, 0x0040

    ; Mailbox (0x0008 - 0x003F)
    DS   56

; === Code ab 0x0040 ===

START:
    LD   R15, #0x00FE       ; SP knapp unter Testbereich

    ; Register-Konventionen:
    ; R1  = Testmuster (Soll-Wert)
    ; R2  = aktuelle Adresse
    ; R3  = Anfangsadresse (0x0100)
    ; R4  = Endadresse (0xFFFE)
    ; R5  = gelesener Wert
    ; R6  = Hilfregister

    LD   R3, #0x0100        ; Startadresse (nach Code+Mailbox)
    LD   R4, #0xFFFE        ; letzte Wortadresse

; ---------------------------------------------------------------
; Phase 1: Aufwaerts mit 0x0000 fuellen
; ---------------------------------------------------------------
    LD   R1, #0x0000
    LD   R2, R3
P1_LOOP:
    LD   @R2, R1
    INC  R2, #2
    CP   R2, R4
    JR   ULE, P1_LOOP
    ; Auch letzte Adresse
    LD   @R2, R1

; ---------------------------------------------------------------
; Phase 2: Aufwaerts lesen 0x0000, schreiben 0xFFFF
; ---------------------------------------------------------------
    LD   R1, #0x0000        ; Erwartung
    LD   R6, #0xFFFF        ; neues Muster
    LD   R2, R3
P2_LOOP:
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL
    LD   @R2, R6
    INC  R2, #2
    CP   R2, R4
    JR   ULE, P2_LOOP
    ; letzte Adresse
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL
    LD   @R2, R6

; ---------------------------------------------------------------
; Phase 3: Aufwaerts lesen 0xFFFF
; ---------------------------------------------------------------
    LD   R1, #0xFFFF
    LD   R2, R3
P3_LOOP:
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL
    INC  R2, #2
    CP   R2, R4
    JR   ULE, P3_LOOP
    ; letzte Adresse
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL

; ---------------------------------------------------------------
; Phase 4: Abwaerts lesen 0xFFFF, schreiben 0x0000
; ---------------------------------------------------------------
    LD   R1, #0xFFFF
    LD   R6, #0x0000
    LD   R2, R4             ; von Ende
P4_LOOP:
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL
    LD   @R2, R6
    DEC  R2, #2
    CP   R2, R3
    JR   UGE, P4_LOOP

; ---------------------------------------------------------------
; Phase 5: Abwaerts lesen 0x0000
; ---------------------------------------------------------------
    LD   R1, #0x0000
    LD   R2, R4
P5_LOOP:
    LD   R5, @R2
    CP   R5, R1
    JR   NZ, FAIL
    DEC  R2, #2
    CP   R2, R3
    JR   UGE, P5_LOOP

; ---------------------------------------------------------------
; Erfolg
; ---------------------------------------------------------------
    LD   R1, #0x0001
    LD   R2, #0x0010
    LD   @R2, R1
    MSET
    JR   T, $

; ---------------------------------------------------------------
; Fehler: R1=Soll, R5=Ist, R2=Adresse
; ---------------------------------------------------------------
FAIL:
    LD   R7, #0x0010        ; STATUS offset
    LD   R8, #0x0002        ; STATUS = FEHLER
    LD   @R7, R8
    INC  R7, #2
    LD   @R7, R1            ; RESULT1 = Soll
    INC  R7, #2
    LD   @R7, R5            ; RESULT2 = Ist
    INC  R7, #2
    LD   @R7, R2            ; RESULT3 = Fehleradresse
    MSET
    JR   T, $
