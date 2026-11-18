"""verify_js.py -- cross-check the page's JavaScript math core in node.

Extracts the MATHCORE block and the injected SELFTEST constant from the
built html/tribit_face.html, runs runSelfTest() in node, and compares
the result with Python's own verdict.  This is the same test the page's
badge runs in the browser -- here it runs headless.

Run (from python/):  python3 verify_js.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "html" / "tribit_face.html"
SELFTEST = Path(__file__).resolve().parent / "selftest.json"

MC_START = "/*MATHCORE-START*/"
MC_END = "/*MATHCORE-END*/"


def main() -> int:
    if not HTML.exists():
        print("html/tribit_face.html not built -- run make.py first",
              file=sys.stderr)
        return 1

    html = HTML.read_text()
    if MC_START not in html or MC_END not in html:
        print("mathcore markers not found in built html", file=sys.stderr)
        return 1

    mathcore = html.split(MC_START, 1)[1].split(MC_END, 1)[0]

    m = re.search(r"^const SELFTEST = (\{.*\});$", html, re.M)
    if not m:
        print("SELFTEST constant not found in built html", file=sys.stderr)
        return 1
    selftest_line = "const SELFTEST = " + m.group(1) + ";"

    harness = (
        '"use strict";\n'
        + mathcore + "\n"
        + selftest_line + "\n"
        + "console.log(JSON.stringify(runSelfTest(SELFTEST)));\n"
    )

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        proc = subprocess.run(["node", path], capture_output=True, text=True)
    finally:
        Path(path).unlink(missing_ok=True)

    if proc.returncode != 0:
        print("node failed:", proc.stderr, file=sys.stderr)
        return 1

    result = json.loads(proc.stdout.strip())
    js_passed, js_total = result["passed"], result["total"]

    py = json.loads(SELFTEST.read_text())
    py_passed = sum(1 for c in py["checks"] if c["pass"])
    py_total = len(py["checks"])

    print(f"python core : {py_passed}/{py_total} checks")
    print(f"js mathcore : {js_passed}/{js_total} golden vectors")
    if result["failures"]:
        print("failures:")
        for f in result["failures"][:10]:
            print("  ", f["op"], "in", f["in"], "expected", f["expected"],
                  "got", f.get("actual"))
    ok = js_passed == js_total and py_passed == py_total
    print("CROSS-CHECK " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
