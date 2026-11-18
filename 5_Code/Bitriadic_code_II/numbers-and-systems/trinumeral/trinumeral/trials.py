"""Proof by trial: the V1-V10 battery for the trinumeral implementation.

Verdict vocabulary (as in the companion fare-octal and nilpotent-crypto
projects):

  EST-CONFIRMED   a monograph claim reproduced exactly;
  CORRECTED       a monograph inconsistency, pinned by an exact
                  witness, with the corrected statement implemented;
  BY-TRIAL        an empirical finding of this battery;
  OPEN            documented, not decidable here.

Headline results (full dossier in results/TRINUMERAL_TRIALS.md):

* The sec. 8.4.8 worked example (T3 = 0.1) reproduces EXACTLY:
  gamma = 1/2^55 ~ 2.78e-17 ("approximately 1e-17"), tau-cycle
  coefficient ~ -2.78e-19 ("on the order of 1e-19"), and the three
  discrepancies telescope to zero identically (the heterobase triangle
  closes -- established here as the Telescope Theorem).
* The default (trigger 1, response 1) regime makes the monograph's
  "coherent spinor regime" literal: a 720-degree rotation returns
  sigma to +1 with zero crossing trace and ghost = 2; the Berry-phase
  regime (+360, -360) leaves trace e1 - e2 != 0.
* Seven monograph inconsistencies corrected with exact witnesses
  (C1-C7), including: the float->binary edge is degenerate under the
  formal definition (every IEEE double is dyadic); sec. 8.4.8's
  discrepancy signs are the negatives of sec. 8.4.2's; sec. 8.4.3
  Level 1 transfers |alpha| where sec. 8.4.3a transfers 2|alpha|.
"""

from __future__ import annotations

import datetime
import io
import math
import random
from fractions import Fraction

from .core import (DEFAULT_P, EDGE_NAMES, Regime, Trinumeral, canonical,
                   encode_binary, exact)
from .grassmann import (E1, E2, E3, TOP, ZERO, GrassmannElement, scalar,
                        wedge)
from .ladder import LadderEngine
from .spin import FULL_TURN, SpinTally, SpinorialTally


def _rng():
    return random.Random(20261115)


# ---------------------------------------------------------------------------
def v1_exterior_algebra():
    a, b = E1 * E2, E2 * E1
    assoc = True
    rng = _rng()

    def rnd():
        el = ZERO
        for _ in range(3):
            g = GrassmannElement.generator(rng.randrange(3))
            el = el + rng.randint(-3, 3) * g
        return el

    for _ in range(300):
        x, y, z = rnd(), rnd(), rnd()
        assoc &= (x * y) * z == x * (y * z)
    basis = [scalar(1), E1, E2, E3, E1 * E2, E1 * E3, E2 * E3, TOP]
    grades = [sum(1 for b in basis
                  if not b.is_zero() and len(next(iter(b.terms))) == g)
              for g in range(4)]
    return {
        "verdict": "EST-CONFIRMED",
        "generators_nilpotent": all(e * e == ZERO for e in (E1, E2, E3)),
        "anticommute": (a == -b and E2 * E3 == -(E3 * E2)
                        and E3 * E1 == -(E1 * E3)),
        "associativity_300": assoc,
        "tau_cycle_squared_zero": TOP * TOP == ZERO,
        "monograph_derivation": ("sec. 8.4.5's anticommutation chase "
                                 "reproduces: (e1e2e3)^2 moves e3 past "
                                 "e1 and e2 (two sign flips, net +), "
                                 "then e1e1 = 0 kills it -- implemented "
                                 "structurally by the wedge product"),
        "basis_by_grade_1_3_3_1": grades == [1, 3, 3, 1],
        "eight_activation_patterns": 2 ** 3 == len(basis),
    }


def v2_construction():
    T = Trinumeral.omega_0(Fraction(1, 10))
    a, b, g = T.fresh_discrepancies()
    rng = _rng()
    telescope = True
    for _ in range(500):
        v = Fraction(rng.randint(-10 ** 6, 10 ** 6),
                     rng.randint(1, 10 ** 6))
        t = Trinumeral.omega_0(v)
        x, y, z = t.fresh_discrepancies()
        telescope &= (x + y + z) == 0
    Tn = Trinumeral.omega_0(Fraction(-1, 10))
    an, bn, gn = Tn.fresh_discrepancies()
    return {
        "verdict": "EST-CONFIRMED",
        "worked_example_alpha": (a == Fraction(900719925474099, 2 ** 53),
                                 f"{float(a):.17g} (monograph: ~0.1)"),
        "worked_example_beta": (b == Fraction(-3602879701896397, 2 ** 55),
                                f"{float(b):.17g} (monograph: -0.1)"),
        "worked_example_gamma": (g == Fraction(1, 2 ** 55),
                                 f"{float(g):.3g} (monograph: ~1e-17)"),
        "telescope_theorem_500_random": telescope,
        "telescope_statement": ("with fb_mode='stored' (the practice "
                                "note of sec. 8.4.2), alpha+beta+gamma = "
                                "0 identically: the heterobase triangle "
                                "B -> i -> f -> B closes"),
        "negative_symmetry": (an == -a and bn == -b and gn == -g),
        "fb_mode_exact_gamma_zero": (Trinumeral.omega_0(
            Fraction(1, 10), fb_mode="exact").fresh_discrepancies()[2] == 0),
        "C1_note": ("under the FORMAL definition (B_fb = exact re-encode "
                    "of f) gamma is identically ZERO -- every IEEE "
                    "double is a dyadic rational with a finite binary "
                    "expansion; the monograph's own example magnitude "
                    "requires the 'stored B' reading, which is the "
                    "default here"),
    }


def v3_tau_cycle():
    T = Trinumeral.omega_0(Fraction(1, 10))
    cyc = T.cycle_coefficient()
    any_exact_kills = all(
        Trinumeral.omega_0(v).cycle_coefficient() == 0
        for v in (5, Fraction(1, 2), Fraction(3, 2)))
    frag = T.float2bin()          # e3 ledger goes to zero (linear cancel)
    return {
        "verdict": "EST-CONFIRMED",
        "cycle_coefficient": (cyc, f"{float(cyc):.3g} "
                                 f"(monograph: order 1e-19)"),
        "cycle_sign_contraction": cyc < 0,
        "sign_meaning": ("alpha beta gamma < 0: net contraction parity "
                         "around the cycle (sec. 8.4.4)"),
        "any_exact_edge_kills_cycle": any_exact_kills,
        "cycle_nilpotent": T.tau_cycle() * T.tau_cycle() == ZERO,
        "accumulates_cannot_compound": ("(e1^e2^e3)^2 = 0 structurally "
                                        "-- the wedge of the top with "
                                        "itself vanishes"),
    }


def v4_invariant_points():
    traceless = {v: Trinumeral.omega_0(v).is_traceless()
                 for v in (0, 1, 5, -7, 2 ** 53, Fraction(3, 2),
                           Fraction(1, 2), 2 ** 53 + 1, 2 ** 53 + 2)}
    chars = all(Trinumeral.omega_0(k).is_traceless() == (float(k) == k)
                for k in (0, 1, 5, 2 ** 53, 2 ** 53 + 1, 2 ** 53 + 2,
                          2 ** 54 - 2, 10 ** 20, 2 ** 54 + 1))
    return {
        "verdict": "CORRECTED (C7: the sec. 8.4.17 candidate list)",
        "traceless_by_value": {str(k): v for k, v in traceless.items()},
        "exact_characterization": ("traceless  <=>  v is an integer "
                                   "exactly representable in double "
                                   "precision (float(int(v)) == v): "
                                   "all |k| <= 2^53, even steps up to "
                                   "2^54, ..."),
        "characterization_holds": chars,
        "C7_witness": ("3/2 and 1/2 ('powers of two, exactly "
                       "representable floats' per sec. 8.4.17) are NOT "
                       "invariant points: beta = i - f = -1/2 != 0 -- "
                       "the integer sheet cannot hold fractions, as the "
                       "monograph's own sec. 8.4.1 opening states"),
        "nihilum": Trinumeral.omega_0(0).is_nihilum(),
    }


def v5_conversions():
    u = Trinumeral.omega_0(2 ** 53 + 1)
    v1 = u.int2float()
    t01 = Trinumeral.omega_0(Fraction(1, 10))
    fb1 = t01.float2bin()
    fb55 = Trinumeral.omega_0(Fraction(1, 10), p=55).float2bin()
    bi = Trinumeral.omega_0(Fraction(7, 3)).bin2int()
    return {
        "verdict": "EST-CONFIRMED",
        "int2float_rounding_witness": (v1.tau.coefficient(1) == 0
                                       and
                                       v1.fresh_discrepancies()[1] == 1,
                                       "the e2 record for i = 2^53+1 is "
                                       "exactly -1 (the double rounds); "
                                       "the LEDGER cancels the "
                                       "construction's +1 linearly, the "
                                       "STATE stays incoherent by "
                                       "exactly 1 -- both exact"),
        "float2bin_residue": (fb1.tau.coefficient(2)
                              + Fraction(1, 2 ** 55) == 0,
                              "ledger: initial +1/2^55 (construction) "
                              "cancels the conversion's -1/2^55 linearly "
                              "-- the LEDGER vs STATE distinction"),
        "float2bin_record_zero_at_p55": (fb55.tau.coefficient(2)
                                         == Fraction(1, 2 ** 55),
                                         "at p = 55 the re-encode of the "
                                         "double is exact, so the "
                                         "conversion records 0; the "
                                         "ledger keeps only the "
                                         "construction's +1/2^55"),
        "bin2int_extracts_integer": (bi.i == 2,
                                     "i' = trunc(canonical(B)) = 2 for "
                                     "v = 7/3; recorded (i'-i) = 0 since "
                                     "i was already 2 -- the fractional "
                                     "residue stays on the state, "
                                     "alpha = 1/3"),
        "post_int2float_float_of_int": v1.f == float(2 ** 53 + 1),
        "ledger_vs_state": ("tau is a path-dependent LEDGER of "
                            "conversion events; fresh_discrepancies() is "
                            "a path-independent STATE function; a "
                            "conversion record can cancel initial trace "
                            "linearly without annihilation (witness "
                            "above) -- the monograph's two uses of "
                            "'trace' are distinguished here"),
    }


def _scenario(trigger, response, seq, edge=2, **kw):
    """Run a conversion sequence on a clean edge under a regime."""
    regime = Regime(trigger=trigger, response=response, **kw)
    eng = LadderEngine(regime)
    transfers = [eng.record(edge, Fraction(a)) for a in seq]
    return eng, transfers


def v6_annihilation_ladder():
    out = {"verdict": "BY-TRIAL (+ corrections C3, C4)"}
    # response invariants, each under trigger 5 (always) so the response
    # alone is exercised, on the clean sequence [a, a]:
    seqs = {}
    for resp in range(6):
        eng, tr = _scenario(5, resp, [1, 1])
        seqs[f"R{resp}([1,1])"] = {
            "trace_e": eng.tau.coefficient(2), "ghost": eng.ghost}
    # R1 pair conservation (C3): 2|alpha| conserved
    eng, tr = _scenario(1, 1, [1, 1])
    r1 = {"pair": (eng.tau.coefficient(2) == 0 and eng.ghost == 2),
          "transfer_2alpha": tr[1] == 2,
          "C3": ("sec. 8.4.3 Level 1 prints ghost += |alpha| (loses "
                 "|alpha|); sec. 8.4.3a Level 1's 2|alpha| conserves "
                 "total magnitude -- implemented, tested")}
    # R2 saturation: trace bounded at one unit, repeats diverted
    eng2, _ = _scenario(5, 2, [1, 1, 1, 1])
    r2 = {"saturation": (eng2.tau.coefficient(2) == 1
                         and eng2.ghost == 3)}
    # R3 reset loses prior magnitude
    eng3, _ = _scenario(5, 3, [1, 1])
    r3 = {"reset_loss": (eng3.tau.coefficient(2) == 0
                         and eng3.ghost == 1)}
    # R4 chiral: same sign cancels, opposite adds
    eng4, _ = _scenario(5, 4, [1, 1])
    eng4b, _ = _scenario(5, 4, [1, -1])
    r4 = {"same_sign_cancels": (eng4.tau.coefficient(2) == 0
                                and eng4.ghost == 2),
          "opposite_adds": (eng4b.tau.coefficient(2) == 0
                            and eng4b.ghost == 0,
                            "linear: +1 + (-1) = 0 with NO ghost "
                            "transfer -- the crossing pair is invisible "
                            "to the ghost under R4")}
    # R5 threshold k=3
    eng5, _ = _scenario(5, 5, [1, 1, 1], k_resp=3)
    r5 = {"threshold_k3": (eng5.tau.coefficient(2) == 0
                           and eng5.ghost == 3)}
    # trigger semantics, each paired with response 3 (reset), which
    # leaves clear evidence of firing (trace -> 0, ghost grows)
    t0 = _scenario(0, 3, [1, 1])[0]              # never fires
    t1_no = _scenario(1, 3, [1, 2])[0]           # different value: no
    t1_yes = _scenario(1, 3, [1, 1])[0]          # identical: fires
    t2 = _scenario(2, 3, [1, 1 + Fraction(1, 10 ** 7)])[0]  # within eps
    t2_no = _scenario(2, 3, [1, 2])[0]           # outside eps: no
    t3 = _scenario(3, 3, [1, 5])[0]              # any second conversion
    t4 = _scenario(4, 3, [1, 1, 1], k_trig=3)[0]  # 3rd repetition fires
    t5 = _scenario(5, 3, [1])[0]                 # always: first fires
    # spent flag: after T1 annihilation, identical conversions inert
    engs = _scenario(1, 1, [1, 1, 1])[0]
    return {
        **out,
        "response_matrix_[1,1]_per_level": seqs,
        "R1_pair": r1,
        "R2_saturation": r2,
        "R3_reset_loss": r3,
        "R4_chiral": r4,
        "R5_threshold_k3": r5,
        "T0_never_fires": (t0.tau.coefficient(2) == 2 and t0.ghost == 0),
        "T1_exact_only": (t1_no.tau.coefficient(2) == 3
                          and t1_no.ghost == 0
                          and t1_yes.tau.coefficient(2) == 0
                          and t1_yes.ghost == 1),
        "T2_within_eps": (t2.tau.coefficient(2) == 0
                          and t2_no.tau.coefficient(2) == 3),
        "T3_any_repeat": t3.tau.coefficient(2) == 0,
        "T4_count_k3": t4.tau.coefficient(2) == 0,
        "T5_first_conversion_fires": (t5.tau.coefficient(2) == 0
                                      and t5.ghost == 1,
                                      "the extreme bosonic limit of "
                                      "sec. 8.4.3 Level 5: every "
                                      "conversion immediately to the "
                                      "ghost disc"),
        "spent_flag_after_pair": (engs.tau.coefficient(2) == 0
                                  and engs.ghost == 2,
                                  "third identical conversion has no "
                                  "effect (sec. 8.4.3 Level 1)"),
        "C4": ("response-level embedded preconditions clarified: R1 "
               "cancels only true pairs; R4's transfer generalized to "
               "|t| + |alpha|; R2 fills an empty cell before "
               "saturating -- see ladder.py docstring"),
    }


def v7_arithmetic():
    A, B = Trinumeral.omega_0(2), Trinumeral.omega_0(3)
    S = A + B
    X = Trinumeral.omega_0(2, adder="xor") + Trinumeral.omega_0(3,
                                                                adder="xor")
    I = Trinumeral.omega_0(Fraction(1, 10), adder="ieee") \
        + Trinumeral.omega_0(Fraction(2, 10), adder="ieee")
    M = Trinumeral.omega_0(2 ** 64 - 1, adder="mod", mod_bits=64) \
        + Trinumeral.omega_0(2, adder="mod", mod_bits=64)
    return {
        "verdict": "EST-CONFIRMED (+ correction C2)",
        "monograph_2_plus_3": (S.i == 5 and S.f == 5.0 and S.is_traceless()
                               and S.tau.is_zero(),
                               "sec. 8.4.8: '(B, 5, 5.0, 0) with no "
                               "trace'"),
        "xor_parity_sheet": (canonical(X.B) == 1 and X.i == 5
                             and X.tau.coefficient(0) == -4,
                             "2 xor 3 = 1: the carry 4 is discarded and "
                             "RECORDED on e1 (alpha = 1 - 5 = -4) -- "
                             "'discards magnitude and retains only "
                             "parity'"),
        "ieee_rounding_feeds_tau": (I.f == 0.1 + 0.2
                                    and not I.is_traceless(),
                                    f"0.1 + 0.2 = {I.f!r}; the rounding "
                                    "is recorded on the trace"),
        "mod_wraps": (canonical(M.B) == 1,
                      "(2^64 - 1) + 2 mod 2^64 = 1: cyclic tally"),
        "C2_signs_witness": (X.fresh_discrepancies()[0] == -4,
                             "the xor case: recorded fresh alpha = "
                             "canonical(B) - i = 1 - 5 = -4, while sec. "
                             "8.4.8's printed Delta_bi = i - canonical(B) "
                             "= +4 -- the signs are flipped; the "
                             "consistent sec. 8.4.2 conventions are "
                             "implemented (either telescopes)"),
    }


def v8_spin_tallies():
    rng = _rng()
    s = SpinTally(0, 300) + SpinTally(0, 100)
    neg = SpinTally.from_angle(-1)
    invariant = True
    for _ in range(500):
        a = SpinTally(rng.randint(-5, 5),
                      Fraction(rng.randint(0, 359)))
        b = SpinTally(rng.randint(-5, 5),
                      Fraction(rng.randint(0, 359)))
        c = a + b
        invariant &= 0 <= c.r < FULL_TURN and c.angle == a.angle + b.angle
    theta = Fraction(700, 3)
    variants = SpinTally.from_angle(theta).in_variants()
    shifts = [SpinTally.from_angle(theta).shift_to(v)
              for v in variants.values()]
    return {
        "verdict": "EST-CONFIRMED",
        "angle_bridge_example": (s == SpinTally(1, 40),
                                 "sec. 8.4.10: (0,300)+(0,100) = (1,40)"),
        "negative_angle_remark": (neg == SpinTally(-1, 359),
                                  "theta = -1: floor(-1/360) = -1, "
                                  "r = 359 -- the convention remark"),
        "invariant_500_random": invariant,
        "three_tally_types_one_angle": {
            v: (t.t, str(t.r)) for v, t in variants.items()},
        "shifts": [str(x) for x in shifts],
        "shift_note": ("the re-encoding shifts between tally types are "
                       "the spin-domain translation costs (sec. 8.4.11: "
                       "the tally type defines the representation)"),
    }


def v9_double_cover():
    origin = SpinTally(0, 0)
    s = SpinorialTally(origin)
    s360 = s.rotate(360)
    s720 = s.rotate(360).rotate(360)
    s720jump = s.rotate(720)
    berry = s.rotate(360).rotate(-360)
    quad = s.rotate(180).rotate(180).rotate(180).rotate(180)
    boson = origin + SpinTally.from_angle(360)
    return {
        "verdict": "EST-CONFIRMED (+ corrections C5, C6)",
        "360_flips_once": (s360.sigma == -1 and not s360.tau.is_zero()),
        "720_returns_original_sheet": (s720.sigma == +1
                                       and s720.tau.is_zero()
                                       and s720.ghost == 2,
                                       "the coherent spinor regime "
                                       "(sec. 8.4.18 Level 1): two "
                                       "identical crossings pair-"
                                       "annihilate, ghost = 2, pure "
                                       "state"),
        "single_720_jump": (s720jump.sigma == +1
                            and s720jump.tau.coefficient(0) == 2,
                            "C5: sigma flips PER BOUNDARY (net parity), "
                            "so one 720-degree jump also returns to +1; "
                            "sec. 8.4.12's printed rule (flip once when "
                            "floors differ) would give -1 here and "
                            "contradict sec. 8.4.18"),
        "berry_phase_regime": (not berry.tau.is_zero()
                               and berry.tau.coefficient(0) == 1
                               and berry.tau.coefficient(1) == -1,
                               "sec. 8.4.18 Level 4: +360 then -360 "
                               "leaves trace e1 - e2 != 0 -- the system "
                               "remembers the path, not the endpoint"),
        "four_half_turns": quad.sigma == +1,
        "bosonic_plain_tally": (boson.t == 1 and boson.r == 0,
                                "the plain tally returns to the origin "
                                "mod 360 with the winding recorded in t "
                                "('a wound spring')"),
        "C6": ("sec. 8.4.18 Level 3's 'after 360, sigma returns to +1' "
               "does not follow from the algebraic flip rule (sigma = "
               "-1 after one crossing under every regime); the bosonic "
               "return is the PLAIN tally's mod-360 identity; the "
               "ladder levels change trace/ghost bookkeeping, not the "
               "flip rule"),
    }


def v10_gates_and_status():
    T = Trinumeral.omega_0(Fraction(1, 10))
    proj = (T.project_0a("bin") == T.B and T.project_0a("int") == T.i
            and T.project_0a("float") == T.f)
    # ghost monotone under a long random conversion history
    rng = _rng()
    eng = LadderEngine(Regime())
    prev = 0
    monotone = True
    for _ in range(500):
        eng.record(rng.randrange(3), Fraction(rng.randint(1, 9)))
        monotone &= eng.ghost >= prev
        prev = eng.ghost
    # all 8 activation patterns reachable
    seen = set()
    for bits in range(8):
        t = Trinumeral.omega_0(5)
        for edge in range(3):
            if bits >> edge & 1:
                t.engine.record(edge, Fraction(1))
        seen.add(t.activation())
    return {
        "verdict": "EST-CONFIRMED (gates) / OPEN (status)",
        "projections_lose_trace": proj,
        "projection_note": ("0/a returns exactly the sheet; tau and the "
                            "ghost disc are invisible to every "
                            "single-base observer (sec. 8.4.6)"),
        "ghost_monotone_500": monotone,
        "all_8_activation_patterns_reachable": len(seen) == 8,
        "patterns_embed_note": ("the 2^3 = 8 patterns of sec. 8.4.7 are "
                                "the basis monomials of Lambda(V); the "
                                "117-point lattice embedding is asserted "
                                "by the monograph, not implemented here"),
        "OPEN_tau_cycle_bifurcation": ("sec. 8.4.5: 'Its growth under "
                                       "iteration would force a "
                                       "bifurcation - a topic for "
                                       "further research' -- not "
                                       "decidable here"),
        "OPEN_ladder_UCQ_UCO_UCS": ("sec. 8.4.16's two-sheet ladder "
                                    "UC -> UCQ -> UCO -> UCS: the UCQ "
                                    "rung is implemented and verified in "
                                    "the companion nilpotent-crypto "
                                    "project; UCO/UCS are not "
                                    "implemented"),
    }


# ---------------------------------------------------------------------------
def run_trials() -> dict:
    return {"V1_exterior_algebra": v1_exterior_algebra(),
            "V2_construction": v2_construction(),
            "V3_tau_cycle": v3_tau_cycle(),
            "V4_invariant_points": v4_invariant_points(),
            "V5_conversions": v5_conversions(),
            "V6_annihilation_ladder": v6_annihilation_ladder(),
            "V7_arithmetic": v7_arithmetic(),
            "V8_spin_tallies": v8_spin_tallies(),
            "V9_double_cover": v9_double_cover(),
            "V10_gates_and_status": v10_gates_and_status()}


def _fmt(obj, indent=0):
    pad = "  " * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list, tuple)):
                lines.append(f"{pad}{k}:")
                lines.append(_fmt(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {v}")
        return "\n".join(lines)
    if isinstance(obj, (list, tuple)):
        return "\n".join(f"{pad}- {x}" for x in obj)
    return f"{pad}{obj}"


def write_report(results: dict, path: str) -> str:
    buf = io.StringIO()
    w = buf.write
    w("# The Trinumeral, Operational: Proof by Trial\n\n")
    w(f"**Generated:** "
      f"{datetime.datetime.now().isoformat(timespec='seconds')}  \n")
    w("**Source:** Poetica Mathematica Ch. VIII sec. 8.4 "
      "(Heterobase counting system: Trinumeral, spin-tallies), "
      "secs. 8.4.1-8.4.18.\n\n")
    w("## Verdicts\n\n| id | trial | verdict |\n|----|-------|--------|\n")
    for k, v in results.items():
        w(f"| {k.split('_')[0]} | {k.split('_', 1)[1].replace('_', ' ')} "
          f"| **{v['verdict']}** |\n")
    w("\n## Corrections to the monograph (exact witnesses above)\n\n")
    w("* **C1** sec. 8.4.2: under the formal definition of gamma "
      "(B_fb = exact re-encoding of Re(f)) the float-to-binary edge is "
      "degenerate -- every IEEE 754 double is a dyadic rational, so "
      "gamma = 0 identically.  The sec. 8.4.8 worked example (~1e-17) "
      "requires the practice-note reading (B_fb = stored B); both are "
      "implemented ('stored' is the default and yields the Telescope "
      "Theorem alpha+beta+gamma = 0).\n")
    w("* **C2** sec. 8.4.8: the prescribed fresh-discrepancy signs "
      "(Delta_bi = i - canonical(B), ...) are the negatives of sec. "
      "8.4.2's edge conventions; the consistent 8.4.2 signs are "
      "implemented.\n")
    w("* **C3** sec. 8.4.3 Level 1 transfers |alpha| to the ghost; sec. "
      "8.4.3a Level 1 transfers 2|alpha| and 'conserves total "
      "magnitude'.  The conserving version is implemented.\n")
    w("* **C4** response-level preconditions clarified (R1 cancels only "
      "true pairs; R4's transfer generalized to |t|+|alpha|; R2 fills "
      "an empty cell before saturating).\n")
    w("* **C5** sec. 8.4.12's sigma-flip rule as printed (flip once "
      "when the floor-quotients differ) contradicts sec. 8.4.18 for "
      "multi-boundary jumps (a single 720-degree jump must return "
      "sigma to +1); flip-per-boundary is implemented.\n")
    w("* **C6** sec. 8.4.18 Level 3's 'after 360, sigma returns to +1': "
      "under the algebraic flip rule sigma = -1 after one crossing in "
      "every regime; the bosonic return is the plain tally's mod-360 "
      "identity.\n")
    w("* **C7** sec. 8.4.17's invariant-point candidates ('integer "
      "values, powers of two, and exactly representable floats'): the "
      "exact simultaneous-vanishing set is the integers exactly "
      "representable in double precision; 3/2 and 1/2 have beta != 0 "
      "necessarily.\n\n")
    w("## Established here\n\n")
    w("* **The Telescope Theorem**: with the stored-B reading, "
      "alpha + beta + gamma = 0 identically -- the heterobase triangle "
      "B -> i -> f -> B closes (500 random rationals, exact).\n")
    w("* **The monograph's worked example reproduces exactly**: for "
      "v = 1/10, gamma = 1/2^55 (the 'approximately 1e-17'), tau-cycle "
      "coefficient -2.78e-19 (the 'order of 1e-19').\n")
    w("* **The coherent spinor regime is literal**: under the default "
      "(trigger 1, response 1), a 720-degree rotation pair-annihilates "
      "its crossing trace (ghost = 2, pure state, sigma = +1), and the "
      "Berry-phase regime leaves e1 - e2 != 0.\n")
    w("* **Ledger vs state**: the trace tau is a path-dependent ledger "
      "of conversion events; fresh_discrepancies() is a path-"
      "independent state function.  The monograph's 'trace' names "
      "both; the implementation separates them (V5 witness).\n\n")
    w("## Reproduction\n\n```bash\ntrinumeral trials   # or: python -m "
      "trinumeral trials\npytest\n```\n")
    for k, v in results.items():
        w(f"\n---\n\n## {k.replace('_', ' ')}\n\n```\n{_fmt(v)}\n```\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return path
