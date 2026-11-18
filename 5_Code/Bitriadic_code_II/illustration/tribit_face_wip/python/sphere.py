"""sphere.py -- the Fare-Riemann sphere S3_FR (Def. 4.2.4.1).

S3_FR = { z in UC : |val(z)|^2 + |tr(z)|^2 = 1 }  -- the round 3-sphere
in R^4, forced by the spectral involution at the critical value s = 1/2
(Remark 4.2.4.1a: value and trace on equal footing, symmetry group
containing the O_k).

Structures implemented here:

  * the value-fibers: at fixed value v the trace circle
    { v + tau*t : |t|^2 = 1 - |v|^2 }   (Sec. 4.2.4, explicit fibration)
    -- the circles the O_k rotations navigate (Sec. 4.5.2a);
  * the classical Hopf map  h(z) = tr(z)/val(z)  with h = infinity on
    the nadir (pure trace) and h = 0 on the pure value circle --
    matching the monograph's "fiber at infinity = pure trace";
  * the nadir circle N = { tau*s : |s| = 1 }  (Def. 4.2.4.4), the
    pure-transit states;
  * the balance torus |val| = |tr| = 1/sqrt(2) (the AGS spectral
    critical line s = 1/2 locus on the sphere; algebraically the
    Clifford torus);
  * the intrinsic metric ||z||_tau = |val| + |tr|  (Def. 4.2.4.6),
    whose supremum on the sphere is sqrt(2), attained exactly on the
    balance torus;
  * the square-free lattice: prime angles phi_p, square-free n placed
    at the sum of its prime angles on the nadir circle, so that
    coprime multiplication becomes angle addition (Sec. 4.1.5);
  * stereographic projection S3 -> R3 from the pure value pole,
    which turns the above circles into the familiar nested-torus
    picture.

Honest note: the monograph's Sec. 4.2.4 calls the value map a Hopf
fibration and gives fiber formulas that fix the value (the trace
circles above).  Fixing the value does not give the classical Hopf
fibration -- its fibers are the h-fibers {(u, q*u)}.  We implement
both, display both, and flag the tension in the README.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from tribit import UC

TAU = 2.0 * math.pi


# --------------------------------------------------------------------------
# elementary parametrised subsets of S3_FR
# --------------------------------------------------------------------------

def nadir_point(phi: float) -> UC:
    """Point of the nadir circle N = {tau*s : |s| = 1} (Def. 4.2.4.4)."""
    return UC(0.0, 0.0, math.cos(phi), math.sin(phi))


def pure_value_point(theta: float) -> UC:
    """Point of the pure value circle {|val| = 1, tr = 0}."""
    return UC(math.cos(theta), math.sin(theta), 0.0, 0.0)


def balance_point(psi: float, phi: float) -> UC:
    """Point of the balance torus |val| = |tr| = 1/sqrt(2).

    psi runs along the value circle, phi along the trace circle; the
    surface is the Clifford torus, the locus of the AGS balance
    condition |val(z)| = |tr(z)| at the spectral critical line s=1/2.
    """
    r = 1.0 / math.sqrt(2.0)
    return UC(r * math.cos(psi), r * math.sin(psi),
              r * math.cos(phi), r * math.sin(phi))


def value_fiber_point(v: complex, phi: float) -> UC:
    """Point of the value-fiber over v (|v| < 1), trace angle phi.

    { v + tau*t : |t|^2 = 1 - |v|^2 }  -- the O_k navigation circle.
    """
    v = complex(v)
    rv = abs(v)
    if rv >= 1.0:
        raise ValueError("value-fiber needs |v| < 1")
    rt = math.sqrt(1.0 - rv * rv)
    return UC(v.real, v.imag, rt * math.cos(phi), rt * math.sin(phi))


def value_fiber_radius(v: complex) -> float:
    """Radius of the value-fiber circle over v: sqrt(1 - |v|^2)."""
    return math.sqrt(max(0.0, 1.0 - abs(complex(v)) ** 2))


# --------------------------------------------------------------------------
# the two fibrations
# --------------------------------------------------------------------------

def hopf_map(z: UC):
    """Classical Hopf map h(z) = tr(z)/val(z).

    Returns a complex q, or None for infinity (val = 0: pure trace,
    the nadir -- the monograph's "fiber at infinity = pure trace").
    h(z) = 0 exactly on the pure value circle (tr = 0).
    """
    v, t = z.val, z.tr
    if abs(v) < 1e-15:
        return None  # infinity
    return t / v


def hopf_fiber_point(q: complex, theta: float) -> UC:
    """Point of the classical Hopf fiber over finite q.

    The fiber is {(u, q*u) : |u| = 1} normalised to the sphere:
    (u, q*u)/sqrt(1 + |q|^2), u = e^{i theta}.
    """
    u = complex(math.cos(theta), math.sin(theta))
    w = q * u
    s = math.sqrt(1.0 + abs(q) ** 2)
    return UC(u.real / s, u.imag / s, w.real / s, w.imag / s)


def hopf_fiber_infinity_point(phi: float) -> UC:
    """The fiber at infinity IS the nadir circle."""
    return nadir_point(phi)


# --------------------------------------------------------------------------
# intrinsic metric
# --------------------------------------------------------------------------

def intrinsic_norm(z: UC) -> float:
    """||z||_tau = |val| + |tr|   (Def. 4.2.4.6)."""
    return abs(z.val) + abs(z.tr)


def intrinsic_sup_on_sphere() -> float:
    """Supremum of ||z||_tau over S3_FR: sqrt(2), by Cauchy-Schwarz.

    Equality holds exactly where |val| = |tr| -- the balance torus.
    (The monograph's Prop. 4.2.4.7: "the Fare-Riemann sphere has
    intrinsic radius sqrt(2)".)
    """
    return math.sqrt(2.0)


# --------------------------------------------------------------------------
# square-free lattice on the nadir circle
# --------------------------------------------------------------------------

#: label range: angles live in [0, TAU) for square-free n <= LABEL_LIMIT
LABEL_LIMIT = 210
_L = math.log(LABEL_LIMIT + 1)


def label_angle(n: int) -> float:
    """The logarithmic height of square-free n as a circle angle.

    Phi(n) = 2*pi * ln(n) / ln(LABEL_LIMIT + 1).

    The monograph assigns "an angle phi_p to each prime and lets the
    angle of a square-free n be the sum of its prime angles"
    (Sec. 4.1.5) without pinning the assignment.  We take the natural
    one: the logarithm, which turns the Fare Algebra's coprime
    multiplication into exact angle addition, Phi(mn) = Phi(m) +
    Phi(n), with no wrap-around for mn <= LABEL_LIMIT.  It is
    injective on the range (ln is strictly increasing), and it is the
    coordinate in which the spectral involution n^(1-2s) acts by
    phases -- on the critical line s = 1/2 + i*t the label at angle
    theta rotates by -(t*L/pi)*theta, the identity at t = 0.
    """
    if n < 1 or n > LABEL_LIMIT:
        raise ValueError(f"n must be in [1, {LABEL_LIMIT}]")
    return TAU * math.log(n) / _L


def first_primes(count: int) -> List[int]:
    out: List[int] = []
    cand = 2
    while len(out) < count:
        if all(cand % p for p in out):
            out.append(cand)
        cand += 1
    return out


def prime_angle(p: int, primes: Optional[List[int]] = None) -> float:
    """Angle of the prime p: its logarithmic height (see label_angle)."""
    return label_angle(p)


def squarefree_label_angle(n: int, primes: Optional[List[int]] = None) -> float:
    """Angle of square-free n: the sum of its prime angles (Sec. 4.1.5).

    With the logarithmic assignment this equals label_angle(n)
    exactly, with no modular wrap for n <= LABEL_LIMIT.
    """
    if n < 1:
        raise ValueError("n must be a positive square-free integer")
    ang = 0.0
    for p in factorize(n):
        ang += prime_angle(p)
    return ang % TAU


def factorize(n: int) -> List[int]:
    """Distinct prime factors of square-free n."""
    out: List[int] = []
    m = n
    p = 2
    while m > 1 and p * p <= m:
        if m % p == 0:
            out.append(p)
            while m % p == 0:
                m //= p
        p += 1
    if m > 1:
        out.append(m)
    return out


def is_squarefree(n: int) -> bool:
    return all(e == 1 for e in _factor_exp(n).values())


def _factor_exp(n: int) -> dict:
    out: dict = {}
    m, p = n, 2
    while m > 1 and p * p <= m:
        while m % p == 0:
            out[p] = out.get(p, 0) + 1
            m //= p
        p += 1
    if m > 1:
        out[m] = out.get(m, 0) + 1
    return out


def squarefree_lattice_points(max_n: int = 210,
                              primes: Optional[List[int]] = None
                              ) -> List[Tuple[int, UC]]:
    """Square-free labels placed on the nadir circle by angle sums.

    Returns [(n, point)] for square-free n <= max_n whose prime
    factors are among the first 16 primes.  Multiplication of coprime
    labels is angle addition: the Fare Algebra rule tau_m * tau_n =
    tau_{mn} read as geometry.
    """
    primes = primes or first_primes(50)
    out = []
    for n in range(1, max_n + 1):
        if is_squarefree(n):
            out.append((n, nadir_point(squarefree_label_angle(n, primes))))
    return out


# --------------------------------------------------------------------------
# stereographic projection to R^3 (for display)
# --------------------------------------------------------------------------

POLE = (1.0, 0.0, 0.0, 0.0)  # the pure value pole


def stereographic(z: UC) -> Tuple[float, float, float]:
    """Project S3_FR \\ {pole} -> R^3 from the pure value pole.

    X = (b, c, d) / (1 - a).  The pure value circle through the pole
    becomes a line; the nadir circle stays the unit circle of the
    (c, d)-plane; Hopf fibers become the nested-torus circles.
    """
    a, b, c, d = z.a, z.b, z.c, z.d
    den = 1.0 - a
    if den < 1e-12:
        den = 1e-12  # near-pole clamp; display only, never used in proofs
    return (b / den, c / den, d / den)


def inv_stereographic(X: Tuple[float, float, float]) -> UC:
    """Inverse of stereographic(); round-trip partner for tests."""
    x, y, zc = X
    r2 = x * x + y * y + zc * zc
    a = (r2 - 1.0) / (r2 + 1.0)
    s = 2.0 / (r2 + 1.0)
    return UC(a, s * x, s * y, s * zc)
