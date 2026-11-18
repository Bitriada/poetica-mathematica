"""The NPCS guided tour: nilpotent cryptography, demonstrably.

    npcs demo    (or: python demo.py)
"""

from __future__ import annotations

import random
import time


def main() -> int:
    t0 = time.time()
    from fareoctal import FareOctal
    from npcs import (TAU, UCQ, commit, encode, generate_path,
                      path_product, sheet_hashes, verify)
    from npcs.encode import decode_blocks
    from npcs.ucq import cq_add, cq_mul, cq_zero

    print("=" * 74)
    print("NPCS -- the Nilpotent Path-Commitment Scheme, in code")
    print("Poetica Mathematica: UC-Q algebra (Ch. VI 6.2.8) x Fare-Octal")
    print("=" * 74)

    # -- 1. the algebra -----------------------------------------------------
    print("\n[1] The UC-Q algebra: 16 real dimensions, tau^2 = 0, "
          "non-commutative:")
    Za = encode(0b101)        # block a only -- the central class
    Zb = encode(1 << 4)       # block a only as well
    Zc = encode(1 << 13)      # block c -- a generic direction
    print(f"    tau * tau == 0                      : {TAU * TAU == UCQ.uc()}")
    print(f"    two block-a chunks commute           : {Za * Zb == Zb * Za}"
          f"  (central class)")
    print(f"    generic pair commutes?               : {Zb * Zc == Zc * Zb}"
          f"  (non-commutativity)")
    print(f"    tr(Z1 Z2) = V1*D2 + D1*V2 (Leibniz)  : "
          f"{(Zb * Zc).tr() == cq_add(cq_mul(Zb.val(), Zc.tr()), cq_mul(Zb.tr(), Zc.val()))}")

    # -- 2. the encoding ----------------------------------------------------
    print("\n[2] A Fare-Octal chunk -> a UC-Q element (blocks 6/7/7/7):")
    chunk = (1 << 0) | (1 << 6) | (1 << 20)
    T = FareOctal.from_int(chunk)
    print(f"    chunk {chunk:027b}")
    print(f"      Fare-Octal display {T.display()}, value {T.value()}")
    for b in decode_blocks(chunk):
        print(f"      block {b['block']}: value {b['value']:>10}, "
              f"trace (weight, possum) = {b['trace']}")
    print(f"    encode -> {encode(chunk)!r}")

    # -- 3. the bi-sheet commitment ------------------------------------------
    print("\n[3] Commit to a path of 32 chunks (the secret key):")
    rng = random.Random(7)
    path = generate_path(32, rng)
    c = commit(path)
    Tp = path_product(path)
    h_val, h_tr = sheet_hashes(Tp)
    print(f"    H_val  = SHA-256(value sheet) = {h_val.hex()[:32]}..")
    print(f"    H_tr   = SHA-256(trace sheet) = {h_tr.hex()[:32]}..")
    print(f"    H      = SHA-256(H_val||H_tr)  = {c.H.hex()[:32]}..")
    print(f"    (published: H, H_val, H_tr, L = {c.L}; the path stays "
          f"secret)")

    # -- 4. verification and tamper-evidence -----------------------------------
    print("\n[4] Verification: the honest path passes, every tampered "
          "variant fails:")
    print(f"    honest path          : {verify(path, c)}")
    bad = list(path)
    bad[17] ^= 1 << 9
    print(f"    one flipped bit      : {verify(bad, c)}")
    print(f"    truncated path       : {verify(path[:-1], c)}")
    print(f"    reversed path        : {verify(path[::-1], c)}")

    # -- 5. the trace sheet is the transcript ------------------------------------
    print("\n[5] The trace sheet IS the path's transcript (the "
          "monograph's self-auditing):")
    small = path[:4]
    encs = [encode(x) for x in small]
    Ts = path_product(small)
    acc = cq_zero()
    for j in range(4):
        prod_l = None
        for v in [encs[k].val() for k in range(j)]:
            prod_l = v if prod_l is None else cq_mul(prod_l, v)
        prod_r = None
        for v in [encs[k].val() for k in range(j + 1, 4)]:
            prod_r = v if prod_r is None else cq_mul(prod_r, v)
        term = encs[j].tr()
        if prod_l is not None:
            term = cq_mul(prod_l, term)
        if prod_r is not None:
            term = cq_mul(term, prod_r)
        acc = cq_add(acc, term)
    print(f"    tr(T(s0 s1 s2 s3)) == ordered Leibniz transcript: "
          f"{Ts.tr() == acc}")
    print("    (each chunk's trace, wrapped in the value products of "
          "everything before and after it -- order included)")

    # -- 6. ghost disc ---------------------------------------------------------
    print("\n[6] The ghost disc tie-in (monograph: binding territory "
          "2^648):")
    maximal = FareOctal(frozenset(range(27)))
    print(f"    Fare-Octal maximal H-weight = 2^{maximal.h_exponent()} "
          f"== ghost disc territory 2^648: "
          f"{maximal.h_weight() == 2 ** 648}")

    print("\n" + "=" * 74)
    print(f"demo complete in {time.time() - t0:.1f}s -- run 'npcs "
          f"trials' for the T1-T10 proof-by-trial dossier")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
