# CHANGELOG

## Voidwell-2.0.0 (17 November 2026)

Voidwell-2 is the redesign of Voidwell-1 (the "nilpotent voidwell"
demonstration of 16 November 2026) after that construction was
cryptanalyzed on the day of issue.  This file is the complete
record of what changed and why; the package itself (README, code,
tests) is written to be studied without knowing any of this
history.  The full design rationale, including the five design
rules derived from the cryptanalysis, is
`docs/voidwell2_design_study.pdf`.

### What was broken in Voidwell-1 (context)

The issued challenge was broken down to its seed by an independent
cryptanalyst within the day, and the issuer re-executed and
verified every finding against the withheld key (the record lives
in the V1 archive as `results/cryptanalysis_verification.json`).
Three findings, all surface problems, not machinery problems:

1. **The schedule digest was a preimage target.**  The well
   schedule (k=3 positions among 43 steps plus digit choices) was
   a secret with a published SHA-256 commitment — a space of
   C(43,3) x 9^3 = 2^23.1, preimaged by exhaustive scan in
   2.9-4.4 s.
2. **The nullifiers were 27-bit commitments.**  Each well
   published `N = SHA256(ser(D'))` over a 27-bit state — one 2^27
   dictionary scan (63 s) recovered all of them.
3. **The published surface enabled early abort.**  With the
   nullifier list public, a seed search could abort a replay at
   the first well mismatch: 555 abort replays/s vs 184 full
   replays/s, a 3.0x advantage.

The 2^279.1 security claim (a key-space product: seeds x
schedules) was withdrawn; the corrected accounting was 2^180,
seed-bounded.

### What changed in Voidwell-2

**1. Full-width nullifiers.**  `N_j = SHA256(ser(D') || ser(M Q
M^-1))` — the nullifier commits the entire conjugated matrix, a
27 + 4096-bit preimage domain (2^4123), hash-capped at 256 bits
per well.  One well saturates a 256-bit seed; there are three.
This closes finding 2 at the root: there is no small domain to
dictionary.

**2. H-only publication, enforced by the gate.**  The challenge
publishes `H` and the public parameters.  No schedule digest
(there is no secret schedule at all — see 3), no nullifier list.
The gate rejects any challenge carrying per-well values as
malformed, so the surface cannot regress unnoticed.  This closes
findings 1 and 3: nothing to preimage, nothing to match, nothing
to abort against.  Measured: wrong-seed replays run at the honest
rate (ratio ~1.0; V1 gave the attacker the 3.0x abort advantage).

**3. Seed-only keys; the wells are public constants.**  The V1
key was (seed, schedule); the schedule multiplied the claimed key
space by 2^23.1 while adding zero search cost (it was the first
thing preimaged).  Voidwell-2's wells sit at the pi-skeleton —
positions 3, 14, 15, digits 3, 1, 4 (pi = 3.1415...) — public,
nothing-up-my-sleeve constants.  The key is the seed alone, and
the claim is min(seed bits, 256), never a product.

**4. Two variants instead of one.**  Flagship (32-byte seed,
2^256) and compact (16-byte seed, 2^128): the same construction,
the seed width is the only difference.  The compact variant exists
so the claim "security = seed bits" can be seen to move with the
seed, not with the narrative.

**5. The small model harness, revised.**  The V1 harness reported
"attack cost" as |K| / |keys hitting the reference H| — an inverse
density that trivially equaled the key space at k >= 1 (a counting
artifact, not adversary work).  The V2 harness enumerates the 2^8
seed space exhaustively (the k=0 collapse and k >= 1 saturation
are both visible), measures seed enumeration as the honest
baseline, and demonstrates the nullifier dictionary at the only
scale where it can exist (2^14.2 in the 2x2/F_7 toy) with the
honest split printed: the toy can never exhibit 256-bit preimage
hardness; the claim rests on SHA-256, stated.

**6. New: the tick-key toy** (`voidwell2/tickkey.py`).  The
family's floor piece — a key that is nothing but a pi-clock tick,
with exactly log2(tick) bits of security — added to keep the
family's security accounting legible.

**7. New: the attacker package** (`attacker/`, its own folder).
Every attack that exists, shipped by the designer: seed
enumeration (the best attack), the toy dictionary (methodology
demonstration), and the surface audit (the pre-shipment check —
the check that would have caught V1's 27-bit nullifier before it
shipped).

**8. New: the sealed offline challenge**
(`contests/flagship/`, shipped separately as
`voidwell2_challenge.zip`).  A published H, a withheld key, and an
offline gate that confirms a solve — the publishable form of the
construction.

### What did NOT change

The machinery is untouched: the fare-octal base transitions, the
lift/project heterobase conversion, the UCQ conjugation over
F_p = 2^256 - 2^32 - 977, the rejection-sampled emergent
nullification (a wrong matrix fails the gate's structural audit
with probability 1 - 2^-3), the checkpoints, the fare ledger and
its tau^2 = 0 linearity (verified on real encodings).  The
monograph's three utilized pieces — UC-Q (Ch. VI sec. 6.2.8b),
the Multinumeral (App. A), UC-polynomials (Ch. VIII sec. 8.5) —
carry over verbatim.  Voidwell-2 is Voidwell-1 with honest
commitments: the design study's retroactive note is that V1 with
these two changes and the same seed would have carried an honest
2^256.

### Where the history lives

* `docs/voidwell2_design_study.pdf` — the design study (the five
  design rules, the accounting, the spec).
* The Voidwell-1 archive (`voidwell_demo.zip`,
  `voidwell_challenge.zip`, the cryptanalysis report) — the
  original construction, its break, and the verification dossier.
