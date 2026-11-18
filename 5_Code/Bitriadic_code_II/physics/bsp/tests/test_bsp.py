"""Test suite for the bsp package.

Run:  python -m pytest tests/ -q
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bsp.cases_io import PRESETS, case_to_params, load_case, load_user_data
from bsp.checks import run_checks
from bsp.enthalpy import run_enthalpy
from bsp.lattice import Lattice1DB, lattice_report
from bsp.neumann import (NeumannOnePhase, solve_lambda_melt,
                         solve_lambda_one_phase,
                         solve_lambda_two_phase)
from bsp.nodes import NodeRole, NodeStates
from bsp.solver import BSPParams, run_bsp
from bsp.uc import UC, prop32_product, phi_ext_1db

MONO = dict(mode="freezing", T_m=0.0, T_s=-10.0, T_0=0.0,
            length=0.05, dx=0.001, t_end=2000.0,
            rho=1000.0, L=334000.0, k_grown=2.2, cp_grown=4186.0,
            k_bulk=0.6, cp_bulk=4186.0)


def _mono_params(**kw):
    d = {**MONO, **kw}
    return BSPParams(**d)


# ======================================================================
# UC algebra (paper sec. 3)
# ======================================================================
def test_tau_squared_exactly_zero():
    tau = UC.from_arrays(0.0, 0.0, 1.0, 0.0)
    sq = tau * tau
    assert (sq.a, sq.b, sq.c, sq.d) == (0.0, 0.0, 0.0, 0.0)


def test_uc_product_matches_leibniz_expansion():
    rng = np.random.default_rng(0)
    z = UC.from_arrays(*rng.standard_normal(4))
    w = UC.from_arrays(*rng.standard_normal(4))
    prod = z * w
    # Leibniz: val z * val w + tau (val z * tr w + val w * tr z)
    vz, tw = z.value(), w.trace()
    vw, tz = w.value(), z.trace()
    expect_c = (vz * tw + vw * tz).real
    expect_d = (vz * tw + vw * tz).imag
    assert prod.a == pytest.approx((z.value() * w.value()).real)
    assert prod.b == pytest.approx((z.value() * w.value()).imag)
    assert prod.c == pytest.approx(expect_c)
    assert prod.d == pytest.approx(expect_d)


def test_prop32_formula_deviates_from_the_algebra():
    """Audit finding A0: Prop 3.2's printed product is not the product
    of the algebra it defines (missing -bd'-b'd, sign flip on b'c)."""
    rng = np.random.default_rng(1)
    z = UC.from_arrays(*rng.standard_normal(4))
    w = UC.from_arrays(*rng.standard_normal(4))
    correct = z * w
    printed = prop32_product(z, w)
    assert not np.allclose(printed.c, correct.c)
    assert not np.allclose(printed.d, correct.d)
    # value parts agree
    assert np.allclose(printed.a, correct.a)
    assert np.allclose(printed.b, correct.b)


def test_phi_ext_1db_projection():
    z = UC.from_arrays([3.0], [4.0], [0.0], [0.0])
    X, Y = phi_ext_1db(z)[0]
    assert X == 3.0 and Y == 4.0


# ======================================================================
# Lattices (paper sec. 4)
# ======================================================================
def test_lattice_counts():
    rep = lattice_report()
    assert rep["1DB_points_match"]
    assert rep["L_table_matches_paper"]
    assert rep["M_table_matches_paper"]
    assert rep["2DB_consistent"]
    assert Lattice1DB.total() == 117
    assert Lattice1DB.level_sizes() == {"L": 9, "M": 27, "H": 81}


# ======================================================================
# Neumann analytical solutions
# ======================================================================
def test_lambda_one_phase_satisfies_equation():
    for ste in (0.05, 0.1253, 0.5, 1.0, 5.0):
        lam = solve_lambda_one_phase(ste)
        assert lam * np.exp(lam ** 2) * _erf(lam) == pytest.approx(
            ste / np.sqrt(np.pi), rel=1e-10)


def test_lambda_melt_satisfies_equation():
    """One-phase melting is the mirror of freezing: the SAME erf
    equation with the superheat Ste = c_p (T_s - T_m)/L (the erfc
    form belongs to the two-phase problem only)."""
    for ste in (0.05, 0.3, 0.9):
        lam = solve_lambda_melt(ste)
        assert lam * np.exp(lam ** 2) * _erf(lam) == pytest.approx(
            ste / np.sqrt(np.pi), rel=1e-10)
        assert lam == pytest.approx(solve_lambda_one_phase(ste), rel=1e-12)


def test_two_phase_reduces_to_one_phase():
    lam1 = solve_lambda_one_phase(0.1253)
    lam2 = solve_lambda_two_phase(0.1253, 0.0, ar=1.0)
    assert lam1 == pytest.approx(lam2, rel=1e-8)


def test_neumann_stefan_self_consistency():
    """The analytical solution must satisfy the Stefan condition
    rho L s'(t) = k dT/dx at the front (residual ~ 0)."""
    neu = NeumannOnePhase.freezing(-10.0, 0.0, 5.26e-7, 2.2, 1000.0,
                                   334000.0, 4186.0)
    for t in (50.0, 500.0, 2000.0):
        assert abs(neu.stefan_residual(t)) < 1e-6 * neu.rho * neu.L


def test_neumann_monograph_lambda_is_not_015():
    """Audit findings A1/A2: the correct lambda for the paper's case is
    ~0.245, not the claimed 0.15."""
    neu = NeumannOnePhase.freezing(-10.0, 0.0, 5.26e-7, 2.2, 1000.0,
                                   334000.0, 4186.0)
    assert neu.lam == pytest.approx(0.2453, abs=0.002)
    assert abs(neu.lam - 0.15) > 0.05


def _erf(x):
    from scipy.special import erf
    return erf(x)


def _erfc(x):
    from scipy.special import erfc
    return erfc(x)


# ======================================================================
# Node layers / null transit (monograph sec. 2.7.1)
# ======================================================================
def test_null_transit_axioms():
    st = NodeStates.init(5, 0.0, "freezing")
    st.impose_boundary(0, -10.0)
    assert st.interfaces() == 0
    assert st.boundary_set().tolist() == [0]
    # transit 0 -> 1: nilpotent departure, trace record
    assert st.transit_to(1, 0.0, T_bc_0=-10.0) is True
    assert st.role[0] == NodeRole.GROWN
    assert st.c[0] == 0.0 and st.d[0] == 1.0     # trace stays
    assert st.interfaces() == 1
    # nilpotence: node 0 cannot transit again
    assert st.transit_to(1, 0.0) is False
    # irreversibility: node 1 is visited, cannot be re-entered
    st.transit_to(2, 0.0)
    assert st.visited[:3].tolist() == [True, True, True]
    assert st.d[:3].tolist() == [1.0, 1.0, 1.0]


def test_coincident_first_interval_shields_the_bulk():
    """During the first interval the value layer at node 0 shows T_m
    (the interface), NOT T_s -- the bulk must not see the cold
    boundary (the bug that collapsed the field in early runs)."""
    from bsp.solver import _diffuse, apply_value_pins
    p = _mono_params(t_end=100.0)
    a = np.zeros(6)
    a[0] = -10.0                       # Event-0 Dirichlet value
    apply_value_pins(a, 0, p)          # coincident pin -> T_m
    assert a[0] == p.T_m
    _diffuse(a, 0, p, 20.0, 0.4)
    assert np.allclose(a, p.T_m)       # one-phase bulk never moves


# ======================================================================
# The BSP solver
# ======================================================================
def test_first_event_matches_paper_formula():
    """Paper B.2: dt_1 = rho L dx^2 / (k (T_0 - T_s)) = 15.18 s."""
    p = _mono_params(t_end=30.0)
    r = run_bsp(p)
    dt1 = p.rho * p.L * p.dx ** 2 / (p.k_grown * (p.T_0 - p.T_s))
    assert r.t_events[0] == pytest.approx(dt1, rel=1e-9)
    assert r.t_events[0] == pytest.approx(15.18, abs=0.02)


def test_explicit_rule_stalls_as_printed():
    """Audit finding A4: the paper's explicit rule cannot run on its
    own field (start-of-interval velocity is zero after the first
    transit) -- the appendix table must have used hand-fed gradients."""
    p = _mono_params(t_end=1100.0, event_mode="explicit")
    r = run_bsp(p)
    assert len(r.t_events) <= 3
    assert "velocity" in r.termination or "transit" in r.termination \
        or r.termination == ""


def test_solver_converges_to_neumann():
    p = _mono_params(dx=0.001)
    r = run_bsp(p)
    alpha = p.k_grown / (p.rho * p.cp_grown)
    neu = NeumannOnePhase.freezing(p.T_s, p.T_m, alpha, p.k_grown,
                                   p.rho, p.L, p.cp_grown)
    s = np.asarray(r.s_events)
    t = np.asarray(r.t_events)
    m = s > 0.3 * s[-1]
    rel = np.abs(s[m] - neu.front(t)[m]) / neu.front(t)[m]
    assert float(np.mean(rel)) < 0.10


def test_error_halves_with_dx():
    p1 = _mono_params(dx=0.001)
    p2 = _mono_params(dx=0.0005)
    alpha = p1.k_grown / (p1.rho * p1.cp_grown)
    neu = NeumannOnePhase.freezing(p1.T_s, p1.T_m, alpha, p1.k_grown,
                                   p1.rho, p1.L, p1.cp_grown)
    errs = []
    for p in (p1, p2):
        r = run_bsp(p)
        s = np.asarray(r.s_events)
        t = np.asarray(r.t_events)
        m = s > 0.3 * s[-1]
        errs.append(float(np.mean(np.abs(
            s[m] - neu.front(t)[m]) / neu.front(t)[m])))
    order = np.log2(errs[0] / errs[1])
    assert errs[1] < errs[0]          # decreasing
    assert order > 0.5                # ~1st order (node-pinned front)


def test_energy_conservation_at_events():
    p = _mono_params()
    r = run_bsp(p)
    fare = np.asarray(r.fare_events)
    rhoLdx = p.rho * p.L * p.dx
    # event 1: the null-transit fare = -(rho L dx + boundary-cell chill)
    chill = p.rho * p.cp_grown * (p.T_m - p.T_s) * p.dx
    assert fare[0] == pytest.approx(-(rhoLdx + chill), rel=0.02)
    # events >= 2: conservation drift small vs one cell's latent
    assert float(np.max(np.abs(fare[1:]))) < 0.05 * rhoLdx


def test_second_law():
    p = _mono_params()
    r = run_bsp(p)
    assert float(np.min(r.dS_events)) >= 0.0
    S = np.asarray(r.S_events)
    assert bool(np.all(np.diff(S) >= -1e-15))


def test_sharp_interface_and_clock():
    p = _mono_params()
    r = run_bsp(p)
    assert float(np.sum(r.c_final)) == 1.0
    assert bool(np.all(np.diff(np.asarray(r.p_events)) == 1))
    t = np.asarray(r.t_events)
    dt = np.asarray(r.dt_events)
    assert bool(np.all(np.diff(t) > 0)) and bool(np.all(dt > 0))
    # non-uniform clock (sqrt(t) front -> linearly growing intervals)
    assert float(np.max(dt) / np.min(dt)) > 2.0


def test_melting_mode_runs_and_converges():
    p = BSPParams(mode="melting", T_m=0.0, T_s=15.0, T_0=0.0,
                  length=0.05, dx=0.001, t_end=6000.0,
                  rho=917.0, L=333600.0, k_grown=0.56, cp_grown=4186.0,
                  k_bulk=2.22, cp_bulk=2050.0)
    r = run_bsp(p)
    assert len(r.t_events) >= 5
    alpha = p.k_grown / (p.rho * p.cp_grown)
    neu = NeumannOnePhase.melting(p.T_s, p.T_m, alpha, p.k_grown,
                                  p.rho, p.L, p.cp_grown)
    s = np.asarray(r.s_events)
    t = np.asarray(r.t_events)
    m = s > 0.3 * s[-1]
    rel = np.abs(s[m] - neu.front(t)[m]) / neu.front(t)[m]
    assert float(np.mean(rel)) < 0.10


def test_two_phase_bsp_runs():
    """Superheated liquid (T_0 > T_m): two-phase freezing."""
    p = _mono_params(T_0=5.0, t_end=3000.0)
    r = run_bsp(p)
    assert len(r.t_events) >= 3
    # superheat must slow the front vs the one-phase case
    p1 = _mono_params(t_end=3000.0)
    r1 = run_bsp(p1)
    assert r.s_events[-1] < r1.s_events[-1]


# ======================================================================
# Enthalpy benchmark
# ======================================================================
def test_enthalpy_matches_neumann():
    p = _mono_params()
    er = run_enthalpy(p)
    alpha = p.k_grown / (p.rho * p.cp_grown)
    neu = NeumannOnePhase.freezing(p.T_s, p.T_m, alpha, p.k_grown,
                                   p.rho, p.L, p.cp_grown)
    m = er.t_grid > 200
    rel = np.abs(er.s_grid[m] - neu.front(er.t_grid[m])) / \
        neu.front(er.t_grid[m])
    assert float(np.mean(rel)) < 0.08


def test_bsp_agrees_with_enthalpy():
    """BSP vs the enthalpy benchmark REFINED to dx/4 (at matched dx the
    two schemes carry opposite O(dx) biases of up to ~one cell; the
    refined reference isolates BSP's own error)."""
    p = _mono_params()
    r = run_bsp(p)
    er = run_enthalpy(p, dx=p.dx / 4.0)
    t = np.asarray(r.t_events)
    s = np.asarray(r.s_events)
    s_en = er.front_at(t)
    ok = s_en > 0
    rel = np.abs(s[ok] - s_en[ok]) / s_en[ok]
    assert float(np.mean(rel)) < 0.12


# ======================================================================
# Case I/O
# ======================================================================
def test_case_loading_and_presets():
    path = os.path.join(os.path.dirname(__file__), "..", "cases",
                        "water_ice_monograph.toml")
    cfg = load_case(path)
    p = case_to_params(cfg)
    assert p.mode == "freezing"
    assert p.dx == 0.001
    assert p.rho == 1000.0 and p.L == 334000.0
    assert "water_ice_monograph" in PRESETS


def test_user_data_loading(tmp_path):
    f = tmp_path / "meas.csv"
    f.write_text("t_s,s_m\n100,0.002\n200,0.003\n300,0.004\n")
    t, s = load_user_data(str(f))
    assert list(t) == [100.0, 200.0, 300.0]
    assert list(s) == [0.002, 0.003, 0.004]


# ======================================================================
# Checks / end-to-end
# ======================================================================
def test_check_suite_runs_and_passes():
    p = _mono_params(t_end=1500.0)
    r = run_bsp(p)
    alpha = p.k_grown / (p.rho * p.cp_grown)
    neu = NeumannOnePhase.freezing(p.T_s, p.T_m, alpha, p.k_grown,
                                   p.rho, p.L, p.cp_grown)
    enth = run_enthalpy(p)
    checks = run_checks(p, r, neu, enth=enth)
    by_name = {c.name: c for c in checks}
    assert by_name["neumann_agreement"].verdict == "PASS"
    assert by_name["energy_conservation"].verdict == "PASS"
    assert by_name["second_law"].verdict == "PASS"
    assert by_name["sharp_interface"].verdict == "PASS"
    assert by_name["trace_clock"].verdict == "PASS"
    assert by_name["null_transit"].verdict == "PASS"
    assert by_name["uc_algebra"].verdict == "PASS"
    assert by_name["lattice_counts"].verdict == "PASS"
    assert by_name["enthalpy_agreement"].verdict in ("PASS", "MARGINAL")


def test_monograph_audit():
    from bsp.monograph import audit_monograph
    a = audit_monograph()
    assert a["lambda"]["correct_lambda"] == pytest.approx(0.2453,
                                                          abs=0.002)
    assert a["lambda"]["paper_claim"] == 0.15
    assert a["first_event"]["reproduced"] is True
    assert a["alpha"]["ratio"] == pytest.approx(2.19, abs=0.05)
    # the paper's explicit rule cannot reproduce its own table
    assert a["event_tables"]["explicit_rule_run"]["n_events"] <= 3
    # the faithful run is within a few percent of the CORRECT Neumann
    assert a["headline_t1000"]["bsp_vs_correct_selfconsistent"] < 0.06
