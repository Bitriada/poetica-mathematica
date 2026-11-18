/* bif.js -- the Nested-Bif pi-clock comparative analyzer.
 *
 * V1 Bracket · V2 Gap-Rate · V3 Phase · V4 Trinumeral, all sharing
 * one tick cursor (hover = transient, click = anchored, log-row click
 * = jump).  The LIVE LOG has three tabs (Ticks | Events | Orders,
 * defaulting to Events -- the stream a human watches), a filter by
 * kind, pause-on-hover, click-row-to-cursor, and CSV/JSONL/JSON
 * exports.  Everything runs locally on core/nestedbif.js.
 */

(function () {
  "use strict";
  const { NestedBifClock, TotientSieve, franelLandau } = PiLock;
  const PI = Math.PI;
  const PI_STR = "3.14159265358979323846";
  const SPEEDS = [1, 4, 16, 64, 256, 1024];

  const $ = (id) => document.getElementById(id);
  const sieve = new TotientSieve(10000);
  let engine = new NestedBifClock({ sieve, logCap: 8192 });
  let running = false, tps = 4, acc = 0, lastT = 0;
  let burstRemaining = 0;
  let lastChartDraw = 0, lastLogDraw = 0;
  let ticksThisSecond = 0, lastPerfT = performance.now();

  // ------------------------------------------------------------ cursor
  const cursor = { hoverB: null, anchorB: null };
  let cursorDirty = true;

  function cursorB() {
    return cursor.anchorB !== null ? cursor.anchorB : cursor.hoverB;
  }

  /** binary search the ring (ascending B) for the snapshot at B */
  function snapAt(B) {
    const log = engine.tickLog;
    if (!log.length) return null;
    let lo = 0, hi = log.length - 1;
    if (B <= log[0].B) return { s: log[0], clamped: B < log[0].B };
    if (B >= log[hi].B) return { s: log[hi], clamped: B > log[hi].B };
    while (lo + 1 < hi) {
      const mid = (lo + hi) >> 1;
      if (log[mid].B <= B) lo = mid; else hi = mid;
    }
    return { s: log[lo], clamped: false };
  }

  function renderReadout() {
    const el = $("cursorReadout");
    const B = cursorB();
    if (B === null || !engine.tickLog.length) {
      el.innerHTML = "shared cursor: hover any chart to inspect a tick" +
        " · click to anchor · click a log row to jump — the cursor is" +
        " shared by V1–V4";
      return;
    }
    const hit = snapAt(B);
    const s = hit.s;
    const anchored = cursor.anchorB !== null;
    const mid = (s.L_final + s.U_final) / 2;
    el.innerHTML =
      (anchored ? "" : "") +
      `<span class="clr" id="cursorClear" title="release the anchor">` +
      (anchored ? "✕ release" : "") + `</span>` +
      `cursor @ <b>B=${s.B.toLocaleString("en-US")}</b>` +
      (hit.clamped ? " (outside the ring — clamped)" : "") +
      (anchored ? " · <b>anchored</b>" : " · hover") +
      ` &nbsp; final [${s.L_final.toFixed(9)}, ${s.U_final.toFixed(9)}]` +
      ` width ${(s.U_final - s.L_final).toExponential(2)}` +
      ` · π̂ ${mid.toFixed(9)}` +
      ` · σ ${s.sigma > 0 ? "+1" : "−1"} · sheet ${s.sheetOuter}` +
      ` · α ${s.alpha.toLocaleString("en-US")}` +
      ` β ${s.beta.toLocaleString("en-US")}` +
      ` γ ${s.gamma.toLocaleString("en-US")}` +
      ` · balance ${s.balance.toFixed(2)}`;
    const clr = $("cursorClear");
    if (clr) clr.onclick = () => { cursor.anchorB = null; cursorDirty = true;
      renderReadout(); };
  }

  // ------------------------------------------------------------ charts
  function logXFor(pts) {
    const b0 = Math.max(1, pts[0].B), b1 = Math.max(2, pts[pts.length - 1].B);
    const x0 = Math.log10(b0), xr = Math.max(1e-9, Math.log10(b1) - x0);
    return { x0, xr, b0, b1,
      at(B, W) { return 12 + (W - 24) * (Math.log10(Math.max(1, B)) - x0) / xr; },
      inv(x, W) { return Math.round(10 ** (x0 + (x - 12) / (W - 24) * xr)); } };
  }

  function drawCursor(ctx, W, H, xOf, b0, b1) {
    const B = cursorB();
    if (B === null || B < b0 || B > b1) return;
    const x = xOf(B);
    if (cursor.anchorB !== null) {
      ctx.strokeStyle = "#facc15"; ctx.lineWidth = 2.5;
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      ctx.fillStyle = "#facc15"; ctx.font = "bold 19px monospace";
      ctx.fillText("▸" + B.toLocaleString("en-US"),
        Math.min(x + 6, W - 90), 20);
    } else {
      ctx.strokeStyle = "rgba(250,204,21,0.55)"; ctx.lineWidth = 1.5;
      ctx.setLineDash([5, 5]);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  function drawV1(pts) {
    const cv = $("chartBracket"), ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    if (pts.length < 2) return;
    const X = logXFor(pts);
    let lo = Infinity, hi = -Infinity;
    for (const p of pts) {
      lo = Math.min(lo, p.L_final, p.L_outer, p.U_final, p.U_outer);
      hi = Math.max(hi, p.L_final, p.L_outer, p.U_final, p.U_outer);
    }
    const pad = (hi - lo) * 0.12 + 1e-9;
    lo -= pad; hi = Math.max(hi + pad, PI + pad * 0.5);
    const Y = (v) => 10 + (H - 20) * (1 - (v - lo) / (hi - lo));
    ctx.strokeStyle = "#facc15"; ctx.lineWidth = 3;
    ctx.setLineDash([12, 8]);
    ctx.beginPath(); ctx.moveTo(0, Y(PI)); ctx.lineTo(W, Y(PI)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#facc15"; ctx.font = "26px monospace";
    ctx.fillText("π — the membrane", 10, Y(PI) - 9);
    ctx.lineWidth = 2; ctx.strokeStyle = "#475569";
    for (const get of [(p) => p.L_outer, (p) => p.U_outer]) {
      ctx.beginPath();
      pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(get(p));
        k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.stroke();
    }
    ctx.beginPath();
    pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(p.L_final);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    for (let k = pts.length - 1; k >= 0; k--)
      ctx.lineTo(X.at(pts[k].B, W), Y(pts[k].U_final));
    ctx.closePath();
    ctx.fillStyle = "rgba(56,189,248,0.13)"; ctx.fill();
    ctx.lineWidth = 3.5; ctx.strokeStyle = "#38bdf8";
    ctx.beginPath();
    pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(p.L_final);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.strokeStyle = "#f472b6";
    ctx.beginPath();
    pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(p.U_final);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.font = "20px monospace";
    ctx.fillStyle = "#38bdf8"; ctx.fillText("L_final", 10, 26);
    ctx.fillStyle = "#f472b6"; ctx.fillText("U_final", 110, 26);
    ctx.fillStyle = "#94a3b8"; ctx.fillText("outer", 230, 26);
    drawCursor(ctx, W, H, (B) => X.at(B, W), X.b0, X.b1);
  }

  function drawV2(pts) {
    const cv = $("chartGaps"), ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    if (pts.length < 2) return;
    const X = logXFor(pts);
    let lo = Infinity, hi = -Infinity;
    for (const p of pts) {
      lo = Math.min(lo, p.gapB, p.gapI, p.gapF, p.gapFF);
      hi = Math.max(hi, p.gapB, p.gapI, p.gapF, p.gapFF);
    }
    const yl0 = Math.log10(lo), yl1 = Math.log10(hi);
    const Y = (v) => H - 12 - (H - 26) *
      (Math.log10(Math.max(v, 1e-18)) - yl0) / Math.max(1e-9, yl1 - yl0);
    const line = (get, color, width, dash) => {
      ctx.strokeStyle = color; ctx.lineWidth = width;
      ctx.setLineDash(dash || []);
      ctx.beginPath();
      pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(get(p));
        k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.stroke(); ctx.setLineDash([]);
    };
    line((p) => p.gapFF, "#facc15", 3, [10, 7]);    // the law 3pi/I
    line((p) => p.gapB, "#94a3b8", 2.5);
    line((p) => p.gapI, "#38bdf8", 2.5);
    line((p) => p.gapF, "#a78bfa", 2.5);
    line((p) => p.U_final - p.L_final, "#f472b6", 3);
    ctx.font = "20px monospace";
    ctx.fillStyle = "#facc15"; ctx.fillText("3π/I (law / δ_target)", 10, 24);
    ctx.fillStyle = "#94a3b8"; ctx.fillText("Gap_B", 330, 24);
    ctx.fillStyle = "#38bdf8"; ctx.fillText("Gap_i", 420, 24);
    ctx.fillStyle = "#a78bfa"; ctx.fillText("Gap_f", 510, 24);
    ctx.fillStyle = "#f472b6"; ctx.fillText("final width", 600, 24);
    drawCursor(ctx, W, H, (B) => X.at(B, W), X.b0, X.b1);
  }

  function drawV3(pts) {
    const cv = $("chartPhase"), ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    const win = pts.slice(-900);
    if (win.length < 2) return;
    const b0 = win[0].B, b1 = win[win.length - 1].B;
    const X = (B) => 12 + (W - 24) * (B - b0) / Math.max(1, b1 - b0);
    const Ys = (v) => 12 + (H / 2 - 22) * (1 - (v + 1) / 2);
    ctx.strokeStyle = "#f472b6"; ctx.lineWidth = 3.5;
    ctx.beginPath();
    win.forEach((p, k) => { const x = X(p.B), y = Ys(p.sigma);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.strokeStyle = "#334155"; ctx.lineWidth = 1; ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(0, Ys(1)); ctx.lineTo(W, Ys(1));
    ctx.moveTo(0, Ys(-1)); ctx.lineTo(W, Ys(-1));
    ctx.stroke(); ctx.setLineDash([]);
    ctx.font = "17px monospace"; ctx.fillStyle = "#f472b6";
    ctx.fillText("σ — inner bif (spinorial): +1 even · −1 odd", 10, 20);
    const Yb = (v) => H - 13 - (H / 2 - 22) * v;
    ctx.strokeStyle = "#facc15"; ctx.lineWidth = 3.5;
    ctx.beginPath();
    win.forEach((p, k) => { const x = X(p.B),
      y = Yb(p.sheetOuter === "upper" ? 1 : 0);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "#facc15";
    ctx.fillText("outer bif sheet: upper · lower", 10, H - 6);
    drawCursor(ctx, W, H, X, b0, b1);
  }

  function drawV4(pts) {
    const cv = $("chartTri"), ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    if (pts.length < 2) return;
    const X = logXFor(pts);
    const top = H * 0.68, bot = H - 26;
    let lo = Infinity, hi = -Infinity;
    for (const p of pts) {
      lo = Math.min(lo, p.alpha, p.beta, p.gamma);
      hi = Math.max(hi, p.alpha, p.beta, p.gamma);
    }
    const pad = (hi - lo) * 0.08 + 1;
    lo -= pad; hi += pad;
    const Y = (v) => 12 + (top - 22) * (1 - (v - lo) / (hi - lo));
    const line = (get, color) => {
      ctx.strokeStyle = color; ctx.lineWidth = 2.5;
      ctx.beginPath();
      pts.forEach((p, k) => { const x = X.at(p.B, W), y = Y(get(p));
        k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.stroke();
    };
    // zero line (perfect sync)
    if (lo < 0 && hi > 0) {
      ctx.strokeStyle = "#334155"; ctx.lineWidth = 1;
      ctx.setLineDash([6, 6]);
      ctx.beginPath(); ctx.moveTo(0, Y(0)); ctx.lineTo(W, Y(0)); ctx.stroke();
      ctx.setLineDash([]);
    }
    line((p) => p.alpha, "#38bdf8");
    line((p) => p.beta, "#a78bfa");
    line((p) => p.gamma, "#f472b6");
    // bottom lane: ghost steps + event marks
    let gMax = 1;
    for (const p of pts) gMax = Math.max(gMax, p.ghost);
    const Yg = (v) => bot - (bot - top - 8) * (v / gMax);
    ctx.strokeStyle = "#facc15"; ctx.lineWidth = 2.5;
    ctx.beginPath();
    pts.forEach((p, k) => { const x = X.at(p.B, W), y = Yg(p.ghost);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    const marks = engine.history;
    for (const e of marks) {
      if (e.tick < X.b0 || e.tick > X.b1) continue;
      const x = X.at(e.tick, W);
      if (e.type === "OUTER_FLIP") {
        ctx.strokeStyle = "#fcd34d"; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(x, top - 4); ctx.lineTo(x, bot); ctx.stroke();
      } else if (e.type === "WARN_BALANCE") {
        ctx.strokeStyle = "#f87171"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x, bot - 10); ctx.lineTo(x, bot); ctx.stroke();
      } else if (e.type === "PRECISION_FOLD") {
        ctx.strokeStyle = "#22d3ee"; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(x, top - 4); ctx.lineTo(x, bot); ctx.stroke();
      } else if (e.type === "ORDER_ROLL") {
        ctx.fillStyle = "rgba(125,211,252,0.5)";
        ctx.fillRect(x, bot - 5, 1.5, 5);
      }
    }
    ctx.font = "19px monospace";
    ctx.fillStyle = "#38bdf8"; ctx.fillText("α = B−m", 10, 24);
    ctx.fillStyle = "#a78bfa"; ctx.fillText("β = m−n", 110, 24);
    ctx.fillStyle = "#f472b6"; ctx.fillText("γ = n−B", 210, 24);
    ctx.fillStyle = "#facc15"; ctx.fillText("ghost + flips ▮outer ▬warn ▮roll", 330, 24);
    drawCursor(ctx, W, H, (B) => X.at(B, W), X.b0, X.b1);
  }

  function drawCharts(now) {
    if (now - lastChartDraw < 120 && !cursorDirty) return;
    lastChartDraw = now; cursorDirty = false;
    const pts = engine.tickLog;
    drawV1(pts); drawV2(pts); drawV3(pts); drawV4(pts);
    chartDraws++;
  }
  let chartDraws = 0;

  // ------------------------------------------------------------ render
  function renderPiHat(mid) {
    const s = mid.toFixed(13);
    let lock = 0;
    while (lock < s.length && s[lock] === PI_STR[lock]) lock++;
    $("bigPi").innerHTML =
      `<span class="lock">${s.slice(0, lock)}</span>` +
      `<span class="free">${s.slice(lock)}</span>`;
  }

  function render(s) {
    const mid = (s.L_final + s.U_final) / 2;
    renderPiHat(mid);
    $("bigLaw").textContent =
      `final [${s.L_final.toFixed(10)}, ${s.U_final.toFixed(10)}]` +
      `  width ${(s.U_final - s.L_final).toExponential(3)}  ·  midpoint error ` +
      `${(mid - PI).toExponential(3)}  ·  telescope ` +
      (s.telescope ? "0 ✓" : "BROKEN");
    $("vB").textContent = `${s.B.toLocaleString("en-US")} · ${s.I.toLocaleString("en-US")}`;
    $("vFinal").textContent = `[${s.L_final.toFixed(9)}, ${s.U_final.toFixed(9)}]`;
    $("vGap").textContent = (s.U_final - s.L_final).toExponential(3);
    $("vContains").innerHTML = s.containsPi
      ? '<span class="badge ok">YES</span>'
      : '<span class="badge bad">no — tracking below</span>';
    $("vSheet").innerHTML = s.sheetOuter === "upper"
      ? '<span class="badge up">upper</span>'
      : '<span class="badge lo">lower</span>';
    $("vSigma").textContent = s.sigma > 0 ? "+1" : "−1";
    $("vOrder").textContent = `${s.order} · ${s.orderSize.toLocaleString("en-US")}`;
    $("vMN").textContent = `${s.m.toLocaleString("en-US")} · ${s.n.toLocaleString("en-US")}`;

    const rows = [
      ["oLB", "oUB", "oGB", "oBindB", s.L_B, s.U_B, s.gapB, "B"],
      ["oLI", "oUI", "oGI", "oBindI", s.L_i, s.U_i, s.gapI, "i"],
      ["oLF", "oUF", "oGF", "oBindF", s.L_f, s.U_f, s.gapF, "f"],
    ];
    for (const [l, u, g, b, lv, uv, gv, name] of rows) {
      $(l).textContent = lv.toFixed(10);
      $(u).textContent = uv.toFixed(10);
      $(g).textContent = gv.toExponential(3);
      $(b).innerHTML = `<span class="badge bind">${(s.bindsL === name
        ? "L" : "–")}/${(s.bindsU === name ? "U" : "–")}</span>`;
    }
    $("oLO").textContent = s.L_outer.toFixed(10);
    $("oUO").textContent = s.U_outer.toFixed(10);
    $("oGO").textContent = (s.U_outer - s.L_outer).toExponential(3);
    const exact = (a) => a[0].length > 24
      ? a[0].slice(0, 18) + "…/" + a[1] : a.join("/");
    $("noteShi").textContent = exact(s.S_hi_exact);
    $("noteSlo").textContent = exact(s.S_lo_exact);
    $("notePiEst").textContent = s.piEst.toPrecision(17);

    $("iLF").textContent = s.L_F.toFixed(10);
    $("iFex").textContent = s.Fexact.toFixed(4);
    $("iF").textContent = s.F.toFixed(4);
    $("iWraps").textContent = s.wraps;
    $("iGap").textContent = s.gapFF.toExponential(3) + `  (law: 3π/${s.I.toLocaleString("en-US")})`;
    $("iSigma").textContent = s.sigma > 0 ? "+1" : "−1";
    $("iSigmaSheet").textContent = s.sigma > 0 ? "even sheet (+1)" : "odd sheet (−1)";
    $("iFrac").textContent = `${s.fraction[0]}/${s.fraction[1]}`;

    $("fL").textContent = s.L_final.toPrecision(17);
    $("fU").textContent = s.U_final.toPrecision(17);
    $("fW").textContent = (s.U_final - s.L_final).toExponential(3);
    $("fToPi").textContent = (PI - s.U_final).toExponential(3);
    $("fNote").textContent =
      `L_final = max(L_outer, L_F) — bound by ${s.bindsL === "F"
        ? "the Farey lower sheet" : "scheme " + s.bindsL}; ` +
      `U_final = min(U_outer, π) — ${s.U_final >= PI - 1e-15
        ? "the membrane π itself" : "clipped by the outer upper sheet"}.` +
      ` π − U_final = ${(PI - s.U_final).toExponential(3)}.`;

    $("bTarget").textContent = s.gapFF.toExponential(3);
    $("bGB").textContent = s.gapB.toExponential(3);
    $("bGI").textContent = s.gapI.toExponential(3);
    $("bGF").textContent = s.gapF.toExponential(3);
    $("bRatio").textContent = s.balance.toFixed(3);
    $("bStatus").innerHTML = s.warn
      ? '<span class="badge bad">WARNING: unbalanced</span>'
      : '<span class="badge ok">balanced</span>';

    $("tA").innerHTML = `${s.B.toLocaleString("en-US")} − ${s.m.toLocaleString("en-US")} = <b>${s.alpha.toLocaleString("en-US")}</b>`;
    $("tB").innerHTML = `${s.m.toLocaleString("en-US")} − ${s.n.toLocaleString("en-US")} = <b>${s.beta.toLocaleString("en-US")}</b>`;
    $("tG").innerHTML = `${s.n.toLocaleString("en-US")} − ${s.B.toLocaleString("en-US")} = <b>${s.gamma.toLocaleString("en-US")}</b>`;
    $("tTel").innerHTML = s.telescope
      ? '<span class="badge ok">= 0 ✓</span>'
      : '<span class="badge bad">≠ 0 ✗</span>';
    $("tLed").textContent = s.ledger.map((x) => x.toLocaleString("en-US")).join("  ·  ");
    $("tGhost").textContent = s.ghost.toLocaleString("en-US");
    $("tSig").textContent = `${s.sigma > 0 ? "+1" : "−1"} · ${s.phaseAngle.toLocaleString("en-US")}°`;
    $("tF").textContent = `${s.F.toPrecision(17)} operational · ${s.Fexact.toPrecision(17)} exact · wraps ${s.wraps}`;

    // V2 rate chips: gap * I = the convergence-rate constant
    const I = s.I;
    const rates = [
      ["B", s.gapB * I, "#94a3b8"], ["i", s.gapI * I, "#38bdf8"],
      ["f", s.gapF * I, "#a78bfa"], ["law 3π", 3 * PI, "#facc15"],
      ["final", (s.U_final - s.L_final) * I, "#f472b6"],
    ];
    $("rateChips").innerHTML = "rate = gap × I: " + rates.map(([n, v, c]) =>
      `<span class="chip" style="border-color:${c}">${n} <b>${v.toFixed(3)}</b></span>`).join("")
      + `<span class="chip">balanced ⇔ the outer rates sit near the law 3π ≈ 9.425 · B runs tighter (2)</span>`;
  }

  // ------------------------------------------------------------ live log
  let logTab = "events";       // default: the stream a human watches
  let logFilter = "all";
  let logFrozen = false;
  let logRenders = 0;

  const FILTERS = {
    ticks: [["all", "all ticks"], ["warn", "balance warnings"],
            ["contains", "contains π"], ["notcontains", "not containing π"],
            ["upper", "outer sheet = upper"], ["lower", "outer sheet = lower"]],
    events: [["all", "all events"], ["flips", "flips (outer + spin)"],
             ["outer", "OUTER_FLIP"], ["spin", "SPIN_FLIP"],
             ["warnings", "warnings"], ["rolls", "ORDER_ROLL"],
             ["folds", "PRECISION_FOLD"]],
    orders: [["all", "all rollovers"]],
  };

  function buildFilter() {
    $("selFilter").innerHTML = FILTERS[logTab].map(([v, label]) =>
      `<option value="${v}">${label}</option>`).join("");
    logFilter = "all";
  }

  function eventPasses(e) {
    if (logFilter === "all") return true;
    if (logFilter === "flips") return e.type === "OUTER_FLIP" || e.type === "SPIN_FLIP";
    if (logFilter === "outer") return e.type === "OUTER_FLIP";
    if (logFilter === "spin") return e.type === "SPIN_FLIP";
    if (logFilter === "warnings") return e.type.startsWith("WARN");
    if (logFilter === "rolls") return e.type === "ORDER_ROLL";
    if (logFilter === "folds") return e.type === "PRECISION_FOLD";
    return true;
  }

  function tickPasses(s) {
    if (logFilter === "all") return true;
    if (logFilter === "warn") return s.warn;
    if (logFilter === "contains") return s.containsPi;
    if (logFilter === "notcontains") return !s.containsPi;
    if (logFilter === "upper") return s.sheetOuter === "upper";
    if (logFilter === "lower") return s.sheetOuter === "lower";
    return true;
  }

  const esc = (x) => String(x).replace(/&/g, "&amp;").replace(/</g, "&lt;");

  function renderLog() {
    if (logFrozen) return;
    logRenders++;
    const head = $("logHead"), body = $("logBody");
    if (logTab === "ticks") {
      head.innerHTML = "<tr><th>B</th><th>final bracket</th><th>width</th>" +
        "<th>sheet</th><th>σ</th><th>balance</th><th>binds L/U</th></tr>";
      const rows = engine.tickLog.filter(tickPasses).slice(-120);
      body.innerHTML = rows.length ? rows.map((s) =>
        `<tr data-b="${s.B}"><td>${s.B.toLocaleString("en-US")}</td>` +
        `<td>[${s.L_final.toFixed(9)}, ${s.U_final.toFixed(9)}]</td>` +
        `<td>${(s.U_final - s.L_final).toExponential(2)}</td>` +
        `<td>${s.sheetOuter}</td><td>${s.sigma > 0 ? "+1" : "−1"}</td>` +
        `<td>${s.balance.toFixed(2)}${s.warn ? " ⚠" : ""}</td>` +
        `<td>${s.bindsL}/${s.bindsU}</td></tr>`).join("")
        : `<tr><td colspan="7" class="empty">no ticks match the filter yet</td></tr>`;
    } else if (logTab === "events") {
      head.innerHTML = "<tr><th>tick B</th><th>event</th><th>detail</th></tr>";
      const rows = engine.history.filter(eventPasses).slice(-150);
      body.innerHTML = rows.length ? rows.map((e) => {
        let detail = "";
        if (e.type === "OUTER_FLIP")
          detail = `${e.from} → ${e.to} · ladder annihilated [${e.annihilated.join(", ")}] · ghost ${e.ghost.toLocaleString("en-US")}`;
        else if (e.type === "SPIN_FLIP") detail = `σ → ${e.to > 0 ? "+1" : "−1"}`;
        else if (e.type === "WARN_BALANCE") detail = `ratio ${e.balance.toFixed(2)} > 10`;
        else if (e.type === "WARN_CLEAR") detail = `ratio ${e.balance.toFixed(2)} back in range`;
        else if (e.type === "ORDER_ROLL") detail = `order ${e.order} · |Fₙ| ${e.orderSize.toLocaleString("en-US")} · φ(n) ${e.phi}`;
        else if (e.type === "PRECISION_FOLD") detail = `F wrapped by n = ${e.n} · wraps ${e.wraps} · F ← ${e.F_after.toExponential(3)}`;
        return `<tr data-b="${e.tick}"><td>${e.tick.toLocaleString("en-US")}</td>` +
          `<td class="ev-${e.type}">${e.type}</td><td>${esc(detail)}</td></tr>`;
      }).join("") : `<tr><td colspan="3" class="empty">no events match the filter yet</td></tr>`;
    } else {
      head.innerHTML = "<tr><th>tick B</th><th>order n</th><th>|Fₙ|</th><th>φ(n)</th></tr>";
      const rows = engine.history.filter((e) => e.type === "ORDER_ROLL");
      const tail = rows.slice(-150);
      body.innerHTML = tail.length ? tail.map((e) =>
        `<tr data-b="${e.tick}"><td>${e.tick.toLocaleString("en-US")}</td>` +
        `<td>${e.order}</td><td>${e.orderSize.toLocaleString("en-US")}</td>` +
        `<td>${e.phi}</td></tr>`).join("")
        : `<tr><td colspan="4" class="empty">no rollovers yet</td></tr>`;
    }
    const wrap = $("logWrap");
    wrap.scrollTop = wrap.scrollHeight;
    $("logStats").textContent =
      `${engine.tickLog.length.toLocaleString("en-US")} ticks held` +
      (engine.logDropped ? ` (${engine.logDropped.toLocaleString("en-US")} dropped)` : "") +
      ` · ${engine.history.length.toLocaleString("en-US")} events held` +
      ` · ${engine.flipsOuter} outer flips · ${engine.flipsSpin} spin flips` +
      ` · ${engine.rolls} rollovers · ${engine.wraps} folds`;
  }

  // ------------------------------------------------------------ loop
  function frame(t) {
    const dt = Math.min(0.25, (t - lastT) / 1000);
    lastT = t;
    let n = 0;
    if (running) { acc += dt * tps; n = Math.floor(acc); acc -= n; }
    if (burstRemaining > 0) {
      const take = Math.min(burstRemaining, 2000);
      n += take; burstRemaining -= take;
    }
    n = Math.min(n, 20000);
    for (let k = 0; k < n; k++) engine.tick();
    ticksThisSecond += n;
    if (t - lastPerfT >= 1000) {
      $("perfNote").textContent =
        `${ticksThisSecond.toLocaleString("en-US")} ticks/s · log ${engine.tickLog.length.toLocaleString("en-US")}`;
      ticksThisSecond = 0; lastPerfT = t;
    }
    if (engine.B > 0n) render(engine.tickLog[engine.tickLog.length - 1]);
    drawCharts(t);
    if (t - lastLogDraw >= 150) { lastLogDraw = t; renderLog(); }
    if (cursorB() !== null && cursorDirty) renderReadout();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame((t) => { lastT = t; requestAnimationFrame(frame); });

  // ------------------------------------------------------------ controls
  $("btnPlay").addEventListener("click", () => {
    running = !running;
    $("btnPlay").textContent = running ? "⏸ pause" : "▶ play";
  });
  $("btnSpeed").addEventListener("click", () => {
    tps = SPEEDS[(SPEEDS.indexOf(tps) + 1) % SPEEDS.length];
    $("btnSpeed").textContent = "×" + tps;
  });
  $("btnStep").addEventListener("click", () => { for (let k = 0; k < 100; k++) engine.tick(); });
  $("btnBurst").addEventListener("click", () => { burstRemaining += 5000; });
  $("btnReset").addEventListener("click", () => {
    engine = new NestedBifClock({ sieve, logCap: engine.logCap });
    cursor.anchorB = null; cursor.hoverB = null; cursorDirty = true;
    running = true;
    $("btnPlay").textContent = "⏸ pause";
  });
  $("selLogCap").addEventListener("change", () => {
    engine.logCap = parseInt($("selLogCap").value, 10);
  });

  // ------------------------------------------------------------ cursor wiring
  function wireCursor(id, linear) {
    const cv = $(id);
    cv.addEventListener("mousemove", (ev) => {
      const r = cv.getBoundingClientRect();
      const x = (ev.clientX - r.left) * (cv.width / r.width);
      const pts = engine.tickLog;
      if (pts.length < 2) return;
      let B;
      if (linear) {
        const win = pts.slice(-900);
        const b0 = win[0].B, b1 = win[win.length - 1].B;
        B = Math.round(b0 + (x - 12) / (cv.width - 24) * (b1 - b0));
      } else {
        const X = logXFor(pts);
        B = X.inv(x, cv.width);
      }
      const b0 = pts[Math.max(0, pts.length - 900)].B;
      const b1 = pts[pts.length - 1].B;
      if (B >= Math.max(1, b0 - 2) && B <= b1) {
        cursor.hoverB = Math.max(1, B);
        cursorDirty = true;
        renderReadout();
      }
    });
    cv.addEventListener("mouseleave", () => {
      cursor.hoverB = null; cursorDirty = true; renderReadout();
    });
    cv.addEventListener("click", (ev) => {
      if (cursor.hoverB !== null) {
        cursor.anchorB = cursor.hoverB;
        cursorDirty = true;
        renderReadout();
      }
    });
  }
  wireCursor("chartBracket", false);
  wireCursor("chartGaps", false);
  wireCursor("chartPhase", true);
  wireCursor("chartTri", false);

  // ------------------------------------------------------------ log wiring
  for (const tab of document.querySelectorAll("#logTabs .tab")) {
    tab.addEventListener("click", () => {
      logTab = tab.dataset.tab;
      document.querySelectorAll("#logTabs .tab").forEach((x) =>
        x.classList.toggle("on", x === tab));
      buildFilter();
      renderLog();
    });
  }
  $("selFilter").addEventListener("change", () => {
    logFilter = $("selFilter").value;
    renderLog();
  });
  const wrap = $("logWrap");
  wrap.addEventListener("mouseenter", () => {
    logFrozen = true;
    $("frozenBadge").style.display = "inline-block";
  });
  wrap.addEventListener("mouseleave", () => {
    logFrozen = false;
    $("frozenBadge").style.display = "none";
    renderLog();
  });
  $("logBody").addEventListener("click", (ev) => {
    const tr = ev.target.closest("tr[data-b]");
    if (!tr) return;
    cursor.anchorB = parseInt(tr.dataset.b, 10);
    cursorDirty = true;
    renderReadout();
  });
  buildFilter();

  // ------------------------------------------------------------ exports
  function download(name, text, mime) {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    window.__bif.lastExport = { name, bytes: text.length };
    return text.length;
  }

  const CSV_COLS = ["B", "I", "m", "n", "order", "orderSize", "piEst",
    "F", "Fexact", "wraps", "rolls", "L_B", "U_B", "L_i", "U_i",
    "L_f", "U_f", "L_F", "U_F", "L_outer", "U_outer", "L_final",
    "U_final", "gapB", "gapI", "gapF", "gapFF", "balance", "warn",
    "sheetOuter", "sigma", "phaseAngle", "alpha", "beta", "gamma",
    "telescope", "ledger", "ghost", "containsPi", "bindsL", "bindsU",
    "flipsOuter", "flipsSpin", "precisionFold"];

  function exportTicks() {
    const rows = [CSV_COLS.concat(["fraction_a", "fraction_b",
      "S_hi_num", "S_hi_den", "S_lo_num", "S_lo_den"]).join(",")];
    for (const s of engine.tickLog) {
      const cells = CSV_COLS.map((c) => {
        const v = s[c];
        return typeof v === "boolean" ? (v ? 1 : 0)
          : Array.isArray(v) ? v.join(";")
          : String(v);
      });
      cells.push(s.fraction[0], s.fraction[1],
        s.S_hi_exact[0], s.S_hi_exact[1],
        s.S_lo_exact[0], s.S_lo_exact[1]);
      rows.push(cells.join(","));
    }
    return download(`piclock_nested_bif_ticks_${engine.B}.csv`,
      rows.join("\n"), "text/csv");
  }

  function exportEvents() {
    const text = engine.history.map((e) => JSON.stringify(e)).join("\n");
    return download(`piclock_nested_bif_events_${engine.B}.jsonl`, text,
      "application/x-ndjson");
  }

  function exportSession() {
    const log = engine.tickLog;
    const step = Math.max(1, Math.ceil(log.length / 4000));
    const series = [];
    for (let k = 0; k < log.length; k += step) {
      const s = log[k];
      series.push({ B: s.B, L_final: s.L_final, U_final: s.U_final,
        gapB: s.gapB, gapI: s.gapI, gapF: s.gapF, gapFF: s.gapFF,
        sigma: s.sigma, sheet: s.sheetOuter, balance: s.balance,
        alpha: s.alpha, beta: s.beta, gamma: s.gamma, ghost: s.ghost });
    }
    const session = {
      engine: "NestedBifClock (piclock-browser core/nestedbif.js)",
      spec: "The Nested-Bif pi-clock (user spec, precision-fold build)",
      resolutions: ["R1 I transfinite (no reset)",
        "R2 Leibniz U_i=S_{2m+1}, L_i=S_{2m+2}",
        "R3 apeirogon n>=3", "R4 B scheme literal",
        "R5 balance over 3 outer gaps",
        "R6 fold = the 2^52 numerical precision boundary"],
      config: { threshold: engine.threshold, logCap: engine.logCap,
        maxHistory: engine.maxHistory },
      counters: { ticks: Number(engine.B), flipsOuter: engine.flipsOuter,
        flipsSpin: engine.flipsSpin, rolls: engine.rolls,
        wraps: engine.wraps,
        balanceWarnings: engine.balanceWarns,
        logDropped: engine.logDropped,
        eventsDropped: engine.logDroppedEvents },
      final: log[log.length - 1] || null,
      historyTail: engine.history.slice(-500),
      series,
    };
    return download(`piclock_nested_bif_session_${engine.B}.json`,
      JSON.stringify(session, null, 1), "application/json");
  }

  $("btnExportTicks").addEventListener("click", exportTicks);
  $("btnExportEvents").addEventListener("click", exportEvents);
  $("btnExportSession").addEventListener("click", exportSession);

  // ------------------------------------------------------------ franel
  $("btnFranel").addEventListener("click", () => {
    const n = Math.min(engine.order, PiLock.FRANEL_MAX_N);
    $("franelBody").innerHTML =
      `<tr><td class="k">auditing</td><td>F<sub>${n}</sub> — exact
        BigInt, one rational per Farey term…</td></tr>`;
    setTimeout(() => {
      const r = franelLandau(n, sieve);
      $("franelBody").innerHTML = `
        <tr><td class="k">order · |Fₙ| = mₙ+1</td><td>${r.n} ·
          ${(r.m_n + 1).toLocaleString("en-US")}${n === PiLock.FRANEL_MAX_N
            && engine.order > PiLock.FRANEL_MAX_N ? " (capped)" : ""}</td></tr>
        <tr><td class="k">Σ d² (Franel)</td><td>
          ${r.franel.toNumber().toExponential(8)} =
          ${r.franel.toString()}</td></tr>
        <tr><td class="k">Σ |d| (Landau)</td><td>
          ${r.landau.toNumber().toExponential(8)} =
          ${r.landau.toString()}</td></tr>
        <tr><td class="k">Σ d² / mₙ</td><td>
          ${(r.franel.toNumber() / r.m_n).toExponential(4)} — the
          RH-relevant rate</td></tr>`;
    }, 30);
  });

  // ------------------------------------------------------------ debug
  window.__bif = {
    get engine() { return engine; },
    isRunning: () => running, getTps: () => tps,
    cursor: () => ({ ...cursor }),
    setAnchor(B) { cursor.anchorB = B; cursorDirty = true; renderReadout(); },
    clearAnchor() { cursor.anchorB = null; cursorDirty = true; renderReadout(); },
    switchTab(t) { logTab = t;
      document.querySelectorAll("#logTabs .tab").forEach((x) =>
        x.classList.toggle("on", x.dataset.tab === t));
      buildFilter(); renderLog(); },
    setFilter(v) { logFilter = v; $("selFilter").value = v; renderLog(); },
    getTab: () => logTab,
    isFrozen: () => logFrozen,
    stats: () => ({ logRenders, chartDraws }),
    exports: { ticks: exportTicks, events: exportEvents, session: exportSession },
    lastExport: null,
  };

  // boot: render once, then autoplay
  $("btnPlay").click();
})();
