"""make.py -- build html/tribit_face.html from the template and selftest.json.

The template carries a /*__SELFTEST_JSON__*/ placeholder; this script
replaces it with `const SELFTEST = {...};` produced by verify.py, so the
delivered page re-runs Python's golden vectors through its own JavaScript
math core on load.

Run (from python/):  python3 make.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # tribit-face/
TEMPLATE = ROOT / "html" / "template.html"
OUT = ROOT / "html" / "tribit_face.html"
SELFTEST = Path(__file__).resolve().parent / "selftest.json"

PLACEHOLDER = "/*__SELFTEST_JSON__*/"


def main() -> int:
    if not TEMPLATE.exists():
        print(f"missing template: {TEMPLATE}", file=sys.stderr)
        return 1
    if not SELFTEST.exists():
        print("missing selftest.json -- run verify.py first", file=sys.stderr)
        return 1

    data = json.loads(SELFTEST.read_text())
    if not all(c["pass"] for c in data["checks"]):
        print("selftest.json contains FAILING checks -- fix verify.py first",
              file=sys.stderr)
        return 1

    injection = "const SELFTEST = " + json.dumps(data, separators=(",", ":")) + ";"
    html = TEMPLATE.read_text()
    if PLACEHOLDER not in html:
        print(f"placeholder {PLACEHOLDER} not found in template", file=sys.stderr)
        return 1
    html = html.replace(PLACEHOLDER, injection, 1)
    if PLACEHOLDER in html:
        print("placeholder appears more than once", file=sys.stderr)
        return 1

    OUT.write_text(html)
    n_vec = len(data["vectors"])
    n_chk = len(data["checks"])
    print(f"built {OUT}  ({OUT.stat().st_size} bytes, "
          f"{n_chk} checks / {n_vec} vectors embedded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
