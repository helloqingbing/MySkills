#!/usr/bin/env python3
"""Record an auditable gate decision and advance one launch only after proof."""
import argparse
import csv
import fcntl
import hashlib
import importlib.util
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

GATES = [f"G{i}" for i in range(13)]
LIFECYCLE = ("raw_data", "live_data_synced", "normalized", "scored", "risk_screened",
             "sourcing_qc_ready", "commercially_validated", "launch_gate_reviewed",
             "product_requirements_ready", "listing_ready", "seller_central_ready",
             "fba_ready", "ads_ready", "performance_reviewed")


def artifact_row(path, workspace, launch_id, sku, gate, owner):
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise ValueError(f"evidence file does not exist: {path}")
    with resolved.open("rb") as f:
        checksum = hashlib.file_digest(f, "sha256").hexdigest()
    row_count = ""
    if resolved.suffix.lower() == ".csv":
        with resolved.open(newline="", encoding="utf-8-sig") as f:
            row_count = sum(1 for _ in csv.DictReader(f))
        if row_count == 0:
            raise ValueError(f"evidence CSV has no rows: {path}")
    return {"launch_id": launch_id, "sku": sku, "gate": gate,
            "artifact_path": os.path.relpath(resolved, workspace), "artifact_type": resolved.suffix.lower().lstrip("."),
            "source_file": str(resolved), "date_range": "", "generated_at": datetime.now(timezone.utc).isoformat(),
            "row_count": row_count, "checksum": checksum, "owner": owner,
            "freshness": "unknown", "blocking_gap": ""}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def replace_csv(path, rows):
    with open(path, newline="", encoding="utf-8") as f:
        fields = csv.DictReader(f).fieldnames
    if not fields:
        raise ValueError(f"invalid manifest header: {path}")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def verify_launch_gate(sku, decision_file, evidence_files):
    """Recompute the G6 decision from its source inputs, not a caller-authored CSV."""
    by_name = {Path(path).name: path for path in evidence_files}
    if len(by_name) != len(evidence_files) or not {"evidence_matrix.csv", "landed_cost_model.csv"} <= set(by_name):
        raise ValueError("G6 requires evidence_matrix.csv and landed_cost_model.csv")
    source = Path(__file__).resolve().parents[2] / "amazon-jp-launch-gate" / "scripts" / "evaluate_launch_gate.py"
    spec = importlib.util.spec_from_file_location("amazon_jp_launch_gate", source)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    result = validator.evaluate_all(read_csv(by_name["evidence_matrix.csv"]),
                                    read_csv(by_name["landed_cost_model.csv"]), 35,
                                    Path(by_name["evidence_matrix.csv"]).resolve().parent)
    matching = [row for row in result if row["sku"] == sku]
    if len(matching) != 1 or matching[0]["decision"] != "pass":
        raise ValueError("G6 validator did not pass for this SKU")
    decisions = [row for row in read_csv(decision_file) if row.get("sku") == sku]
    if len(decisions) != 1 or decisions[0].get("decision") != matching[0]["decision"]:
        raise ValueError("G6 decision CSV differs from the recalculated result")


def record(workspace, launch_id, sku, gate, decision, owner, approver="", reason="",
           next_action="", due_date="", evidence_files=(), decision_file=""):
    workspace = Path(workspace).resolve()
    with (workspace / ".workflow.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _record_locked(workspace, launch_id, sku, gate, decision, owner, approver,
                              reason, next_action, due_date, evidence_files, decision_file)


def _record_locked(workspace, launch_id, sku, gate, decision, owner, approver="", reason="",
                   next_action="", due_date="", evidence_files=(), decision_file=""):
    workspace = Path(workspace).resolve()
    state_path = workspace / "workflow_state.json"
    with state_path.open(encoding="utf-8") as f:
        state = json.load(f)
    if gate not in GATES or decision not in {"pass", "needs_proof", "blocked"}:
        raise ValueError("invalid gate or decision")
    if not launch_id or not sku or not owner:
        raise ValueError("launch_id, sku and owner are required")
    if decision == "pass" and (not approver or not decision_file or not evidence_files):
        raise ValueError("pass requires approver, a decision CSV and separate evidence files")
    if decision != "pass" and not reason:
        raise ValueError("non-pass decision requires a reason")
    current = state["launches"].get(launch_id)
    if current and current["lifecycle_state"] == "complete":
        raise ValueError("launch is already complete")
    if current and current["sku"] != sku:
        raise ValueError("launch_id already belongs to another SKU")
    expected = current["current_gate"] if current else "G0"
    if gate != expected:
        raise ValueError(f"expected {expected}, got {gate}; skipping or rewriting a passed gate is forbidden")
    if decision_file and any(Path(path).resolve() == Path(decision_file).resolve() for path in evidence_files):
        raise ValueError("decision CSV cannot be its own evidence file")
    if decision == "pass":
        with open(decision_file, newline="", encoding="utf-8-sig") as f:
            matching = [row for row in csv.DictReader(f) if row.get("sku") == sku and
                        row.get("decision") == "pass" and row.get("gate", gate) == gate]
        if len(matching) != 1:
            raise ValueError("decision CSV must contain exactly one pass row for this SKU and gate")
        if gate == "G6":
            verify_launch_gate(sku, decision_file, evidence_files)
    proof_paths = list(evidence_files) + ([decision_file] if decision_file else [])
    artifacts = [artifact_row(path, workspace, launch_id, sku, gate, owner) for path in proof_paths]
    now = datetime.now(timezone.utc).isoformat()
    row = {"run_id": str(uuid.uuid4()), "launch_id": launch_id, "sku": sku, "gate": gate,
           "decision": decision, "reason": reason, "owner": owner, "approver": approver,
           "decision_at": now, "next_action": next_action, "due_date": due_date}
    next_gate = GATES[GATES.index(gate) + 1] if decision == "pass" and gate != "G12" else gate
    state["launches"][launch_id] = {
        "sku": sku, "lifecycle_state": "complete" if decision == "pass" and gate == "G12" else
        LIFECYCLE[GATES.index(gate) + 1] if decision == "pass" else LIFECYCLE[GATES.index(gate)],
        "current_gate": next_gate, "last_gate": gate, "last_decision": decision,
        "blocking_issues": [] if decision == "pass" else [reason],
        "next_action": next_action, "updated_at": now,
    }
    if "gate_decisions" not in state:
        state["gate_decisions"] = read_csv(workspace / "gate_decisions.csv")
    if "artifact_manifest" not in state:
        state["artifact_manifest"] = read_csv(workspace / "artifact_manifest.csv")
    state["gate_decisions"].append(row)
    state["artifact_manifest"].extend(artifacts)
    temporary = state_path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    temporary.replace(state_path)
    # The JSON commit is authoritative. If a CSV write fails, the next call repairs it.
    replace_csv(workspace / "gate_decisions.csv", state["gate_decisions"])
    replace_csv(workspace / "artifact_manifest.csv", state["artifact_manifest"])
    return state["launches"][launch_id]


def main():
    parser = argparse.ArgumentParser()
    for name in ("workspace", "launch-id", "sku", "gate", "decision", "owner"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--approver", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--due-date", default="")
    parser.add_argument("--evidence-file", action="append", default=[])
    parser.add_argument("--decision-file", default="")
    args = parser.parse_args()
    try:
        result = record(args.workspace, args.launch_id, args.sku, args.gate, args.decision,
                        args.owner, args.approver, args.reason, args.next_action, args.due_date,
                        args.evidence_file, args.decision_file)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
