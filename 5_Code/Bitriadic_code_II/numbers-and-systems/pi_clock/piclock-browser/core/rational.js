/* rational.js -- exact rational arithmetic on BigInt.
 *
 * The Python piclock uses fractions.Fraction; this is its JavaScript
 * port for the browser (WebExtensions, no build step).  JavaScript's
 * Number (IEEE 754 double) loses exactness beyond 2^53 -- the Farey
 * counts, the alpha/beta/gamma discrepancies and the Franel-Landau
 * sums therefore live on BigInt rationals (class Rat).
 *
 * Plain script (no modules): attaches to globalThis.PiLockRat.
 */

(function (global) {
  "use strict";

  function bigint(x) {
    if (typeof x === "bigint") return x;
    if (typeof x === "number" && Number.isInteger(x)) return BigInt(x);
    if (typeof x === "string") {
      const m = x.match(/^(-?\d+)(?:\/(\d+))?$/);
      if (!m) throw new Error("bad rational: " + x);
      return BigInt(m[1]);
    }
    throw new Error("cannot convert to BigInt: " + x);
  }

  function bgcd(a, b) {
    a = a < 0n ? -a : a;
    b = b < 0n ? -b : b;
    while (b) { const t = a % b; a = b; b = t; }
    return a;
  }

  const ZERO_N = 0n, ONE_N = 1n;

  class Rat {
    constructor(num, den = 1n) {
      num = bigint(num); den = bigint(den);
      if (den === ZERO_N) throw new Error("Rat: zero denominator");
      if (den < ZERO_N) { num = -num; den = -den; }
      const g = bgcd(num, den);
      if (g > ONE_N) { num /= g; den /= g; }
      this.n = num; this.d = den;      // frozen by convention
    }

    static parse(s) {
      const m = String(s).match(/^(-?\d+)(?:\/(\d+))?$/);
      if (!m) throw new Error("Rat.parse: " + s);
      return new Rat(m[1], m[2] || 1n);
    }

    add(o) { return new Rat(this.n * o.d + o.n * this.d, this.d * o.d); }
    sub(o) { return new Rat(this.n * o.d - o.n * this.d, this.d * o.d); }
    mul(o) { return new Rat(this.n * o.n, this.d * o.d); }
    div(o) {
      if (o.n === ZERO_N) throw new Error("Rat: division by zero");
      return new Rat(this.n * o.d, this.d * o.n);
    }
    neg() { return new Rat(-this.n, this.d); }
    abs() { return this.n < ZERO_N ? this.neg() : this; }

    cmp(o) {
      const l = this.n * o.d, r = o.n * this.d;
      return l < r ? -1 : l > r ? 1 : 0;
    }
    eq(o) { return this.n === o.n && this.d === o.d; }
    isZero() { return this.n === ZERO_N; }
    sign() { return this.n < ZERO_N ? -1 : this.n > ZERO_N ? 1 : 0; }

    /** floor toward -infinity (exact) */
    floor() {
      const q = this.n / this.d;      // BigInt division truncates
      return this.n % this.d !== ZERO_N && this.n < ZERO_N ? q - ONE_N : q;
    }
    /** truncate toward zero (Python int()) */
    trunc() { return this.n / this.d; }

    /** float value, display-only (exactness lives in the Rat).  Safe
     * for extreme parts (e.g. 2^-1074 subnormals) by scaling the
     * denominator into range with exact powers of two. */
    toNumber() {
      const LIM = 9007199254740992n;                  // 2^53
      let neg = this.n < ZERO_N;
      let n = neg ? -this.n : this.n;
      if (n < LIM && this.d < LIM) return Number(this.n) / Number(this.d);
      let d = this.d, dshift = 0;
      while (d >= LIM) { d >>= 1n; dshift++; }
      let nshift = 0;
      while (n >= LIM) { n >>= 1n; nshift++; }
      const val = Number(n) / Number(d) * Math.pow(2, nshift - dshift);
      return neg ? -val : val;
    }
    toString() { return this.d === ONE_N ? String(this.n)
                                         : this.n + "/" + this.d; }

    /** decimal expansion to `digits` places (for display only) */
    toDecimal(digits = 10) {
      const neg = this.n < ZERO_N;
      let num = neg ? -this.n : this.n;
      let s = (num / this.d).toString();
      let rem = num % this.d;
      if (rem === ZERO_N && digits === 0) return (neg ? "-" : "") + s;
      let frac = "";
      for (let k = 0; k < digits && rem !== ZERO_N; k++) {
        rem *= 10n;
        frac += (rem / this.d).toString();
        rem %= this.d;
      }
      return (neg ? "-" : "") + s + (frac ? "." + frac : "");
    }
  }

  const R0 = new Rat(0n), R1 = new Rat(1n);

  global.PiLockRat = { Rat, R0, R1, bgcd, bigint };
})(typeof globalThis !== "undefined" ? globalThis : self);
