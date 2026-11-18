"""toy_dictionary.py -- what a wider surface would concede,
demonstrated on the small model.

The Voidwell-2 toy dictionary enumerated all nullifier preimages of
the F_7 model (19,208 entries, 0.1 s) and inverted 3/3 published
nullifiers.  The V3 toy (F_257) preimage domain per well is
8 states x |GL(2,257)| orbits -- far larger, so the dictionary is
built the honest way instead: replay all 2^16 seeds once and index
their nullifiers.  Any challenge that published a nullifier would
then surrender the seed for free.  This is why the construction
publishes H only, and why the gate REJECTS over-publication as
malformed.
"""
from __future__ import annotations

import sys
import time

from ucq.lift import TOY
from voidwell3 import wells as wells_mod
from voidwell3.encoder import run_path

DATA = bytes.fromhex("00112233")
L = wells_mod.L_TOY


def main() -> int:
    wells = wells_mod.wells_for(TOY, L, 4)
    ref = run_path(TOY, DATA, b"\x34\x21", wells, L)
    print("toy dictionary: indexing all 65,536 toy seeds...")
    t0 = time.perf_counter()
    table = {}
    for i in range(1 << 16):
        r = run_path(TOY, DATA, i.to_bytes(2, "big"), wells, L)
        for n in r.nullifiers:
            table[n] = i
    dt = time.perf_counter() - t0
    print(f"  built {len(table)} nullifier entries in {dt:.1f}s")
    hits = 0
    for j, n in enumerate(ref.nullifiers, 1):
        t1 = time.perf_counter()
        seed = table.get(n)
        dt1 = time.perf_counter() - t1
        if seed is not None:
            hits += 1
        print(f"  published nullifier {j}: "
              f"{'seed ' + hex(seed) if seed is not None else 'no hit'}"
              f" (lookup {dt1 * 1e6:.0f} us)")
    print(f"dictionary inverts {hits}/{len(ref.nullifiers)} "
          "published nullifiers instantly -- H-only publication is "
          "why this table cannot be aimed at a real challenge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
