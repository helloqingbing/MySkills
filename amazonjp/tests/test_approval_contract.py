"""Approval lineage, economics, recurring reviews and executable ad counterexamples."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from test_workflow import ROOT, ads, gate, seller, record_gate, approved_workspace, write_csv
from approval_contract import ApprovalContext


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.paths = approved_workspace(self.root, stage=11)
        self.product = {'sku': 'A', 'asin': 'ASIN-A', 'price_jpy': '1', 'gross_profit_jpy': '1',
                        'target_acos_pct': '25', 'daily_budget_jpy': '3000'}
        keyword = {'sku': 'A', 'keyword': 'storage', 'relevance': 'high'}
        write_csv(self.root / 'keywords.csv', list(keyword), [keyword])

    def ads(self, extra=()):
        write_csv(self.root / 'products.csv', list(self.product), [self.product])
        return subprocess.run([sys.executable, str(ROOT / 'skills/amazon-ads-planner/scripts/plan_amazon_ads.py'),
            '--workspace', str(self.root), '--launch-id', 'L1', '--products', str(self.root / 'products.csv'),
            '--keywords', str(self.root / 'keywords.csv'), '--gate-decision', str(self.paths['G6']),
            '--seller-decision', str(self.paths['G9']), '--fba-plan', str(self.paths['G10']),
            '--output-prefix', str(self.root / 'result'), *extra], capture_output=True, text=True)

    def test_ads_uses_approved_costs_and_rejects_unprofitable_target(self):
        result = self.ads()
        self.assertEqual(result.returncode, 0, result.stderr)
        with (self.root / 'result.economics.csv').open() as stream:
            actual = next(csv.DictReader(stream))
        self.assertEqual(float(actual['selling_price_jpy']), 1000)
        self.assertEqual(float(actual['gross_profit_jpy']), 400)
        self.assertEqual(float(actual['break_even_acos_pct']), 40)
        self.product['target_acos_pct'] = '90'
        self.assertNotEqual(self.ads().returncode, 0)
        for invalid in ('-1', 'nan', 'inf', '0'):
            self.product['target_acos_pct'] = invalid
            self.assertNotEqual(self.ads().returncode, 0)

    def test_same_sku_old_approval_and_wrong_stage_are_rejected(self):
        old = self.root / 'old.csv'
        write_csv(old, ['launch_id', 'sku', 'decision'], [{'launch_id': 'OLD', 'sku': 'A', 'decision': 'pass'}])
        self.assertNotEqual(self.ads(['--gate-decision', str(old)]).returncode, 0)
        self.assertNotEqual(self.ads(['--launch-id', 'OLD']).returncode, 0)
        with self.assertRaises(ValueError):
            ApprovalContext(self.root, 'L1', 'A', 'G10')
        state_file = self.root / 'workflow_state.json'
        state = json.loads(state_file.read_text())
        state['launches']['L1']['current_gate'] = 'G6'
        state_file.write_text(json.dumps(state))
        self.assertNotEqual(self.ads().returncode, 0)

    def test_modified_approved_cost_or_referenced_proof_invalidates_release(self):
        for key in ('costs', 'proof'):
            path = self.paths[key]
            original = path.read_bytes()
            path.write_bytes(original + b'\nchanged')
            self.assertNotEqual(self.ads().returncode, 0, key)
            path.write_bytes(original)
        self.assertEqual(self.ads().returncode, 0)

    def test_missing_audit_event_rejects_approval(self):
        path = self.root / 'workflow_state.json'
        state = json.loads(path.read_text())
        state['gate_decisions'] = [r for r in state['gate_decisions'] if r['gate'] != 'G9']
        path.write_text(json.dumps(state))
        self.assertNotEqual(self.ads().returncode, 0)

    def test_g11_cannot_approve_missing_or_unprofitable_policy(self):
        decision = self.root / 'G11.csv'
        row = {'launch_id': 'L1', 'sku': 'A', 'decision': 'pass'}
        write_csv(decision, list(row), [row])
        def approve(evidence):
            return record_gate.record(self.root, 'L1', 'A', 'G11', 'pass', 'owner', 'approver',
                                      decision_file=decision, evidence_files=evidence)
        with self.assertRaises(ValueError):
            approve([self.paths['proof']])
        write_csv(self.paths['economics'], ['launch_id', 'sku', 'target_acos_pct'],
                  [{'launch_id': 'L1', 'sku': 'A', 'target_acos_pct': '90'}])
        with self.assertRaises(ValueError):
            approve([self.paths['economics']])



class NegativeAndEvidenceTests(unittest.TestCase):
    def test_negatives_reference_existing_auto_and_broad_with_valid_match(self):
        product = ads.normalize_product({'sku': 'A', 'price_jpy': '1000', 'gross_profit_jpy': '400'}, 3000)
        blocked = ads.normalize_keyword({'keyword': 'blocked', 'risk': 'blocked', 'ads_match_type': 'exact'})
        for budget in (300, 1500, 3000):
            product['daily_budget_jpy'] = budget
            for usable in ([], [ads.normalize_keyword({'keyword': 'storage', 'relevance': 'high'})]):
                campaigns, negatives = ads.plan_for_product(product, [blocked, *usable], [])
                names = {r['campaign_name'] for r in campaigns}
                discovery = {r['campaign_name'] for r in campaigns if r['ad_group'] in {'auto', 'broad'}}
                self.assertEqual({r['campaign_name'] for r in negatives}, discovery)
                self.assertTrue(all(r['campaign_name'] in names and r['negative_type'] == 'negative exact' for r in negatives))
        forbidden = ads.normalize_keyword({'keyword': '医療 storage', 'relevance': 'high'})
        campaigns, negatives = ads.plan_for_product(product, [forbidden], [])
        self.assertEqual(len(campaigns), 1)
        self.assertEqual(negatives[0]['campaign_name'], campaigns[0]['campaign_name'])

    def test_claims_na_uses_control_reference_and_same_gate_rules(self):
        with tempfile.TemporaryDirectory() as folder:
            proof = Path(folder) / 'proof.pdf'
            proof.write_bytes(b'documented no claim')
            row = {'sku': 'A', 'control_ref': 'CLAIMS-JP-01', 'status': 'not_applicable',
                   'blocking_reason': 'No performance claim', 'owner': 'lead', 'evidence': 'proof.pdf',
                   'evidence_source': 'claim ledger', 'evidence_date': date.today().isoformat()}
            self.assertEqual(seller.evidence_status([row], 'claim', folder), 'pass')
            for field in ('blocking_reason', 'owner', 'evidence_source', 'evidence_date', 'evidence'):
                self.assertEqual(seller.evidence_status([{**row, field: ''}], 'claim', folder), 'needs_proof')
            self.assertEqual(seller.evidence_status([{**row, 'control_ref': 'JP-IMPORT-FBA-01'}], 'import', folder), 'needs_proof')
            self.assertEqual(seller.evidence_status([row, row], 'claim', folder), 'needs_proof')
            proof.unlink()
            self.assertEqual(seller.evidence_status([row], 'claim', folder), 'needs_proof')


class ReviewCycleTests(unittest.TestCase):
    def test_completed_pause_review_can_repeat_next_week_without_overlap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = approved_workspace(root)
            def record_week(days, action='pause', gate_decision='pass'):
                week = (date.today() - timedelta(days=days)).isoformat()
                row = {'sku': 'A', 'launch_id': 'L1', 'gate': 'G12', 'week_start': week,
                       'review_id': f'L1:A:{week}', 'decision': action, 'gate_decision': gate_decision}
                decision = root / f'review-{days}.csv'
                write_csv(decision, list(row), [row])
                return record_gate.record(root, 'L1', 'A', 'G12', 'pass', 'owner', 'approver',
                                          decision_file=decision, evidence_files=[paths['proof']])
            first = record_week(14)
            self.assertEqual(first['current_gate'], 'G12')
            self.assertEqual(first['lifecycle_state'], 'optimizing')
            self.assertEqual(first['reviews'][0]['action'], 'pause')
            self.assertEqual(len(record_week(14)['reviews']), 1)  # exact retry
            with self.assertRaises(ValueError):
                record_week(13)
            with self.assertRaises(ValueError):
                record_week(7, 'needs_proof', 'needs_proof')
            second = record_week(7, 'optimize')
            self.assertEqual(len(second['reviews']), 2)
            with self.assertRaises(ValueError):
                record_week(14)
