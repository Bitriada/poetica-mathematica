"""Tests: UC algebra (exact), Fare-Riemann sphere, triadic decomposition."""

from fractions import Fraction

import numpy as np
import pytest

from btc_without_ac import sphere, triadic
from btc_without_ac.uc import ExactUC, TAU, UC


# ----------------------------------------------------------------------
# UC algebra -- exact verification on random Gaussian rationals
# ----------------------------------------------------------------------
def _rand_exact(rng, n=1):
    return [ExactUC(*(Fraction(int(rng.integers(-9, 10)), 4) for _ in range(4)))
            for _ in range(n)]


def test_tau_squared_is_zero_exact():
    assert TAU * TAU == UC(0, 0)
    assert ExactUC(0, 0, 1, 0) * ExactUC(0, 0, 1, 0) == ExactUC()


def test_commutative_associative_unital_exact():
    rng = np.random.default_rng(0)
    for _ in range(150):
        x, y, w = _rand_exact(rng, 3)
        assert x * y == y * x
        assert (x * y) * w == x * (y * w)
        assert x * ExactUC(1) == x


def test_leibniz_rule_exact():
    """z1 z2 = v1 v2 + tau (v1 t2 + v2 t1), exactly (Claim 4.2.1.3)."""
    rng = np.random.default_rng(1)
    for _ in range(100):
        x, y = _rand_exact(rng, 2)
        prod = x * y
        # value = v1*v2
        v1v2 = ExactUC._cmul((x.a, x.b), (y.a, y.b))
        assert (prod.a, prod.b) == v1v2
        # trace = v1*t2 + v2*t1
        t = ExactUC._cadd(ExactUC._cmul((x.a, x.b), (y.c, y.d)),
                          ExactUC._cmul((y.a, y.b), (x.c, x.d)))
        assert (prod.c, prod.d) == t


def test_inverse_formula_exact():
    """(v + tau t)^-1 = 1/v - tau t/v^2 (Claim 4.2.1.2 formula is right)."""
    rng = np.random.default_rng(2)
    for _ in range(100):
        (x,) = _rand_exact(rng)
        if x.is_pure_trace():
            with pytest.raises(ZeroDivisionError):
                x.inverse()
            assert x * x == ExactUC()      # zero divisor
        else:
            assert x * x.inverse() == ExactUC(1)


def test_uc_float_matches_exact():
    rng = np.random.default_rng(3)
    for _ in range(50):
        (x,) = _rand_exact(rng)
        if x.is_pure_trace():
            continue
        zf = x.to_float_uc()
        assert zf.inverse().close_to(x.inverse().to_float_uc(), atol=1e-12)


def test_pure_trace_squares_to_zero():
    rng = np.random.default_rng(4)
    t = np.exp(1j * rng.uniform(0, 2 * np.pi, 1000))
    ghost = UC(np.zeros(1000), t)
    sq = ghost * ghost
    assert float(np.max(np.abs(sq.to_real4()))) == 0.0


# ----------------------------------------------------------------------
# Fare-Riemann sphere
# ----------------------------------------------------------------------
def test_samples_live_on_sphere():
    rng = np.random.default_rng(5)
    z = sphere.sample_sphere(50_000, rng)
    assert float(np.max(np.abs(z.norm_fr() - 1.0))) < 1e-12


def test_value_map_lands_in_unit_disc():
    rng = np.random.default_rng(6)
    z = sphere.sample_sphere(50_000, rng)
    assert np.all(np.abs(z.val()) <= 1.0)


def test_hopf_fiber_circle():
    for v in (0.0 + 0.0j, 0.3 + 0.4j, 0.9 + 0.1j):
        f = sphere.hopf_fiber(v, 512)
        assert np.allclose(np.abs(f.tr()), np.sqrt(1 - abs(v) ** 2), atol=1e-12)
        assert np.allclose(f.norm_fr(), 1.0, atol=1e-12)
        assert np.allclose(f.val(), v)


def test_hopf_fiber_rejects_outside_disc():
    with pytest.raises(ValueError):
        sphere.hopf_fiber(1.5 + 0.2j)


def test_nadir_plane():
    n = sphere.nadir_plane(256)
    assert np.all(n.val() == 0)
    assert np.allclose(np.abs(n.tr()), 1.0)


def test_c8_action_preserves_sphere_and_commutes():
    rng = np.random.default_rng(7)
    z = sphere.sample_sphere(1000, rng)
    for k in range(8):
        assert np.allclose(sphere.trace_rotation(z, k).norm_fr(), 1.0, atol=1e-12)
    for k1 in range(8):
        for k2 in range(8):
            a = sphere.trace_rotation(sphere.trace_rotation(z, k1), k2)
            b = sphere.trace_rotation(sphere.trace_rotation(z, k2), k1)
            assert np.allclose(a.to_real4(), b.to_real4(), atol=1e-12)
    # O_k fixes the value, rotates the trace by k*pi/4
    z8 = sphere.trace_rotation(z, 1)
    assert np.allclose(z8.val(), z.val())
    assert np.allclose(z8.tr(), np.exp(1j * np.pi / 4) * z.tr())


# ----------------------------------------------------------------------
# triadic decomposition (secs. 6.6.3, 6.6.17)
# ----------------------------------------------------------------------
def test_assign_domain_theorem_3_4():
    rng = np.random.default_rng(8)
    z = sphere.sample_sphere(200_000, rng)
    k, pole = triadic.assign_domain(z)
    assert not pole.any()                       # continuous samples
    assert np.isin(k, [0, 1, 2]).all()          # total, single-valued
    counts = np.bincount(k, minlength=3) / len(k)
    assert np.allclose(counts, 1 / 3, atol=0.005)  # volumes are 1/3


def test_assign_domain_boundary_and_pole_conventions():
    # pole: pure trace point (nadir circle)
    z = UC(0.0, 1.0 + 0.0j)
    k, pole = triadic.assign_domain(z)
    assert pole and k == -1
    # boundary ray conventions: theta = 0 -> D0; 2pi/3 -> D1; 4pi/3 -> D2
    for theta, expect in ((0.0, 0), (2 * np.pi / 3, 1), (4 * np.pi / 3, 2)):
        p = UC(np.exp(1j * theta), 0.3 + 0.1j)
        assert triadic.assign_domain(p)[0] == expect


def test_c3_group_and_isometry():
    rng = np.random.default_rng(9)
    z = sphere.sample_sphere(5000, rng)
    grp = triadic.verify_c3_group(z)
    assert grp["R3_identity_error"] < 1e-12
    assert grp["closure_error"] < 1e-12
    assert grp["omega3_minus_1"] < 1e-12
    assert triadic.verify_rotation_isometry(z) < 1e-12


def test_rotation_cycles_domains():
    rng = np.random.default_rng(10)
    z = sphere.sample_sphere(200_000, rng)
    assert triadic.verify_rotation_cycles_domains(z) < 1e-4  # boundary only


def test_domain_volume_matches_one_third():
    p, se = triadic.domain_volume(300_000)
    assert np.allclose(p, 1 / 3, atol=0.005)
    assert se < 0.002
