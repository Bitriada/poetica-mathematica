"""rtfa.ledger -- the Nilpotent Fare Ledger (CTS module 4, sections 4.3/7/8).

The ledger is the core innovation of the tool.  It encodes the
nilpotent trace of the MBP Owner algebra, tau^2 = 0 (Monkey Business
Pipeline, section 6.2):

    "The constraint tau^2 = 0 is the log's unique-key rule: the same
     entry cannot appear twice.  If an identical step is attempted a
     second time, its log entry is silently dropped -- the second tau
     squares to zero, leaving the first tau untouched."

Concretely: the *same transition* (same run, same source value, same
operation, same target) logged a second time does not create a row; it
increments ``annihilation_counter`` on the original row.  The fare paid
on a transition is a structural fact -- you cannot pay the same fare
twice in the same context (PDD section 7).

Key schema note: the PDD section 7 rule defines the transition identity
as "same source value, same operation, same target rep, same run_id";
the CTS section 2.3 sketch writes the key as
sha256(run_id|source_repr|operation|target_repr) without the value.
We implement the PDD rule -- the value is part of the key -- because
without it two *different* values through the same representation pair
would wrongly annihilate.  The CTS/handoff Test 5 (the same value three
times) passes identically under both schemas.

Tamper evidence: every entry is hash-chained (entry_hash covers the
canonical payload and the previous entry's hash), so editing a past
line breaks the chain and ``verify`` reports the exact line
("Hash Mismatch at index N").
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    import orjson

    def canonical_json(obj) -> bytes:
        """Canonical bytes for hashing (sorted keys, no whitespace)."""
        return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
except ImportError:                                   # pragma: no cover
    def canonical_json(obj) -> bytes:
        return json.dumps(obj, sort_keys=True,
                          separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")

GENESIS = "genesis"


class FareLedger:
    """Append-only, hash-chained, nilpotent JSONL ledger."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.entries: list[dict] = []
        self.index: dict[str, int] = {}

    # -- key ---------------------------------------------------------------

    @staticmethod
    def transition_key(run_id: str, payload: dict) -> str:
        """sha256(run_id | source_repr | source_val | op | target_repr)."""
        raw = "|".join((run_id,
                        payload["source_repr"],
                        payload["source_val_exact"],
                        payload["operation"],
                        payload["target_repr"]))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # -- append (the tau^2 = 0 rule) ----------------------------------------

    def append(self, payload: dict) -> tuple[str, int]:
        """Returns ('appended', index) or ('annihilated', index)."""
        key = self.transition_key(self.run_id, payload)
        if key in self.index:
            idx = self.index[key]
            self.entries[idx]["annihilation_counter"] += 1
            return "annihilated", idx
        prev_hash = self.entries[-1]["entry_hash"] if self.entries \
            else GENESIS
        payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()
        entry_hash = hashlib.sha256(
            f"{prev_hash}|{payload_hash}".encode("utf-8")).hexdigest()
        entry = {
            "ledger_index": len(self.entries),
            "run_id": self.run_id,
            "transition_key": key,
            "record_payload": payload,
            "prev_hash": prev_hash,
            "payload_hash": payload_hash,
            "entry_hash": entry_hash,
            "status": "appended",
            "annihilation_counter": 0,
        }
        self.entries.append(entry)
        self.index[key] = len(self.entries) - 1
        return "appended", len(self.entries) - 1

    # -- export / stats ------------------------------------------------------

    def export(self, path: str | Path) -> int:
        """Write the ledger as JSONL; returns the number of lines."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for entry in self.entries:
                fh.write(json.dumps(entry, sort_keys=True,
                                    ensure_ascii=False) + "\n")
        return len(self.entries)

    def stats(self) -> dict:
        return {
            "run_id": self.run_id,
            "entries": len(self.entries),
            "annihilations": sum(e["annihilation_counter"]
                                 for e in self.entries),
            "head_hash": self.entries[-1]["entry_hash"]
            if self.entries else GENESIS,
        }


# ---------------------------------------------------------------------------
# Verification (CTS Test 6: tamper with a line -> "Hash Mismatch at index N")
# ---------------------------------------------------------------------------

def verify(path: str | Path) -> tuple[list[str], dict]:
    """Re-verify an exported ledger.

    Returns (issues, stats).  issues is empty iff the chain is intact,
    every transition key matches its payload, and no key is duplicated
    (nilpotence consistency).  Line numbers in the messages are 1-based
    (the CTS golden wording: "Hash Mismatch at index 3" for line 3).
    """
    issues: list[str] = []
    entries = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                issues.append(f"Malformed JSON at index {lineno}")
    seen_keys: dict[str, int] = {}
    prev_hash = GENESIS
    for i, entry in enumerate(entries, start=1):
        payload = entry.get("record_payload", {})
        payload_hash = hashlib.sha256(
            canonical_json(payload)).hexdigest()
        # self-consistency of the entry (against its own stored prev_hash)
        entry_hash = hashlib.sha256(
            (entry.get("prev_hash", GENESIS) + "|" + payload_hash)
            .encode("utf-8")).hexdigest()
        if payload_hash != entry.get("payload_hash") \
                or entry_hash != entry.get("entry_hash"):
            issues.append(f"Hash Mismatch at index {i}")
            prev_hash = entry.get("entry_hash", prev_hash)
            continue
        # linkage to the verified predecessor
        if entry.get("prev_hash") != prev_hash:
            issues.append(f"Chain break at index {i}: prev_hash does not "
                          "link to the verified predecessor")
        key = FareLedger.transition_key(entry.get("run_id", ""), payload)
        if key != entry.get("transition_key"):
            issues.append(f"Transition-key mismatch at index {i}")
        if entry.get("ledger_index") != i - 1:
            issues.append(f"Ledger index mismatch at index {i}")
        if key in seen_keys:
            issues.append(f"Nilpotence violation at index {i}: duplicate "
                          f"transition key, first seen at index "
                          f"{seen_keys[key]}")
        seen_keys[key] = i
        prev_hash = entry["entry_hash"]
    stats = {"entries": len(entries),
             "head_hash": entries[-1]["entry_hash"] if entries else GENESIS}
    return issues, stats
