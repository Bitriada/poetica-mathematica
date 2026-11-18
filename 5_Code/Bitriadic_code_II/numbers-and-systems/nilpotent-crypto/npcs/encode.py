"""Encoding Fare-Octal states into UCQ: the NPCS injective map.

DRAFT SOURCE (NPCS sec. 1.3, 1.4), with corrections marked.

The 27 bits of a Fare-Octal chunk are partitioned into four blocks of
6/7/7/7 bits; each block feeds one quaternion coefficient:

    block a = bits 0..5    (primes 2, 3, 5, 7, 11, 13)    -> scalar
    block b = bits 6..12   (primes 17..43)                -> I
    block c = bits 13..19  (primes 47..79)                -> J
    block d = bits 20..26  (primes 83..103)               -> K

VALUE sheet (real quaternion): v_x = product of the block's primes at
active bits (the Fare-Octal VALUE reading restricted to the block).
Unique factorization makes each block's bit pattern recoverable from
v_x, so encode is injective -- verified exhaustively per block (T2).

TRACE sheet (complex quaternion, Gaussian-integer coefficients):
tr_x = (hamming weight of block x) + i * (sum of set-bit positions) --
the draft's design choice, kept verbatim (global bit positions).

The block structure COUPLES the two sheets to the same quaternion
axes: a chunk's V and D have nonzero components on exactly the same
units.  Structural consequence (proven in trials T6): two chunks whose
V-parts commute (same bits in blocks b, c, d) differ only in the
SCALAR block (a), so their difference is a central UC element and the
FULL product is swap-invariant -- the value sheet already binds order
generically, because generic quaternion products do not commute.

MINI SYSTEM (trials T7): a reduced 8-bit replica with four blocks of
2 bits and mini-primes ((2,3), (5,7), (11,13), (17,19)) -- the same
coupling structure, small enough for exhaustive pair censuses.

CHUNKING (draft sec. 1.4): messages split into 27-bit chunks,
zero-padded, original bit-length recorded alongside (length-prefix
commitment metadata).
"""

from __future__ import annotations

from fareoctal import PRIMES

from .ucq import UCQ

__all__ = ["CHUNK_BITS", "BLOCKS", "encode", "decode_blocks", "chunk_bits",
           "unchunk_bits", "MINI_BITS", "MINI_PRIMES", "mini_encode",
           "block_value", "block_trace"]

CHUNK_BITS = 27
# (start, width, prime-tuple) per block, per the draft's 6/7/7/7 split
BLOCKS = (
    (0, 6, PRIMES[0:6]),
    (6, 7, PRIMES[6:13]),
    (13, 7, PRIMES[13:20]),
    (20, 7, PRIMES[20:27]),
)


def _block_parts(chunk: int, block):
    start, width, primes = block
    weight = possum = 0
    value = 1
    for j in range(width):
        if chunk >> (start + j) & 1:
            weight += 1
            possum += start + j        # global bit position
            value *= primes[j]
    return value, weight, possum


def block_value(chunk: int, x: int) -> int:
    """The squarefree VALUE of block x of a 27-bit chunk."""
    return _block_parts(chunk, BLOCKS[x])[0]


def block_trace(chunk: int, x: int):
    """The block's trace contribution as a Gaussian integer
    (weight + i * position-sum) -- draft sec. 1.3."""
    _, w, p = _block_parts(chunk, BLOCKS[x])
    return (w, p)


def encode(chunk: int) -> UCQ:
    """encode: {0,1}^27 -> UCQ, the draft's sec. 1.3 map.

    V = v_a + v_b*I + v_c*J + v_d*K   (real quaternion, squarefree ints)
    D = tr_a + tr_b*I + tr_c*J + tr_d*K (Gaussian integer coefficients)
    """
    v = []
    d = []
    for x in range(4):
        value, weight, possum = _block_parts(chunk, BLOCKS[x])
        v.append(value)
        d.extend((weight, possum))
    return UCQ.from_real(v, d)


def decode_blocks(chunk: int):
    """The four (v_x, tr_x) block readings, for display."""
    out = []
    for x in range(4):
        value, weight, possum = _block_parts(chunk, BLOCKS[x])
        out.append({"block": "abcd"[x], "value": value,
                    "trace": (weight, possum)})
    return out


# -- chunking (draft sec. 1.4) -----------------------------------------------
def chunk_bits(bitstring: str):
    """'01101...' -> (list of 27-bit ints, original bit length).
    The last chunk is zero-padded; the true length is carried alongside
    (the draft's length-recorded padding)."""
    n = len(bitstring)
    if any(c not in "01" for c in bitstring):
        raise ValueError("bitstring must be 0/1 only")
    padded = bitstring + "0" * (-n % CHUNK_BITS)
    chunks = [int(padded[i:i + CHUNK_BITS], 2)
              for i in range(0, len(padded), CHUNK_BITS)] or [0]
    return chunks, n


def unchunk_bits(chunks, n_bits: int) -> str:
    """Inverse: rebuild the original bitstring."""
    bits = "".join(f"{c:027b}" for c in chunks)
    if len(bits) < n_bits:
        raise ValueError("inconsistent chunk list / length")
    return bits[:n_bits]


# -- the mini system (reduced 8-bit replica, for exhaustive censuses) --------
MINI_BITS = 8
MINI_PRIMES = ((2, 3), (5, 7), (11, 13), (17, 19))


def mini_encode(chunk: int) -> UCQ:
    """8-bit analogue of encode: four blocks of 2 bits, mini-primes."""
    if not 0 <= chunk < 1 << MINI_BITS:
        raise ValueError("mini chunk must be in 0..255")
    v, d = [], []
    for x in range(4):
        start = 2 * x
        weight = possum = 0
        value = 1
        for j in range(2):
            if chunk >> (start + j) & 1:
                weight += 1
                possum += start + j
                value *= MINI_PRIMES[x][j]
        v.append(value)
        d.extend((weight, possum))
    return UCQ.from_real(v, d)
