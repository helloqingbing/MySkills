"""Regression tests for decisions that can release a launch or increase spend."""
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


gate = module("gate", "skills/amazon-jp-launch-gate/scripts/evaluate_launch_gate.py")
performance = module("performance", "skills/amazon-jp-performance-reviewer/scripts/review_performance.py")
fba = module("fba", "skills/amazon-jp-fba-shipment-planner/scripts/plan_fba_shipment.py")
seller = module("seller", "skills/amazon-jp-seller-central-ops/scripts/build_seller_central_checklist.py")
workspace = module("workspace", "skills/amazon-jp-sop-orchestrator/scripts/create_launch_workspace.py")
record_gate = module("record_gate", "skills/amazon-jp-sop-orchestrator/scripts/record_gate.py")
live = module("live", "skills/amazon-jp-live-data-sync/scripts/normalize_live_reports.py")
ads = module("ads", "skills/amazon-ads-planner/scripts/plan_amazon_ads.py")


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class GateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.proof = Path(folder.name) / "proof.pdf"
        self.proof.write_bytes(b"source evidence")
        self.cost = {"sku": "A", "candidate_id": "C", "selling_price_jpy": "100",
                     "unit_cost_jpy": "20", "international_freight_jpy": "5",
                     "duty_tax_jpy": "5", "fba_fee_jpy": "10", "referral_fee_jpy": "10"}
        self.evidence = [{"sku": "A", "control_ref": ref, "status": "pass", "owner": "owner",
                          "evidence": str(self.proof), "evidence_source": "Seller Central",
                          "evidence_date": date.today().isoformat()} for ref in gate.REQUIRED_CONTROLS]

    def test_empty_and_incomplete_evidence_never_pass(self):
        self.assertEqual(gate.evaluate_all([], [self.cost], 35)[0]["decision"], "needs_proof")
        self.assertEqual(gate.evaluate_all(self.evidence[:1], [self.cost], 35)[0]["decision"], "needs_proof")

    def test_full_evidence_and_sku_isolation(self):
        other = {**self.evidence[0], "sku": "B", "status": "blocked"}
        results = gate.evaluate_all(self.evidence + [other], [self.cost], 35)
        self.assertEqual({row["sku"]: row["decision"] for row in results},
                         {"A": "pass", "B": "blocked"})

    def test_confirmation_and_negative_cost_fail(self):
        self.evidence[0]["evidence"] = "user confirmation"
        self.assertEqual(gate.evaluate_all(self.evidence, [self.cost], 35)[0]["decision"], "needs_proof")
        self.cost["unit_cost_jpy"] = "-20"
        self.assertEqual(gate.evaluate_all(self.evidence, [self.cost], 35)[0]["decision"], "blocked")

    def test_unfetched_url_does_not_pass(self):
        self.evidence[0]["evidence"] = "https://example.com/proof.pdf"
        self.assertEqual(gate.evaluate_all(self.evidence, [self.cost], 35)[0]["decision"], "needs_proof")

    def test_duplicate_blocked_control_stays_blocked(self):
        duplicate = {**self.evidence[0], "status": "blocked", "blocking_reason": "restricted"}
        self.assertEqual(gate.evaluate_all(self.evidence + [duplicate], [self.cost], 35)[0]["decision"], "blocked")


class PerformanceTests(unittest.TestCase):
    def test_blank_week_needs_proof(self):
        actions = performance.review_metric_row({"sku": "A"})
        self.assertEqual(performance.final_decision(actions), "needs_proof")

    def test_complete_recent_week_can_scale(self):
        row = {"sku": "A", "week_start": (date.today() - timedelta(days=7)).isoformat(),
               "sessions": "100", "orders": "10", "sales_jpy": "10000", "ad_spend_jpy": "1000",
               "acos_pct": "10", "tacos_pct": "10", "break_even_acos_pct": "25",
               "unit_session_pct": "10", "rating": "4.5", "returns": "0", "days_of_supply": "40"}
        self.assertEqual(performance.final_decision(performance.review_metric_row(row)), "scale")
        row["week_start"] = (date.today() - timedelta(days=40)).isoformat()
        self.assertEqual(performance.final_decision(performance.review_metric_row(row)), "needs_proof")
        row["week_start"] = (date.today() - timedelta(days=7)).isoformat()
        row["returns"] = "-1"
        self.assertEqual(performance.final_decision(performance.review_metric_row(row)), "needs_proof")

    def test_missing_acos_never_promotes(self):
        self.assertFalse(performance.search_term_actions([{"sku": "A", "search_term": "x",
                                                           "orders": "2", "sales_jpy": "1000"}]))

    def test_manifest_requires_all_fresh_reports(self):
        self.assertTrue(performance.manifest_issues([], 14))
        with tempfile.TemporaryDirectory() as folder:
            artifact = Path(folder) / "report.csv"
            artifact.write_text("sku\nA\n", encoding="utf-8")
            rows = [{"report_name": name, "period_start": date.today().isoformat(),
                     "period_end": date.today().isoformat(), "exported_at": date.today().isoformat() + "T12:00:00",
                     "freshness": "fresh", "blocking_gap": "", "rows": "1",
                     "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                     "normalized_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                     "source_file": str(artifact), "normalized_file": str(artifact), "sku_scope": "A"}
                    for name in ("business_metrics", "ads_search_terms", "inventory", "returns", "reviews")]
            self.assertEqual(performance.manifest_issues(rows, 14, sku="A"), [])
            self.assertTrue(performance.manifest_issues(rows, 14, sku="B"))
            rows[0]["sha256"] = "a" * 64
            self.assertTrue(performance.manifest_issues(rows, 14, sku="A"))
            rows[0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            rows[0]["period_end"] = (date.today() - timedelta(days=30)).isoformat()
            self.assertTrue(performance.manifest_issues(rows, 14))

    def test_ads_feedback_uses_matching_sku_and_calculated_acos(self):
        products = [{"sku": "A", "gross_profit_jpy": 100, "target_acos": 0.2},
                    {"sku": "B", "gross_profit_jpy": 100, "target_acos": 0.5}]
        report = [{"sku": "B", "search_term": "収納", "spend_jpy": "40",
                   "orders": "2", "sales_jpy": "100"}]
        self.assertEqual(ads.build_feedback(products, report)[0]["action"], "promote_exact")
        report[0]["sku"] = "A"
        self.assertNotEqual(ads.build_feedback(products, report)[0]["action"], "promote_exact")
        report[0]["sales_jpy"] = "0"
        self.assertNotEqual(ads.build_feedback(products, report)[0]["action"], "promote_exact")


class OperationsTests(unittest.TestCase):
    def test_ads_budget_never_exceeds_sku_cap(self):
        product = {"sku": "A", "asin": "A", "price_jpy": 1000, "gross_profit_jpy": 300,
                   "target_acos": 0.2, "daily_budget_jpy": 500}
        keyword = {"keyword": "storage", "relevance": 1, "ads_match_type": "", "risk": "", "cvr_pct": 10}
        for budget in (300, 500, 600, 1999, 2000, 3000):
            product["daily_budget_jpy"] = budget
            rows, _ = ads.plan_for_product(product, [keyword], [])
            by_campaign = {row["campaign_name"]: row["daily_budget_jpy"] for row in rows}
            self.assertLessEqual(sum(by_campaign.values()), budget)
            self.assertTrue(all(value >= 300 for value in by_campaign.values()))
        campaigns, targets = ads.campaign_and_target_rows(rows)
        self.assertEqual(len(campaigns), len({row["campaign_name"] for row in targets}))
        self.assertTrue(all("daily_budget_jpy" not in row for row in targets))

    def test_zero_event_reports_require_explicit_sku_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "returns.csv"
            write_csv(source, ["SKU", "Return Date", "Quantity"], [])
            output = root / "out"
            command = [sys.executable, str(ROOT / "skills/amazon-jp-live-data-sync/scripts/normalize_live_reports.py"),
                       "--returns", str(source), "--period-start", date.today().isoformat(),
                       "--report-end", date.today().isoformat(),
                       "--exported-at", date.today().isoformat() + "T12:00:00", "--output-dir", str(output)]
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            subprocess.run([*command, "--sku-scope", "A"], check=True, capture_output=True)
            with open(output / "report_manifest.csv", encoding="utf-8") as f:
                row = next(csv.DictReader(f))
            self.assertEqual((row["rows"], row["sku_scope"]), ("0", "A"))
            self.assertFalse(any("unverified report returns" in issue for issue in
                                 performance.manifest_issues([row], 14, sku="A")))

    def test_business_report_cannot_claim_missing_sku(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "business.csv"
            write_csv(source, ["SKU", "Sessions", "Units Ordered", "Sales"],
                      [{"SKU": "A", "Sessions": "10", "Units Ordered": "1", "Sales": "100"}])
            with self.assertRaises(ValueError):
                live.normalize_file("business_metrics", source, folder, [], {"A", "B"})

    def test_state_commit_recovers_csv_after_write_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-sop-orchestrator/scripts/create_launch_workspace.py"),
                            "--output-dir", folder], check=True, capture_output=True)
            proof = Path(folder) / "proof.txt"
            proof.write_text("evidence", encoding="utf-8")
            decisions = []
            for name in ("G0", "G1"):
                path = Path(folder) / f"{name}.csv"
                write_csv(path, ["sku", "gate", "decision"], [{"sku": "A", "gate": name, "decision": "pass"}])
                decisions.append(path)
            with patch.object(record_gate, "replace_csv", side_effect=OSError("simulated write failure")):
                with self.assertRaises(OSError):
                    record_gate.record(folder, "L1", "A", "G0", "pass", "owner", "approver",
                                       evidence_files=[str(proof)], decision_file=str(decisions[0]))
            record_gate.record(folder, "L1", "A", "G1", "pass", "owner", "approver",
                               evidence_files=[str(proof)], decision_file=str(decisions[1]))
            with open(Path(folder) / "gate_decisions.csv", encoding="utf-8") as f:
                self.assertEqual([row["gate"] for row in csv.DictReader(f)], ["G0", "G1"])

    def test_g6_rejects_fabricated_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-sop-orchestrator/scripts/create_launch_workspace.py"),
                            "--output-dir", folder], check=True, capture_output=True)
            proof = Path(folder) / "anything.txt"
            proof.write_text("unrelated", encoding="utf-8")
            for index in range(6):
                gate_name = f"G{index}"
                decision_path = Path(folder) / f"{gate_name}.csv"
                write_csv(decision_path, ["sku", "gate", "decision"],
                          [{"sku": "A", "gate": gate_name, "decision": "pass"}])
                record_gate.record(folder, "L1", "A", gate_name, "pass", "owner", "approver",
                                   evidence_files=[str(proof)], decision_file=str(decision_path))
            decision_path = Path(folder) / "G6.csv"
            write_csv(decision_path, ["sku", "gate", "decision"],
                      [{"sku": "A", "gate": "G6", "decision": "pass"}])
            with self.assertRaises(ValueError):
                record_gate.record(folder, "L1", "A", "G6", "pass", "owner", "approver",
                                   evidence_files=[str(proof)], decision_file=str(decision_path))
            with open(Path(folder) / "workflow_state.json", encoding="utf-8") as f:
                self.assertEqual(json.load(f)["launches"]["L1"]["current_gate"], "G6")

    def test_g6_accepts_recalculated_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-sop-orchestrator/scripts/create_launch_workspace.py"),
                            "--output-dir", folder], check=True, capture_output=True)
            state_path = Path(folder) / "workflow_state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["launches"]["L1"] = {"sku": "A", "current_gate": "G6", "lifecycle_state": "commercially_validated"}
            state_path.write_text(json.dumps(state), encoding="utf-8")
            evidence_path = Path(folder) / "evidence_matrix.csv"
            proof = Path(folder) / "proof.pdf"
            proof.write_bytes(b"source evidence")
            evidence_rows = [{"sku": "A", "control_ref": ref, "status": "pass", "owner": "owner",
                              "evidence": str(proof), "evidence_source": "Seller Central",
                              "evidence_date": date.today().isoformat()} for ref in gate.REQUIRED_CONTROLS]
            write_csv(evidence_path, list(evidence_rows[0]), evidence_rows)
            cost_path = Path(folder) / "landed_cost_model.csv"
            cost = {"sku": "A", "selling_price_jpy": "100", "unit_cost_jpy": "20",
                    "international_freight_jpy": "5", "duty_tax_jpy": "5",
                    "fba_fee_jpy": "10", "referral_fee_jpy": "10"}
            write_csv(cost_path, list(cost), [cost])
            decision_path = Path(folder) / "launch_gate.decision.csv"
            write_csv(decision_path, ["sku", "decision"], [{"sku": "A", "decision": "pass"}])
            result = record_gate.record(folder, "L1", "A", "G6", "pass", "owner", "approver",
                                        evidence_files=[str(evidence_path), str(cost_path)],
                                        decision_file=str(decision_path))
            self.assertEqual(result["current_gate"], "G7")

    def test_downstream_scripts_reject_blocked_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gate_decision = root / "gate.csv"
            write_csv(gate_decision, ["sku", "decision"], [{"sku": "A", "decision": "blocked"}])
            listing = root / "listing.csv"
            write_csv(listing, ["sku", "title"], [{"sku": "A", "title": "商品"}])
            seller_result = subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-seller-central-ops/scripts/build_seller_central_checklist.py"),
                                            "--listing", str(listing), "--gate-decision", str(gate_decision),
                                            "--output-prefix", str(root / "seller")], capture_output=True)
            self.assertNotEqual(seller_result.returncode, 0)
            self.assertFalse((root / "seller.decision.csv").exists())

    def test_fba_does_not_invent_sales(self):
        result = fba.plan_row({"sku": "A", "fulfillable_qty": "100", "inbound_qty": "0"},
                              {"package_weight_g": "50", "package_length_cm": "10"}, {})
        self.assertEqual(result["status"], "needs_proof")
        self.assertEqual(result["recommended_first_shipment_qty"], "")

    def test_fba_uses_sellable_stock_and_requires_real_proof(self):
        with tempfile.TemporaryDirectory() as folder:
            proof_file = Path(folder) / "proof.png"
            proof_file.write_bytes(b"proof")
            specs = {"package_weight_g": "50", "package_length_cm": "10", "package_width_cm": "10",
                     "package_height_cm": "10", "carton_qty": "20", "carton_weight_g": "1000",
                     "production_lead_time_days": "10", "freight_lead_time_days": "10",
                     "fba_receiving_buffer_days": "5", "safety_stock_days": "10", "target_days_of_supply": "60"}
            inventory = {"sku": "A", "fulfillable_qty": "100", "inbound_qty": "200"}
            sales = {"daily_sales_estimate": "2"}
            without_proof = fba.plan_row(inventory, specs, sales)
            self.assertEqual(without_proof["days_of_supply"], 50)
            self.assertEqual(without_proof["recommended_first_shipment_qty"], 0)
            self.assertEqual(without_proof["status"], "needs_proof")
            proof = {}
            for field in fba.PROOF_FIELDS:
                path = Path(folder) / f"{field}.png"
                path.write_bytes(field.encode())
                proof[field] = str(path)
            self.assertEqual(fba.plan_row(inventory, specs, sales,
                                          {field: str(proof_file) for field in fba.PROOF_FIELDS})["status"], "needs_proof")
            self.assertEqual(fba.plan_row(inventory, specs, sales, proof)["status"], "pass")
            prelaunch = {**inventory, "launch_phase": "prelaunch", "fulfillable_qty": "0", "inbound_qty": "0"}
            first = fba.plan_row(prelaunch, specs, sales, proof)
            self.assertEqual(first["status"], "pass")
            self.assertEqual(first["recommended_first_shipment_qty"], 120)

    def test_seller_proof_must_be_file(self):
        with tempfile.TemporaryDirectory() as folder:
            proof = Path(folder) / "upload.png"
            proof.write_bytes(b"screenshot")
            checklist = [{"sku": "A", "field": "title", "owner": "operator",
                          "status": "pass", "next_action": "ready"}]
            row = {"sku": "A", "field": "title", "owner": "operator", "status": "done",
                   "evidence_file": str(proof)}
            self.assertEqual(seller.build_ops_rows(checklist, [row])[0]["status"], "done")
            row["evidence_file"] = str(Path(folder) / "missing.png")
            self.assertEqual(seller.build_ops_rows(checklist, [row])[0]["status"], "needs_proof")

    def test_workspace_record_and_no_gate_skip(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-sop-orchestrator/scripts/create_launch_workspace.py"),
                            "--output-dir", folder], check=True, capture_output=True)
            decision_path = Path(folder) / "decision.csv"
            proof_path = Path(folder) / "proof.txt"
            proof_path.write_text("source evidence", encoding="utf-8")
            write_csv(decision_path, ["sku", "gate", "decision"], [{"sku": "A", "gate": "G0", "decision": "pass"}])
            with self.assertRaises(ValueError):
                record_gate.record(folder, "L1", "A", "G1", "pass", "owner", "approver", decision_file=str(decision_path))
            state = record_gate.record(folder, "L1", "A", "G0", "pass", "owner", "approver",
                                       evidence_files=[str(proof_path)], decision_file=str(decision_path))
            self.assertEqual(state["current_gate"], "G1")
            with self.assertRaises(ValueError):
                record_gate.record(folder, "L1", "A", "G0", "pass", "owner", "approver",
                                   evidence_files=[str(proof_path)], decision_file=str(decision_path))
            with open(Path(folder) / "gate_decisions.csv", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_live_report_missing_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "business.csv"
            write_csv(source, ["SKU", "Sessions"], [{"SKU": "A", "Sessions": "1"}])
            with self.assertRaises(ValueError):
                live.normalize_file("business_metrics", source, folder, [])

    def test_stale_live_report_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "business.csv"
            write_csv(source, ["SKU", "Sessions", "Units Ordered", "Sales"],
                      [{"SKU": "A", "Sessions": "10", "Units Ordered": "1", "Sales": "100"}])
            output = Path(folder) / "normalized"
            result = subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-live-data-sync/scripts/normalize_live_reports.py"),
                                     "--business", str(source), "--period-start", (date.today() - timedelta(days=30)).isoformat(),
                                     "--exported-at", date.today().isoformat() + "T12:00:00", "--report-end",
                                     (date.today() - timedelta(days=30)).isoformat(),
                                     "--output-dir", str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((output / "business_metrics.normalized.csv").exists())


class GoldenRunTests(unittest.TestCase):
    def test_synthetic_sku_from_raw_reports_to_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = root / "raw"
            raw.mkdir()
            today = date.today().isoformat()
            specs = {
                "business": (["SKU", "Sessions", "Units Ordered", "Sales"],
                             [{"SKU": "SKU-A", "Sessions": "100", "Units Ordered": "10", "Sales": "10000"}]),
                "search-terms": (["SKU", "Customer Search Term", "Spend", "Orders", "Sales"],
                                 [{"SKU": "SKU-A", "Customer Search Term": "収納", "Spend": "100", "Orders": "2", "Sales": "1000"}]),
                "inventory": (["SKU", "Fulfillable Quantity"],
                              [{"SKU": "SKU-A", "Fulfillable Quantity": "100"}]),
                "returns": (["SKU", "Return Date", "Quantity"],
                            [{"SKU": "SKU-A", "Return Date": today, "Quantity": "0"}]),
                "reviews": (["ASIN", "Review Date", "Rating"],
                            [{"ASIN": "B000000001", "Review Date": today, "Rating": "4.5"}]),
            }
            args = []
            for kind, (fields, rows) in specs.items():
                path = raw / f"{kind}.csv"
                write_csv(path, fields, rows)
                args.extend([f"--{kind}", str(path)])
            output = root / "live"
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-live-data-sync/scripts/normalize_live_reports.py"),
                            *args, "--period-start", today, "--report-end", today,
                            "--exported-at", today + "T12:00:00", "--sku-scope", "SKU-A",
                            "--output-dir", str(output)], check=True, capture_output=True)
            with open(output / "report_manifest.csv", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 5)

            evidence = root / "evidence.csv"
            proof = root / "proof.pdf"
            proof.write_bytes(b"source evidence")
            evidence_rows = [{"sku": "SKU-A", "control_ref": ref, "status": "pass", "owner": "lead",
                              "evidence": str(proof), "evidence_source": "Seller Central",
                              "evidence_date": today} for ref in gate.REQUIRED_CONTROLS]
            write_csv(evidence, list(evidence_rows[0]), evidence_rows)
            costs = root / "costs.csv"
            write_csv(costs, ["sku", *gate.MAJOR_COST_FIELDS],
                      [{"sku": "SKU-A", "selling_price_jpy": "100", "unit_cost_jpy": "20",
                        "international_freight_jpy": "5", "duty_tax_jpy": "5",
                        "fba_fee_jpy": "10", "referral_fee_jpy": "10"}])
            gate_prefix = root / "gate"
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-launch-gate/scripts/evaluate_launch_gate.py"),
                            "--evidence", str(evidence), "--costs", str(costs),
                            "--output-prefix", str(gate_prefix)], check=True, capture_output=True)
            with open(str(gate_prefix) + ".decision.csv", encoding="utf-8") as f:
                self.assertEqual(next(csv.DictReader(f))["decision"], "pass")

            metrics = root / "metrics.csv"
            row = {"launch_id": "L1", "sku": "SKU-A",
                   "week_start": (date.today() - timedelta(days=7)).isoformat(),
                   "sessions": "100", "orders": "10", "sales_jpy": "10000", "ad_spend_jpy": "1000",
                   "acos_pct": "10", "tacos_pct": "10", "break_even_acos_pct": "25",
                   "unit_session_pct": "10", "rating": "4.5", "returns": "0", "days_of_supply": "40"}
            write_csv(metrics, list(row), [row])
            prefix = root / "performance"
            subprocess.run([sys.executable, str(ROOT / "skills/amazon-jp-performance-reviewer/scripts/review_performance.py"),
                            "--metrics", str(metrics), "--search-terms", str(output / "ads_search_terms.normalized.csv"),
                            "--inventory", str(output / "inventory.normalized.csv"),
                            "--returns", str(output / "returns.normalized.csv"),
                            "--report-manifest", str(output / "report_manifest.csv"),
                            "--output-prefix", str(prefix)], check=True, capture_output=True)
            with open(str(prefix) + ".decisions.csv", encoding="utf-8") as f:
                self.assertEqual(next(csv.DictReader(f))["decision"], "scale")
            with open(str(prefix) + ".actions.csv", encoding="utf-8") as f:
                self.assertTrue(list(csv.DictReader(f)))


if __name__ == "__main__":
    unittest.main()
