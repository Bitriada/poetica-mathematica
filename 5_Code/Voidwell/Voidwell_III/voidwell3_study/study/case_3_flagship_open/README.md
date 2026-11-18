# Case 3 — Flagship, Open (the unsolved test case)

**Variant:** `flagship` · **Model:** full (4×4 over the 256-bit
prime, L = 43, wells at the primes 2, 3, 5, 7) ·
**Claim:** security = min(256, 256) = 2²⁵⁶.

```
H = 8c0b6127ca1c65966c63ab34190d7370f7d6e34c00e448d33809bcbe59e6bf20
```

**The problem:** find the 32-byte seed. The key is not in this
package.

## The rules (short, and the whole of them)

1. Any tool, any hardware, any amount of time. There are no rules
   about *how* you search — the construction's claim is about how
   *much* search is needed, and it states the number itself.
2. The claim: expected work is 2²⁵⁵ full-walk replays (half the key
   space, on average), under the single assumption of SHA-256
   preimage resistance. No layer of the construction purports to
   add difficulty beyond the seed width, and no layer subtracts
   from it.
3. There is nothing to exploit in the publication: the challenge
   carries H and the public parameters, nothing per-well. The
   surface audit confirms it, and the gate rejects anything wider.

## Verifying a candidate (you do not need the issuer)

Anyone can check a candidate seed without contacting anyone:

```
echo '{"version": 3, "variant": "flagship", "seed": "<your 64-hex chars>"}' > candidate.json
python3 -m voidwell3 gate study/case_3_flagship_open/challenge.json candidate.json
```

`PASS` means you hold the key. `FAIL: binding` means the replay
produced a different H — most candidates fail this way, at full
replay cost, with no partial feedback.

## Tools you are expected to use

* `python3 -m voidwell3.attacker.surface_audit study/case_3_flagship_open/challenge.json`
  — confirm there is nothing published to filter against.
* `python3 -m voidwell3.attacker.seed_search study/case_3_flagship_open/challenge.json`
  — the honest enumeration: random seeds at full path cost, with
  the accounting printed (coverage, rate, expected work).
  `--exhaustive` will refuse: the space is 2²⁵⁶, and the tool caps
  exhaustive walks at 2²⁰ by design.
* `python3 -m voidwell3 verify` — the 34-check battery, so you can
  confirm the construction behaves as this file claims before
  spending compute on it.
* `python3 -m voidwell3 toy` — the exhaustive small model, where
  the same accounting can be checked end-to-end in 95 seconds.

## Fairness note (why the issuer holds a key at all)

The issuer sealed this challenge from a real 32-byte seed and keeps
the key file OUT of this distribution, solely so the challenge can
be *retired* later — the key can be revealed to prove H was
produced by an honest encoding and not chosen arbitrarily. The key
grants no verification monopoly: any candidate seed verifies
locally, as above. If the issuer ever publishes the retirement key,
the gate's PASS on it is the proof of honest construction.

## A sober reading

By the artifact's own accounting — the same accounting that let you
break case 1 in four seconds — this case does not fall. If someone
submits a working seed, either they searched 2²⁵⁵ replays, or
SHA-256 preimage resistance failed, or the construction has a flaw
its battery did not measure. All three outcomes are informative,
which is why the case is published open.
