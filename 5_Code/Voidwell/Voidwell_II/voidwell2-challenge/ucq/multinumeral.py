"""multinumeral.py -- the digivector as a multinumeral (App. A).

The monograph's Appendix A proposes the multinumeral: a value held in
n representational bases at once, where conversions between
incommensurable bases are native operations that generate nilpotent
traces.  This module reads the digivector through that lens and makes
the reading computational (used by the demonstration's measurements):

* NINE BASES.  Digivector digit Dn (bits bn2 bn1 bn0) is the n-th
  representational base: a 3-bit sub-state with its own prime labels
  (p_{3n}, p_{3n+1}, p_{3n+2} -- core.py's addressing) and its own
  tensor row (n//3 + 1, n%3 + 1) of the H-structure.

* TRACE DIMENSION (App. A.4.1): "the total number of trace components
  for n bases is n(n-1)/2" -- 36 for the 9-digit digivector.  The
  monograph derives this twice (combinatorial: pairwise conversions;
  algebraic: the off-diagonal of the n x n commensurability structure)
  and calls the convergence "probably the strongest formal result of
  the architecture".  `trace_dimension` computes it.

* COMMENSURABILITY (App. A.2.1): the 9x9 commensurability structure.
  The diagonal entries are the completions (each digit with its own
  switches); the off-diagonal is free -- and it is where the trace
  lives.  `commensurability` evaluates it for two digivectors: digit
  i of A against digit j of B are commensurable (merge without
  annihilation) iff their active switch sets are disjoint -- which
  for i != j is ALWAYS true (different bases own different switch
  positions), and for i == j fails exactly when the two states share
  an active switch in base i.  Annihilation is thus an INTRA-base
  event; the inter-base off-diagonal is always free -- the monograph's
  "constraint on the diagonal and freedom of the off-diagonal",
  verbatim in the algebra.

* THE WELL AS A CONVERSION (App. A.2.2): lift/project is the
  conversion between the fare-octal base and the UCQ matrix base; the
  nullifier is the trace the conversion generates.  The regime scale
  of App. A.2.2 reads the construction as: commutative regime (base
  layer) -> non-commutative regime (well conjugation).

* THE NIHILUM (App. A.3.1): the annihilated ZERO state is the cone's
  apex -- value = 0, trace = 0, all bases collapsed.  The base-layer
  transition never enters it (an annihilating union falls back to a
  slot write: the fare is paid, the state survives).
"""
from __future__ import annotations

from ucq.lift import Profile


def trace_dimension(n_bases: int) -> int:
    """App. A.4.1: n(n-1)/2 pairwise trace components."""
    return n_bases * (n_bases - 1) // 2


def digit_value(pro: Profile, state: int, n: int) -> int:
    pro.check_state(state)
    pro.check_digit(n)
    return (state >> (pro.bits_per_digit * n)) & pro.digit_max


def commensurability(pro: Profile, a: int, b: int) -> list[list[bool]]:
    """The n x n commensurability structure of two digivectors:
    cell (i, j) = digits i of a and j of b merge without annihilation
    (disjoint active switch sets).  Off-diagonal is always True;
    diagonal (i == j) fails iff a shared switch is active in both."""
    pro.check_state(a)
    pro.check_state(b)
    out = []
    for i in range(pro.n_digits):
        row = []
        for j in range(pro.n_digits):
            di = digit_value(pro, a, i)
            dj = digit_value(pro, b, j)
            if i != j:
                row.append(True)       # different bases, free merge
            else:
                row.append(di & dj == 0)
        out.append(row)
    return out


def annihilates(pro: Profile, a: int, b: int) -> bool:
    """Fare-octal product a * b annihilates iff some base has the same
    switch active in both (all-diagonal scan of the structure above)."""
    return any(not row[i]
               for i, row in enumerate(commensurability(pro, a, b)))


def diagonal_conflicts(pro: Profile, a: int, b: int) -> int:
    """How many bases (digits) block the merge a * b."""
    return sum(1 for i in range(pro.n_digits)
               if digit_value(pro, a, i) & digit_value(pro, b, i))


__all__ = ["trace_dimension", "digit_value", "commensurability",
           "annihilates", "diagonal_conflicts"]
