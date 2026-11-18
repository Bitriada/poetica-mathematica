"""lift.py -- digivector <-> UCQ matrix: the heterobase conversion.

MONOGRAPH SOURCES.

* Ch. VI sec. 6.2.8b: the UCQ element's matrix form -- a 4x4 matrix
  indexed by quaternionic direction (rows: 1, i, j, k) x UC component
  (columns: value real, value imag, trace real, trace imag).
* Appendix A (The Multinumeral): the digivector is a NINE-base object
  (one base per octal digit); the lift is a CONVERSION between two
  incommensurable representational bases -- the fare-octal base (27
  switches) and the UCQ matrix base (16 cells over F_p) -- and the
  nullifier at each well is the nilpotent record the conversion
  generates.  App. A.2.2's regime reading: the fare-octal layer is
  the commutative regime; the UCQ conjugation is the non-commutative
  regime; the well is the transit between them.

BIT PACKING (LIFT_VERSION 1), general over a Profile:

  state bits:  n_digits * bits_per_digit bits, numbered 0..B-1
               (bit j = ((state >> j) & 1); bit 3n+m is digit n's
               switch m -- the fare-octal addressing of core.py)
  matrix:      size x size cells, row-major cell index c
               cell c = sum over j with (j mod C == c) of
                        bit_j << (j // C)          (C = size*size)

  Full model: 27 bits -> 16 cells: bits 0..15 land in cells 0..15
  (shift 0), bits 16..26 land in cells 0..10 (shift 1).  Cell values
  are in {0,1,2,3} (cells 0..10) and {0,1} (cells 11..15), well below
  p, so `project` reads the low bits back exactly:

      bit j = (cell[j mod C] >> (j // C)) & 1

  Small model (spec D8): 3 bits -> 2x2 over F_7: bits 0..2 in cells
  0..2, cell 3 carries the constant 0 (the Nihilum anchor).

`project` is defined for ARBITRARY matrices (after conjugation the
cells are uniform in F_p): it reads the packed low bits, a
deterministic many-to-one map.  The round-trip project(lift(D)) == D
holds on lift's image (verified over the full 2^27 for the small
model and 10^5 samples + structure for the full model, V9).
"""
from __future__ import annotations

from dataclasses import dataclass

from ucq.field import P
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


#: the full demonstration model: 9 octal digits, 4x4 UCQ over F_p
FULL = Profile(p=P, n_digits=9, bits_per_digit=3, size=4)
#: the small model (spec D8): 3 one-bit digits, 2x2 over F_7
SMALL = Profile(p=7, n_digits=3, bits_per_digit=1, size=2)


def lift(pro: Profile, state: int) -> FpMatrix:
    """Digivector -> UCQ matrix (the packing table above)."""
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


__all__ = ["LIFT_VERSION", "Profile", "FULL", "SMALL",
           "lift", "project", "roundtrip_ok"]
