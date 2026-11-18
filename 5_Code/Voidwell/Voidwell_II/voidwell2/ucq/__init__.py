"""ucq -- the UC-Quaternion layer of the voidwell construction.

MONOGRAPH SOURCES.

* Ch. VI sec. 6.2.8 ("The UC-Quaternion Algebra"): UCQ = H (x)_R UC,
  16-dimensional; each quaternion coefficient lives in the commutative
  ring UC = R[i, tau]/(i^2+1, tau^2); matrix form sec. 6.2.8b: a 4x4
  matrix indexed by quaternionic direction (rows 1, i, j, k) x UC
  component (columns: value real, value imag, trace real, trace imag).
* Appendix A ("The Multinumeral"): the digivector's nine digits are
  nine representational bases; conversions between them generate
  nilpotent traces (multinumeral.py); the off-diagonal trace dimension
  is n(n-1)/2 = 36 for n = 9.
* Ch. VIII sec. 8.5 ("UC-polynomials"): the composition reading of the
  path -- coefficients in UC, the convolution rule, fare(F) = sum of
  trace weights, tau^2 = 0 keeps the trace linear (ucpoly.py).

MODULES.

  field.py        the prime field F_p (256-bit prime, hard-coded)
  matrix.py       FpMatrix: n x n over F_p, @, inverse, trace, serialize
  lift.py         digivector <-> UCQ matrix (LIFT_VERSION 1) + profiles
  conjugate.py    Q' = M Q M^-1, trace_digit, nullify
  multinumeral.py the 9-base commensurability structure (App. A)
  ucpoly.py       UC-polynomials and the fare ledger (sec. 8.5)
"""
from ucq.field import P, P_HEX, PRIME_BITS
from ucq.matrix import FpMatrix, SingularMatrix
from ucq.lift import (LIFT_VERSION, Profile, FULL, SMALL,
                      lift, project, roundtrip_ok)
from ucq import conjugate, multinumeral, ucpoly

__all__ = ["P", "P_HEX", "PRIME_BITS", "FpMatrix", "SingularMatrix",
           "LIFT_VERSION", "Profile", "FULL", "SMALL",
           "lift", "project", "roundtrip_ok",
           "conjugate", "multinumeral", "ucpoly"]
