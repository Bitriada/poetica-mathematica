"""Fare-Octal core: the 27-bit state space of Appendix A, made operational.

THE OBJECT (monograph Appendix A, "Fare-Octal Counting System").

A Fare-Octal state is 27 on/off switches ("tau-generators"), displayed
as 9 octal digits

    [D8 D7 D6 D5 D4 D3 D2 D1 D0],   Dn = [b2 b1 b0] of bits 3n, 3n+1, 3n+2,

so the display counts like ordinary base 8 (standard carry), while the
2^27 = 134,217,728 states are tau-configurations, not integers.

THREE READINGS OF ONE STATE (all exact, all in this module).

(1) COUNT  (linear count / display integer): the 27-bit pattern read
    as an integer 0..2^27-1.  Counting = octal increment (App. A sec. 3).
(2) VALUE  (Fare / squarefree reading): each bit position n is labelled
    by the (n+1)-th prime p_n; the state's value is the squarefree
    integer  N = prod_{active bits} p_n.  This is the reading of the
    monograph's own gloss ("two numbers merge their active switches
    only if the underlying prime labels share no common factor, and
    produce zero if any switch is duplicated") and of the Fare Algebra
    (Ch. IV sec. 4.1.1): states = basis elements tau_N.
(3) H-WEIGHT (spectral embedding): each bit is an H-tensor cell
    (i, j, k) of the 117-point Arithmetic Bitriada, carrying weight
    2^(3*k*i*j); the state's H-weight is 2^(3 * sum k*i*j) over active
    cells (App. A sec. 9 item 4, "spectral embedding via the H-tensor
    weights").

ADDRESSING (App. A sec. 6).  Bit position L in 0..26 maps to the
tensor cell (i, j, k) with i, j, k in {1,2,3} by the monograph's
formula  L = 9(k-1) + 3(i-1) + (j-1),  and to the prime p_L (the
(L+1)-th prime: 2, 3, 5, ..., 103).  The three addressing schemes are
bijections, verified in verify.py (V2).

MULTIPLICATION.  The Fare product (App. A sec. 4) under the VALUE
reading:

    tau_m * tau_n = tau_{m*n}   if gcd(m, n) = 1      (merge switches)
    tau_m * tau_n = 0           otherwise             (collapse on overlap)

equivalently: union of the prime-switch sets if disjoint, ZERO if they
overlap.  With the algebra's ZERO adjoined (annihilation target) and
the all-off state as multiplicative UNIT (tau_1 in the Fare Algebra;
the empty product), the state space becomes a commutative monoid,
closed and associative -- verified in verify.py (V3), where the
LITERAL index-gcd rule of App. A sec. 4.1 (gcd on the 0..26 indices
themselves) is shown to be non-closed and non-associative, and is kept
only as `index_rule_product` for divergence witnesses.

NAMING TENSION (documented, not hidden): the monograph calls the
all-off state the "zero state" (display [0 0 0 0 0 0 0 0 0]), but in
the Fare Algebra that state is tau_empty-set = 1, the multiplicative
unit; the algebra's 0 arises only from annihilation and is NOT one of
the 2^27 states.  This module names them UNIT and ZERO respectively.
"""

from __future__ import annotations

from math import gcd, prod

__all__ = ["PRIMES", "N_BITS", "N_DIGITS", "FareOctal", "ZERO", "UNIT",
           "tau", "count_table", "index_rule_product", "sieve_primes"]

# The first 27 primes (positions 0..26); p_26 = 103 (App. A sec. 6.3).
PRIMES: tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37,
                           41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
                           89, 97, 101, 103)
N_BITS = 27
N_DIGITS = 9


def sieve_primes(n: int) -> list[int]:
    """First n primes by sieve (self-check for PRIMES)."""
    out, cand = [], 2
    while len(out) < n:
        if all(cand % p for p in out):
            out.append(cand)
        cand += 1
    return out


# -- addressing -----------------------------------------------------------
def linear_to_tensor(L: int) -> tuple[int, int, int]:
    """L = 9(k-1) + 3(i-1) + (j-1)  ->  (i, j, k), all in {1,2,3}."""
    if not 0 <= L < N_BITS:
        raise ValueError(f"bit position {L} outside 0..26")
    k, rest = divmod(L, 9)
    i, j0 = divmod(rest, 3)
    return (i + 1, j0 + 1, k + 1)


def tensor_to_linear(i: int, j: int, k: int) -> int:
    if not all(x in (1, 2, 3) for x in (i, j, k)):
        raise ValueError("tensor coordinates must be in {1,2,3}")
    return 9 * (k - 1) + 3 * (i - 1) + (j - 1)


def prime_at(position: int) -> int:
    return PRIMES[position]


def position_of_prime(p: int) -> int:
    if p not in PRIMES:
        raise ValueError(f"{p} is not one of the first {N_BITS} primes")
    return PRIMES.index(p)


# -- the state class ------------------------------------------------------
class FareOctal:
    """A Fare-Octal state: 27 switches, or the algebra's ZERO.

    `_bits` is a frozenset of active bit positions 0..26, or None for
    ZERO (the annihilation target, not one of the 2^27 states).
    """

    __slots__ = ("_bits",)
    _bits: frozenset[int] | None

    def __init__(self, bits=None):
        if bits is None:
            object.__setattr__(self, "_bits", None)  # ZERO
            return
        b = frozenset(bits)
        if any(not 0 <= x < N_BITS for x in b):
            raise ValueError("bit positions must be in 0..26")
        object.__setattr__(self, "_bits", b)

    # -- constructors -----------------------------------------------------
    @staticmethod
    def from_int(n: int) -> "FareOctal":
        """The state whose linear count is n (0 <= n < 2^27)."""
        if not 0 <= n < 2 ** N_BITS:
            raise ValueError("count outside 0..2^27-1")
        return FareOctal({b for b in range(N_BITS) if n >> b & 1})

    @staticmethod
    def from_value(N: int) -> "FareOctal":
        """The state whose squarefree VALUE is N.

        N = 0 -> ZERO; N = 1 -> UNIT (empty product); N must be a
        squarefree integer with all prime factors among the first 27
        primes (the Fare Algebra window)."""
        if N == 0:
            return ZERO
        if N < 0:
            raise ValueError("value must be a nonnegative integer")
        if N == 1:
            return UNIT
        bits, m = set(), N
        for pos, p in enumerate(PRIMES):
            if m % p == 0:
                bits.add(pos)
                m //= p
                if m % p == 0:
                    raise ValueError(f"{N} is not squarefree")
        if m != 1:
            raise ValueError(f"{N} has prime factors outside the "
                             f"27-prime window (remainder {m})")
        return FareOctal(bits)

    # -- readings ---------------------------------------------------------
    def to_int(self) -> int:
        """(1) linear count: the 27-bit pattern as an integer."""
        if self._bits is None:
            raise TypeError("ZERO has no count (not a state)")
        return sum(1 << b for b in self._bits)

    def value(self) -> int:
        """(2) squarefree value: prod of primes at active bits."""
        if self._bits is None:
            return 0
        return prod(PRIMES[b] for b in self._bits) if self._bits else 1

    def h_exponent(self) -> int:
        """(3) H-weight exponent: 3 * sum k*i*j over active cells."""
        if self._bits is None:
            return 0
        return 3 * sum(prod(linear_to_tensor(b)) for b in self._bits)

    def h_weight(self) -> int:
        """(3) H-weight: 2^(h_exponent) (exact big integer)."""
        return 1 << self.h_exponent()

    # -- display ----------------------------------------------------------
    def digits(self) -> tuple[int, ...]:
        """(D8, D7, ..., D0) -- most significant digit first."""
        if self._bits is None:
            return (None,) * N_DIGITS
        n = self.to_int()
        return tuple((n >> (3 * d)) & 7 for d in reversed(range(N_DIGITS)))

    def display(self) -> str:
        """The monograph's bracket display '[D8 ... D0]'."""
        if self._bits is None:
            return "0 (annihilated)"
        return "[" + " ".join(str(d) for d in self.digits()) + "]"

    def active_linear(self) -> tuple[int, ...]:
        """Active switches as LINEAR labels tau_n (App. A sec. 6.1) --
        the convention of the counting table (sec. 5)."""
        if self._bits is None:
            return ()
        return tuple(sorted(self._bits))

    def active_prime_labels(self) -> tuple[int, ...]:
        """Active switches as PRIME labels tau_p (App. A sec. 6.3) --
        the convention of the multiplication examples (sec. 7)."""
        if self._bits is None:
            return ()
        return tuple(PRIMES[b] for b in sorted(self._bits))

    def is_zero(self) -> bool:
        return self._bits is None

    def is_unit(self) -> bool:
        """The all-off state: display zero, Fare-algebraic unit tau_1."""
        return self._bits == frozenset()

    # -- the Fare product (value reading) ----------------------------------
    def __mul__(self, other: "FareOctal") -> "FareOctal":
        if not isinstance(other, FareOctal):
            return NotImplemented
        if self._bits is None or other._bits is None:
            return ZERO
        if self._bits & other._bits:
            return ZERO  # overlap -> annihilation (collapse on overlap)
        return FareOctal(self._bits | other._bits)

    def annihilates_with(self, other: "FareOctal") -> bool:
        """True iff the product is ZERO (gcd of values > 1)."""
        if self._bits is None or other._bits is None:
            return True
        return bool(self._bits & other._bits)

    # -- plumbing ----------------------------------------------------------
    def __eq__(self, other):
        return isinstance(other, FareOctal) and self._bits == other._bits

    def __hash__(self):
        return hash((FareOctal, self._bits))

    def __repr__(self):
        if self._bits is None:
            return "ZERO"
        return f"FareOctal({self.display()}, count={self.to_int()}, " \
               f"value={self.value()})"


ZERO = FareOctal.__new__(FareOctal)
ZERO.__init__(None)
UNIT = FareOctal(frozenset())  # display [0 0 0 0 0 0 0 0 0]; value 1


def tau(position: int) -> FareOctal:
    """The single-generator state tau_{position} (linear label)."""
    return FareOctal({position})


# -- counting (App. A sec. 3 and sec. 5) -----------------------------------
def count_table(n: int):
    """Yield states 0..n-1 in linear count order, with their monograph
    tau-interpretations (linear labels)."""
    for c in range(n):
        s = FareOctal.from_int(c)
        yield c, s, s.active_linear()


# -- the literal index rule (App. A sec. 4.1 AS WRITTEN) -------------------
def index_rule_product(a: int, b: int):
    """Appendix A Rules 1-3 applied LITERALLY to the 0..26 indices:

        tau_a * tau_b = 0            if a == b          (nilpotency)
        tau_a * tau_b = tau_{a*b}    if gcd(a, b) == 1
        tau_a * tau_b = 0            if gcd(a, b) > 1

    Returns the resulting linear index, or None for annihilation.
    Kept for the divergence analysis (verify.py V3): this rule is NOT
    closed (products leave 0..26) and NOT associative."""
    if a == b:
        return None
    return a * b if gcd(a, b) == 1 else None
