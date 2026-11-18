# THE VOIDWELL-2 CHALLENGE

**The hash:**

```
H = 30ec8b3b3164f173a11b556da9ab0c7c22086f6e950d9b95a0a5c570af8794cd
```

**The task:** find the 32-byte seed (the key) whose Voidwell-2
encoding of the public data, under the public parameters below,
produces exactly this hash.  The construction is fully public; the
seed is the only unknown.

**The check:** run the gate, offline, against your candidate key:

```bash
python3 -m voidwell2 gate --challenge challenge.json --key yourkey.json
```

`yourkey.json` is a two-line file:

```json
{"version": 2, "variant": "flagship", "seed": "<your 64 hex chars>"}
```

The gate prints `PASS` (exit 0) if and only if your seed is a
preimage of the published H under the public parameters.  There is
nothing else to submit and no server to contact — the gate IS the
judge.

---

## What H commits (the full construction)

Voidwell-2 derives everything from the seed and walks a 43-step
path through a three-layer number system:

```
D_0 = PRF(seed, "D0")                    -- 27-bit initial state
h   = SHA256("voidwell-v2" || ser(D_0))
for i in 1..43:
    if i in {3, 14, 15} (the PUBLIC pi-skeleton wells):
        Q  = lift(D)                     -- digivector -> 4x4 matrix over F_p
        Q' = M_j Q M_j^{-1}              -- M_j = PRF(seed), rejection-sampled
                                             until digit n_j of project(Q')
                                             is zero (the wells nullify
                                             digits 3, 1, 4 respectively)
        N_j = SHA256(ser(D') || Q')      -- the full-width nullifier
        D  = C_j                         -- C_j = PRF(seed) checkpoint
    else:
        D  = base_step(D, data[i])       -- fare-octal transition
    h = SHA256(h || ser(D))
H = SHA256(h || N_1 || N_2 || N_3 || ser(D_43) || wells_digest)
```

**Public parameters** (also in `challenge.json`):

| parameter | value |
|---|---|
| field | F_p, p = 2^256 − 2^32 − 977 (the hex in challenge.json) |
| data | `00112233` (its SHA-256 commitment is in the challenge) |
| path length | L = 43 |
| wells | positions 3, 14, 15; digits 3, 1, 4 (public π-skeleton) |
| lift version | 1 (the digivector↔matrix packing in `ucq/lift.py`) |
| variant | flagship — a 32-byte seed |

The PRF is domain-separated SHA-256 (`voidwell2/prf.py`); the
fare-octal base step is `voidwell2/encoder.py: base_step`; the
canonical serializations are in the same file.  The reference
implementation is the whole `voidwell2` package in this archive —
`run_path` is the single code path used by encoder, gate and
attacker alike, and re-implementing it from this table must
reproduce the same H bit-for-bit.

## The honest accounting

* **Security: 2^256.**  The expected work is 2^255 seed trials;
  every trial costs one FULL replay (~180/s on one core here —
  parallelize honestly and divide).
* **The sole assumption: SHA-256 preimage resistance.**  Nothing
  else in the construction is claimed as hardness.
* **Nothing to stand on but H.**  The challenge publishes no
  schedule digest and no per-well values, so there is no smaller
  commitment to invert, no dictionary to build, and no early
  abort: a candidate seed can only be checked by replaying the
  full path and comparing H.
* **The designer ships the attacker.**  `attacker/seed_search.py`
  runs the best known attack (seed enumeration) and prints the
  extrapolation; `attacker/surface_audit.py` audits the challenge
  surface; `attacker/toy_dictionary.py` demonstrates the
  dictionary methodology at the scale where it can exist.  Run
  them.
* If you find a better attack than seed enumeration, you have
  found something the design study believes does not exist — write
  it up.  Every finding is re-executed and verified before it is
  answered.

## Trying it out first

Two worked examples with published seeds are in `examples/` —
case 1 (flagship) and case 2 (compact, different data) each carry
the exact expected output (`OUTPUT.txt`).  Run them to see the
programs work before aiming at the sealed hash:

```bash
python3 -m voidwell2 gate --challenge examples/case1-flagship/challenge.json \
    --key examples/case1-flagship/key.json     # PASS
```

A compact study challenge (16-byte key, 2^128) is also sealed in
`contests/compact/` — same construction, a smaller needle, for
practice at attacking the same surface.

## Rules and disclosure

* Any seed that makes the gate print `PASS` is a valid solve —
  the construction is deterministic, so the preimage is unique up
  to SHA-256 collisions (finding a colliding alternative preimage
  would itself be the interesting result).
* The key is withheld by the issuer and archived outside this
  archive (`voidwell2_challenge_KEY.json`, demonstration
  disclosure); it is not needed to verify a solve.
* Everything in this archive is the complete construction — there
  are no secrets in the code, only in the 32 bytes you are looking
  for.
