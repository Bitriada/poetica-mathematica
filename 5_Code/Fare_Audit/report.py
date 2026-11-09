"""rtfa.report -- the Report Generator (CTS module 5, PDD section 9).

Outputs:
* the Main Audit Table (CSV, PDD section 9.1 columns);
* the Irreversibility Report (reflection audits whose round trip did
  not return the source, PDD section 9.2);
* the Saturation / Apeirogon Report (the exact step where a projection
  audit hit the Goedelian limit of the current algebra);
* the Blocked Transitions Report (level collisions the audit prevented
  -- the MBP cross-layer leak demo);
* the Compaction (GIF) Report: audits grouped by threes -- three
  sequential operations at one algebraic level compress into a single
  "macro-fare" block (PDD section 9.2; the triadic rule of the
  Generative Integer Fractal).
"""

from __future__ import annotations

import csv
from pathlib import Path

from . import registry
from .classifier import FLAG_ORDER

CSV_COLUMNS = ["ID", "Source Rep", "Source Val", "Target Rep", "Result Val",
               "Fare Code", "Abs Error", "ULP", "Overflow",
               "Level Collision", "Provenance Hash"]


def _vector_codes(fare_dict: dict) -> str:
    parts = [fare_dict["exactness"]] if fare_dict["exactness"] != "-" else []
    parts += [code for attr, code in FLAG_ORDER if fare_dict.get(attr)]
    return ",".join(parts) if parts else "-"


def _short_hash(h: str) -> str:
    return f"sha256:{h[:12]}..."


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main audit table
# ---------------------------------------------------------------------------

def audit_table_csv(ledger, path: str | Path) -> int:
    """PDD section 9.1: one row per appended ledger entry."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_COLUMNS)
        for entry in ledger.entries:
            p = entry["record_payload"]
            fare = p["fare_vector"]
            err = p["error_metrics"]
            w.writerow([
                entry["ledger_index"] + 1,
                p["source_repr"], p["source_val_exact"],
                p["target_repr"], p["target_val_computed"],
                _vector_codes(fare),
                err.get("abs", "-"), err.get("ulp", "-"),
                "Yes" if fare.get("overflow") else "No",
                "Yes" if fare.get("level_collision") else "No",
                _short_hash(entry["entry_hash"]),
            ])
    return len(ledger.entries)


# ---------------------------------------------------------------------------
# Irreversibility report
# ---------------------------------------------------------------------------

def irreversibility_report(reflections: list[dict]) -> str:
    lines = ["IRREVERSIBILITY REPORT (reflection audits)",
             "-" * 78,
             "Round trips that did not return exactly the source value.",
             ""]
    bad = [r for r in reflections if not r["equal"]]
    if not bad:
        lines.append("  (none: every round trip was exact)")
    for r in bad:
        lines.append(f"  source      {r['source_spec']}")
        lines.append(f"  path        {r['source_repr']} -> {r['via']} -> "
                     f"{r['return_to']}")
        lines.append(f"  returned    {r['returned_display']}")
        lines.append(f"  verdict     IRREVERSIBLE -- the fare paid on the "
                     f"way in cannot be refunded on the way out")
        if r.get("delta"):
            lines.append(f"  delta       {r['delta']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Saturation (Apeirogon) report
# ---------------------------------------------------------------------------

def saturation_report(attempts: list[dict]) -> str:
    lines = ["SATURATION (APEIROGON) REPORT",
             "-" * 78,
             "Steps where an audit hit the Goedelian limit of the current",
             "algebra (G6GF section 4.6: the F environment cannot simulate",
             "the continuous curve).",
             ""]
    hits = [a for a in attempts if a["result"].saturation]
    if not hits:
        lines.append("  (none)")
    for a in hits:
        r = a["result"]
        lines.append(f"  run          {a['run_id']}")
        step = a.get("seq_step", a["step"])
        lines.append(f"  step         {step}"
                     + (f" of {a['total_steps']}" if a.get("total_steps")
                        else ""))
        lines.append(f"  transition   {r.src_spec or r.src_id + ':' + r.src_display} "
                     f"--{r.op}--> {r.tgt_id}")
        lines.append(f"  drift score  {r.drift_after}")
        lines.append(f"  event        {r.saturation}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Blocked transitions (level collisions prevented)
# ---------------------------------------------------------------------------

def blocked_report(attempts: list[dict]) -> str:
    lines = ["BLOCKED TRANSITIONS (level collisions prevented)",
             "-" * 78,
             "Attempts refused by the audit: the operation's home rung",
             "sits above the operand's or target's Fare-Ladder rung, so",
             "the transition would be a cross-layer leak (MBP 9.2/9.6).",
             "No fare is ledgered -- prevention, not repair.",
             ""]
    blocked = [a for a in attempts if a["result"].blocked]
    if not blocked:
        lines.append("  (none)")
    for a in blocked:
        r = a["result"]
        lines.append(f"  {r.src_spec or r.src_id + ':' + r.src_display} "
                     f"--{r.op}"
                     + (f"({r.arg_display})" if r.arg_display else "")
                     + f"--> {r.tgt_id}    fare: {r.fare.codes()}")
        for note in r.notes:
            lines.append(f"      note: {note}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Compaction (GIF triadic) report
# ---------------------------------------------------------------------------

def compaction_report(ledger) -> str:
    """Groups audits by threes (PDD section 9.2): three sequential
    operations inside one algebraic level compress into one macro-fare
    block.  The triadic ceiling is also why the saturation limit is 3
    (no more than 3 identical operations: the GIF triadic rule)."""
    lines = ["COMPACTION (GIF) REPORT -- audits grouped by threes",
             "-" * 78, ""]
    runs: list[tuple[str, list[int]]] = []
    for entry in ledger.entries:
        p = entry["record_payload"]
        env = registry.get(p["source_repr"]).g6gf_env
        if runs and runs[-1][0] == env:
            runs[-1][1].append(entry["ledger_index"] + 1)
        else:
            runs.append((env, [entry["ledger_index"] + 1]))
    blocks = 0
    for env, ids in runs:
        if len(ids) < 3:
            continue
        for start in range(0, len(ids) - len(ids) % 3, 3):
            triad = ids[start:start + 3]
            blocks += 1
            lines.append(f"  macro-fare block {blocks}  [{env} environment]")
            lines.append(f"      audit rows {triad} compressed: three "
                         f"sequential operations at one algebraic level")
        if len(ids) % 3:
            lines.append(f"      rows {ids[-(len(ids) % 3):]} at [{env}] "
                         f"remain uncompressed (a triad is not complete)")
    if not blocks:
        lines.append("  (no complete triad in this run)")
    lines.append("")
    lines.append("  Triadic rule (GIF): no more than three identical "
                 "operations at one")
    lines.append("  level; the fourth is either annihilated by the "
                 "ledger (tau^2=0) or")
    lines.append("  saturates the environment (the Apeirogon).")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Everything at once
# ---------------------------------------------------------------------------

def generate_all(session, out_dir: str | Path) -> dict[str, str]:
    """Write every report for an audit session; returns the texts."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    texts = {}
    texts["audit_table.csv"] = ""            # written by audit_table_csv
    n = audit_table_csv(session.ledger, out / "audit_table.csv")
    texts["rows"] = str(n)
    texts["irreversibility_report.txt"] = \
        irreversibility_report(session.reflections)
    _write(out / "irreversibility_report.txt",
           texts["irreversibility_report.txt"])
    texts["saturation_report.txt"] = saturation_report(session.attempts)
    _write(out / "saturation_report.txt", texts["saturation_report.txt"])
    texts["blocked_report.txt"] = blocked_report(session.attempts)
    _write(out / "blocked_report.txt", texts["blocked_report.txt"])
    texts["compaction_report.txt"] = compaction_report(session.ledger)
    _write(out / "compaction_report.txt", texts["compaction_report.txt"])
    return texts
