"""The 117-point Arithmetic Bitriada as a storage/addressing convention.

MONOGRAPH SOURCES.

* Ch. I sec. I.8 ("The Complete 117-Point Lattice") and the level
  table: L has 9 points, M has 27, H has 81 -- "Sum | 39 | 39 | 39 |
  117" per axis (prime / reflection / projection).
* Ch. I: the L grid (z x i), the three M matrices (M, M', M''), and
  the H tensor slices H_k(i, j) = 2^(3*k*i*j), exponents 3..81.
* Ch. V (line ~4090): "Projected H-level counting is a tad bit more
  complex than that so it was moved to Appendix A.  Fare-octal
  counting system" -- Fare-Octal IS the H-level counting system.
* Ch. IX / 6.3a.1: the 27-chamber Tribit (Atlas-lattice hypercube,
  "a cross-sectional model, a scaffolding for computation") and the
  81-point Fortress 3^4 (Epoch 6: the Tribit duplicated along an
  observation axis).

THE RELATION (as the user framed it: a combinatorial convention for
storage/addresses, NOT a 1:1 matchup).  The 117-point lattice supplies
the addressing geometry of the 27-bit Fare-Octal window:

* the 27 BITS are the 27 cells (i, j, k) of the H tensor (3 slices x
  3x3), via the monograph's own formula L = 9(k-1) + 3(i-1) + (j-1)
  (App. A sec. 6.2 -- identical to the H-cell indexing);
* the 9 OCTAL DIGITS are the 9 rows (k, i) of the H tensor: digit n
  = 3(k-1) + (i-1) packages the three j-cells of slice k, row i --
  and 9 is the cardinality of the L level;
* the M level (27) is the Tribit itself: 27 chambers, the cardinality
  bridge between the 9 digits and the 81-point Fortress;
* the H level (81) exceeds the window: the Fortress is the Epoch-6
  extension (3^4), outside the closed 27-bit Tribit -- Fare-Octal
  stores configurations of 27 H-cells, i.e. the M-level chamber
  occupancy, and leaves the Fortress out.

All tables are EXACT big integers; the monograph's rounded entries
("6,87E+10", "1,8E+16") are matched by their exact values here.
"""

from __future__ import annotations

from .core import N_BITS, PRIMES, linear_to_tensor, tensor_to_linear

__all__ = ["L_TABLE", "M_TABLES", "H_EXPONENTS", "lattice_sums",
           "digit_address", "bit_address", "fortress_note",
           "L_FORMULA", "M_FORMULA", "H_FORMULA"]

# -- Ch. I, the L grid (z = 1..3 rows, i = 1..3 columns) --------------------
# printed: 2 4 8 / 4 8 16 / 6 12 24.  Observed exact fit: L(z,i) = 2^i*rad(z)
# (rad = product of distinct prime factors); kept as a verified fit, the
# monograph prints values only.
L_TABLE: tuple[tuple[int, ...], ...] = (
    (2, 4, 8),
    (4, 8, 16),
    (6, 12, 24),
)
L_FORMULA = "L(z, i) = 2^i * rad(z)  (verified fit to the printed table)"


def _rad(n: int) -> int:
    out, m = 1, n
    p = 2
    while m > 1:
        if m % p == 0:
            out *= p
            while m % p == 0:
                m //= p
        p += 1
    return out


# -- Ch. I, the three M matrices: M_k(i, j) = 4^(k*i*j), k = 1, 2, 3 --------
# printed as M (4..262144), M' (16..68719476736), M'' (64..2^54).
M_FORMULA = "M_k(i, j) = 4^(k*i*j)  (k = 1: M, 2: M', 3: M'')"


def m_value(k: int, i: int, j: int) -> int:
    return 4 ** (k * i * j)


M_TABLES: dict[int, tuple[tuple[int, ...], ...]] = {
    k: tuple(tuple(m_value(k, i, j) for j in (1, 2, 3))
             for i in (1, 2, 3)) for k in (1, 2, 3)
}

# -- Ch. I, the H tensor slices: H_k(i, j) = 2^(3*k*i*j) --------------------
# exponents 3*k*i*j range 3..81; the monograph also displays iterated
# H', H'' exponential towers elsewhere in Ch. I -- outside this module.
H_FORMULA = "H_k(i, j) = 2^(3*k*i*j)  (three slices, exponents 3..81)"


def h_exponent(k: int, i: int, j: int) -> int:
    return 3 * k * i * j


H_EXPONENTS: dict[int, tuple[tuple[int, ...], ...]] = {
    k: tuple(tuple(h_exponent(k, i, j) for j in (1, 2, 3))
             for i in (1, 2, 3)) for k in (1, 2, 3)
}


# -- level sums -------------------------------------------------------------
def lattice_sums() -> dict:
    """The Ch. I level table: 9 + 27 + 81 = 117 total points; each of
    the three axes (prime / reflection / projection) carries 3 + 9 + 27
    = 39 points ("Sum | 39 | 39 | 39 | 117")."""
    levels = {"L": 9, "M": 27, "H": 81}
    per_axis = {"L": 3, "M": 9, "H": 27}
    total = sum(levels.values())
    axis = sum(per_axis.values())
    return {
        "levels": levels,
        "per_axis": per_axis,
        "total_points": total,
        "per_axis_sum": axis,
        "table_matches_monograph": (total == 117 and axis == 39
                                    and levels == {"L": 9, "M": 27, "H": 81}),
    }


# -- the storage/addressing convention --------------------------------------
def digit_address(n: int) -> tuple[int, int]:
    """Digit Dn <-> H-tensor row (k, i): n = 3(k-1) + (i-1).

    The 9 digits are the 9 rows of the H tensor (3 slices x 3 rows) --
    cardinality 9 = the L level.  Digit Dn packages the three j-cells
    (bits 3n, 3n+1, 3n+2) of slice k, row i."""
    if not 0 <= n < 9:
        raise ValueError("digit index must be in 0..8")
    k, i = divmod(n, 3)
    return (k + 1, i + 1)


def bit_address(L: int) -> dict:
    """Bit position L <-> full address: H-cell (i,j,k), digit Dn and
    position within the digit, and prime label p_L (the Fare value
    axis).  The 27 bits are the 27 H cells -- cardinality 27 = the M
    level (the Tribit)."""
    i, j, k = linear_to_tensor(L)
    n, r = divmod(L, 3)
    kk, ii = digit_address(n)
    assert (kk, ii) == (k, i)  # digit row = (k, i) of the H cell
    return {"bit": L, "cell": (i, j, k), "digit": n, "digit_bit": r,
            "prime": PRIMES[L]}


# -- the Fortress (outside the window) ---------------------------------------
FORTRESS_NOTE = {
    "points": 81,
    "structure": "3^4 hypercube, coordinates in {1,2,3}^4, centre (2,2,2,2)",
    "relation": ("the 27-chamber Tribit (the Fare-Octal window, M level) "
                 "duplicated along a fourth OBSERVATION axis (Epoch 6); "
                 "the Fortress is NOT addressable in the 27-bit window"),
    "zeta_array": "16 = 2^4 cells; 81/16 = (3/2)^4 ~ 5.06 nodes per strand",
}
