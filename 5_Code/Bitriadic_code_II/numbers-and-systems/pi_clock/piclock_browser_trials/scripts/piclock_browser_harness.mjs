#!/usr/bin/env node
/* Cross-check the JS core (BigInt) against the authoritative Python
 * reference (assets/reference.json, produced by the VERIFIED Python
 * piclock package on fractions.Fraction).  Every check is exact.
 *
 *   node scripts/piclock_browser_harness.mjs
 */

import { readFileSync } from "node:fs";

const ROOT = "/home/z/my-project/download/piclock-browser";

// load the plain-script cores into this module's globalThis
globalThis.globalThis = globalThis;
(0, eval)(readFileSync(`${ROOT}/core/rational.js`, "utf8"));
(0, eval)(readFileSync(`${ROOT}/core/piclock.js`, "utf8"));

const { Rat, TotientSieve, PiClock, Trinumeral, FareyWalker,
        FractionTracker, franelLandau, squareFreeCount, exactDouble,
        serializeSnapshot } = globalThis.PiLock;

const ref = JSON.parse(readFileSync(`${ROOT}/assets/reference.json`,
  "utf8"));

let pass = 0, fail = 0;
function check(name, ok, detail = "") {
  if (ok) { pass++; }
  else { fail++; console.log(`  FAIL  ${name}  ${detail}`); }
}

// -- 1. the totient sieve (computed) vs the Python reference --------
console.log("[1] totient sieve + summatory totient Phi(n)");
{
  const sieve = new TotientSieve(10000);
  for (const [n, [phiSum, size]] of Object.entries(ref.phi_sums)) {
    check(`phiSum(${n})`, sieve.phiSum(+n) === phiSum,
      `${sieve.phiSum(+n)} != ${phiSum}`);
    check(`fareySize(${n})`, sieve.fareySize(+n) === size);
  }
}

// -- 2. the totient asset (totients.bin) vs the computed sieve -------
console.log("[2] the totients.bin asset matches the computed sieve");
{
  const buf = readFileSync(`${ROOT}/assets/totients.bin`);
  const u32 = new Uint32Array(buf.buffer, buf.byteOffset,
                              buf.byteLength / 4);
  const fromAsset = new TotientSieve(u32);
  const computed = new TotientSieve(10000);
  let ok = true;
  for (let k = 1; k <= 10000; k += 97) ok = ok && fromAsset.phi(k) === computed.phi(k);
  ok = ok && fromAsset.phi(10000) === computed.phi(10000)
           && fromAsset.phiSum(10000) === computed.phiSum(10000);
  check("asset == computed (sampled + endpoints)", ok);
}

// -- 3. the pi-cycle law: pi_hat = pi (I-3)/I exactly ----------------
console.log("[3] the pi-cycle law 2F/I = pi(I-3)/I");
{
  const clk = new PiClock({ region: "half" });
  for (const [I, expected] of Object.entries(ref.pi_law)) {
    while (Number(clk.I) < +I) clk.tick();
    check(`ratio at I=${I}`,
      clk.ratio().toPrecision(17) === Number(expected).toPrecision(17),
      `${clk.ratio()} != ${expected}`);
    // the exact-layer reading matches the closed form exactly; the F
    // REGISTER is fold-wrapped (Path 6) and must stay bounded
    check(`Fexact at I=${I}`,
      clk.Fexact === (Math.PI / 2) * (+I - 3));
    check(`F tracks Fexact, unbounded below 2^52 at I=${I}`,
      clk.F <= PiLock.PRECISION_BOUND
      && Math.abs(clk.F - clk.Fexact) <= 1e-9 * clk.Fexact,
      `F=${clk.F}`);
  }
  // error law: -3 pi / I
  const I = Number(clk.I);
  check("error law -3pi/I",
    Math.abs(clk.ratio() - Math.PI + 3 * Math.PI / I) < 1e-15);
  // full region -> 2 pi
  const full = new PiClock({ region: "full" });
  while (Number(full.I) < 1000) full.tick();
  check("full region ratio = 2pi(I-2)/I",
    Math.abs(full.ratio() - 2 * Math.PI * 998 / 1000) < 1e-12);
}

// -- 4. the Farey walk: the I-th fraction of the current order -------
console.log("[4] the Farey walk (I-th fraction of F_n)");
{
  const sieve = new TotientSieve(10000);
  const tracker = new FractionTracker(sieve);
  const clk = new PiClock({ region: "half" });
  for (const [I, exp] of Object.entries(ref.farey_walk)) {
    while (Number(clk.I) < +I) clk.tick();
    const [a, b] = tracker.sync(clk.n, clk.I);
    check(`fraction at I=${I}`,
      a === BigInt(exp.kth_fraction[0]) &&
      b === BigInt(exp.kth_fraction[1]) &&
      clk.n === exp.order,
      `${a}/${b} @ n=${clk.n} != ${exp.kth_fraction.join("/")} @ ${exp.order}`);
  }
  // walker length agreement: |F_n|
  const w = new FareyWalker(10);
  let count = 1;
  while (w.next() !== null) count++;
  check("walker enumerates |F_10| = 33 terms", count === 33);
}

// -- 5. Franel-Landau audits, exact ----------------------------------
console.log("[5] Franel-Landau exact sums vs Python Fraction");
{
  const sieve = new TotientSieve(10000);
  for (const [n, exp] of Object.entries(ref.franel_landau)) {
    const r = franelLandau(+n, sieve);
    check(`franel sum d^2 at n=${n}`,
      r.franel.toString() === exp.franel_sum_sq,
      `${r.franel} != ${exp.franel_sum_sq}`);
    check(`landau sum |d| at n=${n}`,
      r.landau.toString() === exp.landau_sum_abs);
    check(`m_n at n=${n}`, r.m_n === exp.m_n);
  }
}

// -- 6. the trinumeral cycle: sheets, discrepancies, ledger ----------
console.log("[6] the trinumeral cycle (12 ticks, exact)");
{
  const T = Trinumeral.omega0(Rat.parse("1/10"));
  const init = ref.trinumeral_initial;
  const [a0, b0, g0] = T.freshDiscrepancies();
  check("initial B sheet", T.B === init.B, T.B);
  check("initial alpha", a0.toString() === init.alpha);
  check("initial beta", b0.toString() === init.beta);
  check("initial gamma", g0.toString() === init.gamma);
  check("initial ledger", [0, 1, 2].every(e =>
    (T.tau[e] || Rat.parse("0")).toString() === init.ledger[e]));

  for (const exp of ref.trinumeral_cycle) {
    const conv = [() => T.bin2int(), () => T.int2float(),
                  () => T.float2bin()][exp.tick % 3];
    // reference ticks are 1-indexed with edge (tick-1) % 3
    const convRef = [() => T.bin2int(), () => T.int2float(),
                     () => T.float2bin()][(exp.tick - 1) % 3];
    convRef();
    const [a, b, g] = T.freshDiscrepancies();
    check(`tick ${exp.tick} B`, T.B === exp.B);
    check(`tick ${exp.tick} i`, T.i === BigInt(exp.i));
    check(`tick ${exp.tick} f`, T.f === Number(exp.f));
    check(`tick ${exp.tick} alpha`, a.toString() === exp.alpha);
    check(`tick ${exp.tick} beta`, b.toString() === exp.beta);
    check(`tick ${exp.tick} gamma`, g.toString() === exp.gamma);
    check(`tick ${exp.tick} telescope`,
      a.add(b).add(g).eq(Rat.parse("0")) && exp.telescope);
    check(`tick ${exp.tick} ledger`,
      [0, 1, 2].every(e => (T.tau[e] || Rat.parse("0")).toString()
        === exp.ledger[e]),
      [0, 1, 2].map(e => (T.tau[e] || Rat.parse("0")).toString()).join(","));
    check(`tick ${exp.tick} ghost`, T.ghost.toString() === exp.ghost);
    check(`tick ${exp.tick} tauCycle`,
      T.tauCycle().toString() === exp.tau_cycle);
  }
}

// -- 7. the machine's embedded trinumeral matches the standalone -----
console.log("[7] the PiClock machine embeds the same trinumeral");
{
  const clk = new PiClock({ value: "1/10" });
  const T = Trinumeral.omega0(Rat.parse("1/10"));
  for (let k = 1; k <= 12; k++) {
    const snap = clk.tick();
    const exp = ref.trinumeral_cycle[k - 1];
    check(`machine tick ${k} alpha`,
      snap.alpha.toString() === exp.alpha);
    check(`machine tick ${k} ledger`,
      snap.ledger.every((x, e) => x.toString() === exp.ledger[e]));
    check(`machine tick ${k} telescope`, snap.telescope);
    check(`machine tick ${k} sigma`,
      snap.sigma === (Math.floor(snap.angle / 360) % 2 === 0 ? 1 : -1));
  }
  // round trip: sigma = -1 after one round trip (3 ticks), +1 after 2
  const q = new PiClock({});
  q.tick(); q.tick(); q.tick();
  check("sigma -1 after one round trip", q.phase.sigma === -1);
  q.tick(); q.tick(); q.tick();
  check("sigma +1 after two round trips", q.phase.sigma === 1);
}

// -- 8. square-free counts (the pi^2 identity layer) ------------------
console.log("[8] square-free counts vs Python");
{
  for (const [N, sf] of Object.entries(ref.square_free)) {
    check(`SF(${N})`, squareFreeCount(+N) === sf,
      `${squareFreeCount(+N)} != ${sf}`);
  }
}

// -- 9. epochs, folds, serialization round-trip ------------------------
console.log("[9] precision folds (the 2^52 boundary) + JSON round-trip");
{
  const clk = new PiClock({});
  for (let k = 0; k < 1000; k++) clk.tick();
  check("no fold below the bound in 1000 ticks",
    clk.wraps === 0 && clk.lastWrapN === 0);
  check("I and Ireg never reset", clk.Ireg === Number(clk.I)
    && Number(clk.I) === 1000);
  check("B mask never cleared", clk.B !== 0n);
  check("precision bound constant", PiLock.PRECISION_BOUND === 2 ** 52);

  // synthetic injection: force F past the boundary, then tick
  const inj = new PiClock({});
  for (let k = 0; k < 10; k++) inj.tick();
  inj.pastFixed = true;
  inj.F = PiLock.PRECISION_BOUND + 100;
  const sf = inj.tick();
  check("PRECISION_FOLD fires past 2^52",
    sf.fold === true && inj.wraps === 1);
  check("F wrapped into [0, 2pi)",
    inj.F >= 0 && inj.F < 2 * Math.PI, `F=${inj.F}`);
  const expectN = Math.floor((PiLock.PRECISION_BOUND + 100
    + Math.PI / 2) / (2 * Math.PI));
  check("wrap count n = floor(F/2pi)", inj.lastWrapN === expectN,
    `${inj.lastWrapN} != ${expectN}`);
  const In = Number(inj.I);
  check("ratio unaffected (the exact layer governs)",
    Math.abs(sf.ratio - Math.PI * (In - 3) / In) < 1e-15);
  const sf2 = inj.tick();
  check("no immediate refold", sf2.fold === false && inj.wraps === 1);

  // the Ouroboros epoch machinery is gone
  check("no epoch constants exported",
    PiLock.EPOCH_TICKS === undefined && PiLock.FOLD_TICK === undefined
    && PiLock.FOLD_EDGE === undefined);

  // migration: a state JSON written by the Ouroboros build (no wraps
  // field) loads with wraps defaulting to 0
  const old = new PiClock({ value: "1/3" });
  for (let k = 0; k < 50; k++) old.tick();
  const legacyJSON = JSON.parse(JSON.stringify(old.toJSON()));
  delete legacyJSON.wraps; delete legacyJSON.lastWrapN;
  const migrated = PiClock.fromJSON(legacyJSON);
  check("Ouroboros-era state migrates (wraps default 0)",
    migrated.wraps === 0 && Number(migrated.I) === 50);
  // serialize -> restore -> continue: identical continuation
  const a = new PiClock({ value: "1/3" });
  for (let k = 0; k < 777; k++) a.tick();
  const json = JSON.stringify(a.toJSON());
  const b = PiLock.PiClock.fromJSON(JSON.parse(json));
  const s1 = a.tick(), s2 = b.tick();
  check("round-trip: same I", s1.I === s2.I);
  check("round-trip: same ratio", s1.ratio === s2.ratio);
  check("round-trip: same sheets",
    s1.sheetB === s2.sheetB && s1.sheetI === s2.sheetI
    && s1.sheetF === s2.sheetF);
  check("round-trip: same alpha", s1.alpha.toString() === s2.alpha.toString());
  check("round-trip: same ledger",
    s1.ledger.every((x, e) => x.toString() === s2.ledger[e].toString()));
  check("round-trip: same ghost", s1.ghost.toString() === s2.ghost.toString());
  // serializeSnapshot is JSON-able
  const snap = serializeSnapshot(b.snapshot());
  check("serializeSnapshot JSON round-trip",
    JSON.parse(JSON.stringify(snap)).I === b.I.toString());
}

// -- 10. exactDouble: every small double round-trips exactly ----------
console.log("[10] exactDouble bit-exactness");
{
  let ok = true;
  for (const x of [0.1, 1 / 3, 0.5, 123.456, 1e-7, 2 ** -1074,
                   1e300, 42]) {
    const r = exactDouble(x);
    ok = ok && r.toNumber() === x;
  }
  ok = ok && exactDouble(0.1).toString() === "3602879701896397/36028797018963968";
  check("exactDouble on samples", ok);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
