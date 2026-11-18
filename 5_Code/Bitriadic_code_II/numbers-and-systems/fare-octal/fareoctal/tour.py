"""The Fare-Octal guided tour: everything in about a second.

    python demo.py          (or: fare-octal demo)
"""

from __future__ import annotations

import time


def main() -> int:
    t0 = time.time()
    from fareoctal import (FORTRESS_NOTE, FareElement, FareOctal, PRIMES,
                           UNIT, ZERO, bit_address, lattice_sums, tau)

    print("=" * 72)
    print("FARE-OCTAL -- Poetica Mathematica Appendix A, in code")
    print("=" * 72)

    # -- 1. counting -------------------------------------------------------
    print("\n[1] Counting looks like base 8 (App. A sec. 3):")
    for c, s, labels in list(__import__("fareoctal").count_table(11))[7:]:
        lab = ", ".join(f"tau_{b}" for b in labels)
        print(f"    {s.display()}  = {c:2d}   ({lab})")
    print("    ... up to [7 7 7 7 7 7 7 7 7] = 2^27 - 1 = 134,217,727")

    # -- 2. three readings --------------------------------------------------
    print("\n[2] One state, three readings (bits 1,2 = primes 3,5):")
    s = FareOctal({1, 2})
    print(f"    display  {s.display()}   (count {s.to_int()})")
    print(f"    value    {s.value()}            (= 3*5, squarefree Fare reading)")
    print(f"    h-weight 2^{s.h_exponent()}          (H cells (1,2,1) & (1,3,1): 2^6 * 2^9)")
    a = bit_address(1)
    print(f"    bit 1 lives at H-cell (i={a['cell'][0]}, j={a['cell'][1]}, "
          f"k={a['cell'][2]}), digit D{a['digit']} pos {a['digit_bit']}, "
          f"prime {a['prime']}")

    # -- 3. the Fare product -------------------------------------------------
    print("\n[3] Multiplication: merge switches if coprime, collapse on "
          "overlap:")
    for m, n in ((2, 3), (3, 5), (6, 10), (15, 77)):
        A, B = FareOctal.from_value(m), FareOctal.from_value(n)
        P = A * B
        out = "ZERO (overlap)" if P is ZERO else \
            f"{P.display()}  (value {P.value()})"
        print(f"    tau_{m} * tau_{n} = {out}")
    print(f"    the all-off state {UNIT.display()} is the UNIT "
          f"(value 1):  UNIT * tau_2 = tau_2")
    print(f"    annihilation ZERO is NOT one of the 2^27 states "
          "(finding F5)")

    # -- 4. sec. 7.2 completed ------------------------------------------------
    print("\n[4] App. A sec. 7.2, left symbolic in the monograph, "
          "completed exactly:")
    A = FareElement.from_states(tau(0), tau(1))
    B = FareElement.from_states(tau(0), tau(2))
    print(f"    A = {A!r}   (bits 0,1 = primes 2,3)")
    print(f"    B = {B!r}   (bits 0,2 = primes 2,5)")
    print(f"    A*B = {A * B!r}")
    print("    (a SUM of states -- a window Fare-algebra element, not a "
          "single state)")

    # -- 5. the 117-lattice storage convention --------------------------------
    print("\n[5] The 117-point Arithmetic Bitriada as storage convention:")
    sums = lattice_sums()
    print(f"    levels L={sums['levels']['L']}, M={sums['levels']['M']}, "
          f"H={sums['levels']['H']}  ->  {sums['total_points']} points "
          f"(axes sum {sums['per_axis_sum']}/side)")
    print("    9 digits  = the 9 H-tensor rows (k,i)   -- the L level")
    print("    27 bits   = the 27 H-tensor cells       -- the M level "
          "(the Tribit)")
    print(f"    H level (81) = the Epoch-6 Fortress {FORTRESS_NOTE['structure']}"
          " -- outside the window")
    print(f"    max state value = 2*3*5*...*103 (primorial, "
          f"{len(str(__import__('math').prod(PRIMES)))} digits); "
          f"max h-weight = 2^648")

    print("\n" + "=" * 72)
    print(f"demo complete in {time.time() - t0:.1f}s -- run "
          "'fare-octal verify' for the V1-V7 proof-by-trial dossier")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
