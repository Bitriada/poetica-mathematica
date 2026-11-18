# BTC without AC

A computational model and verification of the case study
**“Banach–Tarski Without the Axiom of Choice”** — section 6.6 of the
monograph *Poetica Mathematica: Cogitatio ex Nihilo et Speculum
Scientiae* (Kirill I. Kovlekov, independent researcher, CC BY 4.0).

The monograph closes that section with an invitation: *“Fare-Riemann
sphere S³_FR admits a constructive decomposition (**verify it please**)
into three measurable domains, each homeomorphic to the full sphere,
with no Axiom of Choice required. The apparent ‘multiplication’ of
spheres is spectator-relative.”* This project is that verification,
turned into an executable model: every checkable claim of §6.6 (and of
Chapter IV §4.2 it rests on) is implemented, measured and reported.

---

## What the case study says, in one page

**BTC** is the monograph’s shorthand for the Banach–Tarski
phenomenon. Classically, a ball in ℝ³ decomposes into ~5 pieces that
rotations reassemble into two copies of itself; the proof needs the
free group F₂ and — to pick one representative from each of
uncountably many orbits — the Axiom of Choice (AC), with “no method”
for the selection.

The monograph’s alternative lives in the **Ultra-Complex numbers**
(Ch. IV): UC = ℂ[τ]/(τ²), elements Z = a + bi + τc + τdi with a
**value** val(Z) = a+bi and a **trace** tr(Z) = c+di, τ² = 0. The
**Fare–Riemann sphere** S³_FR = {‖Z‖_FR = 1} is a 3-sphere fibred over
the unit disc by the value map (Hopf-type; the fiber over v is the
circle {v + τs : |s|² = 1−|v|²}; the fiber over 0 is the **nadir
plane**).

Instead of F₂ + AC, the monograph uses the cyclic group C₃ generated
by the **triadic rotation** R(Z) = ω·val(Z) + τ·tr(Z), ω = e^(2πi/3),
which partitions the sphere constructively into three 120° wedges
D₀ ⊔ D₁ ⊔ D₂ — each of volume 1/3 — by a single angle test. No choice
is involved: “This is not a choice. This is structure.” (§6.6.6a).

The **spectators** (§6.6.1, §6.6.15; Ch. VII §6.3a) are the
observer model: each is a projection π_S onto a visible subspace
(π_ℝ sees only the interval [−1,1]; π_ℂ sees the value disc; the Deep
spectator sees value and trace). The **apparent sphere count** N_S
depends on the spectator: the Unfathoming one sees 1 sphere, the
Forward/Backward/Deep ones see 3. The **spectator shift** 1 ↔ 3 is the
“multiplication” — reversible bookkeeping, not volume replication. The
**ghost disc** D²_τ = {τs : |s| ≤ 1} carries 2 units of intrinsic
volume invisible to classical projections, and the accounting
V_int = 1 + 2 + 2 − 1 = 4 reconciles the books. The reassembly maps
φ_k (angle-tripling) turn each wedge into a full sphere.

The three interpretive conjectures of §6.6.14 (AC as the τ²→τ³ gate
key; the BT paradox as a spectator trap; AC as “sudo”) are documented
but not modeled — see the verification report.

## What this project does

| Module | Models | Monograph |
|---|---|---|
| `uc.py` | UC algebra (vectorized floats + exact `Fraction` variant), Leibniz product, inverse, trace payment | §4.2.1 |
| `sphere.py` | uniform sampler on S³_FR, Hopf fibers, nadir plane, C₃ and C₈ actions | §4.2.4, §4.4.3 |
| `triadic.py` | the §6.6.17 assignment algorithm, partition/volume/isometry/cycling verification | §6.6.3, §6.6.17 |
| `spectators.py` | projections π_ℝ/π_ℂ/π_τ, six-spectator registry, apparent counts N_S (computed from support overlaps, not hard-coded), spectator shift | §6.6.1, §6.6.6, §6.6.15, Ch. VII |
| `ghost.py` | ghost disc properties (nilpotence, invisibility, area π, V_int = 2), intrinsic-volume accounting | §6.6.15 |
| `reassembly.py` | φ_k and φ_k⁻¹ (base + fiber versions), trace payment, reassembly composition, virtual spheres | §6.6.5, §6.6.8, §6.6.15 |
| `classical.py` | F₂ words, 4-piece paradoxical decomposition, free rotation pair (arccos 3/5), orbit transfer, Følner ratios, AC-entry analysis, comparison table | §6.6.2, §6.6.7, §6.6.9 |
| `report.py` | claim registry (17 claims), console summary, Markdown verification report | §6.6.16 |

## Quick start

```bash
cd btc_without_ac
python -m pytest tests/ -q      # 44 tests, ~3 s (needs numpy, pytest)
python demo.py                  # narrated walkthrough + 6 figures + report
```

Output lands in `figures/` (PNG) and `VERIFICATION_REPORT.md`.
Only dependency: `numpy` (the demo additionally uses `matplotlib`).

## Results summary

**11 claims verified** (exact / constructive / Monte-Carlo), **1
verified with caveat**, **5 interpretive or not-computable-by-design**.
Highlights:

* **The constructive partition is real.** The §6.6.17 algorithm is a
  terminating O(1) function; measured volumes are 1/3 each to ~10⁻³
  (600k samples); the C₃ action is an exact isometry and cycles the
  domains. No choice anywhere.
* **Apparent counts are computed, not assumed.** N = 1 for the
  Unfathoming spectator (its π_ℝ-images of D₀ and D₂ are the *same
  interval* (−½, 1] — set-theoretically indistinguishable), N = 3 for
  Forward/Backward/Deep. The spectator shift 1 → 3 → 1 reproduces.
* **Ghost-disc accounting checks exactly**: ranks 1 + 2 + 2 = 5 > 4,
  corrected by the shared a-axis: 3 + 2 − 1 = 4.
* **The classical side is genuinely constructive — up to one step.**
  The 4-piece paradoxical decomposition of F₂ and its transfer to one
  explicitly chosen orbit need no choice; AC enters exactly at the
  transversal over uncountably many orbits. The Følner computation
  (|∂B_L|/|B_L| → 2 for F₂, → 0 for ℤ, trivially 0 for finite C₃) shows
  *why*: by Tarski’s theorem, non-amenability is equivalent to
  paradoxicality, so the amenable C₃ can never classically double a
  volume — the UC “multiplication” cannot be classical volume doubling,
  consistent with the monograph’s spectator-relative reading.

### Caveats found while verifying (and kept in the report)

1. **φ_k is a continuous bijection, not a homeomorphism** (§6.6.15):
   the wedge D_k is non-compact and φ_k⁻¹ is discontinuous across the
   seam — the [0,1) → S¹ phenomenon. It scales measure by exactly 3
   (piece 1/3 → image 1); the three “virtual spheres” coincide with
   S³_FR as sets and differ only by provenance labels. This sharpens,
   rather than breaks, the spectator-relative interpretation.
2. **The reassembly composition as literally written** (φ_k ∘
   φ⁻¹_{k_in}) is the identity; the glossed order (“expand then
   compress”, φ⁻¹_target ∘ φ_{k_in}) is the triadic rotation
   R^{target−k_in}. Both identities verified numerically.
3. **Two monograph tables disagree about N_Deep** (1 in §6.6.6, 3 in
   §6.6.15); the computation supports 3 (π_Deep sees the value angle).
4. **The inverse formula of Claim 4.2.1.2 is correct**, but the
   one-line proof printed next to it multiplies by the wrong conjugate.

## Repository layout

```
btc_without_ac/
├── btc_without_ac/          # the package (8 modules, see table above)
├── tests/                   # 44 pytest tests
├── demo.py                  # narrated pipeline -> figures + report
├── figures/                 # 6 PNG figures (generated)
├── VERIFICATION_REPORT.md   # full claim-by-claim report (generated)
├── README.md                # this file
└── pyproject.toml
```

## Sources

All mathematical content modeled here is from the uploaded monograph
*Poetica Mathematica* (Ch. IV §§4.2–4.4, Ch. VI §6.6, Ch. VII §6.3a,
Ch. IX Starshooting note). Standard background facts used by the code:
dual/Study numbers ℂ[τ]/(τ²); the Hopf fibration; the Banach–Tarski
theorem and its standard proof via F₂ (Wagon, *The Banach–Tarski
Paradox*); the free rotation pair with angle arccos(3/5)
(Swierczkowski 1958); Tarski’s theorem (paradoxical ⟺ non-amenable).
The monograph itself flags its Claims as proposals pending specialist
review; this project is exactly such a review, executed by machine.
