; fw_sub.s - C2: Subtraktion 0x8000 - 0x0001 = 0x7FFF
;
; Erwartung: RESULT1 = 0x7FFF, STATUS = 0x0001

    ORG  0x0000

    ; Z8001 Reset-Vektor (FCW=0x4000: System Mode fuer MSET)
    DW   0x0000, 0x4000, 0x0000, 0x0040

    ; Mailbox (0x0008 - 0x003F)
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0       ; SP
    LD   R1, #0x8000
    SUB  R1, #0x0001
    ; R1 = 0x7FFF -> Mailbox
    LD   R2, #0x0012        ; RESULT1 offset
    LD   @R2, R1
    ; STATUS = OK
    LD   R1, #0x0001
    LD   R2, #0x0010
    LD   @R2, R1
    MSET
    JR   T, $
