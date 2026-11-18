# The QDME Experimental Program

**Project:** QDME-bs v1.1 -- experimental layer  
**Goal:** convert the workbench's (mat) findings into testable empirical claims, with each protocol's discriminating power stated honestly.

**Generated:** 2026-11-15T16:37:05  
**Runtime:** 14.6 s (all simulations seeded)

---

## The program at a glance

| # | protocol | platform | discriminating power | verdict | timeframe |
|---|----------|----------|---------------------|---------|-----------|
| 1 | C_8 winding constraint | two-level, engineered symmetry | none (operationally = standard symmetry covariance) | CONSISTENCY CHECK | near-term |
| 2 | **memory-kernel sqrt(8) sector rigidity** | qutrit, structured environment | **genuine** (unsolicited triangle equality) | **DISCRIMINATING** | medium-term |
| 3 | birth-death / Lambda | monitored qubit | none (degenerate with thermal GKLS) | NOT DISCRIMINATING (corrected) | long-term |
| 4 | trace-clock T2 | any qubit | none (by construction) | SANITY CHECK | immediate |

**Bottom line:** the program stands on ONE discriminating protocol -- the qutrit triangle equality Omega_max = Omega_mid + Omega_min with the common sqrt(8) factor.  Everything else the v1.1 brief proposed survives only as consistency checks, with the birth-death contrast corrected (it is standard thermal fluorescence, not a QDME-vs-GKLS dichotomy).

---

## Protocol 1 -- C_8 winding constraint (near-term)

- Platform: two-level system, C_8-engineered environment (U = diag(1, e^{i pi/4}))
- Prediction: covariant channels generate |rho_01| = 0.0e+00 from a diagonal state; the mixed-winding control generates 0.276.
- Detection: 118 shots detect the control-arm coherence at 3 sigma; the 3-sigma noise floor at 10k shots is 0.015.
- d>=9 subtlety: a Delta-m = 8 transition is C_8-covariant (True) but U(1)-covariant (False) -- the one operational difference between the discrete and continuous readings, set by the engineered symmetry identically in both frameworks.
- Falsification of the READING: measured |rho_01| above the 3-sigma threshold under process-tomographed single-winding channels.
- Discriminating power: NONE at the framework level: winding-graded covariance is operationally equivalent to standard symmetry-covariant channel theory; standard GKLS with the same symmetric environment predicts the same zero coherence
- **Verdict: CONSISTENCY CHECK (not framework-discriminating)**

## Protocol 2 -- memory-kernel sqrt(8) sector rigidity (medium-term) -- THE discriminating test

- Signature: Omega_ab = sqrt(8)|k_a - k_b|: the three qutrit sector kernel frequencies are sqrt(8) x pairwise differences of ONE spectrum -> triangle equality Omega_max = Omega_mid + Omega_min
- sqrt(8) = 2.828427 (from theta^3 = 8 theta, the chiral eigenpair +-2 sqrt(2), K6)
- Simulated theta-chain arm: fitted sector frequencies 2.546 +- 0.031; 3.682 +- 0.024; 6.220 +- 0.021; rigidity residual R = -0.0071 vs 3sigma_R = 0.1601 -> consistent: True
- Simulated standard arm (independent detunings): fitted 2.548 +- 0.026; 3.676 +- 0.029; 4.602 +- 0.024; z-score -32.4 -> REJECTED
- Power (standard-arm rejection vs noise level): sigma=0.01: z=-75.5; sigma=0.02: z=-31.3; sigma=0.05: z=-10.2; sigma=0.1: z=-6.0; sigma=0.2: z=-3.4 (discriminates up to ~20% noise)
- Secondary signature: fitted phases phi_ab ~ 0 (pure cosine) and a shared damping gamma across sectors
- Falsification: |R| > 3 sigma_R rejects the theta-chain reading of the specializations-table rows 3-4 for that system
- Caveats: (i) the kernel is the K6 construction; (ii) a fine-tuned standard environment can mimic the rigidity (statistical, not logical, discrimination); (iii) needs d >= 3 -- for a qubit the sqrt(8) is absorbable into K
- **Verdict: DISCRIMINATING PROTOCOL (simulation: theta-chain arm consistent, standard arm rejected)**

## Protocol 3 -- birth-death / Lambda (long-term, corrected)

- Platform: continuously monitored qubit (fluorescence), beta = 0.80, mu = 0.50, T = 8.0
- Exact count statistics: mean 5.065, variance 5.013, Fano 0.9897 (NOT Poisson: the intensity is state-dependent)
- Balanced case (beta = mu): Fano 1.0000, TV to Poisson 4.05e-16 (Poisson exactly)
- Degeneracy: standard quantum-jump fluorescence over 30000 trajectories gives TV = 0.0117 to the exact distribution (3-sigma bound 0.0781): same_statistics = True
- Statement: the carry-reading value-tier dynamics IS the thermal GKLS generator; its non-Poisson statistics are standard finite-temperature fluorescence, not a QDME signature
- What would discriminate: an observable attached to the Lambda-record tier -- the container does not provide one (records are gauge, universality/faithful.py); speculating beyond this is (par)-adjacent
- **Verdict: NOT DISCRIMINATING as formulated (corrected analysis); long-term speculative**

## Protocol 4 -- trace-clock T2 (immediate, sanity only)

- T2 from the trace-clock ensemble: 2.0088 vs reference 2.0000 (relative deviation 0.440%; within MC error -- v1.0's 0.5% gap is noise, as the brief suspected)
- Ensemble-vs-GKLS errors: {'amplitude damping': 0.005762203978366465, 'phase damping': 0.008829306783582846, 'MC 4-sigma bound': np.float64(0.044721359549995794)}
- Pooled event rate (MC, exact): (0.120625, np.float64(0.11990472450270423))
- Discriminating power: NONE: standard GKLS makes the same prediction; the trace-clock reproduces standard QM (as K4/Issue 11 established)
- **Verdict: CONSISTENCY CHECK (not discriminating; sanity only)**

---

## The order of operations (updated from the brief)

1. ~~Close the derivation~~ -- DONE (DERIVATION.md; the convention is the unique survivor of four stated requirements).
2. Write the C_8 protocol -- done here, with the corrected verdict (consistency check, near-term, cheap: run it first as the fastest falsifier of the winding reading).
3. **Prioritise the qutrit kernel protocol** -- the only genuinely discriminating experiment; medium-term; needs a structured-environment qutrit with three addressable sectors and kernel tomography at <= 5% noise.
4. Birth-death -- retain only as a corrected long-term proposal; the Poisson contrast in the brief does not survive analysis.
5. Trace-clock -- sanity check, executed, closed.

## Register notes

- The discriminating content of Protocol 2 is a prediction of the K6 CONSTRUCTION (the monograph never writes the kernel); confirming the triangle equality would support the construction, not prove monograph intent: (res) boundary.
- Protocol 3's Lambda-record speculation is (par)-adjacent and marked as such.
- No (res) claim in this program is rendered as a framework-level empirical fact.
