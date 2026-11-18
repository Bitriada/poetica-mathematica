/* demo.js -- the full-page pi-clock instrument.
 *
 * Runs a LOCAL PiClock instance (exact BigInt machine) with
 * requestAnimationFrame batching; the chart shows the lock-in onto pi
 * and the scaled error  -error*I/(3pi), which sits flat at 1: the
 * error law, visible. All numbers on this page are computed by the
 * same core the extension ships (core/piclock.js).
 */

(function () {
  "use strict";
  const { PiClock, TotientSieve, FractionTracker, franelLandau,
          squareFreeCount, PRECISION_BOUND } = PiLock;
  const PI = Math.PI;
  const PI_STR = "3.14159265358979323846";

  const $ = (id) => document.getElementById(id);
  const sieve = new TotientSieve(10000);
  let clock = new PiClock({ region: "half", value: "1/10", sieve });
  let tracker = new FractionTracker(sieve);
  let running = false, tps = 4, acc = 0, lastT = 0;
  const hist = [];

  // the B mask cells
  const maskEl = $("mask");
  for (let k = 0; k < 64; k++) maskEl.appendChild(document.createElement("i"));
  const maskCells = Array.from(maskEl.children);
  // the meter fill is set in render (F vs the 2^52 boundary)

  function fmt(n) { return Number(n).toLocaleString("en-US"); }

  function render() {
    const s = clock.snapshot();
    // digit-lock big readout
    const str = s.ratio.toFixed(13);
    let lock = 0;
    while (lock < str.length && str[lock] === PI_STR[lock]) lock++;
    $("bigPi").innerHTML =
      `<span class="lock">${str.slice(0, lock)}</span>` +
      `<span class="free">${str.slice(lock)}</span>`;
    const law = -3 * PI / s.Inum;
    $("lawLine").innerHTML =
      `error ${s.error >= 0 ? "+" : ""}${s.error.toExponential(4)}` +
      ` &nbsp;≡&nbsp; −3π/I = ${law.toExponential(4)}` +
      ` &nbsp;·&nbsp; ${s.telescope
        ? '<span class="ok">telescope α+β+γ = 0 ✓</span>'
        : "TELESCOPE BROKEN"}`;
    $("vI").textContent = fmt(s.I);
    $("vN").textContent = `${s.n} · ${fmt(s.orderSize)}`;
    $("vF").textContent = `${s.F.toFixed(5)} (${s.Fexact.toFixed(1)} unwrapped)`;
    $("vSph").textContent = `${s.spheres} · ${s.wraps}`;
    const frac = tracker.sync(s.n, s.I);
    $("vFrac").textContent = `${frac[0]}/${frac[1]}`;
    $("vSig").textContent = `${s.sigma > 0 ? "+1" : "−1"} · ${s.angle}°`;
    // the mask
    let B = s.B;
    for (let k = 0; k < 64; k++) {
      maskCells[k].classList.toggle("on", (B & 1n) === 1n);
      B >>= 1n;
    }
    // the precision meter (F vs 2^52)
    $("epochFill").style.width =
      (100 * Math.min(1, s.F / PRECISION_BOUND)).toPrecision(3) + "%";
    $("epochLbl").textContent =
      `F ${s.F.toExponential(2)} / 2²⁵² · wraps ${s.wraps}` +
      (s.fold ? " · PRECISION_FOLD" : "");
    // trinumeral
    $("tB").textContent = s.sheetB.slice(0, 40) + "…" + s.sheetB.slice(-16);
    $("tI").textContent = s.sheetI.toString();
    $("tF").textContent = s.sheetF.toPrecision(17);
    $("tA").textContent = s.alpha.toString();
    $("tBt").textContent = s.beta.toString();
    $("tG").textContent = s.gamma.toString();
    $("tTel").innerHTML = s.telescope
      ? '<span class="ok">= 0 exactly ✓</span>' : "≠ 0";
    $("tLed").textContent = s.ledger.map(String).join("  ·  ");
    $("tGhost").textContent = `${s.ghost}  ·  ${s.tauCycle}`;
    // identities
    $("id1").innerHTML = `2F/I = <b>${s.ratio.toPrecision(17)}</b> ·
      π(1−3/I) = ${(PI * (s.Inum - 3) / s.Inum).toPrecision(17)} ·
      identical`;
    $("id3").textContent =
      `n = ${s.n}: 3n²/π² = ${fmt(3 * s.n * s.n / (PI * PI))}` +
      ` vs |Fₙ| = ${fmt(s.orderSize)}  (ratio ` +
      (s.orderSize / (3 * s.n * s.n / (PI * PI))).toFixed(5) + " → 1)";
    // history
    if (s.Inum > 3) {
      hist.push({ I: s.Inum, ratio: s.ratio,
                  scaled: -s.error * s.Inum / (3 * PI) });
      if (hist.length > 3000) hist.shift();
    }
    drawChart();
    return s;
  }

  function drawChart() {
    const cv = $("chart");
    const ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    if (hist.length < 2) return;
    const x0 = Math.log10(hist[0].I), x1 = Math.log10(hist[hist.length - 1].I);
    const xr = Math.max(1e-9, x1 - x0);
    const X = (I) => 14 + (W - 28) * (Math.log10(I) - x0) / xr;

    // lane 1: pi-hat vs pi
    let lo = Infinity, hi = -Infinity;
    for (const p of hist) { lo = Math.min(lo, p.ratio); hi = Math.max(hi, p.ratio); }
    const pad = Math.max((hi - lo) * 0.18, 1e-4);
    lo -= pad; hi += pad;
    const H1 = H * 0.56 - 10;
    const Y1 = (v) => 10 + H1 * (1 - (v - lo) / (hi - lo));
    ctx.strokeStyle = "#334155"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, Y1(PI)); ctx.lineTo(W, Y1(PI)); ctx.stroke();
    ctx.strokeStyle = "#38bdf8"; ctx.lineWidth = 4;
    ctx.beginPath();
    hist.forEach((p, k) => { const x = X(p.I), y = Y1(p.ratio);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "#facc15"; ctx.font = "26px monospace";
    ctx.fillText("π", 8, Y1(PI) - 8);
    ctx.fillStyle = "#38bdf8"; ctx.font = "20px monospace";
    ctx.fillText("2F/I", 8, 34);

    // lane 2: the scaled error (flat at 1 = the law)
    const y0 = H * 0.62, y1 = H - 12;
    const Y2 = (v) => y1 - (y1 - y0) * Math.min(1.2, Math.max(0, v / 2));
    ctx.strokeStyle = "#334155"; ctx.setLineDash([9, 7]); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, Y2(1)); ctx.lineTo(W, Y2(1)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = "#f472b6"; ctx.lineWidth = 3;
    ctx.beginPath();
    hist.forEach((p, k) => { const x = X(p.I), y = Y2(p.scaled);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "#f472b6"; ctx.font = "20px monospace";
    ctx.fillText("−error·I/(3π) ≡ 1  — the exact law, visible", 8, y0 - 6);
  }

  // ------------------------------------------------------------ loop
  function frame(t) {
    const dt = Math.min(0.25, (t - lastT) / 1000);
    lastT = t;
    if (running) {
      acc += dt * tps;
      const due = Math.min(Math.floor(acc), 5000);
      acc -= Math.floor(acc);
      for (let k = 0; k < due; k++) clock.tick();
    }
    render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame((t) => { lastT = t; requestAnimationFrame(frame); });

  // ------------------------------------------------------------ controls
  $("btnPlay").addEventListener("click", () => {
    running = !running;
    $("btnPlay").textContent = running ? "⏸ pause" : "▶ play";
  });
  $("btnSpeed").addEventListener("click", () => {
    const speeds = [1, 4, 16, 64, 256];
    tps = speeds[(speeds.indexOf(tps) + 1) % speeds.length];
    $("btnSpeed").textContent = "×" + tps;
  });
  $("btnStep").addEventListener("click", () => {
    for (let k = 0; k < 10; k++) clock.tick();
  });
  $("btnReset").addEventListener("click", () => {
    clock = new PiClock({ region: $("selRegion").value,
      value: $("selValue").value, sieve });
    tracker = new FractionTracker(sieve);
    hist.length = 0;
  });
  $("selRegion").addEventListener("change", () => {
    const keep = Number(clock.I);
    clock = new PiClock({ region: $("selRegion").value,
      value: $("selValue").value, sieve });
    tracker = new FractionTracker(sieve);
    hist.length = 0;
    for (let k = 0; k < keep; k++) clock.tick();
  });
  $("selValue").addEventListener("change", () => $("btnReset").click());

  // ------------------------------------------------------------ panels
  $("btnFranel").addEventListener("click", () => {
    const n = Math.max(1, Math.min(120, parseInt($("franelN").value, 10)
      || 30));
    $("franelBody").innerHTML =
      `<tr><td class="k">auditing</td><td class="v">F<sub>${n}</sub> …
       (exact BigInt, one rational per Farey term)</td></tr>`;
    setTimeout(() => {
      const r = franelLandau(n, sieve);
      const f = r.franel, l = r.landau;
      $("franelBody").innerHTML = `
        <tr><td class="k">order n · |Fₙ| = mₙ+1</td>
          <td class="v">${r.n} · ${fmt(r.m_n + 1)}</td></tr>
        <tr><td class="k">Σ d<sub>k,n</sub>² (Franel)</td>
          <td class="v">${f.toNumber().toExponential(8)} =
            ${f.toString()}</td></tr>
        <tr><td class="k">Σ |d<sub>k,n</sub>| (Landau)</td>
          <td class="v">${l.toNumber().toExponential(8)} =
            ${l.toString()}</td></tr>
        <tr><td class="k">Σ d² / mₙ</td>
          <td class="v">${(f.toNumber() / r.m_n).toExponential(4)}
            — the RH-relevant rate (→ 0 like the RH equivalent
            demands)</td></tr>`;
    }, 30);
  });

  $("btnPi2").addEventListener("click", () => {
    setTimeout(() => {
      const N = 1000000, sf = squareFreeCount(N), est = 6 * N / sf;
      $("franelBody").innerHTML = `
        <tr><td class="k">N · SF(N) exact (Möbius)</td>
          <td class="v">${fmt(N)} · ${fmt(sf)}</td></tr>
        <tr><td class="k">6N / SF(N)</td>
          <td class="v">${est.toFixed(9)}</td></tr>
        <tr><td class="k">π²</td>
          <td class="v">${(PI * PI).toFixed(9)} — relative error
            ${(est / (PI * PI) - 1).toExponential(2)}</td></tr>`;
    }, 30);
  });

  render();
})();
