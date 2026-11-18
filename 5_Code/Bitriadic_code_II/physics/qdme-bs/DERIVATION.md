# The Physicality Convention: Derived, Not Designated

**Project:** QDME-bs v1.1 -- derivation layer  
**Closes:** the v1.0 report's entry "physicality convention (monograph gap) -- constructed"; Issue 7.  
**Generated:** 2026-11-15T16:36:50  
**Runtime:** 0.0 s (all checks exact, over Q(i))

---

## The statement

The v1.0 workbench **adopted** the convention:

> a container state is physical iff the value tier rho is a density matrix and every record tier is Hermitian and traceless.

This page replaces the adoption with a **derivation**: the convention is the unique solution of four stated physical requirements inside the complete family of *-structures on UC = C[tau]/(tau^2).

## Step 1 -- the complete family of *-structures (exact)

A *-structure is a conjugate-linear involution with (xy)* = y* x*; on a unital complex algebra it fixes 1* = 1 and therefore i* = -i.  Since (tau^2)* = (tau*)^2 = 0, tau* must be square-zero; the square-zero elements of UC are exactly the pure-trace elements (sympy: the value part must vanish), so tau* = tau.w, and involutivity forces |w|^2 = w-bar w = 1.

**The family is exactly the unit circle** (tau* = lambda tau, |lambda| = 1) -- a U(1) gauge.  Verified exactly (Gaussian rationals, no floating point) for lambda in {1, -1, i, (3+4i)/5, (5+12i)/13}: both *-axioms hold on random instances for each.

```
- **square-zero elements of UC are exactly tau*C (sympy)**:
  - solutions for value part: [{a: 0, b: 0}]
  - only zero: True
- involutivity forces |w| = 1: Eq(c**2 + d**2, 1)
- i* = -i forced: unital + conjugate-linear
- family: tau* = lambda tau with lambda on the unit circle U(1)
```

**The theta-generator is different** (Step 1b): theta is NOT nilpotent (theta^3 = 8 theta), so its gauge equation is mu^3 = mu, i.e. mu in {+1, -1} -- a Z_2 gauge, not U(1).  *Only the nilpotent tau carries a continuous *-gauge.*  This is why the gauge-fixing problem is finite: a continuous family reduced by two reflections, not an infinite search.

Monograph context (sec. 3.4.2-3.4.4): the perspectival algebras UC1 (i^2 = i idempotent), UC2 ("i = +-i" -- a sign ambiguity of the imaginary unit), UC3 ([[i]] obfuscated) close into UC4, whose closure conditions themselves force i^2 = -1 and tau^2 = 0.  The U(1) *-gauge found here is the involutive counterpart of UC2's sign ambiguity; the gauge fixing below is the *-analogue of the UC4 closure selecting i^2 = -1.  The monograph never states an involution -- supplying and fixing it is this layer's new content, documented as such.

## Step 2 -- the four physical requirements

| id | name | statement | monograph anchor |
|----|------|-----------|------------------|
| R1 | real record | the record tier sigma is Hermitian for every physical state (records are event logs of real dissipative processes) | sec. 2.2 (tau = decoherence record), sec. 4.2 |
| R2 | self-adjoint state | rho_hat* = rho_hat (state is an observable) | standard QM state axiom |
| R3 | probability conservation | Tr rho_hat = 1 with probability in the value tier only; record tiers carry none (Tr sigma = 0) | value map Def. 4.2.1.3 (pinned UC package) |
| R4 | *-positivity | physical states are sums of squares rho_hat = sum x_i* x_i | *-algebraic state axiom |

## Step 3 -- the finite enumeration (exact witnesses)

Candidate space: lambda-gauge x record-Hermiticity x record-trace (10 rows).  Each rejected row fails a stated requirement, with an exact witness:

| tau* | record | Tr sigma = 0 | survives | fails | witness |
|------|--------|--------------|----------|-------|---------|
| tau | Hermitian | True | **YES** | - | sigma* = lambda_bar sigma = sigma: all Hermitian records allowed |
| tau | anti-Hermitian | True | no | R2 | rho_hat* = rho_hat forces sigma* = sigma; an anti-Hermitian sigma makes rho_hat* = rho_hat - 2 tau sigma != rho_hat (witness: sigma = [[0,1],[-1,0]]i) |
| tau | Hermitian | False | no | R3 | Tr rho_hat = 1 + tau Tr sigma = 1 + tau*Gauss(3, 0) != 1: probability leaks onto the nilpotent tier (square-zero: unobservable), the value tier carries 1 - T... |
| tau | anti-Hermitian | False | no | R2, R3 | both witnesses above apply |
| -tau | Hermitian | True | no | R2 | rho_hat* = rho_hat forces sigma* = -sigma (anti-Hermitian); a Hermitian sigma gives rho_hat* = rho_hat - 2 tau sigma != rho_hat.  Equivalently under tau* = -... |
| -tau | anti-Hermitian | True | no | R1' | the record is anti-Hermitian: an observable of a dissipative process cannot be skew-adjoint (its eigenvalues would be imaginary); the monograph's tau-records... |
| -tau | anti-Hermitian | False | no | R1', R3 | both witnesses apply |
| -tau | Hermitian | False | no | R1', R2, R3 | all witnesses apply |
| i tau (generic phase) | Hermitian | True | no | R1 | sigma* = lambda_bar sigma = -i sigma for lambda = i: NO nonzero record is Hermitian (exact witness sigma = tau.Identity); the same holds for every lambda not... |
| i tau (generic phase) | Hermitian | False | no | R1, R3 | both witnesses apply |

**Survivors: 1 of 10 -- unique.**  the physicality convention (tau* = tau; rho, sigma Hermitian; Tr rho = 1, Tr sigma = 0; rho >= 0) is the UNIQUE solution of (R1)-(R4) in the U(1) family of *-structures: derived, not designated

## Step 4 -- what *-positivity forces (and what it frees)

Expanding x = A + tau B with the lambda-involution:

    x* x = A* A + tau (A* B + lambda B* A)    (tau^2 = 0)

so the **value tier of any sum of squares is exactly the Gram matrix A* A -- positive semidefinite for every gauge lambda** (verified exactly, Sylvester criterion over Q(i), for lambda in {1, -1, i, (3+4i)/5}; the record tier is verified to be A* B + lambda B* A in the same pass).  Bonus exact fact: the record of a square is Hermitian for lambda = +1, anti-Hermitian for lambda = -1, and neither for generic lambda -- outside {+1, -1} the positive cone does not even close on the self-adjoint class.

Conversely, for ANY Hermitian sigma (indefinite included) the element x = 1 + tau(sigma/2) satisfies x* x = 1 + tau sigma exactly (lambda = 1; exact rational witnesses computed for a traceless, an indefinite, and a generic record).  **The record tier is not constrained by positivity at all.**

```
- **traceless diagonal [[1,0],[0,-1]]**:
  - x* x == 1 + tau sigma (exact): True
  - indefinite record: True
- **indefinite [[2,0],[0,-3]]**:
  - x* x == 1 + tau sigma (exact): True
  - indefinite record: True
- **generic Hermitian [[1,1],[1,2]]**:
  - x* x == 1 + tau sigma (exact): True
  - indefinite record: False
```

**Conclusion of Step 4:** the PSD clause of the convention (rho >= 0) and the record-freedom clause are both *theorems* of the *-algebra -- they could not have been chosen otherwise.

## The derivation, complete

(R1) + (R2) + (R3) + (R4) have exactly one solution in the complete U(1) family:

> **tau\* = tau;  rho\* = rho, sigma\* = sigma;  Tr rho = 1, Tr sigma = 0;  rho >= 0, sigma unconstrained.**

That is precisely the v1.0 convention.  The gap flagged in the v1.0 verification report ("constructed convention (monograph gap)") is closed: what was a designation is now the unique survivor of four stated physical requirements, with an exact witness for the failure of every alternative.

**Register note.** The *derivation itself* (family completeness, the four requirements, the enumeration, the Gram identity) is (mat).  The claim that requirements (R1)-(R4) are what the *monograph's author intended* is (res) -- the monograph never states an involution; the anchors cited are semantic, not axiomatic.

---

## Reproduction

```bash
qdme-bs derive            # runs every check on this page and writes DERIVATION.md
pytest tests/test_derivation.py
```
