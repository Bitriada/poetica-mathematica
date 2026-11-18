# Audit of the BSP paper's own numbers

Recomputation of every quantitative claim in the paper's validation (sec. 12 / appendix B).

## The Neumann constant (claims A1, A2)

- Ste = c_p (T_m - T_s) / L = **0.1253**
- the paper's printed equation e^(-l^2)/erf(l) = L sqrt(pi) / (c_p dT) has RHS = 14.14; its true root is lambda = 0.0625
- the correct one-phase equation l e^(l^2) erf(l) = Ste/sqrt(pi) gives **lambda = 0.2453**
- the paper's claim lambda = 0.15 satisfies NEITHER: it is off by a factor 2.43 on the printed equation and 2.74 on the correct one (the printed equation is the correct one with the factor lambda on the RHS missing, i.e. evaluated at lambda = 1)

## Thermal diffusivity (claim A3)

- the paper states alpha = 1.150e-06 m2/s but its own k, rho, c_p give 5.256e-07 (factor 2.19). 1.15e-6 matches physical ice (rho=917, cp=2050); the paper mixes water and ice property tables

## First event (claim A5)

- paper formula dt_1 = rho L dx^2 / (k dT) = 15.1818 s; paper prints 15.2 s; this package's solver reproduces 15.1818 s -- **correct and reproduced**

## Event tables (claim A4)

- sec. 12.2 first events: [152.0, 366.0, 628.0, 931.0, 1270.0]
- appendix B.2 first events: [15.2, 36.9, 63.2, 92.8, 125.1] (mutually inconsistent by 10x)
- the paper's explicit rule run on its own field: **2 events, then stalls: non-positive interface velocity at t=30.4s** -- the printed rule cannot produce the appendix table; the appendix's intervals were hand-fed from the Neumann profile
- faithful run (crossing condition): first events [15.2, np.float64(30.4), np.float64(61.5), np.float64(108.4), np.float64(171.1)]

## The headline 'within 2%' (claim A6)

- at t = 1000 s the paper claims Neumann s = 0.0102 m (from lambda = 0.15, alpha = 1.15e-6): recomputed = 10.17 mm
- with the CORRECT lambda but the paper's alpha: 16.64 mm
- with correct lambda and self-consistent alpha: 11.25 mm
- faithful BSP at dx = 0.5 mm: 11.00 mm (**2.2%** from the correct value)
- verdict: the paper's 'within 2%' compares its BSP table to a Neumann position computed with the wrong lambda; against the correct self-consistent Neumann position the faithful BSP run agrees to a few percent, which SUPPORTS the method while contradicting the paper's arithmetic

## Overall

The paper's validation arithmetic contains four independent errors (missing factor in the lambda equation; mis-solved lambda; inconsistent alpha; two mutually inconsistent event tables). None of them invalidates the METHOD: the faithful BSP run converges to the correct Neumann solution (see the convergence study in the case reports). The framework is sound; the paper's numbers needed this correction.