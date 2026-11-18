# The Attacker Package

The designer ships the attacker.  This folder contains every attack
that exists against a Voidwell-2 challenge, priced honestly — so
the security claim can be checked, not believed.

## Why the package is this small

The attack surface of a Voidwell-2 challenge is exactly one thing:
the published hash `H`.  There is nothing else to stand on:

* **No preimage targets.**  The challenge publishes no schedule
  digest and no per-well values — only `H` and the public
  parameters.  There is no small commitment to invert.
* **No dictionaries.**  Nothing per-well is published, so there is
  nothing to match a dictionary against — and the nullifiers'
  preimage domain is 2^4123 (the full conjugated matrix), so the
  dictionary itself could not be built either.
* **No early abort.**  The only check a seed trial can fail is the
  final H comparison, so every trial costs one FULL replay
  (measured: wrong-seed replays run at the honest rate, ratio
  ~1.0).

What remains is **seed enumeration at full replay cost**.  That is
not a gap in this package — it is the entire attack surface, and
`seed_search.py` is it.

## The tools

### 1. `seed_search.py` — the best known attack

```bash
python3 attacker/seed_search.py --challenge contests/flagship/challenge.json --budget 4096
python3 attacker/seed_search.py --challenge contests/compact/challenge.json  --budget 4096
```

Draws random seeds of the challenge's width, replays each in full,
reports the rate and the extrapolation: 2^255 full replays for the
flagship, 2^127 for the compact, at the measured ~180 replays/s
(that is 10^67 and 10^28 years respectively on this sandbox's
single core — parallelize honestly and divide).

### 2. `toy_dictionary.py` — the methodology demo

```bash
python3 attacker/toy_dictionary.py
```

Builds the complete nullifier dictionary in the 2x2/F_7 small
model — 8 x 7^4 = 19,208 = 2^14.2 entries — and matches a
published nullifier list.  This is the demonstration that the
dictionary attack *exists* where domains are toy-sized and cannot
exist at full scale (2^4123), and that against a real challenge it
is moot anyway: no nullifiers are published.  The small model
demonstrates the method; it can never demonstrate 256-bit preimage
hardness.  The claim rests on SHA-256, stated.

### 3. `surface_audit.py` — the pre-shipment check

```bash
python3 attacker/surface_audit.py contests/flagship/challenge.json contests/compact/challenge.json
```

Asserts that a challenge publishes exactly `H` + public parameters,
that every hash field is a 64-hex full-width SHA-256, that the
per-well leak fields (`nullifiers`, `schedule_digest`) are absent,
and that the parameters are the spec constants.  Run it against
every challenge before it is issued.  The `gate` also enforces the
surface at verification time (a challenge carrying leak fields is
MALFORMED).

## The honest summary

* **Flagship** (32-byte seed): security = min(256, 256) = **2^256**.
* **Compact** (16-byte seed): security = min(128, 256) = **2^128**.
* **The assumption**: SHA-256 preimage resistance.  Everything else
  (fare-octal base, UCQ conjugation, fares, nullification) is
  integrity and narrative, audited as such.
* **The tick-key toy** (`python -m voidwell2 tickkey demo`) is the
  floor piece: an n-bit key with exactly n bits of security and
  nothing on top — it exists to keep the accounting legible.  Climb
  it with `voidwell2.tickkey` at ~60,000 ticks/s.

If you find a better attack than seed enumeration, you have found
something the design study (section 7) believes does not exist —
write it up; the discipline that produced this package applies to
findings too: every claim is re-executed and verified before it is
answered.
