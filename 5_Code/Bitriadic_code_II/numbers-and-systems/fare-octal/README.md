# fare-octal — the Fare-Octal counting system, operational

**Pure Python, zero dependencies** (standard library only).  A small, neat
implementation of **Appendix A ("Fare-Octal Counting System")** of
*Poetica Mathematica: Cogitatio ex Nihilo et Speculum Scientiae*
(K. I. Kovlekov, CC BY 4.0) — built **proof by trial**: every claim of the
appendix is either reproduced exactly, or fails with an exact witness.

```bash
python demo.py            # the guided tour (~1 s)
python -m fareoctal verify   # V1-V7 proof-by-trial dossier -> results/VERIFICATION.md
python -m fareoctal address value:15
pytest                    # unit tests (pytest only, no other deps)
```

## What Fare-Octal is (per the monograph)

> "This counting system looks and counts like ordinary base-8, with digits
> 0–7 and standard carry-based addition, but each octal digit encodes three
> on/off switches, giving a hidden 27-bit space.  Multiplication follows a
> square-free prime mechanic: two numbers merge their active switches only
> if the underlying prime labels share no common factor, and produce zero
> if any switch is duplicated." — Ch. V (the appendix's own gloss)

A state is 27 switches displayed as 9 octal digits `[D8 … D0]`; counting is
plain octal; multiplication *merges* switch sets when coprime and
*collapses to zero* on overlap.  The appendix's stated purpose: a compact
readable notation for all 2²⁷ switch configurations — "familiar counting
on the surface, with a special collapse-on-overlap rule at the core."

## The three readings of one state

```python
from fareoctal import FareOctal

s = FareOctal.from_value(15)   # switches of the squarefree integer 15 = 3*5
s.display()    # '[0 0 0 0 0 0 0 0 6]'  -- the octal display (bits 1,2)
s.to_int()     # 6        -- COUNT: the 27-bit pattern as an integer
s.value()      # 15       -- VALUE: squarefree Fare reading (primes 3,5)
s.h_weight()   # 2**15    -- H-WEIGHT: spectral embedding in the 117-point
                            #   lattice's H tensor: cells (1,2,1)+(1,3,1),
                            #   weights 2^(3·2) · 2^(3·3) = 2^6 · 2^9
```

## The 117-point lattice as a storage convention (not a 1:1 matchup)

The Arithmetic Bitriada (Ch. I) is a 9 + 27 + 81 = 117-point structure
(axes 39/39/39); the monograph notes its **H-level counting was moved to
Appendix A** — Fare-Octal *is* that system.  This project reads the
lattice, per the user's framing, as a **combinatorial convention for
storage and addresses**:

| lattice piece | cardinality | Fare-Octal role |
|---|---|---|
| L level | 9 | the 9 octal digits Dn ↔ H-tensor rows (k, i) |
| M level (the Tribit, 27 chambers) | 27 | the 27 bits ↔ the 27 H-tensor cells (i, j, k), via the monograph's own `L = 9(k−1) + 3(i−1) + (j−1)` |
| H tensor cells | 27 | bit b's storage weight 2^(3·k·i·j); state weight = product |
| H level / Fortress (81 = 3⁴) | 81 | **outside the window**: the Epoch-6 observation axis; not addressable in 27 bits |

All L/M/M′/M″/H tables are implemented exactly (the monograph's rounded
entries "6,87E+10", "1,8E+16" match their exact values 2³⁶·…, 2⁵⁴).

## The window Fare algebra F₂₇

Appendix A's states are exactly the basis elements of the Fare Algebra
(Ch. IV §4.1.1) restricted to the first 27 primes:

    τ_S · τ_T = τ_{S∪T}  if S∩T = ∅,   else 0        (Prop. 4.1.1.2)

```python
from fareoctal import FareElement, tau, spectral_involution, zeta_element
from fractions import Fraction

A = FareElement.from_states(tau(0), tau(1))    # τ₂ + τ₃  (App. A §7.2)
B = FareElement.from_states(tau(0), tau(2))    # τ₂ + τ₅
A * B        # τ₁₀ + τ₆ + τ₁₅  (exact, completing the monograph's symbolic §7.2)

Z = zeta_element(Fraction(1, 2), r=4)          # the window zeta element
spectral_involution(Z, Fraction(1, 2)) == Z    # critical line: ι_{1/2} = id
```

The **spectral involution** ι_s(τ_n) = n^{1−2s}τ_n and the algebraic
**functional equation** Z(s) = ι_s(Z(1−s)) (Claim 4.1.1.6) are checked
exactly (integer s over ℚ; the exponent identity holds structurally).

## Proof by trial — the findings

`python -m fareoctal verify` runs V1–V7 (all exact arithmetic):

| id | check | verdict |
|----|-------|---------|
| V1 | counting table, first 16 states, carry displays | **PASS** |
| V2 | addressing: bit ↔ tensor ↔ digit ↔ prime, all 27 | **PASS** |
| V3 | product rules: closure, associativity, unit, nilpotency (2000 random triples) | **PASS** (documented divergence) |
| V4 | the appendix's worked examples (§4.2, §7.1, §7.2) | **PASS** (documented divergences F2, F4) |
| V5 | window product ≡ Fare-Algebra basis product (500 random pairs); involution; functional equation | **PASS** |
| V6 | the 117-lattice tables and storage convention | **PASS** |
| V7 | state census: 2²⁷ states, primorial max value, 2⁶⁴⁸ max H-weight, bijections | **PASS** |

The five honest findings (each with an exact witness in the report):

* **F1** — Appendix A §4.1's multiplication rules, read *literally* as gcd
  on the 0–26 indices, are **not closed** (τ₅·τ₇ → τ₃₅; there is no bit 35)
  and **not associative** ((τ₁τ₁)τ₂ = 0 but τ₁(τ₁τ₂) = τ₂).  The value
  reading — the monograph's own Ch. V gloss (gcd on the squarefree
  integers) — repairs both: a commutative monoid, closed and associative.
* **F2** — the §4.2 worked example's printed AFTER state matches **no**
  reading: its BEFORE state (τ₃ → `[0 0 0 0 0 0 0 0 2]`) uses the value
  reading, so τ₃·τ₅ = τ₁₅ should display as `[0 0 0 0 0 0 0 0 6]` (bits 1,2
  = primes 3,5); the linear-index reading of "tau_15" would be
  `[0 0 0 1 0 0 0 0 0]` (D5 is the 4th token from the left); the printed
  `[0 0 0 0 0 1 0 0 0]` is actually bit 9 (prime 29).
* **F3** — the symbol τ_n denotes two different switches in one appendix:
  linear labels in the §5 counting table (Count 1: "τ₀ active"), prime
  labels in §7.1 (τ₂·τ₃ = τ₆ works only if τ₂ = prime 2).  Both are
  implemented (`active_linear()` / `active_prime_labels()`).
* **F4** — §7.2's multi-tau product is left symbolic ("Each term
  evaluated: … if gcd=1, else 0"); the window algebra completes it
  exactly: (τ₂+τ₃)(τ₂+τ₅) = τ₁₀ + τ₆ + τ₁₅, a *sum* of states — which is
  precisely why a linear layer (FareElement) is needed.
* **F5** — the "zero state" `[0 0 0 0 0 0 0 0 0]` (all switches off) is
  the Fare algebra's **unit** τ₁ = 1, not zero; the algebra's 0 is not one
  of the 2²⁷ states.  Hence `UNIT` and `ZERO` in this package.

## Layout

```
fareoctal/
├── core.py       the 27-bit state space: display/count/value/h-weight,
│                 addressing (linear/tensor/prime/digit), the Fare
│                 product, the literal index rule (divergence witnesses)
├── lattice.py    the 117-point tables (L, M, M', M'', H) exactly; the
│                 storage/addressing convention; the Fortress note
├── algebra.py    FareElement (window Fare algebra F_27), spectral
│                 involution, zeta element, functional equation
├── verify.py     V1-V7 proof-by-trial dossier + VERIFICATION.md writer
├── tour.py       the guided tour (demo)
└── __main__.py   CLI: verify / demo / info / address
demo.py           thin wrapper -> fareoctal.tour
tests/            19 unit tests (pytest; everything exact)
results/          VERIFICATION.md (generated)
```

## Scope and honesty

This is a faithful *implementation and trial* of Appendix A's counting
system, the §4.1.1 window algebra, and the Ch. I lattice tables.  It does
not verify the monograph's (par)/(res) narrative around the lattice
(attractor, IFS, least-action); it operationalizes exactly what is
combinatorially stated.  Where the appendix contradicts itself, the
contradiction is kept and pinned (F1–F5), not silently repaired.

## License

MIT (the code).  The monograph it implements is CC BY 4.0 (K. I. Kovlekov).
