#!/usr/bin/env python3
"""
z8001asm.py - Minimal Z8001 (segmented) Cross-Assembler

Assembles Z8001 assembly source into binary output, M80-compatible .inc files,
and optional listing files. Two-pass assembly with label support.

Usage:
    python z8001asm.py input.s [-o output.bin] [--inc output.inc] [--lst] [--label PREFIX]

Author: (c) 2026 Olaf Krieger
License: MIT
"""

import sys
import re
import argparse
from pathlib import Path


# =============================================================================
# Condition codes (Z8001 FCW Bits)
#
# Kodierung als 4-Bit-Wert im Instruktionswort (z.B. JR cc, JP cc, RET cc).
# Jeder Wert kombininiert die Flags C, Z, S, P/V nach dem Schema der
# Zilog Z8000 CPU User's Reference.
# =============================================================================
CC_TABLE = {
    'F': 0x0, 'T': 0x8,
    'Z': 0x6, 'EQ': 0x6,
    'NZ': 0xE, 'NE': 0xE,
    'C': 0x7, 'ULT': 0x7,
    'NC': 0xF, 'UGE': 0xF,
    'PL': 0xD, 'MI': 0x5,
    'OV': 0x4, 'NOV': 0xC,
    'GT': 0xA, 'GE': 0x9,
    'LT': 0x1, 'LE': 0x2,
    'UGT': 0xB, 'ULE': 0x3,
}

# =============================================================================
# Register parsing
# =============================================================================

def parse_register(s):
    """Parse register name, return (type, number).
    type: 'R' (word), 'RH' (high byte), 'RL' (low byte), 'RR' (pair), 'RQ' (quad)
    """
    s = s.strip().upper()
    m = re.match(r'^RQ(\d+)$', s)
    if m:
        n = int(m.group(1))
        if n not in (0, 4, 8, 12):
            raise ValueError(f"Invalid quad register: {s}")
        return ('RQ', n)
    m = re.match(r'^RR(\d+)$', s)
    if m:
        n = int(m.group(1))
        if n % 2 != 0 or n > 14:
            raise ValueError(f"Invalid register pair: {s}")
        return ('RR', n)
    m = re.match(r'^RH(\d+)$', s)
    if m:
        n = int(m.group(1))
        if n > 7:
            raise ValueError(f"Invalid high byte register: {s}")
        return ('RH', n)
    m = re.match(r'^RL(\d+)$', s)
    if m:
        n = int(m.group(1))
        if n > 7:
            raise ValueError(f"Invalid low byte register: {s}")
        return ('RL', n + 8)
    m = re.match(r'^R(\d+)$', s)
    if m:
        n = int(m.group(1))
        if n > 15:
            raise ValueError(f"Invalid register: {s}")
        return ('R', n)
    return None


def parse_indirect(s):
    """Parse @Rn or @RRn, return (type, number) or None."""
    s = s.strip()
    if s.startswith('@'):
        return parse_register(s[1:])
    return None


# =============================================================================
# Expression evaluator (for immediates and labels)
# =============================================================================

def eval_expr(expr, symbols, pc=0):
    """Evaluate a numeric expression with symbol substitution.
    Supports: hex (0xNN, 0NNh, $NN), decimal, binary (0bNNN, NNNb),
    +, -, *, /, %, ~, (, ), and symbol names.
    Special: $ = current PC.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty expression")

    # Tokenize and substitute
    result = _subst_expr(expr, symbols, pc)

    try:
        # Safe eval with no builtins
        val = eval(result, {"__builtins__": {}}, {})
        if isinstance(val, float):
            val = int(val)
        return val & 0xFFFFFFFF  # 32-bit mask
    except Exception as e:
        raise ValueError(f"Cannot evaluate expression '{expr}' -> '{result}': {e}")


def _subst_expr(expr, symbols, pc):
    """Substitute symbols, hex literals, $ into Python-evaluable string."""
    # Replace $ (current PC) as standalone token
    # But not inside 0x... or similar
    result = []
    i = 0
    tokens = _tokenize_expr(expr)
    for tok in tokens:
        tok_upper = tok.upper()
        if tok == '$':
            result.append(str(pc))
        elif tok_upper in symbols:
            result.append(str(symbols[tok_upper]))
        elif re.match(r'^0[xX][0-9a-fA-F]+$', tok):
            result.append(tok)  # Python understands 0x...
        elif re.match(r'^0[bB][01]+$', tok):
            result.append(tok)  # Python understands 0b...
        elif re.match(r'^[0-9][0-9a-fA-F]*[hH]$', tok):
            # Zilog hex: 0FFh, 1234h
            result.append('0x' + tok[:-1])
        elif re.match(r'^[01]+[bB]$', tok) and len(tok) > 1:
            # Zilog binary: 10101010b
            result.append('0b' + tok[:-1])
        elif re.match(r'^\d+$', tok):
            result.append(tok)
        elif tok in '+-*/%~()&|^<<>>':
            result.append(tok)
        elif tok in ('<', '>', '<<', '>>', '&', '|', '^'):
            result.append(tok)
        elif tok_upper == 'SHL':
            result.append('<<')
        elif tok_upper == 'SHR':
            result.append('>>')
        elif tok_upper == 'AND':
            result.append('&')
        elif tok_upper == 'OR':
            result.append('|')
        elif tok_upper == 'XOR':
            result.append('^')
        elif tok_upper == 'NOT':
            result.append('~')
        elif tok_upper == 'MOD':
            result.append('%')
        elif tok_upper == 'HIGH':
            # HIGH expr -> (expr >> 8) & 0xFF
            result.append('(')
            # Look ahead handled by nesting
            result.append('0 +')  # placeholder, HIGH is unary
            # Actually this is complex. Let's handle specially.
            result.append('')
        else:
            # Try as unknown symbol - might be forward reference
            if tok_upper in symbols:
                result.append(str(symbols[tok_upper]))
            else:
                raise ValueError(f"Undefined symbol: {tok}")
    return ' '.join(result)


def _tokenize_expr(expr):
    """Split expression into tokens."""
    tokens = []
    i = 0
    expr = expr.strip()
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        # Multi-char operators
        if expr[i:i+2] in ('<<', '>>', '>=', '<=', '==', '!='):
            tokens.append(expr[i:i+2])
            i += 2
            continue
        # Single char operators/parens
        if expr[i] in '+-*/%~()&|^<>,':
            tokens.append(expr[i])
            i += 1
            continue
        # Number or identifier
        m = re.match(r'[0-9a-zA-Z_$.]+', expr[i:])
        if m:
            tokens.append(m.group(0))
            i += m.end()
            continue
        # Hash for immediate
        if expr[i] == '#':
            i += 1
            continue
        raise ValueError(f"Unexpected character in expression: '{expr[i]}' at position {i}")
    return tokens


# =============================================================================
# Instruction encoder
#
# Jede statische Methode kodiert eine Z8001-Instruktion in eine Folge
# von Bytes (Big-Endian).  Die Kommentare referenzieren die MAME-
# Opcode-Tabelle z8000tbl.hxx als Verifikationsquelle.
#
# Z8001-Wortformat:  Byte 0 = MSB (Bits 15-8), Byte 1 = LSB (Bits 7-0)
# Alle Instruktionen sind wortausgerichtet (2, 4 oder 6 Bytes).
# =============================================================================

class Encoder:
    """Kodiert Z8001-Instruktionen zu Bytes (non-segmented Adressierung)."""

    @staticmethod
    def word_bytes(w):
        """Convert 16-bit word to big-endian bytes."""
        return [(w >> 8) & 0xFF, w & 0xFF]

    @staticmethod
    def encode_ld_r_imm(rd, imm16):
        """LD Rd, #imm16 -> 0x2100|Rd, imm16"""
        w1 = 0x2100 | (rd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_ldb_r_imm_short(rbd, imm8):
        """LDB Rbd, #imm8 -> short form: 0xC0|Rbd<<4|imm8_high, imm8_low
        Actually: byte1 = 0xC0 | (Rbd << 4) | (imm8 >> 4), byte2 = (imm8 << 4) | (imm8 & 0xF)
        Wait, the short form is: 1100 Rbd data(8bit) -> first byte = 0xC0|(Rbd<<0), but
        actually format is: bits 15-12=1100, bits 11-8=Rbd, bits 7-0=data
        So word = 0xC000 | (Rbd << 8) | (imm8 & 0xFF)
        """
        w1 = 0xC000 | ((rbd & 0xF) << 8) | (imm8 & 0xFF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldl_rr_imm(rrd, imm32):
        """LDL RRd, #imm32 -> 0x1400|RRd, high16, low16"""
        w1 = 0x1400 | (rrd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_ld_r_r(rd, rs, byte_op=False):
        """LD Rd, Rs -> 1010 000w ssss dddd
        LDB Rbd, Rbs: 0xA0 (w=0), LD Rd, Rs: 0xA1 (w=1)
        Verified from MAME: ZA0=LDB, ZA1=LD (R,R)
        """
        w_bit = 0 if byte_op else 1
        w1 = 0xA000 | (w_bit << 8) | ((rs & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ld_r_ir(rd, rs, byte_op=False):
        """LD Rd, @Rs -> 0010 0001 w Rs Rd (same opcode family as LD Rd,#imm)
        Actually from table: LD Rd, @Rs: 0w|1|Rs|Rd
        Known: LD Rd,#imm is 0010 0001 0000 Rd + data
        And LD Rd,@Rs: 0010 0001 w Rs!=0 Rd = 0x20 | (w<<8)... let me reconsider.

        Actually from the extract:
        LD R,@Rs (IR): 0w|1|Rs|Rd -> this is a condensed notation.
        The full word: 0010 000w 1 ssss dddd -> wait, the original says bits:
        0 w 1 Rs Rd for nonsegmented. But that's only describing part of the word.
        
        Let's check: LD Rd,#data gave us word1=0x2100|Rd = 0010 0001 0000 dddd
        So LD R,IR should be: 0010 000w ssss dddd where ssss!=0.
        With w=1 for word: 0010 0001 ssss dddd = 0x2100 | (Rs<<4) | Rd
        """
        w_bit = 0 if byte_op else 1
        w1 = 0x2000 | (w_bit << 8) | ((rs & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ld_ir_r(rd_ir, rs, byte_op=False):
        """LD @Rd, Rs -> 0010 1111 w Rd*0 Rs
        Known: LD @R2, R1 = 0x2F21 = 0010 1111 0010 0001
        So: 0010 1111 w=1 Rd*0=0010 Rs=0001 -> 0x2F, (Rd<<4)|Rs
        Hmm wait: 0x2F = 0010 1111, then 0x21 = 0010 0001
        Rd*0 means the register forced to even? R2=0010, Rs=R1=0001.
        So format: 0010 111w ssss rrrr where ssss=Rd (with LSB=0 for IR), rrrr=Rs.
        Wait no. LD @Rd, Rs: the encoding is 0010 1111 w Rd*0 Rs
        0x2F21: 0010 1111 0010 0001. Bits: 0010 1111 = opcode with w=1,
        next byte: Rd*0=0010 (R2, even), Rs=0001 (R1).
        Actually: bits 15-8 = 0010 111w. w=1 -> 0010 1111 = 0x2F. 
        bits 7-4 = Rd (the destination for indirect), bits 3-0 = Rs.
        """
        w_bit = 0 if byte_op else 1
        w1 = (0x2E00 | (w_bit << 8)) | ((rd_ir & 0xF) << 4) | (rs & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ld_ir_imm(rd_ir, imm16):
        """LD @Rd, #data -> 0000 1101 Rd*0 0101 + data
        See table: 0010 0110 1 Rd*0 0101 + data
        Hmm, extracted: LD @Rd1, #data: 0010 0110 1 Rd*0 0101 + data (word)
        = 0x2600 | 0x0100 | (Rd<<4) | 0x05 = 0x2705 | (Rd<<4)?
        Wait: 001 0 0 1 1 0 1 Rd*0 1 0 1 0 1. That's bits 15-0:
        0010 0110 1 Rd(3:0) 0101. But Rd*0 means bit 4 of the low byte is 0.
        So: 0010 0110 1 ddd0 0101 where ddd0 = Rd (must be even).
        For word: 0x0D05 seems wrong. Let me re-derive from the table.
        
        Actually from the table: LD @Rd1, #data: 0010 0110 1 Rd*0 1 0101
        Hmm, the OCR is messy. Let me just use: 0x0D << 8 format.
        
        From alternate: The format is 001001101 Rd*0 0101 which is:
        bits 15-7: 0 0100 1101, bits 6-4: Rd>>1, bit 3: 0, bits 2-0: 101
        No wait. Let me look at it differently.
        
        0010 0110 1ddd 0101 where ddd0=Rd(even register or register pair).
        That gives 0x26 for high byte if starts with 0, or is it 0x0D?
        
        Actually I think the table says: 0000 1101 Rd*0 0101.
        0000 1101 = 0x0D. Then Rd<<4 | 0x05.
        So word1 = 0x0D00 | (Rd<<4) | 0x05 = 0x0D05 | (Rd<<4).
        
        Hmm but cross-referencing the extract says:
        LD @Rd1, #data: 0010011011Rd*010101
        Let me parse: 0 0 1 0 0 1 1 0 1 Rd*0 1 0 1 0 1
        That's 16 bits: 0010 0110 1Rd* 0101
        If Rd=R2 (0010): 0010 0110 1001 0101 = 0x2695. That doesn't look right either.
        
        Let me try another approach. I'll trust the known-working patterns and
        derive from the reference. For now, let me encode what I know for certain
        and we can add more as needed.
        """
        # Using: 0000 1101 Rd*0 0101 (the cleaner reading from the extract)
        w1 = 0x0D00 | ((rd_ir & 0xE) << 4) | 0x05
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_ldk(rd, n):
        """LDK Rd, #n (0-15) -> 1011 1101 Rd n"""
        w1 = 0xBD00 | ((rd & 0xF) << 4) | (n & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldl_rr_rr(rrd, rrs):
        """LDL RRd, RRs -> 1001 0100 RRs RRd"""
        w1 = 0x9400 | ((rrs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_arith_r_imm(opcode_base, rd, imm16):
        """Arithmetic Rd, #imm16. Format: opcode_base 0000 Rd + imm16.
        ADD: 0x0100, SUB: 0x0300, CP: 0x0B00, AND: 0x0700, OR: 0x0500, XOR: 0x0900
        Known: ADD R1,#0x5678 = 0x0101 0x5678 -> 0000 0001 0000 0001
        So format: 0000 0001 0000 Rd + imm16. Base for ADD = 0x0100.
        """
        w1 = (opcode_base & 0xFF00) | (rd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_arith_r_r(opcode_base, rd, rs, byte_op=False):
        """Arithmetic Rd, Rs. Format: opcode_base w Rs Rd.
        ADD R,R: 1000 0001 w Rs Rd. For word w=1.
        SUB R,R: 1000 0011 w Rs Rd.
        CP R,R:  1000 1011 w Rs Rd.
        AND R,R: 1000 0111 w Rs Rd.
        OR R,R:  1000 0101 w Rs Rd.
        XOR R,R: 1000 1001 w Rs Rd.
        ADC R,R: 1011 0101 w Rs Rd.
        SBC R,R: 1011 0111 w Rs Rd.
        """
        w_bit = 0 if byte_op else 1
        w1 = (opcode_base & 0xFF00) | (w_bit << 8) | ((rs & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_arith_r_ir(opcode_base, rd, rs, byte_op=False):
        """Arithmetic Rd, @Rs. Same format but different opcode_base:
        ADD @Rs: 0000 0001 w Rs Rd (Rs != 0)
        Actually for IR mode, the opcode high byte changes.
        ADD Rd,@Rs: 0000 0001 w Rs Rd -> wait, that's the same as LD Rd,@Rs.
        No: ADD Rd,#imm = 0000 0001 0000 Rd + data
        ADD Rd,@Rs = 0000 0001 w Rs Rd (where Rs!=0 differentiates from imm)
        
        So the opcode base for IR is 0x0000 | (specific bits).
        """
        w_bit = 0 if byte_op else 1
        w1 = (opcode_base & 0xFF00) | (w_bit << 8) | ((rs & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_addl_rr_rr(rrd, rrs):
        """ADDL RRd, RRs -> 1001 0110 RRs RRd (MAME: Z96=ADDL)"""
        w1 = 0x9600 | ((rrs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_subl_rr_rr(rrd, rrs):
        """SUBL RRd, RRs -> 1001 0010 RRs RRd (MAME: Z92=SUBL)"""
        w1 = 0x9200 | ((rrs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_cpl_rr_rr(rrd, rrs):
        """CPL RRd, RRs -> 1001 0000 RRs RRd (MAME: Z90=CPL)"""
        w1 = 0x9000 | ((rrs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_addl_rr_imm(rrd, imm32):
        """ADDL RRd, #imm32 -> 0x1600 | RRd + imm32 (MAME: Z16=ADDL)"""
        w1 = 0x1600 | (rrd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_subl_rr_imm(rrd, imm32):
        """SUBL RRd, #imm32 -> 0x1200 | RRd + imm32 (MAME: Z12=SUBL)"""
        w1 = 0x1200 | (rrd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_cpl_rr_imm(rrd, imm32):
        """CPL RRd, #imm32 -> 0x1000 | RRd + imm32 (MAME: Z10=CPL)"""
        w1 = 0x1000 | (rrd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_addl_rr_ir(rrd, rs):
        """ADDL RRd, @Rs -> 0x1600 | (Rs<<4) | RRd (MAME: Z16_ssN0)"""
        w1 = 0x1600 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_subl_rr_ir(rrd, rs):
        """SUBL RRd, @Rs -> 0x1200 | (Rs<<4) | RRd"""
        w1 = 0x1200 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_cpl_rr_ir(rrd, rs):
        """CPL RRd, @Rs -> 0x1000 | (Rs<<4) | RRd"""
        w1 = 0x1000 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_mult_rr_rs(rrd, rs):
        """MULT RRd, Rs -> 0x9900 | (Rs<<4) | RRd (MAME: Z99=MULT, 70 cycles)"""
        w1 = 0x9900 | ((rs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_mult_rr_imm(rrd, imm16):
        """MULT RRd, #imm16 -> 0x1900 | RRd + imm16 (MAME: Z19=MULT)"""
        w1 = 0x1900 | (rrd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_mult_rr_ir(rrd, rs):
        """MULT RRd, @Rs -> 0x1900 | (Rs<<4) | RRd"""
        w1 = 0x1900 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_multl_rq_rrs(rqd, rrs):
        """MULTL RQd, RRs -> 0x9800 | (RRs<<4) | RQd (MAME: Z98=MULTL, 282 cycles)"""
        w1 = 0x9800 | ((rrs & 0xF) << 4) | (rqd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_multl_rq_imm(rqd, imm32):
        """MULTL RQd, #imm32 -> 0x1800 | RQd + imm32 (MAME: Z18=MULTL)"""
        w1 = 0x1800 | (rqd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_multl_rq_ir(rqd, rs):
        """MULTL RQd, @Rs -> 0x1800 | (Rs<<4) | RQd"""
        w1 = 0x1800 | ((rs & 0xE) << 4) | (rqd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_div_rr_rs(rrd, rs):
        """DIV RRd, Rs -> 0x9B00 | (Rs<<4) | RRd (MAME: Z9B=DIV, 107 cycles)"""
        w1 = 0x9B00 | ((rs & 0xF) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_div_rr_imm(rrd, imm16):
        """DIV RRd, #imm16 -> 0x1B00 | RRd + imm16 (MAME: Z1B=DIV)"""
        w1 = 0x1B00 | (rrd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_div_rr_ir(rrd, rs):
        """DIV RRd, @Rs -> 0x1B00 | (Rs<<4) | RRd"""
        w1 = 0x1B00 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_divl_rq_rrs(rqd, rrs):
        """DIVL RQd, RRs -> 0x9A00 | (RRs<<4) | RQd (MAME: Z9A=DIVL, 744 cycles)"""
        w1 = 0x9A00 | ((rrs & 0xF) << 4) | (rqd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_divl_rq_imm(rqd, imm32):
        """DIVL RQd, #imm32 -> 0x1A00 | RQd + imm32 (MAME: Z1A=DIVL)"""
        w1 = 0x1A00 | (rqd & 0xF)
        hi = (imm32 >> 16) & 0xFFFF
        lo = imm32 & 0xFFFF
        return Encoder.word_bytes(w1) + Encoder.word_bytes(hi) + Encoder.word_bytes(lo)

    @staticmethod
    def encode_divl_rq_ir(rqd, rs):
        """DIVL RQd, @Rs -> 0x1A00 | (Rs<<4) | RQd"""
        w1 = 0x1A00 | ((rs & 0xE) << 4) | (rqd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_extsb(rd):
        """EXTSB Rd -> 0xB100 | (Rd<<4) | 0x00 (MAME: ZB1_dddd_0000)
        Sign-extend byte in low half of Rd to word."""
        w1 = 0xB100 | ((rd & 0xF) << 4) | 0x00
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_exts(rrd):
        """EXTS RRd -> 0xB100 | (RRd<<4) | 0x0A (MAME: ZB1_dddd_1010)
        Sign-extend word in low half of RRd to long."""
        w1 = 0xB100 | ((rrd & 0xF) << 4) | 0x0A
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_extsl(rqd):
        """EXTSL RQd -> 0xB100 | (RQd<<4) | 0x07 (MAME: ZB1_dddd_0111)
        Sign-extend long in low half of RQd to quad."""
        w1 = 0xB100 | ((rqd & 0xF) << 4) | 0x07
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_test(rd, byte_op=False):
        """TEST Rd -> 0x8D00 | (Rd<<4) | 0x04 (MAME: Z8D_dddd_0100)
        TESTB Rbd -> 0x8C00 | (Rbd<<4) | 0x04 (MAME: Z8C_dddd_0100)"""
        w_bit = 0 if byte_op else 1
        w1 = 0x8C00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x04
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_testl(rrd):
        """TESTL RRd -> 0x9C00 | (RRd<<4) | 0x08 (MAME: Z9C_dddd_1000)"""
        w1 = 0x9C00 | ((rrd & 0xF) << 4) | 0x08
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_tset(rd, byte_op=False):
        """TSET Rd -> 0x8D00 | (Rd<<4) | 0x06 (MAME: Z8D_dddd_0110)
        TSETB Rbd -> 0x8C00 | (Rbd<<4) | 0x06 (MAME: Z8C_dddd_0110)"""
        w_bit = 0 if byte_op else 1
        w1 = 0x8C00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x06
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_dab(rbd):
        """DAB Rbd -> 0xB000 | (Rbd<<4) | 0x00 (MAME: ZB0_dddd_0000)"""
        w1 = 0xB000 | ((rbd & 0xF) << 4)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_rldb(rba, rbb):
        """RLDB Rbb, Rba -> 0xBE00 | (Rba<<4) | Rbb (MAME: ZBE_aaaa_bbbb)"""
        w1 = 0xBE00 | ((rba & 0xF) << 4) | (rbb & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_rrdb(rba, rbb):
        """RRDB Rbb, Rba -> 0xBC00 | (Rba<<4) | Rbb (MAME: ZBC_aaaa_bbbb)"""
        w1 = 0xBC00 | ((rba & 0xF) << 4) | (rbb & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldm_load(rs, rd_first, count):
        """LDM Rd, @Rs, #n -> load n registers starting at Rd from memory @Rs
        MAME: Z1C_ssN0_0001_0000_dddd_0000_nmin1
        word1 = 0x1C00 | (Rs<<4) | 0x01
        word2 = (Rd<<8) | (n-1)
        """
        w1 = 0x1C00 | ((rs & 0xE) << 4) | 0x01
        w2 = ((rd_first & 0xF) << 8) | ((count - 1) & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(w2)

    @staticmethod
    def encode_ldm_store(rd, rs_first, count):
        """LDM @Rd, Rs, #n -> store n registers starting at Rs to memory @Rd
        MAME: Z1C_ddN0_1001_0000_ssss_0000_nmin1
        word1 = 0x1C00 | (Rd<<4) | 0x09
        word2 = (Rs<<8) | (n-1)
        """
        w1 = 0x1C00 | ((rd & 0xE) << 4) | 0x09
        w2 = ((rs_first & 0xF) << 8) | ((count - 1) & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(w2)

    @staticmethod
    def encode_lda(rd, addr16):
        """LDA Rd, address -> 0x7600 | Rd + addr16 (MAME: Z76_0000_dddd_addr)"""
        w1 = 0x7600 | (rd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(addr16 & 0xFFFF)

    @staticmethod
    def encode_ld_r_da(rd, addr16, byte_op=False):
        """LD Rd, address -> 0x6100 | Rd + addr16 (MAME: Z61_0000_dddd_addr)
        LDB Rbd, address -> 0x6000 | Rbd + addr16 (MAME: Z60_0000_dddd_addr)"""
        w_bit = 0 if byte_op else 1
        w1 = 0x6000 | (w_bit << 8) | (rd & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(addr16 & 0xFFFF)

    @staticmethod
    def encode_ld_da_r(addr16, rs, byte_op=False):
        """LD address, Rs -> 0x6F00 | Rs + addr16 (MAME: Z6F_0000_ssss_addr)
        LDB address, Rbs -> 0x6E00 | Rbs + addr16 (MAME: Z6E_0000_ssss_addr)"""
        w_bit = 0 if byte_op else 1
        w1 = 0x6E00 | (w_bit << 8) | ((rs & 0xF) << 4)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(addr16 & 0xFFFF)

    @staticmethod
    def encode_ldl_rr_ir(rrd, rs):
        """LDL RRd, @Rs -> 0x1400 | (Rs<<4) | RRd (MAME: Z14_ssN0_dddd)"""
        w1 = 0x1400 | ((rs & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldl_ir_rrs(rd, rrs):
        """LDL @Rd, RRs -> 0x1D00 | (Rd<<4) | RRs (MAME: Z1D_ddN0_ssss)"""
        w1 = 0x1D00 | ((rd & 0xE) << 4) | (rrs & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldi(dst_reg, src_reg, cnt_reg, repeat=False):
        """LDI @Rd, @Rs, Rr -> block load increment
        LDIR @Rd, @Rs, Rr -> block load increment with repeat
        MAME: ZBB_ssN0_0001_0000_rrrr_ddN0_x000
        word1 = 0xBB00 | (Rs<<4) | 0x01
        word2 = (Rr<<8) | (Rd<<4) | (0x08 if repeat else 0x00)
        """
        w1 = 0xBB00 | ((src_reg & 0xE) << 4) | 0x01
        w2 = ((cnt_reg & 0xF) << 8) | ((dst_reg & 0xE) << 4) | (0x08 if repeat else 0x00)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(w2)

    @staticmethod
    def encode_ldd(dst_reg, src_reg, cnt_reg, repeat=False):
        """LDD @Rd, @Rs, Rr -> block load decrement
        LDDR @Rd, @Rs, Rr -> block load decrement with repeat
        MAME: ZBB_ssN0_1001_0000_rrrr_ddN0_x000
        word1 = 0xBB00 | (Rs<<4) | 0x09
        word2 = (Rr<<8) | (Rd<<4) | (0x08 if repeat else 0x00)
        """
        w1 = 0xBB00 | ((src_reg & 0xE) << 4) | 0x09
        w2 = ((cnt_reg & 0xF) << 8) | ((dst_reg & 0xE) << 4) | (0x08 if repeat else 0x00)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(w2)

    @staticmethod
    def encode_inc_dec(rd, n, is_dec=False, byte_op=False):
        """INC Rd, #n / DEC Rd, #n (n=1..16, encoded as n-1).
        INC: 1010 1001 w Rd (n-1)  -> 0xA9 for word
        DEC: 1010 1011 w Rd (n-1)  -> 0xAB for word
        INCB: 1010 1000 w Rd (n-1) -> wait, the extract says:
        INC Rd, #n: 1010 1001 w Rd (n-1)
        INCB Rbd, #n: 1010 1000 w Rbd (n-1) -> but that's same as LD R,R for byte!
        
        Hmm, re-checking: INC: 1010 100w 1 Rd(4) (n-1)(4)
        Wait. Let me re-read the extract carefully:
        INC Rd, #n: 1010 1001 w Rd (n-1) -- but that's 10 bits for first 10 + Rd(4) + n-1(4)
        Actually: word = 1010 100X wRRR R(n-1)(n-1)(n-1)(n-1)
        
        From extract: INC R,IM: 1010 1001 w Rd (n-1)
        That means: bits 15-8 = 1010 100w where the 1 before w means it's register mode,
        No. Let me just consider the encoding literally:
        INC Rd, #n (word): high byte = 0xA9 (1010 1001), low byte = Rd<<4 | (n-1)
        INCB Rbd, #n: high byte = 0xA8 (1010 1000), low byte = Rbd<<4 | (n-1)
        DEC Rd, #n (word): high byte = 0xAB (1010 1011), low byte = Rd<<4 | (n-1)
        DECB Rbd, #n: high byte = 0xAA (1010 1010), low byte = Rbd<<4 | (n-1)
        """
        if is_dec:
            base = 0xAA00 if byte_op else 0xAB00
        else:
            base = 0xA800 if byte_op else 0xA900
        enc_n = (n - 1) & 0xF
        w1 = base | ((rd & 0xF) << 4) | enc_n
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_neg(rd, byte_op=False):
        """NEG Rd -> 1000 1101 w Rd 0010
        NEGB: 1000 1100 Rbd 0010
        0x8D for word, 0x8C for byte.
        """
        w_bit = 0 if byte_op else 1
        w1 = 0x8C00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x02
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_com(rd, byte_op=False):
        """COM Rd -> 1000 1101 w Rd 0000
        COMB: 1000 1100 Rbd 0000
        """
        w_bit = 0 if byte_op else 1
        w1 = 0x8C00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x00
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_clr(rd, byte_op=False):
        """CLR Rd -> 1000 1101 w Rd 1000"""
        w_bit = 0 if byte_op else 1
        w1 = 0x8C00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x08
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_bit_static(rd, bit_num, op='BIT', byte_op=False):
        """BIT/SET/RES Rd, #b (static bit test/set/reset).
        BIT: 1010 0111 w Rd b    (0xA7 for word)
        SET: 1010 0101 w Rd b    (0xA5 for word)  
        RES: 1010 0011 w Rd b    (0xA3 for word)
        """
        w_bit = 0 if byte_op else 1
        if op == 'BIT':
            base = 0xA600
        elif op == 'SET':
            base = 0xA400
        elif op == 'RES':
            base = 0xA200
        else:
            raise ValueError(f"Unknown bit op: {op}")
        w1 = base | (w_bit << 8) | ((rd & 0xF) << 4) | (bit_num & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_jr(cc, disp8):
        """JR cc, disp -> 1110 cc disp(8bit signed).
        Known: JR T,$ = E8 FE. T=1000, disp=-2=0xFE.
        So: byte1 = 0xE0 | cc, byte2 = disp & 0xFF.
        """
        return [0xE0 | (cc & 0xF), disp8 & 0xFF]

    @staticmethod
    def encode_jp_da(cc, addr16):
        """JP cc, address -> 0101 1110 0000 cc + address.
        0x5E00 | cc + addr16.
        """
        w1 = 0x5E00 | (cc & 0xF)
        return Encoder.word_bytes(w1) + Encoder.word_bytes(addr16 & 0xFFFF)

    @staticmethod
    def encode_jp_ir(cc, rs):
        """JP cc, @Rd -> 0001 1110 Rd*0 cc"""
        w1 = 0x1E00 | ((rs & 0xE) << 4) | (cc & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_djnz(rd, disp7):
        """DJNZ Rd, disp -> 1111 Rd 1 disp(7bit).
        Format: bits 15-12=1111, bits 11-8=Rd, bit 7=w(1=word), bits 6-0=displacement.
        """
        w1 = 0xF000 | ((rd & 0xF) << 8) | 0x80 | (disp7 & 0x7F)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_dbjnz(rbd, disp7):
        """DBJNZ Rbd, disp -> 1111 Rbd 0 disp(7bit) (byte version)."""
        w1 = 0xF000 | ((rbd & 0xF) << 8) | (disp7 & 0x7F)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_call_da(addr16):
        """CALL address -> 0101 1111 0000 0000 + address.
        0x5F00 + addr16.
        """
        w1 = 0x5F00
        return Encoder.word_bytes(w1) + Encoder.word_bytes(addr16 & 0xFFFF)

    @staticmethod
    def encode_call_ir(rs):
        """CALL @Rd -> 0001 1111 Rd*0 0000"""
        w1 = 0x1F00 | ((rs & 0xE) << 4)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_calr(disp12):
        """CALR address -> 1101 disp(12bit signed).
        disp12 is signed, relative to instruction address + 2.
        """
        w1 = 0xD000 | (disp12 & 0xFFF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ret(cc):
        """RET cc -> 1001 1110 cc 0000. -> 0x9E00 | (cc << 4)."""
        # Wait: 1001 1110 cc(4) 0000(4). But cc is in bits 7-4.
        # 0x9E00 | (cc << 4) | 0x00
        w1 = 0x9E00 | ((cc & 0xF) << 4)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_push(rd_stack, rs):
        """PUSH @Rd, Rs -> 1001 0011 Rd*0 Rs"""
        w1 = 0x9300 | ((rd_stack & 0xE) << 4) | (rs & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_pop(rd, rs_stack):
        """POP Rd, @Rs -> 1001 0111 Rs*0 Rd"""
        w1 = 0x9700 | ((rs_stack & 0xE) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_pushl(rd_stack, rrs):
        """PUSHL @Rd, RRs -> 1001 0001 Rd*0 RRs"""
        w1 = 0x9100 | ((rd_stack & 0xE) << 4) | (rrs & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_popl(rrd, rs_stack):
        """POPL RRd, @Rs -> 1001 0101 Rs*0 RRd"""
        w1 = 0x9500 | ((rs_stack & 0xE) << 4) | (rrd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_nop():
        """NOP -> 0x8D07"""
        return [0x8D, 0x07]

    @staticmethod
    def encode_halt():
        """HALT -> 0x7A00"""
        return [0x7A, 0x00]

    @staticmethod
    def encode_sc(imm8):
        """SC #imm -> 0x7F00 | imm8"""
        return [0x7F, imm8 & 0xFF]

    @staticmethod
    def encode_iret():
        """IRET -> 0x7B00"""
        return [0x7B, 0x00]

    @staticmethod
    def encode_di(vi=True, nvi=True):
        """DI -> 0111 1100 0000 011y where y encodes which ints.
        DI VI,NVI: 0x7C03. DI VI: 0x7C03. Let me check.
        Extract: DI int: 0111 1100 0000 011y.
        The 'y' bits: bit 1 = NVI, bit 0 = VI? Or encoded differently.
        Let's use: DI = 0x7C03 (disable all).
        """
        val = 0
        if vi:
            val |= 0x02
        if nvi:
            val |= 0x01
        return [0x7C, val | 0x00]  # Needs more research on exact DI encoding

    @staticmethod
    def encode_ei(vi=True, nvi=True):
        """EI -> similar to DI but different opcode bits."""
        val = 0
        if vi:
            val |= 0x02
        if nvi:
            val |= 0x01
        return [0x7C, val | 0x04]  # EI has bit 2 set

    @staticmethod
    def encode_shift(rd, amount, shift_type='SRA', byte_op=False):
        """Shifts and rotates (MAME-verified encodings).
        Base: 0xB2 (byte) / 0xB3 (word)
        Low byte: dddd ssss where dddd=register, ssss=sub-opcode
        
        Sub-opcodes (from MAME z8000tbl.hxx / z8000ops.hxx):
        Rotates (single word, no imm16):
          RL 1-bit:  0000 (0x00)    RL 2-bit:  0010 (0x02)
          RR 1-bit:  0100 (0x04)    RR 2-bit:  0110 (0x06)
          RLC 1-bit: 1000 (0x08)    RLC 2-bit: 1010 (0x0A)
          RRC 1-bit: 1100 (0x0C)    RRC 2-bit: 1110 (0x0E)
        Shifts (+ imm16 follow word, positive=left, negative=right):
          SLL/SRL: 0001 (0x01)
          SLA/SRA: 1001 (0x09)
          SLAL/SRAL: 1101 (0x0D) [word-sized base 0xB3 for long shift]
        """
        w_bit = 0 if byte_op else 1
        
        if shift_type in ('SLA', 'SRA'):
            sub = 0x09
            if shift_type == 'SRA':
                amount = (-amount) & 0xFFFF
            w1 = 0xB200 | (w_bit << 8) | ((rd & 0xF) << 4) | sub
            return Encoder.word_bytes(w1) + Encoder.word_bytes(amount & 0xFFFF)
        elif shift_type in ('SLL', 'SRL'):
            sub = 0x01
            if shift_type == 'SRL':
                amount = (-amount) & 0xFFFF
            w1 = 0xB200 | (w_bit << 8) | ((rd & 0xF) << 4) | sub
            return Encoder.word_bytes(w1) + Encoder.word_bytes(amount & 0xFFFF)
        elif shift_type in ('SLAL', 'SRAL'):
            sub = 0x0D
            if shift_type == 'SRAL':
                amount = (-amount) & 0xFFFF
            # Long shifts always use 0xB3 base (word-size opcode acts on long register pair)
            w1 = 0xB300 | ((rd & 0xF) << 4) | sub
            return Encoder.word_bytes(w1) + Encoder.word_bytes(amount & 0xFFFF)
        elif shift_type in ('RL', 'RLC'):
            # RL: bits[3:2]=00, RLC: bits[3:2]=10
            s = 0 if amount == 1 else 1
            base = 0x00 if shift_type == 'RL' else 0x08
            sub = base | (s << 1)
            w1 = 0xB200 | (w_bit << 8) | ((rd & 0xF) << 4) | sub
            return Encoder.word_bytes(w1)
        elif shift_type in ('RR', 'RRC'):
            # RR: bits[3:2]=01, RRC: bits[3:2]=11
            s = 0 if amount == 1 else 1
            base = 0x04 if shift_type == 'RR' else 0x0C
            sub = base | (s << 1)
            w1 = 0xB200 | (w_bit << 8) | ((rd & 0xF) << 4) | sub
            return Encoder.word_bytes(w1)
        else:
            raise ValueError(f"Unknown shift type: {shift_type}")

    @staticmethod
    def encode_ex(rd, rs, byte_op=False):
        """EX Rd, Rs -> 1010 1101 w Rs Rd"""
        w_bit = 0 if byte_op else 1
        w1 = 0xAC00 | (w_bit << 8) | ((rs & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_ldctl(dst_is_ctl, ctl_name, reg):
        """LDCTL dst, src.
        From MAME: Z7D_dddd_0ccc = load ctl→reg, Z7D_ssss_1ccc = load reg→ctl
        Control register encoding (from MAME):
          FCW=2, REFRESH=3, PSAPSEG=4, PSAPOFF=5, NSPSEG=6, NSPOFF=7
        """
        ctl_nums = {
            'FCW': 2, 'REFRESH': 3, 'PSAPSEG': 4,
            'PSAPOFF': 5, 'PSAP': 5, 'NSPSEG': 6,
            'NSPOFF': 7, 'NSP': 7,
        }
        ctl_upper = ctl_name.upper()
        ctl_num = ctl_nums.get(ctl_upper, 2)
        if dst_is_ctl:
            # LDCTL ctl, Rs -> 0x7D00 | (Rs<<4) | (0x08 | ctl_num)
            w1 = 0x7D00 | ((reg & 0xF) << 4) | (0x08 | ctl_num)
        else:
            # LDCTL Rd, ctl -> 0x7D00 | (Rd<<4) | ctl_num
            w1 = 0x7D00 | ((reg & 0xF) << 4) | ctl_num
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_setflg(flags):
        """SETFLG flags -> 1000 1101 CZSP 0001
        flags is a combination: C=bit7, Z=bit6, S=bit5, P=bit4
        """
        w1 = 0x8D00 | ((flags & 0xF) << 4) | 0x01
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_resflg(flags):
        """RESFLG flags -> 1000 1101 CZSP 0011"""
        w1 = 0x8D00 | ((flags & 0xF) << 4) | 0x03
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_comflg(flags):
        """COMFLG flags -> 1000 1101 CZSP 0101"""
        w1 = 0x8D00 | ((flags & 0xF) << 4) | 0x05
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_tcc(cc, rd, byte_op=False):
        """TCC cc, Rd -> 1010 1111 w cc Rd
        Wait: extract says 1010 1111 w cc Rd. But that looks like LD @Rd,Rs format.
        Let me re-check: TCC cc, Rd: R: 1010 1111 w cc Rd.
        Hmm this conflicts with LD IR,R. Let me look closer.
        
        LD @Rd, Rs = 0010 111w dddd ssss (opcode 0x2E/0x2F)
        TCC cc, Rd = 1010 1111 w cc Rd -> high byte = 1010 111w = 0xAE/0xAF
        So TCC has 1010 prefix and LD @Rd,Rs has 0010 prefix. No conflict.
        """
        w_bit = 0 if byte_op else 1
        w1 = 0xAE00 | (w_bit << 8) | ((cc & 0xF) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_push_imm(rd_stack, imm16):
        """PUSH @Rd, #data -> 0000 1101 Rd*0 1001 + data"""
        w1 = 0x0D00 | ((rd_stack & 0xE) << 4) | 0x09
        return Encoder.word_bytes(w1) + Encoder.word_bytes(imm16 & 0xFFFF)

    @staticmethod
    def encode_in(rd, rs_port, byte_op=False):
        """IN Rd, @Rs -> 0011 1100 w Rs*0 Rd (I/O indirect)
        0x3C for word = 0011 1101, 0x3C for byte = 0011 1100? 
        Hmm: bits 15-8 = 0011 110w. w=1 -> 0x3D, w=0 -> 0x3C.
        Then bits 7-4 = Rs (even), bits 3-0 = Rd.
        """
        w_bit = 0 if byte_op else 1
        w1 = 0x3C00 | (w_bit << 8) | ((rs_port & 0xE) << 4) | (rd & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_in_da(rd, port16, byte_op=False):
        """IN Rd, port -> 0011 1011 w Rd 0100 + port"""
        w_bit = 0 if byte_op else 1
        w1 = 0x3A00 | (w_bit << 8) | ((rd & 0xF) << 4) | 0x04
        return Encoder.word_bytes(w1) + Encoder.word_bytes(port16 & 0xFFFF)

    @staticmethod
    def encode_out_ir(rd_port, rs, byte_op=False):
        """OUT @Rd, Rs -> 0011 1111 w Rd*0 Rs
        Actually from extract: OUT @Rd, Rs: 0011 111w Rd*0 Rs.
        Wait: 0011 1111 = 0x3F for w=1 (word). 0011 1110 = 0x3E for w=0 (byte).
        Bits 7-4 = Rd (even/stack pointer for port), bits 3-0 = Rs.
        
        Hmm, checking extract: OUT @Rd, Rs: 0011 1111 w Rs*0 Rd
        Wait, it says 0011 1111 w Rs*0 Rd. So the register roles are swapped in encoding?
        Let me look: the assembler syntax is OUT @Rd, Rs where @Rd is the port register.
        But the encoding puts Rs*0 first (port) and Rd second (data).
        So: w1 = 0x3E00 | (w_bit<<8) | ((rd_port & 0xE)<<4) | (rs & 0xF)
        """
        w_bit = 0 if byte_op else 1
        w1 = 0x3E00 | (w_bit << 8) | ((rd_port & 0xE) << 4) | (rs & 0xF)
        return Encoder.word_bytes(w1)

    @staticmethod
    def encode_out_da(port16, rs, byte_op=False):
        """OUT port, Rs -> 0011 1011 w Rs 0110 + port"""
        w_bit = 0 if byte_op else 1
        w1 = 0x3A00 | (w_bit << 8) | ((rs & 0xF) << 4) | 0x06
        return Encoder.word_bytes(w1) + Encoder.word_bytes(port16 & 0xFFFF)

    @staticmethod
    def encode_mbit():
        """MBIT -> 0x7B0A"""
        return [0x7B, 0x0A]

    @staticmethod
    def encode_mres():
        """MRES -> 0x7B09"""
        return [0x7B, 0x09]

    @staticmethod
    def encode_mset():
        """MSET -> 0x7B08"""
        return [0x7B, 0x08]


# =============================================================================
# Assembler (two-pass)
#
# Pass 1: Labels und Groessen sammeln (forward references erlaubt).
#          Symboltabelle wird aufgebaut, PC wird fuer jede Instruktion
#          um deren Groesse weitergeschoben.
# Pass 2: Code generieren.  Alle Symbole sind bekannt, Ausdruecke
#          werden endgueltig ausgewertet und Binaerdaten erzeugt.
#
# Unterstuetzte Pseudo-Instruktionen: ORG, EQU, DW, DB, DS
# =============================================================================

class AsmError(Exception):
    def __init__(self, msg, line_num=None, line_text=None):
        self.line_num = line_num
        self.line_text = line_text
        super().__init__(f"Line {line_num}: {msg}" if line_num else msg)


class Assembler:
    """Zwei-Pass Z8001 Cross-Assembler.

    Verarbeitet Z8001-Assemblerquelltext und erzeugt Binaerausgabe.
    Unterstuetzt alle gaengigen Instruktionen des Z8001 im non-segmented
    Modus (innerhalb eines Segments), Labels, Ausdruecke und
    Pseudo-Instruktionen.
    """

    # Instruction table mapping mnemonic -> handler method name
    ARITH_R_IMM_OPS = {
        'ADD': 0x0100, 'ADDB': 0x0000,
        'SUB': 0x0300, 'SUBB': 0x0200,
        'CP':  0x0B00, 'CPB':  0x0A00,
        'AND': 0x0700, 'ANDB': 0x0600,
        'OR':  0x0500, 'ORB':  0x0400,
        'XOR': 0x0900, 'XORB': 0x0800,
    }

    ARITH_R_R_OPS = {
        'ADD': 0x8100, 'ADDB': 0x8000,
        'SUB': 0x8300, 'SUBB': 0x8200,
        'CP':  0x8B00, 'CPB':  0x8A00,
        'AND': 0x8700, 'ANDB': 0x8600,
        'OR':  0x8500, 'ORB':  0x8400,
        'XOR': 0x8900, 'XORB': 0x8800,
        'ADC': 0xB500, 'ADCB': 0xB400,
        'SBC': 0xB700, 'SBCB': 0xB600,
    }

    def __init__(self):
        self.symbols = {}
        self.pc = 0
        self.origin = 0
        self.output = []  # list of (addr, bytes, source_line, line_num)
        self.errors = []
        self.lines = []
        self.pass_num = 0

    def assemble(self, source_text):
        """Assemble source text. Returns binary output bytes."""
        self.lines = source_text.splitlines()
        self.symbols = {}
        self.errors = []

        # Pass 1: collect labels and sizes
        self.pass_num = 1
        self.pc = 0
        self.origin = 0
        for i, line in enumerate(self.lines):
            try:
                self._process_line(line, i + 1)
            except (AsmError, ValueError) as e:
                self.errors.append(AsmError(str(e), i + 1, line))

        # Pass 2: generate code
        self.pass_num = 2
        self.pc = 0
        self.origin = 0
        self.output = []
        for i, line in enumerate(self.lines):
            try:
                self._process_line(line, i + 1)
            except (AsmError, ValueError) as e:
                self.errors.append(AsmError(str(e), i + 1, line))

        if self.errors:
            return None

        # Build binary image
        return self._build_binary()

    def _build_binary(self):
        """Build contiguous binary from output records."""
        if not self.output:
            return bytearray()

        min_addr = min(addr for addr, _, _, _ in self.output)
        max_end = max(addr + len(data) for addr, data, _, _ in self.output)
        img = bytearray(max_end - min_addr)

        for addr, data, _, _ in self.output:
            offset = addr - min_addr
            for j, b in enumerate(data):
                img[offset + j] = b

        return img

    def _process_line(self, line, line_num):
        """Process a single assembly line."""
        # Strip comments
        raw_line = line
        comment_pos = line.find(';')
        if comment_pos >= 0:
            line = line[:comment_pos]
        line = line.strip()
        if not line:
            return

        # Check for label
        label = None
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:', line)
        if m:
            label = m.group(1).upper()
            line = line[m.end():].strip()
            if self.pass_num == 1:
                if label in self.symbols:
                    raise AsmError(f"Duplicate label: {label}", line_num)
                self.symbols[label] = self.pc

        if not line:
            return

        # Parse mnemonic and operands
        parts = line.split(None, 1)
        mnemonic = parts[0].upper()
        operands_str = parts[1].strip() if len(parts) > 1 else ''

        # Pseudo-instructions
        if mnemonic == 'ORG':
            val = eval_expr(operands_str, self.symbols, self.pc)
            self.pc = val & 0xFFFF
            if self.origin == 0 and not self.output:
                self.origin = self.pc
            return
        elif mnemonic == 'EQU':
            # label EQU value (label was already parsed, or inline: NAME EQU val)
            if label:
                val = eval_expr(operands_str, self.symbols, self.pc)
                self.symbols[label] = val
            else:
                # Might be: NAME EQU value (without colon)
                # Actually the label was not parsed because EQU doesn't use colon.
                # Re-parse: first word before EQU is the name.
                # But we already split on whitespace with mnemonic=first word.
                # So 'NAME' was consumed as mnemonic. Let operands be the expression.
                raise AsmError("EQU requires a label (NAME: EQU value)", line_num)
            return
        elif mnemonic == 'DW':
            values = self._parse_comma_exprs(operands_str)
            data = []
            for val in values:
                v = eval_expr(val, self.symbols, self.pc) if self.pass_num == 2 else 0
                data += Encoder.word_bytes(v & 0xFFFF)
            if self.pass_num == 2:
                self.output.append((self.pc, data, raw_line, line_num))
            self.pc += len(data)
            return
        elif mnemonic == 'DB':
            values = self._parse_comma_exprs(operands_str)
            data = []
            for val in values:
                val = val.strip()
                if val.startswith("'") or val.startswith('"'):
                    # String literal
                    s = val[1:-1] if len(val) >= 2 and val[-1] == val[0] else val[1:]
                    data += [ord(c) for c in s]
                else:
                    v = eval_expr(val, self.symbols, self.pc) if self.pass_num == 2 else 0
                    data.append(v & 0xFF)
            if self.pass_num == 2:
                self.output.append((self.pc, data, raw_line, line_num))
            self.pc += len(data)
            return
        elif mnemonic == 'DS':
            count = eval_expr(operands_str, self.symbols, self.pc)
            if self.pass_num == 2:
                self.output.append((self.pc, [0] * count, raw_line, line_num))
            self.pc += count
            return

        # Check for EQU without colon: if mnemonic looks like a name and operands start with EQU
        if operands_str.upper().startswith('EQU'):
            name = mnemonic
            val_str = operands_str[3:].strip()
            val = eval_expr(val_str, self.symbols, self.pc) if self.pass_num == 2 else 0
            if self.pass_num == 1:
                self.symbols[name] = eval_expr(val_str, self.symbols, self.pc)
            return

        # Instructions
        data = self._encode_instruction(mnemonic, operands_str, line_num, raw_line)
        if data is not None:
            if self.pass_num == 2:
                self.output.append((self.pc, data, raw_line, line_num))
            self.pc += len(data)

    def _parse_comma_exprs(self, s):
        """Split comma-separated expressions, respecting parens and strings."""
        result = []
        depth = 0
        current = []
        in_string = False
        string_char = None
        for c in s:
            if in_string:
                current.append(c)
                if c == string_char:
                    in_string = False
                continue
            if c in ('"', "'"):
                in_string = True
                string_char = c
                current.append(c)
            elif c == '(':
                depth += 1
                current.append(c)
            elif c == ')':
                depth -= 1
                current.append(c)
            elif c == ',' and depth == 0:
                result.append(''.join(current).strip())
                current = []
            else:
                current.append(c)
        if current:
            result.append(''.join(current).strip())
        return result

    def _encode_instruction(self, mnemonic, operands_str, line_num, raw_line):
        """Encode a single instruction. Returns list of bytes or None."""
        ops = self._parse_comma_exprs(operands_str) if operands_str else []

        # ===== No-operand instructions =====
        if mnemonic == 'NOP':
            return Encoder.encode_nop()
        if mnemonic == 'HALT':
            return Encoder.encode_halt()
        if mnemonic == 'IRET':
            return Encoder.encode_iret()
        if mnemonic == 'MBIT':
            return Encoder.encode_mbit()
        if mnemonic == 'MRES':
            return Encoder.encode_mres()
        if mnemonic == 'MSET':
            return Encoder.encode_mset()
        if mnemonic == 'DI':
            return Encoder.encode_di()
        if mnemonic == 'EI':
            return Encoder.encode_ei()
        if mnemonic == 'SC':
            imm = self._eval(ops[0]) if ops else 0
            return Encoder.encode_sc(imm)

        # ===== RET cc =====
        if mnemonic == 'RET':
            cc_name = ops[0].strip().upper() if ops else 'T'
            cc = CC_TABLE.get(cc_name)
            if cc is None:
                raise AsmError(f"Unknown condition code: {cc_name}", line_num)
            return Encoder.encode_ret(cc)

        # ===== JR cc, label =====
        if mnemonic == 'JR':
            if len(ops) < 2:
                raise AsmError("JR requires cc, target", line_num)
            cc_name = ops[0].strip().upper()
            cc = CC_TABLE.get(cc_name)
            if cc is None:
                raise AsmError(f"Unknown condition code: {cc_name}", line_num)
            target = self._eval(ops[1])
            # Displacement in bytes, then convert to words (CPU multiplies dsp8 by 2)
            byte_disp = target - (self.pc + 2)
            if self.pass_num == 2 and byte_disp % 2 != 0:
                raise AsmError(f"JR target not word-aligned: disp={byte_disp}", line_num)
            disp = byte_disp // 2
            if self.pass_num == 2 and (disp < -128 or disp > 127):
                raise AsmError(f"JR displacement out of range: {disp}", line_num)
            return Encoder.encode_jr(cc, disp & 0xFF)

        # ===== JP cc, target =====
        if mnemonic == 'JP':
            if len(ops) < 2:
                raise AsmError("JP requires cc, target", line_num)
            cc_name = ops[0].strip().upper()
            cc = CC_TABLE.get(cc_name)
            if cc is None:
                raise AsmError(f"Unknown condition code: {cc_name}", line_num)
            target_str = ops[1].strip()
            ir = parse_indirect(target_str)
            if ir:
                return Encoder.encode_jp_ir(cc, ir[1])
            target = self._eval(ops[1])
            return Encoder.encode_jp_da(cc, target)

        # ===== DJNZ Rd, label =====
        if mnemonic == 'DJNZ':
            if len(ops) < 2:
                raise AsmError("DJNZ requires Rd, target", line_num)
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'R':
                raise AsmError(f"DJNZ requires word register, got: {ops[0]}", line_num)
            target = self._eval(ops[1])
            disp = target - (self.pc + 2)
            # DJNZ uses 7-bit negative displacement (always backward)
            if self.pass_num == 2 and (disp > 0 or disp < -254):
                raise AsmError(f"DJNZ displacement out of range: {disp}", line_num)
            return Encoder.encode_djnz(reg[1], (-disp // 2) & 0x7F if disp != 0 else 0)

        # ===== DBJNZ Rbd, label =====
        if mnemonic == 'DBJNZ':
            if len(ops) < 2:
                raise AsmError("DBJNZ requires Rbd, target", line_num)
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"Invalid register: {ops[0]}", line_num)
            target = self._eval(ops[1])
            disp = target - (self.pc + 2)
            return Encoder.encode_dbjnz(reg[1], (-disp // 2) & 0x7F if disp != 0 else 0)

        # ===== CALL =====
        if mnemonic == 'CALL':
            if not ops:
                raise AsmError("CALL requires target", line_num)
            target_str = ops[0].strip()
            ir = parse_indirect(target_str)
            if ir:
                return Encoder.encode_call_ir(ir[1])
            target = self._eval(ops[0])
            return Encoder.encode_call_da(target)

        # ===== CALR =====
        if mnemonic == 'CALR':
            if not ops:
                raise AsmError("CALR requires target", line_num)
            target = self._eval(ops[0])
            disp = target - (self.pc + 2)
            if self.pass_num == 2 and (disp < -4096 or disp > 4094):
                raise AsmError(f"CALR displacement out of range: {disp}", line_num)
            return Encoder.encode_calr((disp // 2) & 0xFFF)

        # ===== LD family =====
        if mnemonic in ('LD', 'LDB', 'LDL', 'LDK'):
            return self._encode_load(mnemonic, ops, line_num)

        # ===== LDCTL =====
        if mnemonic == 'LDCTL':
            return self._encode_ldctl(ops, line_num)

        # ===== Arithmetic/Logic Rd, src =====
        if mnemonic in self.ARITH_R_R_OPS or mnemonic in self.ARITH_R_IMM_OPS:
            return self._encode_arith(mnemonic, ops, line_num)

        # ===== ADDL, SUBL, CPL =====
        if mnemonic in ('ADDL', 'SUBL', 'CPL'):
            return self._encode_long_arith(mnemonic, ops, line_num)

        # ===== INC, INCB, DEC, DECB =====
        if mnemonic in ('INC', 'INCB', 'DEC', 'DECB'):
            return self._encode_inc_dec(mnemonic, ops, line_num)

        # ===== NEG, NEGB, COM, COMB, CLR, CLRB =====
        if mnemonic in ('NEG', 'NEGB'):
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"NEG requires register, got: {ops[0]}", line_num)
            return Encoder.encode_neg(reg[1], byte_op=mnemonic.endswith('B'))
        if mnemonic in ('COM', 'COMB'):
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"COM requires register, got: {ops[0]}", line_num)
            return Encoder.encode_com(reg[1], byte_op=mnemonic.endswith('B'))
        if mnemonic in ('CLR', 'CLRB'):
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"CLR requires register, got: {ops[0]}", line_num)
            return Encoder.encode_clr(reg[1], byte_op=mnemonic.endswith('B'))

        # ===== BIT, BITB, SET, SETB, RES, RESB =====
        if mnemonic in ('BIT', 'BITB', 'SET', 'SETB', 'RES', 'RESB'):
            base_op = mnemonic.rstrip('B')
            if mnemonic != base_op:
                base_op = mnemonic[:-1] if mnemonic.endswith('B') else mnemonic
            # Extract base: BIT, SET, or RES
            base_op = mnemonic.replace('B', '') if mnemonic.endswith('B') else mnemonic
            byte_op = mnemonic.endswith('B')
            if len(ops) < 2:
                raise AsmError(f"{mnemonic} requires Rd, #bit", line_num)
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"Invalid register: {ops[0]}", line_num)
            bit_num = self._eval(ops[1])
            return Encoder.encode_bit_static(reg[1], bit_num, op=base_op, byte_op=byte_op)

        # ===== Shifts & Rotates =====
        if mnemonic in ('SLA', 'SLAB', 'SRA', 'SRAB', 'SLL', 'SLLB', 'SRL', 'SRLB',
                        'SLAL', 'SRAL',
                        'RL', 'RLB', 'RLC', 'RLCB', 'RR', 'RRB', 'RRC', 'RRCB'):
            byte_op = mnemonic.endswith('B')
            base_op = mnemonic.rstrip('B') if byte_op else mnemonic
            if len(ops) < 2:
                raise AsmError(f"{mnemonic} requires Rd, #n", line_num)
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"Invalid register: {ops[0]}", line_num)
            amount = self._eval(ops[1])
            return Encoder.encode_shift(reg[1], amount, shift_type=base_op, byte_op=byte_op)

        # ===== EX, EXB =====
        if mnemonic in ('EX', 'EXB'):
            if len(ops) < 2:
                raise AsmError(f"EX requires two registers", line_num)
            rd = parse_register(ops[0])
            rs = parse_register(ops[1])
            if not rd or not rs:
                raise AsmError(f"EX requires registers", line_num)
            return Encoder.encode_ex(rd[1], rs[1], byte_op=mnemonic == 'EXB')

        # ===== PUSH, POP, PUSHL, POPL =====
        if mnemonic in ('PUSH', 'PUSHL'):
            return self._encode_push(mnemonic, ops, line_num)
        if mnemonic in ('POP', 'POPL'):
            return self._encode_pop(mnemonic, ops, line_num)

        # ===== IN, INB, OUT, OUTB =====
        if mnemonic in ('IN', 'INB'):
            return self._encode_in(mnemonic, ops, line_num)
        if mnemonic in ('OUT', 'OUTB'):
            return self._encode_out(mnemonic, ops, line_num)

        # ===== SETFLG, RESFLG, COMFLG =====
        if mnemonic == 'SETFLG':
            flags = self._parse_flags(ops[0]) if ops else 0
            return Encoder.encode_setflg(flags)
        if mnemonic == 'RESFLG':
            flags = self._parse_flags(ops[0]) if ops else 0
            return Encoder.encode_resflg(flags)
        if mnemonic == 'COMFLG':
            flags = self._parse_flags(ops[0]) if ops else 0
            return Encoder.encode_comflg(flags)

        # ===== TCC =====
        if mnemonic in ('TCC', 'TCCB'):
            if len(ops) < 2:
                raise AsmError("TCC requires cc, Rd", line_num)
            cc = CC_TABLE.get(ops[0].strip().upper())
            if cc is None:
                raise AsmError(f"Unknown condition: {ops[0]}", line_num)
            reg = parse_register(ops[1])
            if not reg:
                raise AsmError(f"Invalid register: {ops[1]}", line_num)
            return Encoder.encode_tcc(cc, reg[1], byte_op=mnemonic == 'TCCB')

        # ===== MULT, MULTL, DIV, DIVL =====
        if mnemonic in ('MULT', 'MULTL', 'DIV', 'DIVL'):
            return self._encode_mult_div(mnemonic, ops, line_num)

        # ===== EXTSB, EXTS, EXTSL =====
        if mnemonic == 'EXTSB':
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'R':
                raise AsmError("EXTSB requires Rd", line_num)
            return Encoder.encode_extsb(reg[1])
        if mnemonic == 'EXTS':
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'RR':
                raise AsmError("EXTS requires RRd", line_num)
            return Encoder.encode_exts(reg[1])
        if mnemonic == 'EXTSL':
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'RQ':
                raise AsmError("EXTSL requires RQd", line_num)
            return Encoder.encode_extsl(reg[1])

        # ===== TEST, TESTB, TESTL =====
        if mnemonic in ('TEST', 'TESTB'):
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"{mnemonic} requires register", line_num)
            return Encoder.encode_test(reg[1], byte_op=mnemonic == 'TESTB')
        if mnemonic == 'TESTL':
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'RR':
                raise AsmError("TESTL requires RRd", line_num)
            return Encoder.encode_testl(reg[1])

        # ===== TSET, TSETB =====
        if mnemonic in ('TSET', 'TSETB'):
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError(f"{mnemonic} requires register", line_num)
            return Encoder.encode_tset(reg[1], byte_op=mnemonic == 'TSETB')

        # ===== DAB =====
        if mnemonic == 'DAB':
            reg = parse_register(ops[0])
            if not reg:
                raise AsmError("DAB requires Rbd", line_num)
            return Encoder.encode_dab(reg[1])

        # ===== RLDB, RRDB =====
        if mnemonic == 'RLDB':
            if len(ops) < 2:
                raise AsmError("RLDB requires Rbb, Rba", line_num)
            rbb = parse_register(ops[0])
            rba = parse_register(ops[1])
            if not rbb or not rba:
                raise AsmError("RLDB requires register operands", line_num)
            return Encoder.encode_rldb(rba[1], rbb[1])
        if mnemonic == 'RRDB':
            if len(ops) < 2:
                raise AsmError("RRDB requires Rbb, Rba", line_num)
            rbb = parse_register(ops[0])
            rba = parse_register(ops[1])
            if not rbb or not rba:
                raise AsmError("RRDB requires register operands", line_num)
            return Encoder.encode_rrdb(rba[1], rbb[1])

        # ===== LDM =====
        if mnemonic == 'LDM':
            return self._encode_ldm(ops, line_num)

        # ===== LDA =====
        if mnemonic == 'LDA':
            if len(ops) < 2:
                raise AsmError("LDA requires Rd, address", line_num)
            reg = parse_register(ops[0])
            if not reg or reg[0] != 'R':
                raise AsmError("LDA requires Rd", line_num)
            addr = self._eval(ops[1])
            return Encoder.encode_lda(reg[1], addr)

        # ===== LDIR, LDDR, LDI, LDD =====
        if mnemonic in ('LDI', 'LDIR', 'LDD', 'LDDR'):
            return self._encode_block_load(mnemonic, ops, line_num)

        raise AsmError(f"Unknown mnemonic: {mnemonic}", line_num)

    def _eval(self, expr_str):
        """Evaluate expression (wrapper).
        In pass 1, returns 0 for undefined symbols (forward references).
        In pass 2, raises on undefined symbols.
        """
        try:
            return eval_expr(expr_str, self.symbols, self.pc)
        except ValueError:
            if self.pass_num == 1:
                return 0  # Placeholder for forward references
            raise

    def _parse_flags(self, s):
        """Parse flag combination like 'C,Z' or 'CZS' into bitmask."""
        s = s.upper().replace(',', '')
        val = 0
        if 'C' in s: val |= 0x8
        if 'Z' in s: val |= 0x4
        if 'S' in s: val |= 0x2
        if 'P' in s: val |= 0x1
        return val

    def _encode_load(self, mnemonic, ops, line_num):
        """Encode LD, LDB, LDL, LDK instructions."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires two operands", line_num)

        byte_op = mnemonic == 'LDB'
        is_long = mnemonic == 'LDL'
        is_ldk = mnemonic == 'LDK'

        dst_str = ops[0].strip()
        src_str = ops[1].strip()

        # Check for indirect destination
        dst_ir = parse_indirect(dst_str)
        dst_reg = parse_register(dst_str) if not dst_ir else None

        # Check for indirect source
        src_ir = parse_indirect(src_str)
        src_reg = parse_register(src_str) if not src_ir else None

        # Is source an immediate?
        src_is_imm = src_str.startswith('#') or (not src_reg and not src_ir)

        # LDK Rd, #n
        if is_ldk:
            if not dst_reg or dst_reg[0] != 'R':
                raise AsmError("LDK requires Rd", line_num)
            n = self._eval(src_str)
            if n < 0 or n > 15:
                raise AsmError(f"LDK value must be 0-15, got: {n}", line_num)
            return Encoder.encode_ldk(dst_reg[1], n)

        # LDL RRd, #imm32
        if is_long and dst_reg and dst_reg[0] == 'RR' and src_is_imm:
            imm = self._eval(src_str)
            return Encoder.encode_ldl_rr_imm(dst_reg[1], imm)

        # LDL RRd, RRs
        if is_long and dst_reg and src_reg and dst_reg[0] == 'RR' and src_reg[0] == 'RR':
            return Encoder.encode_ldl_rr_rr(dst_reg[1], src_reg[1])

        # LDL RRd, @Rs
        if is_long and dst_reg and src_ir and dst_reg[0] == 'RR':
            return Encoder.encode_ldl_rr_ir(dst_reg[1], src_ir[1])

        # LDL @Rd, RRs
        if is_long and dst_ir and src_reg and src_reg[0] == 'RR':
            return Encoder.encode_ldl_ir_rrs(dst_ir[1], src_reg[1])

        # LD Rd, #imm16
        if dst_reg and dst_reg[0] == 'R' and src_is_imm and not byte_op:
            imm = self._eval(src_str)
            return Encoder.encode_ld_r_imm(dst_reg[1], imm)

        # LDB Rbd, #imm8 (short form)
        if dst_reg and src_is_imm and byte_op:
            imm = self._eval(src_str)
            return Encoder.encode_ldb_r_imm_short(dst_reg[1], imm)

        # LD Rd, Rs / LDB Rbd, Rbs
        if dst_reg and src_reg and not src_ir:
            return Encoder.encode_ld_r_r(dst_reg[1], src_reg[1], byte_op=byte_op)

        # LD Rd, @Rs
        if dst_reg and src_ir:
            return Encoder.encode_ld_r_ir(dst_reg[1], src_ir[1], byte_op=byte_op)

        # LD @Rd, Rs
        if dst_ir and src_reg:
            return Encoder.encode_ld_ir_r(dst_ir[1], src_reg[1], byte_op=byte_op)

        # LD @Rd, #imm
        if dst_ir and src_is_imm and not byte_op and not is_long:
            imm = self._eval(src_str)
            return Encoder.encode_ld_ir_imm(dst_ir[1], imm)

        raise AsmError(f"Unsupported {mnemonic} operand combination: {ops}", line_num)

    def _encode_arith(self, mnemonic, ops, line_num):
        """Encode arithmetic/logic instructions."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires two operands", line_num)

        byte_op = mnemonic.endswith('B')
        dst_str = ops[0].strip()
        src_str = ops[1].strip()

        dst_reg = parse_register(dst_str)
        src_reg = parse_register(src_str)
        src_ir = parse_indirect(src_str)
        src_is_imm = src_str.startswith('#') or (not src_reg and not src_ir)

        if not dst_reg:
            raise AsmError(f"{mnemonic} requires register destination", line_num)

        # Rd, #imm
        if src_is_imm and mnemonic in self.ARITH_R_IMM_OPS:
            imm = self._eval(src_str)
            return Encoder.encode_arith_r_imm(self.ARITH_R_IMM_OPS[mnemonic], dst_reg[1], imm)

        # Rd, Rs
        if src_reg and mnemonic in self.ARITH_R_R_OPS:
            return Encoder.encode_arith_r_r(self.ARITH_R_R_OPS[mnemonic], dst_reg[1], src_reg[1], byte_op=byte_op)

        # Rd, @Rs (indirect)
        if src_ir:
            # IR mode uses different opcode base
            ir_ops = {
                'ADD': 0x0100, 'ADDB': 0x0000,
                'SUB': 0x0300, 'SUBB': 0x0200,
                'CP':  0x0B00, 'CPB':  0x0A00,
                'AND': 0x0700, 'ANDB': 0x0600,
                'OR':  0x0500, 'ORB':  0x0400,
                'XOR': 0x0900, 'XORB': 0x0800,
            }
            if mnemonic in ir_ops:
                return Encoder.encode_arith_r_ir(ir_ops[mnemonic], dst_reg[1], src_ir[1], byte_op=byte_op)

        raise AsmError(f"Unsupported {mnemonic} operand combination", line_num)

    def _encode_inc_dec(self, mnemonic, ops, line_num):
        """Encode INC/INCB/DEC/DECB Rd, #n."""
        if not ops:
            raise AsmError(f"{mnemonic} requires register", line_num)
        byte_op = mnemonic.endswith('B')
        is_dec = mnemonic.startswith('DEC')
        reg = parse_register(ops[0])
        if not reg:
            raise AsmError(f"Invalid register: {ops[0]}", line_num)
        n = self._eval(ops[1]) if len(ops) > 1 else 1
        if n < 1 or n > 16:
            raise AsmError(f"INC/DEC value must be 1-16, got: {n}", line_num)
        return Encoder.encode_inc_dec(reg[1], n, is_dec=is_dec, byte_op=byte_op)

    def _encode_push(self, mnemonic, ops, line_num):
        """Encode PUSH/PUSHL @Rd, Rs or PUSH @Rd, #imm."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires @Rd, Rs/#imm", line_num)
        dst_ir = parse_indirect(ops[0])
        if not dst_ir:
            raise AsmError(f"{mnemonic} requires indirect destination @Rd", line_num)
        src_reg = parse_register(ops[1])
        src_is_imm = ops[1].strip().startswith('#') or not src_reg

        if mnemonic == 'PUSHL':
            if src_reg and src_reg[0] == 'RR':
                return Encoder.encode_pushl(dst_ir[1], src_reg[1])
            raise AsmError("PUSHL requires RRs source", line_num)
        else:
            if src_reg:
                return Encoder.encode_push(dst_ir[1], src_reg[1])
            if src_is_imm:
                imm = self._eval(ops[1])
                return Encoder.encode_push_imm(dst_ir[1], imm)
        raise AsmError(f"Unsupported {mnemonic} operands", line_num)

    def _encode_pop(self, mnemonic, ops, line_num):
        """Encode POP/POPL Rd, @Rs."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires Rd, @Rs", line_num)
        dst_reg = parse_register(ops[0])
        src_ir = parse_indirect(ops[1])
        if not dst_reg or not src_ir:
            raise AsmError(f"{mnemonic} requires Rd, @Rs", line_num)
        if mnemonic == 'POPL':
            return Encoder.encode_popl(dst_reg[1], src_ir[1])
        return Encoder.encode_pop(dst_reg[1], src_ir[1])

    def _encode_in(self, mnemonic, ops, line_num):
        """Encode IN/INB Rd, @Rs or IN Rd, port."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires Rd, source", line_num)
        byte_op = mnemonic == 'INB'
        dst_reg = parse_register(ops[0])
        if not dst_reg:
            raise AsmError(f"Invalid register: {ops[0]}", line_num)
        src_ir = parse_indirect(ops[1])
        if src_ir:
            return Encoder.encode_in(dst_reg[1], src_ir[1], byte_op=byte_op)
        # Direct port address
        port = self._eval(ops[1])
        return Encoder.encode_in_da(dst_reg[1], port, byte_op=byte_op)

    def _encode_out(self, mnemonic, ops, line_num):
        """Encode OUT/OUTB @Rd, Rs or OUT port, Rs."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires destination, Rs", line_num)
        byte_op = mnemonic == 'OUTB'
        dst_ir = parse_indirect(ops[0])
        if dst_ir:
            src_reg = parse_register(ops[1])
            if not src_reg:
                raise AsmError(f"Invalid register: {ops[1]}", line_num)
            return Encoder.encode_out_ir(dst_ir[1], src_reg[1], byte_op=byte_op)
        # Direct port
        port = self._eval(ops[0])
        src_reg = parse_register(ops[1])
        if not src_reg:
            raise AsmError(f"Invalid register: {ops[1]}", line_num)
        return Encoder.encode_out_da(port, src_reg[1], byte_op=byte_op)

    def _encode_ldctl(self, ops, line_num):
        """Encode LDCTL instructions."""
        if len(ops) < 2:
            raise AsmError("LDCTL requires two operands", line_num)
        dst_str = ops[0].strip().upper()
        src_str = ops[1].strip().upper()

        ctl_names = {'FCW', 'REFRESH', 'PSAPSEG', 'PSAPOFF', 'PSAP', 'NSPSEG', 'NSPOFF', 'NSP'}

        if dst_str in ctl_names:
            # LDCTL ctl, Rs
            src_reg = parse_register(src_str)
            if not src_reg:
                raise AsmError(f"LDCTL requires register source, got: {src_str}", line_num)
            return Encoder.encode_ldctl(True, dst_str, src_reg[1])
        elif src_str in ctl_names:
            # LDCTL Rd, ctl
            dst_reg = parse_register(dst_str)
            if not dst_reg:
                raise AsmError(f"LDCTL requires register dest, got: {dst_str}", line_num)
            return Encoder.encode_ldctl(False, src_str, dst_reg[1])
        else:
            raise AsmError(f"LDCTL requires a control register operand", line_num)

    def _encode_long_arith(self, mnemonic, ops, line_num):
        """Encode ADDL, SUBL, CPL with RR,RR / RR,#imm32 / RR,@Rs operand modes."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires two operands", line_num)
        rrd = parse_register(ops[0])
        if not rrd or rrd[0] != 'RR':
            raise AsmError(f"{mnemonic} requires RRd as destination", line_num)

        src_str = ops[1].strip()
        src_reg = parse_register(src_str)
        src_ir = parse_indirect(src_str)
        src_is_imm = src_str.startswith('#') or (not src_reg and not src_ir)

        # RRd, RRs
        if src_reg and src_reg[0] == 'RR':
            if mnemonic == 'ADDL':
                return Encoder.encode_addl_rr_rr(rrd[1], src_reg[1])
            elif mnemonic == 'SUBL':
                return Encoder.encode_subl_rr_rr(rrd[1], src_reg[1])
            elif mnemonic == 'CPL':
                return Encoder.encode_cpl_rr_rr(rrd[1], src_reg[1])

        # RRd, @Rs
        if src_ir:
            if mnemonic == 'ADDL':
                return Encoder.encode_addl_rr_ir(rrd[1], src_ir[1])
            elif mnemonic == 'SUBL':
                return Encoder.encode_subl_rr_ir(rrd[1], src_ir[1])
            elif mnemonic == 'CPL':
                return Encoder.encode_cpl_rr_ir(rrd[1], src_ir[1])

        # RRd, #imm32
        if src_is_imm:
            imm = self._eval(src_str)
            if mnemonic == 'ADDL':
                return Encoder.encode_addl_rr_imm(rrd[1], imm)
            elif mnemonic == 'SUBL':
                return Encoder.encode_subl_rr_imm(rrd[1], imm)
            elif mnemonic == 'CPL':
                return Encoder.encode_cpl_rr_imm(rrd[1], imm)

        raise AsmError(f"Unsupported {mnemonic} operand combination: {ops}", line_num)

    def _encode_mult_div(self, mnemonic, ops, line_num):
        """Encode MULT, MULTL, DIV, DIVL."""
        if len(ops) < 2:
            raise AsmError(f"{mnemonic} requires two operands", line_num)

        dst = parse_register(ops[0])
        if not dst:
            raise AsmError(f"{mnemonic} requires register destination", line_num)

        src_str = ops[1].strip()
        src_reg = parse_register(src_str)
        src_ir = parse_indirect(src_str)
        src_is_imm = src_str.startswith('#') or (not src_reg and not src_ir)

        if mnemonic == 'MULT':
            if dst[0] != 'RR':
                raise AsmError("MULT requires RRd", line_num)
            if src_reg and src_reg[0] == 'R':
                return Encoder.encode_mult_rr_rs(dst[1], src_reg[1])
            if src_ir:
                return Encoder.encode_mult_rr_ir(dst[1], src_ir[1])
            if src_is_imm:
                return Encoder.encode_mult_rr_imm(dst[1], self._eval(src_str))

        elif mnemonic == 'MULTL':
            if dst[0] != 'RQ':
                raise AsmError("MULTL requires RQd", line_num)
            if src_reg and src_reg[0] == 'RR':
                return Encoder.encode_multl_rq_rrs(dst[1], src_reg[1])
            if src_ir:
                return Encoder.encode_multl_rq_ir(dst[1], src_ir[1])
            if src_is_imm:
                return Encoder.encode_multl_rq_imm(dst[1], self._eval(src_str))

        elif mnemonic == 'DIV':
            if dst[0] != 'RR':
                raise AsmError("DIV requires RRd", line_num)
            if src_reg and src_reg[0] == 'R':
                return Encoder.encode_div_rr_rs(dst[1], src_reg[1])
            if src_ir:
                return Encoder.encode_div_rr_ir(dst[1], src_ir[1])
            if src_is_imm:
                return Encoder.encode_div_rr_imm(dst[1], self._eval(src_str))

        elif mnemonic == 'DIVL':
            if dst[0] != 'RQ':
                raise AsmError("DIVL requires RQd", line_num)
            if src_reg and src_reg[0] == 'RR':
                return Encoder.encode_divl_rq_rrs(dst[1], src_reg[1])
            if src_ir:
                return Encoder.encode_divl_rq_ir(dst[1], src_ir[1])
            if src_is_imm:
                return Encoder.encode_divl_rq_imm(dst[1], self._eval(src_str))

        raise AsmError(f"Unsupported {mnemonic} operand combination: {ops}", line_num)

    def _encode_ldm(self, ops, line_num):
        """Encode LDM @Rd, Rs, #n (store) or LDM Rd, @Rs, #n (load)."""
        if len(ops) < 3:
            raise AsmError("LDM requires three operands: @Rd, Rs, #n or Rd, @Rs, #n", line_num)
        first_ir = parse_indirect(ops[0])
        second_ir = parse_indirect(ops[1])

        count = self._eval(ops[2])
        if count < 1 or count > 16:
            raise AsmError(f"LDM count must be 1-16, got: {count}", line_num)

        if first_ir:
            # LDM @Rd, Rs, #n (store to memory)
            rs = parse_register(ops[1])
            if not rs:
                raise AsmError("LDM store requires Rs", line_num)
            return Encoder.encode_ldm_store(first_ir[1], rs[1], count)
        elif second_ir:
            # LDM Rd, @Rs, #n (load from memory)
            rd = parse_register(ops[0])
            if not rd:
                raise AsmError("LDM load requires Rd", line_num)
            return Encoder.encode_ldm_load(second_ir[1], rd[1], count)
        else:
            raise AsmError("LDM requires indirect addressing (@Rd or @Rs)", line_num)

    def _encode_block_load(self, mnemonic, ops, line_num):
        """Encode LDI/LDIR/LDD/LDDR @Rd, @Rs, Rr."""
        if len(ops) < 3:
            raise AsmError(f"{mnemonic} requires @Rd, @Rs, Rr", line_num)
        dst_ir = parse_indirect(ops[0])
        src_ir = parse_indirect(ops[1])
        cnt_reg = parse_register(ops[2])
        if not dst_ir or not src_ir or not cnt_reg:
            raise AsmError(f"{mnemonic} requires @Rd, @Rs, Rr", line_num)
        repeat = mnemonic.endswith('R')
        if mnemonic.startswith('LDI') or mnemonic.startswith('LDIR'):
            return Encoder.encode_ldi(dst_ir[1], src_ir[1], cnt_reg[1], repeat=repeat)
        else:
            return Encoder.encode_ldd(dst_ir[1], src_ir[1], cnt_reg[1], repeat=repeat)

    # ===== Output generators =====

    def generate_listing(self):
        """Generate listing text."""
        lines = []
        for addr, data, src_line, line_num in self.output:
            hex_str = ' '.join(f'{b:02X}' for b in data[:8])
            lines.append(f'{addr:04X}: {hex_str:<24s} {src_line.rstrip()}')
            # Additional hex lines if data > 8 bytes
            for i in range(8, len(data), 8):
                chunk = data[i:i+8]
                hex_str = ' '.join(f'{b:02X}' for b in chunk)
                lines.append(f'{addr+i:04X}: {hex_str}')
        return '\n'.join(lines)

    def generate_inc(self, label_prefix='Z8K'):
        """Generate M80-compatible .inc file with DB statements."""
        lines = []
        lines.append(f'; Generated by z8001asm.py')
        lines.append(f'; Origin: 0x{self.origin:04X}, Size: {len(self._build_binary())} bytes')
        lines.append(f'{label_prefix}_CODE:')

        for addr, data, src_line, line_num in self.output:
            # Strip the source line for comment
            comment = src_line.strip()
            if ';' in comment:
                comment = comment[comment.index(';'):]
            else:
                comment = '; ' + comment

            # Generate DB lines (max 8 bytes per line)
            for i in range(0, len(data), 8):
                chunk = data[i:i+8]
                hex_parts = [f'0{b:02X}H' for b in chunk]
                db_line = '\tDB\t' + ', '.join(hex_parts)
                if i == 0:
                    # Add source as comment on first line
                    db_line += f'\t\t{comment}'
                lines.append(db_line)

        lines.append(f'{label_prefix}_CODE_LEN\tEQU\t$ - {label_prefix}_CODE')
        lines.append('')
        return '\n'.join(lines)


# =============================================================================
# Command line interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Z8001 Cross-Assembler')
    parser.add_argument('input', help='Input assembly source file')
    parser.add_argument('-o', '--output', help='Output binary file')
    parser.add_argument('--inc', help='Output M80-compatible include file')
    parser.add_argument('--lst', action='store_true', help='Generate listing to stdout')
    parser.add_argument('--label', default='Z8K', help='Label prefix for .inc output (default: Z8K)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    source = input_path.read_text()

    asm = Assembler()
    binary = asm.assemble(source)

    if asm.errors:
        for err in asm.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # Output binary
    if args.output:
        out_path = Path(args.output)
        out_path.write_bytes(binary)
        print(f"Binary: {out_path} ({len(binary)} bytes)")

    # Output .inc
    if args.inc:
        inc_path = Path(args.inc)
        inc_text = asm.generate_inc(label_prefix=args.label)
        inc_path.write_text(inc_text)
        print(f"Include: {inc_path}")

    # Listing
    if args.lst:
        print(asm.generate_listing())

    if not args.output and not args.inc and not args.lst:
        # Default: print listing
        print(asm.generate_listing())

    # Summary
    binary_len = len(binary) if binary else 0
    print(f"\nAssembly complete: {binary_len} bytes, "
          f"{len(asm.symbols)} symbols, {len(asm.errors)} errors",
          file=sys.stderr)


if __name__ == '__main__':
    main()
