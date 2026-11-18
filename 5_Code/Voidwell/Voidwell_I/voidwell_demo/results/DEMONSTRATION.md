# The Voidwell Demonstration — What Was Built, Measured, Broken, and What Survives

**Generated:** 2026-11-16 (revision 2 — post-cryptanalysis)
**Source specification:** `hashkey.docx` ("Nilpotent Voidwell Cryptography", Parts I–IV and task D1–D13)
**Monograph utilization:** UC-Q (Ch. VI §6.2.8), the Multinumeral (App. A), UC-polynomials (Ch. VIII §8.5)
**Independent cryptanalysis:** `voidwell_test3_cryptanalysis.docx` (2026-11-16, unrestricted) — verified by the issuer; see §7 and `results/cryptanalysis_verification.json`

---

## 1. The demonstration case, in one paragraph

A key holder encodes a message into a **segmented path** of 27-bit
digivectors: a commutative fare-octal base layer generates the path
from the message, and at `k` secret positions (**voidwells**) the
current digivector is lifted into its 4×4 UC-Quaternion matrix form,
conjugated by a seed-derived matrix that *provably nullifies one of
the nine digits* (rejection-sampled at derivation), committed by a
SHA-256 nullifier, and the path restarts from a secret checkpoint.
The public hash `H` commits the entire path, all nullifiers, the
endpoint, and the schedule digest. The gate replays everything from
the key and accepts in constant time. The demonstration shipped three
runnable cases (k = 0, 1, 3), a sealed public contest, and an
exhaustive small-model measurement. **On the day of issue, an
independent cryptanalysis recovered the schedule in 4.4 seconds and
all three nullifier preimages in about a minute, and refuted the
2^279.1 security claim down to an effective 2^180 — a 99.1-bit
overstatement — while the seed itself did not fall.** Every finding
of that analysis was re-executed and confirmed by the issuer (§7).
This document is the honest account: what was claimed, what broke,
what the error was, and what survives.

## 2. Acceptance criteria (spec D11), item by item

| # | Criterion | Status |
|---|---|---|
| 1 | `V8` digit operations exact over 10⁵ states | **PASS** (V8a; 0 failures) + V8b: the encoder's int fast path ≡ the `FareOctal` class over 10⁵ states |
| 2 | `V9` `project(lift(D)) == D` | **PASS** (all 8 small-model states; 10⁵ full-model samples; packing table honored) |
| 3 | `V10` nullification | **PASS** (1000 random conjugations read back exactly; identity conjugation is identity; 200/200 well-order swaps differ; PRF matrices nullify 20/20) |
| 4 | `test_gate.py` six cases | **ALL PASS** (valid → 0; perturbed seed/schedule/H/nullifier → 1; truncated key → 2) — and confirmed airtight by the cryptanalyst's line-by-line read |
| 5 | small-model harness, four rows + slope + r² | **RUNS (rev. 2)** — density artifact 2.989 bits/well (r² = 0.9940, an artifact of counting); **structured attack 1.312 bits/well** (r² = 0.9588), speedups 21× / 125× / 218× (§3) |
| 6 | key-space table matches `2^256·C(43,k)·9^k` | **EXACT as a count of keys** — and now correctly labeled: it is not a security level (§5, §7) |
| 7 | `contests/test3/` self-contained | **YES** (challenge.json, rules.md with the corrected claim and full disclosure, verify.sh, submission_template.json; no key inside; verify.sh passes against the archived withheld key) |
| 8 | `params` prints the table | **YES** (matches rules.md) |
| 9 | seeds published | S1 = `11…11`, S2 = `22…22` (baselines); the demo case S3 = `33…33` archived at `results/test3_withheld_key.json`; the ISSUED challenge (`voidwell_challenge.zip`) uses a fresh CSPRNG seed, never published, not recovered by the cryptanalysis |
| 10 | one command reproduces all three tests | **`make demo`** |

## 3. The small-model measurement, revised (the artifact, and the honest baseline)

Exhaustive enumeration over the complete key space — F₇, 2×2
matrices, 3-bit digivector (3 one-bit digits), L = 8, all 256 seeds ×
all schedules, the same `run_path` code as the full model. Revision 2
adds the structured attack (schedule preimage → nullifier dictionary
→ seed replay, worst-case work counting) and relabels the original
"attack cost" as what it always was — the inverse density of keys per
hash value:

| k | key space | distinct H | keys/H (mean / max) | density (artifact) | **structured attack** | speedup |
|---|---|---|---|---|---|---|
| 0 | 256 | 8 | 32.00 / 41 | 2^2.83 | 257 | 1.0× |
| 1 | 6,144 | 2,777 | 2.21 / 11 | 2^12.58 | **288** | **21.3×** |
| 2 | 64,512 | 60,367 | 1.07 / 4 | 2^15.98 | **516** | **125.0×** |
| 3 | 387,072 | 384,688 | 1.01 / 2 | 2^18.56 | **1,776** | **217.9×** |

**Slopes (k ≥ 1):** density 2.989 bits/well (r² = 0.9940) — identical
to the key-space slope *by construction*, because at k ≥ 1 the
binding constraints far exceed log₂|K| and every reference H is hit
by exactly one key; the quotient measured counting, not adversaries.
The structured attack — the honest baseline — scales at **1.312
bits/well** (r² = 0.9588).

**Reading (corrected).** The original conclusion — "the first
voidwell closes the decomposition; from k = 1 on, attack cost equals
the key space exactly" — is **refuted inside the harness's own
model**: the structured attack solves the harness's own reference
challenges at 21×–218× below the claimed cost, with work
|schedules| + |states| + |seeds| (a **sum**: 24+8+256 = 288 at k =
1; 252+8+256 = 516 at k = 2; 1,512+8+256 = 1,776 at k = 3) where the
claim priced |schedules| × |seeds|. The k = 0 row keeps its meaning:
with no wells the construction is endpoint-decomposable (8 distinct
hashes, 36 keys share the reference H, blind cost 2^2.83 against a
space of 2^8) — and the k = 0 → k ≥ 1 transition is real but is a
*filter*, not independent hardness (§8). The gap between the two
slopes would widen with k and saturate near the seed-space size: the
attack pays |schedules| + |seeds|, the claim multiplied them.

## 4. The three monograph pieces, operational

*(Unchanged by the cryptanalysis — these pieces were verified
operationally and the attack does not touch them; what changed is
their security reading, see §7–§8.)*

### 4.1 UC-Q (Ch. VI §6.2.8) — the well layer's algebra

The well conjugates the digivector's UC-Quaternion matrix form
(§6.2.8b: rows = quaternionic direction 1, i, j, k; columns = UC
component — value real, value imag, trace real, trace imag). The lift
places the 27 switches in the 16 cells by a documented, versioned
packing table; the value sheet carries bits 0–15, the trace sheet
bits 16–26. `lift`/`project` round-trip exactly (V9). Conjugation
`M Q M⁻¹` mixes all 16 degrees of freedom non-commutatively — verified
order-sensitive (V10c: 200/200 A-then-B ≠ B-then-A), which is the
property that chains the wells: reordering the schedule changes every
subsequent nullifier.

**The nullification is emergent, not applied** (resolution R2): the
PRF rejection-samples each well matrix until the conjugated,
projected digivector *already* has the target digit zero (measured
rejection counter: mean 7.9 tries against the theoretical 8 for the
3-bit condition). The gate's structural audit (`digit_value(n) == 0`)
is therefore a real filter rather than a tautology. **The
cryptanalysis added the attacker's half of this picture:** the
conjugated state D′ is uniform over its 2^24 reachable values
(χ² = 241 on 255 df, issuer's measurement; 265 by the analyst — both
well below the 293.2 critical value), so each nullifier is exactly a
2^-24 filter — which is precisely what makes it a free early-abort
oracle for the attacker rather than a work factor for the defender.

### 4.2 The Multinumeral (App. A) — the digivector's structure

The digivector is read as a **nine-base** object: each octal digit is
a representational base owning three switches with prime labels
(p₃ₙ, p₃ₙ₊₁, p₃ₙ₊₂ from 2, 3, 5, …, 103) and one H-tensor row. The
module `ucq/multinumeral.py` computes the App. A structure exactly:

* **Trace dimension 36** = 9·8/2 — the monograph's "strongest formal
  result of the architecture", now a computed constant of the
  construction.
* **The off-diagonal is free; annihilation is intra-base** (V12b,
  10³ pairs): digits of two states in *different* bases always merge;
  a merge annihilates exactly when the *same* base has the same
  switch active in both.
* **The well is a heterobase conversion** (App. A.2.2): the lift is
  the conversion, the nullifier is the nilpotent record the
  conversion generates. The base layer never enters the Nihilum
  (App. A.3.1's apex): an annihilating union falls back to a slot
  write — the fare is paid, the state survives (resolution R3).

Measured on the test paths: 6 intra-base annihilations per 43-step
path, each an exact diagonal-conflict event in the 9×9 structure.

### 4.3 UC-polynomials (Ch. VIII §8.5) — the path as composition

Every encoding carries a **fare ledger**: each step's coefficient is
(the digivector's display value) + τ·(the fare the step paid). The
two monograph laws are verified on real encodings: **L1** (τ² = 0
linearity: Fare(path) = Σ per-step fares, exactly, for k = 0, 1, 3)
and **L2** (the cross-convolution formula on 500 random polynomial
pairs). The wells pay the *weight of the digit they nullify* — the
τ² = 0 signature: the burned digit's value cannot compound, it can
only be paid once.

## 5. Key-space arithmetic — a count of keys, not a security level

The arithmetic below is exact (and corrects the spec's own rounding
slips); what the cryptanalysis refuted is reading it as a security
level:

| k | C(43,k)·9^k | log₂ (schedule factor) | key count |
|---|---|---|---|
| 0 | 1 | 0 | 2^256 |
| 1 | 387 | 8.59 | 2^264.60 |
| 2 | 73,143 | 16.16 | 2^272.16 |
| 3 | 8,996,589 | 23.10 | 2^279.10 |
| 6 | 3.24×10¹² | 41.57 | 2^297.57 |

**The corrected attack-cost table (k = 3), all values log₂ and all
stages measured or verified (§7):**

| Quantity | log₂ | Basis |
|---|---|---|
| Schedule space C(43,3)×9³ (**recovered**) | 23.10 | digest preimage, seconds (measured: 2.9–4.4 s), unique |
| Nullifier preimage space per well (**recovered**) | 27.00 | one dictionary scan, ~1 min (measured: 63–66 s) |
| Path constraints on the seed (H binding) | 108.00 | 4 × 27 bits: D₀, C₁, C₂, C₃ |
| Nullifier constraints on the seed | 72.00 | 3 wells × 24 bits (uniformity verified) |
| **Best structured attack** | **180.00** | 108 + 72 bits of conditions, early abort |
| Unstructured brute force over random keys | 203.10 | 1 / P(random key passes) |
| Claimed security (key count) | 279.10 | 2^256 × C(43,3) × 9³ |

The 99.1-bit overstatement decomposes into two identifiable errors:
**76.0 bits** of metric error (a key *count* is not a trial count —
brute force stops at the first success, so even a blind attacker
expected 2^203.1 trials, not 2^279.1) plus **23.1 bits** of
committed-but-enumerable schedule (the attacker preimages it in
seconds instead of guessing it). At the measured replay rates
(184–190 full evaluations/s, 548–555 early-abort evaluations/s on
this sandbox), 2^180 ≈ **8.8×10^43 years** — the challenge is not
practically solvable; its security theorem was simply off by 2^99.

## 6. Spec resolutions (engineering decisions, documented)

* **R1 — the well operator.** Realized as genuine 4×4 conjugation
  `M Q M⁻¹`, M ∈ GL(4, F_p) — the 16 *degrees of freedom* of the UCQ
  element are what get mixed; the realized entropy is the 256-bit
  seed.
* **R2 — emergent nullification.** Rejection sampling makes the
  structural audit non-vacuous (and, per §7, makes the nullifier
  filters exactly uniform — which cuts both ways).
* **R3 — the annihilation fallback.** An annihilating union writes a
  slot instead (fare 1): the path never enters the Nihilum, and the
  annihilation is recorded in the fare ledger.
* **R4 — the small model.** 3 one-bit digits, F₇, 2×2 lift, L = 8,
  256 seeds — exhaustive at every k through the same `run_path` as
  the full model.
* **R5 — published nullifiers.** The nullifier list is public so the
  gate's nullifier check is explicit and independently testable.
  *(Post-mortem: at a 27-bit state space this also made them
  dictionaries — see §7, Finding 2.)*
* **R6 (new) — security is a binding count, not a key count.**
  Report security as min(seed entropy, binding constraint count) —
  here 2^180 — and treat committed secrets from spaces below ~2^128
  as public. This resolution is incorporated into the revised
  `rules.md`, the revised harness, and `tests/measurements.py`.

## 7. The independent cryptanalysis — and the issuer's verification

**Subject:** `voidwell_challenge.zip` (test 3, k = 3), sealed with a
fresh CSPRNG seed on 2026-11-16. **Analyst's report:**
`voidwell_test3_cryptanalysis.docx`. **Issuer's verification:** every
finding re-executed against the withheld key; the full record is
`results/cryptanalysis_verification.json` (this tree) and
`scripts/verify_cryptanalysis.py` (issuer's sandbox).

| # | Finding (analyst) | Issuer's verification | Verdict |
|---|---|---|---|
| 1 | The schedule is the unique preimage of the published digest over 8,996,589 = 2^23.10 candidates; recovered in 4.4 s | reproduced: unique match in 2.9 s, identical to the withheld key: **[(28, 0), (32, 5), (42, 3)]** | **confirmed** |
| 2 | All three nullifier preimages — the secret post-conjugation states — fall to one 2^27 dictionary scan in ~1 min; each carries exactly the digit zeroed that its well nullifies | reproduced: 2^27 in 63 s single-core (2.1 M hashes/s); states 38,644,752 / 86,246,842 / 92,106,969 match the key derivation exactly; digits 0 / 5 / 3 zeroed | **confirmed** |
| 3 | For the fixed message the base layer degenerates to a period-4 cycle of four fixed digit operations; 15 of 27 bits are structurally untouchable | reproduced on 300 random seeds: period-4 description holds at every step; ops touch only digits {0, 4, 8} (the digit-6 annihilation fallback never fires); digits 1,2,3,5,7 — 15 bits — are never even targeted, and in practice 18 of 27 bits ride through every base segment untouched; D_L is exactly the last checkpoint C₃ with digit 8 zeroed | **confirmed** (with the refinement that digit 6 is untouched in practice too) |
| 4 | Effective security is ~2^180: 108 path-binding bits + 72 nullifier-binding bits; blind brute force 2^203.1; claimed 2^279.1 — a 99.1-bit overstatement | arithmetic exact; uniformity of D′ verified (χ² = 241.0 on 255 df, critical 293.2); measured replay 184–190 full/s, 548–555 early-abort/s → 8.8×10^43 years | **confirmed** |
| 5 | The small-model evidence is refuted in its own harness: the structured attack solves the reference challenges at k = 1, 2, 3 with worst-case work 288 / 516 / 1,776 against claimed 6,144 / 64,512 / 387,072 (21.3× / 125.0× / 217.9×), slope 1.31 vs the claimed 2.99 bits/well | reproduced exactly (harness rev. 2, §3): 288 / 516 / 1,776 ops, speedups 21.3× / 125.0× / 217.9×, slopes 1.312 vs 2.989 | **confirmed** |
| 6 | The seed did not fall: ~830,000 low-entropy candidates across nine classes (patterned bytes, hash-derived words, hex words, numerics, MT outputs including a 820,800-point timestamp sweep over the packaging window) all fail; consistent with a uniformly random 256-bit value | consistent with the issuer's provenance: the seed was drawn with `secrets.token_bytes(32)`; `prf_schedule(seed)` reproduces the sealed schedule; the seed has never been written to any public artifact | **confirmed — the seed is the entire construction** |

**What the analysis establishes about each layer** (the negative
result, now part of the record): the schedule is a 4-second preimage
— a committed secret drawn from a 23-bit space is a transparency, not
a work factor; the nullifiers are 27-bit dictionaries whose only
cryptographic role is to serve as free 2^-24 early-abort filters for
the attacker; the fare-octal base layer is, for a fixed message, a
fixed public period-4 digit shuffler whose algebraic dressing (prime
labels, H-tensor weights, Fare products, the ledger) plays no role in
the transition function; and the non-commutative conjugation is,
from the attacker's perspective, simply a hash. All secrecy lives in
the PRF outputs of the seed.

## 8. What survives, what does not

**Survives:**
* **The gate.** Logically airtight (line-by-line read by the analyst,
  six tamper cases, 13/13 algebra battery) — acceptance is exactly
  equality of recomputed SHA-256 values with published strings.
* **The seed's barrier.** 2^180 effective, ≈ 10^44 years at measured
  rates; the seed is CSPRNG-generated and survived the low-entropy
  hunt. The challenge is not practically solvable — it is simply 99
  bits weaker than advertised.
* **The k = 0 → k ≥ 1 step, as a filter.** One non-commutative,
  hash-committed point does close *endpoint* decomposition (k = 0 is
  solvable at 2^2.83; k ≥ 1 is not endpoint-decomposable). But the
  cryptanalysis shows the well does not convert this into independent
  hardness: attack cost is |schedules| + |seed search|, not the
  product. The pattern — commutative base + non-commutative
  segmentation + hash-committed coupling — remains a transferable
  design vocabulary, with the measured caveat that the coupling buys
  filtering, not multiplication.
* **The methodology lesson.** Measure the best attack (the structured
  attack is now the harness baseline), never the key density; publish
  the attack's slope (1.31 bits/well), not the key-space slope. This
  generalizes to any security argument built on a small model, and
  the harness now demonstrates both the artifact and its correction
  in one runnable file.

**Does not survive:** the 2^279.1 claim (withdrawn; corrected to
2^180 structured / 2^203.1 unstructured); the schedule and nullifier
preimages of the issued challenge (public; disclosed in `rules.md`);
the original small-model evidence (density ≠ attack cost); the notion
that the exotic layers add work beyond the seed.

**The open direction** (for the next construction): make the well
contribute *independent hardness* rather than filtering. The realized
well draws its matrix by rejection sampling until the nullification
emerges — which is exactly why the attacker can compute the nullifier
cheaply and use it as an early abort. If the well instead required
solving a hard problem — e.g. finding W ∈ GL(16, F_p) such that
Tr(W·Q·W⁻¹) lands in a target submanifold — the cost would become
|schedules| × well-hardness × seed search, a product again. That is
the design decision the cryptanalysis isolates, and the construction
that would make the well a work factor rather than a filter is the
genuine primitive this one stopped short of.

## 9. Reproduction

```bash
make verify     # V8-V12 battery (13/13) + the six gate cases
make demo       # tests 1-3, the sealed contest, the small model (rev. 2), params
python3 tests/measurements.py    # + the measured attack surface (~3 min)
```

The attack surface measured on this tree's own demo challenge
(key published at `results/test3_withheld_key.json`, so every stage
is checkable end-to-end): schedule preimage — 8,996,589 candidates,
one match in 3.12 s, equal to the published key; nullifier
dictionary — one 2^27 scan in 66.2 s, all three states recovered with
the correct digits zeroed; accounting as in §5. The issuer's
verification of the *issued* challenge's cryptanalysis is
`results/cryptanalysis_verification.json` (schedule preimage 2.9 s;
nullifier scan 63 s; structured attack 288/516/1,776; χ² = 241.0 on
255 df; rejection counter 7.9 vs 8 expected).
