# Case 1 — The Toy, Solved (and re-solvable by you)

**Variant:** `study-toy` · **Model:** the small model (2×2 over F₂₅₇,
8 one-bit digits, L = 10, wells at the primes 2, 3, 5, 7) ·
**Claim:** security = min(16, 256) = 2¹⁶ — **breakable by design.**

```
H    = 2bb7236985d8d8394c568c2a55d711817c26fc07455805e3452b592ea47f8266
seed = 104f        (the key, 2 bytes -- published here)
```

This is the entire Voidwell-3 construction in miniature: the same
code path as the flagship, the same prime skeleton, the same four
perspective wells, the same zeta-array and ghost-disc assembly —
only the field is F₂₅₇ and the state is a byte. It exists so that
every claim of the construction can be *seen*, not believed.

## Step 1 — Verify the published key

```
python3 -m voidwell3 gate study/case_1_toy_solved/challenge.json \
                        study/case_1_toy_solved/KEY.json
```

Expected output: `PASS`. The gate checked the schema, the challenge
surface (H and public parameters only), the public mathematics (the
four perspective laws, the loop closure, the quaternion table),
then replayed the whole walk from the seed and compared H in
constant time.

## Step 2 — Forget the key. Break it yourself.

The key space is 2¹⁶ = 65,536 seeds. The shipped attacker walks it
in order, at full replay cost per candidate — no shortcuts, because
the challenge publishes nothing per-well to filter against:

```
python3 -m voidwell3.attacker.seed_search \
        study/case_1_toy_solved/challenge.json --exhaustive
```

Live run (issuer's machine, this distribution):

```
seed search against study/case_1_toy_solved/challenge.json
  model: toy (F_257); target H: 2bb7236985d839...
  exhaustive: all 65,536 seeds in order (2-byte)
  HIT after 4,176 replays: seed = 104f
  trials: 4,176, hits: 1
  rate: 1042.5 full replays/s
  expected work: 2^15 replays = 9.96e-07 years at this rate
  (the claim is min(16, 256): the key space is small enough to exhaust -- the study case's lesson)
  the gate will now PASS this seed -- write it to a key file and try it
```

The search hit after 4,176 replays because the seed happens to sit
at 0x104f = 4,175; the *expected* position is the midpoint, 2¹⁵ ≈
32,768 replays (~30 seconds at this rate). Every candidate costs a
complete 10-step walk — that is the point: the construction offers
no early abort, no partial check, nothing to precompute against.

## Step 3 — Confirm the find with the gate

Write the found seed into your own key file:

```
echo '{"version": 3, "variant": "study-toy", "seed": "104f"}' > my_key.json
python3 -m voidwell3 gate study/case_1_toy_solved/challenge.json my_key.json
```

Expected: `PASS`. You now hold the key exactly as the issuer does.

## Why this case is solvable (and case 3 is not)

The construction's security accounting is one line:
**security = min(seed bits, 256)**. The key space IS the seed space;
nothing in the layers above adds bits, and nothing is claimed to.
With a 2-byte seed, 65,536 replays recover the key with certainty.
With a 16-byte seed (case 2), the same search costs 2¹²⁷ replays.
With a 32-byte seed (case 3), 2²⁵⁵. The construction does not
change between the three — only the seed width does. That is the
lesson of this case, stated by the artifact itself.

## Study extensions

* `python3 -m voidwell3 toy` — the exhaustive small-model battery:
  the collapse-to-saturation scan (k = 0, 1, 4), the final-state
  uniformity (χ² test), and the nullifier dictionary (250,562
  entries; why the surface is H-only). About 95 seconds.
* `python3 -m voidwell3.attacker.toy_dictionary` — the dictionary
  attack demonstrated standalone: what a wider publication surface
  would concede instantly.
