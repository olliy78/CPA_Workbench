; fw_logic.s - C3: Logik-Test AND/OR/XOR
;
; R1 = 0xFF00 AND 0x0F0F = 0x0F00
; R1 = R1 OR 0x00F0       = 0x0FF0
; R1 = R1 XOR 0x0FF0      = 0x0000
; R1 = R1 XOR 0x1234      = 0x1234
;
; Erwartung: RESULT1 = 0x1234, STATUS = 0x0001

    ORG  0x0000

    ; Z8001 Reset-Vektor
    DW   0x0000, 0x0000, 0x0000, 0x0040

    ; Mailbox
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0
    LD   R1, #0xFF00
    AND  R1, #0x0F0F        ; -> 0x0F00
    OR   R1, #0x00F0        ; -> 0x0FF0
    XOR  R1, #0x0FF0        ; -> 0x0000
    XOR  R1, #0x1234        ; -> 0x1234
    ; Ergebnis -> Mailbox
    LD   R2, #0x0012
    LD   @R2, R1
    ; STATUS = OK
    LD   R1, #0x0001
    LD   R2, #0x0010
    LD   @R2, R1
    JR   T, $
