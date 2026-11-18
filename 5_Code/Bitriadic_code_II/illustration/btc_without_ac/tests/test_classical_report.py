"""Tests: classical F2 machinery and the report pipeline."""

import numpy as np

from btc_without_ac import classical, report
from btc_without_ac.uc import ExactUC


# ----------------------------------------------------------------------
# free group word machinery
# ----------------------------------------------------------------------
def test_reduce_and_multiply():
    assert classical.reduce_word((0, 2)) == ()
    assert classical.reduce_word((0, 1, 3)) == (0,)
    assert classical.reduce_word((0, 0, 2, 1)) == (0, 1)
    assert classical.multiply_words((0,), (2, 1)) == (1,)
    assert classical.word_to_str(()) == "e"
    assert classical.word_to_str((0, 3)) == "aB"


def test_ball_size_formula():
    for L in range(1, 7):
        assert len(classical.ball_words(L)) == classical.ball_size(L)


def test_paradoxical_decomposition_of_f2():
    r = classical.paradoxical_decomposition(6)
    assert r.partition_ok                    # 4 pieces + {e} partition B_6
    assert r.copy1_cover                     # S(a) + a S(A) covers B_5
    assert r.copy2_cover                     # S(b) + b S(B) covers B_5
    assert r.copies_disjoint_pieces          # disjoint piece usage
    # no choice anywhere: pieces are defined by first letter
    assert sum(r.pieces.values()) == r.words - 1


def test_free_rotation_generators_are_rotations():
    A, B = classical.free_rotation_generators()
    for M in (A, B):
        assert np.allclose(M @ M.T, np.eye(3), atol=1e-12)
        assert np.isclose(np.linalg.det(M), 1.0)
    # the 3-4-5 angle: cos = 3/5 sits on each generator's rotation block
    assert np.isclose(A[0, 0], 3.0 / 5.0) and np.isclose(A[1, 1], 3.0 / 5.0)
    assert np.isclose(B[1, 1], 3.0 / 5.0) and np.isclose(B[2, 2], 3.0 / 5.0)


def test_freeness_spot_check():
    res = classical.check_freeness(4)
    assert res["no_word_is_identity"]
    assert res["orbit_injective"]
    assert res["words_checked"] == classical.ball_size(4) - 1


def test_orbit_transfer_choice_free():
    res = classical.orbit_transfer(3)
    assert res["pieces_disjoint"]
    assert res["pieces_cover_orbit"]


def test_foelner_ratios():
    fol = classical.foelner_ratio(6)
    # F2: ratio decreases to 2 from above (non-amenable)
    ratios = [r for _, r in fol["F2_ratios"]]
    assert all(r > 1.9 for r in ratios)
    assert abs(ratios[-1] - 2.0) < 0.05
    # Z: ratio decays to 0 (amenable)
    assert fol["Z_ratios"][-1][1] < 0.025


# ----------------------------------------------------------------------
# report pipeline
# ----------------------------------------------------------------------
def test_report_runs_and_writes(tmp_path):
    claims = report.run_all_checks(seed=123)
    assert len(claims) == 17  # claims 1-14 + three conjectures 15a-15c
    # every claim produced a status
    assert all(c.status for c in claims)
    # the load-bearing claims must verify
    by_no = {c.number: c for c in claims}
    assert by_no["1"].status.startswith("VERIFIED")   # UC algebra
    assert by_no["3"].status.startswith("VERIFIED")   # triadic partition
    assert by_no["4"].status.startswith("VERIFIED")   # apparent counts
    assert by_no["7"].status.startswith("VERIFIED")   # ghost + accounting
    assert by_no["9"].status.startswith("VERIFIED")   # phi bijections
    assert by_no["10"].status.startswith("PARTIAL")   # homeomorphism caveat
    assert by_no["12"].status.startswith("VERIFIED")  # F2 decomposition
    assert by_no["14"].status.startswith("NOT COMPUTABLE")
    out = tmp_path / "report.md"
    report.write_report(claims, str(out), header="test run")
    text = out.read_text(encoding="utf-8")
    assert "Verification Report" in text
    assert "Where the Axiom of Choice enters" in text
    assert "## Claim 10" in text


def test_console_summary_format():
    claims = report.run_all_checks(seed=7)
    text = report.format_console(claims)
    assert "verification summary" in text
    assert "FAIL" not in text.replace("FAILED", "")  # no failed claims


def test_exact_uc_cross_check_in_report():
    """The report's algebra check uses exact Fractions; make sure the
    deterministic seed really exercises non-invertible elements too."""
    rng = np.random.default_rng(11)
    zero_divisors = 0
    for _ in range(500):
        x = ExactUC(*(int(rng.integers(-3, 4)) for _ in range(4)))
        if x.is_pure_trace():
            zero_divisors += 1
            assert x * x == ExactUC()
    assert zero_divisors > 0
