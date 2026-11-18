# trinumeral — the heterobase counting system, operational

**Pure Python, zero dependencies** (standard library only; exact arithmetic via
`fractions.Fraction`). A demonstrable implementation of the **Trinumeral** of
*Poetica Mathematica: Cogitatio ex Nihilo et Speculum Scientiae* (K. I.
Kovlekov, CC BY 4.0), Ch. VIII §8.4 (*Heterobase counting system: Trinumeral,
spin-tallies*, §§8.4.1–8.4.18) — built **proof by trial**, in the style of the
companion `fare-octal` and `nilpotent-crypto` projects.

```bash
python demo.py                  # the guided tour (~0 s)
python -m trinumeral trials     # V1-V10 proof-by-trial -> results/TRINUMERAL_TRIALS.md
pytest                          # 20 unit tests, all exact
python -m trinumeral show 1/10 --p 8
python -m trinumeral spin --angles 360,360,-360
```

## What a trinumeral is

> "A trinumeral T is a meta-number: a container that holds one value in three
> distinct representations simultaneously. We write T = (B, i, f, τ)." — §8.4.1

* **B** — binary, the *deep* representation (truncated to p fractional bits, default 53)
* **i** — integer, the *forward* representation (truncation toward zero)
* **f** — float, the *backward* representation (nearest IEEE 754 double)
* **τ** — the **heterobase trace**: the discrepancies of forcing one value
  through three bases, living in the graded exterior algebra Λ(V) on three
  nilpotent, anticommuting generators:

```
alpha = canonical(B) - i          e1: binary -> integer
beta  = i - exact(f)              e2: integer -> float
gamma = exact(f) - canonical(B_fb) e3: float -> binary
```

Every coefficient is an exact rational. The float sheet is always read back
through `float.as_integer_ratio()`, so the algebra never rounds — it *records*,
exactly, what the representations themselves lose.

## The monograph's claims, and what happens to them here

| § | claim | outcome |
|---|---|---|
| 8.4.2 | Λ(V) on 3 nilpotent anticommuting generators; the 2³=8 activation patterns | **EST-CONFIRMED** exactly (V1); the 8 patterns *are* the basis monomials — Pascal's row 1,3,3,1 by grade |
| 8.4.5 | the τ-cycle αβγ·(e₁e₂e₃); "(e₁e₂e₃)² = 0 … can accumulate but cannot compound" | **EST-CONFIRMED** structurally (V3) |
| 8.4.8 | worked example v = 0.1: γ ≈ 10⁻¹⁷, τ-cycle "on the order of 10⁻¹⁹" | **reproduces exactly**: γ = 1/2⁵⁵ ≈ 2.78e−17, cycle ≈ −2.78e−19 (V2) |
| 8.4.3/8.4.3a | the two annihilation ladders (trigger × response) | **implemented as the 2D parameter space the monograph calls for**; every level's invariant tested (V6) |
| 8.4.10 | the angle bridge; floor convention; the negative-angle remark | **EST-CONFIRMED**: (0,300)+(0,100) = (1,40); θ = −1° → (−1, 359) (V8) |
| 8.4.12/8.4.18 | the spinorial double cover; "the coherent spinor regime"; the Berry-phase regime | **EST-CONFIRMED literally**: 720° → σ = +1 with zero trace and ghost = 2 (pair annihilation); +360°,−360° → trace e₁ − e₂ ≠ 0 (V9) |
| 8.4.16 | the two-sheet ladder UC → UCQ → UCO → UCS | the **UCQ rung** is implemented and verified in the companion `nilpotent-crypto` project; UCO/UCS [OPEN] here |

## Established here (new exact results)

* **The Telescope Theorem** — with the stored-B reading of B_fb, **α + β + γ = 0
  identically**: the heterobase triangle B → i → f → B closes (500 random
  rationals, exact). The three translation costs cancel around the cycle.
* **Ledger vs state** — the trace τ is a *path-dependent ledger* of conversion
  events; `fresh_discrepancies()` is a *path-independent state function*. The
  monograph's "trace" names both; a conversion record can cancel initial trace
  linearly with no annihilation (V5 witness).
* **Invariant points exactly characterized** — traceless ⟺ v is an integer
  exactly representable in double precision (correction C7 to §8.4.17's
  candidate list: 3/2 and 1/2 do *not* qualify — the integer sheet cannot hold
  fractions).

## Seven corrections to the monograph (exact witnesses in the trials)

* **C1** — §8.4.2's formal γ (B_fb = exact re-encode of the double) is
  *identically zero*: every IEEE double is a dyadic rational. The §8.4.8
  example's 10⁻¹⁷ magnitude requires the practice-note reading (B_fb = stored
  B), which is the default here (and yields the Telescope Theorem).
* **C2** — §8.4.8's fresh-discrepancy signs are the negatives of §8.4.2's edge
  conventions (witness: the XOR case, −4 vs +4).
* **C3** — §8.4.3 Level 1 transfers |α| to the ghost; §8.4.3a Level 1 transfers
  2|α| and "conserves total magnitude". The conserving version is implemented.
* **C4** — response-level preconditions clarified (R1 cancels only true pairs;
  R4's transfer generalized; R2 fills before saturating).
* **C5** — §8.4.12's σ-flip rule as printed breaks §8.4.18's own claim for
  multi-boundary jumps (a single 720° jump must return σ = +1);
  flip-per-boundary is implemented.
* **C6** — §8.4.18 Level 3's "after 360°, σ returns to +1" does not follow from
  the algebraic flip rule; the bosonic return is the plain tally's mod-360
  identity.
* **C7** — the §8.4.17 invariant-point candidates are too loose (above).

## Layout

```
trinumeral/
├── grassmann.py   Λ(V): exact exterior algebra, 8 monomials, wedge
├── core.py        Trinumeral: ω/0 and 0/a gates, α β γ, conversions,
│                  arithmetic species (carry | xor | ieee | mod),
│                  τ-cycle, ghost disc, activation patterns
├── ladder.py      the annihilation engine: trigger ladder × response
│                  ladder (one implementation, two users)
├── spin.py        SpinTally (angle bridge, three tally types) and
│                  SpinorialTally (σ, crossing edges e₊/e₋, double cover)
├── trials.py      V1-V10 proof-by-trial -> results/TRINUMERAL_TRIALS.md
├── demo.py        the guided tour
└── __main__.py    CLI: demo | trials | show | spin | info
tests/             20 unit tests (exact arithmetic throughout)
```

## Scope and honesty

This implements what is combinatorially stated in §8.4 and trials it. The
τ-cycle's "growth under iteration would force a bifurcation" is the monograph's
own "topic for further research" — [OPEN]. The 117-point lattice embedding of
the 8 activation patterns is asserted by the monograph; only the 2³ = 8 part is
implemented. The [CONJ]-level numerology of the surrounding chapters is not
tested here. What *is* delivered: the algebra, the ladder, the gates, the
worked example, the double cover — every number exact, every claim either
confirmed or corrected by witness.

## License

MIT (the code). The monograph it implements is CC BY 4.0 (K. I. Kovlekov).
