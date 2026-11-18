# Voidwell-3 — The Perspective Walk

**A study distribution.** Voidwell-3 is a hash-and-key
construction: from a secret seed it deterministically derives a
43-step walk through a three-layer number system — a fare-octal
state space, four "wells" of quaternionic conjugation, and a
SHA-256 binding — and publishes a single hash `H` of the whole
journey. Holding the seed is holding the key. Everything about the
construction is public except the seed: there is nothing to know
and nowhere to stand except the hash.

This package is meant for **studying and testing**: two solved test
cases (keys published), one open case (key withheld), the gate that
verifies, the encoder that produces encodings, the attacker tools
that price the security honestly, an architecture scheme, and a
changelog covering all three versions of the construction.

```
the four perspectives (public constants, exact matrix laws):
    i1^2 = i1                 UC1, the Complex Point (idempotent)
    i2^2 = -i2                UC2, the Complex Line (the half-turn)
    i3^2 = -1 - i1^2 - i2^2   UC3, the Complex Disc (obfuscated)
    i4^2 = -1                 UC4, the Field (the proper unit)
    i1^2 + i2^2 + i3^2 + 1 = 0    the loop closure

the prime skeleton (public, nothing-up-my-sleeve):
    wells at positions 2, 3, 5, 7 nullifying digits 2, 3, 5, 7
```

## The claim, stated first

**Security = min(seed bits, 256).** Flagship (32-byte seed): 2²⁵⁶.
Compact (16-byte seed): 2¹²⁸. Study-toy (2-byte seed): 2¹⁶ —
breakable by design, in about a minute, with the tools in this
package. **The key space IS the seed space.** The sole hardness
assumption is SHA-256 preimage resistance. Every layer above the
hash — the perspectives, the wells, the zeta-array, the ghost disc —
is binding, audit, and accounting machinery, and is priced as such.
The best attack is seed enumeration at full replay cost; it ships
in this package so the claim can be checked, not believed.

## What is in the box

| Path | What it is |
|---|---|
| `HOWTO.md` | **start here** — step-by-step: verify, break, study |
| `ARCHITECTURE.md` + `scheme_voidwell3.png` | the construction, layer by layer, with the scheme |
| `CHANGELOG.md` | every version: 1.0.0 → 2.0.0 → 3.0.0, in full |
| `study/case_1_toy_solved/` | the toy model as a challenge; key published; you can re-break it yourself |
| `study/case_2_compact_solved/` | a full-strength 2¹²⁸ challenge; key published as a specimen |
| `study/case_3_flagship_open/` | the open problem: a 2²⁵⁶ challenge, key withheld |
| `ucq/`, `voidwell3/`, `tests/` | the complete source: fields, matrices, the walk, the gate, the attacker, the verification battery |

## Quickstart (from this directory)

```
python3 -m voidwell3 params                        # the public constants
python3 -m voidwell3 gate study/case_1_toy_solved/challenge.json \
                             study/case_1_toy_solved/KEY.json      # -> PASS
python3 -m voidwell3.attacker.seed_search \
        study/case_1_toy_solved/challenge.json --exhaustive        # -> your first break
python3 -m voidwell3 verify                        # the 34-check battery
python3 -m voidwell3 demo                          # one guided encoding
```

Requirements: Python 3.10+ and nothing else (the standard library
is the whole dependency list). Run every command from the root of
this directory.

## The three test cases at a glance

| Case | Model | Seed | Status | What it teaches |
|---|---|---|---|---|
| 1 — toy | small (F₂₅₇, byte state) | 2 bytes | **solved** (key inside) | the whole construction in miniature; breakable in seconds — the accounting made visible |
| 2 — compact | full | 16 bytes | **solved** (key inside) | a real 2¹²⁸ challenge as a specimen; the same tool that breaks case 1 cannot dent it |
| 3 — flagship | full | 32 bytes | **open** (key withheld) | the honest 2²⁵⁶ problem; verify candidates locally, no issuer needed |

## The honest split

The small model demonstrates **method** — collapse without wells,
saturation with them, the dictionary, the surface — at a scale
where everything is visible. The claim rests on **SHA-256** and the
measured behavior of the full artifact. The structure adds
auditability, binding, and accounting; it does not add bits, and it
says so in every document of this package.

## Where to read next

* `HOWTO.md` — the guided tour, including the attacker tools and
  the exhaustive small-model battery.
* `ARCHITECTURE.md` — what each layer is and where each law lives
  in the source.
* `CHANGELOG.md` — what version 1 was, what happened to it, and
  what versions 2 and 3 changed (the cryptanalysis of V1 is part of
  the record, not a footnote).
