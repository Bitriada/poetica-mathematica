# Voidwell-3 — The Perspective Walk

A hash-and-key construction in the Voidwell family. From a secret
seed, a 43-step walk through fare-octal states, punctuated by
**four wells — one per perspectival algebra** (UC1 point, UC2 line,
UC3 disc, UC4 field) — placed and directed by the first four
primes, committed by full-width nullifiers, accumulated in a
ghost-disc Merkle tree, and contracted through the sixteen-cell
zeta-array. Published as a single hash H. **The key is the seed
alone.**

```
the four perspectives (public constants, exact matrix laws):
    i1^2 = i1                 UC1, the Complex Point (idempotent)
    i2^2 = -i2                UC2, the Complex Line (the half-turn)
    i3^2 = -1 - i1^2 - i2^2   UC3, the Complex Disc (obfuscated:
                              present only through the closure)
    i4^2 = -1                 UC4, the Field (the proper unit)
    i1^2 + i2^2 + i3^2 + 1 = 0    the loop closure; the circuit's
                                  holonomy is tau^2 = 0

the prime skeleton (public, nothing-up-my-sleeve):
    wells at positions 2, 3, 5, 7 nullifying digits 2, 3, 5, 7

the involution exponent (public parameter):
    e = 1 - 2s; the well derivations scale their primes by n_j^e.
    At e = 0 (s = 1/2, the critical line of the Fare Algebra's
    spectral involution) every scaling is 1 — the fixed point.
```

## The claim (stated first, as always)

**security = min(seed bits, 256)** — flagship (32-byte seed) 2^256,
compact (16-byte seed) 2^128. The key space IS the seed space. The
sole assumption is SHA-256 preimage resistance. Expected attack
work: 2^(seed_bits-1) full replays. No layer of this construction
inflates that number, and no layer is claimed to.

What the layers add is everything else: verifiable per-well
binding, an enforced publication surface, a duplicate-proof ledger,
log-size state proofs, and a challenge whose public mathematics the
gate audits before it even looks at a key.

## What is new in V3 (everything measured, battery-verified)

| # | Feature | Module | The measured fact |
|---|---------|--------|-------------------|
| D1 | **The Perspective Walk** — four wells, four kinds of complex direction, the loop closure exact over F_p | `perspectives.py` | all four laws + closure hold bit-exact (W1); each well carries a conjugation-invariant trace law tr(Q') = tr(Q) + tr(Q U_j^2), audited per well (W6) |
| D2 | **The Primes Spine** — wells placed and directed by the first four primes; the spectral involution exponent e = 1−2s public | `wells.py` | at e = 0 every prime scaling is 1 — the monograph's fixed point s = 1/2, visible as a parameter (W7) |
| D3 | **The zeta-array** — sixteen named cells (quaternion component × perspective), contracted into H | `zeta.py` | 16 cells, all recomputable, all distinct (W5) |
| D4 | **The disentangling meta-layer** — cells re-indexed by the quaternion multiplication table (component map + signs) before contraction | `zeta.py` | the table is exact against quaternion ground truth, all 16 products (W5) |
| D5 | **The ghost-disc accumulator** — a Merkle tree over every walk state; any state provable with a log-size path | `ghost.py` | 6-hash proofs verify; tamper detection works (W4) |
| D6 | **The engineering layer** — packed XOF matrix derivation (one SHAKE-256 call per candidate), adjugate inverses (one pow), cached inverses across the acceptance | `prf.py`, `ucq/matrix.py` | 4 wells at the cost of V2's 3: 7.5 ms/replay, 1.86 ms/well vs V2's 2.26 (W13) |
| D7 | **The bijection walk** — every base op is a permutation (Λ-carry, τ-rotate, ξ-write), so the walk cannot lose information | `encoder.py` | D_L entropy 26.98 of 27 bits (V2 measured 18.21); toy D_L exactly uniform, chi2 p = 0.96 (W3) |

Plus, kept from V2 on purpose: full-width nullifiers (2^4123
preimage domain per well, four wells), H-only publication enforced
by the gate, the τ² = 0 fare ledger (measured 65 = 65 on demo
paths), the same-code-path small model, and the shipped attacker.

## The small model (F_257, exhaustively enumerated)

The V2 toy used F_7, and the V3 investigation measured why that
understates the construction: conjugation orbits in F_7 collapse
(63–119 distinct conjugated matrices per well) and the V2 toy's
final state was literally one bit. The V3 toy runs **F_257** —
same code path, byte-sized state, the SAME prime skeleton — and
the measurements change qualitatively:

```
k=0: distinct H =    256 of 65536   (the collapse: without wells,
                                     H binds only the initial state)
k=1: distinct H =  65339 of 65536   (ONE well binds past the state
                                     space)
k=4: distinct H =  65536 of 65536   (perfect saturation: ZERO
                                     collisions; V2's F_7 toy had
                                     1,061 at the same scale)
D_L: 256/256 values, chi2 p = 0.961 (the bijection walk is uniform)
dictionary: 250,562 nullifier entries invert 4/4 published
            nullifiers instantly  (why the surface is H-only)
```

## Run it

```
python3 -m voidwell3 params     # the public constants + audits
python3 -m voidwell3 demo       # one encoding, the guided tour
python3 -m voidwell3 verify     # the W-battery (34 checks)
python3 -m voidwell3 toy        # the exhaustive small model (~95 s)
python3 -m voidwell3 seal DIR   # seal a challenge (+ key)
python3 -m voidwell3 gate CHALLENGE KEY
python3 -m voidwell3 attack CHALLENGE   # surface audit + seed search
```

The sealed flagship challenge lives in `contests/flagship/`
(H = 9c6e0b62dc5338a414a50552aba0f73f1a8c8f57bea7fe2534186b32fa89a258).
The gate verdict for the shipped key: **PASS**.

## The honest split (unchanged doctrine)

The toy demonstrates **method** — collapse, saturation, the
dictionary, the surface — at a scale where everything is visible.
The claim rests on **SHA-256** and the measured behavior of the
full artifact. The structure adds auditability, binding, and
accounting; it does not add bits, and it says so.

## Logged for a future version (conjecture hygiene)

The monograph's zeta-STRING layer (sixteen strands each carrying a
local 1/2 line, the null-transit reunification) and the T_tower
spectral construction (the ζ(s)·ζ(2s)·ζ(3s) vacuum expectation)
are marked conjectural in the monograph itself; V3 ships their
verified FORM (the array, the disentangling, the fixed point) and
leaves the conjectural machinery named but unclaimed. The deeper
Fare-Algebra walk (ι_s acting on a square-free state basis) and the
C_8 public-operator wells (with their binding tradeoff) are
designed for, not shipped in, this version.
