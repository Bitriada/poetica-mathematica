# Voidwell Challenge — Test 3 (k = 3)

> **Challenge.** `challenge.json` contains `H`. Find any `key.json`
> (a 256-bit `seed` and a `schedule` of 3 well positions with 3 well
> digits) such that
> `python -m voidwell gate --challenge challenge.json --key key.json`
> prints PASS.
>
> **Parameters.** Field: F_p, p = 2^256 − 2^32 − 977 (printed by
> `python -m voidwell params`). Path length L = 43. Wells k = 3.
> Hash: SHA-256, iterated over the full path. Lift version 1. The
> public message is `data = 00112233` (its SHA-256 commitment is in
> the challenge).
>
> **Key space — a count of keys, not a security level.** 2^256 ×
> C(43,3) × 9^3 = 2^256 × 8,996,589 ≈ **2^279.1** keys exist. The
> security claim originally attached to that product is **withdrawn**
> (see the disclosure below): the schedule digest commits only
> C(43,3) × 9^3 = 2^23.1 schedules and falls to an exhaustive
> preimage in seconds; each nullifier commits a 2^27 state and falls
> to a dictionary scan in about a minute. Committed secrets drawn
> from spaces this small are integrity checks, not work factors.
>
> **Corrected claim.** A passing key must satisfy about **180 bits**
> of independent hash-derived conditions on the seed: 108 bits
> pinning the path (the initial state D_0 and the three checkpoints
> C_1, C_2, C_3 are fixed by `H` through the hash chain) plus 3 × 24
> bits pinning the three nullifiers (the nullified digit itself is
> free — the rejection sampling enforces it). The best known attack
> is the structured one: fix the schedule by preimage, invert the
> nullifiers into early-abort filters, then search seeds — about
> 2^180 seed evaluations. Blind brute force over random (seed,
> schedule) pairs costs about 2^203.1 trials. Neither is practical
> (~10^44 years at the measured replay rate); within the stated
> model the seed is the entire construction.
>
> **Disclosure (2026-11-16).** This challenge was independently
> cryptanalyzed on the day of issue, and every finding was verified
> against the withheld key by the issuer. The schedule is
> **[(28, 0), (32, 5), (42, 3)]** — the unique preimage of the
> published schedule digest, recovered by exhaustive hashing in 4.4
> s. All three nullifier preimages — the secret post-conjugation
> states 38,644,752 / 86,246,842 / 92,106,969 — were recovered by a
> single 2^27 dictionary scan in about a minute, each carrying
> exactly the digit zeroed that its well nullifies. The **seed did
> not fall**: ~830,000 low-entropy candidates (patterned bytes,
> hash-derived words, numerics, timestamp-seeded Mersenne Twister
> outputs spanning the packaging window) all fail, and the seed is
> consistent with a uniformly random 256-bit value. The schedule and
> nullifier preimages above are therefore public knowledge; the
> standing problem is exactly the 256-bit seed, and the challenge
> remains open under the corrected claim.
>
> **Small-model evidence (revised).** The original harness reported
> "attack cost equals the key space for every k ≥ 1, slope 2.989
> bits/well". That number measured the inverse density of keys per
> hash value — an artifact of counting, not the work of any
> adversary — and is refutable inside the harness's own model: the
> structured attack solves the harness's own reference challenges at
> k = 1, 2, 3 with worst-case work of 288 / 516 / 1,776 operations
> against key spaces of 6,144 / 64,512 / 387,072 (speedups 21× /
> 125× / 218×, growing with k; slope 1.31 bits/well). The harness
> (revision 2, `python -m voidwell.small_model.harness`) now
> measures the structured attack as the baseline and retains the
> density quotient only as a labeled artifact.
>
> **Submission.** Fill in `submission_template.json` and send it via
> the announcement channel. First valid submission wins. Verification
> is `./verify.sh your_key.json`, which runs the public gate.
>
> **Verification of the challenge itself.** Anyone can run
> `python -m voidwell gate --challenge challenge.json --key key.json`
> with the withheld key, which will be published after the contest
> closes, to confirm the challenge was solvable and the gate accepts
> it.

## What the layers do

* **Base layer (fare-octal, commutative).** The path state is a
  27-bit digivector: nine octal digits, each a 3-switch sub-base with
  its own prime labels (2, 3, 5, …, 103) and its own H-tensor row.
  Transitions are exact algebraic operations: generator union
  (annihilating unions fall back to a slot write — the fare is paid,
  the state survives), slot burns, slot writes. *Attacker's view
  (verified):* for a fixed message the layer is a period-4 cycle of
  four fixed digit operations touching only digits {0, 4, 8} — the
  fare-octal apparatus plays no role in the transition function, and
  18 of the 27 bits ride through every base segment untouched.
* **Well layer (UCQ, non-commutative).** At each well the digivector
  is lifted to its 4×4 UC-Quaternion matrix form (rows = quaternion
  direction, columns = UC component; §6.2.8b of the source), conjugated
  by a PRF-derived matrix (rejection-sampled so that the conjugated,
  projected digivector has the target digit zero — the nullification
  is emergent, and the gate's structural audit checks it), committed
  by a nullifier, and the path restarts from a secret checkpoint.
  Well order matters: conjugations do not commute (verified, 200/200
  random pairs differ). *Attacker's view (verified):* the conjugation
  is simply a hash — its only cryptographic role is to make the
  nullifier filters uniform (measured: chi-square 241 on 255 df,
  exactly a 2^-24 filter per well).
* **Binding (SHA-256).** `h_{i+1} = SHA-256(h_i ‖ serialize(D_{i+1}))`
  commits the FULL path; `H` additionally commits the nullifiers, the
  endpoint, and the schedule digest. This is the layer that carries
  the construction: everything the gate checks funnels into ~180 bits
  of hash conditions on the seed.

## Files

* `challenge.json` — the public challenge (H, schedule digest,
  nullifiers, data commitment, parameters).
* `verify.sh` — runs the gate on a submitted key.
* `submission_template.json` — the submission form.
* `../README.md` — how to run everything.
