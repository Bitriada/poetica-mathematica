# Voidwell — Nilpotent Voidwell Cryptography, the demonstration case

A three-layer construction (spec: `hashkey.docx`, Part II):

```
LAYER 3  BINDING    SHA-256, iterated over the full digivector path
LAYER 2  WELLS      UC-Quaternion conjugation over F_p (non-commutative):
                    lift -> M Q M^-1 -> project -> nullifier -> restart
LAYER 1  BASE       Fare-Octal digivector transitions (commutative):
                    27 bits, nine 3-switch bases, union-or-annihilate
```

**Status (2026-11-16): cryptanalyzed.** The issued challenge was
independently broken down to its seed on the day of issue — the
original 2^279.1 security claim is withdrawn and replaced by the
corrected accounting below. The gate is airtight and the challenge
remains open; read `results/DEMONSTRATION.md` §8–§9 for the full
post-mortem, and `results/cryptanalysis_verification.json` for the
issuer's independent verification of every finding.

**Monograph utilization** (the three requested pieces):

* **UC-Q** (Ch. VI §6.2.8): the well layer's algebra — the 4×4 matrix
  form of §6.2.8b (rows = quaternionic direction, columns = UC
  component), the value/trace sheet split, non-commutative
  conjugation.  `ucq/`.
* **Multinumeral** (App. A): the digivector as a NINE-base object;
  `lift`/`project` as the heterobase conversion between the
  fare-octal and UCQ bases; the nullifier as the conversion's
  nilpotent record; the 9×9 commensurability structure with its free
  off-diagonal (36 trace components).  `ucq/multinumeral.py`.
* **UC-polynomials** (Ch. VIII §8.5): the path as composition — the
  convolution rule, the fare ledger `Fare(F) = Σ|β|`, and the τ² = 0
  linearity law (the fare never compounds), verified on real
  encodings.  `ucq/ucpoly.py`.

Read `results/DEMONSTRATION.md` for the full story with measurements.

## Layout (spec D1)

```
fareoctal/           the fare-octal package (vendored), extended with
                     digit_value / digit_zero / digit_set / digit_vector
ucq/                 field.py (F_p), matrix.py (n×n over F_p),
                     lift.py (digivector <-> UCQ), conjugate.py,
                     multinumeral.py, ucpoly.py
voidwell/            prf.py, schedule.py, encoder.py, gate.py,
                     __main__.py (CLI), small_model/harness.py (rev. 2)
tests/               verify.py (V8-V12 battery), test_gate.py (six cases),
                     measurements.py (incl. the attack surface)
contests/test3/      the sealed public challenge (no key inside)
results/             measurements, the small-model table, the withheld
                     demo key, the cryptanalysis verification,
                     DEMONSTRATION.md
Makefile             make demo / make verify
```

## Run the demonstration

```bash
make demo        # tests 1-3 (k=0,1,3), the small model, the params table
make verify      # the V8-V12 battery + the six gate cases
python3 tests/measurements.py   # incl. the measured attack surface (~3 min)
```

or by hand (spec D5/D6/D7):

```bash
python3 -m voidwell encode --data 00112233 --seed <hex> --wells 3 \
    --length 43 --out challenge.json --key-out key.json
python3 -m voidwell gate --challenge challenge.json --key key.json
python3 -m voidwell params
python3 -m voidwell.small_model.harness
```

## The three test cases (spec D9)

| test | k | seed (published) | key space (count) | purpose |
|---|---|---|---|---|
| 1 | 0 | `11…11` (S1) | 2^256 | the commutative layer alone |
| 2 | 1 | `22…22` (S2) | 2^264.6 | one well; schedule entropy enters |
| 3 | 3 | `33…33` (S3, withheld) | 2^279.1 | the demo contest case |

Test 3's key is withheld from `contests/test3/` (sealed) and archived
for this demonstration at `results/test3_withheld_key.json`. The
ISSUED challenge (`voidwell_challenge.zip`) is sealed with a fresh
CSPRNG seed that has never been published and did not fall to the
cryptanalysis.

## Security statement (corrected 2026-11-16)

The original statement — "attack cost equals the key space for every
k ≥ 1, slope 2.989 bits/well" — is **withdrawn**: the small-model
harness had measured the inverse density of keys per hash value, not
the work of any adversary. The corrected picture, every number of it
measured or verified:

* **What the layers contribute.** The schedule digest commits 2^23.1
  schedules — an exhaustive preimage falls in seconds (measured: 2.9
  s). Each nullifier commits a 2^27 state — a dictionary scan falls
  in about a minute (measured: 63 s single-core), and the recovered
  states are free early-abort filters (2^-24 each, uniformity
  verified). For a fixed message the base layer is a period-4 cycle
  of four fixed digit operations. The conjugation is, from the
  attacker's perspective, simply a hash. None of the exotic layers
  adds work beyond the seed.
* **The honest accounting.** A passing key must satisfy ~180 bits of
  hash-derived conditions on the seed (108 path-binding + 72
  nullifier-binding). Best known attack: **2^180** seed evaluations
  (structured). Blind brute force: **2^203.1** trials. Key-space
  count: 2^279.1 — a **99.1-bit overstatement** (76.0 bits of
  keys-vs-trials metric error + 23.1 bits of committed-but-enumerable
  schedule). At the measured early-abort replay rate, 2^180 ≈ 10^44
  years.
* **What survives.** The gate is logically airtight (verified
  line-by-line by the cryptanalyst, six tamper cases pass); the
  256-bit seed was drawn from the CSPRNG and survived an ~830,000
  candidate low-entropy hunt; the challenge is not practically
  solvable. The residual barrier is real, and it is exactly the
  seed's contribution — nothing else in the system survives contact
  with a laptop.
* **The transferable results.** The k = 0 → k ≥ 1 step (one
  non-commutative, hash-committed point closes endpoint
  decomposition) survives as a *filter*, not independent hardness:
  attack cost is |schedules| + |seed search|, not the product. The
  methodology lesson — measure the best attack, never the key
  density — is the portable cautionary tale; the small-model harness
  (rev. 2) now demonstrates both the artifact and the honest
  baseline (structured slope 1.31 bits/well, speedups 21×/125×/218×
  at k = 1/2/3).

## Two packages, two purposes

* **`voidwell_demo.zip`** — this tree. Everything is published,
  including the demo test-3 key (`results/test3_withheld_key.json`)
  and the issuer's verification of the cryptanalysis
  (`results/cryptanalysis_verification.json`), so a reviewer can
  verify the whole story end-to-end. Do NOT use it as an attack
  exercise: the demo documents disclose seed S3.
* **`voidwell_challenge.zip`** — the attacker package: the public
  subset only, sealed with the fresh CSPRNG seed (unbroken; the
  schedule and nullifier preimages of that challenge are now public
  and disclosed in its rules.md, which also carries the corrected
  claim). Its withheld key lives outside the package
  (`voidwell_challenge_KEY.json`).
