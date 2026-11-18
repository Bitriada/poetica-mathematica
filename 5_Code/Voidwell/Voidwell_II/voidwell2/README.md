# Voidwell-2 — Nilpotent Voidwell Cryptography

Voidwell-2 is a **hash-and-key construction**: from a secret seed
it deterministically derives a 43-step walk through a three-layer
number system and publishes a single SHA-256 hash `H` of the walk.
Holding the seed is holding the key — the gate re-derives the walk
and accepts the key only if the hash matches.  Everything about the
construction is public except the seed; there is nothing to know
and nowhere to stand except the hash.

**Security = min(seed bits, 256).  Flagship: 2^256 (32-byte key).
Compact: 2^128 (16-byte key).  The sole hardness assumption is
SHA-256 preimage resistance; every other layer — the fare-octal
base, the quaternionic conjugations, the fare ledger — is
integrity and narrative, audited as such.**  The best attack is
seed enumeration at full replay cost, and it ships in this package
(`attacker/seed_search.py`) so the claim can be checked, not
believed.

## The construction

```
LAYER 3  BINDING    SHA-256 chained over the full path; only the
                    final H is published
LAYER 2  WELLS      UC-Quaternion conjugation over F_p: lift the
                    state to a 4x4 matrix, conjugate by a secret
                    M, project back, record a FULL-WIDTH nullifier
                    (the whole conjugated matrix is hashed), restart
                    from a secret checkpoint
LAYER 1  BASE       fare-octal digivector transitions: a 27-bit
                    state of nine octal digits, union-or-annihilate
```

The walk, precisely:

```
D_0 = PRF(seed, "D0")                    -- 27-bit initial state
h   = SHA256(IV || ser(D_0))
for i in 1..43:
    if i in {3, 14, 15} (the PUBLIC pi-skeleton wells):
        Q  = lift(D)                     -- digivector -> 4x4 over F_p
        Q' = M_j Q M_j^{-1}              -- secret matrix, PRF-derived
        D' = project(Q')                 -- 4x4 -> digivector
        (M_j is rejection-sampled until digit n_j of D' is zero
         -- the nullification is emergent, and the gate audits it)
        N_j = SHA256(ser(D') || Q')      -- the FULL-WIDTH nullifier:
                                           a 27 + 4096-bit domain
        D  = C_j                         -- secret checkpoint restart
    else:
        D  = base_step(D, data[i])       -- fare-octal transition
    h = SHA256(h || ser(D))
H = SHA256(h || N_1..N_3 || ser(D_43) || wells_digest)
```

Three design facts carry the security accounting:

* **Full-width nullifiers.**  Each well commits the entire
  conjugated matrix, not just its 27-bit shadow — a preimage
  domain of 2^4123.  One well already saturates a 256-bit seed;
  there are three.
* **Minimal publication.**  The challenge publishes `H` and the
  public parameters — nothing per-well, no schedule, no
  intermediate values.  The gate *enforces* this surface: a
  challenge that publishes more is rejected as malformed.  With
  nothing to match against, every wrong seed costs one full
  replay — no dictionaries, no preimage targets, no early abort
  (measured: wrong-seed replays run at the same rate as honest
  ones).
* **The key is the seed alone.**  The wells sit at public
  constants — the pi-skeleton, positions 3, 14, 15, digits 3, 1,
  4 (pi = 3.1415...: the first six digits place and direct the
  three wells).  Secret positions would buy zero bits once
  nothing is published per-well; public constants have nothing to
  preimage and are nothing-up-my-sleeve by construction.

## The two variants

| variant | key | security | best attack |
|---|---|---|---|
| flagship | 32-byte seed | 2^256 | 2^255 full replays (~1e+67 years at 180/s) |
| compact | 16-byte seed | 2^128 | 2^127 full replays (~3e+28 years at 180/s) |

## Quick start: two test cases

Nothing to install — pure standard library, Python 3.10+.  From
this directory:

**Case 1 — create a challenge and key (flagship), then check it:**

```bash
python3 -m voidwell2 encode --variant flagship --data 00112233 \
    --seed 1111111111111111111111111111111111111111111111111111111111111111 \
    --out examples/case1-flagship/challenge.json \
    --key-out examples/case1-flagship/key.json
python3 -m voidwell2 gate --challenge examples/case1-flagship/challenge.json \
    --key examples/case1-flagship/key.json
# PASS
```

**Case 2 — the compact variant with different input data:**

```bash
python3 -m voidwell2 encode --variant compact --data deadbeef \
    --seed 22222222222222222222222222222222 \
    --out examples/case2-compact/challenge.json \
    --key-out examples/case2-compact/key.json
python3 -m voidwell2 gate --challenge examples/case2-compact/challenge.json \
    --key examples/case2-compact/key.json
# PASS
```

Both cases are pre-computed in `examples/` with the exact expected
output in `examples/case*/OUTPUT.txt`; `make examples` re-runs them
and asserts the stored results reproduce bit-for-bit.  The seeds
above are published demonstration seeds — any real key is
generated with `keygen`:

```bash
python3 -m voidwell2 keygen --variant compact --out mykey.json
python3 -m voidwell2 encode --variant compact --data <your hex> \
    --out challenge.json --key-out key.json     # --seed omitted: random
python3 -m voidwell2 gate --challenge challenge.json --key key.json
```

## The programs

```
python3 -m voidwell2 keygen   --variant flagship|compact [--out key.json]
python3 -m voidwell2 encode   --variant ... --data <hex> [--seed <hex>]
                              --out challenge.json [--key-out key.json]
python3 -m voidwell2 gate     --challenge challenge.json --key key.json
                              exit codes: 0 PASS, 1 FAIL, 2 malformed
python3 -m voidwell2 params   the parameter table
python3 -m voidwell2 tickkey  the pi-clock floor piece (see below)
```

The attacker package in `attacker/` (its own folder, with its own
README) contains every attack that exists, priced honestly:

```bash
python3 attacker/surface_audit.py contests/flagship/challenge.json
python3 attacker/seed_search.py --challenge contests/flagship/challenge.json --budget 4096
python3 attacker/toy_dictionary.py
```

## The sealed challenge

`contests/flagship/challenge.json` is a live, sealed challenge: a
hash with its key withheld.  The task, the rules and the
verification protocol are in `contests/flagship/README-CHALLENGE.md`
— find the 32-byte seed that produces the published `H`, and the
gate will confirm it offline.  (The demonstration key is archived
outside the shipped package, at the issuer's discretion.)

## What else is here

* **The small model** (`python3 -m voidwell2.small_model.harness`)
  — the whole construction at 2x2/F_7 with a 3-bit state,
  exhaustively enumerated: the checkpoint-less collapse at k=0, the
  saturation at one seed per hash, and the nullifier dictionary
  demonstrated at the only scale where it can exist (2^14.2 in the
  toy, 2^4123 at full scale — the honest split, printed).
* **The tick-key toy** (`python3 -m voidwell2 tickkey demo`) — the
  family's floor piece: the key is a moment in the pi-clock's life,
  the gate hashes the clock's three sheets at that tick.  An n-bit
  key with n bits of security and nothing on top; it exists to keep
  the accounting legible — everything above it adds structure and
  auditability, not bits.
* **`RESEARCH-V3.md`** — the parked research direction (a well with
  independent hardness): why the obvious candidates fail by linear
  algebra, and the first real question.
* **`docs/voidwell2_design_study.pdf`** — the full design study.
* **`CHANGELOG.md`** — what changed relative to Voidwell-1 and why.
* **`results/`** — measurements, the small-model table, the run
  record (`RUN.md`), the withheld demonstration keys.

## Layout

```
fareoctal/           the fare-octal counting package (base layer)
ucq/                 F_p matrices, the digivector <-> matrix lift,
                     conjugation, multinumeral structure, fare ledger
voidwell2/           prf.py, wells.py, encoder.py, gate.py,
                     __main__.py (CLI), tickkey.py,
                     small_model/harness.py, pi_const.json
tests/               verify.py (the W1-W13 battery), measurements.py
examples/            case1-flagship/ and case2-compact/ (the two
                     illustration cases, with expected outputs)
contests/            the sealed challenge (+ the compact study
                     challenge); keys withheld to results/
attacker/            the attacker package (separate folder)
docs/                the design study
results/             measurements and the run record
Makefile             make demo / verify / examples / attacker / ...
CHANGELOG.md         the change record
```

## Run everything

```bash
make demo         # the full battery (~2 minutes)
make verify       # the W1-W13 battery
make examples     # re-run and check the two illustration cases
make challenge    # verify the sealed challenge gates with the
                  # withheld demonstration key
make small        # the small model
make attacker     # the attacker package against the contests
make measurements # rates + attack extrapolations
make tickkey      # the floor piece demo
```

## The honest security statement

* Security = **min(seed bits, 256)** — never a key-space product.
* The assumption: **SHA-256 preimage resistance**, stated as the
  sole hardness assumption.
* The best attack is **seed enumeration at full replay cost**
  (~180 replays/s on one sandbox core; the attacker package is
  that attack, shipped).
* The small model demonstrates the method and the accounting; it
  cannot demonstrate 256-bit preimage hardness — the claim rests
  on SHA-256, stated, never on the toy.
