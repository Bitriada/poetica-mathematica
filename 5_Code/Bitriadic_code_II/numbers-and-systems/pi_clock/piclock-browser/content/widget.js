/* content/widget.js -- the floating pi-clock widget.
 *
 * Injected into every page (WebExtensions content script; the core
 * modules rational.js + piclock.js are injected before this file, so
 * PiLock is available in this isolated world).  The widget holds NO
 * clock state of its own: it renders snapshots broadcast by the
 * background service worker over a runtime port, and sends control
 * messages back.  A shadow DOM keeps the page's CSS out.
 *
 *   collapsed: a small draggable pill  [ pi^ 3.14159 | I 1,234 | > ]
 *   expanded:  the full instrument --
 *     . the big pi-hat readout with digit-lock highlighting
 *       (digits that have converged to pi's light up in gold),
 *     . the exact error law  error = -3 pi / I,
 *     . a two-lane live chart (pi-hat vs pi; the scaled error
 *       -error*I/(3pi), which sits flat at 1 -- the law, visible),
 *     . the registers: the 64-bit sphere mask, the fold-wrapped F,
 *       the precision meter (F against the 2^52 fold boundary),
 *     . the trinumeral panel: sheets, alpha/beta/gamma, telescope,
 *       ledger, ghost, sigma (the double cover),
 *     . the Franel-Landau audit (exact BigInt) and the pi^2 identity,
 *     . controls: play/pause, speed, step, reset.
 */

(function () {
  "use strict";
  if (window.__piclockWidget) return;          // one widget per page
  window.__piclockWidget = true;
  if (!/^text\/html/i.test(document.contentType || "text/html")) return;

  const PI = Math.PI;
  const PI_STR = "3.14159265358979323846";
  const PRECISION_BOUND = PiLock.PRECISION_BOUND;

  // ------------------------------------------------------------ shell
  const host = document.createElement("div");
  host.id = "piclock-widget-host";
  const shadow = host.attachShadow({ mode: "closed" });
  if (!document.body) { document.addEventListener("DOMContentLoaded",
    mount); } else { mount(); }

  function mount() { document.documentElement.appendChild(host); }

  const CSS = `
    :host(*), * { box-sizing: border-box; margin: 0; padding: 0; }
    .panel {
      position: fixed; z-index: 2147483647;
      font: 12px/1.45 "Segoe UI", system-ui, sans-serif;
      color: #e2e8f0; user-select: none;
      width: 344px; right: 18px; top: 18px;
    }
    .card { background: #0b1220; border: 1px solid #293548;
            border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,.5);
            overflow: hidden; }
    .hdr { display: flex; align-items: center; gap: 8px;
           padding: 8px 12px; background: #101a2e; cursor: move;
           border-bottom: 1px solid #293548; }
    .hdr .logo { color: #facc15; font-weight: 700; font-size: 15px; }
    .hdr .sub { color: #64748b; font-size: 10.5px; }
    .hdr .sp { flex: 1; }
    .pill-btn { background: #1e293b; color: #cbd5e1; border: 1px solid
                #334155; border-radius: 6px; padding: 2px 8px;
                font-size: 11px; cursor: pointer; }
    .pill-btn:hover { background: #273449; color: #fff; }
    .body { padding: 10px 12px 12px; }
    .big { font: 700 30px/1.1 ui-monospace, "Cascadia Mono", monospace;
           letter-spacing: .5px; }
    .big .lock { color: #facc15; }
    .big .free { color: #64748b; }
    .law { color: #7dd3fc; font: 11.5px ui-monospace, monospace;
           margin-top: 3px; }
    .muted { color: #64748b; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
    .cell { flex: 1; min-width: 88px; background: #101a2e;
            border: 1px solid #22304a; border-radius: 8px; padding: 6px 8px; }
    .cell .k { color: #64748b; font-size: 10px; text-transform:
               uppercase; letter-spacing: .08em; }
    .cell .v { font: 600 13px ui-monospace, monospace; margin-top: 2px;
               word-break: break-all; }
    canvas { display: block; width: 100%; margin-top: 10px;
             background: #0d1526; border: 1px solid #22304a;
             border-radius: 8px; }
    .meter { position: relative; height: 10px; margin-top: 10px;
             background: #101a2e; border: 1px solid #22304a;
             border-radius: 5px; overflow: hidden; }
    .meter .fill { position: absolute; inset: 0 auto 0 0; width: 0%;
                   background: linear-gradient(90deg,#1d4ed8,#38bdf8); }
    .meter .cap { position: absolute; top: 0; bottom: 0;
                       width: 2px; background: #f472b6; left: 50%; }
    .meter .lbl { position: absolute; right: 4px; top: -2px;
                  font-size: 9px; color: #64748b; line-height: 12px; }
    .mask { display: grid; grid-template-columns: repeat(16, 1fr);
            gap: 2px; margin-top: 8px; }
    .mask i { height: 7px; border-radius: 2px; background: #1e293b; }
    .mask i.on { background: #facc15; box-shadow: 0 0 4px #facc1588; }
    details { margin-top: 8px; border: 1px solid #22304a;
              border-radius: 8px; background: #0d1526; }
    details summary { cursor: pointer; padding: 6px 10px; color: #93c5fd;
                      font-size: 11.5px; list-style: none; }
    details summary::before { content: "\\25B8 "; color: #64748b; }
    details[open] summary::before { content: "\\25BE "; }
    details .inner { padding: 2px 10px 10px; }
    .mono { font: 11px ui-monospace, monospace; word-break: break-all;
            color: #cbd5e1; }
    .kv { display: flex; gap: 8px; justify-content: space-between;
          padding: 2px 0; }
    .kv b { color: #7dd3fc; font-weight: 600; }
    .ok { color: #4ade80; } .bad { color: #f87171; }
    .ctrl { display: flex; gap: 6px; margin-top: 10px; }
    .ctrl button { flex: 1; padding: 6px 0; border-radius: 7px;
                   border: 1px solid #334155; background: #1e293b;
                   color: #e2e8f0; cursor: pointer; font-size: 12px; }
    .ctrl button:hover { background: #273449; }
    .ctrl button.primary { background: #b45309; border-color: #d97706;
                           color: #fff7ed; font-weight: 600; }
    .tiny { font-size: 10px; color: #64748b; margin-top: 6px; }
    .collapsed { display: flex; align-items: center; gap: 8px;
                 padding: 6px 10px; background: #0b1220;
                 border: 1px solid #293548; border-radius: 999px;
                 box-shadow: 0 6px 20px rgba(0,0,0,.45); cursor: move;
                 font: 12px ui-monospace, monospace; }
    .collapsed .pi { color: #facc15; font-weight: 700; }
    .collapsed .tick { color: #94a3b8; }
    .collapsed .state { width: 9px; height: 9px; border-radius: 50%;
                        background: #4ade80; }
    .collapsed .state.paused { background: #f87171; }
    .hidden { display: none !important; }
  `;

  shadow.innerHTML = `
    <style>${CSS}</style>
    <div class="panel" part="panel">
      <div class="collapsed" id="pill">
        <span class="state" id="pillState"></span>
        <span class="pi" id="pillPi">\u03c0\u0302 3.14</span>
        <span class="tick" id="pillI">I 0</span>
        <span class="pill-btn" id="pillOpen" title="open">\u25B8</span>
      </div>
      <div class="card hidden" id="card">
        <div class="hdr" id="drag">
          <span class="logo">\u03c0-clock</span>
          <span class="sub">Trinumeral Clock \u00b7 exact BigInt</span>
          <span class="sp"></span>
          <span class="pill-btn" id="btnCollapse" title="collapse">\u2013</span>
        </div>
        <div class="body">
          <div class="big" id="bigPi"></div>
          <div class="law" id="lawLine"></div>
          <canvas id="chart" width="640" height="300"></canvas>
          <div class="row">
            <div class="cell"><div class="k">I \u00b7 ticks (exact)</div>
              <div class="v" id="vI">0</div></div>
            <div class="cell"><div class="k">order n \u00b7 |F\u2099|</div>
              <div class="v" id="vN">1</div></div>
            <div class="cell"><div class="k">F register (fold-wrapped)</div>
              <div class="v" id="vF">0.000</div></div>
            <div class="cell"><div class="k">spheres \u00b7 wraps</div>
              <div class="v" id="vSph">1 \u00b7 0</div></div>
          </div>
          <div class="mask" id="mask"></div>
          <div class="meter" id="meterBar" title="F vs the 2^52 precision boundary — the fold trigger">
            <div class="fill" id="meterFill"></div>
            <div class="cap"></div>
            <div class="lbl" id="meterLbl"></div>
          </div>
          <details id="dTri">
            <summary>Trinumeral \u2014 sheets, \u03b1 \u03b2 \u03b3, ledger, \u03c3</summary>
            <div class="inner mono" id="triBody">\u2026</div>
          </details>
          <details id="dFranel">
            <summary>Franel\u2013Landau audit (exact) \u2014 the RH view</summary>
            <div class="inner">
              <div class="mono" id="franelBody">
                d<sub>k,n</sub> = a<sub>k,n</sub> \u2212 k/m<sub>n</sub> for the
                terms of F<sub>n</sub>. Franel (1924): RH \u21d4
                \u03a3 d\u00b2 = O(n<sup>r</sup>) \u2200 r &gt; \u22121;
                Landau (1924): RH \u21d4 \u03a3|d| = O(n<sup>r</sup>)
                \u2200 r &gt; \u00bd.
              </div>
              <div class="ctrl" style="margin-top:8px">
                <button id="btnFranel">audit order n</button>
                <button id="btnPi2">\u03c0\u00b2 identity</button>
              </div>
            </div>
          </details>
          <div class="ctrl">
            <button class="primary" id="btnPlay">\u23F8 pause</button>
            <button id="btnSpeed">\u00D71</button>
            <button id="btnStep">+1</button>
            <button id="btnReset">reset</button>
          </div>
          <div class="tiny">2F/I = \u03c0(1 \u2212 3/I) exactly; error
            = \u22123\u03c0/I \u2192 0. Time is the conversion count:
            one Farey fraction per tick. F folds at the numerical
            precision boundary (2\u00b2\u2075\u00b2), not a lattice
            constant \u2014 B and I never reset.</div>
        </div>
      </div>
    </div>`;

  const $ = (id) => shadow.getElementById(id);
  const panel = shadow.querySelector(".panel");
  // debug/test hook: the shadow root is closed, so expose it for the
  // headless smoke tests (and the curious)
  window.__piclock_debug = { host, shadow, panel };

  // ------------------------------------------------------------ mask
  const maskEl = $("mask");
  for (let k = 0; k < 64; k++) maskEl.appendChild(document.createElement("i"));
  const maskCells = Array.from(maskEl.children);

  // ------------------------------------------------------------ drag
  function makeDraggable(handle) {
    let sx = 0, sy = 0, px = 0, py = 0, dragging = false;
    handle.addEventListener("pointerdown", (e) => {
      if (e.target.classList.contains("pill-btn")) return;
      dragging = true; sx = e.clientX; sy = e.clientY;
      const r = panel.getBoundingClientRect();
      px = r.left; py = r.top;
      panel.style.left = px + "px"; panel.style.top = py + "px";
      panel.style.right = "auto";
      try { handle.setPointerCapture(e.pointerId); } catch (err) {
        /* synthetic/test pointers have no active capture */
      }
    });
    handle.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const x = Math.max(4, Math.min(innerWidth - 80, px + e.clientX - sx));
      const y = Math.max(4, Math.min(innerHeight - 40, py + e.clientY - sy));
      panel.style.left = x + "px"; panel.style.top = y + "px";
    });
    handle.addEventListener("pointerup", () => {
      dragging = false;
      const r = panel.getBoundingClientRect();
      chrome.storage.local.set({ "piclock.pos":
        { x: r.left, y: r.top, expanded: !card.classList.contains("hidden") } });
    });
  }
  makeDraggable($("drag"));
  makeDraggable($("pill"));

  // ------------------------------------------------------------ port
  let port = null;
  function connect() {
    port = chrome.runtime.connect({ name: "piclock" });
    port.onMessage.addListener(onMessage);
    port.onDisconnect.addListener(() => setTimeout(connect, 800));
    port.postMessage({ cmd: "hello" });
  }

  // ------------------------------------------------------------ data
  const hist = [];                  // {I, ratio, scaled}
  const HIST_MAX = 900;

  function fmtInt(n) {
    return Number(n).toLocaleString("en-US");
  }

  function renderPiHat(ratio) {
    const s = ratio.toFixed(11);
    let lock = 0;
    while (lock < s.length && s[lock] === PI_STR[lock]) lock++;
    // the law: I >= 30 locks "3.1"; every 10x ticks adds a digit
    const el = $("bigPi");
    el.innerHTML =
      `<span class="lock">${s.slice(0, lock)}</span>` +
      `<span class="free">${s.slice(lock)}</span>`;
  }

  function onMessage(msg) {
    if (msg.type !== "snapshot") return;
    const s = msg.snap;
    renderPiHat(s.ratio);
    const law = -3 * PI / s.Inum;
    $("lawLine").textContent =
      `error ${s.error >= 0 ? "+" : ""}${s.error.toExponential(3)}` +
      `   \u2261  \u22123\u03c0/I = ${law.toExponential(3)}` +
      `   (${s.telescope ? "telescope \u2713" : "TELESCOPE \u2717"})`;
    $("vI").textContent = fmtInt(s.I);
    $("vN").textContent = `${s.n} \u00b7 ${fmtInt(s.orderSize)}`;
    $("vF").textContent = s.F.toFixed(4) +
      ` (${s.Fexact.toFixed(1)} unwrapped)`;
    $("vSph").textContent = `${s.spheres} \u00b7 ${s.wraps}`;
    $("pillPi").textContent = "\u03c0\u0302 " + s.ratio.toFixed(6);
    $("pillI").textContent = "I " + fmtInt(s.I);
    // the B mask (64 cells)
    let B = BigInt(s.B);
    for (let k = 0; k < 64; k++) {
      maskCells[k].classList.toggle("on", (B & 1n) === 1n);
      B >>= 1n;
    }
    // the precision meter: F against the 2^52 fold boundary
    $("meterFill").style.width =
      (100 * Math.min(1, s.F / PRECISION_BOUND)).toPrecision(3) + "%";
    $("meterLbl").textContent =
      `F ${s.F.toExponential(2)} / 2\u00b2\u2075\u00b2 \u00b7 wraps ${s.wraps}` +
      (s.fold ? " \u00b7 PRECISION_FOLD" : "");
    // play state
    $("btnPlay").textContent = msg.running ? "\u23F8 pause" : "\u25B6 play";
    $("pillState").classList.toggle("paused", !msg.running);
    $("btnSpeed").textContent = "\u00D7" + msg.tps;
    // history + chart
    hist.push({ I: s.Inum, ratio: s.ratio,
                scaled: s.Inum > 3 ? -s.error * s.Inum / (3 * PI) : NaN });
    if (hist.length > HIST_MAX) hist.shift();
    drawChart();
    renderTri(s);
    lastSnap = s;
  }

  let lastSnap = null;

  function renderTri(s) {
    const short = (r) => {
      const t = String(r);
      return t.length > 44 ? t.slice(0, 30) + "\u2026" + t.slice(-11) : t;
    };
    const B = s.sheetB;
    $("triBody").innerHTML = `
      <div class="kv"><span>B sheet</span><b>${B.slice(0, 18)}\u2026${B.slice(-10)}</b></div>
      <div class="kv"><span>i sheet</span><b>${s.sheetI}</b></div>
      <div class="kv"><span>f sheet</span><b>${s.sheetF.toPrecision(17)}</b></div>
      <div class="kv"><span>\u03b1 (B\u2192i)</span><b>${short(s.alpha)}</b></div>
      <div class="kv"><span>\u03b2 (i\u2192f)</span><b>${short(s.beta)}</b></div>
      <div class="kv"><span>\u03b3 (f\u2192B)</span><b>${short(s.gamma)}</b></div>
      <div class="kv"><span>telescope \u03b1+\u03b2+\u03b3</span>
        <b class="${s.telescope ? "ok" : "bad"}">
          ${s.telescope ? "= 0 \u2713" : "\u2260 0 \u2717"}</b></div>
      <div class="kv"><span>ledger e1|e2|e3</span>
        <b>${s.ledger.map(short).join(" | ")}</b></div>
      <div class="kv"><span>ghost disc</span><b>${short(s.ghost)}</b></div>
      <div class="kv"><span>\u03c3 (phase ${s.angle}\u00b0)</span>
        <b>${s.sigma > 0 ? "+1" : "\u22121"}</b></div>
      <div class="kv"><span>Farey fraction</span>
        <b>${s.fraction ? s.fraction[0] + "/" + s.fraction[1] : "\u2013"}</b></div>`;
  }

  // ------------------------------------------------------------ chart
  function drawChart() {
    const cv = $("chart");
    const ctx = cv.getContext("2d");
    const W = cv.width, H = cv.height;
    ctx.clearRect(0, 0, W, H);
    if (hist.length < 2) return;
    const pts = hist.filter((p) => p.I >= 4);
    if (pts.length < 2) return;
    const x0 = Math.log10(pts[0].I), x1 = Math.log10(pts[pts.length - 1].I);
    const xr = Math.max(1e-6, x1 - x0);
    const X = (I) => 8 + (W - 16) * (Math.log10(I) - x0) / xr;

    // lane 1: pi-hat vs pi  (top 55%)
    let lo = Infinity, hi = -Infinity;
    for (const p of pts) { lo = Math.min(lo, p.ratio); hi = Math.max(hi, p.ratio); }
    const pad = Math.max((hi - lo) * 0.15, 1e-3);
    lo -= pad; hi += pad;
    const H1 = H * 0.55 - 8;
    const Y1 = (v) => 6 + H1 * (1 - (v - lo) / (hi - lo));
    ctx.strokeStyle = "#334155"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, Y1(PI)); ctx.lineTo(W, Y1(PI));
    ctx.stroke();
    ctx.strokeStyle = "#38bdf8"; ctx.lineWidth = 2.4;
    ctx.beginPath();
    pts.forEach((p, k) => { const x = X(p.I), y = Y1(p.ratio);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "#facc15"; ctx.font = "16px monospace";
    ctx.fillText("\u03c0", 6, Y1(PI) - 5);
    ctx.fillStyle = "#64748b"; ctx.font = "13px monospace";
    ctx.fillText("2F/I", 6, 16);

    // lane 2: the scaled error  -error*I/(3pi)  (should sit at 1)
    const H2 = H * 0.32, y0 = H * 0.60, y1 = H - 6;
    const Y2 = (v) => y1 - (y1 - y0) * Math.min(1, Math.max(0, v / 2));
    ctx.strokeStyle = "#334155"; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(0, Y2(1)); ctx.lineTo(W, Y2(1)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = "#f472b6"; ctx.lineWidth = 2;
    ctx.beginPath();
    pts.forEach((p, k) => {
      if (!isFinite(p.scaled)) { ctx.moveTo(X(p.I), y1); return; }
      const x = X(p.I), y = Y2(p.scaled);
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = "#f472b6"; ctx.font = "13px monospace";
    ctx.fillText("\u2212error\u00B7I/(3\u03c0) = 1 (the law)", 6, y0 - 2);
  }

  // ------------------------------------------------------------ panels
  $("btnFranel").addEventListener("click", () => {
    const n = lastSnap ? Math.min(lastSnap.n, PiLock.FRANEL_MAX_N)
      : 10;
    const capped = lastSnap && lastSnap.n > PiLock.FRANEL_MAX_N;
    $("franelBody").textContent = `auditing F_${n} \u2026`;
    setTimeout(() => {
      try {
        const r = PiLock.franelLandau(n, new PiLock.TotientSieve(n + 8));
        const f = r.franel, l = r.landau;
        $("franelBody").innerHTML = `
          <div class="kv"><span>order n</span><b>${r.n}${capped
            ? " (capped)" : ""}</b></div>
          <div class="kv"><span>terms m\u2099 + 1 = |F\u2099|</span>
            <b>${fmtInt(r.m_n + 1)}</b></div>
          <div class="kv"><span>\u03a3 d\u00b2 (Franel)</span>
            <b>${f.toDecimal(6)} \u00b7 ${(f.toNumber()).toExponential(3)}</b></div>
          <div class="kv"><span>\u03a3 d\u00b2 / m</span>
            <b>${(f.toNumber() / r.m_n).toExponential(3)} \u2192 0 iff RH-side rate</b></div>
          <div class="kv"><span>\u03a3 |d| (Landau)</span>
            <b>${l.toDecimal(6)} \u00b7 ${(l.toNumber()).toExponential(3)}</b></div>
          <div class="kv"><span>exact \u03a3 d\u00b2</span>
            <b>${f.toString().length > 52
              ? f.toString().slice(0, 40) + "\u2026" : f.toString()}</b></div>`;
      } catch (e) {
        $("franelBody").textContent = "audit failed: " + e.message;
      }
    }, 20);
  });

  $("btnPi2").addEventListener("click", () => {
    $("franelBody").textContent = "counting square-free integers \u2026";
    setTimeout(() => {
      const N = 1000000;
      const sf = PiLock.squareFreeCount(N);
      const est = 6 * N / sf;
      $("franelBody").innerHTML = `
        <div class="mono">the second cross-numeral identity (sec. 8.9):
          \u03c0\u00b2 = 6N / SF(N) via the square-free density 6/\u03c0\u00b2</div>
        <div class="kv"><span>N</span><b>${fmtInt(N)}</b></div>
        <div class="kv"><span>SF(N) (exact, M\u00f6bius)</span>
          <b>${fmtInt(sf)}</b></div>
        <div class="kv"><span>6N / SF(N)</span>
          <b>${est.toFixed(8)}</b></div>
        <div class="kv"><span>\u03c0\u00b2</span>
          <b>${(PI * PI).toFixed(8)}</b></div>
        <div class="kv"><span>relative error</span>
          <b>${(est / (PI * PI) - 1).toExponential(2)}</b></div>`;
    }, 20);
  });

  // ------------------------------------------------------------ ctrl
  function send(action, extra = {}) {
    if (port) port.postMessage({ cmd: "control", action, ...extra });
  }
  $("btnPlay").addEventListener("click", () => {
    send($("btnPlay").textContent.includes("pause") ? "pause" : "play");
  });
  $("pillState").addEventListener("click", () =>
    send(lastSnap && $("btnPlay").textContent.includes("play")
      ? "play" : "pause"));
  $("btnSpeed").addEventListener("click", () => {
    const speeds = [1, 4, 16, 64, 256];
    const cur = lastSnap ? speeds.indexOf(
      parseInt($("btnSpeed").textContent.slice(1), 10)) : 0;
    send("speed", { tps: speeds[(cur + 1) % speeds.length] });
  });
  $("btnStep").addEventListener("click", () => send("step", { n: 1 }));
  $("btnReset").addEventListener("click", () => send("reset"));
  $("btnCollapse").addEventListener("click", () => {
    card.classList.add("hidden"); pill.classList.remove("hidden");
    savePos(false);
  });
  $("pillOpen").addEventListener("click", () => {
    pill.classList.add("hidden"); card.classList.remove("hidden");
    savePos(true);
  });

  function savePos(expanded) {
    const r = panel.getBoundingClientRect();
    chrome.storage.local.set({ "piclock.pos":
      { x: r.left, y: r.top, expanded } });
  }

  // ------------------------------------------------------------ boot
  const card = $("card"), pill = $("pill");
  chrome.storage.local.get("piclock.pos", (got) => {
    const p = got && got["piclock.pos"];
    if (p && isFinite(p.x)) {
      panel.style.left = Math.max(4, p.x) + "px";
      panel.style.top = Math.max(4, p.y) + "px";
      panel.style.right = "auto";
    }
    if (p && p.expanded) {
      pill.classList.add("hidden"); card.classList.remove("hidden");
    } else {
      card.classList.add("hidden"); pill.classList.remove("hidden");
    }
  });
  connect();
})();
