"""The constructive triadic decomposition of S^3_FR (secs. 6.6.3, 6.6.17).

Theorem 3.4 (Constructive Partition) of the monograph:

    S^3_FR = D0 |_| D1 |_| D2,
    D_k = { Z in S^3_FR : k*2pi/3 <= arg(val(Z)) < (k+1)*2pi/3 },

every point is assigned by an explicit O(1) test on the angle of its
value -- no selection from uncountable families, hence no Axiom of
Choice.  Section 6.6.17 spells the algorithm out:

    STEP 1  v <- val(Z);  if v = 0 return "pole"  (measure zero)
    STEP 2  theta <- arg(v) in [0, 2pi)
    STEP 3  theta < 2pi/3 -> D0;  theta < 4pi/3 -> D1;  else D2

This module implements that algorithm literally (`assign_domain`) and
verifies, by Monte-Carlo on the uniform sphere measure:

* the three domains are disjoint and exhaustive (partition),
* each carries volume 1/3 (the C_3 action is by isometries, sec. 6.6.3),
* the triadic rotation cycles the domains: R(D_k) = D_{k+1 mod 3},
* the pole set (nadir plane) has measure zero.
"""

from __future__ import annotations

import numpy as np

from .sphere import OMEGA, sample_sphere, triadic_rotation
from .uc import UC

__all__ = [
    "assign_domain",
    "domain_index",
    "domain_volume",
    "partition_report",
    "verify_rotation_isometry",
    "verify_rotation_cycles_domains",
    "verify_c3_group",
    "DOMAIN_COLORS",
    "DOMAIN_NAMES",
]

DOMAIN_NAMES = ("D0", "D1", "D2")
DOMAIN_COLORS = ("#4C72B0", "#DD8452", "#55A868")


# ----------------------------------------------------------------------
# the constructive algorithm of sec. 6.6.17
# ----------------------------------------------------------------------
def assign_domain(z: UC):
    """The O(1), choice-free domain assignment of sec. 6.6.17.

    Returns
    -------
    k : int ndarray
        Domain label in {0, 1, 2}, or -1 for the pole set (val(Z) = 0).
    pole : bool ndarray
        Mask of the pole points (the nadir plane, measure zero).
    """
    v = z.val()
    pole = v == 0
    # STEP 2: theta in [0, 2pi).  np.angle returns (-pi, pi]; map to [0, 2pi).
    theta = np.mod(np.angle(v), 2.0 * np.pi)
    # STEP 3: wedge test.  3*theta/(2pi) in [0, 3) -> floor in {0, 1, 2}.
    k = np.floor(3.0 * theta / (2.0 * np.pi)).astype(np.int64)
    k = np.clip(k, 0, 2)          # guard against theta == 2pi rounding
    k = np.where(pole, -1, k)
    return k, pole


def domain_index(z: UC) -> int:
    """Domain of a single point (for scalar inputs)."""
    k, _ = assign_domain(z)
    return int(np.asarray(k))


# ----------------------------------------------------------------------
# Monte-Carlo volume measurement
# ----------------------------------------------------------------------
def domain_volume(n: int = 600_000, rng: np.random.Generator | None = None):
    """Relative volumes of D0, D1, D2 under the uniform measure on S^3_FR.

    Returns (fractions, stderr) where fractions should be (1/3, 1/3, 1/3)
    and stderr is the binomial standard error 1/sqrt(4.5 n).
    """
    rng = rng or np.random.default_rng(42)
    z = sample_sphere(n, rng)
    k, _ = assign_domain(z)
    counts = np.array([(k == j).sum() for j in range(3)], dtype=float)
    p = counts / counts.sum()
    se = float(np.sqrt((1.0 / 3.0) * (2.0 / 3.0) / n))
    return p, se


def partition_report(n: int = 600_000, rng: np.random.Generator | None = None) -> dict:
    """Full verification bundle for the constructive partition."""
    rng = rng or np.random.default_rng(7)
    z = sample_sphere(n, rng)
    k, pole = assign_domain(z)

    # partition property: every sampled point lies in exactly one domain
    # (assign_domain is a function, so 'exactly one' holds by construction;
    # we verify totality: no point is left out, none is a pole here).
    exhaustive = bool(np.isin(k, [0, 1, 2]).all())
    disjoint_by_construction = True  # a function assigns exactly one label
    pole_fraction = float(pole.mean())

    # volumes
    counts = np.array([(k == j).sum() for j in range(3)], dtype=float)
    volumes = counts / counts.sum()
    vol_err = float(np.max(np.abs(volumes - 1.0 / 3.0)))

    return {
        "n": n,
        "exhaustive": exhaustive,
        "disjoint_by_construction": disjoint_by_construction,
        "pole_fraction": pole_fraction,
        "volumes": volumes,
        "max_volume_deviation": vol_err,
        "labels": k,
        "sphere": z,
    }


# ----------------------------------------------------------------------
# C3 action checks
# ----------------------------------------------------------------------
def verify_rotation_isometry(z: UC) -> float:
    """Max deviation of ||R^k(Z)||_FR from ||Z||_FR over k = 0,1,2.

    The triadic rotation multiplies val by a unit complex number and
    leaves tr untouched, so the Fare-Riemann norm is preserved exactly
    up to floating point (|omega| = 1).
    """
    n0 = z.norm_fr()
    err = 0.0
    for k in range(3):
        err = max(err, float(np.max(np.abs(triadic_rotation(z, k).norm_fr() - n0))))
    return err


def verify_rotation_cycles_domains(z: UC) -> float:
    """R(D_k) = D_{k+1 mod 3}:  max violation over sampled non-pole points.

    A point with value angle theta lands, after one triadic rotation, at
    theta + 2pi/3 (mod 2pi), i.e. in the next wedge.  Returns the
    fraction of points violating the cycle (should be 0 up to the
    measure-zero boundary rays).
    """
    k, _ = assign_domain(z)
    ok = np.ones(k.shape, dtype=bool)
    for m in range(3):
        k2, _ = assign_domain(triadic_rotation(z, m))
        ok &= k2 == np.mod(k + m, 3)
    return float(1.0 - np.mean(ok))


def verify_c3_group(z: UC) -> dict:
    """Group checks: R^3 = id, closure R^a R^b = R^{a+b mod 3}, omega^3 = 1."""
    id_err = float(np.max(np.abs(
        triadic_rotation(z, 3).to_real4() - z.to_real4())))
    closure_err = 0.0
    for a in range(3):
        for b in range(3):
            lhs = triadic_rotation(triadic_rotation(z, a), b)
            rhs = triadic_rotation(z, (a + b) % 3)
            closure_err = max(closure_err, float(np.max(np.abs(
                lhs.to_real4() - rhs.to_real4()))))
    omega_err = float(abs(OMEGA ** 3 - 1.0))
    return {
        "R3_identity_error": id_err,
        "closure_error": closure_err,
        "omega3_minus_1": omega_err,
    }
