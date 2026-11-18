# QDME-bs — Quantum Dynamics Master Equation Bitriadic solver

**v1.1** — verification project for **Theorem 8.1 (Unified Quantum Master Equation)** and its
specializations table in *Poetica Mathematica: Cogitatio ex Nihilo et Speculum
Scientiae* (Kirill I. Kovlekov, CC BY 4.0), chapter “Bitriada Quantum Dynamics:
A Complete Framework”:

```
d(rho_hat)/dt = -i[H, rho] - i*tau*[Gamma, rho] - i*theta*[K, rho] + Lambda . E[rho]

Active terms              ->  Named equation        (DB level)
H only                    ->  Schrödinger           (1DB)
H, Gamma, tau^2 = 0       ->  Lindblad              (2DB)
H, Gamma, K, theta != 0   ->  Non-Markovian         (3DB–4DB)
all terms                 ->  Evolutionary          (5DB)
```

The project follows the monograph’s own verification standard (*“productivity,
checkability, honesty, illumination … test the outputs that this monograph
provides”*) and its three-register discipline (sec. 3.5.6):

* **(mat)** conjectured identities — verified or falsified here, with numbers;
* **(res)** structural resonances — characterized, never rendered as proven;
* **(par)** poetic parables — listed, not tested.

## Quick start

```bash
pip install -e . --no-deps
pip install numpy scipy sympy pytest

qdme-bs verify --seed 2026          # K1-K8 kill tests (~40 s, 10^5 sweep included)
qdme-bs derive                      # the physicality-convention derivation (exact)
qdme-bs experiments                 # the four experimental protocols (simulated)
qdme-bs verify --seed 2026 --quick  # reduced verify run (~15 s)
pytest                              # unit + integration tests
python demo.py                      # the whole story in ~20 s
```

Everything runs from the single seed; `verify` writes
`results/VERIFICATION_REPORT.md` (+ JSON), `derive` writes
`results/DERIVATION.md`, `experiments` writes
`results/EXPERIMENTAL_PROGRAM.md`.

## What this project is

A **falsification harness** for the (mat) content of Theorem 8.1: eight kill
tests (K1–K8), a resolution dossier for the twelve open issues of the project
specification, an exact-algebra layer (Fractions, zero floating-point doubt),
a dynamics layer (the tier container: value / τ-record / θ-memory / Λ-record),
a literal implementation of Algorithm 4.1 (trace-driven evolution), and a
10⁵-instance universality sweep — all under enforced register discipline
(no (res) claim is ever rendered as (mat); enforced by `verification/registers.py`).

### The verdicts (seed 2026, full run)

| id | test | verdict |
|----|------|---------|
| K1 | τ-centrality gate (Issue 2) | **PASS** (exact; Grassmann reading fails; free reading infinite-dimensional) |
| K2 | unified equation well-posedness | **PASS** (1000/1000 unique flow) |
| K3 | Schrödinger specialization (Thm 2.2) | **PASS** (worst error 5.6e-16, tol 1e-12) |
| K4 | Lindblad specialization (Thm 2.4) — **load-bearing** | **PASS with documented obstruction** (see below) |
| K5 | C₈ constraint (Issue 4) | **PASS** (winding-graded covariance identified; sector-block-diagonal reach) |
| K6 | memory kernel (Thm 2.6) | **PASS** (exact kernel identity 2e-15; pseudomode cross-check 2e-16) |
| K7 | Λ problem (Issue 6) | **VACUOUS (literal) / NONVACUOUS (carry reading (d))** |
| K8 | universality sweep (Issue 10) | **PASS** (10⁵ instances, machine precision, reading (a) SUPPORTED) |

### The central honest finding

The literal Thm 8.1 commutators are **well-posed and internally consistent**
(K1/K2), but the nilpotent/graded terms **never lower tier**: the value-tier
flow of the bare equation is purely Hamiltonian — an *exact structural zero*
(the dissipator coefficient is identically 0 for every Γ). Consequently each
row of the specializations table beyond row 1 holds **only through the
monograph’s own trace-event mechanism** (Alg. 4.1 / sec. 8.2 “time emerges
from trace events”):

* **Lindblad row** — the (H,Γ)↦GKLS map (never written in the monograph;
  Issue 3) is constructed via the event feed and reproduces GKLS to 1e-10 on
  100 random generators over t∈[0,10]; the naive projection (R1) and adiabatic
  elimination (R2) routes fail on the literal equation, with the exact break
  points documented (the missing term is precisely the λ-deformation
  τ_λ²=(1−λ)ε of Addendum XXIV).
* **Non-Markovian rows** — the memory kernel (never specified; Issue 5) is
  constructed from the θ-chain: k(t) = −ηC²e^{−γt}cos(√8·C·t); the chiral pole
  pair ±2√2 is **forced** by θ³=8θ; verified exactly and against a damped
  Jaynes–Cummings pseudomode.
* **Evolutionary row** — Λ=τ³ is identically 0 in every τ²=0 algebra (exact),
  so the row is vacuous literally; under the carry extension
  Λ∈ℍ[τ,Λ]/(τ²,Λ²,τΛ) it is non-vacuous, with exact birth-death dynamics and
  the record semantics Λ-record = ρ(t)−ρ(0).

With the constructed feeds, **10⁵ random QDMEs across all four classes encode
as specializations of the single equation** at machine precision (K8, reading
(a)); the strong “single context” reading (b) remains (res) beyond the swept
families.

### v1.1 — The derived physicality convention (`qdme-bs derive`)

The v1.0 convention is now **derived, not designated** (`results/DERIVATION.md`):

* **Step 1 (exact):** all *-structures on UC = ℂ[τ]/(τ²) extending complex
  conjugation form exactly the U(1) family τ\* = λτ, |λ| = 1 (τ\* must be
  square-zero → pure trace; involutivity → |λ| = 1; verified exactly over ℚ(i)
  at λ ∈ {1, −1, i, (3+4i)/5, (5+12i)/13}).  The θ-generator’s gauge is **ℤ₂
  only** (θ³ = 8θ forces μ³ = μ) — only the nilpotent τ carries a continuous
  gauge.  Monograph context: the perspectival algebras UC1–UC3 and the UC4
  loop closure (§3.4.2–3.4.4), which itself forces i² = −1 and τ² = 0.
* **Steps 2–3 (exact witnesses):** four physical requirements — real record,
  self-adjoint state, probability conservation, \*-positivity — reduce the
  family to a **unique survivor** (1 of 10 candidate rows): τ\* = τ; ρ, σ
  Hermitian; Tr ρ = 1, Tr σ = 0; ρ ⪰ 0.  Every alternative fails a stated
  requirement with an exact witness.
* **Step 4 (theorems, not choices):** the value tier of any sum of squares is
  the Gram matrix A†A — **PSD for every gauge λ**; and any Hermitian record
  (indefinite included) is realizable as one — so \*-positivity forces ρ ⪰ 0
  and constrains nothing else.  Bonus exact fact: the record of a square is
  Hermitian only for λ = +1.

Register note: the derivation is (mat); the claim that the four requirements
are what the author intended is (res) — the monograph never states an
involution.

### v1.1 — The experimental program (`qdme-bs experiments`)

Four protocols, simulated with power analyses
(`results/EXPERIMENTAL_PROGRAM.md`), ranked by honest discriminating power:

| # | protocol | discriminating power | verdict |
|---|----------|---------------------|---------|
| 1 | C₈ winding constraint (two-level, near-term) | none — operationally equivalent to standard symmetry covariance | CONSISTENCY CHECK |
| 2 | **memory-kernel √8 sector rigidity** (qutrit, medium-term) | **genuine** — Ω_ab = √8·\|k_a−k_b\| forces the triangle equality Ω_max = Ω_mid + Ω_min, unsolicited by standard theory (three independent detunings) | **DISCRIMINATING** |
| 3 | birth–death / Λ (monitored qubit, long-term) | none at the value tier — the carry dynamics **is** thermal GKLS; the Poisson contrast in the brief applies only to single-channel GKLS; the Λ-record is gauge | NOT DISCRIMINATING (corrected) |
| 4 | trace-clock T₂ (immediate) | none by construction | SANITY CHECK |

Simulated: the θ-chain arm satisfies the triangle equality within noise
(R = −0.007 vs 3σ = 0.16) while the standard arm is rejected at z = −32, with
discriminating power surviving to ~20% measurement noise.  The program’s
order of operations: run the cheap C₈ consistency test first (fastest
falsifier of the winding reading), prioritise the qutrit kernel test (the
only genuinely discriminating experiment), retain birth–death only as a
corrected long-term proposal.

### Other resolved issues (see the report for all twelve)

* **Issue 1 (12D vs 16D):** both counts are correct for different objects —
  T₈ (12D, commutative, the τ/θ memory layer) and UC-Q = ℍ⊗ℝ UC (16D, the
  quaternionic layer, monograph sec. 6.2.8); the join is the Gate algebra
  ℍ⊗T₈ (48D), containing both plus ℍ[τ]/(τ²) (8D) via exact multiplicative
  embeddings. Note: “ℍ[τ]/(τ²)” with τ central is 8D, not 16D.
* **Issue 12 (does Epoch 5 contain j,k?):** no — the only square roots of −1
  in UC are exactly ±i (sympy-solved over ℚ); the i↦j differential is genuine
  emergence (φ/ψ are linear isomorphisms but NOT homomorphisms — exact
  witnesses of Remark 2.16c).
* **Issue 11 (trace-clock):** Algorithm 4.1, implemented literally, reproduces
  standard decoherence times within Monte-Carlo error (event-driven ensemble
  matches GKLS; T₂ from the trace-clock ensemble = 2.011 vs 2.000 reference).
  The “inverts standard QM” reading is (res).

## What this project is not

* It is **not** a proof of Theorem 8.1 in any accepted formal sense; it is a
  computational verification/falsification of the (mat) content, exactly as
  the monograph’s introduction requests (“test the outputs”).
* It does **not** test the (par) register (gearshift metaphor, life/death as
  language, Emperor/Trickster agents) — these are listed and left in register.
* It does **not** claim the constructed maps ((H,Γ)↦GKLS, K(θ), the carry
  reading) are what the author intended; each is documented as a
  construction filling a monograph gap, with the gap cited.  (The physicality
  convention, by contrast, is v1.1-DERIVED — but from four requirements the
  monograph itself never states; the attribution of those requirements to
  the author remains open.)
* It does **not** verify the (res) reading of “single context” beyond the
  swept families; no (res) claim appears with a PASS/FAIL verdict anywhere.
* It is not a physics engine: d=2–3 systems, exact and small by design.

## Layout

```
qdme_bs/
├── algebra/          exact algebras: ℍ, ℍ[τ]/(τ²) (8D), UC-Q=ℍ⊗UC (16D),
│                     T₈ (12D), Gate ℍ⊗T₈ (48D), CARRY (56D), K1 centrality,
│                     Issues 1, 2, 6, 9, 12
├── derivation/       v1.1: the *-structure family (U(1) for τ, ℤ₂ for θ),
│                     four requirements, exact-witness enumeration ->
│                     the physicality convention DERIVED (Issue 7)
├── state/            tier container: lift/project, physicality (Issue 7),
│                     trace/CP per term (Issue 8)
├── unified/          Thm 8.1 superoperator (bare / event / deformation /
│                     carry feeds), Thm 5.2, well-posedness (K2)
├── specializations/  the four table rows: Schrödinger (K3), Lindblad (K4,
│                     three routes), C₈ (K5), memory (K6), birth-death (K7)
├── algorithm/        Algorithm 4.1 literal (trace-driven), event clock (K11)
├── universality/     10⁵ sweep (K8), faithfulness, reachable set
├── experiments/      v1.1: the experimental program -- C₈, kernel √8
│                     sector rigidity, birth-death, trace-clock; each with
│                     simulation, power analysis, honest verdict
├── verification/     kill tests K1–K8, twelve-issue dossier, register
│                     discipline + lint, report generator
└── cli.py            qdme-bs verify / derive / experiments

btc_without_ac/       the PINNED sub-algebra reference (UC = C[τ]/(τ²), 4D),
                      vendored byte-identical, wrapped — never modified:
                      UC is 4D, UC-Q is 16D; do not conflate.
tests/                unit + integration tests, incl. the spec's literal
                      first test tests/test_caveat_c1.py (the K1 gate)
results/              VERIFICATION_REPORT.md, DERIVATION.md,
                      EXPERIMENTAL_PROGRAM.md + JSON (generated)
```

## Dependencies

Python ≥ 3.11, numpy, scipy, sympy (pytest for the test suite). No other
dependencies; everything is deterministic under `--seed`.

## License

The verification code is MIT. The vendored `btc_without_ac` retains its own
notice; the monograph it verifies is CC BY 4.0 (K. I. Kovlekov).
