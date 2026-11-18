# Architecture — the construction, layer by layer

This document explains what the scheme (`scheme_voidwell3.png`)
depicts, top to bottom, and names the module where each piece
lives. Read it next to the image.

## The one-paragraph version

A secret seed expands, through a PRF, into an initial state and
four checkpoints. A 43-step walk carries a 27-bit state through a
fare-octal space; at four public positions — the first four primes
— the state is lifted into a 4×4 quaternionic matrix over a 256-bit
prime field, twisted by one of four "perspective" units, conjugated
by a PRF-derived matrix, and slammed back down into the state
space, with the conversion recorded as a full-width nullifier and
the walk restarting from a checkpoint. Every state along the way
becomes a leaf of a Merkle tree (the ghost disc). The four wells'
material fills a 4×4 array of named hashes (the zeta cells), which
the quaternion multiplication table then permutes and signs (the
disentangling). One final SHA-256 over the tree root, the sixteen
disentangled cells, the final state, and the public constants
produces **H** — the only thing published besides the public
parameters. The gate replays all of it from a candidate seed and
compares H; the attacker, seeing only H, must pay a full replay per
guess.

## Phase 1 — Public constants (everyone holds these)

| Constant | Value | Where |
|---|---|---|
| The prime skeleton | wells at positions 2, 3, 5, 7; digit targets 2, 3, 5, 7 | `voidwell3/wells.py` |
| The four perspective units | U₁ idempotent, U₂ anti-idempotent, U₃ closure-defined, U₄ a proper complex structure; 4×4 (full) and 2×2 (toy) | `voidwell3/perspectives.py` |
| The four laws + closure | i₁²=i₁, i₂²=−i₂, i₃²=−1−i₁²−i₂², i₄²=−1; i₁²+i₂²+i₃²+1=0 | verified at import; re-audited by the gate |
| The involution exponent | e = 1−2s, default 1; e = 0 is the critical s = ½ | `wells.py` (`prime_scaling`) |
| The field | p = 2²⁵⁶ − 2³² − 977 (full); 257 (toy) | `ucq/field.py` |

Nothing here is secret, and nothing needs to be: with H-only
publication, secret positions would buy zero bits (a lesson priced
in V2's design study).

## Phase 2 — The secret side (the seed is the only secret)

The seed (16 or 32 bytes) feeds a domain-separated PRF:
`D₀` (the initial state), the checkpoints `C₁..C₄` (one per well,
each domain including the involution scaling nⱼ^e mod p), and the
well-matrix stream. Candidate matrices come one SHAKE-256 call per
candidate (sixteen field entries packed from a single stream) and
are **rejection-sampled until the conjugation nullifies the target
digit** — expected 8 tries, geometric; the counter is issuer-side
effort and never published.

## Phase 3 — The walk (one code path for everyone)

Between wells, the state moves by three named **bijections** (V3's
fix for V2's measured information loss — see CHANGELOG):

* **Λ-carry** (Maiden Math): `state += 2^g mod 2^27`; the fare is
  the carry chain length. (`encoder.base_step`, op 0)
* **τ-rotate** (the multinumeral conversion): swap digits n, n′.
  (op 1)
* **ξ-write** (the obfuscation pair): digit n XOR= v. (op 2)

At position pⱼ (the j-th prime), the well fires:
`Q = lift(D)` → `TQ = Tⱼ(Q) = Q + UⱼQUⱼ` (the perspective twist) →
`Q′ = Mⱼ TQ Mⱼ⁻¹` → `D′ = project(Q′)` — and two audits hold:
**digit nⱼ of D′ is zero** (emergent, from the rejection loop; a
wrong matrix fails with probability 1 − 2⁻³) and **tr(Q′) =
tr(Q) + tr(Q Uⱼ²)** (the perspective's trace signature; a forgery
fails with probability 1 − 1/p). The nullifier
`Nⱼ = SHA(V3N ‖ ser(D′) ‖ ser(Q′))` commits the full conversion —
a 2⁴¹²³ preimage domain — and the walk restarts at checkpoint Cⱼ.

## Phase 4 — The assembly

* **The ghost disc** (`voidwell3/ghost.py`): all 44 states
  (D₀..D_L) become leaves of a canonical Merkle tree. The root
  enters H at full strength; any single state can be proven with a
  6-hash authentication path — V3's new partial-proof capability.
* **The zeta cells** (`voidwell3/zeta.py`): sixteen commitments,
  `cell(a, b) = SHA(component a ‖ well b ‖ N_b ‖ row a of Q′_b)` —
  a 4×4 array whose axes are the quaternionic directions and the
  perspectives.
* **The disentangling**: the quaternion multiplication table's
  component map μ and sign table re-index the cells
  (`disentangled[μ_b(a), b] = SHA(cell[a,b] ‖ sign(a,b))`). The map
  is a bijection, is nothing-up-my-sleeve (it IS the quaternion
  table), and is recomputed by the gate.
* **The contraction**:
  `H = SHA(V3H ‖ ghost_root ‖ disentangled ‖ ser(D_L) ‖ wells_digest ‖ e)`.

## Phase 5 — Publication and verification

The challenge JSON carries six fields — `version, params, H, data,
data_commitment, nullifier_count` — and the gate is the teeth:
anything per-well published is `MALFORMED`. With a key, the gate
runs the public-math audits (the perspective laws, the closure,
the quaternion table), replays the walk through the identical
`run_path`, recomputes the tree, the cells and the disentangling,
and compares H in constant time: `PASS` / `FAIL` / `MALFORMED`.

The attacker's view is the same H and the same constants. Every
candidate seed costs one full replay (~130/s on the issuer's
machine for the full model); there is no early abort and nothing to
precompute against. Expected work: 2^(seed_bits−1).

## The two models

| | Full | Toy |
|---|---|---|
| Field | p = 2²⁵⁶−2³²−977 | F₂₅₇ |
| Matrix algebra | 4×4 | 2×2 |
| State | 9 octal digits (27 bits) | 8 one-bit digits (a byte) |
| Walk | L = 43 | L = 10 |
| Wells | positions 2,3,5,7 / digits 2,3,5,7 | **the same** |
| Seed | 16 or 32 bytes | 2 bytes (study-toy) |

The toy exists so the accounting can be *exhaustively checked*:
`python3 -m voidwell3 toy` enumerates all 65,536 seeds and shows
the collapse without wells, the saturation with them, the uniform
final state, and the dictionary lesson. It is the same `run_path`
— no simplified model code anywhere.

## Module map

```
ucq/field.py        the prime fields (full + toy)
ucq/matrix.py       FpMatrix: @, inverse, adjugate_inverse, serialize
ucq/lift.py         state <-> matrix (the heterobase conversion) + profiles
ucq/conjugate.py    Q' = M Q M^-1 with cached inverses
ucq/ucpoly.py       UC-polynomials: the fare ledger, tau^2 = 0
voidwell3/perspectives.py   the four units, laws, closure, twists, trace law
voidwell3/wells.py          the prime skeleton + the exponent e
voidwell3/prf.py            the XOF stream + rejection loop
voidwell3/ghost.py          the Merkle accumulator (open/verify/tamper)
voidwell3/zeta.py           the 16 cells + the quaternion disentangling
voidwell3/encoder.py        run_path: the walk, the wells, the assembly
voidwell3/gate.py           the audits, the surface, the replay, PASS/FAIL
voidwell3/__main__.py       the CLI (params/encode/seal/gate/demo/toy/attack/verify)
voidwell3/attacker/         seed_search (+ --exhaustive), surface_audit, toy_dictionary
voidwell3/small_model/      the exhaustive harness
tests/verify.py             the 34-check battery
```
