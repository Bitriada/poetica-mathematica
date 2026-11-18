"""conjugate.py -- the voidwell operation: non-commutative mixing.

The well operator (spec D3.3, resolution R1): a genuine matrix
conjugation in the UCQ matrix form of sec. 6.2.8b,

    Q' = M @ Q @ M^{-1},       M in GL(size, F_p),

which is order-sensitive across wells ((M2 M1) Q (M1^{-1} M2^{-1}) !=
(M1 M2) Q (M2^{-1} M1^{-1}) in general) and mixes all 16 UCQ degrees
of freedom.  The spec's "GL(16, F_p)" is realized as GL(size, F_p)
acting on the 16-dof UCQ element; the matrices are PRF-derived from
the 256-bit seed either way, so the realized entropy is seed-bounded
(documented in DEMONSTRATION.md, resolution R1).

`nullify` is the deterministic digit-zeroing on the digivector (the
tau^2 = 0 signature: the voidwell burns a slot); `trace_digit` reads a
digit back.  The ENCODER does not apply nullify after conjugation --
instead the PRF rejection-samples M until the conjugated-and-projected
digivector ALREADY has digit n zero (resolution R2), so the gate's
structural audit is a non-vacuous check (a wrong M fails it with
probability 1 - 1/2^bits_per_digit).
"""
from __future__ import annotations

from ucq.lift import Profile, lift, project
from ucq.matrix import FpMatrix


def conjugate(Q: FpMatrix, M: FpMatrix) -> FpMatrix:
    """Q' = M @ Q @ M^{-1} (raises SingularMatrix if M is not in GL)."""
    return M @ Q @ M.inverse()


def trace_digit(pro: Profile, Q: FpMatrix, digit: int) -> int:
    """The nullifiable digit of the UCQ element, read through the
    projection."""
    pro.check_digit(digit)
    return (project(pro, Q) >> (pro.bits_per_digit * digit)) \
        & pro.digit_max


def nullify(pro: Profile, state: int, digit: int) -> int:
    """Deterministic slot burn: set digit n of the digivector to 0."""
    pro.check_state(state)
    pro.check_digit(digit)
    shift = pro.bits_per_digit * digit
    return state & ~(((1 << pro.bits_per_digit) - 1) << shift)


def conjugation_nullifies(pro: Profile, state: int, M: FpMatrix,
                          digit: int) -> bool:
    """Does M's conjugation of `state` nullify `digit`?  (The PRF's
    rejection condition, resolution R2.)"""
    Q = lift(pro, state)
    return trace_digit(pro, conjugate(Q, M), digit) == 0


__all__ = ["conjugate", "trace_digit", "nullify",
           "conjugation_nullifies"]
