; fw_loop.s - C5: Schleifentest (DJNZ)
;
; Zaehlt R1 256 mal hoch (R1 += 1, R2 = 256 Iterationen)
; Ergebnis: R1 = 256 = 0x0100
;
; Erwartung: RESULT1 = 0x0100, STATUS = 0x0001

    ORG  0x0000

    ; Z8001 Reset-Vektor (FCW=0x4000: System Mode fuer MSET)
    DW   0x0000, 0x4000, 0x0000, 0x0040

    ; Mailbox
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0
    LD   R1, #0x0000        ; Summe
    LD   R2, #0x0100        ; Zaehler = 256

LOOP:
    INC  R1, #1
    DEC  R2, #1
    CP   R2, #0x0000
    JR   NZ, LOOP

    ; Ergebnis -> Mailbox
    LD   R3, #0x0012        ; RESULT1
    LD   @R3, R1
    ; STATUS = OK
    LD   R1, #0x0001
    LD   R3, #0x0010
    LD   @R3, R1
    MSET
    JR   T, $
