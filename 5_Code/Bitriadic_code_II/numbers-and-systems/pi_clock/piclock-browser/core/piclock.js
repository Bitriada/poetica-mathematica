/* piclock.js -- the pi-clock machine, ported to exact BigInt JavaScript.
 *
 * The Python original (download/piclock, verified by the W1-W12 trial
 * battery) runs on fractions.Fraction; this port runs on BigInt
 * rationals (PiLockRat.Rat).  JavaScript Numbers are used ONLY where
 * the Python original uses floats: the F register (an IEEE double per
 * the monograph, sec. 8.2) and the transcendental evaluations (pi,
 * log).  Every count, discrepancy, ledger entry and Franel-Landau sum
 * is exact.
 *
 * THE PI-CYCLE (sec. 8.9, settled by the trials):
 *   I counts Farey fractions: I = |F_n| = 1 + Phi(n) at order n
 *   F accumulates (pi/2) per fraction (half region)
 *   2F/I = pi (1 - 3/I)  EXACTLY  ->  error = -3 pi / I
 *
 * THE FOLD is the NUMERICAL PRECISION BOUNDARY, not a lattice constant
 * (the Ouroboros epoch 232 = 2*117-2 is retired): F is an operational
 * accumulator -- the accumulation is the metaphor of time -- and it
 * folds when F + pi/2 starts rounding the increment, i.e. when
 * F > 2^52 (the ulp of a double at that magnitude is 1, so an
 * increment of pi/2 no longer lands on a representable neighbour).
 * At the fold: F <- F - n*2pi with n = floor(F/2pi); the exact layer
 * F_exact = (pi/2)(I-3) keeps the ratio observable; the event is
 * logged as a PRECISION_FOLD.  No B clear, no I reload: B is BigInt
 * (unbounded), I never resets -- transfinite running.
 *
 * Plain script (no modules): attaches to globalThis.PiLock.
 * Used by: background service worker (importScripts), content widget,
 * toolbar popup, the bundled demo page and the Node test harness.
 */

(function (global) {
  "use strict";

  const { Rat, R0, R1 } = global.PiLockRat;
  const PI = Math.PI;
  const PRECISION_BOUND = 2 ** 52;  // F folds when F > 2^52 (ulp = 1)
  const DEFAULT_P = 53;             // fractional bits (IEEE 754 mantissa)

  // ---------------------------------------------------------------- sieve
  class TotientSieve {
    constructor(maxN) {
      if (maxN instanceof Uint32Array) {
        this._phi = [0].concat(Array.from(maxN));
      } else {
        this._phi = this._compute(maxN);
      }
      this._rebuildSums();
    }

    _compute(n) {
      const phi = new Array(n + 1);
      for (let k = 0; k <= n; k++) phi[k] = k;
      for (let p = 2; p <= n; p++) {
        if (phi[p] === p) {                    // p prime
          for (let m = p; m <= n; m += p) phi[m] -= Math.floor(phi[m] / p);
        }
      }
      return phi;
    }

    _rebuildSums() {
      this.sum = [0];
      let acc = 0;
      for (let k = 1; k < this._phi.length; k++) {
        acc += this._phi[k];                   // exact: << 2^53 here
        this.sum[k] = acc;
      }
    }

    ensure(n) {
      if (n >= this._phi.length - 1) {
        const grow = Math.max(2 * this._phi.length, n + 8);
        this._phi = this._compute(grow);
        this._rebuildSums();
      }
    }

    phi(k) { this.ensure(k); return this._phi[k]; }
    phiSum(n) { this.ensure(n); return this.sum[n]; }
    fareySize(n) { return this.phiSum(n) + 1; }          // |F_n| (Number)
    fareySizeBig(n) { return BigInt(this.fareySize(n)); }
  }

  // ---------------------------------------------------------- farey walk
  /** Walks F_n term by term, exactly (BigInt pairs), via the standard
   * next-term recurrence k = floor((n + b) / d).  The UI layer uses it
   * to show the current fraction; the machine itself stays O(1)/tick. */
  class FareyWalker {
    constructor(n) { this.reset(n); }

    reset(n) {
      this.n = n;
      this.a = 0n; this.b = 1n; this.c = 1n; this.d = BigInt(n);
      this.position = 1;                       // term #1 is 0/1
    }

    /** advance to the next term; returns [a, b] or null at the end */
    next() {
      if (this.b === 1n && this.a === 1n) return null;   // ended at 1/1
      const k = Math.floor((this.n + Number(this.b)) / Number(this.d));
      const ka = BigInt(k) * this.c - this.a;
      const kb = BigInt(k) * this.d - this.b;
      this.a = this.c; this.b = this.d; this.c = ka; this.d = kb;
      this.position++;
      return [this.a, this.b];
    }

    current() { return [this.a, this.b]; }

    /** rebuild the walker at `position` of F_n (used on order rollover) */
    seek(n, position) {
      this.reset(n);
      while (this.position < position && this.next()) { /* skip */ }
      return this.current();
    }
  }

  /** UI-side tracker: keeps the current fraction of F_n at tick I,
   * advancing incrementally, rebuilding once per order rollover. */
  class FractionTracker {
    constructor(sieve) {
      this.sieve = sieve;
      this.walker = new FareyWalker(1);
      this.order = 1;
      this.position = 1;
    }

    sync(n, IBig) {
      const I = Number(IBig);
      if (I < 1) return [0n, 1n];
      if (n !== this.order) {
        this.order = n;
        this.position = Math.min(I, this.sieve.fareySize(n));
        return this.walker.seek(n, this.position);
      }
      const size = this.sieve.fareySize(n);
      const target = Math.min(I, size);
      while (this.position < target && this.walker.next()) this.position++;
      return this.walker.current();
    }
  }

  // ------------------------------------------------------- exact doubles
  /** The exact rational value of an IEEE 754 double (Python:
   * Fraction(*f.as_integer_ratio())). */
  function exactDouble(f) {
    if (!Number.isFinite(f)) throw new Error("exactDouble: not finite");
    const buf = new ArrayBuffer(8);
    new DataView(buf).setFloat64(0, f);
    const bits = new DataView(buf).getBigUint64(0);
    const sign = (bits >> 63n) === 1n ? -1n : 1n;
    const expField = Number((bits >> 52n) & 0x7ffn);
    const mant = bits & 0xfffffffffffffn;
    let num, exp;
    if (expField === 0) { num = mant; exp = -1074; }       // subnormal
    else { num = mant | 0x10000000000000n; exp = expField - 1075; }
    if (num === 0n) return R0;
    if (exp >= 0) return new Rat(sign * (num << BigInt(exp)), 1n);
    return new Rat(sign * num, 1n << BigInt(-exp));
  }

  /** The nearest double to an exact rational (Python: float(Fraction)).
   * Both parts must be exactly representable (< 2^53); IEEE division
   * then rounds the TRUE quotient once -- correctly rounded. */
  function ratToDouble(v) {
    const n = v.abs().n, d = v.d;
    if (n <= 9007199254740991n && d <= 9007199254740991n) {
      const q = Number(v.n) / Number(v.d);
      return Object.is(q, -0) ? 0 : q;
    }
    throw new Error("ratToDouble: |parts| > 2^53 (choose a simpler "
                    + "start value)");
  }

  // --------------------------------------------------------- trinumeral
  /** The Trinumeral (Ch. VIII sec. 8.4), ported: three sheets
   * (B binary string, i BigInt, f double) + the grade-1 trace ledger
   * with the (trigger 1, response 1) annihilation ladder. */
  class Trinumeral {
    constructor(B, i, f, p = DEFAULT_P) {
      this.B = B; this.i = i; this.f = f; this.p = p;
      this.tau = {};                    // edge -> Rat (grade 1 only)
      this.ghost = R0;
      this.edgeMemory = {};             // edge -> {last, spent, runAny}
    }

    static encodeBinary(v, p = DEFAULT_P) {
      const neg = v.sign() < 0;
      const m = v.abs();
      const intPart = m.floor();
      let frac = m.sub(new Rat(intPart, 1n));
      const intBits = intPart === 0n ? "0" : intPart.toString(2);
      let fracBits = "";
      for (let k = 0; k < p; k++) {
        frac = frac.mul(new Rat(2n));
        const bit = frac.cmp(R1) >= 0;
        fracBits += bit ? "1" : "0";
        if (bit) frac = frac.sub(R1);
      }
      return (neg ? "-" : "") + intBits + "." + fracBits;
    }

    static canonical(B) {
      B = B.trim();
      const sign = B.startsWith("-") ? -1n : 1n;
      B = B.replace(/^[+-]/, "");
      const dot = B.indexOf(".");
      const intBits = dot >= 0 ? B.slice(0, dot) : B;
      const fracBits = dot >= 0 ? B.slice(dot + 1) : "";
      let q = intBits ? new Rat(BigInt("0b" + intBits), 1n) : R0;
      for (let j = 1; j <= fracBits.length; j++) {
        if (fracBits[j - 1] === "1") {
          q = q.add(new Rat(1n, 1n << BigInt(j)));
        }
      }
      return new Rat(sign * q.n, q.d);
    }

    static omega0(v) {
      const T = new Trinumeral(Trinumeral.encodeBinary(v), v.trunc(),
                               ratToDouble(v));
      const [a, b, g] = T.freshDiscrepancies();
      T.tau = { 0: a, 1: b, 2: g };
      return T;
    }

    freshDiscrepancies() {
      const alpha = Trinumeral.canonical(this.B)
        .sub(new Rat(this.i, 1n));
      const beta = new Rat(this.i, 1n).sub(exactDouble(this.f));
      const gamma = exactDouble(this.f)
        .sub(Trinumeral.canonical(this.B));      // "stored" mode
      return [alpha, beta, gamma];
    }

    /** the annihilation ladder, regime (1, 1): exact consecutive
     * repeat fires; the pair cancels and the ghost keeps the total
     * magnitude (sec. 8.4.3a Level 1, corrected variant C3). */
    record(edge, alpha) {
      const mem = this.edgeMemory[edge] ||
        (this.edgeMemory[edge] = { last: null, spent: false, runAny: 0 });
      if (mem.spent && mem.last && alpha.eq(mem.last)) return R0;
      const t = this.tau[edge] || R0;
      const fire = mem.last !== null && alpha.eq(mem.last) && !t.isZero();
      let newT, transfer;
      if (!fire) { newT = t.add(alpha); transfer = R0; }
      else {
        newT = R0;
        transfer = t.abs().add(alpha.abs());
        this.ghost = this.ghost.add(transfer);
        if (alpha.eq(mem.last)) mem.spent = true;
      }
      if (newT.isZero()) delete this.tau[edge]; else this.tau[edge] = newT;
      mem.last = alpha; mem.runAny++;
      return transfer;
    }

    bin2int() {                    // e1: i' = int(canonical(B))
      const iNew = Trinumeral.canonical(this.B).trunc();
      this.record(0, new Rat(iNew - this.i, 1n));
      this.i = iNew;
      return this;
    }

    int2float() {                  // e2: f' = float(i), exact rounding
      const fNew = Number(this.i);
      this.record(1, exactDouble(fNew).sub(new Rat(this.i, 1n)));
      this.f = fNew;
      return this;
    }

    float2bin() {                  // e3: B' = binary of exact(f), p bits
      const ef = exactDouble(this.f);
      const BNew = Trinumeral.encodeBinary(ef, this.p);
      this.record(2, Trinumeral.canonical(BNew).sub(ef));
      this.B = BNew;
      return this;
    }

    tauCycle() {                   // alpha*beta*gamma (e1^e2^e3 coeff)
      const a = this.tau[0] || R0, b = this.tau[1] || R0,
        g = this.tau[2] || R0;
      return a.mul(b).mul(g);
    }

    toJSON() {
      const tau = {};
      for (const k of Object.keys(this.tau)) tau[k] = this.tau[k].toString();
      const mem = {};
      for (const k of Object.keys(this.edgeMemory)) {
        const m = this.edgeMemory[k];
        mem[k] = { last: m.last ? m.last.toString() : null,
                   spent: m.spent, runAny: m.runAny };
      }
      return { B: this.B, i: this.i.toString(), f: this.f, p: this.p,
               tau, ghost: this.ghost.toString(), edgeMemory: mem };
    }

    static fromJSON(o) {
      const T = new Trinumeral(o.B, BigInt(o.i), o.f, o.p);
      for (const k of Object.keys(o.tau)) T.tau[k] = Rat.parse(o.tau[k]);
      T.ghost = Rat.parse(o.ghost);
      for (const k of Object.keys(o.edgeMemory)) {
        T.edgeMemory[k] = { last: o.edgeMemory[k].last === null ? null
                            : Rat.parse(o.edgeMemory[k].last),
                            spent: o.edgeMemory[k].spent,
                            runAny: o.edgeMemory[k].runAny || 0 };
      }
      return T;
    }
  }

  // ---------------------------------------------------- spinorial tally
  /** S = total rotation in exact integer degrees; sigma flips per
   * 360-degree boundary crossing (the double cover, sec. 8.4.9). */
  class SpinorialTally {
    constructor(total = 0) {
      this.total = total;
      this.crossings = Math.floor(total / 360);
      this.sigma = this.crossings % 2 === 0 ? 1 : -1;
    }

    rotate(deg) {
      const old = this.total;
      this.total += deg;
      const c = Math.floor(this.total / 360) - Math.floor(old / 360);
      if (c % 2 !== 0) this.sigma = -this.sigma;
      this.crossings += c;
      return this;
    }

    get angle() { return this.total; }
  }

  // ------------------------------------------------- Franel-Landau audit
  /** d_{k,n} = a_{k,n} - k/m_n for the terms a_0..a_m of F_n.
   * Franel (1924): RH <=> sum d^2 = O(n^r) for all r > -1.
   * Landau (1924): RH <=> sum |d| = O(n^r) for all r > 1/2.
   * Exact BigInt rationals; capped at MAX_N for the exact form. */
  const FRANEL_MAX_N = 120;

  function franelLandau(n, sieve) {
    if (n < 1) throw new Error("n >= 1");
    if (n > FRANEL_MAX_N) throw new Error("exact audit capped at n = "
                                          + FRANEL_MAX_N);
    sieve.ensure(n);
    const m = sieve.fareySize(n) - 1;         // terms k = 0..m
    const w = new FareyWalker(n);
    let franel = R0, landau = R0, k = 0;
    for (; k <= m; k++) {
      const [p, q] = w.current();
      const d = new Rat(p, q).sub(new Rat(BigInt(k), BigInt(m)));
      franel = franel.add(d.mul(d));
      landau = landau.add(d.abs());
      if (k < m && w.next() === null) break;
    }
    return { n, m_n: m, franel, landau };
  }

  // ----------------------------------------------------------- Moebius
  /** #square-free integers in {1..N}: Sum_{d^2 <= N} mu(d) floor(N/d^2).
   * Exact (linear Moebius sieve to sqrt(N)). */
  function squareFreeCount(N) {
    const limit = Math.floor(Math.sqrt(N));
    const mu = new Array(limit + 1).fill(1);
    mu[0] = 0;
    const primes = [];
    const comp = new Array(limit + 1).fill(false);
    for (let p = 2; p <= limit; p++) {
      if (!comp[p]) { primes.push(p); mu[p] = -1; }
      for (const q of primes) {
        const x = p * q;
        if (x > limit) break;
        comp[x] = true;
        if (p % q === 0) { mu[x] = 0; break; }
        mu[x] = -mu[p];
      }
    }
    let total = 0;
    for (let d = 1; d <= limit; d++) total += mu[d] * Math.floor(N / (d * d));
    return total;
  }

  // --------------------------------------------------------------- clock
  class PiClock {
    constructor(opts = {}) {
      this.region = opts.region === "full" ? "full" : "half";
      this.sieve = opts.sieve || new TotientSieve(4096);
      this.value = opts.value || "1/10";
      this.tri = Trinumeral.omega0(Rat.parse(this.value));
      this.phase = new SpinorialTally(0);
      this.I = 0n;                 // the tick counter (BigInt, exact)
      this.Ireg = 0;               // register I (never resets now)
      this.n = 1;                  // current Farey order
      this.orderSize = 2;          // |F_1|
      this.F = 0;                  // the float register (area mode)
      this.Fturns = 0;
      this.B = 0n;                 // presence mask of spheres
      this.spheres = 0;
      this.wraps = 0;              // precision folds taken
      this.lastWrapN = 0;          // turns removed by the last fold
      this.pastFixed = false;
      this.tickCount = 0;
      this._sphereEvent();
    }

    _sphereEvent() {
      this.B |= 1n << BigInt(this.spheres % 64);
      this.spheres++;
    }

    _orderRollover() {
      this.n += 1;
      this.sieve.ensure(this.n);
      this.orderSize = this.sieve.fareySize(this.n);
      this._sphereEvent();
    }

    tick() {
      if (this.I >= BigInt(this.orderSize)) this._orderRollover();
      this.I += 1n;
      this.Ireg += 1;
      this.tickCount += 1;
      // the conversion cycle: e1 bin2int, e2 int2float, e3 float2bin
      const conv = [() => this.tri.bin2int(), () => this.tri.int2float(),
                    () => this.tri.float2bin()][(this.tickCount - 1) % 3];
      conv();
      const per = this.region === "half" ? PI / 2 : PI;
      if (this.I > (this.region === "half" ? 3n : 2n)) this.pastFixed = true;
      let fold = false;
      if (this.pastFixed) {
        this.F += per;
        this.Fturns += per / (2 * PI);
        if (this.F > PRECISION_BOUND) { this._precisionFold(); fold = true; }
      }
      this.phase.rotate(120);                 // 1/3 turn per gate
      return this.snapshot({ fold });
    }

    _precisionFold() {            // the numerical precision boundary
      const w = Math.floor(this.F / (2 * PI));
      this.F -= w * (2 * PI);               // wrap into [0, 2 pi)
      this.wraps += 1;
      this.lastWrapN = w;
      // the exact layer needs no action: Fexact = (pi/2)(I-3) by
      // formula, so the ratio 2F_exact/I stays observable forever
    }

    ratio() {
      const I = Number(this.I);
      if (I === 0) return NaN;
      return this.region === "half"
        ? PI * (I - 3) / I
        : 2 * PI * (I - 2) / I;
    }

    get Fexact() {
      const I = Number(this.I);
      return this.region === "half"
        ? (PI / 2) * Math.max(0, I - 3)
        : PI * Math.max(0, I - 2);
    }

    snapshot(extra = {}) {
      const [a, b, g] = this.tri.freshDiscrepancies();
      return Object.assign({
        tick: this.tickCount,
        I: this.I, Inum: Number(this.I), n: this.n,
        orderSize: this.orderSize,
        Ireg: this.Ireg, F: this.F, Fexact: this.Fexact,
        ratio: this.ratio(),
        error: this.ratio() - PI,
        B: this.B, spheres: this.spheres,
        wraps: this.wraps, lastWrapN: this.lastWrapN,
        alpha: a, beta: b, gamma: g,
        telescope: a.add(b).add(g).eq(R0),
        ledger: [this.tri.tau[0] || R0, this.tri.tau[1] || R0,
                 this.tri.tau[2] || R0],
        ghost: this.tri.ghost,
        tauCycle: this.tri.tauCycle(),
        sigma: this.phase.sigma, angle: this.phase.angle,
        sheetB: this.tri.B, sheetI: this.tri.i, sheetF: this.tri.f,
        region: this.region,
      }, extra);
    }

    toJSON() {
      return { region: this.region, value: this.value,
               tri: this.tri.toJSON(), phaseTotal: this.phase.total,
               I: this.I.toString(), Ireg: this.Ireg, n: this.n,
               orderSize: this.orderSize, F: this.F, Fturns: this.Fturns,
               B: this.B.toString(), spheres: this.spheres,
               wraps: this.wraps, lastWrapN: this.lastWrapN,
               pastFixed: this.pastFixed,
               tickCount: this.tickCount };
    }

    static fromJSON(o, sieve) {
      const c = new PiClock({ region: o.region, value: o.value, sieve });
      c.tri = Trinumeral.fromJSON(o.tri);
      c.phase = new SpinorialTally(o.phaseTotal);
      c.I = BigInt(o.I); c.Ireg = o.Ireg; c.n = o.n;
      c.orderSize = o.orderSize; c.F = o.F; c.Fturns = o.Fturns;
      c.B = BigInt(o.B); c.spheres = o.spheres;
      // migration: states written by the Ouroboros build (epoch,
      // tickInEpoch, folds, ghostEpochs, fiducial) fold differently --
      // their F was unit-interval wrapped and their Ireg restarted.
      // Continuing such a state is safe: the registers keep counting
      // from where they are, and no epoch fields are read again.
      c.wraps = o.wraps || 0; c.lastWrapN = o.lastWrapN || 0;
      c.pastFixed = o.pastFixed;
      c.tickCount = o.tickCount;
      return c;
    }
  }

  /** A snapshot as a plain JSON-able object (for chrome.runtime port
   * broadcasts and storage): Rats and BigInts become strings. */
  function serializeSnapshot(s) {
    const r = (x) => (x === undefined || x === null ? null : String(x));
    return {
      tick: s.tick, I: s.I.toString(), Inum: s.Inum, n: s.n,
      orderSize: s.orderSize, Ireg: s.Ireg, F: s.F, Fexact: s.Fexact,
      ratio: s.ratio, error: s.error, B: s.B.toString(),
      spheres: s.spheres, wraps: s.wraps, lastWrapN: s.lastWrapN,
      alpha: r(s.alpha), beta: r(s.beta), gamma: r(s.gamma),
      telescope: s.telescope,
      ledger: s.ledger.map(r), ghost: r(s.ghost),
      tauCycle: r(s.tauCycle), sigma: s.sigma, angle: s.angle,
      sheetB: s.sheetB, sheetI: s.sheetI.toString(),
      sheetF: s.sheetF, region: s.region,
      fold: !!s.fold,
    };
  }

  // --------------------------------------------------------------- export
  global.PiLock = {
    TotientSieve, FareyWalker, FractionTracker, Trinumeral,
    SpinorialTally, PiClock, franelLandau, squareFreeCount,
    exactDouble, ratToDouble, serializeSnapshot,
    PRECISION_BOUND, FRANEL_MAX_N, DEFAULT_P, PI,
    Rat,
  };
})(typeof globalThis !== "undefined" ? globalThis : self);
