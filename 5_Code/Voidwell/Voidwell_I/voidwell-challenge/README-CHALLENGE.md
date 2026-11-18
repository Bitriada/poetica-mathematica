# Voidwell Challenge -- Test 3 (k = 3)

Everything in this package is yours: the full source of the
construction (no obfuscation, no withheld components) and the sealed
challenge.  The only thing not in the package is the key.

## The challenge

`contests/test3/challenge.json` holds `H`, the schedule digest, the
three nullifiers, and the public message `data = 00112233` (SHA-256
committed).  Find any key -- a 256-bit `seed` and a schedule of three
well positions with three well digits -- such that the public gate
accepts:

    ./contests/test3/verify.sh your_key.json

or equivalently:

    python3 -m voidwell gate --challenge contests/test3/challenge.json --key your_key.json

Fill in `contests/test3/submission_template.json` for your
submission.  Read `contests/test3/rules.md` for the parameters, the
corrected security claim, and the full cryptanalysis disclosure.

## What you have

* `fareoctal/`, `ucq/`, `voidwell/` -- the complete source: the
  fare-octal base layer, the UC-Quaternion well layer (lift,
  conjugation, nullification), the encoder, the gate, the CLI, and
  the small-model harness in revision 2, which measures the
  structured attack as the honest baseline
  (`python3 -m voidwell.small_model.harness`).
* `tests/verify.py` -- the V8-V12 verification battery for the
  algebra (run it; it should print 13/13 PASS).
* `tests/test_gate.py` -- the six tamper cases of the gate.
* `tests/test1/`, `tests/test2/` -- the published baselines k = 0 and
  k = 1 WITH their keys (seeds S1, S2), so you can confirm the
  pipeline end-to-end.
* `results/small_model.json` -- the revised measurement: the density
  artifact exposed for what it is, the structured attack measured
  (288 / 516 / 1,776 worst-case operations at k = 1 / 2 / 3 against
  key spaces of 6,144 / 64,512 / 387,072; slope 1.31 bits/well).

## State of play (2026-11-16)

This challenge was independently cryptanalyzed on the day of issue;
every finding is disclosed in `rules.md`.  In short: the schedule and
the three nullifier preimages are public (they cost seconds and one
minute to recover by preimage); the effective security is about 2^180
seed evaluations, not the 2^279.1 key-space count; the seed has not
fallen (~830,000 low-entropy candidates ruled out).  The challenge
stands under the corrected claim: produce any passing key.  If you
can beat 2^180, you have found something the issuer and the
independent analyst both missed.
