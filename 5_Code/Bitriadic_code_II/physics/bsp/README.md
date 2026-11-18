# bsp — Bitriada Stefan Projection: a validation workbench

A professional-grade tool for testing **BSP (Bitriada Stefan
Projection)** — the event-driven, "trace-driven time" solver for
moving-boundary phase-change (Stefan) problems proposed in the
*Poetica Mathematica* monograph — **on your own data**, against exact
analytical solutions, an independent industry-standard benchmark, and
your own measurements.

The design question this project answers: *is BSP a sound alternative
to classical Stefan solvers?* The tool does not presuppose the answer —
every claim the BSP paper makes that a computation can test is turned
into a check with a printed number and a verdict.

```
    your case file (TOML)  ──►  bsp run  ──►  events.csv   (the trace clock)
                                          ├─►  summary.json (all numbers)
                                          ├─►  report.md    (verdicts + tables)
                                          └─►  fig_*.png    (validation figures)
```

## Quick start

```bash
cd bsp_project
python -m bsp.cli run cases/water_ice_monograph.toml --out results/mono
python -m bsp.cli audit-monograph          # recompute the paper's own numbers
python -m bsp.cli presets                  # list material presets
python -m pytest tests/ -q                 # 27 tests, <10 s
python demo.py                             # full workflow incl. user data
```

Requirements: Python 3.11+, numpy, scipy, matplotlib (pytest for the
test suite). No other dependencies.

## Bring your own data

Write a case file (copy `cases/aluminum_freeze.toml` as a template):

```toml
[case]
name = "my_experiment"
mode = "freezing"       # or "melting"
T_m = 660.3             # melting point [C] (or K with temp_unit = "K")
T_s = 200.0             # boundary temperature at x = 0
T_0 = 660.3             # initial temperature of the bulk phase
length = 0.03           # domain length [m]
dx = 0.0005             # lattice spacing [m]
t_end = 120.0           # stop time [s]

[material]
# EITHER a preset (see `python -m bsp.cli presets`) ...
# preset = "aluminum"
# ... or your own measured properties (SI units):
rho = 2700.0            # density [kg/m^3]
L = 397000.0            # latent heat [J/kg]
k_grown = 237.0         # conductivity of the GROWING phase
cp_grown = 900.0        # specific heat of the growing phase
k_bulk = 237.0          # conductivity of the bulk phase (melt)
cp_bulk = 900.0

[run]
event_mode = "integral" # default; "explicit" = the paper's printed rule

[validation]
neumann = true          # compare to the exact analytical solution
enthalpy = true         # compare to an independent enthalpy benchmark
convergence = true      # dx -> 0 study (order of accuracy)
convergence_levels = 4
user_data = "data/my_measurements.csv"   # YOUR interface measurements
```

Measured interface data is a CSV with columns `t_s,s_m` (time in
seconds, front position in meters; header optional). The report then
grades BSP against your data with Neumann as reference:

```bash
python -m bsp.cli run my_case.toml --out results/mine --user-data data/exp01.csv
```

`data/example_measurements.csv` is SYNTHETIC (exact Neumann + 3 %
noise, seed 42) — it exists to demonstrate the workflow. Replace it
with your real experiment.

## What gets checked (each maps to a paper claim)

| check | paper claim | PASS criterion |
|---|---|---|
| `neumann_agreement` | Thm 12.1: events track s(t) = 2λ√(αt) | mean err < 10 % |
| `convergence` | Thm 12.1 in the dx→0 limit | order ≥ 0.7, errors decrease |
| `enthalpy_agreement` | — (independent benchmark, dx/4) | mean diff < 10 % |
| `energy_conservation` | Thm 13.2: E conserved per event + flux | drift < 5 % of one cell's latent |
| `second_law` | Thm 14.1: dS = k(∇T)²/T² dt ≥ 0 | dS ≥ 0, S monotone |
| `sharp_interface` | Prop 9.3 (τ²=0): no smearing | exactly 1 interface node |
| `trace_clock` | Prop 9.2: time from trace events | increasing, dt > 0, non-uniform |
| `null_transit` | monograph §2.7.1 axioms (see below) | fare ≈ ρLΔx, record complete, one-way |
| `boundary_set` | Prop 9.4: B = {p : c(p) ≠ 0} | exact front tracking |
| `uc_algebra` | §3: UC algebra, τ² = 0 | exact; Prop 3.2 deviation quantified |
| `lattice_counts` | §4: 117/243 lattices | counts + tables verified |
| `user_data` | — (your measurements) | RMS < 10 % |

Measured results on the three shipped cases (water/ice freezing,
aluminum freezing, ice melting): **convergence order 0.93–1.02**,
per-event energy drift 0.5–0.7 % of one cell's latent heat,
entropy monotone, interface exactly one node wide, and the transit
fare exact to the derived formula. The framework's operational core is
sound; see `results/audit/audit.md` for what needed correcting in the
paper's own arithmetic (below).

## Architecture

```
bsp/
  uc.py         UC algebra z = a + bi + τc + τdi (τ² = 0); the correct
                Leibniz product; Prop 3.2's printed formula kept
                verbatim for the audit
  lattice.py    1DB (117 = 9+27+81) and 2DB (243) lattices, value
                tables, and the finding that Algorithm 9.1 never uses them
  nodes.py      LAYERED node states + the null-transit machinery
  neumann.py    exact Neumann solutions (one-phase freezing/melting,
                two-phase), correctly derived transcendental equations
  solver.py     Algorithm 9.1: trace-driven event solver (single-pass
                crossing sweep; the paper's explicit rule kept as
                event_mode = "explicit")
  enthalpy.py   independent apparent-capacity enthalpy benchmark
  checks.py     the soundness suite + grid-convergence study
  monograph.py  the audit of the paper's own numbers
  cases_io.py   case files, material presets, user-data CSV
  report.py     report.md / summary.json / events.csv generation
  figures.py    validation, field/layers, and clock figures
  cli.py        the command line interface
cases/          example case files        data/  synthetic demo data
tests/          27 tests (pytest)         results/ pre-generated outputs
```

## The node-0 conflict and the null-transit resolution

Algorithm 9.1 starts by imposing the boundary condition AND the
interface marker at node 0 — the node must simultaneously be T_s (the
Dirichlet layer driving the heat flow) and T_m (the isotherm the bulk
sees). Pinning one scalar to both values collapses the field.

The resolution uses the monograph's **null-transit operator** (§2.7.1:
nilpotent, irreversible, trace-preserving state transitions) as a
dynamic layer model (`bsp/nodes.py`):

- during the first interval, node 0 is the **coincident state**: its
  value layer shows T_m to the diffusing field while its Dirichlet
  layer (the case parameter T_s) drives the event-1 gradient exactly
  as in paper §11.2;
- **Event 1 is the null transit**: the interface layer departs
  irreversibly to node 1, node 0's value layer switches to T_s, and
  the departure cannot repeat (nilpotence: each node transits at most
  once) and never returns (irreversibility);
- the departure leaves a **trace**: the coupling layer d = 1 on every
  visited node, and pays a **fare**: exactly the first cell's latent
  heat ρLΔx plus the boundary-cell chill — measured in every run
  (check `null_transit`), O(Δx), vanishing in the continuum limit.

## Event rules: what the paper prints vs. what runs

The paper's STEP 3 as printed (`dt = Δx / v` with v from the current
field) **cannot run on its own field**: right after any transit the
just-released interior node still sits at T_m, so the start-of-
interval velocity is zero and the rule stalls after two events. The
paper's appendix tables were built by hand-feeding Neumann-profile
gradients (its own sec. B.2: "Approximating the temperature decay
from the Neumann profile") — reproduced by `--event-mode explicit` in
this package.

The default `integral` mode is the self-consistent realization of
"advance to the next trace event": the field evolves (STEP 1), the
Stefan velocity is re-evaluated on the evolving field (STEP 2), and
the event fires when the integrated front advance reaches Δx (a
single-pass sweep with a partial final substep; crossing residuals
are logged per event). This converges to the exact Neumann solution
with order ≈ 1.

## Audit of the paper's own numbers (`python -m bsp.cli audit-monograph`)

The paper validates BSP on water/ice freezing (T_s = −10 °C). Recomputed:

| item | paper | correct |
|---|---|---|
| λ-equation | e^{−λ²}/erf(λ) = L√π/(c_p ΔT) | λe^{λ²}erf(λ) = Ste/√π (factor λ missing) |
| λ for their case | 0.15 | **0.2453** |
| α with their k, ρ, c_p | 1.15×10⁻⁶ | 5.26×10⁻⁷ (they mix water and ice tables) |
| dt₁ | 15.2 s | 15.18 s — **correct, reproduced exactly** |
| event tables | §12.2 vs. appendix B.2 disagree by 10× | neither reproducible by the printed algorithm |
| "within 2 %" at t = 1000 s | vs. wrong-λ Neumann | faithful BSP is **2.2 %** from the correct value |

Verdict: four independent arithmetic errors in the paper's validation;
none invalidates the method — the faithful BSP run converges to the
correct Neumann solution (order ≈ 1), which **supports the framework
while contradicting the paper's numbers**. Prop 3.2's multiplication
formula also deviates from the algebra it defines (missing −bd′−b′d,
sign flip); `bsp.uc` implements the correct product.

## Honest limitations and adopted readings

- One-dimensional, single-front problems (the paper's own scope);
  boundary conditions: constant T_s at x = 0, initial T_0 held at x = L.
- The UC b and d components and the 2DB-SP layer have roles but no
  evolution laws in the paper; the readings used here are marked
  ADOPTED in the code and reports (b = phase sign, d = visited record,
  q₀/q₂/τ₁/τ₂ = energy/entropy/event-production/event-count).
- The 117/243 Bitriada lattices are verified but not load-bearing:
  Algorithm 9.1 runs on a plain uniform lattice (a finding, reported).
- Material presets are typical handbook values — override with your
  own measurements for critical work.
- Figures in `results/` were verified programmatically (size,
  non-blank content); regenerate any of them with the commands above.
