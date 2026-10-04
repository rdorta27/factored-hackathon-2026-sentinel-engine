#!/usr/bin/env python3
"""Call-center aggregates for the ROI projection (docs/build/roi.md).

Computes the human side of the break-even from the call-center tables: calls,
mean handle time (with the count of missing durations), first-contact
resolution and escalation share for the transactional reason, plus the
complaint calls as an upper bound. Writes aggregates only to a new write-once
folder under ``evidence/roi/<run-id>/``; no row, identifier or text is ever
written.

Source switch (design §5): reads ``silver_call_center_interactions`` when it
has ``duration_seconds``, else ``bronze_call_center_interactions``, and
records which one was used. The DuckDB file location is read from the
environment (``SENTINEL_CALLCENTER_DB``, see ``.env.example``); nothing about
the data location is committed.

Usage::

    python3 scripts/roi_aggregates.py <run-id>          # freeze the aggregates
    python3 scripts/roi_aggregates.py --verify <run-id>  # recompute and compare
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "evidence" / "roi"
DEFAULT_DB = ROOT / "sentinel-data-engine" / "data" / "gold_bank.duckdb"
DB_ENV = "SENTINEL_CALLCENTER_DB"
TRANSACTIONAL_REASON = "Transaccional"
COMPLAINT_REASON = "Queja"


def _has_duration(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    rows = con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]
    ).fetchall()
    return "duration_seconds" in {row[0] for row in rows}


def pick_source(con: duckdb.DuckDBPyConnection) -> dict:
    """Silver when it kept the durations, else Bronze (design §5)."""
    if _has_duration(con, "silver_call_center_interactions"):
        return {
            "table": "silver_call_center_interactions",
            "layer": "silver",
            "reason": "silver kept duration_seconds",
        }
    return {
        "table": "bronze_call_center_interactions",
        "layer": "bronze",
        "reason": "silver drops duration_seconds, bronze has it",
    }


def _reason_block(con: duckdb.DuckDBPyConnection, table: str, reason: str) -> dict:
    """Aggregates for one contact reason: counts, handle time, resolution, escalation."""
    total, with_duration, mean_seconds, resolved, escalated = con.execute(
        f"""
        SELECT COUNT(*),
               SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END),
               AVG(duration_seconds),
               SUM(CASE WHEN was_resolved THEN 1 ELSE 0 END),
               SUM(CASE WHEN was_escalated THEN 1 ELSE 0 END)
        FROM {table}
        WHERE contact_reason = ?
        """,
        [reason],
    ).fetchone()
    missing = total - (with_duration or 0)
    return {
        "n": total,
        "handle_time": {
            "n_with_duration": with_duration,
            "missing_duration": missing,
            "mean_minutes": round(mean_seconds / 60.0, 3) if with_duration else None,
            "origin": "derived",
        },
        "first_contact_resolution": {
            "n": total,
            "resolved": resolved,
            "share": round(resolved / total, 4) if total else None,
            "origin": "derived",
            "field": "was_resolved",
        },
        "escalation": {
            "n": total,
            "escalated": escalated,
            "share": round(escalated / total, 4) if total else None,
            "origin": "derived",
            "field": "was_escalated",
        },
    }


def summarize(db_path: Path | str) -> dict:
    """Aggregate the call-center tables; every block carries its n and origin."""
    path = Path(db_path)
    if not path.is_file():
        raise SystemExit(f"call-center database not found at {path}; set {DB_ENV}")
    con = duckdb.connect(str(path), read_only=True)
    # The Bronze views glob a relative data/raw path; resolve it next to the DB.
    con.execute(f"SET file_search_path='{path.parent.parent}'")
    source = pick_source(con)
    table = source["table"]
    total_calls, missing_all, first, last = con.execute(
        f"""
        SELECT COUNT(*),
               SUM(CASE WHEN duration_seconds IS NULL THEN 1 ELSE 0 END),
               MIN(interaction_date), MAX(interaction_date)
        FROM {table}
        """
    ).fetchone()
    transactional = _reason_block(con, table, TRANSACTIONAL_REASON)
    summary = {
        "kind": "callcenter_aggregates",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {**source, "origin": "measured", "field": "contact_reason"},
        "window": {"first": str(first), "last": str(last)},
        "total_calls": {
            "n": total_calls,
            "missing_duration": missing_all,
            "origin": "measured",
        },
        "transactional_calls": {
            "n": transactional["n"],
            "share_of_calls": round(transactional["n"] / total_calls, 4) if total_calls else None,
            "origin": "measured",
            "field": "contact_reason",
        },
        "transactional": transactional,
        "complaint_calls": _reason_block(con, table, COMPLAINT_REASON),
        "notes": [
            "The data does not separate dispute calls from other transactional calls: "
            "Transaccional is a superset of disputes, so the projection bounds them.",
            "Mean handle time is over calls with a duration; the calls without one "
            "are counted beside it, not imputed.",
            "The advisor-hour cost is assumed, not from any dataset; the projection "
            "labels it assumed and cites no dataset.",
            "Aggregates only: no row, identifier or text is written.",
        ],
    }
    con.close()
    return summary


def render_report(summary: dict) -> str:
    transactional = summary["transactional"]
    handle = transactional["handle_time"]
    fcr = transactional["first_contact_resolution"]
    escalation = transactional["escalation"]
    complaint = summary["complaint_calls"]
    complaint_handle = complaint["handle_time"]
    complaint_fcr = complaint["first_contact_resolution"]
    lines = [
        f"# Call-center aggregates {summary.get('run_id') or summary['kind']}",
        "",
        f"Source: {summary['source']['table']} ({summary['source']['reason']}), "
        f"{summary['window']['first']} to {summary['window']['last']}, "
        f"n={summary['total_calls']['n']} calls "
        f"({summary['total_calls']['missing_duration']} without duration).",
        "",
        f"- Transaccional (transactional) calls: {summary['transactional_calls']['n']} "
        f"({summary['transactional_calls']['share_of_calls']} of all calls), "
        f"origin {summary['transactional_calls']['origin']}.",
        f"- Mean handle time: {handle['mean_minutes']} minutes over {handle['n_with_duration']} "
        f"calls with a duration; {handle['missing_duration']} without one (origin {handle['origin']}).",
        f"- First-contact resolution: {fcr['resolved']}/{fcr['n']} = {fcr['share']} "
        f"(origin {fcr['origin']}, field {fcr['field']}).",
        f"- Escalation share: {escalation['escalated']}/{escalation['n']} = {escalation['share']} "
        f"(origin {escalation['origin']}, field {escalation['field']}).",
        f"- Bound: Queja (complaint) calls handle time {complaint_handle['mean_minutes']} minutes, "
        f"first-contact resolution {complaint_fcr['share']} (n={complaint['n']}).",
        "",
        "## Notes",
    ]
    lines += [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def freeze(run_id: str, summary: dict) -> Path:
    folder = EVIDENCE_DIR / run_id
    if folder.exists():
        raise SystemExit(f"refusing to overwrite committed run {folder}; use a new run id")
    summary = {"run_id": run_id, **summary}
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (folder / "report.md").write_text(render_report(summary), encoding="utf-8")
    return folder


def verify(run_id: str, db_path: Path | str) -> bool:
    frozen_path = EVIDENCE_DIR / run_id / "summary.json"
    if not frozen_path.is_file():
        raise SystemExit(f"no frozen run {frozen_path}")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    fresh = {"run_id": run_id, **summarize(db_path)}
    for body in (frozen, fresh):
        body.pop("created_at", None)
    return frozen == fresh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze call-center aggregates for the ROI projection.")
    parser.add_argument("run_id")
    parser.add_argument("--verify", action="store_true", help="recompute from the data and compare")
    args = parser.parse_args(argv)
    db_path = Path(os.environ.get(DB_ENV) or DEFAULT_DB)
    if args.verify:
        same = verify(args.run_id, db_path)
        print(f"[verify] {args.run_id}: {'matches' if same else 'DIFFERS from'} the frozen summary")
        return 0 if same else 1
    summary = summarize(db_path)
    folder = freeze(args.run_id, summary)
    print(f"[roi] froze {folder} ({summary['source']['table']}, n={summary['total_calls']['n']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
