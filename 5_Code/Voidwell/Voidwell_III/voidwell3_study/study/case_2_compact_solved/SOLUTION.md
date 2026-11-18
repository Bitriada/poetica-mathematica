# Case 2 — Compact, Solved (a real challenge, key published for study)

**Variant:** `compact` · **Model:** full (4×4 over the 256-bit prime,
9 octal digits, L = 43, wells at the primes 2, 3, 5, 7) ·
**Claim:** security = min(128, 256) = 2¹²⁸.

```
H    = b703646ebdde0955782fbd31a01d16b62357f711df85ad58ca5e47b2c16e94cd
seed = 4f062253c2e10034a651ba793244c10f   (the key, 16 bytes -- published here)
```

This is a full-strength Voidwell-3 challenge — the same 43-step
perspective walk as the flagship, the same ghost-disc accumulator
and zeta-array assembly — at the compact seed width of 128 bits.
The key is published so you can study the interior: replay it,
audit it, take it apart.

## Step 1 — Verify the published key

```
python3 -m voidwell3 gate study/case_2_compact_solved/challenge.json \
                        study/case_2_compact_solved/KEY.json
```

Expected: `PASS`.

## Step 2 — Look inside the encoding

```
python3 -m voidwell3 encode 4f062253c2e10034a651ba793244c10f
```

This replays the same walk in verbose form: the initial and final
digivectors, each well's rejection counter, the conjugated states
D′ⱼ, the four full-width nullifiers, the ghost root, the 16 zeta
cells, and the fare ledger balance. Everything the gate recomputes
is visible here — the encoder, the gate, the small model and the
attacker all run the same `run_path` code path.

## Step 3 — Price the attack honestly

```
python3 -m voidwell3.attacker.seed_search \
        study/case_2_compact_solved/challenge.json --trials=2048
```

Live run (issuer's machine, this distribution):

```
seed search against study/case_2_compact_solved/challenge.json
  random: 2,048 seeds against the published H
  trials: 2,048, hits: 0
  coverage: 2^11 of 2^128 (a 2^-117 fraction)
  rate: ~130 full replays/s
  expected work: 2^127 replays = ~1.35e+31 years at this rate
  (the claim is min(128, 256); the search does not warm up)
```

The same tool that cracked case 1 in four seconds cannot make a
dent here, and — this is the point — for the same *reason*: the key
space is the seed space, and this seed is 128 bits wide. There is
no structural weakness to find, because the structure adds no bits
and claims none: the wells, the perspectives, the zeta-array and
the ghost disc are binding and audit machinery, priced as such.

## Step 4 — Audit the publication surface

```
python3 -m voidwell3.attacker.surface_audit \
        study/case_2_compact_solved/challenge.json
```

Expected: `SURFACE: PASS (H and public parameters only)`. The
challenge publishes six fields; everything per-well (nullifiers,
the ghost root, the zeta cells, the schedule digest) is checked
*absent* — publishing any of them would hand the attacker a filter
or a dictionary target, and the gate rejects such challenges as
malformed. Try adding a `"nullifiers"` field to a copy of the
challenge and re-running the gate: `MALFORMED`.

## What "solved" means here

The key is public, so this case is not a puzzle — it is a specimen.
Use it to see what a passing key produces: run the gate, run the
verbose encode, flip one bit of the seed in a copy of `KEY.json`
and watch the gate print `FAIL: binding`. One bit, one completely
different walk, one different hash — the avalanche is measurable
(128 one-bit seed flips average 127.6 of 256 flipped hash bits in
the shipped battery).
