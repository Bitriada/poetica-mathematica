"""encoder.py -- the Voidwell-3 encoder: the Perspective Walk.

THE CONSTRUCTION (one deterministic code path shared by the encoder,
the gate, the small-model harness and the attacker package -- the V2
discipline, kept):

  D_0 = prf_digivector(seed, "D0")
  for i in 1..L:
      if i is the j-th well position (PUBLIC: the j-th prime):
          scale = n_j^e mod p               (the involution exponent)
          T_j  = the j-th perspective twist (perspectives.py)
          M_j  = XOF matrix stream, rejection-sampled until
                 project(M_j T_j(lift(D)) M_j^{-1}) has digit n_j = 0
                 (emergent nullification, as in V2)
          Q'_j = M_j @ T_j(lift(D)) @ M_j^{-1}
          D'_j = project(Q'_j)              (digit n_j is 0 -- emergent)
          N_j  = SHA256("V3N" || ser(D'_j) || ser(Q'_j))
                 (FULL-WIDTH: 27 + 4096-bit preimage domain in the
                  full model)
          tr(Q'_j) = tr(D's lift) + tr(lift(D) U_j^2)   (the trace law,
                  conjugation-invariant, gate-audited)
          D    = C_j                          (checkpoint restart)
      else:
          D    = base_step(D, block_i)        (fare-octal transition
                  with STATE-DEPENDENT indices -- the D7 mixer fix)
  ghost = Merkle accumulator over D_0..D_L   (the ghost disc, D5)
  cells = the 16 zeta cells (a = quaternion row, b = well) and the
          quaternion disentangling map       (the zeta array, D3+D4)
  H     = SHA256("V3H" || ghost_root || ser(disentangled) ||
                 ser(D_L) || wells_digest || e)

THE KEY IS STILL THE SEED ALONE.  D_0, the checkpoints and all four
well matrices are PRF(seed); the wells, the perspectives and e are
public constants; security = min(seed bits, 256) with SHA-256
preimage resistance as the sole assumption -- unchanged, and stated.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from ucq.conjugate import conjugate
from ucq.lift import Profile, lift, project
from voidwell3 import ghost as ghost_mod
from voidwell3 import perspectives as persp
from voidwell3 import prf, wells as wells_mod
from voidwell3 import zeta as zeta_mod

IV = b"voidwell-v3"
SER_VERSION = 3

#: the variants: the seed width is the only difference; security =
#: min(seed bits, 256) (unchanged from V2).  study-toy is the small
#: model as a CHALLENGE variant: 2^16 by design, breakable with the
#: shipped attacker's --exhaustive mode in about a minute, for study.
VARIANTS = {
    "flagship": {"seed_bytes": 32, "seed_bits": 256,
                 "claim": "min(256, 256) = 2^256"},
    "compact": {"seed_bytes": 16, "seed_bits": 128,
                "claim": "min(128, 256) = 2^128"},
    "study-toy": {"seed_bytes": 2, "seed_bits": 16,
                  "claim": "min(16, 256) = 2^16 -- breakable by "
                           "design (the study case)"},
}


class EncodingError(RuntimeError):
    pass


# -- serialization ------------------------------------------------------
def ser_state(pro: Profile, state: int) -> bytes:
    """Canonical digivector serialization: version + width byte +
    big-endian state."""
    w = (pro.n_bits + 7) // 8
    return bytes([SER_VERSION, w]) + state.to_bytes(w, "big")


def ser_nullifiers(nullifiers: list[str]) -> bytes:
    out = bytearray(bytes([SER_VERSION, len(nullifiers)]))
    for n in nullifiers:
        out += bytes.fromhex(n)
    return bytes(out)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# -- the base transition: the BIJECTION walk (D7, final form) ----------
def digit_set(pro: Profile, state: int, n: int, v: int) -> int:
    shift = pro.bits_per_digit * n
    mask = pro.digit_max << shift
    return (state & ~mask) | (v << shift)


def digit_value(pro: Profile, state: int, n: int) -> int:
    return (state >> (pro.bits_per_digit * n)) & pro.digit_max


def base_step(pro: Profile, state: int, block: int) -> tuple[int, int]:
    """One fare-octal transition.  Every operation is a BIJECTION of
    the state space, so the walk between checkpoints is a public
    permutation -- it cannot lose information, and the final state
    is an exact relabeling of the last checkpoint (the V2 mixer's
    measured degeneracy, 18.21 of 27 bits, is structurally
    impossible under this walk).

    The three operations are monograph-native:

      op 0 -- the LAMBDA-CARRY (Maiden Math, Ch. VI sec. 6.4: the
              carry operator Lambda = tau^3).  state += 1 << g,
              mod 2^n_bits.  The fare is the carry chain length
              (the number of bits the addition flipped).
      op 1 -- the TAU-ROTATE (the multinumeral base conversion,
              App. A): swap digits n and n'.  The fare is 1 when
              the bases actually differ, 0 for an identity turn.
      op 2 -- the XI-WRITE (the obfuscation pair |b| / [[b]],
              Ch. III): digit n XOR= v.  The fare is 1 when v
              obfuscates, 0 when it is a no-op.

    All indices are derived from the PUBLIC data block (the walk is
    a public permutation; the secrets enter only through the PRF
    checkpoints and well matrices, exactly as in V2).
    """
    op = block % 3
    if op == 0:                                   # lambda-carry
        g = (block >> 2) % pro.n_bits
        # the carry chain: k consecutive ones starting at bit g.
        # flipped bits = k+1 when the chain lands on a 0 inside the
        # state (k ones -> 0, the 0 -> 1); k when it runs off the
        # top (mod 2^n discards the carry); 1 when bit g is 0.
        k = 0
        while g + k < pro.n_bits and (state >> (g + k)) & 1:
            k += 1
        fare = k + 1 if (k == 0 or g + k < pro.n_bits) else k
        return (state + (1 << g)) % (1 << pro.n_bits), fare
    if op == 1:                                   # tau-rotate
        n = (block >> 2) % pro.n_digits
        n2 = (n + 1 + (block >> 5)) % pro.n_digits
        a = digit_value(pro, state, n)
        b = digit_value(pro, state, n2)
        s = digit_set(pro, state, n, b)
        return digit_set(pro, s, n2, a), (1 if a != b else 0)
    # op == 2: xi-write (obfuscation)
    n = (block >> 2) % pro.n_digits
    v = (block >> 5) & pro.digit_max
    return (state ^ (v << (pro.bits_per_digit * n))), (1 if v else 0)


def block_at(data: bytes, i: int) -> int:
    return data[(i - 1) % len(data)] if data else 0


# -- the walk result ----------------------------------------------------
@dataclass
class WalkResult:
    H: str
    ghost_root: str
    nullifiers: list[str]
    D_L: int
    D_0: int
    checkpoints: dict
    wells_detail: list[dict] = field(default_factory=list)
    zeta_cells: dict = field(default_factory=dict)
    disentangled: list = field(default_factory=list)
    values: list = field(default_factory=list)
    fares: list = field(default_factory=list)
    tree: list = field(default_factory=list)

    def open_state(self, pro: Profile, i: int):
        """Ghost-disc authentication path for state i (log-size)."""
        return ghost_mod.open_path(self.tree, i)

    def verify_state(self, pro: Profile, i: int) -> bool:
        return ghost_mod.verify_path(
            self.open_state(pro, i), i,
            ghost_mod.leaf(pro, self.values[i]),
            bytes.fromhex(self.ghost_root))


# -- the core ------------------------------------------------------------
def run_path(pro: Profile, data: bytes, seed: bytes,
             wells: list[tuple[int, int]], L: int,
             e: int = wells_mod.DEFAULT_E,
             collect: bool = False) -> WalkResult:
    """Replay the full Perspective Walk.  The same code path serves
    the encoder, the gate, the small model and the attacker."""
    wells_mod.validate(pro, wells, L)
    U = persp.units(pro)
    well_at = {m: (j + 1, n) for j, (m, n) in enumerate(wells)}

    D = prf.prf_digivector(pro, seed, b"D0")
    Cs = {}
    for m, (j, n) in well_at.items():
        scale = wells_mod.prime_scaling(pro, j, e)
        dom = b"C" + bytes([j]) + scale.to_bytes(32, "big")
        Cs[j] = prf.prf_digivector(pro, seed, dom)

    values, fares = [D], []
    wells_detail: list[dict] = []
    nullifiers: list[str] = []
    for i in range(1, L + 1):
        if i in well_at:
            j, n = well_at[i]
            scale = wells_mod.prime_scaling(pro, j, e)
            T = persp.twist(pro, j)
            Q = lift(pro, D)
            TQ = T(Q)
            try:
                M, Minv, ctr = prf.prf_well_matrix(
                    pro, seed, j, D, n, scale, twist=T)
            except RuntimeError as err:                    # pragma
                raise EncodingError(str(err))
            Qp = conjugate(TQ, M, Minv)
            Dp = project(pro, Qp)
            if digit_value(pro, Dp, n) != 0:               # pragma
                raise EncodingError(
                    f"well {j}: nullification failed (derivation bug)")
            # the trace law (conjugation-invariant): tr(Q') must
            # equal tr(Q) + tr(Q U_j^2) -- the perspective's signature
            trace_expected = persp.twist_trace_law(Q, U[j])
            trace_actual = Qp.trace()
            if trace_actual != trace_expected:             # pragma
                raise EncodingError(
                    f"well {j}: trace law failed (derivation bug)")
            # the nullifier records the FULL conversion (fact 1)
            nullifiers.append(
                sha(b"V3N" + ser_state(pro, Dp) + Qp.serialize()))
            wells_detail.append({
                "j": j, "position": i, "digit": n, "ctr": ctr,
                "scale": scale,
                "D_arriving": D, "D_prime": Dp,
                "nullifier": nullifiers[-1],
                "trace_expected": trace_expected,
                "trace_actual": trace_actual,
                "Qp": Qp, "M": M,
            })
            fares.append(digit_value(pro, D, n))
            D = Cs[j]
        else:
            D, fare = base_step(pro, D, block_at(data, i))
            fares.append(fare)
        values.append(D)

    # the ghost-disc accumulator over every state (D5)
    leaves = [ghost_mod.leaf(pro, s) for s in values]
    tree = ghost_mod.build(leaves)
    groot = ghost_mod.root(tree)

    # the zeta-array: 16 cells, disentangled, contracted (D3 + D4)
    cells = {}
    for wd in wells_detail:
        b = wd["j"] - 1
        for a in range(4):
            cells[(a, b)] = zeta_mod.cell(
                a, b, wd["nullifier"], wd["Qp"].row(a))
    disentangled = zeta_mod.disentangle(cells)

    wd_bytes = bytes.fromhex(wells_mod.digest(wells, e))
    H = hashlib.sha256(
        b"V3H" + groot + zeta_mod.serialize_cells(disentangled)
        + ser_state(pro, D) + wd_bytes
        + e.to_bytes(2, "big")).hexdigest()

    return WalkResult(
        H=H, ghost_root=groot.hex(), nullifiers=nullifiers, D_L=D,
        D_0=values[0], checkpoints={str(j): Cs[j] for j in Cs},
        wells_detail=wells_detail, zeta_cells=cells,
        disentangled=disentangled, values=values, fares=fares,
        tree=tree)


__all__ = ["IV", "SER_VERSION", "VARIANTS", "EncodingError",
           "ser_state", "ser_nullifiers", "sha", "base_step",
           "digit_set", "digit_value", "block_at", "run_path",
           "WalkResult"]
