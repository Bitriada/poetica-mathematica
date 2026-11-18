# HOWTO — the guided tour

Everything below runs from the root of this directory with
**Python 3.10+ and no other dependencies**. Every command is real;
the outputs shown were captured on the issuer's machine from this
exact distribution.

## 0. Five-minute orientation

```
python3 -m voidwell3 params      # the public constants and audits
python3 -m voidwell3 demo        # one full encoding, narrated
python3 -m voidwell3 verify      # the 34-check battery (~40 s)
```

The `demo` output walks you through one flagship encoding: the
initial state, each well's perspective and rejection counter, the
digits nullified, a live ghost-disc proof (6 hashes for one of the
44 states), the 16 zeta cells, and the fare ledger balance.

## 1. Case 1 — verify the solved toy, then break it yourself

```
python3 -m voidwell3 gate study/case_1_toy_solved/challenge.json \
                        study/case_1_toy_solved/KEY.json
```
→ `PASS`

```
python3 -m voidwell3.attacker.seed_search \
        study/case_1_toy_solved/challenge.json --exhaustive
```
→ finds `seed = 104f` after 4,176 replays (~4 s at ~1,050
replays/s). The expected position is the middle of the space
(2¹⁵ replays, ~30 s) — the seed just happens to sit early.

That is the whole security model in one command: the key space IS
the seed space; when the space is 2¹⁶, the construction concedes it
honestly, at full replay cost per candidate, with no shortcut.

Full walkthrough: `study/case_1_toy_solved/SOLUTION.md`.

## 2. Case 2 — a real challenge as a specimen

```
python3 -m voidwell3 gate study/case_2_compact_solved/challenge.json \
                        study/case_2_compact_solved/KEY.json
python3 -m voidwell3 encode 4f062253c2e10034a651ba793244c10f
python3 -m voidwell3.attacker.seed_search \
        study/case_2_compact_solved/challenge.json --trials=2048
```

The gate passes; the verbose encode shows the interior (wells,
nullifiers, ghost root, zeta cells, ledger); the same search that
cracked case 1 covers a 2⁻¹¹⁷ fraction of this key space and is
priced at 2¹²⁷ replays. Then try the surface audit, and try to
sneak a `nullifiers` field into a copy of the challenge — the gate
answers `MALFORMED`:

```
python3 -m voidwell3.attacker.surface_audit \
        study/case_2_compact_solved/challenge.json
```

Full walkthrough: `study/case_2_compact_solved/SOLUTION.md`.

## 3. Case 3 — the open problem

Read `study/case_3_flagship_open/README.md`. Short version: find
the 32-byte seed behind

```
H = 8c0b6127ca1c65966c63ab34190d7370f7d6e34c00e448d33809bcbe59e6bf20
```

You verify candidates locally (the gate with your own key file);
you never need the issuer. The artifact's own accounting says this
costs 2²⁵⁵ replays. All three outcomes of an attempt — enormous
search, a broken SHA-256 assumption, or a construction flaw the
battery missed — are informative, which is why it ships open.

## 4. The attacker tools (meant for studying, on purpose)

| Tool | What it shows |
|---|---|
| `attacker/seed_search.py` | the honest enumeration; `--exhaustive` (capped at 2²⁰) walks a whole small space in order |
| `attacker/surface_audit.py` | that a challenge publishes only H + public parameters |
| `attacker/toy_dictionary.py` | the dictionary lesson: 250,562 nullifier entries invert 4/4 published nullifiers instantly — the reason the surface is H-only |

The designer ships the attack so the claims can be checked, not
believed. Run them against the sealed challenge in the main
distribution or against your own (`python3 -m voidwell3 seal DIR`).

## 5. Going deeper

```
python3 -m voidwell3 toy         # the exhaustive small model (~95 s):
                                 #   k=0: 256 distinct H (the collapse)
                                 #   k=1: 65,339 (one well binds)
                                 #   k=4: 65,536 -- exact saturation, 0 collisions
                                 #   D_L: 256/256 values, chi2 p = 0.96
python3 -m voidwell3 verify      # all 34 checks with their measured facts
```

Then read the source in this order: `encoder.py` (the walk — start
at `base_step`), `perspectives.py` (the four laws), `zeta.py` (the
cells and the disentangling), `ghost.py` (the accumulator),
`gate.py` (the audit suite). `ARCHITECTURE.md` is the map, and
`CHANGELOG.md` is the story — including the V1 cryptanalysis that
produced the doctrine this package runs on.

## 6. Exit codes and conventions

* The gate: `0` PASS, `1` FAIL (key replays to a different H),
  `2` MALFORMED (schema, surface, or public-math audit failure).
* Challenges are JSON; keys are JSON (`{"version": 3, "variant":
  "...", "seed": "<hex>"}`). The seed width must match the variant.
* All hashing is SHA-256 (binding) or SHAKE-256 (matrix derivation
  only); the field arithmetic is exact integer arithmetic mod p.

## 7. Sealing your own challenge

```
python3 -m voidwell3 seal mydir flagship    # or: compact
```

writes `mydir/challenge.json` + `mydir/challenge_KEY.json` and
gates the pair. The KEY file is the seed — keep it private, publish
the directory without it. (The `study-toy` variant of the shipped
cases was sealed the same way; see `attacker/` and the small model
for how such keys are studied.)
