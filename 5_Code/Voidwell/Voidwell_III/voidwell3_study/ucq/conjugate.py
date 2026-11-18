"""conjugate.py -- the voidwell operation, with cached inverses.

Same operation as Voidwell-2: Q' = M @ Q @ M^{-1} in the UCQ matrix
form.  The V3 change (D6): `conjugate` accepts a precomputed Minv so
the well loop can test a candidate and, on acceptance, reuse the
inverse it already computed (the V2 profile recomputed the inverse
inside every conjugation, including the accepted one).
"""
from __future__ import annotations

from ucq.lift import Profile, lift, project
from ucq.matrix import FpMatrix


def conjugate(Q: FpMatrix, M: FpMatrix,
              Minv: FpMatrix | None = None) -> FpMatrix:
    """Q' = M @ Q @ M^{-1} (raises SingularMatrix if M is not in GL)."""
    if Minv is None:
        Minv = M.adjugate_inverse()
    return M @ Q @ Minv


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
                          digit: int,
                          twist=None) -> bool:
    """Does M's conjugation of `state` (optionally through a
    perspective twist) nullify `digit`?  (The PRF's rejection
    condition.)"""
    Q = lift(pro, state)
    if twist is not None:
        Q = twist(Q)
    Minv = M.adjugate_inverse()
    return trace_digit(pro, conjugate(Q, M, Minv), digit) == 0


__all__ = ["conjugate", "trace_digit", "nullify",
           "conjugation_nullifies"]
