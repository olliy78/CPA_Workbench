; fw_memrw.s - C4: Speicher Read/Write Test
;
; Schreibt verschiedene Muster in Speicheradressen und liest zurueck.
; Vergleicht geschriebene mit gelesenen Werten.
;
; Erwartung: STATUS = 0x0001 (OK), RESULT1 = 0xA55A (letztes gelesenes Muster)

    ORG  0x0000

    ; Z8001 Reset-Vektor (FCW=0x4000: System Mode fuer MSET)
    DW   0x0000, 0x4000, 0x0000, 0x0040

    ; Mailbox
    DS   56

    ; Code ab 0x0040
    LD   R15, #0xFFF0

    ; Test 1: Muster 0xA55A an Adresse 0x0100
    LD   R1, #0xA55A
    LD   R3, #0x0100
    LD   @R3, R1
    LD   R4, @R3
    CP   R4, R1
    JR   NZ, FAIL

    ; Test 2: Muster 0x5AA5 an Adresse 0x0102
    LD   R1, #0x5AA5
    INC  R3, #2
    LD   @R3, R1
    LD   R4, @R3
    CP   R4, R1
    JR   NZ, FAIL

    ; Test 3: Muster 0xFFFF an Adresse 0x0104
    LD   R1, #0xFFFF
    INC  R3, #2
    LD   @R3, R1
    LD   R4, @R3
    CP   R4, R1
    JR   NZ, FAIL

    ; Test 4: Muster 0x0000 an Adresse 0x0106
    LD   R1, #0x0000
    INC  R3, #2
    LD   @R3, R1
    LD   R4, @R3
    CP   R4, R1
    JR   NZ, FAIL

    ; Test 5: Gegenlesen - Adresse 0x0100 sollte noch 0xA55A haben
    LD   R3, #0x0100
    LD   R4, @R3
    LD   R1, #0xA55A
    CP   R4, R1
    JR   NZ, FAIL

    ; Alle OK -> Ergebnis
    LD   R2, #0x0012        ; RESULT1
    LD   @R2, R4            ; letzter gelesener Wert (0xA55A)
    LD   R1, #0x0001
    LD   R2, #0x0010
    LD   @R2, R1
    MSET
    JR   T, $

FAIL:
    ; R1=Soll, R4=Ist, R3=Adresse
    LD   R5, #0x0010
    LD   R6, #0x0002        ; STATUS = FEHLER
    LD   @R5, R6
    INC  R5, #2
    LD   @R5, R1            ; RESULT1 = Soll
    INC  R5, #2
    LD   @R5, R4            ; RESULT2 = Ist
    INC  R5, #2
    LD   @R5, R3            ; RESULT3 = Adresse
    MSET
    JR   T, $
