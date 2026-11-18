# π-clock for the browser — a timer whose tick is a counted Farey fraction

**Pure JavaScript, zero dependencies, no build step.** The π-clock
(*Poetica Mathematica*, Book II §8, *The Trinumeral Clock*) as a
WebExtensions browser extension plus a standalone demo page. The exact
core runs on **BigInt rationals** — the port of the verified Python
`piclock` package (itself proven by the W1–W12 trial battery) — and is
**cross-checked 253/253, bit for bit, against the Python original**
(totient sums, the π-law, the Farey walk, the Franel–Landau sums, the
trinumeral cycle, square-free counts, serialization round-trip).

## What you see when you run it

A timer that **locks onto π**:

```
I  (ticks)      2F/I                     error      ≡ −3π/I
      10        2.1991148581         −9.42e−01     −9.42e−01
     100        3.0473448738         −9.42e−02     −9.42e−02
   1,000        3.1321678757         −9.42e−03     −9.42e−03
  10,000        3.1406501758         −9.42e−04     −9.42e−04
```

Each tick advances **one Farey fraction**: the integer register counts
`I = |Fₙ| = 1 + Φ(n)` **exactly** (BigInt; Φ is the summatory totient),
the float register accumulates `F += π/2` per fraction (the half-region
hyperbolic area — each ideal triangle of the Farey tessellation is
exactly π), and the ratio obeys

```
2F/I = π (1 − 3/I)   exactly   →   error = −3π/I  (halves as I doubles)
```

The big readout highlights in gold every digit that has **converged to
π's** — you watch the lock-in, digit by digit, at exactly the rate the
law predicts. The chart's second lane plots `−error·I/(3π)`, which sits
**flat at 1**: the error law, visible.

## Install (Chrome / Edge / Brave)

1. Open `chrome://extensions`
2. Enable **Developer mode** (top right)
3. **Load unpacked** → select this folder (`piclock-browser/`)
4. The π-clock starts running immediately:
   * a **floating pill** on every page — click `▸` to expand the full
     instrument (draggable; position remembered),
   * the **toolbar popup** for quick control,
   * `chrome-extension://…/demo/index.html` (link in the popup) for the
     full-page demo.

**Firefox (≥ 121):** `about:debugging#/runtime/this-firefox` →
**Load Temporary Add-on** → pick `manifest.json`. The manifest carries
both `background.service_worker` (Chrome) and `background.scripts`
(Firefox) — the standard cross-browser MV3 pattern.

**No install at all:** open `piclock_demo.html` (the standalone
single-file copy shipped beside this folder) by double-clicking — the
same exact core, the same instrument, zero permissions.

## What the extension proves operationally

| piece | what it does |
|---|---|
| **registers (§8.2)** | B: the sphere mask, BigInt and **never cleared** (a sphere fires per Farey order rollover) · I: exact BigInt tick counter, **never resets** · F: the IEEE-double area register (the accumulation is the metaphor of time) |
| **the π-cycle (§8.9)** | `2F/I = π(1−3/I)` exactly; the PLL lock onto π; full-region toggle → 2π |
| **the fold (precision boundary)** | the Ouroboros epoch (232 = 2·117−2, fold at 116) is **retired**; F now folds at the **numerical precision boundary**: when F > 2⁵², adding π/2 to a double starts rounding the increment — so F ← F − n·2π (n = ⌊F/2π⌋), logged as PRECISION_FOLD, and the exact layer F_exact = (π/2)(I−3) keeps the ratio observable. No B clear, no I reload — transfinite running |
| **the Trinumeral (Ch. VIII §8.4)** | the three sheets (B binary, i BigInt, f double) cycle bin2int → int2float → float2bin per tick; α, β, γ exact; **telescope α+β+γ = 0 at every tick**; the nilpotent ladder ledger + ghost disc; σ, the spinorial double cover (−1 after one round trip, +1 after two) |
| **Franel–Landau audit** | d_{k,n} = a_{k,n} − k/mₙ for the current order, **exact BigInt rationals**; Franel (1924): RH ⟺ Σd² = O(n^r) ∀r>−1; Landau (1924): RH ⟺ Σ\|d\| = O(n^r) ∀r>½ (exact audit capped at n = 120; verified against Python at n = 5…50) |
| **the π² identity (§8.9)** | π² = 6N/SF(N) via exact Möbius-sieve square-free counts (N = 10⁶: 9.8696223 vs π² = 9.8696044) |
| **\|Fₙ\| ~ 3n²/π²** | the summatory-totient asymptotic, live, converging |

## Architecture (the WebExtensions pattern)

```
manifest.json          MV3; background.service_worker (Chrome) +
                       background.scripts (Firefox ≥ 121)
background.js          the SINGLE OWNER of the clock: setInterval drives
                       live ticks; state persists to chrome.storage.local;
                       every worker wake (startup/connect/30 s alarm)
                       CATCHES UP deterministically from the stored
                       wall-clock timestamp -- the machine is pure
                       (state -> tick()), so catch-up has no drift;
                       snapshots (B, I, F, error, fraction, sheets,
                       ledger, σ, wraps) broadcast to all ports at 10 fps
core/rational.js       exact BigInt rationals (the fractions.Fraction port)
core/piclock.js        the machine: totient sieve, Farey walker,
                       trinumeral + annihilation ladder, spinorial tally,
                       Franel-Landau, Moebius; plain scripts (no modules)
core/nestedbif.js      the Nested-Bif engine (see the section below):
                       two nested two-sheet environments converging on pi
content/widget.js      the floating widget: closed shadow DOM, draggable,
                       digit-lock readout, two-lane chart, registers,
                       precision meter (F vs the 2^52 fold boundary),
                       trinumeral panel, audits, controls
popup/                 the toolbar mini-panel (self-stubs chrome.* when
                       opened as a plain file, so it is testable/demoable)
assets/totients.bin    phi(1..10000) as Uint32 (precomputed, per the
                       spec; the core computes the sieve identically as a
                       fallback -- the harness proves they agree)
assets/nested_bif_reference.json
                       the authoritative Python reference for the
                       nested-bif engine (400 full ticks + a 2000-tick
                       deep run), used by the 39-assertion harness
demo/                  the legacy full-page instrument (bundled)
demo/bif.html          the Nested-Bif comparative analyzer — V1-V4
                       visualizations with a shared tick cursor and a
                       tabbed live log (also shipped standalone as
                       piclock_nested_bif_demo.html)
```

The content scripts are classic scripts sharing the isolated world's
globals (`PiLock`), so the **same core files** run in the service
worker (`importScripts`), the widget, the popup, the demo, the
standalone file and the Node test harness — one source of truth.

## Exactness contract

* BigInt everywhere it matters: I, \|Fₙ\|, the Farey walk, α/β/γ, the
  ladder ledger, the ghost disc, the Franel–Landau sums, SF(N), the B
  mask, serialization.
* IEEE doubles only where the monograph puts them (the F register is
  *specified* as a float register, §8.2) and for the transcendental
  evaluations π, log. `exactDouble` recovers the exact rational of any
  double by bit decomposition.
* The Node harness (`scripts/piclock_browser_harness.mjs` in the
  project workbench) checks **253 exact assertions** against
  `assets/reference.json`, generated by the verified Python package —
  including one bug it caught and fixed in the reference generator
  itself (stale bound methods), which is exactly what cross-implementation
  checking is for.

## The Nested-Bif π-clock (the refined architecture)

**Files:** `core/nestedbif.js` (engine) · `demo/bif.html` + `demo/bif.js`
(the comparative analyzer) · `piclock_nested_bif_demo.html` (standalone,
double-click to run) · `assets/nested_bif_reference.json` (Python
reference) · harness: 48/48 exact cross-checks.

A transfinite bracketing engine with **two nested bif environments**
converging on π. The outer bif runs three schemes — ordinal counting
(B, a band `π_est ± 1/B` around the previous final-bracket midpoint),
Leibniz (i, exact rational sheets `S_{2m+1}` above π, `S_{2m+2}` below),
apeirogon (f, `n·sin(π/n)` / `n·tan(π/n)`) — combined by
`L_outer = max(…)`, `U_outer = min(…)`. The inner bif is the Farey layer
with **two parallel bif structures**: the value bif `[2F/I, π]` (gap
exactly `3π/I` — the membrane is π itself) and the spinorial bif
`σ = ±1` (flips every 360° of phase, i.e. every third tick). The final
bracket is the intersection; the balancer holds the outer schemes at the
Farey rate (`m ≈ I/(3π)`, `n ≈ √(π²I/6)`); the Trinumeral records the
index discrepancies `α = B−m`, `β = m−n`, `γ = n−B` (telescope ≡ 0) and
its ladder annihilates the ledger at each outer phase flip. **No
epochs** — transfinite running. The F register folds at the numerical
precision boundary (2⁵²), never at a lattice constant. Logging for
later analysis: a tick-log ring (CSV export), the phase-history event
log with flips, warnings, order rollovers and precision folds (JSONL
export), and a session summary (JSON export), all downloaded as files.

### The analyzer: V1–V4, one shared cursor, one live log

* **V1 · Bracket** — what is π estimated as, right now? The final
  bracket band chasing the π membrane, the outer bracket behind it.
* **V2 · Gap-Rate** — how fast is each scheme converging, and are they
  balanced? The four gaps on a log scale against the law line 3π/I,
  plus the rate constants (gap × I: B → 2, i and f → 3π, the law → 3π).
* **V3 · Phase** — which sheets are active, and how do the two bifs
  relate? The σ staircase (inner, spinorial) over the outer-sheet band
  (recent window: the 3-tick alternation is visible).
* **V4 · Trinumeral** — are the schemes synchronized? The α, β, γ
  trajectories over the full ring, with the ghost disc and an event
  lane (outer flips, warnings, order rollovers, precision folds).
* **Shared tick cursor** — hover any chart for a transient readout,
  click to anchor, click a log row to jump; the gold cursor line and
  the readout strip are shared by all four charts.
* **Live log** — tabs **Ticks | Events | Orders** (defaulting to
  Events, the stream a human watches; the tick stream is for export
  and cursor jumps), filter by kind, **pause-on-hover** (the table
  freezes while the pointer is over it — verified: renders hold while
  the clock keeps ticking), click a row to jump the cursor, and the
  CSV / JSONL / JSON exports in the panel header.

### Spec resolutions (checked against the monograph)

* **R1 — I is transfinite, never reset.** The spec's `I_reset
  (fiducial)` line in its § 10.1 contradicts its own § 1 ("No epochs.
  Transfinite running") and § 13 (the preserved law
  `2F/I = π(1−3/I)`), which the monograph states with I = the **total**
  Farey count (§8.9: "half region: F = (π/2)·(|Fₙ|−3) → 2F/I → π").
  The fiducial reload belongs to the Path-6 fold (trials W10), which
  this architecture removes. Implemented: order rolls over when I
  reaches |F_order|; I keeps counting. (B = I always — the spec keeps
  both registers; α, γ read B, the Farey layer reads I.)
* **R2 — Leibniz pairing.** § 4.1's labels (L_i = S_{2m+1} "below π")
  contradict both the series' alternation (odd partial sums lie **above**
  π: S₁ = 4) and the spec's own gap law `Gap_i = 4/(4m+3) =
  S_{2m+1} − S_{2m+2}`. Implemented per the gap law:
  U_i = S_{2m+1}, L_i = S_{2m+2}.
* **R3 — apeirogon guard n ≥ 3** (n = 1 gives sin π = 0; n = 2 gives
  tan(π/2) = ∞).
* **R4 — the B scheme is implemented literally**, and the consequence is
  surfaced, not patched: the B band's width 2/B outpaces the final
  bracket's convergence 3π/I, so once π_est's lag exceeds 1/B (around
  tick 10) the final bracket **tracks just below π** instead of
  straddling it (4 of the first 400 ticks contain π; steady state
  ≈ [π−3.1/I, π−1.1/I]). The analyzer reports `contains π` and
  `π − U_final` live; the charts show the bracket chasing the membrane.
  The Leibniz and apeirogon brackets still straddle π throughout — the
  membrane story lives in the scheme rows. (One-line change if a
  straddling final bracket is preferred: derive π_est from the previous
  **outer** bracket, or clamp U_B ≥ π.)
* **R5 — balance** = max/min over the **three outer gaps** (§ 7's
  formula); Gap_F is displayed alongside as the calibration target.
  Warnings fire on the rising edge (the first at tick 8, when the
  apeirogon n-quantization lags the 3π/I target; steady-state balance
  ≈ 3π/2 ≈ 4.7, inside the threshold 10).
* **R6 — the fold is the numerical precision boundary.** The value bif
  reads the exact layer F_exact = (π/2)(I−3) by formula, so the
  operational F may wrap at 2⁵² (PRECISION_FOLD event: F ← F − n·2π,
  n = ⌊F/2π⌋) without ever touching the bracket — same rule as the
  legacy clock above. Unit-tested by injection; the boundary sits at
  I ≈ 2.9·10¹⁵ ticks, so no live run ever reaches it.

### Exactness in the nested-bif engine

B, m, n, I, α, β, γ, the ledger and the ghost are BigInt. The Leibniz
partial sums are **exact rationals kept over a shared running
denominator** (the lcm of the odd denominators): each advance does one
big-mod-small, one big-div-small and big×small multiplications —
O(limbs), **no big-big gcd ever**, so the exact layer stays fast at any
depth (m = 542 at I = 5,116 in the smoke test; the 2,000-tick reference
holds a 210-digit denominator without effort). The gap identity
`S_hi − S_lo = 4/(4m+3)` is checked **exactly** (cross-multiplied
BigInts) every harness run. Doubles live only where the spec puts them
(π_est, the bracket layer, trig, F). The harness cross-checks **400
ticks field-for-field** against the Python reference (exact for all
integer/boolean/enum fields, 1e-12 relative for the trig-derived
doubles) plus the 2,000-tick deep run, and re-derived the reference's
own semantics twice: it caught an aliasing bug in the JS `_leibStep`
(rescaling the discarded sheet instead of the kept one) and a
warn-dedupe flaw in the Python generator.



## Trial results (November 2026 battery)

`results/` holds the full trial run and log analysis:
`NESTEDBIF_TRIALS.md` (verdicts T1–T15, corrections, established
results, OPEN), `ANALYSIS.md` (sections A–F with figures),
`HARNESS.md` (54/54 + 253/253), `SUMMARY.txt`, `measurements.json`,
`t12_injection.json`, `runs/` (R-A…R-F + CTRL-R4, each with ticks.csv,
events.jsonl, session.json) and `figures/`.  Headline: exactness
confirmed with zero failures across 241,000 logged ticks; the final
bracket collapses onto the B band below π (width law 2/B), the four
rates are balancer-locked, and the R4 control fix inverts the bracket.
The runs (~70 MB of logs) are kept out of the extension zip.

## License

MIT (code). The monograph it implements is CC BY 4.0 (K. I. Kovlekov).
