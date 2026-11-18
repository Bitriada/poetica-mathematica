# The Trinumeral, Operational: Proof by Trial

**Generated:** 2026-11-15T20:12:58  
**Source:** Poetica Mathematica Ch. VIII sec. 8.4 (Heterobase counting system: Trinumeral, spin-tallies), secs. 8.4.1-8.4.18.

## Verdicts

| id | trial | verdict |
|----|-------|--------|
| V1 | exterior algebra | **EST-CONFIRMED** |
| V2 | construction | **EST-CONFIRMED** |
| V3 | tau cycle | **EST-CONFIRMED** |
| V4 | invariant points | **CORRECTED (C7: the sec. 8.4.17 candidate list)** |
| V5 | conversions | **EST-CONFIRMED** |
| V6 | annihilation ladder | **BY-TRIAL (+ corrections C3, C4)** |
| V7 | arithmetic | **EST-CONFIRMED (+ correction C2)** |
| V8 | spin tallies | **EST-CONFIRMED** |
| V9 | double cover | **EST-CONFIRMED (+ corrections C5, C6)** |
| V10 | gates and status | **EST-CONFIRMED (gates) / OPEN (status)** |

## Corrections to the monograph (exact witnesses above)

* **C1** sec. 8.4.2: under the formal definition of gamma (B_fb = exact re-encoding of Re(f)) the float-to-binary edge is degenerate -- every IEEE 754 double is a dyadic rational, so gamma = 0 identically.  The sec. 8.4.8 worked example (~1e-17) requires the practice-note reading (B_fb = stored B); both are implemented ('stored' is the default and yields the Telescope Theorem alpha+beta+gamma = 0).
* **C2** sec. 8.4.8: the prescribed fresh-discrepancy signs (Delta_bi = i - canonical(B), ...) are the negatives of sec. 8.4.2's edge conventions; the consistent 8.4.2 signs are implemented.
* **C3** sec. 8.4.3 Level 1 transfers |alpha| to the ghost; sec. 8.4.3a Level 1 transfers 2|alpha| and 'conserves total magnitude'.  The conserving version is implemented.
* **C4** response-level preconditions clarified (R1 cancels only true pairs; R4's transfer generalized to |t|+|alpha|; R2 fills an empty cell before saturating).
* **C5** sec. 8.4.12's sigma-flip rule as printed (flip once when the floor-quotients differ) contradicts sec. 8.4.18 for multi-boundary jumps (a single 720-degree jump must return sigma to +1); flip-per-boundary is implemented.
* **C6** sec. 8.4.18 Level 3's 'after 360, sigma returns to +1': under the algebraic flip rule sigma = -1 after one crossing in every regime; the bosonic return is the plain tally's mod-360 identity.
* **C7** sec. 8.4.17's invariant-point candidates ('integer values, powers of two, and exactly representable floats'): the exact simultaneous-vanishing set is the integers exactly representable in double precision; 3/2 and 1/2 have beta != 0 necessarily.

## Established here

* **The Telescope Theorem**: with the stored-B reading, alpha + beta + gamma = 0 identically -- the heterobase triangle B -> i -> f -> B closes (500 random rationals, exact).
* **The monograph's worked example reproduces exactly**: for v = 1/10, gamma = 1/2^55 (the 'approximately 1e-17'), tau-cycle coefficient -2.78e-19 (the 'order of 1e-19').
* **The coherent spinor regime is literal**: under the default (trigger 1, response 1), a 720-degree rotation pair-annihilates its crossing trace (ghost = 2, pure state, sigma = +1), and the Berry-phase regime leaves e1 - e2 != 0.
* **Ledger vs state**: the trace tau is a path-dependent ledger of conversion events; fresh_discrepancies() is a path-independent state function.  The monograph's 'trace' names both; the implementation separates them (V5 witness).

## Reproduction

```bash
trinumeral trials   # or: python -m trinumeral trials
pytest
```

---

## V1 exterior algebra

```
verdict: EST-CONFIRMED
generators_nilpotent: True
anticommute: True
associativity_300: True
tau_cycle_squared_zero: True
monograph_derivation: sec. 8.4.5's anticommutation chase reproduces: (e1e2e3)^2 moves e3 past e1 and e2 (two sign flips, net +), then e1e1 = 0 kills it -- implemented structurally by the wedge product
basis_by_grade_1_3_3_1: True
eight_activation_patterns: True
```

---

## V2 construction

```
verdict: EST-CONFIRMED
worked_example_alpha:
  - True
  - 0.099999999999999978 (monograph: ~0.1)
worked_example_beta:
  - True
  - -0.10000000000000001 (monograph: -0.1)
worked_example_gamma:
  - True
  - 2.78e-17 (monograph: ~1e-17)
telescope_theorem_500_random: True
telescope_statement: with fb_mode='stored' (the practice note of sec. 8.4.2), alpha+beta+gamma = 0 identically: the heterobase triangle B -> i -> f -> B closes
negative_symmetry: True
fb_mode_exact_gamma_zero: True
C1_note: under the FORMAL definition (B_fb = exact re-encode of f) gamma is identically ZERO -- every IEEE double is a dyadic rational with a finite binary expansion; the monograph's own example magnitude requires the 'stored B' reading, which is the default here
```

---

## V3 tau cycle

```
verdict: EST-CONFIRMED
cycle_coefficient:
  - -3245185536584266727399604921303/11692013098647223345629478661730264157247460343808
  - -2.78e-19 (monograph: order 1e-19)
cycle_sign_contraction: True
sign_meaning: alpha beta gamma < 0: net contraction parity around the cycle (sec. 8.4.4)
any_exact_edge_kills_cycle: True
cycle_nilpotent: True
accumulates_cannot_compound: (e1^e2^e3)^2 = 0 structurally -- the wedge of the top with itself vanishes
```

---

## V4 invariant points

```
verdict: CORRECTED (C7: the sec. 8.4.17 candidate list)
traceless_by_value:
  0: True
  1: True
  5: True
  -7: True
  9007199254740992: True
  3/2: False
  1/2: False
  9007199254740993: False
  9007199254740994: True
exact_characterization: traceless  <=>  v is an integer exactly representable in double precision (float(int(v)) == v): all |k| <= 2^53, even steps up to 2^54, ...
characterization_holds: True
C7_witness: 3/2 and 1/2 ('powers of two, exactly representable floats' per sec. 8.4.17) are NOT invariant points: beta = i - f = -1/2 != 0 -- the integer sheet cannot hold fractions, as the monograph's own sec. 8.4.1 opening states
nihilum: True
```

---

## V5 conversions

```
verdict: EST-CONFIRMED
int2float_rounding_witness:
  - True
  - the e2 record for i = 2^53+1 is exactly -1 (the double rounds); the LEDGER cancels the construction's +1 linearly, the STATE stays incoherent by exactly 1 -- both exact
float2bin_residue:
  - False
  - ledger: initial +1/2^55 (construction) cancels the conversion's -1/2^55 linearly -- the LEDGER vs STATE distinction
float2bin_record_zero_at_p55:
  - True
  - at p = 55 the re-encode of the double is exact, so the conversion records 0; the ledger keeps only the construction's +1/2^55
bin2int_extracts_integer:
  - True
  - i' = trunc(canonical(B)) = 2 for v = 7/3; recorded (i'-i) = 0 since i was already 2 -- the fractional residue stays on the state, alpha = 1/3
post_int2float_float_of_int: True
ledger_vs_state: tau is a path-dependent LEDGER of conversion events; fresh_discrepancies() is a path-independent STATE function; a conversion record can cancel initial trace linearly without annihilation (witness above) -- the monograph's two uses of 'trace' are distinguished here
```

---

## V6 annihilation ladder

```
verdict: BY-TRIAL (+ corrections C3, C4)
response_matrix_[1,1]_per_level:
  R0([1,1]):
    trace_e: 2
    ghost: 0
  R1([1,1]):
    trace_e: 0
    ghost: 2
  R2([1,1]):
    trace_e: 1
    ghost: 1
  R3([1,1]):
    trace_e: 0
    ghost: 2
  R4([1,1]):
    trace_e: 0
    ghost: 2
  R5([1,1]):
    trace_e: 0
    ghost: 2
R1_pair:
  pair: True
  transfer_2alpha: True
  C3: sec. 8.4.3 Level 1 prints ghost += |alpha| (loses |alpha|); sec. 8.4.3a Level 1's 2|alpha| conserves total magnitude -- implemented, tested
R2_saturation:
  saturation: True
R3_reset_loss:
  reset_loss: False
R4_chiral:
  same_sign_cancels: True
  opposite_adds:
    - True
    - linear: +1 + (-1) = 0 with NO ghost transfer -- the crossing pair is invisible to the ghost under R4
R5_threshold_k3:
  threshold_k3: True
T0_never_fires: True
T1_exact_only: True
T2_within_eps: True
T3_any_repeat: True
T4_count_k3: True
T5_first_conversion_fires:
  - True
  - the extreme bosonic limit of sec. 8.4.3 Level 5: every conversion immediately to the ghost disc
spent_flag_after_pair:
  - True
  - third identical conversion has no effect (sec. 8.4.3 Level 1)
C4: response-level embedded preconditions clarified: R1 cancels only true pairs; R4's transfer generalized to |t| + |alpha|; R2 fills an empty cell before saturating -- see ladder.py docstring
```

---

## V7 arithmetic

```
verdict: EST-CONFIRMED (+ correction C2)
monograph_2_plus_3:
  - True
  - sec. 8.4.8: '(B, 5, 5.0, 0) with no trace'
xor_parity_sheet:
  - True
  - 2 xor 3 = 1: the carry 4 is discarded and RECORDED on e1 (alpha = 1 - 5 = -4) -- 'discards magnitude and retains only parity'
ieee_rounding_feeds_tau:
  - True
  - 0.1 + 0.2 = 0.30000000000000004; the rounding is recorded on the trace
mod_wraps:
  - True
  - (2^64 - 1) + 2 mod 2^64 = 1: cyclic tally
C2_signs_witness:
  - True
  - the xor case: recorded fresh alpha = canonical(B) - i = 1 - 5 = -4, while sec. 8.4.8's printed Delta_bi = i - canonical(B) = +4 -- the signs are flipped; the consistent sec. 8.4.2 conventions are implemented (either telescopes)
```

---

## V8 spin tallies

```
verdict: EST-CONFIRMED
angle_bridge_example:
  - True
  - sec. 8.4.10: (0,300)+(0,100) = (1,40)
negative_angle_remark:
  - True
  - theta = -1: floor(-1/360) = -1, r = 359 -- the convention remark
invariant_500_random: True
three_tally_types_one_angle:
  natural:
    - 0
    - 700/3
  integer:
    - 1
    - -380/3
  float:
    - 0
    - 700/3
shifts:
  - 0
  - 1
  - 0
shift_note: the re-encoding shifts between tally types are the spin-domain translation costs (sec. 8.4.11: the tally type defines the representation)
```

---

## V9 double cover

```
verdict: EST-CONFIRMED (+ corrections C5, C6)
360_flips_once: True
720_returns_original_sheet:
  - True
  - the coherent spinor regime (sec. 8.4.18 Level 1): two identical crossings pair-annihilate, ghost = 2, pure state
single_720_jump:
  - True
  - C5: sigma flips PER BOUNDARY (net parity), so one 720-degree jump also returns to +1; sec. 8.4.12's printed rule (flip once when floors differ) would give -1 here and contradict sec. 8.4.18
berry_phase_regime:
  - True
  - sec. 8.4.18 Level 4: +360 then -360 leaves trace e1 - e2 != 0 -- the system remembers the path, not the endpoint
four_half_turns: True
bosonic_plain_tally:
  - True
  - the plain tally returns to the origin mod 360 with the winding recorded in t ('a wound spring')
C6: sec. 8.4.18 Level 3's 'after 360, sigma returns to +1' does not follow from the algebraic flip rule (sigma = -1 after one crossing under every regime); the bosonic return is the PLAIN tally's mod-360 identity; the ladder levels change trace/ghost bookkeeping, not the flip rule
```

---

## V10 gates and status

```
verdict: EST-CONFIRMED (gates) / OPEN (status)
projections_lose_trace: True
projection_note: 0/a returns exactly the sheet; tau and the ghost disc are invisible to every single-base observer (sec. 8.4.6)
ghost_monotone_500: True
all_8_activation_patterns_reachable: True
patterns_embed_note: the 2^3 = 8 patterns of sec. 8.4.7 are the basis monomials of Lambda(V); the 117-point lattice embedding is asserted by the monograph, not implemented here
OPEN_tau_cycle_bifurcation: sec. 8.4.5: 'Its growth under iteration would force a bifurcation - a topic for further research' -- not decidable here
OPEN_ladder_UCQ_UCO_UCS: sec. 8.4.16's two-sheet ladder UC -> UCQ -> UCO -> UCS: the UCQ rung is implemented and verified in the companion nilpotent-crypto project; UCO/UCS are not implemented
```
