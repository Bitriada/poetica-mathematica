"""lift.py -- digivector <-> UCQ matrix: the heterobase conversion.

Unchanged from Voidwell-2 (LIFT_VERSION 1; the bit-packing table and
the proven round trip carry over), with the V3 profiles:

  FULL  9 octal digits (27 bits) <-> 4x4 over F_p (256-bit prime)
  TOY   8 one-bit digits (a byte) <-> 2x2 over F_257

The toy upgrade from F_7 is the V3 investigation's P3 fix: GL(2, 257)
has room for real conjugation orbits, so the miniature demonstrates
the binding behavior it is supposed to demonstrate.  The toy's eight
one-bit digits also let the prime skeleton keep its full constants
(the digits 2, 3, 5, 7 all fit), so the small model runs the SAME
schedule as the flagship.
"""
from __future__ import annotations

from dataclasses import dataclass

from ucq.field import P, P_TOY
from ucq.matrix import FpMatrix

LIFT_VERSION = 1


@dataclass(frozen=True)
class Profile:
    p: int
    n_digits: int
    bits_per_digit: int
    size: int

    @property
    def n_bits(self) -> int:
        return self.n_digits * self.bits_per_digit

    @property
    def n_cells(self) -> int:
        return self.size * self.size

    @property
    def digit_max(self) -> int:
        return (1 << self.bits_per_digit) - 1

    def check_state(self, state: int) -> int:
        if not 0 <= state < (1 << self.n_bits):
            raise ValueError(
                f"state {state} outside 0..2^{self.n_bits}-1")
        return state

    def check_digit(self, n: int) -> int:
        if not 0 <= n < self.n_digits:
            raise ValueError(f"digit {n} outside 0..{self.n_digits - 1}")
        return n


#: the full model: 9 octal digits, 4x4 UCQ over the 256-bit prime
FULL = Profile(p=P, n_digits=9, bits_per_digit=3, size=4)
#: the small model: a byte (8 one-bit digits), 2x2 over F_257
TOY = Profile(p=P_TOY, n_digits=8, bits_per_digit=1, size=2)


def lift(pro: Profile, state: int) -> FpMatrix:
    """Digivector -> UCQ matrix (the V2 bit-packing table)."""
    pro.check_state(state)
    cells = [0] * pro.n_cells
    for j in range(pro.n_bits):
        if (state >> j) & 1:
            cells[j % pro.n_cells] |= 1 << (j // pro.n_cells)
    rows = [cells[r * pro.size:(r + 1) * pro.size]
            for r in range(pro.size)]
    return FpMatrix(rows, pro.p)


def project(pro: Profile, Q: FpMatrix) -> int:
    """UCQ matrix -> digivector (read the packed low bits)."""
    if Q.p != pro.p or Q.n != pro.size:
        raise ValueError("matrix does not match the profile")
    state = 0
    for j in range(pro.n_bits):
        c = Q.rows[(j % pro.n_cells) // pro.size][(j % pro.n_cells)
                                                  % pro.size]
        if (int(c) >> (j // pro.n_cells)) & 1:
            state |= 1 << j
    return state


def roundtrip_ok(pro: Profile, state: int) -> bool:
    return project(pro, lift(pro, state)) == state


__all__ = ["LIFT_VERSION", "Profile", "FULL", "TOY",
           "lift", "project", "roundtrip_ok"]
