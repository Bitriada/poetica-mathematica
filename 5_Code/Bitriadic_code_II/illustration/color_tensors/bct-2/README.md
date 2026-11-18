# BCT-2 · Colors that remember

A single-file web app: the bitriadic color tensor as a **teaching
instrument, a game, a reference manual, and an honest list of failures**.
Built on the color tensor of *Poetica Mathematica* (Ch. IX §9.4.2) and
embedding the BCT-1 instrument (part 3) as its reference machine.

## Run it

Open `index.html` in any browser. No server, no build, no dependencies —
one self-contained file, everything computed locally. Responsive, tested
at 375 px and 1280 px.

## The four parts

### 1 · Six facts you can poke (plain language, no jargon)

Each fact states something true about the model, explains it in plain
words, then lets you make it happen:

1. **Three lights, three inks** — six toggles, physical rendering
   (lights add, inks filter), a color-wheel dot that shows position.
2. **The same grey, three ways** — the three light+ink pairs, one
   identical grey, three different ledgers (metamerism, unstated).
3. **Every color has a mirror** — the light↔ink involution: totals
   trade places, balance flips sign (additive–subtractive duality).
4. **Grey is a balance, not a color** — a slider across the whole
   ladder; exactly one state in 81 balances perfectly.
5. **One number, many colors** — the five states that share balance +3;
   the collision fibers of the imbalance.
6. **The notebook will not write the same memory twice** — nilpotency
   (τ² = 0) as an ink-note that annihilates on re-write, while light
   merely accumulates.

### 2 · The Fruition game (a roguelike)

You are given a broken color: three columns (weights 1, 2, 4), all
leaning against your chosen fruition. Each click plays one of three
offered cards. When all three columns are fully yours, the fourth
column — the Spectrum, the recorder that stays balanced all game —
seals your color: pure White or pure Black. **Par is 10 clicks.**
The game object is readable at a glance: a color and its history.

The five cards (odds out of 10): **Coin** (3) — flip for your biggest
unfinished column; **Sift** (2) — your smallest unfinished column leans
over, sure thing; **Flood** (2) — a random half-done column comes all
the way over; **Slip** (2) — the weakest half-done column slips back;
**Stir** (1) — one leans your way, then the weakest half-done one slips
back. Columns fully with you are safe; only half-done work decays.

**Balance math** (verified by simulating 20,000 games of perfect
greedy play before building):

- median **10 clicks** (mean 10.6), middle 80% of runs between 6 and 16
- per-play randomness worth **0.75–1.5 clicks** toward the target,
  never more than 2 — luck matters, skill decides
- **zero unwinnable games**; the start is deterministic (all columns
  opposed, balance −7) so all variance is card luck
- best scores per fruition persist locally (browser localStorage)

Design decisions found by simulation: a periodic "grey pull" drag
either does nothing or creates unwinnable endgames (median 30+, 4%
stalls) — so the pull lives inside the cards (Slip, Stir) instead;
"aligned is safe, only half-done decays" is the rule that bounds every
run; a deterministic start removes luck from game length the player
cannot influence.

### 3 · The machine (BCT-1 embedded)

The full instrument from the first proof of concept, embedded verbatim,
preceded by a plain-words→machine-names glossary and an explanation of
what the weights and parameters do and why: the powers of two (why
Δ = 0 has exactly one owner), the gate ε (the price of a legible
answer), and the observer's rendering rule. Interactive: the 3×4
operator matrix, the assignment panel, the 81-point space with the live
40/40/1 verification, the color→tensor gate with nearest-assignment
search, and the ring calculator (R + C = W₁, C × C = 0, the witness
sum). It verifies the monograph's central claim in your browser on
every load.

### 4 · Where it breaks

- **Where the model fails (research map):** the balance is not
  brightness; the fourth column has no receiver; the number collides;
  mixing is straight-line; 81 states cannot name every color; no
  wavelengths; the picture is a convention. Each with what fixing it
  would need.
- **Where the computer representation fails (open questions):** the
  pixel erases history; pickers teach the wrong grey; screens live
  inside metamerism; files keep no provenance; the language gap —
  "same color" conflates same-looking with same-made, which is why
  metamerism is hard to think about. Ends on the open question: what
  would a color representation that ordinary intuition reads as
  *made-of* rather than *looks-like* look like?

## Verification

- All four scripts pass `node --check`; the embedded instrument's math
  is the BCT-1 code, previously cross-checked 22/22 against an
  independent Python enumeration.
- Game card semantics mirror the tuning simulator exactly (documented
  in `fruition_sim_final.py`); a full playthrough, replay, goal switch,
  restart, quit, and best-score persistence were exercised in a real
  headless browser, with zero console errors.
- Every fact widget was driven programmatically (toggles, recipes,
  inversion, ladder slider, collision cycler, the annihilation rule).
- Layout audited at 375 px (no page-level overflow; wide tables and the
  81-grid scroll inside their containers) and 1280 px.

## Source

*Poetica Mathematica*, Ch. IX §9.4.2 "The Color Tensor: A Second
Verification of the 81-Point Grammar"; §9.4.3 (the threefold
verification); Question XIII.52 / Answer 53. BCT-1 (the embedded
instrument) is the first proof of concept from the same project.

## License

MIT License · Copyright (c) 2026 Kirill I. Kovlekov
