"""ucq -- the UC-Quaternion layer of the Voidwell-3 construction.

MONOGRAPH SOURCES.

* Ch. VI sec. 6.2.8 ("The UC-Quaternion Algebra"): UCQ = H (x)_R UC,
  16-dimensional; matrix form sec. 6.2.8b: a 4x4 matrix indexed by
  quaternionic direction (rows 1, i, j, k) x UC component.
* Ch. III sec. 3.4.2-3.4.3 (the perspectival algebras UC1-UC4): the
  point, line, disc and field views of the complex numbers, closed by
  UC4 with i4^2 = -1 and nilpotent holonomy -- the four perspectives
  Voidwell-3 realizes as its four wells (voidwell3/perspectives.py).
* Ch. VIII sec. 8.5 ("UC-polynomials"): the fare ledger, tau^2 = 0
  keeps the trace linear (ucpoly.py, ported unchanged from V2).

MODULES.

  field.py        the prime fields (256-bit p for the full model,
                  F_257 for the toy -- the investigation's P3 fix)
  matrix.py       FpMatrix: @, inverse, adjugate_inverse, serialize
  lift.py         digivector <-> UCQ matrix + the V3 profiles
  conjugate.py    Q' = M Q M^-1 with cached inverses
  ucpoly.py       UC-polynomials and the fare ledger (sec. 8.5)
"""
from ucq.field import P, P_HEX, PRIME_BITS, P_TOY
from ucq.matrix import FpMatrix, SingularMatrix
from ucq.lift import (LIFT_VERSION, Profile, FULL, TOY,
                      lift, project, roundtrip_ok)
from ucq import conjugate, ucpoly

__all__ = ["P", "P_HEX", "PRIME_BITS", "P_TOY", "FpMatrix",
           "SingularMatrix", "LIFT_VERSION", "Profile", "FULL", "TOY",
           "lift", "project", "roundtrip_ok", "conjugate", "ucpoly"]
