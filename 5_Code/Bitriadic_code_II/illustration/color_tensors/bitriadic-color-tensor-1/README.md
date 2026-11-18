# Bitriadic Color Tensor

An instrument for the mathematical analysis of color — a proof of concept
that makes the color tensor of *Poetica Mathematica* (Ch. IX §9.4.2,
"The Color Tensor: A Second Verification of the 81-Point Grammar")
executable: an interactive, single-file web instrument with operator
selection, live assignment analysis, the full 81-point space, color
input and conversion, and a ring calculator demonstrating τ² = 0.

## Run it

Open `index.html` in any browser. There is no server, no build step, no
dependency: one self-contained file, everything computed locally. Works
on desktop and mobile (responsive, tested at 375 px).

## The mathematics (from the monograph)

Each color operator X is an element of a commutative ring ℭ over ℝ with
a nilpotent generator τ² = 0:

    X = val(X) + τ·tr(X)

- **val** — the flow pool: the intensity of light contributed.
- **tr** — the absorption pool: the nilpotent record of wavelengths
  absorbed. Recording the same absorption twice annihilates the record.

The operators stand in a 3 × 4 matrix. Three mixing regimes:

| Row | Regime | Pools |
|---|---|---|
| I | Additive | v = M, t = 0 (light, no history) |
| II | Subtractive | v = 0, t = M (absorption only) |
| III | Mixed | v = t = M (both, equal) |

Four spectral channels with power-of-two magnitudes:

| Col | Channel | M | Additive | Subtractive | Mixed |
|---|---|---|---|---|---|
| 1 | Red / Cyan | 1 | R | C | W₁ = R + C |
| 2 | Blue / Yellow | 2 | B | Y | W₂ = B + Y |
| 3 | Green / Magenta | 4 | G | M | W₃ = G + M |
| 4 | Reflex / Spectrum | 8 | W₄ (white reflex) | K (black reflex) | Ω (equilibrium) |

An assignment selects one operator per column: 3⁴ = **81** assignments.
Operators combine component-wise; with V the total flow, T the total
absorption, the imbalance is Δ = V − T (Row I contributes +M, Row II
−M, Row III 0). The verified partition:

- **40 bright** (Δ > 0, excess flow)
- **40 dark** (Δ < 0, excess absorption)
- **1 equilibrium** (Δ = 0) — uniquely the all-mixed choice
  W₁ + W₂ + W₃ + Ω, **the witness**: the equilibrium grey, the neutral
  ledger, "the grey that underlies every graphic program's color
  picker."

The instrument re-verifies the 40/40/1 partition live, in your browser,
by enumerating all 81 assignments. An independent Python cross-check
(tools below) confirms the same numbers.

Named phenomena the tensor captures, per the monograph:

- **Metamerism** — W₁, W₂, W₃, Ω render the identical equilibrium grey
  yet carry different spectral histories: "different spectral
  distributions appear as the same color because the observer samples
  only a finite projection of the continuum."
- **Additive–subtractive duality** — the all-additive assignment
  renders white, the all-subtractive black; swapping Row I ↔ II in
  every column negates Δ (an involution pairing the 80 non-equilibrium
  assignments).
- **The neutral axis as equilibrium** — the witness is not a grey among
  greys but the state where every channel's flow and absorption cancel
  exactly: the monochrome era persisting inside the six-hue space.
- **The reflex pair** — W₄ (appears pure white; its zero trace records
  its additive origin) and K (appears pure black; its zero value
  records its subtractive origin).

## The instrument

1. **The twelve operators** — the interactive 3 × 4 matrix; click a
   cell to choose that regime for its channel. "Reveal the ledger"
   shows the magnitudes the observer cannot see (metamerism).
2. **The assignment under analysis** — the four regime pickers, the
   total operator X = V + τ·T, Δ and its classification, the rendered
   color, the position on the grey ladder, and per-channel
   contributions. Presets: the witness, the additive/subtractive poles,
   random.
3. **The 81-point space** — every assignment rendered (rows: channels
   1–2, columns: channels 3–4), the witness marked in gold, click to
   analyze; plus the Δ histogram with the live 40/40/1 verification and
   the collision analysis (the powers of two collide: 22 values of Δ
   arise more than once; Δ = 0 arises exactly once).
4. **Color ⇄ tensor: the observer's gate** — pick or type a color; it
   decomposes into the four channel signals (red–cyan, blue–yellow,
   green–magenta, luminance residual) and quantizes onto the regimes
   through the spectator's gate ε — the fare that trades the continuum
   for the legible split. The nearest rendered assignment is reported
   alongside; when gate and projection disagree, the color sits between
   two ledgers (try pure white: the gate reads the reflex white, the
   projection the additive white — two whites no observer can tell
   apart).
5. **The ring calculator** — pool-wise addition and ring
   multiplication (v₁ + τt₁)(v₂ + τt₂) = v₁v₂ + τ(v₁t₂ + t₁v₂), the τ²
   term annihilated. Presets: R + C = W₁ (the metameric white),
   C × C = 0 (duplicate absorption annihilates), W₁ × W₁, and the
   witness sum W₁ + W₂ + W₃ + Ω.
6. **What the instrument demonstrates** — the threefold verification
   table (Fortress arithmetic / semantic tensor / color tensor), with
   the documented conventions.

## Conventions (design choices of this instrument)

The monograph defines the algebra — the ring, the twelve operators,
the mixing rule, Δ, the partition. To render color, the instrument
fixes three documented conventions (also stated in the app, under
"the instrument's conventions"):

- **Cell identity colors** — Row I/II cells render their exact
  primaries (R, B, G, W₄; C, Y, M, K); all four Row III cells render
  the same equilibrium grey (metamerism by construction).
- **Assignment rendering (the observer's projection)** — with row
  signs sⱼ and Δ = Σ sⱼ·Mⱼ: ladder luminance l = ½ + Δ/30; opponent
  chroma (a−b−g, −a−b+g, −a+b−g) from the three chromatic columns,
  projected to zero achromatic leakage; saturation gain 2·min(l,1−l)/3
  (chroma vanishes at the ladder's ends); clamp. All 81 assignments
  render distinctly under this rule.
- **The gate** — a color decomposes as a = r − (g+b)/2,
  b = bl − (r+g)/2, g = gr − (r+bl)/2, l = (r+g+bl)/3; the chromatic
  axes quantize to Row I / III / II against ±ε; the reflex column takes
  the normalized luminance residual against the same ε.

## Verification

- The 40/40/1 partition, the uniqueness of the equilibrium, the Δ
  collision structure, the ring identities (C × C = 0, R + C = W₁,
  W₁ + W₂ + W₃ + Ω = (15, 15)) are verified **live in the app**.
- The same facts were cross-checked against an independent Python
  enumeration, and the app's JavaScript math was tested in isolation
  against that ground truth (22/22 checks, including the rendering of
  the poles, the witness grey, the gate quantization of canonical
  colors, and the nearest-assignment search).
- Layout verified at 1280 px and 375 px: no page-level horizontal
  overflow; the 81-grid and tables scroll inside their containers.

## Source

*Poetica Mathematica* — Ch. IX §9.4.2, "The Color Tensor: A Second
Verification of the 81-Point Grammar"; §9.4.3 "Conclude: The Threefold
Verification of the 81-Point Grammar" (the Fortress arithmetic, the
semantic tensor, the color tensor); Question XIII.52 and Answer 53
(color as a tensor with nilpotent trace; metamerism,
additive–subtractive duality, the neutral axis as equilibrium).

## License

MIT License · Copyright (c) 2026 Kirill I. Kovlekov
