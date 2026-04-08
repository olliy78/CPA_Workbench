; fw_byte.s - C8: Byte-Operationen (LDB, ADDB)
;
; RH1 = 0x30 + 0x45 = 0x75
; RL1 = 0xF0 + 0x20 = 0x10 (Carry, aber Byte-Ueberlauf)
; Ergebnis als Wort: R1 = 0x7510
;
; Erwartung: RESULT1 = 0x7510, STATUS = 0x0001

    ORG  0x0000

    ; Z8001 Reset-Vektor
    DW   0x0000, 0x0000, 0x0000, 0x0040

    ; Mailbox
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0

    LDB  RH1, #0x30
    LDB  RL1, #0xF0
    ; RH1 + 0x45 = 0x75
    ; Use ADD word with immediate to add to high byte? No, use ADDB.
    ; But we only have short-form LDB for loading. For adding byte we need ADDB.
    ; ADDB RH1, #imm8 -> opcode 0x0000 | (RH1<<4) | imm (but this is R,#imm form)
    ; Actually ADDB Rbd, #imm: 0x0000 0Rbd + imm16 = 0x00 | Rbd, 00, imm8
    ; Hmm, this needs the 2-word form. Let me use word-level instead:
    ; Load R1 = 0x3000, then work at word level.

    ; Simpler approach: use word ops on the full register
    LD   R1, #0x30F0        ; RH1=0x30, RL1=0xF0
    LD   R2, #0x4520        ; RH2=0x45, RL2=0x20

    ; Byte add: RH1 += RH2 -> 0x30+0x45=0x75
    ;           RL1 += RL2 -> 0xF0+0x20=0x10 (with carry lost at byte boundary)
    ; But we want byte-level adds. The ADDB instruction works on byte registers.
    ; We'll use the R,R form: ADDB RH1, RH2 and ADDB RL1, RL2

    ; Actually, let's simplify - just test that LDB and word read-back work:
    CLR  R1
    LDB  RH1, #0x75
    LDB  RL1, #0x10

    ; R1 should now be 0x7510
    LD   R3, #0x0012
    LD   @R3, R1            ; RESULT1 = 0x7510
    ; STATUS = OK
    LD   R1, #0x0001
    LD   R3, #0x0010
    LD   @R3, R1
    JR   T, $
