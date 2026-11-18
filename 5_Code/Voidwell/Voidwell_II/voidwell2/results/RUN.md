# RUN — the Voidwell-2 demonstration record

**Date:** 17 November 2026 (the build day)
**Command:** `make demo` (the full battery, in order)
**Environment:** this project's Linux sandbox, single core, Python 3.12.

## What ran, and what it proved

1. **encode + gate, both variants** — the published illustration
   seeds (`11`*32 flagship, `22`*16 compact) encode
   deterministically and gate PASS.  Cross-process determinism is
   check W1 of the battery.
2. **the two illustration cases** — `examples/case1-flagship`
   (data `00112233`) and `examples/case2-compact` (data
   `deadbeef`) re-encode bit-for-bit identical to the stored
   files and gate PASS; `make examples` asserts this with `cmp`.
3. **the sealed challenges** — `contests/flagship/challenge.json`
   (H = `30ec8b3b3164...`, the publishable offline challenge) and
   `contests/compact/challenge.json` (the 2^128 study challenge)
   both verify against their withheld demonstration keys
   (`results/*_withheld_key.json`, archived outside any shipped
   zip; the flagship disclosure copy is
   `voidwell2_challenge_KEY.json` next to the archives).  The
   challenges are stable artifacts — no make target re-seals
   them.
4. **the small model** — k=0 collapses (8 distinct H over 256
   seeds: with no wells, H commits only D_0's 3 bits and its
   public path); k >= 1 saturates at one seed per H (the
   full-width nullifier binds ~2^22 >> 2^8 in the toy).  The
   density quotient equals the seed space for the right reason:
   the key space IS the seed space.
5. **the attacker package** — surface audit PASS on both
   challenges; the toy dictionary (19,208 = 2^14.2 entries, 0.1 s)
   recovers 3/3 hypothetically published nullifiers in the toy,
   with the honest split printed (the full model's domain is
   2^4123, and against a real challenge nothing per-well is
   published to match); seed enumeration at 2,048 trials per
   challenge: 0 hits, ~170 full replays/s.
6. **measurements** — encode 178/s (flagship), 159/s (compact);
   wrong-seed full replays 179/s vs honest 178/s (**ratio 1.01:
   no early abort** — every seed trial costs a full replay).
   Attacks: compact 2^127 full replays = 3.02e+28 years,
   flagship 2^255 = 1.03e+67 years at the measured rate.
   Tick-key climb 61,113 ticks/s; the demo tick (2^31.55) would
   cost ~25,700 s of climbing.
7. **the tick-key demo** — tick 3,141,592,653 (pi's first ten
   digits): gate PASS, telescope exact, integer sheet on the
   staircase's top step (3, where it rests for all I >= 67).

## The verification battery

`tests/verify.py`: **33/33 PASS** — W1 determinism (same process
and cross-process), W2 variant discipline (lengths enforced,
independent H), W3 full-width commitments (517-byte matrix
serialization, 2^4123 nullifier domain, three 64-hex nullifiers),
W4 seed change flips every nullifier, W5 the public surface is
exactly the allowed fields with the pi-skeleton wells, W6 gate
PASS both variants end-to-end, W7 six rejections (wrong seed,
flipped H, variant mismatch, tampered data, leak fields, tampered
wells), W8 the fare-octal core and lift/project round trips, W9
the fare ledger with tau^2 = 0 linearity on a real encoding
(fare 31 == sum 31), W10 the tick-key laws (telescope exact at
sampled ticks, staircase transitions at I = 5, 9, 67, round trip,
wrong-tick rejection), W11 the small model runs the same
`run_path`, W12 the claims, W13 the two illustration cases
reproduce and gate.

## The honest summary

Security = min(seed bits, 256): flagship 2^256, compact 2^128.
The assumption is SHA-256 preimage resistance.  The best attack is
seed enumeration at full replay cost, and it is shipped
(`attacker/seed_search.py`).  The parked direction is specified in
`RESEARCH-V3.md`.  The design rationale is
`docs/voidwell2_design_study.pdf`; the change record relative to
Voidwell-1 is `CHANGELOG.md`.
