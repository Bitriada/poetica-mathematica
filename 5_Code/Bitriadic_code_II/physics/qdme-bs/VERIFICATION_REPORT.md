# QDME-bs Verification Report

**Project:** QDME-bs -- Quantum Dynamics Master Equation Bitriadic solver  
**Target:** Theorem 8.1 (Unified Quantum Master Equation) and its specializations table, *Poetica Mathematica* (K. I. Kovlekov, CC BY 4.0), chapter "Bitriada Quantum Dynamics: A Complete Framework"

**Generated:** 2026-11-15T16:37:49  
**Seed:** 2026  
**Mode:** FULL  
**Runtime:** 40.4 s  
**Platform:** Python 3.12.16, Linux

---

## Executive summary (the honest verdict)

Theorem 8.1 as literally written,

    d(rho_hat)/dt = -i[H, rho] - i tau [Gamma, rho] - i theta [K, rho] + Lambda . E[rho],

is **well-posed** (K2) and **internally consistent** (the three-term form equals Addendum XXIV's single-commutator restatement exactly, because tau and theta are central -- K1). Its specializations table holds **row by row only through the monograph's own trace-event mechanism** (Alg. 4.1 / sec. 8.2): the bare nilpotent commutators never feed the value tier (an exact structural zero, established in K4-R1/K4-R2), so each dissipative/memory/evolutionary row requires its constructed feed -- the event feed (Lindblad), the deformation feed (memory), the carry feed (birth-death).  With those feeds, every row is reproduced at machine precision, and 10^5 random QDMEs across all four classes encode as specializations of the single equation (K8).  The 5DB row is vacuous on the literal reading of Lambda = tau^3 (it vanishes identically) and non-vacuous under the carry extension (K7).

**Kill-test verdicts:** K1 PASS, K2 PASS, K3 PASS, K4 PASS (with documented obstruction), K5 PASS, K6 PASS, K7 VACUOUS (LITERAL) / NONVACUOUS (CARRY), K8 PASS.

---

## Kill tests K1-K8 (register: mat)

| id | test | verdict |
|----|------|--------|
| K1 | tau-centrality gate (Issue 2) | **PASS** |
| K2 | unified equation well-posedness | **PASS** |
| K3 | Schrodinger specialization (Thm 2.2) | **PASS** |
| K4 | Lindblad specialization (Thm 2.4) -- LOAD-BEARING | **PASS (with documented obstruction)** |
| K5 | C_8 constraint identified (Issue 4) | **PASS** |
| K6 | memory kernel construction (Thm 2.6) | **PASS** |
| K7 | Lambda problem / 5DB row (Issue 6) | **VACUOUS (LITERAL) / NONVACUOUS (CARRY)** |
| K8 | universality sweep (Issue 10) | **PASS** |

### K1 -- tau-centrality gate (Issue 2)

**Verdict:** PASS  
tau commutes with i, j, k exactly in H[tau]/(tau^2), UC-Q (16D) and the Gate (48D); the Grassmann reading fails; the free reading is infinite-dimensional.  Monograph-internal evidence: Addendum XXIV's single-commutator restatement forces centrality.

<details><summary>metrics</summary>

```
- **centrality**:
  - **H[tau]/(tau^2)**:
    - i: True
    - j: True
    - k: True
    - random x (50 draws): True
  - **UC-Q = H (x) UC (16D)**:
    - i: True
    - j: True
    - k: True
    - i_c (UC imaginary): True
    - random x (50 draws): True
  - **Gate H (x) T_8 (48D)**:
    - [tau, i] = 0: True
    - [theta, i] = 0: True
    - [tau, j] = 0: True
    - [theta, j] = 0: True
    - [tau, k] = 0: True
    - [theta, k] = 0: True
    - [tau, theta] = 0: True
    - [theta, theta] = 0: True
  - **T_8 (commutative)**:
    - [tau, i] = 0: True
    - [tau, theta] = 0: True
  - verdict: PASS
- **single_commutator_evidence**:
  - forms_equal_exact (10 random draws): True
  - reduction: [H + tau G + theta K, R] - [H, R] - tau[G, R] - theta[K, R] = -( [R, tau] G + [R, theta] K ); vanishes iff tau, theta commute with the state
  - conclusion: Addendum XXIV's single-commutator restatement of Thm 8.1 is equivalent to the three-term form IFF tau and theta are central: the monograph itself commits to the central reading
- **negative_controls**:
  - **grassmann_reading (tau q = -q tau equiv q tau = tau q̄)**:
    - [tau, i]: NONZERO (2 tau i)
    - [tau, j]: NONZERO (2 tau j)
    - [tau, k]: NONZERO (2 tau k)
  - grassmann_verdict: FAILS K1: tau is not central
  - free_reading: the algebra <i, j, k, tau | i^2 = j^2 = k^2 = ijk = -1, tau^2 = 0> with no commutation rule for tau is the free product H *_R R[tau]/(tau^2); by the normal-form theorem for free products it is infinite-dimensional (al...
  - conclusion: Centrality is not automatic: it must be (and is) built in via the tensor product H (x) UC.  The Grassmann reading fails the gate exactly; the free reading cannot even match the monograph's dimension counts.
- verdict: PASS
- register: mat
```
</details>

### K2 -- unified equation well-posedness

**Verdict:** PASS  
1000/1000 random parameter sets give a unique flow (finite generator, computable propagator on [0,10]).

<details><summary>metrics</summary>

```
- n_params: 1000
- n_unique_flow: 1000
- worst generator 2-norm (Lipschitz): `4.479e+01`
- worst |exp(10 G)| entry: `8.218e+01`
- value-tier GKLS blocks stable (Re lam <= 0): `1.000e+00`
- verdict: PASS
- note: well-posedness = unique flow; container growth from the chiral theta-mode is structural (theta^3 = 8 theta) and does not affect the physical value-tier projections
```
</details>

### K3 -- Schrodinger specialization (Thm 2.2)

**Verdict:** PASS  
20 random draws, worst error 5.59e-16 (tolerance 1e-12); record tiers stay exactly zero (tau introduced, not activated).

<details><summary>metrics</summary>

```
- n: 20
- n_pass: 20
- worst error: `5.590e-16`
- verdict: PASS
- statement: H only: the unified equation's value tier reproduces Schrodinger evolution to < 1e-12; row 1 of the specializations table VERIFIED (mat)
```
</details>

### K4 -- Lindblad specialization (Thm 2.4) -- LOAD-BEARING

**Verdict:** PASS (with documented obstruction)  
R1 naive projection: FAILS (dissipator coefficient identically zero -- exact nilpotent obstruction).  R2 adiabatic elimination: FAILS on the literal equation (the required back-reaction term -i delta [Gamma, sigma] is absent; it is exactly the lambda-deformation).  R3 trace-event mechanism (Alg 4.1 / sec 8.2, ensemble limit): PASSES to 1e-10 over t in [0,10] on 100 random GKLS generators; construction faithful.  Table row 2 is TRUE in the event-driven reading, FALSE in the naive algebraic reading.

<details><summary>metrics</summary>

```
- **R1_naive_projection**:
  - route: R1: value projection of the literal equation
  - max dissipative Tier-0 coefficient (20 draws): `0.000e+00`
  - verdict: FAIL
  - break_point: the nilpotent terms never lower tier: the GKLS dissipator cannot appear at Tier 0 for ANY choice of Gamma (exact structural zero)
- **R2_adiabatic_elimination**:
  - route: R2: adiabatic elimination of the record tier
  - max |value flow - Hamiltonian| over mu scalings: `2.224e-16`
  - verdict: FAIL (on the literal equation)
  - break_point: elimination needs a sigma -> rho back-reaction term; the literal Thm 8.1 contains none (feed matrix exactly zero).  The missing term is -i delta [Gamma, sigma], delta = tau^2: exactly the lambda-deformation of Addendu...
- **R3_event_ensemble**:
  - route: R3: trace-event mechanism (Alg. 4.1 / sec. 8.2), ensemble limit
  - n_gkls: 100
  - d: 2
  - **t_window**:
    - 0.0
    - 10.0
  - worst |value projection - GKLS reference|: `4.806e-15`
  - tolerance: `1.000e-10`
  - verdict: PASS
- **faithfulness**:
  - n_pairs: 30
  - n_distinct_projected_dynamics: 30
  - note: accidental coincidences can occur on measure-zero sets (e.g. both channel sets empty); the construction is generically injective
- verdict: ROW 2 of the specializations table: TRUE in the event-driven reading (R3 PASS, worst err 4.81e-15); FALSE in the naive algebraic reading (R1 exact obstruction).  The (H, Gamma)->GKLS map is a CONSTRUCTION (monograph g...
- register: mat
```
</details>

### K5 -- C_8 constraint identified (Issue 4)

**Verdict:** PASS  
Reading: winding-graded covariance U L U^dag = omega^m L; single-winding channels give invariant dissipators (defects ~1e-17), mixed channels break invariance; standard damping channels are covariant; invariant dynamics is winding-sector-block-diagonal (reach characterized).

<details><summary>metrics</summary>

```
- reading: winding-graded covariance U L U^dag = omega^m L
- **invariance_defects**:
  - sigma_- (w -1): `5.850e-17`
  - sigma_+ (w +1): `4.117e-17`
  - n = |1><1| (w 0): `0.000e+00`
  - mixed sigma_- + n (w -1 + 0): `4.074e-01`
- **standard_channel_windings**:
  - sigma_- winding: 1
  - sigma_+ winding: 7
  - n winding: 0
- **hamiltonian_commutant**:
  - diagonal H: [H,U]: `0.000e+00`
  - off-diagonal H: [H,U]: `1.082e+00`
- **sector_transfer**:
  - covariant: coherence generated from diagonal state: `0.000e+00`
  - mixed: coherence generated from diagonal state: `2.433e-01`
  - interpretation: covariant dynamics preserves the winding sectors of the state (no w0 -> w+-1 transfer); mixed channels break the grading
- verdict: C_8 constraint IDENTIFIED: single-winding channels + commutant Hamiltonians; K4's standard channels (amplitude/phase damping) satisfy it; invariant dynamics is winding-sector-block-diagonal
```
</details>

### K6 -- memory kernel construction (Thm 2.6)

**Verdict:** PASS  
The kernel is CONSTRUCTED from the theta-chain (Issue 5): k(t) = -eta C^2 e^{-gamma t} cos(sqrt(8) C t); the pole structure {0, +-2 sqrt 2} is forced by theta^3 = 8 theta.  Verified exactly (Laplace identity + augmented ODE, ~1e-15) and against the damped Jaynes-Cummings pseudomode (two independent exact implementations, ~1e-16); Markovian limit recovers GKLS at adiabatic accuracy.

<details><summary>metrics</summary>

```
- construction: theta-chain with back-coupling eta and record damping gamma; kernel poles forced by theta^3 = 8 theta (chiral pair +-2 sqrt 2)
- (a1) Laplace kernel identity (exact): `2.220e-15`
- (a2) augmented-ODE vs tier-ODE (exact): `4.136e-15`
- (a3) product quadrature at n=600 (O(h)): `1.495e-05`
- (b-exact) pseudomode: direct 2x2 vs 4-level Lindblad: `2.220e-16`
- (b-quad) pseudomode: Volterra quadrature vs direct: `8.220e-04`
- (c) Markovian limit vs GKLS (adiabatic): `1.984e-04`
- tolerance: `1.000e-10`
- verdict: PASS
- note: (a1)/(a2) verify the constructed theta-kernel exactly (Laplace identity + augmented ODE vs the Thm 8.1 tier ODE); (a3) is the first-order quadrature convergence check; (b) the exponential subfamily is verified by two ...
```
</details>

### K7 -- Lambda problem / 5DB row (Issue 6)

**Verdict:** VACUOUS (LITERAL) / NONVACUOUS (CARRY)  
Literal reading: Lambda = tau^3 = 0 identically in every tau^2 = 0 algebra (exact) -- the 5DB row is vacuous.  Carry reading (d): Lambda . E[rho] != 0, birth-death dynamics exact (p1 error 0), Lambda-record = rho(t)-rho(0); stochastic BD moments match within MC error.

<details><summary>metrics</summary>

```
- **carry_reading**:
  - Lambda-record nonzero: True
  - Lambda-record norm: `8.056e-01`
  - value-tier p1(t): `5.697e-01`
  - exact BD p1(t): `5.697e-01`
  - p1 error: `0.000e+00`
  - Lambda-record == rho(t) - rho(0): True
  - verdict: PASS
- **literal_reading**:
  - Lambda-tier (forced) stays zero: True
  - value-tier p1(t) with Lambda = 0: `0.000e+00`
  - statement: Lambda = tau^3 = 0 identically in every tau^2 = 0 algebra (exact, algebra/lambda_carry): the literal 5DB row of the specializations table is VACUOUS -- birth-death dynamics appear only under the carry extension (d)
  - verdict: VACUOUS (literal) / NONVACUOUS (carry reading (d))
- **stochastic_check**:
  - n_traj: 4000
  - MC mean p1: `6.205e-01`
  - exact p1: `6.145e-01`
  - MC variance: `2.355e-01`
  - exact Bernoulli variance: `2.369e-01`
  - mean deviation (units of SE): `7.849e-01`
  - MC events/traj: `3.200e+00`
  - exact expected events: `3.219e+00`
  - verdict: PASS
- verdict: the 5DB row is NONVACUOUS under the carry reading (d) -- Lambda . E[rho] != 0, birth-death dynamics exact; VACUOUS under the literal reading (Lambda = tau^3 = 0). The report states both readings.
- register: mat
```
</details>

### K8 -- universality sweep (Issue 10)

**Verdict:** PASS  
100000 random QDMEs across four classes (Schrodinger / Lindblad / memory / birth-death): every instance encodes as a specialization of Thm 8.1 with value-tier error at machine precision.  Reading (a) encodability: SUPPORTED.  Reading (b) projection: surjectivity verified on the swept families; the universal reading stays (res).

<details><summary>metrics</summary>

```
- total_instances: 100000
- **classes**:
  - **U_schrodinger**:
    - n: 25000
    - max error: `5.104e-13`
    - mean error: `1.029e-15`
    - fraction below 1e-8: `1.000e+00`
    - fraction below 1e-10: `1.000e+00`
  - **L_lindblad**:
    - n: 25000
    - max error: `1.296e-14`
    - mean error: `3.720e-16`
    - fraction below 1e-8: `1.000e+00`
    - fraction below 1e-10: `1.000e+00`
  - **M_memory**:
    - n: 25000
    - max error: `1.000e-15`
    - mean error: `1.501e-16`
    - fraction below 1e-8: `1.000e+00`
    - fraction below 1e-10: `1.000e+00`
  - **B_birth_death**:
    - n: 25000
    - max error: `5.551e-16`
    - mean error: `1.325e-16`
    - fraction below 1e-8: `1.000e+00`
    - fraction below 1e-10: `1.000e+00`
- reading (a) encodability: SUPPORTED
- reading (b) projection: surjectivity of each sector restriction verified constructively on the swept families; the universal quantification over all conceivable QDMEs is not a computable claim and stays (res)
- verdict: PASS
- register: mat (for the swept families)
- **faithful**:
  - **dynamics_faithfulness**:
    - n_pairs: 40
    - n_distinct_projected_dynamics: 40
    - generically_injective: True
    - note: distinct channel sets give distinct value-tier dynamics (generic injectivity); the fiber of the encoding is the unitary orbit + rate/time rescalings
  - **record_gauge_freedom**:
    - max |value projection difference| over t: `0.000e+00`
    - records_are_gauge: True
    - interpretation: value-tier dynamics is independent of the record content (nilpotent obstruction): the records are a gauge/history layer, not a physical observable of the value projection
- **reachable**:
  - **unconstrained**:
    - n_targets: 25
    - worst |reached - target|: `8.884e-16`
    - reachable_set: entire state space (d=2), constructive
    - verdict: PASS
  - **c8_constrained**:
    - coherence generated from diagonal state under covariant dynamics: `0.000e+00`
    - constrained_reachable_set: winding-sector-block-diagonal (proper subset of the state space)
    - verdict: PROPER SUBSET (covariant family)
  - dichotomy: unconstrained encoded family: reachable set = full state space (constructive, d=2); C_8-constrained family: proper subset (sector-block-diagonal)
```
</details>

## The twelve open issues

| # | issue | resolution (established by) |
|---|-------|------------------------------|
| 1 | 12D (T_8) vs 16D (UC-Q): which is the algebra? | Both counts are correct for different objects: T_8 (12D, commutative, the tau/theta memory layer) and UC-Q = H (x) UC (16D, the quaternionic layer).  Both contain UC (4D); the join is the Gate algebra H (x) T_8 (48D), which contains T_8, UC-Q and H[tau]/(tau^2) as subalgebras (verified by exact multiplicative embeddings).  No count is wrong; the monograph lacked only this census.  NOTE: 'H[tau]... (K1/I1 census + exact multiplicative embeddings) |
| 2 | Is tau central in H[tau]/(tau^2)?  (Thm 5.2 needs it) | YES under the monograph's own reading: UC-Q is the tensor product H (x) UC (sec. 6.2.8), where tau is central by construction; Addendum XXIV's single-commutator restatement of Thm 8.1 forces the same choice.  Grassmann reading fails exactly; free reading is infinite-dimensional.  No pivot needed. (K1 (exact)) |
| 3 | Construct (H, Gamma) -> GKLS (load-bearing) | Constructed via the trace-event mechanism (route R3): H := H_0, Gamma := sum sqrt(g_k)(L_k+L_k^dag)/2, channels := {(L_k, g_k)}; the value projection of the event-fed unified evolution equals GKLS exactly.  The naive projection and adiabatic elimination routes FAIL on the literal equation (exact obstruction documented). (K4) |
| 4 | What does 'under C_8 symmetry' constrain? | Winding-graded covariance: channels must satisfy U L U^dag = omega^m L (single winding) and Hamiltonians must lie in the commutant of U; the invariant dynamics is winding-sector-block-diagonal. (K5) |
| 5 | Construct K(theta) for Thm 2.6 | K(t) = -eta C^2 e^{-gamma t} cos(sqrt(8) C t) from the theta-chain with back-coupling; the chiral pole pair +-2 sqrt 2 is forced by theta^3 = 8 theta; eta, gamma are free (constructed). (K6) |
| 6 | Lambda = tau^3 = 0 in tau^2 = 0: what is Lambda? | Under (d), the Lambda . E[rho] term of Thm 8.1 is a nonzero formal term acting on the Lambda-record tier; the 5DB row of the specializations table is NON-vacuous.  Under the literal reading (Lambda = tau^3 inside any tau^2 = 0 algebra) the row is VACUOUS (Lambda = 0 identically, exact).  The report states both; K7 tests the (d)-dynamics. (K7 + exact algebra) |
| 7 | Physicality of rho_hat in 16D | DERIVED (v1.1, was constructed): the convention (value tier a density matrix; record tiers Hermitian and traceless) is the UNIQUE survivor of four stated physical requirements inside the complete U(1) family of *-structures on UC = C[tau]/(tau^2); every alternative fails with an exact witness, and the PSD clause is a Gram-identity theorem for every gauge.  The remaining monograph gap is the uns... (derivation layer + state/physicality tests) |
| 8 | Trace preservation and CP of each term | All Thm 8.1 terms are trace-preserving on the value tier (the nilpotent terms contribute an exact structural zero); GKLS semigroup CP confirmed via Choi matrices. (state/trace_cp tests) |
| 9 | Relation between tau and theta | Stated in the monograph itself (Transit-Fare relations R4-R6): i tau = tau i, i theta = theta i, tau theta = theta tau -- all generators commute.  Verified exactly in T_8 and the Gate. (algebra tests) |
| 10 | 'Single context': encodability (a) or projection (b)? | (a) SUPPORTED constructively at scale (10^5 instances, four classes, machine precision).  (b) surjectivity verified on the swept families; the universal 'all QDMEs are slices' remains (res). (K8) |
| 11 | Does Alg 4.1's trace-clock reproduce standard times? | YES within Monte-Carlo error: the event-driven ensemble matches GKLS (amplitude and phase damping), the pooled event rate matches the exact intensity, T2 from the trace-clock ensemble = 2.011 vs 2.000 reference.  The 'inversion of standard QM' reading is (res). (event_clock) |
| 12 | Does Epoch 5 already contain j, k? | Epoch 5 does NOT contain j, k: the only square roots of -1 in UC are +-i (exact).  The i -> j differential is genuine emergence (non-commutativity is new structure), while the 3-layer linear skeleton of H is present in UC via phi/psi (Claim 2.16c confirmed); phi and psi are NOT homomorphisms (exact witnesses), so no rename. (exact sqrt(-1) classification + phi/psi) |

---

## The three registers (enforced separation)

### (mat) -- conjectured identities: verified or falsified

All K1-K8 rows above; verdicts PASS/FAIL with numbers and exact break points where an obstruction exists (K4-R1, K4-R2, the literal 5DB vacuity).

### (res) -- structural resonances: characterized, NOT proven

| claim | status |
|-------|--------|
| "single context" in the projection reading, beyond the swept families | STRUCTURALLY CHARACTERIZED (surjectivity on the swept classes; the universal reading is not computably testable) |
| trace-driven time "inverts standard QM" | CHARACTERIZED (the clock generates event times intrinsically; their distribution IS the standard one -- numeric match is (mat), the inversion reading is (res)) |
| Lambda = tau^3 as meta-measurement | CHARACTERIZED (the carry quotient records attempted transcendence; the observer-of-observers reading stays (res)) |
| the four regimes as ONE equation in the strong sense | CHARACTERIZED (one container, four constructed feeds; the bare commutator alone never lowers tier) |

### (par) -- poetic parables: not tested, left in register

- the gearshift engine metaphor (cycle I-IV)
- the life/death cycle as language
- Emperor/Trickster agents of Epoch 6

---

## Documented gaps in the monograph (found by this project)

1. The (H, Gamma) -> GKLS map of Thm 2.4 is never written; it is constructed here (K4) and works only through the event mechanism.
2. The memory kernel K of Thm 2.6 is never specified; constructed here from the theta-chain (K6).
3. The tau-theta relation is stated only in the Transit-Fare relations R4-R6 (all commute); now verified exactly.
4. Lambda = tau^3 is impossible inside any tau^2 = 0 algebra (exact); the carry extension is the consistent reading.
5. The subscripted commutator [.,.]_{lambda,mu} of Thm 5.2 is never defined.
6. 'H[tau]/(tau^2)' with tau central is 8-dimensional, not 16; the monograph's 16D object is H (x) UC (its own sec. 6.2.8), which needs the second central imaginary i_c.
7. Questions Q29-Q33 (project spec) do not appear as numbered items in the provided monograph (its question table lists Q1-Q4); the quantum-questions material is covered by the QDME chapter itself.

---

## Reproduction

```bash
pip install -e . --no-deps
pip install numpy scipy sympy pytest
qdme-bs verify --seed 2026          # full run (< 15 min)
qdme-bs verify --seed 2026 --quick  # reduced run (~20 s)
pytest                              # unit + integration tests
```

All randomness flows from the single seed.  The pinned sub-algebra reference `btc_without_ac` (UC = C[tau]/(tau^2), 4D) is vendored unmodified under `btc_without_ac/` and wrapped, never redefined.
