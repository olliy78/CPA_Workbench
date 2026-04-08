; fw_add32.s - C7: 32-Bit-Arithmetik (ADDL)
;
; RR2 = 0x00010000 + 0x0000FFFF = 0x0001FFFF
; Testet Langwort-Operationen.
;
; Erwartung: RESULT1 = 0x0001 (High), RESULT2 = 0xFFFF (Low), STATUS = 0x0001

    ORG  0x0000

    ; Z8001 Reset-Vektor
    DW   0x0000, 0x0000, 0x0000, 0x0040

    ; Mailbox
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0

    LDL  RR2, #0x00010000
    LDL  RR4, #0x0000FFFF
    ADDL RR2, RR4
    ; RR2 = 0x0001FFFF -> R2=0x0001, R3=0xFFFF

    ; Ergebnis -> Mailbox
    LD   R6, #0x0012
    LD   @R6, R2            ; RESULT1 = High (0x0001)
    INC  R6, #2
    LD   @R6, R3            ; RESULT2 = Low (0xFFFF)
    ; STATUS = OK
    LD   R1, #0x0001
    LD   R6, #0x0010
    LD   @R6, R1
    JR   T, $
