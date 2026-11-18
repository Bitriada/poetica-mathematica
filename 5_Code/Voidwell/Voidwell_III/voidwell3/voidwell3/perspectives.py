"""perspectives.py -- the four perspectival algebras as four wells
(the Perspective Walk, D1 of the V3 investigation).

MONOGRAPH SOURCES (Ch. III sec. 3.4.2-3.4.3, via the Monkey Business
Pipeline stage table):

  UC1 -- the Complex Point.  The sphere seen from infinitely far:
         direction and rotation collapsed.  Law: i1^2 = i1
         (idempotent).
  UC2 -- the Complex Line.  One oscillation: direction emerges, but
         forward and backward cannot be distinguished -- sign is
         ambiguous.  Law: i2^2 = -i2 (anti-idempotent, the
         half-turn: two oscillations reverse orientation).
  UC3 -- the Complex Disc.  Two oscillations: direction around the
         circle is fully OBFUSCATED -- present as a symbol, carrying
         no well-defined value ([[i3]]).  Law: none of its own; its
         square is FIXED by the closure (below).  Realized here by
         the unit whose square is exactly -(1 + i1^2 + i2^2), i.e.
         the unit that exists only through the closure.
  UC4 -- the Loop Completion (the Field).  The fourth edge that
         closes the point-line-disc circuit into a rectangle.  Law:
         i4^2 = -1 (the proper complex unit), and the CLOSURE

             i1^2 + i2^2 + i3^2 + 1 = 0

         the holonomy of the full circuit being the nilpotent trace
         (tau^2 = 0, the fare ledger's law).

REALIZATION (4x4 over F_p, and 2x2 over F_257 for the toy).  All
units are PUBLIC constants; every law is an exact matrix identity
over any odd prime field (no quadratic-residue conditions -- the
blocks are chosen so the squares exist by construction):

  size 4:   U1 = diag(1,1,0,0)
            U2 = diag(0,0,-1,-1)
            U3 = [[0,-2],[1,0]] (+) [[0,-2],[1,0]]   (U3^2 = -2 I)
            U4 = [[0,-1],[1,0]] (+) [[0,-1],[1,0]]   (U4^2 = -I)
  size 2:   U1 = diag(1,0)
            U2 = diag(0,-1)
            U3 = [[0,-2],[1,0]]
            U4 = [[0,-1],[1,0]]

  closure check: U1^2 + U2^2 + U3^2 + I = 0 (both sizes):
      U1^2 = diag(1,1,0,0);  U2^2 = -U2 = diag(0,0,1,1);
      U3^2 = -2 I;           sum + I = 0.  Exact.

THE TWIST (how a perspective acts on a well).  Well j does not
conjugate the lifted state directly; it conjugates the state AS SEEN
FROM perspective j:

    T_j(X) = X + U_j @ X @ U_j          (public, linear, cheap)
    Q'_j   = M_j @ T_j(lift(D)) @ M_j^{-1}

The trace law (conjugation-invariant, gate-auditable):

    tr(Q'_j) = tr(T_j(Q)) = tr(Q) + tr(Q @ U_j^2)

Each perspective leaves a DIFFERENT signature because the four U_j^2
are the four different squares of the imaginary unit (U1, -U2,
-2I, -I) -- the four kinds of complex direction, made operational.
A wrong conversion fails the nullification audit with probability
1 - 2^-bits_per_digit and the trace law with probability 1 - 1/p.
"""
from __future__ import annotations

from ucq.lift import Profile
from ucq.matrix import FpMatrix

PERSPECTIVE_VERSION = 1

#: the named laws, for documentation and the gate's audit report
LAWS = {
    1: "i1^2 = i1            (UC1, the Complex Point: idempotent)",
    2: "i2^2 = -i2           (UC2, the Complex Line: anti-idempotent, "
       "the half-turn)",
    3: "i3^2 = -1 - i1^2 - i2^2  (UC3, the Complex Disc: obfuscated, "
       "present only through the closure)",
    4: "i4^2 = -1            (UC4, the Field: the proper complex unit)",
    0: "i1^2 + i2^2 + i3^2 + 1 = 0   (the loop closure; the circuit's "
       "holonomy is the nilpotent trace, tau^2 = 0)",
}


def _units(pro: Profile) -> dict[int, FpMatrix]:
    """The four public perspective units for a profile."""
    p, n = pro.p, pro.size
    if n == 4:
        u1 = FpMatrix.diagonal((1, 1, 0, 0), p)
        u2 = FpMatrix.diagonal((0, 0, -1, -1), p)
        u3 = FpMatrix([[0, -2, 0, 0], [1, 0, 0, 0],
                       [0, 0, 0, -2], [0, 0, 1, 0]], p)
        rot = [[0, -1], [1, 0]]
        u4 = FpMatrix([rot[0] + [0, 0], rot[1] + [0, 0],
                       [0, 0] + rot[0], [0, 0] + rot[1]], p)
    elif n == 2:
        u1 = FpMatrix.diagonal((1, 0), p)
        u2 = FpMatrix.diagonal((0, -1), p)
        u3 = FpMatrix([[0, -2], [1, 0]], p)
        u4 = FpMatrix([[0, -1], [1, 0]], p)
    else:
        raise ValueError(f"no perspective units for size {n}")
    return {1: u1, 2: u2, 3: u3, 4: u4}


def units(pro: Profile) -> dict[int, FpMatrix]:
    """The four perspective units, law-checked.  Raises if any of the
    four laws or the closure fails (they are constants; this is the
    import-time guarantee that the public table is sound)."""
    U = _units(pro)
    p = pro.p
    I = FpMatrix.identity(pro.size, p)
    zero = FpMatrix([[0] * pro.size for _ in range(pro.size)], p)
    # the four laws
    assert U[1] @ U[1] == U[1], "UC1 law failed: i1^2 != i1"
    assert U[2] @ U[2] == -U[2], "UC2 law failed: i2^2 != -i2"
    assert U[4] @ U[4] == -I, "UC4 law failed: i4^2 != -1"
    # the closure: i1^2 + i2^2 + i3^2 + 1 = 0, which also defines
    # U3's square (the obfuscated unit exists only through it)
    closure = U[1] @ U[1] + U[2] @ U[2] + U[3] @ U[3] + I
    assert closure == zero, "closure failed: i1^2+i2^2+i3^2+1 != 0"
    assert U[3] @ U[3] == -I - U[1] @ U[1] - U[2] @ U[2], \
        "UC3 law failed: i3^2 != -1 - i1^2 - i2^2"
    return U


def audit(pro: Profile) -> list[str]:
    """The perspective laws as human-readable audit lines (used by the
    gate and the CLI's params command)."""
    U = units(pro)
    out = [LAWS[1], LAWS[2], LAWS[3], LAWS[4], LAWS[0]]
    out.append(f"units verified for size {pro.size} over F_p, "
               f"p = {pro.p if pro.p.bit_length() < 32 else
                     str(pro.p.bit_length()) + '-bit prime'}")
    return out


def twist(pro: Profile, j: int):
    """T_j(X) = X + U_j X U_j as a closure over the profile's units."""
    U = units(pro)
    Uj = U[j]
    def T(X: FpMatrix) -> FpMatrix:
        return X + Uj @ X @ Uj
    return T


def twist_trace_law(Q: FpMatrix, Uj: FpMatrix) -> int:
    """The audited quantity: tr(T_j(Q)) = tr(Q) + tr(Q U_j^2).
    Returns the value the conjugated matrix's trace must equal."""
    p = Q.p
    Uj2 = Uj @ Uj
    # tr(Q Uj^2) = sum_i (Q Uj2)[i][i]; use the cyclic form directly
    tr_qu2 = sum(sum(Q.rows[i][k] * Uj2.rows[k][i]
                     for k in range(Q.n)) for i in range(Q.n)) % p
    return (Q.trace() + tr_qu2) % p


__all__ = ["PERSPECTIVE_VERSION", "LAWS", "units", "audit", "twist",
           "twist_trace_law"]
