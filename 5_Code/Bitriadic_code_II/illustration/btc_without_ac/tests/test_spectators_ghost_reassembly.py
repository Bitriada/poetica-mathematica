"""Tests: spectators, ghost disc, reassembly."""

import numpy as np
import pytest

from btc_without_ac import ghost, reassembly, sphere, spectators, triadic
from btc_without_ac.uc import UC


# ----------------------------------------------------------------------
# spectators (secs. 6.6.1, 6.6.15)
# ----------------------------------------------------------------------
N_SPECT = 60_000


def _labeled(rng):
    z = sphere.sample_sphere(N_SPECT, rng)
    labels, _ = triadic.assign_domain(z)
    return z, labels


def test_apparent_counts_match_monograph_table():
    """N_Unfathoming = 1; N_Forward = N_Backward = N_Deep = 3."""
    rng = np.random.default_rng(20)
    z, labels = _labeled(rng)
    counts = {k: spectators.apparent_count(spectators.SPECTATORS[k], z, labels)
              for k in spectators.CASE_STUDY_SPECTATORS}
    assert counts == {"unfathoming": 1, "forward": 3,
                      "backward": 3, "deep": 3}


def test_unfathoming_overlaps_are_large():
    """The Unfathoming spectator's domain images overlap heavily: D0 and D2
    even have identical pi_R-support (−1/2, 1] -- set-theoretically
    indistinguishable, not just statistically."""
    rng = np.random.default_rng(21)
    z, labels = _labeled(rng)
    ov = spectators.pairwise_overlap(spectators.SPECTATORS["unfathoming"], z, labels)
    off = ov[~np.eye(3, dtype=bool)]
    assert off.min() > 0.15          # every pair merges


def test_forward_overlaps_are_small():
    rng = np.random.default_rng(22)
    z, labels = _labeled(rng)
    ov = spectators.pairwise_overlap(spectators.SPECTATORS["forward"], z, labels)
    off = ov[~np.eye(3, dtype=bool)]
    assert off.max() < 0.15          # every pair separable


def test_pi_projections():
    z = UC(0.6 + 0.2j, -0.3 + 0.5j)
    assert np.ravel(spectators.pi_real(z))[0] == pytest.approx(0.6)
    assert np.ravel(spectators.pi_complex(z)).tolist() == pytest.approx([0.6, 0.2])
    assert np.ravel(spectators.pi_tau(z)).tolist() == pytest.approx([-0.3, 0.5])
    assert np.ravel(spectators.pi_complex_chiral(z)).tolist() == pytest.approx([0.6, -0.2])


def test_spectator_shift_1_to_3_reversible():
    rng = np.random.default_rng(23)
    z, labels = _labeled(rng)
    assert spectators.spectator_shift("unfathoming", "forward", z, labels) == (1, 3)
    assert spectators.spectator_shift("forward", "unfathoming", z, labels) == (3, 1)
    assert spectators.spectator_shift("unfathoming", "deep", z, labels) == (1, 3)


def test_functionals_run_and_flagged_interpretive():
    rng = np.random.default_rng(24)
    z = sphere.sample_sphere(10_000, rng)
    assert spectators.spec_unfathoming(z) == pytest.approx(1.0, abs=1e-3)
    for f in (spectators.spec_forward, spectators.spec_backward,
              spectators.spec_meta):
        val = f(z)
        assert np.isfinite(val)


# ----------------------------------------------------------------------
# ghost disc (sec. 6.6.15)
# ----------------------------------------------------------------------
def test_ghost_nilpotence_exact():
    rng = np.random.default_rng(25)
    x = ghost.ghost_disc_samples(20_000, rng)
    assert ghost.verify_nilpotence(x) == 0.0


def test_ghost_invisibility_exact():
    rng = np.random.default_rng(26)
    x = ghost.ghost_disc_samples(20_000, rng)
    inv = ghost.verify_invisibility(x)
    assert inv["max_abs_pi_real"] == 0.0
    assert inv["max_abs_pi_complex"] == 0.0


def test_ghost_area_is_pi():
    area, se = ghost.ghost_area_montecarlo(1_000_000, np.random.default_rng(27))
    assert area == pytest.approx(np.pi, abs=5 * se)


def test_intrinsic_volume_accounting():
    acc = ghost.volume_accounting(10_000, np.random.default_rng(28))
    assert acc["V_int(S^3_FR)"] == 4
    assert acc["V_int(pi_R S^3_FR)"] == 1
    assert acc["V_int(pi_C S^3_FR)"] == 2
    assert acc["V_int(pi_tau S^3_FR)"] == 2
    assert acc["sum_of_projections"] == 5          # 1 + 2 + 2 > 4
    assert acc["sum_exceeds_by"] == 1              # the double-counted a-axis
    assert acc["visible_plus_ghost_minus_overlap"] == 4   # 3 + 2 - 1
    assert acc["accounting_consistent"]


# ----------------------------------------------------------------------
# reassembly (secs. 6.6.8, 6.6.15)
# ----------------------------------------------------------------------
def test_phi_roundtrip_exact_on_each_domain():
    rng = np.random.default_rng(30)
    z = sphere.sample_sphere(150_000, rng)
    for k in range(3):
        assert reassembly.verify_phi_roundtrip(z, k) < 1e-12


def test_phi_image_is_full_sphere():
    rng = np.random.default_rng(31)
    for k in range(3):
        res = reassembly.verify_phi_image_is_full_sphere(k, 30_000, rng)
        assert res["preimages_in_domain_fraction"] == 1.0
        assert res["max_roundtrip_error"] < 1e-9
        assert res["surjective_on_samples"]


def test_reassembly_composition_readings():
    rng = np.random.default_rng(32)
    z = sphere.sample_sphere(50_000, rng)
    comp = reassembly.verify_reassembly_composition(z)
    assert comp["literal_order_identity_error"] < 1e-9     # literal = identity
    assert comp["glossed_equals_triadic_rotation"]         # glossed = R^{t-k}


def test_angle_stretch_measure_scaling():
    res = reassembly.verify_angle_stretch_measure(300_000,
                                                  np.random.default_rng(33))
    assert res["piece_volume_D0"] == pytest.approx(1 / 3, abs=0.005)
    assert res["measure_scaling_factor"] == pytest.approx(3.0, abs=0.05)
    assert res["image_angle_uniform"]


def test_pay_trace_one_way():
    res = reassembly.verify_pay_trace_one_way()
    assert res["idempotent_error"] < 1e-15
    assert res["ghost_layer_collapses_to_zero"]


def test_virtual_spheres_are_full_and_labeled():
    rng = np.random.default_rng(34)
    z = sphere.sample_sphere(120_000, rng)
    vs = reassembly.virtual_spheres(z)
    assert len(vs) == 3
    for label, img in vs:
        assert len(img.val()) > 0
        # each labeled copy is the full sphere as a set:
        # angles cover [0, 2pi) and norms are 1
        assert np.allclose(img.norm_fr(), 1.0, atol=1e-12)
        ang = np.mod(np.angle(img.val()), 2 * np.pi)
        assert ang.min() < 0.05 and ang.max() > 2 * np.pi - 0.05


def test_phi_fiber_roundtrip():
    rng = np.random.default_rng(35)
    z = sphere.sample_sphere(100_000, rng)
    t = z.tr()
    ang = np.mod(np.angle(t), 2 * np.pi)
    k = np.where(t == 0, -1, np.clip(np.floor(3 * ang / (2 * np.pi)).astype(int), 0, 2))
    for j in range(3):
        m = k == j
        img = reassembly.phi_fiber(z[m], j)
        back = reassembly.phi_fiber_inv(img, j)
        assert float(np.max(np.abs(back.to_real4() - z[m].to_real4()))) < 1e-12
