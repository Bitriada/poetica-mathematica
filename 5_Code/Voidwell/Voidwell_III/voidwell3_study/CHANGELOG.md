# Changelog — the Voidwell construction

All notable changes to the construction, newest first. Dates are
issue dates. Each entry says what shipped, what changed, and what
it cost — including the failure, because the failure is where the
project's doctrine comes from.

---

## 3.0.0 — 2026-11-17 — The Perspective Walk

The third generation: the walk is punctuated by **four wells, one
per perspectival algebra**, placed and directed by the first four
primes, and the final hash is assembled through a tensor of sixteen
named commitments. The verification battery grows from V2's W-series
to a 34-check suite; the small model is upgraded so it finally
demonstrates what it claims.

### Added
* **The Perspective Walk (D1).** Four public units over F_p
  realizing the monograph's UC1–UC4 (point, line, disc, field),
  each with an exact matrix law, plus the loop closure
  i₁²+i₂²+i₃²+1 = 0 — verified bit-exact at import and re-audited
  by the gate. Each well conjugates through its perspective twist
  Tⱼ(X) = X + Uⱼ X Uⱼ and carries a conjugation-invariant **trace
  law** tr(Q′) = tr(Q) + tr(Q Uⱼ²), audited per well. (`perspectives.py`)
* **The Primes Spine (D2).** Wells at positions 2, 3, 5, 7
  nullifying digits 2, 3, 5, 7 — the first four primes place AND
  direct. The spectral involution exponent **e = 1−2s** is a public
  parameter; at e = 0 (s = ½, the critical line) every prime
  scaling nⱼ^e is 1 — the fixed point, verifiable in the artifact. (`wells.py`)
* **The zeta-array assembly (D3).** Sixteen cells, axes
  (quaternion component × perspective), each a hash of real
  per-well material, contracted into H. (`zeta.py`)
* **The disentangling meta-layer (D4).** Cells re-indexed by the
  quaternion multiplication table itself (component map μ and sign
  table) before contraction; the table is checked against
  quaternion ground truth on all 16 products. (`zeta.py`)
* **The ghost-disc accumulator (D5).** A Merkle tree over every
  walk state; any intermediate state is provable with a
  logarithmic-size path (6 hashes at L = 43); tamper detection
  verified. Verification previously required a full replay. (`ghost.py`)
* **The study-toy challenge variant.** The small model as a
  sealable challenge (2-byte seed, 2¹⁶ by design), breakable with
  the shipped `--exhaustive` search in about a minute — the
  accounting made executable.
* **A 34-check battery** (`tests/verify.py`): laws, closure, round
  trips, bijectivity, entropy, ghost proofs, the quaternion table,
  the trace law with a negative control, the fixed point,
  nullifier widths, the ledger, output statistics, avalanche,
  variants, six gate scenarios, robust timing, determinism.

### Changed
* **The base walk is now a composition of bijections (D7).** V2's
  burning operations (union-or-annihilate, burn, write) were
  many-to-one: the walk *lost information*, and the final state
  carried 18.21 of 27 bits (V2's own measurement). V3 replaces them
  with three named permutations — the **Λ-carry** (Maiden Math:
  state += 2^g, fare = the carry chain), the **τ-rotate** (the
  multinumeral base conversion: swap digits), the **ξ-write** (the
  obfuscation pair: digit ^= v). Measured result: **26.98 of 27
  bits**, and the property is now a proof (a composition of
  bijections cannot lose information), not just a statistic.
* **The small model moved from F₇ to F₂₅₇** with an 8-bit state
  (eight one-bit digits). V2's F₇ toy had collapsing conjugation
  orbits (63–119 distinct conjugated matrices per well) and 1,061
  seed collisions across its 2¹⁴ probe; the F₂₅₇ toy saturates its
  2¹⁶ seed space **exactly, with zero collisions**, takes all 256
  final-state values (χ² p = 0.96), and runs the identical prime
  skeleton as the flagship.
* **The PRF packs matrix candidates from a single SHAKE-256
  stream** (one XOF call instead of sixteen hashes per candidate),
  uses **adjugate inverses** (one modular inversion instead of one
  per pivot), and **caches the accepted candidate's inverse**
  across the nullification test and the kept conjugation (D6).
  Measured: 1.89 ms per perspective well vs V2's 2.26 ms per well —
  each V3 well does strictly more (twist, trace law, four zeta
  cells) for less.

### Security
* **Unchanged, on purpose:** security = min(seed bits, 256); the
  key space IS the seed space; the sole assumption is SHA-256
  preimage resistance. The new layers add auditability and binding,
  not bits, and every document says so.
* Full-width nullifiers kept (2⁴¹²³ preimage domain per well; four
  wells). H-only publication kept, enforced by the gate.

---

## 2.0.0 — 2026-11-16 — The Honest Rebuild

The second generation, rebuilt from V1's post-mortem with the
security accounting corrected at the center of the design.

### Added
* **Full-width nullifiers:** Nⱼ = SHA256(ser(D′ⱼ) ‖ the whole
  conjugated matrix) — a 2⁴¹²³ preimage domain per well; a single
  well saturates a 256-bit seed.
* **H-only publication with gate enforcement:** the challenge
  carries H and public parameters, nothing per-well; the gate
  REJECTS over-publication as malformed. No dictionaries, no
  preimage targets, no early abort.
* **The pi-skeleton:** wells at pi's opening digits (positions 3,
  14, 15; digits 3, 1, 4) — public, fixed, nothing-up-my-sleeve.
* **Emergent nullification:** the PRF rejection-samples the well
  matrix until the conjugation nullifies the target digit, so the
  gate's structural audit is a non-vacuous check.
* **The shipped attacker package** (seed_search, surface_audit,
  toy_dictionary) — the designer ships the attack.
* **The same-code-path small model** (F₇, 3-bit state) and the
  W-battery; variants flagship/compact.

### Changed
* The security claim restated from the withdrawn 2²⁷⁹·¹ to
  **min(seed bits, 256)**, with the layers priced as integrity and
  narrative, audited as such.

---

## 1.0.0 — 2026-11-16 — The Original Voidwell

The demonstration case: a three-layer construction (fare-octal
base, UC-Quaternion wells over F_p, SHA-256 binding), a 27-bit
digivector of nine octal digits, a secret well schedule, and an
issued challenge with a gate.

### The event that shaped everything after it
**Cryptanalyzed on the day of issue.** The challenge was
independently broken down to its seed; the original 2²⁷⁹·¹ security
claim was **withdrawn** and replaced by the corrected accounting
(the claim V2 and V3 still carry). The gate itself was airtight
throughout — the break was against the claim, not the artifact.

The post-mortem became the project's doctrine, verbatim from the
results file: publish the honest number, ship the attacker, make
the toy exhaustively enumerable, and let the structure carry
binding and auditability — never unpriced "bits". Every version
since is that doctrine, executed.

---

## Versioning policy

Semver-shaped, but the major number counts **constructions**, not
API breaks: each major is a new walk architecture with its own
challenge format (`version` field in the JSON: 1, 2, 3). A gate
from one major does not accept another major's challenges.
