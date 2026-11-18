"""The Fare-Riemann sphere S^3_FR and its symmetry structure.

Objects from the monograph:

* Def. 4.2.4.1:  S^3_FR = { z in UC : ||z||_FR = 1 }, a 3-sphere in R^4.
* Prop. 4.2.4.3:  the value map induces a Hopf-type fibration
  val: S^3_FR -> D^2 (unit disc), fiber over v is the circle
  Fiber(v) = { v + tau s : |s|^2 = 1 - |v|^2 } = S^1.
* Def. 4.2.4.4:  the nadir plane N = { tau s : |s| = 1 }, the circle of
  pure-transit states (fibers over v = 0).
* Sec. 6.6.3:  the triadic rotation R(Z) = omega*val(Z) + tau*tr(Z)
  with omega = e^(2 pi i / 3), generating C_3 = {1, R, R^2} by
  isometries of S^3_FR.
* Sec. 4.4.3:  the C_8 action O_k rotating the trace plane by k*pi/4
  while keeping the value fixed.

Sampling S^3_FR uniformly: we draw 4 iid standard normals and
normalise, which is the standard uniform measure on S^3 (invariant
under O(4), hence under C_3 and C_8).  All Monte-Carlo measurements in
this project use this sampler.
"""

from __future__ import annotations

import numpy as np

from .uc import UC

__all__ = [
    "OMEGA",
    "sample_sphere",
    "triadic_rotation",
    "c3_orbit",
    "trace_rotation",
    "hopf_fiber",
    "nadir_plane",
    "pole_measure",
]

#: omega = e^{2 pi i / 3}, the primitive cube root of unity (sec. 6.6.3)
OMEGA = np.exp(2j * np.pi / 3)


# ----------------------------------------------------------------------
# uniform sampler
# ----------------------------------------------------------------------
def sample_sphere(n: int, rng: np.random.Generator) -> UC:
    """Draw n points uniformly (O(4)-invariant) on S^3_FR.

    Four iid N(0,1) coordinates, normalised, give the uniform measure on
    the unit 3-sphere in R^4 = UC.  The Fare-Riemann norm (Def. 4.2.4.1)
    is exactly the Euclidean norm of (a, b, c, d).
    """
    x = rng.standard_normal((n, 4))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return UC(x[:, 0] + 1j * x[:, 1], x[:, 2] + 1j * x[:, 3])


# ----------------------------------------------------------------------
# the C3 action (sec. 6.6.3)
# ----------------------------------------------------------------------
def triadic_rotation(z: UC, power: int = 1) -> UC:
    """R(Z) = omega^power * val(Z) + tau * tr(Z).

    Rotates the value plane by 120 deg per power, preserves the trace
    plane, preserves ||.||_FR because |omega| = 1.  R^3 = id, so the
    group is C_3 = {1, R, R^2}.
    """
    return UC(OMEGA ** power * z.val(), z.tr())


def c3_orbit(z: UC) -> UC:
    """The full C_3 orbit {Z, R(Z), R^2(Z)} (stacked along axis 0)."""
    return UC(
        np.stack([triadic_rotation(z, k).val() for k in range(3)]),
        np.stack([triadic_rotation(z, k).tr() for k in range(3)]),
    )


# ----------------------------------------------------------------------
# the C8 action (sec. 4.4.3)
# ----------------------------------------------------------------------
def trace_rotation(z: UC, k: int) -> UC:
    """O_k(Z) = val(Z) + tau * (e^{i k pi/4} * tr(Z)).

    Rotates the trace plane by k*pi/4 with the value fixed.  The eight
    operators form the commutative group C_8 of Prop. 4.4.3.1:
    O_k(S^3_FR) = S^3_FR and the action is free on the fibers.
    """
    return UC(z.val(), np.exp(1j * k * np.pi / 4) * z.tr())


# ----------------------------------------------------------------------
# Hopf fibration data (Prop. 4.2.4.3, sec. 6.6.8)
# ----------------------------------------------------------------------
def hopf_fiber(v: complex, m: int = 64) -> UC:
    """m points on the fiber over v in the unit disc:
    Fiber(v) = { v + tau s : |s| = sqrt(1 - |v|^2) } = circle S^1."""
    if abs(v) > 1 + 1e-12:
        raise ValueError(f"|v| = {abs(v):.3f} > 1: v is outside the unit disc")
    r = np.sqrt(max(0.0, 1.0 - abs(v) ** 2))
    ang = np.linspace(0.0, 2.0 * np.pi, m, endpoint=False)
    return UC(np.full(m, v), r * np.exp(1j * ang))


def nadir_plane(m: int = 128) -> UC:
    """The nadir plane N = { tau s : |s| = 1 } (Def. 4.2.4.4): m points on
    the circle of pure-transit states -- the fiber over v = 0."""
    ang = np.linspace(0.0, 2.0 * np.pi, m, endpoint=False)
    return UC(np.zeros(m), np.exp(1j * ang))


def pole_measure(n: int, atol: float = 1e-12) -> float:
    """Monte-Carlo measure of the 'pole' set {Z : val(Z) = 0}.

    The constructive algorithm of sec. 6.6.17 returns 'pole' when
    val(Z) = 0;  this set is the nadir plane, a single circle, hence a
    measure-zero subset of S^3_FR.  We estimate it by sampling: the hit
    count is ~ n * P(|val|^2 < atol^2), used only as a sanity check.
    """
    rng = np.random.default_rng(0)
    z = sample_sphere(n, rng)
    return float(np.mean(np.abs(z.val()) < atol))
