# nilpotent-crypto — NPCS, the Nilpotent Path-Commitment Scheme

**Pure Python, zero dependencies** (standard library only; the `fareoctal`
package is vendored).  A demonstrable implementation of *nilpotent
cryptography* from *Poetica Mathematica: Cogitatio ex Nihilo et Speculum
Scientiae* (K. I. Kovlekov, CC BY 4.0), built **proof by trial** on top of
the Fare-Octal project: the monograph's UC-Q algebra (Ch. VI §6.2.8) made
operational, its Nilpotent Cryptography Conjecture (Book II) reduced to
what is actually testable, and the NPCS draft spec (v0.1) implemented with
every claim either confirmed or corrected by exact witness.

```bash
python demo.py               # the guided tour (~1 s)
python -m npcs trials        # T1-T10 proof-by-trial -> results/NPCS_TRIALS.md
pytest                       # 22 unit tests, all exact
python -m npcs keygen --length 64
python -m npcs commit 1,2,3
```

## The monograph's claims, and what happens to them here

| source | claim | outcome |
|---|---|---|
| Book II, Nilpotent Cryptography Conjecture | nilpotent arithmetic yields one-way commitments; "verification or refutation awaits the construction of a working" implementation | **operationalized**: the commitment below; one-wayness honestly reduces to SHA-256 ([ASSUMED]), quantum resistance stays [OPEN] |
| Ch. VI §6.2.8 | UC-Q = ℍ ⊗ ℝ UC is 16-dimensional; τ² = 0; τ central; Q·Q̄ = a²+b²+c²+d² (UC-valued, split signature) | **EST-CONFIRMED**, exactly (T1) |
| Ch. VI §6.2.8a, Prop. 2.8a.1 | (v₁+τt₁)(v₂+τt₂) = v₁v₂ + τ(v₁t₂+v₂t₁) — Leibniz | **EST-CONFIRMED** (T1, T5) |
| Ch. VI §6.2.8a, Cor. 2.8a.4 | four-direction trace accumulation, order-independent for central coefficients | **EST-CONFIRMED** to the letter (T1) |
| Ch. VI §6.2.8 | "the numbers themselves carry their own history" — self-auditing | **EST-CONFIRMED**: the trace sheet equals the ordered Leibniz transcript of the path (T5) |
| Book II | ghost disc D²_τ binding territory = 2⁶⁴⁸ | **locks exactly** with Fare-Octal's maximal H-weight 2⁶⁴⁸ (T9) |
| Book II, betrayal corollary | "the architecture has no operation for subtraction" | true of the Fortress *counting* architecture; **UC-Q itself has additive inverses** — corrected (C2), with the honest restatement: multiplication by τ is non-injective (information annihilation, demonstrated) |

## The scheme (NPCS draft, corrected)

A **path key** is a sequence of 27-bit Fare-Octal chunks.  Each chunk
encodes into UC-Q via the draft's §1.3 blocks (6/7/7/7 bits → the four
quaternion coefficients; block values are the Fare squarefree products,
block traces are (weight, position-sum) Gaussian integers) — injective by
unique factorization (T2).  The **commitment** is the UC-Q product
T(P) = encode(s₀)·…·encode(s_L), hashed per sheet:

```
H_val = SHA-256(serialize(val(T)))     the value sheet (the result)
H_tr  = SHA-256(serialize(tr(T)))      the trace sheet (the history)
H     = SHA-256(H_val || H_tr)
```

Verification is the draft's five checks (length, recomputation, three hash
equalities — 2⁻⁷⁶⁸ for a random guess); one-shot mode adds a replay
registry (verifier state, honestly not algebra).  All arithmetic is exact
big-integer; **no floats anywhere in the scheme**.

## Proof by trial — the results that matter

**The bi-sheet design is load-bearing, proven by search (T7).**  In an
exhaustively enumerable 8-bit replica (65,536 ordered two-chunk paths),
the census found **three pairs of distinct paths with identical value
sheets and distinct trace sheets** — e.g. paths (20, 162) and (26, 86)
both give V = (−164, 212, −48, 76) but different D.  A value-only
commitment collides there; the bi-sheet H separates them.  The draft's
§3 "trace-visibility asymmetry" is not just composition reasoning — it
is *necessary*, and this code exhibits the witnesses.

**The draft's own arithmetic, corrected (C1–C7, exact witnesses in T3/T1):**

* **C1 (serious)** — §1.5's float64 serialization of UC-Q is non-injective:
  coefficients of any two-chunk path already exceed 2⁵³, so distinct
  elements serialize identically and the draft's `collapse` collides
  (witness: 2⁶⁰ vs 2⁶⁰+1).  Fixed: exact length-prefixed integer
  serialization.
* **C2** — §4's "UC-Q has no subtraction" is false; the monograph's claim
  is about the Fortress counting architecture.  What nilpotence gives:
  τ·Z depends only on val(Z) — multiplication by τ *annihilates*
  information (demonstrated).
* **C3** — §6.2's "adjacent swap changes T up to sign" is false in
  general (50/50 random pairs change T with no sign pattern); what holds:
  negating two chunks leaves T invariant, but such elements lie outside
  the encode image (all coefficients ≥ 0).
* **C4** — §7.3's (v+τt)² = v² + 2τvt assumes commutativity; correct:
  v² + τ(vt + tv), and vt ≠ tv in general.
* **C5** — §5's "128 bytes = 2048 bits" — it is 1024.
* **C6** — §2.2's no-consecutive-equal-trace constraint is not
  load-bearing (nothing annihilates on repetition; §7.3 itself concedes).
* **C7** — §1.1's commuted Leibniz form V₁D₂ + V₂D₁ fails (witness: +K
  vs −K); correct: V₁D₂ + D₁V₂.

**Order is bound by the value sheet itself (T6).**  All 11/11 adjacent
swaps and 30/30 permutations of a random path change the commitment —
quaternion non-commutativity hits V directly.  One structural
multi-preimage class exists (two chunks differing only in block *a* are
interchangeable under an adjacent swap — their difference is central),
documented and harmless for a preimage-resistant commitment.

**The compression honesty (T7), measured.**  65,536 two-chunk paths →
65,152 distinct T (1.006 paths per T): the map compresses, exactly as the
draft's corrected §6.1 concedes.  Path uniqueness comes from the hash
checks, not the algebra.  (The draft's "L ≥ 76" threshold arithmetic is
superseded: with exact serialization T is unbounded; there is no 2¹⁰²⁴
ceiling to overflow.)

**The norm shadow (T8).**  The value sheet's norm |V(P)|² = Π|V(sⱼ)|² is
multiplicative and permutation-invariant — an observer seeing the value
sheet *itself* could factor its norm and read off the multiset of chunk
norms (the order-blind shadow).  The commitment publishes only hashes, so
nothing leaks; the trace sheet has no such shadow.

## Layout

```
npcs/
├── ucq.py        the UC-Q algebra, exact: Gaussian-int complex
│                 quaternions, (V, τD) representation, Leibniz product,
│                 quaternion conjugate, multiplicative UC-norm, exact
│                 serialization (+ the draft's float64 kept only to
│                 demonstrate its flaw)
├── encode.py     Fare-Octal chunks -> UC-Q (blocks 6/7/7/7), the
│                 8-bit mini replica, chunking
├── scheme.py     path keys (draft §2.2 constraints), bi-sheet
│                 commitments, five-check verification, one-shot
│                 registry
├── trials.py     T1-T10 proof-by-trial battery -> NPCS_TRIALS.md
├── demo.py       the guided tour
└── __main__.py   CLI: trials / demo / keygen / commit / verify / info
fareoctal/        vendored v1.0.0 (the Fare-Octal project, unchanged)
tests/            22 unit tests (exact arithmetic throughout)
results/          NPCS_TRIALS.md (generated)
```

## Scope and honesty

This implements and *trials* what is combinatorially stated.  The
monograph's one-wayness conjecture is not proven here — it reduces to
SHA-256 preimage resistance on an exactly-serialized structured input
(the draft's §6.3 honest position, confirmed); quantum resistance remains
[OPEN] — a Grover adversary evaluates collapse ∘ T as a black box and
never simulates the algebra (the monograph's "superposition annihilates"
argument is algebraically true and cryptographically inert).  What the
nilpotent structure genuinely buys, and what this code demonstrates:
ordered bi-sheet commitments with an embedded self-auditing transcript,
and a second independent hash whose necessity is exhibited by explicit
witnesses.

## License

MIT (the code).  The monograph it implements is CC BY 4.0 (K. I. Kovlekov).
