/* nestedbif.js -- The Nested-Bif pi-clock (user spec, refined arch).
 *
 * A transfinite bracketing engine: two nested bif (two-sheet)
 * environments converging on pi.
 *
 *   OUTER bif {B, i, f}:  ordinal counting (B), Leibniz (i),
 *     apeirogon (f) -- each a lower/upper sheet pair, combined into
 *     one bracket.  INNER bif {F}: the Farey layer, itself a two-sheet
 *     environment (the value bif [2F/I, pi] + the spinorial bif
 *     sigma = +-1), nested inside the outer environment.
 *   pi is the MEMBRANE between the sheets.  The exact Farey error law
 *     3*pi/I calibrates the balancer (m ~ I/(3pi), n ~ sqrt(pi^2 I/6)).
 *
 * SPEC RESOLUTIONS (see assets/nested_bif_reference.json +
 * README):  R1 I transfinite (the spec's `I_reset (fiduc)` line is the
 * Path-6 fold vestige, contradicted by "No epochs. Transfinite
 * running" and by the preserved law 2F/I = pi(1-3/I), which needs
 * I = the TOTAL Farey count, monograph sec. 8.9).
 * R2 Leibniz pairing U_i = S_{2m+1} (above pi), L_i = S_{2m+2}
 *   (below pi) -- sec. 4.1's labels contradict the series' own
 *   alternation and the spec's gap law 4/(4m+3) = S_{2m+1}-S_{2m+2}.
 * R3 apeirogon guarded to n >= 3 (n=1: sin(pi)=0; n=2: tan(pi/2)=inf).
 * R4 the B scheme is literal (pi_est = previous final-bracket
 *   midpoint): its band (width 2/B) outpaces the bracket convergence
 *   (3*pi/I), so after the early ticks the final bracket TRACKS just
 *   below pi -- surfaced honestly via snapshot.containsPi.
 * R5 balance = max/min over the three OUTER gaps (sec. 7); Gap_F is
 *   displayed alongside.  Threshold 10, warn on rising edge.
 *
 * EXACTNESS (sec. 12): B, m, n, I, alpha, beta, gamma, ledger, ghost
 * are BigInt (integers here -- the discrepancies of this architecture
 * are index discrepancies).  The Leibniz partial sums are EXACT
 * rationals kept as (numHi, numLo, den) over the running lcm of the
 * odd denominators -- shared denominator, small-gcd updates only, so
 * no big-big gcd is ever needed (see _leibStep).  IEEE doubles: F,
 * pi, the trig evaluations, the bracket/estimator layer (pi_est is
 * specified as a double), display.
 *
 * Plain script (no modules): attaches PiLock.NestedBifClock.
 */

(function (global) {
  "use strict";

  const PI = Math.PI;
  const PRECISION_BOUND = 2 ** 52;   // F folds when F > 2^52 (ulp = 1)

  /** gcd of two small BigInts (both < 2^63) */
  function sgcd(a, b) {
    while (b) { const t = a % b; a = b; b = t; }
    return a;
  }

  /** exact rational -> double, ~1 ulp (scaled 64-bit division) */
  function bigDiv(num, den) {
    if (num === 0n) return 0;
    const neg = num < 0n;
    const n = neg ? -num : num;
    const q = (n << 64n) / den;
    const v = Number(q) / 18446744073709551616;   // 2^64
    return neg ? -v : v;
  }

  class NestedBifClock {
    constructor(opts = {}) {
      this.sieve = opts.sieve || new global.PiLock.TotientSieve(4096);
      this.tracker = new global.PiLock.FractionTracker(this.sieve);
      this.threshold = opts.threshold || 10;
      this.maxHistory = opts.maxHistory || 100000;
      this.logCap = opts.logCap || 8192;

      // registers (sec. 3) -- BigInt where exact
      this.B = 0n;                 // tick counter / ordinal index
      this.m = 0n;                 // Leibniz even index
      this.n = 3n;                 // apeirogon side count (>= 3, R3)
      this.I = 0n;                 // Farey tick counter (transfinite, R1)
      this.order = 1;
      this.orderSize = this.sieve.fareySize(1);
      this.F = 0;                  // hyperbolic area accumulator (double)
      this.sigma = 1;              // spinorial phase (+-1)
      this.phaseAngle = 0;         // integer degrees
      this.sheetOuter = null;      // 'upper' | 'lower'
      this.piEst = 4;              // init from S_1 (sec. 4.3)

      // Leibniz exact: S_hi = S_{2m+1}, S_lo = S_{2m+2} over shared den
      this.den = 3n; this.numHi = 12n; this.numLo = 8n;  // S_1 = 4, S_2 = 8/3

      // trinumeral recorder (sec. 8)
      this.alpha = 0n; this.beta = 0n; this.gamma = 0n;
      this.ledger = [0n, 0n, 0n];
      this.ghost = 0n;

      // history + logging
      this.history = [];
      this.flipsOuter = 0; this.flipsSpin = 0;
      this.balanceWarns = 0; this.warnActive = false;
      this.rolls = 0;                // order rollovers taken
      this.wraps = 0;                // precision folds taken
      this.lastWrapN = 0;            // turns removed by the last fold
      this.tickLog = []; this.logDropped = 0;
      this.logDroppedEvents = 0;
    }

    // ------------------------------------------------------------ leibniz
    /** S_target := S_source + c/q, where the SOURCE sheet is the one
     *  NOT targeted (it keeps its value, rescaled); the target's old
     *  value is discarded.  Both numerators move to the new shared
     *  denominator lcm(den, q) = (den/g)*q.  q is small (< 2^31):
     *  one big-mod-small, one big-div-small, big*small -- O(limbs);
     *  no big-big gcd, ever. */
    _leibStep(target, c, q) {
      const g = sgcd(q, this.den % q);
      const mult = q / g;                  // small
      const denOverG = this.den / g;       // big
      const keep = target === "hi" ? this.numLo : this.numHi;
      const newT = keep * mult + c * denOverG;   // the target sheet
      const newK = keep * mult;                  // the kept sheet
      this.den = denOverG * q;
      if (target === "hi") { this.numHi = newT; this.numLo = newK; }
      else { this.numLo = newT; this.numHi = newK; }
    }

    /** advance the exact Leibniz state to targetM (monotone) */
    _advanceLeibniz(targetM) {
      while (this.m < targetM) {
        const mi = Number(this.m);
        this._leibStep("hi", 4n, BigInt(4 * mi + 5));
        this._leibStep("lo", -4n, BigInt(4 * mi + 7));
        this.m += 1n;
      }
    }

    get S_hi_value() { return bigDiv(this.numHi, this.den); }
    get S_lo_value() { return bigDiv(this.numLo, this.den); }

    // ------------------------------------------------------------ events
    _event(e) {
      if (this.history.length >= this.maxHistory) {
        this.history.shift();
        this.logDroppedEvents++;
      }
      this.history.push(e);
    }

    // ------------------------------------------------------------ tick
    tick() {
      this.B += 1n;
      const B = Number(this.B);
      this.I += 1n;
      const I = Number(this.I);

      // order rollover (R1: I keeps counting -- transfinite)
      if (this.I >= BigInt(this.orderSize)) {
        const prevSize = this.orderSize;
        this.order += 1;
        this.sieve.ensure(this.order + 8);
        this.orderSize = this.sieve.fareySize(this.order);
        this.rolls += 1;
        this._event({ type: "ORDER_ROLL", tick: B, order: this.order,
                      orderSize: this.orderSize,
                      phi: this.orderSize - prevSize });
      }

      // balancer (sec. 7): delta_target = 3 pi / I
      const targetM = BigInt(Math.floor(I / (3 * PI)));
      this._advanceLeibniz(targetM);
      const targetN = BigInt(Math.max(3,
        Math.floor(Math.sqrt(PI * PI * I / 6))));
      this.n = targetN;

      // hyperbolic area (fixed prefix I > 3, half region).  The fold
      // trigger is the NUMERICAL PRECISION BOUNDARY, not a lattice
      // constant: F is the operational accumulator (the accumulation
      // is the metaphor of time); it folds when F > 2^52, where adding
      // pi/2 to a double starts rounding the increment.  The exact
      // layer F_exact = (pi/2)(I-3) keeps the value bif exact forever.
      let precisionFold = false;
      if (this.I > 3n) {
        this.F += PI / 2;
        if (this.F > PRECISION_BOUND) {
          const w = Math.floor(this.F / (2 * PI));
          this.F -= w * (2 * PI);
          this.wraps += 1;
          this.lastWrapN = w;
          precisionFold = true;
          this._event({ type: "PRECISION_FOLD", tick: B,
                        wraps: this.wraps, n: w,
                        F_after: this.F });
        }
      }

      // --------------------------------------------- the four schemes
      const L_B = this.piEst - 1 / B, U_B = this.piEst + 1 / B;
      const L_i = this.S_lo_value, U_i = this.S_hi_value;
      const nf = Number(this.n);
      const L_f = nf * Math.sin(PI / nf);
      const U_f = nf * Math.tan(PI / nf);
      // the value bif reads the EXACT layer, not the wrapped register
      const Fexact = I > 3 ? (PI / 2) * (I - 3) : 0;
      const L_F = 2 * Fexact / I, U_F = PI;

      // --------------------------------------------- brackets (sec. 5)
      const L_outer = Math.max(L_B, L_i, L_f);
      const U_outer = Math.min(U_B, U_i, U_f);
      const L_final = Math.max(L_outer, L_F);
      const U_final = Math.min(U_outer, U_F);

      // --------------------------------------------- phases (sec. 6)
      const sheet = (U_outer - PI < PI - L_outer) ? "upper" : "lower";
      if (this.sheetOuter !== null && sheet !== this.sheetOuter) {
        const ann = this.ledger.map((x) => x < 0n ? -x : x);
        this.ghost += ann[0] + ann[1] + ann[2];
        this.ledger = [0n, 0n, 0n];
        this._event({ type: "OUTER_FLIP", tick: B,
                      from: this.sheetOuter, to: sheet,
                      annihilated: ann.map(Number), ghost: Number(this.ghost) });
        this.flipsOuter++;
      }
      this.sheetOuter = sheet;

      // trinumeral recorder (sec. 8)
      this.alpha = this.B - this.m;
      this.beta = this.m - this.n;
      this.gamma = this.n - this.B;
      this.ledger[0] += this.alpha;
      this.ledger[1] += this.beta;
      this.ledger[2] += this.gamma;
      const oldAngle = this.phaseAngle;
      this.phaseAngle += 120;
      const crossings = Math.floor(this.phaseAngle / 360)
        - Math.floor(oldAngle / 360);
      if (crossings % 2 !== 0) {
        this.sigma = -this.sigma;
        this._event({ type: "SPIN_FLIP", tick: B, to: this.sigma });
        this.flipsSpin++;
      }

      // gaps + balance (sec. 7, R5)
      const gapB = 2 / B;
      const gapI = 4 / (4 * Number(this.m) + 3);
      const gapF = U_f - L_f;
      const gapFF = 3 * PI / I;
      const gaps3 = [gapB, gapI, gapF];
      const balance = Math.max(...gaps3) / Math.min(...gaps3);
      const warn = balance > this.threshold;
      if (warn && !this.warnActive) {
        this._event({ type: "WARN_BALANCE", tick: B, balance });
        this.balanceWarns++;
        this.warnActive = true;
      } else if (!warn && this.warnActive) {
        this._event({ type: "WARN_CLEAR", tick: B, balance });
        this.warnActive = false;
      }

      // pi_est for the NEXT tick (sec. 4.3)
      this.piEst = (L_final + U_final) / 2;

      const snap = this.snapshot({
        L_B, U_B, L_i, U_i, L_f, U_f, L_F, U_F,
        L_outer, U_outer, L_final, U_final,
        gapB, gapI, gapF, gapFF, balance, warn, precisionFold,
        Fexact,
      });
      this._log(snap);
      return snap;
    }

    // ------------------------------------------------------------ snap
    snapshot(extra) {
      const bindsL = ["B", "i", "f"][
        [extra.L_B, extra.L_i, extra.L_f].indexOf(extra.L_outer)];
      const bindsU = ["B", "i", "f"][
        [extra.U_B, extra.U_i, extra.U_f].indexOf(extra.U_outer)];
      const frac = this.tracker.sync(this.order, this.I);
      return {
        B: Number(this.B), I: Number(this.I),
        m: Number(this.m), n: Number(this.n),
        order: this.order, orderSize: this.orderSize,
        piEst: this.piEst, F: this.F, Fexact: extra.Fexact || 0,
        L_B: extra.L_B, U_B: extra.U_B,
        L_i: extra.L_i, U_i: extra.U_i,
        L_f: extra.L_f, U_f: extra.U_f,
        L_F: extra.L_F, U_F: extra.U_F,
        L_outer: extra.L_outer, U_outer: extra.U_outer,
        L_final: extra.L_final, U_final: extra.U_final,
        gapB: extra.gapB, gapI: extra.gapI, gapF: extra.gapF,
        gapFF: extra.gapFF, balance: extra.balance, warn: extra.warn,
        sheetOuter: this.sheetOuter, sigma: this.sigma,
        phaseAngle: this.phaseAngle,
        alpha: Number(this.alpha), beta: Number(this.beta),
        gamma: Number(this.gamma),
        telescope: this.alpha + this.beta + this.gamma === 0n,
        ledger: this.ledger.map(Number), ghost: Number(this.ghost),
        containsPi: extra.L_final <= PI && PI <= extra.U_final,
        bindsL, bindsU,
        fraction: [Number(frac[0]), Number(frac[1])],
        flipsOuter: this.flipsOuter, flipsSpin: this.flipsSpin,
        rolls: this.rolls, wraps: this.wraps,
        lastWrapN: this.lastWrapN,
        precisionFold: !!extra.precisionFold,
        // exact Leibniz layer (unreduced but exact: num/den)
        S_hi_exact: [this.numHi.toString(), this.den.toString()],
        S_lo_exact: [this.numLo.toString(), this.den.toString()],
      };
    }

    _log(snap) {
      if (this.tickLog.length >= this.logCap) {
        this.tickLog.shift();
        this.logDropped++;
      }
      this.tickLog.push(snap);
    }

    /** the last K history events, newest last (for sec. 10.2) */
    recentHistory(k = 8) {
      return this.history.slice(-k);
    }

    /** -------------------------------------------------- serialization
     * Full state for the single-owner loop's deterministic catch-up
     * (kill / restart / replay): every register, the exact Leibniz
     * layer, the trinumeral state, all counters, the event history
     * and the Farey tracker position.  The tick-log RING is not
     * serialized -- it is a UI buffer; the owner loop streams ticks
     * as they fire.  BigInts become strings. */
    toJSON() {
      const S = (x) => x.toString();
      return {
        threshold: this.threshold, logCap: this.logCap,
        maxHistory: this.maxHistory,
        B: S(this.B), m: S(this.m), n: S(this.n), I: S(this.I),
        order: this.order, orderSize: this.orderSize,
        F: this.F, sigma: this.sigma, phaseAngle: this.phaseAngle,
        sheetOuter: this.sheetOuter, piEst: this.piEst,
        den: S(this.den), numHi: S(this.numHi), numLo: S(this.numLo),
        alpha: S(this.alpha), beta: S(this.beta), gamma: S(this.gamma),
        ledger: this.ledger.map(S), ghost: S(this.ghost),
        flipsOuter: this.flipsOuter, flipsSpin: this.flipsSpin,
        balanceWarns: this.balanceWarns, warnActive: this.warnActive,
        rolls: this.rolls, wraps: this.wraps, lastWrapN: this.lastWrapN,
        logDropped: this.logDropped, logDroppedEvents: this.logDroppedEvents,
        history: this.history,
        tracker: {
          order: this.tracker.order, position: this.tracker.position,
          walker: {
            n: this.tracker.walker.n,
            a: S(this.tracker.walker.a), b: S(this.tracker.walker.b),
            c: S(this.tracker.walker.c), d: S(this.tracker.walker.d),
            position: this.tracker.walker.position,
          },
        },
      };
    }

    static fromJSON(o) {
      const B = (x) => BigInt(x);
      const sieve = new global.PiLock.TotientSieve(
        Math.max(4096, 2 * (o.order || 1) + 64));
      const c = new NestedBifClock({ sieve, threshold: o.threshold,
                                     logCap: o.logCap,
                                     maxHistory: o.maxHistory });
      c.B = B(o.B); c.m = B(o.m); c.n = B(o.n); c.I = B(o.I);
      c.order = o.order; c.orderSize = o.orderSize;
      c.F = o.F; c.sigma = o.sigma; c.phaseAngle = o.phaseAngle;
      c.sheetOuter = o.sheetOuter === undefined ? null : o.sheetOuter;
      c.piEst = o.piEst;
      c.den = B(o.den); c.numHi = B(o.numHi); c.numLo = B(o.numLo);
      c.alpha = B(o.alpha); c.beta = B(o.beta); c.gamma = B(o.gamma);
      c.ledger = o.ledger.map(B); c.ghost = B(o.ghost);
      c.flipsOuter = o.flipsOuter; c.flipsSpin = o.flipsSpin;
      c.balanceWarns = o.balanceWarns; c.warnActive = o.warnActive;
      c.rolls = o.rolls; c.wraps = o.wraps; c.lastWrapN = o.lastWrapN;
      c.logDropped = o.logDropped || 0;
      c.logDroppedEvents = o.logDroppedEvents || 0;
      c.history = o.history ? o.history.slice() : [];
      c.tracker = new global.PiLock.FractionTracker(sieve);
      c.tracker.order = o.tracker.order;
      c.tracker.position = o.tracker.position;
      c.tracker.walker.n = o.tracker.walker.n;
      c.tracker.walker.a = B(o.tracker.walker.a);
      c.tracker.walker.b = B(o.tracker.walker.b);
      c.tracker.walker.c = B(o.tracker.walker.c);
      c.tracker.walker.d = B(o.tracker.walker.d);
      c.tracker.walker.position = o.tracker.walker.position;
      return c;
    }
  }

  global.PiLock.NestedBifClock = NestedBifClock;
  global.PiLock.bigDiv = bigDiv;
})(typeof globalThis !== "undefined" ? globalThis : self);
