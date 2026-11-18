"""surface_audit.py -- the published-surface audit (design study,
section 9): every value a challenge publishes is either a public
parameter or a 256-bit hash of full-width material, and no
per-well values are present.

This is the pre-shipment check that keeps the publication minimal
by construction rather than by intention.  Run it against every
challenge before it is issued:

    python3 attacker/surface_audit.py contests/flagship/challenge.json \
        contests/compact/challenge.json
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from voidwell2.gate import ALLOWED_CHALLENGE_FIELDS, \
    FORBIDDEN_CHALLENGE_FIELDS  # noqa: E402

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def audit(path: str) -> tuple[bool, list[str]]:
    with open(path) as f:
        ch = json.load(f)
    problems = []
    fields = set(ch)
    if fields != ALLOWED_CHALLENGE_FIELDS:
        extra = fields - ALLOWED_CHALLENGE_FIELDS
        missing = ALLOWED_CHALLENGE_FIELDS - fields
        if extra:
            problems.append(f"unexpected fields: {sorted(extra)}")
        if missing:
            problems.append(f"missing fields: {sorted(missing)}")
    leaks = fields & FORBIDDEN_CHALLENGE_FIELDS
    if leaks:
        problems.append(f"per-well leak fields present: {sorted(leaks)}")
    for f in ("H", "data_commitment"):
        v = ch.get(f)
        if not isinstance(v, str) or not HEX64.match(v):
            problems.append(f"{f} is not a 64-hex SHA-256 digest")
    p = ch.get("params", {})
    if p.get("variant") not in ("flagship", "compact"):
        problems.append("params.variant invalid")
    if p.get("seed_bits") not in (128, 256):
        problems.append("params.seed_bits invalid")
    if p.get("wells") != [[3, 3], [14, 1], [15, 4]]:
        problems.append("params.wells are not the public "
                        "pi-skeleton constants")
    if p.get("L") != 43 or p.get("k") != 3:
        problems.append("params.L/k are not the spec constants")
    if ch.get("nullifier_count") != 3:
        problems.append("nullifier_count != 3")
    return (not problems), problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    all_ok = True
    for path in sys.argv[1:]:
        ok, problems = audit(path)
        print(f"{'PASS' if ok else 'FAIL'}  {path}")
        for pr in problems:
            print(f"       - {pr}")
        all_ok = all_ok and ok
    print()
    print("the audit: published = H + public params; every hash is "
          "full-width; no per-well values.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
