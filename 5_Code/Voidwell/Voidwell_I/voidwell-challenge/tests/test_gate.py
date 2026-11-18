"""test_gate.py -- the six acceptance cases of spec D6.

  1. valid key                        -> PASS (exit 0)
  2. perturbed seed                   -> FAIL (exit 1)
  3. perturbed schedule               -> FAIL (exit 1)
  4. perturbed H                      -> FAIL (exit 1)
  5. perturbed nullifier              -> FAIL (exit 1)
  6. truncated key (malformed JSON)   -> MALFORMED (exit 2)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from ucq.lift import FULL                      # noqa: E402
from voidwell.encoder import encode            # noqa: E402

SEED = bytes.fromhex(
    "00112233445566778899aabbccddeeff"
    "00112233445566778899aabbccddeeff")
DATA = "00112233"


def write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def run_gate(challenge, key):
    r = subprocess.run(
        [sys.executable, "-m", "voidwell", "gate",
         "--challenge", challenge, "--key", key],
        capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="voidwell-gate-")
    results = []

    # build the reference challenge + key (k = 3, the contest case)
    challenge, key, _ = encode(FULL, bytes.fromhex(DATA), SEED, 3, 43)
    ch_path = os.path.join(tmp, "challenge.json")
    key_path = os.path.join(tmp, "key.json")
    write(ch_path, challenge)
    write(key_path, key)

    # 1. valid key
    results.append(("valid key -> 0",
                    run_gate(ch_path, key_path)[0] == 0))

    # 2. perturbed seed
    bad_seed = bytearray(SEED)
    bad_seed[0] ^= 1
    k2 = dict(key)
    k2["seed"] = bytes(bad_seed).hex()
    p2 = os.path.join(tmp, "key_seed.json")
    write(p2, k2)
    rc, _ = run_gate(ch_path, p2)
    results.append((f"perturbed seed -> 1 (got {rc})", rc == 1))

    # 3. perturbed schedule (still structurally valid)
    m, n = key["schedule"][0]
    m2 = m + 1 if m < 43 else m - 1
    k3 = dict(key)
    k3["schedule"] = [[m2, n]] + key["schedule"][1:]
    p3 = os.path.join(tmp, "key_sched.json")
    write(p3, k3)
    rc, _ = run_gate(ch_path, p3)
    results.append((f"perturbed schedule -> 1 (got {rc})", rc == 1))

    # 4. perturbed H
    c4 = json.loads(json.dumps(challenge))
    c4["H"] = ("0" if c4["H"][0] != "0" else "1") + c4["H"][1:]
    p4 = os.path.join(tmp, "challenge_H.json")
    write(p4, c4)
    rc, _ = run_gate(p4, key_path)
    results.append((f"perturbed H -> 1 (got {rc})", rc == 1))

    # 5. perturbed nullifier
    c5 = json.loads(json.dumps(challenge))
    c5["nullifiers"][0] = ("0" if c5["nullifiers"][0][0] != "0"
                           else "1") + c5["nullifiers"][0][1:]
    p5 = os.path.join(tmp, "challenge_null.json")
    write(p5, c5)
    rc, _ = run_gate(p5, key_path)
    results.append((f"perturbed nullifier -> 1 (got {rc})", rc == 1))

    # 6. truncated key (malformed)
    p6 = os.path.join(tmp, "key_trunc.json")
    with open(p6, "w") as f:
        f.write(json.dumps(key)[:40])          # cut mid-structure
    rc, _ = run_gate(ch_path, p6)
    results.append((f"truncated key -> 2 (got {rc})", rc == 2))

    print("test_gate: the six cases of spec D6")
    ok = True
    for name, passed in results:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok &= passed
    print(f"{'ALL SIX PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
