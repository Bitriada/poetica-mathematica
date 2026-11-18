"""surface_audit.py -- verify the challenge publishes nothing it
should not (the gate's surface rules, standalone)."""
from __future__ import annotations

import json
import sys

from voidwell3.gate import (ALLOWED_CHALLENGE_FIELDS,
                            FORBIDDEN_CHALLENGE_FIELDS)


def main(challenge_path: str) -> int:
    with open(challenge_path) as f:
        ch = json.load(f)
    extra = set(ch) - ALLOWED_CHALLENGE_FIELDS
    leaks = extra & FORBIDDEN_CHALLENGE_FIELDS
    print("surface audit:", challenge_path)
    print("  published fields:", sorted(ch))
    print("  permitted fields:", sorted(ALLOWED_CHALLENGE_FIELDS))
    if leaks:
        print("  LEAKS (per-well values published):",
              sorted(leaks))
        print("SURFACE: FAIL")
        return 1
    if extra:
        print("  unknown fields:", sorted(extra))
        print("SURFACE: FAIL")
        return 1
    print("  per-well leak fields checked:",
          sorted(FORBIDDEN_CHALLENGE_FIELDS))
    print("SURFACE: PASS (H and public parameters only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
