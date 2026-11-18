# SPEC.md — Voidwell-3: the Perspective Walk

Version 3.0.0 · specification of the construction distributed in this
repository (`ucq/`, `voidwell3/`, `tests/`).

> **Status of this document.** This is the reimplementation
> specification: a complete, self-contained, byte-level definition of
> Voidwell-3, written so that an independent implementation produced
> from this document alone — without reading the source — reproduces
> every published hash bit for bit. An implementation is **conformant**
> when it (a) reproduces the test vectors of §15, (b) accepts an
> honest key with `PASS` and rejects a wrong key with `FAIL` (§14),
> and (c) rejects every malformed publication listed in §13.3. Where
> this document and the reference implementation disagree, the
> reference implementation is normative; report the disagreement as a
> bug in either.

The construction's security claim is stated first, as part of the
specification and not as an afterthought: **security = min(seed bits,
256) under the sole assumption of SHA-256 preimage resistance.** No
layer defined below purports to add hardness beyond the seed width,
and no layer subtracts from it. Everything below — the perspectives,
the wells, the ghost disc, the zeta array — is binding, audit, and
accounting machinery. The expected attack effort is 2^(seed_bits−1)
full-walk replays (half the key space, on average, for a uniformly
random target).

---

## 1. Overview

Voidwell-3 is a hash-and-key construction. Inputs: a secret **seed**
(2, 16, or 32 bytes), a public **data block** (arbitrary bytes), and
the public parameters (§2). Output: a 256-bit hash **H**.

One encoding, in one paragraph:

1. The seed expands, through SHA-256-based PRFs, into an initial
   state `D₀` and four checkpoint states `C₁..C₄` (§6).
2. A 43-step walk carries a 27-bit state through a fare-octal digit
   space by three public bijections (§7). At four public positions —
   the first four primes — a **well** fires: the state is lifted to a
   4×4 matrix over a 256-bit prime field, twisted by a public
   *perspective* matrix, conjugated by a seed-derived matrix chosen so
   that the conversion nullifies a named digit, recorded as a
   full-width **nullifier**, and the walk restarts from the
   checkpoint (§8).
3. Every state along the walk becomes a leaf of a canonical Merkle
   tree — the **ghost disc** (§9).
4. The four wells' material fills a 4×4 array of named hashes — the
   **zeta cells** — which the quaternion multiplication table then
   permutes and signs: the **disentangling** (§10).
5. One final SHA-256 over the ghost root, the sixteen disentangled
   cells, the final state, and the public constants contracts
   everything into **H** (§11).

The gate (§14) replays all of it from a candidate seed and compares
H in constant time. The attacker's view is H and the public
parameters — nothing else exists on the wire.

---

## 2. Parameters and profiles

### 2.1 The two profiles

| | **FULL** (flagship, compact) | **TOY** (study-toy) |
|---|---|---|
| Prime field | p = 2²⁵⁶ − 2³² − 977 | p = 257 |
| Matrix algebra | 4×4 over F_p | 2×2 over F_p |
| State | 9 octal digits (27 bits) | 8 one-bit digits (8 bits) |
| Walk length | L = 43 | L = 10 |
| Wells | positions 2, 3, 5, 7 / digits 2, 3, 5, 7 | **the same** |

The full-model prime, in hex:

```
p = 0xffffffff ffffffff ffffffff ffffffff
    ffffffff ffffffff fffffffe fffffc2f
```

(the secp256k1 field prime — chosen as a well-known, independently
verifiable 256-bit prime; it carries no elliptic-curve meaning here).

### 2.2 The well schedule (public constants)

```
PRIMES      = [2, 3, 5, 7]
WELLS       = [(2,2), (3,3), (5,5), (7,7)]     # (position, digit)
K           = 4                                  # number of wells
DEFAULT_E   = 1                                  # the involution exponent (§12)
```

The j-th well (j = 1..4, in position order) sits at walk position
`PRIMES[j−1]` and nullifies state digit `PRIMES[j−1]`. The j-th well
uses the j-th perspective unit (§5). The schedule is fixed: a
challenge may not vary it (§13.3).

A challenge may publish a *prefix* of the schedule: parameter `k`
(0 ≤ k ≤ 4) selects the first k wells. `k = 4` is the canonical
challenge; `k = 0` is the empty schedule (the small-model collapse
demonstration). Partial schedules are valid inputs to `run_path` and
produce correspondingly fewer nullifiers and zeta cells (4k cells,
§10).

### 2.3 The variants

| Variant | Seed | Claimed security |
|---|---|---|
| `flagship` | 32 bytes | min(256, 256) = 2²⁵⁶ |
| `compact` | 16 bytes | min(128, 256) = 2¹²⁸ |
| `study-toy` | 2 bytes | min(16, 256) = 2¹⁶ — breakable by design |

`study-toy` runs on the TOY profile; `flagship` and `compact` on
FULL. The variant fixes only the seed width and the profile; the
algorithm is identical.

---

## 3. Serialization primitives

All integers are **big-endian**. All hex is lowercase. All hashes are
SHA-256 (`SHA` below); the XOF is SHAKE-256.

**ser_state(profile, state)** — canonical state serialization:

```
w = ceil(state_bits / 8)                    # FULL: 4, TOY: 1
ser_state = 0x03 || w as 1 byte || state as w bytes big-endian
```

**ser_matrix(Q)** — canonical matrix serialization (entries reduced
mod p):

```
w_p = ceil(bit_length(p) / 8)               # FULL: 32, TOY: 2
ser_matrix = 0x01 || n as 2 bytes || bit_length(p) as 2 bytes
             || entries row-major, each as w_p bytes big-endian
```

**ser_wells(wells, e)** — the schedule commitment input:

```
ser_wells = 0x03 || len(wells) as 1 byte
            || for each (position, digit): position as 2 bytes || digit as 1 byte
            || e as 2 bytes
wells_digest = SHA(ser_wells)               # 32 raw bytes enter H
```

Domain-separation prefixes (ASCII): `"D0"`, `"C"`, `"M"`, `"V3N"`,
`"V3G"`, `"V3Z"`, `"V3H"`.

---

## 4. The state space and the lift

**State.** A FULL state is an integer in 0..2²⁷−1: nine octal
digits `d₈..d₀` (digit n occupies bits 3n..3n+2; `digit_value(D, n) =
(D >> 3n) & 7`). A TOY state is one byte: eight one-bit digits
(`digit_value(D, n) = (D >> n) & 1`).

**lift(profile, state) → matrix.** The state's bits are packed into
the matrix entries by a fixed table. With `n_cells = size²` (FULL:
16, TOY: 4):

```
cells = [0] * n_cells
for j in 0 .. state_bits-1:
    if bit j of state is set:
        cells[j mod n_cells] |= 1 << (j div n_cells)
Q[r][c] = cells[r * size + c]        # row-major, entries mod p
```

That is: state bit j lands in matrix cell `j mod n_cells`, at bit
position `j div n_cells` of that cell's value. For FULL, bits 0..15
fill bit 0 of cells 0..15, and bits 16..26 fill bit 1 of cells 0..10.
For TOY, bits 0..3 fill bit 0 of cells 0..3 and bits 4..7 fill bit 1.

**project(profile, Q) → state.** The exact inverse: state bit j is
bit `j div n_cells` of entry `Q[j mod n_cells div size][j mod
n_cells mod size]`. The round trip `project(lift(D)) = D` holds for
every state (verified exhaustively on TOY, 5000 samples on FULL —
battery W2). Every lift entry is < 4, so the map is injective on
states; the conjugation orbits live in the full matrix space.

---

## 5. The perspective units (public constants)

Four public matrices over F_p, one per well. FULL (4×4):

```
U₁ = diag(1, 1, 0, 0)
U₂ = diag(0, 0, -1, -1)
U₃ = [[0,-2, 0, 0],      U₄ = [[0,-1, 0, 0],
      [ 1, 0, 0, 0],            [ 1, 0, 0, 0],
      [ 0, 0, 0,-2],            [ 0, 0, 0,-1],
      [ 0, 0, 1, 0]]            [ 0, 0, 1, 0]]
```

TOY (2×2):

```
U₁ = diag(1, 0)     U₂ = diag(0, -1)
U₃ = [[0,-2],       U₄ = [[0,-1],
      [ 1, 0]]            [ 1, 0]]
```

(Entries mod p; −2 and −1 mean p−2 and p−1.)

The four laws, exact matrix identities over any odd prime field:

```
U₁² = U₁                    (UC1, the Complex Point: idempotent)
U₂² = −U₂                   (UC2, the Complex Line: anti-idempotent)
U₃² = −I − U₁² − U₂²        (UC3, the Complex Disc: defined by the closure)
U₄² = −I                    (UC4, the Field: the proper complex unit)
U₁² + U₂² + U₃² + I = 0     (the loop closure)
```

The gate recomputes all five identities from the constants before any
replay (§14). Note U₃² = −2I exactly (and U₂² = −U₂ = diag(0,0,1,1)
in FULL), so the four units' squares are the four different kinds of
"imaginary unit square": U₁, −U₂, −2I, −I — the four perspectives.

**The twist.** Well j does not conjugate the lifted state directly;
it conjugates the state *as seen from* perspective j:

```
T_j(X) = X + U_j · X · U_j                  (public, linear)
```

**The trace law.** For every well conversion (conjugation cannot
change a trace):

```
tr(Q′_j) = tr(T_j(Q)) = tr(Q) + tr(Q · U_j²)
```

where `tr(Q · U_j²) = Σ_{i,k} Q[i][k] · U_j²[k][i] mod p`. The gate
checks this per well; a forged conversion passes with probability
1/p.

---

## 6. The PRF: scalars and matrices from the seed

**Scalar PRF** (SHA-256, unchanged from Voidwell-2):

```
prf_bytes(seed, domain, indices...) =
    SHA( len(seed) as 1 byte || seed || domain || each index as 4 bytes )
```

**Digivector derivation** (a state in 0..2^state_bits−1):

```
raw = prf_bytes(seed, domain, 0) || prf_bytes(seed, domain, 1, 0)   # 64 bytes
state = int(big-endian raw) mod 2^state_bits
```

The initial state and the four checkpoints:

```
D₀ = digivector(seed, "D0")
scale_j = PRIMES[j-1]^e mod p                     # §12
C_j = digivector(seed, "C" || j as 1 byte || scale_j as 32 bytes)   # j = 1..4
```

Note the 32-byte scale encoding is fixed even in the TOY profile.
Checkpoints are derived once per encoding and consumed in well order.

**Matrix XOF** (one SHAKE-256 call per candidate):

```
stream = SHAKE256( len(seed) as 1 byte || seed || "M"
                   || j as 4 bytes || ctr as 4 bytes || scale_j as 32 bytes,
                   output 32·size² bytes )
entry (row-major) = the next 32-byte chunk, as an integer, mod p
```

---

## 7. The base walk: three bijections

Between wells, the state moves by public bijections whose control
bits come from the public data block. At step i (1-based):

```
block_i = data[(i-1) mod len(data)]        # 0 if data is empty
```

A well step consumes no data block (block_i is simply not used at
well positions).

**base_step(state, block) → (state′, fare):**

```
op = block mod 3

op 0 — the Λ-carry (a binary increment):
    g    = (block >> 2) mod state_bits
    state′ = (state + 2^g) mod 2^state_bits
    fare  = carry-chain length: k consecutive 1-bits starting at bit g,
            then fare = k+1 if the chain stops inside the register
            (k = 0, or g+k < state_bits), else k (carry off the top)

op 1 — the τ-rotate (a digit swap):
    n  = (block >> 2) mod n_digits
    n′ = (n + 1 + (block >> 5)) mod n_digits
    swap digit values at n and n′
    fare = 1 if the two values differed, else 0

op 2 — the ξ-write (a digit XOR):
    n = (block >> 2) mod n_digits
    v = (block >> 5) mod 2^bits_per_digit       # FULL: & 7, TOY: & 1
    digit n := digit n XOR v
    fare = 1 if v ≠ 0, else 0
```

Every operation is a bijection of the state space, so the walk
between checkpoints is a public permutation — it cannot lose
information (this is V3's structural fix for V2's measured mixer
degeneracy of 18.21 of 27 bits). The **fares** do not enter H; they
are the ledger quantities of §16 (the fare ledger, τ² = 0).

---

## 8. The wells

At step i, if i is the position of the j-th well (j = 1..k in
schedule order) with digit target n:

```
Q   = lift(D)                          # D = the arriving state
TQ  = T_j(Q)                           # §5: TQ = Q + U_j · Q · U_j
M   = the accepted candidate matrix     # rejection loop, below
Q′  = M · TQ · M⁻¹                     # exact conjugation over F_p
D′  = project(Q′)
```

**The rejection loop** (the only place the seed chooses among
candidates): draw candidates from the XOF (§6) in counter order
ctr = 0, 1, 2, …; skip singular candidates; **accept the first M for
which digit n of project(M · TQ · M⁻¹) is zero.** The acceptance
probability per candidate is ≈ 1/2^bits_per_digit (FULL: 1/8, TOY:
1/2), so the expected counter is small (geometric); the loop gives up
after 10 000 tries (probability of reaching that < 2⁻¹³⁰). The
counter ctr is issuer-side effort and enters nothing published.

**The two in-path audits** (checked by the encoder and re-checked by
the gate inside the replay):

```
digit n of D′ = 0                                  (emergent nullification;
                                                   a wrong matrix passes with
                                                   probability 2^-bits_per_digit)
tr(Q′) = tr(Q) + tr(Q · U_j²)                      (the trace law, §5)
```

**The nullifier** — a full-width commitment to the entire conversion:

```
N_j = SHA( "V3N" || ser_state(D′) || ser_matrix(Q′) )
```

In FULL the preimage commits 27 state bits and 4096 matrix bits (a
2⁴¹²³ entropy domain before framing). The nullifier is the only
per-well value, and it is *never published* — it feeds the zeta cells
(§10).

**The fare** at a well is the destroyed digit: `fare = digit n of D`
(the arriving state). The walk then **restarts**: `D := C_j`.

After the last step, the sequence `D₀, D₁, …, D_L` (L+1 states; 44 in
FULL) is the complete walk record.

---

## 9. The ghost disc: the Merkle accumulator

Every state becomes a leaf; the tree is canonical:

```
leaf_i   = SHA( "V3G" || ser_state(D_i) )
node     = SHA( left || right )
odd leaf = promoted unmixed (hashed value passes upward unchanged)
root     = the single remaining node
```

The root enters H at full strength. A key holder can **open** any
single state with its sibling path (⌈log₂(L+1)⌉ hashes; 6 for 44
leaves): the verifier recomputes upward, using the leaf index for
left/right order and passing promoted levels (no sibling) unchanged.
This is V3's partial-proof capability: state i is provable without
revealing any other state.

---

## 10. The zeta array and the disentangling

Sixteen named commitments — axes: quaternion component × perspective
well:

```
cell(a, b) = SHA( "V3Z" || a as 1 byte || b as 1 byte || N_{b+1} (raw 32 bytes)
                  || each entry of row a of Q′_{b+1}, as 32 bytes big-endian )
```

with a ∈ {0,1,2,3} (components 1, i, j, k) and b ∈ {0,1,2,3} (wells
1..4). Two details are normative: the nullifier enters **raw** (32
bytes), and the row entries are always encoded as **32-byte**
integers — in *both* profiles, including TOY (where p = 257 would
fit in 2 bytes). Row a of a TOY matrix is `rows[a mod 2]`. For a
partial schedule with k wells, only the 4k cells of the present
wells exist.

**The disentangling map** — the quaternion multiplication table,
verbatim. For the product q_a · q_b (components 1, i, j, k indexed
0..3), the table gives the component μ_b(a) of the product and its
sign:

```
μ₀ = (0,1,2,3)     μ₁ = (1,0,3,2)     μ₂ = (2,3,0,1)     μ₃ = (3,2,1,0)

sign(a,b):  +1 on row a=0 and column b=0;
            (1,1)− (1,2)+ (1,3)−
            (2,1)− (2,2)− (2,3)+
            (3,1)+ (3,2)− (3,3)−
```

Each cell is re-hashed with its sign and moved to the product's
component:

```
disentangled[μ_b(a), b] = SHA( cell(a,b) raw || (sign(a,b) mod 256) as 1 byte )
```

(+1 encodes as 0x01, −1 as 0xFF.) Each μ_b is a permutation, so the
16-cell map is a bijection — the gate re-audits this (§14). The
canonical output order is well-major: `[disentangled[a, b] for b in
0..3 for a in 0..3]`.

**Serialization for H:**

```
ser_cells = 0x03 || (4·k) as 1 byte || the disentangled cells, raw 32 bytes each,
             in canonical order
```

---

## 11. The contraction: the final hash

```
H = SHA( "V3H"
         || ghost_root (raw 32 bytes)
         || ser_cells                        (§10)
         || ser_state(D_L)                   (the final state)
         || wells_digest (raw 32 bytes)      (§3)
         || e as 2 bytes big-endian )
```

H is published as 64 lowercase hex characters. Everything the gate
needs to recompute it is either public or derived from the seed.

---

## 12. The involution exponent e

The Fare Algebra's spectral involution acts on the prime index n as
n ↦ n^(1−2s). Voidwell-3 publishes the integer exponent

```
e = 1 − 2s   (mod p−1),      0 ≤ e ≤ p−2
```

and folds `scale_j = PRIMES[j−1]^e mod p` into every checkpoint and
well-matrix derivation domain (§6). At the critical value s = ½ the
exponent is e = 0, every scaling is n_j⁰ = 1 — the involution is the
identity, its unique fixed point — and the parameter is a visible
dial: e = 0 and e = 1 produce different H (battery W7). The default
challenge uses **e = 1** (s = 0). Whether any e ≠ 1 interacts
differently with the wells is an open problem (§17).

---

## 13. Publication format

### 13.1 The challenge (all that is published)

A JSON object with exactly these six fields:

```json
{
 "version": 3,
 "params": {
  "construction": "perspective-walk",
  "variant": "flagship",
  "seed_bits": 256,
  "lift_version": 1,
  "digits": 9,
  "bits_per_digit": 3,
  "L": 43,
  "k": 4,
  "e": 1,
  "wells": [[2,2], [3,3], [5,5], [7,7]]
 },
 "data": "00112233",
 "data_commitment": "aafa373bf008a855815ecb37d8bd52f6a8157cb5833c58edde6d530dbcf3f25d",
 "nullifier_count": 4,
 "H": "8c0b6127ca1c65966c63ab34190d7370f7d6e34c00e448d33809bcbe59e6bf20"
}
```

Normative field values:

- `version` = 3; `params.construction` = `"perspective-walk"`;
  `params.lift_version` = 1.
- `variant` ∈ {`flagship`, `compact`, `study-toy`};
  `seed_bits` must equal the variant's width (256 / 128 / 16).
- `digits` / `bits_per_digit` select the profile: (9, 3) → FULL,
  (8, 1) → TOY. Any other pair is malformed.
- `L` is the walk length (canonical: 43 FULL, 10 TOY); it must be an
  integer with every well position inside 1..L.
- `k` = the number of wells (0..4); `nullifier_count` = k.
- `e` an integer in 0..p−2 of the challenge's profile.
- `wells` = the first k entries of the schedule constants (§2.2) —
  exactly; no schedule freedom exists.
- `data` = the public data block, hex; `data_commitment` =
  SHA(data) as hex.
- `H` = 64 lowercase hex characters.

### 13.2 The key (held by the key holder only)

```json
{ "version": 3, "variant": "flagship", "seed": "<seed hex>" }
```

The seed must be exactly the variant's width in bytes.

### 13.3 The surface rules

A challenge carrying any field beyond the six above is malformed.
Publishing per-well values is a **spec violation**, not merely bad
practice: the field names `nullifiers`, `schedule`, `schedule_digest`,
`wells_detail`, `ghost_root`, `zeta_cells` are rejected on sight.
With H-only publication, secret well positions would buy zero bits —
the surface is minimal by construction, and the gate enforces it.

---

## 14. The gate

`gate(challenge, key)` decides among three outcomes — **PASS** (0),
**FAIL** (1), **MALFORMED** (2) — in this order:

1. **Schema and surface** (§13): parse both JSONs; check every field
   value; reject unknown or forbidden fields → MALFORMED.
2. **The public-math audits** → MALFORMED on failure:
   - the perspective laws: the five identities of §5, recomputed from
     the constants;
   - the quaternion audit: each μ_b is a permutation of 0..3;
   - the schedule: wells equal the public constants, positions
     inside 1..L, strictly increasing, digits in range.
3. **Key checks** → MALFORMED: version 3, variant matches the
   challenge, seed hex of the exact variant width.
4. **The replay**: recompute the entire walk from (profile, data,
   seed, wells, L, e) through the same path as the encoder —
   including the rejection loop, the emergent nullification and the
   trace law per well (a violation → FAIL), the ghost tree, the 4k
   cells, the disentangling — and check `nullifier_count` matches
   the produced count.
5. **Binding**: compare the recomputed H with the published H in
   constant time (e.g. `hmac.compare_digest`).

A wrong seed yields FAIL only at step 5 (binding), not earlier: the
in-path audits pass for any seed because they are properties of the
construction, not of the key. Anyone can verify a candidate key
locally; no issuer is needed.

---

## 15. Test vectors

All vectors use the standard schedule (k = 4), e = 1, and the public
data block `data = 00112233`. An implementation that cannot reproduce
these bit for bit is not conformant.

**V1 — study-toy (TOY profile, L = 10), published case 1.**

```
seed = 104f
H    = 2bb7236985d8d8394c568c2a55d711817c26fc07455805e3452b592ea47f8266
```

**V2 — compact (FULL profile, L = 43), published case 2.**

```
seed = 4f062253c2e10034a651ba793244c10f
H    = b703646ebdde0955782fbd31a01d16b62357f711df85ad58ca5e47b2c16e94cd
```

**V3 — flagship (FULL profile, L = 43), fixed reference seed.**

```
seed = 0000000000000000000000000000000000000000000000000000000000000000
H        = 53c7396cfc54007ed77455ffcb79cb8aabf807fe7754edde41e8bb908bd95111
ghost root = 2102e8fc7afece620e008dd8402a48c8793f065944f97bd298d8f85f07ba352c
D₀ = 302204370 (octal)   D_L = 174547511 (octal)
well rejection counters: ctr = 4, 1, 8, 1 (issuer-side; not published)
```

**V4 — flagship, the open challenge (published case 3).** The target;
the key is withheld:

```
H = 8c0b6127ca1c65966c63ab34190d7370f7d6e34c00e448d33809bcbe59e6bf20
```

Reproduce V1–V3 with the reference CLI (`python3 -m voidwell3 encode
<seed hex>` for V3; the study cases gate to PASS from their published
challenge/key pairs). As a completeness check of this document, an
independent implementation written from this SPEC alone — without
reading the reference source — reproduces all of the above, including
the V3 ghost root, D₀, D_L, and the four rejection counters. It ships
in this repository as `tests/spec_conformance.py` (run `python3 -I
tests/spec_conformance.py` from the root), so the claim is checkable,
not believed.

---

## 16. The fare ledger (audited, not hashed)

Each step pays a fare (§7, §8): the carry-chain length, the
distinctness of a swap, the non-zeroness of a write, the destroyed
digit at a well. Fares do not enter H. They form the **path
polynomial** — coefficient i is the i-th state paired with its fare —
on which the monograph's τ² = 0 law is verified on real paths
(battery W9, both profiles): the fare of the path equals the sum of
the step fares *exactly*, for any path: the trace is paid linearly
and cannot compound. See `ucq/ucpoly.py`.

---

## 17. Open problems

Named, and part of the record:

1. **The group-action direction.** Whether a well can earn independent
   hardness — a conjugation orbit with a hard discrete-log-like
   structure — rather than serving as a commitment layer.
2. **The critical-line dial.** Whether the exponent e (§12) can be
   exploited for any e, or interacts with the wells in any way the
   fixed-point analysis does not cover.
3. **Selective disclosure.** What protocols the ghost disc's
   logarithmic per-state proofs (§9) can serve beyond single-state
   opening.

---

## 18. Conformance: the verification battery

`python3 -m voidwell3 verify` runs the 34-check battery (all green in
the distributed record):

```
W1  the perspective laws + closure (full and toy; plus the closure
    identity recomputed entrywise — 3 checks)
W2  lift/project round trip (TOY exhaustive; FULL 5000 samples)
W3  base ops bijective (TOY exhaustive, 8 blocks); D_L per-digit
    entropy ≈ 3.0 bits (V2 measured 18.21/27 — the mixer's collapse)
W4  ghost open/verify (6 positions); tree internal consistency;
    tamper detection; root differs across seeds
W5  quaternion table exact (all 16 products); 16 zeta cells distinct
    and recomputable
W6  the trace law at all wells; negative control (perturbed Q′
    fails)
W7  the fixed point: e = 0 makes every prime scaling 1; e is live
    (e = 0 and e = 1 give different H); the wells digest commits e
W8  full-width nullifiers (2^4123 preimage domain before framing)
W9  τ² = 0 ledger linearity on real paths (both profiles)
W10 H byte chi-square vs uniform (512 seeds); avalanche (128 one-bit
    seed flips)
W11 compact and flagship encode + gate round trips
W12 gate: honest key PASS; wrong key FAIL; published nullifiers
    MALFORMED; off-skeleton wells MALFORMED; non-integer e
    MALFORMED; wrong H FAIL
W13 speed: a perspective well costs less than a V2 well
W14 determinism (same seed → same H); matrix serialization round
    trip
```

Reference-implementation performance (one core, pure Python):
≈ 7 ms per full-model replay (≈ 140 replays/s), dominated by the
four well conjugations and the rejection loop.

---

## 19. The reference implementation

Pure Python 3.10+, standard library only. From the repository root:

```
python3 -m voidwell3 params                # the public constants
python3 -m voidwell3 encode <seed hex>     # one encoding, verbose
python3 -m voidwell3 seal <dir> [variant]  # issue a challenge + key
python3 -m voidwell3 gate <challenge> <key>
python3 -m voidwell3 demo                  # one guided encoding
python3 -m voidwell3 toy                   # the exhaustive small model
python3 -m voidwell3 verify                # the 34-check battery
```

Module map: `ucq/` (fields, matrices, lift, conjugation, the ledger),
`voidwell3/` (perspectives, wells, PRF, ghost, zeta, encoder, gate,
CLI), `voidwell3/attacker/` (seed search, surface audit, toy
dictionary), `tests/verify.py` (the battery),
`tests/spec_conformance.py` (the from-SPEC reimplementation, §15).
The attacker ships in the same package as the construction so the
security claim can be checked, not believed.

## 20. License and citation

Released under the MIT license (`LICENSE`). If you use this software,
please cite it as described in `CITATION.cff`.
