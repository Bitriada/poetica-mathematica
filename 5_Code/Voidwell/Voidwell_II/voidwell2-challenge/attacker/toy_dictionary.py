"""toy_dictionary.py -- the nullifier dictionary, demonstrated where
it can exist: the small model.

WHAT THIS DEMONSTRATES.  A nullifier dictionary attack needs two
things: a published nullifier to match, and a small preimage domain
to enumerate.  A Voidwell-2 challenge offers neither -- nothing
per-well is published, and the nullifiers hash the full conjugated
matrix (domain 2^4123).  Neither fact can be *shown* at full scale
-- a 2^4123 dictionary is the point -- so this tool demonstrates
the methodology at the only scale where a dictionary still exists:
the 2x2/F_7 small model, where the full-width nullifier domain is
8 x 7^4 = 19,208 = 2^14.2.

The run: build the complete dictionary over (state, matrix) pairs,
match a hypothetically published nullifier list from a small-model
challenge, and print the honest split -- feasible here, impossible
at full scale, and moot against a real challenge because nothing
per-well is published to match against.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from voidwell2.small_model.harness import toy_dictionary  # noqa: E402


def main() -> int:
    print("the toy dictionary (small model, 2x2/F_7):")
    print()
    toy = toy_dictionary(k=3)
    print(f"  full-width nullifier domain: {toy['domain']} entries "
          f"= 2^{toy['domain_log2']}")
    print(f"  dictionary build: {toy['build_seconds']} s")
    print(f"  published nullifiers matched: "
          f"{toy['recovered']}/{toy['published']}")
    print()
    print("the honest split:")
    print(f"  here (small model): the domain is 2^{toy['domain_log2']} "
          f"-- an afternoon of hashing, BY CONSTRUCTION of the toy")
    print(f"  full model: the same domain is "
          f"2^{toy['full_model_domain_log2']} (27-bit state + "
          f"4096-bit matrix) -- not a dictionary anyone builds")
    print("  and against a real V2 challenge the question is moot: "
          "no nullifiers are published (H-only), so there is "
          "nothing to match a dictionary against")
    print()
    print("the security claim of the full model rests on SHA-256 "
          "preimage resistance, stated -- never on the toy")
    with open(os.path.join(ROOT, "results", "toy_dictionary.json"),
              "w") as f:
        json.dump(toy, f, indent=1)
        f.write("\n")
    print("wrote results/toy_dictionary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
