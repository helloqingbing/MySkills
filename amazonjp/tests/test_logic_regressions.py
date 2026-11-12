"""Counterexamples from the full workflow review, exercised through real CSV CLIs."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from test_workflow import ROOT, ads, fba, seller, record_gate, module, write_csv, approved_workspace

qc = module('qc_regression', 'skills/amazon-jp-sourcing-qc-planner/scripts/build_qc_plan.py')
ingestor = module('ingestor_regression', 'skills/amazon-data-ingestor/scripts/normalize_amazon_jp.py')


class ReviewBindingTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.approved = approved_workspace(self.root)
        self.start = (date.today() - timedelta(days=7)).isoformat()
        self.end = (date.today() - timedelta(days=1)).isoformat()
        self.raw = {
            'business': [{'sku': 'A', 'child_asin': 'ASIN-A', 'sessions': '700', 'orders': '70', 'sales_jpy': '70000'}],
            'search-terms': [{'sku': 'A', 'search_term': 'storage', 'spend_jpy': '700', 'orders': '7', 'sales_jpy': '7000'}],
            'inventory': [{'sku': 'A', 'asin': 'ASIN-A', 'fulfillable_qty': '400'}],
            'returns': [{'sku': 'A', 'return_date': self.end, 'return_qty': '0'}],
            'reviews': [{'asin': 'ASIN-A', 'review_date': self.end, 'rating': '4.5'}],
        }
        self.metadata = {'launch_id': 'L1', 'sku': 'A', 'week_start': self.start, 'break_even_acos_pct': '25'}

    def normalize(self):
        args = []
        for kind, rows in self.raw.items():
            path = self.root / f'{kind}.csv'
            write_csv(path, list(rows[0]), rows)
            args.extend([f'--{kind}', str(path)])
        subprocess.run([sys.executable, str(ROOT / 'skills/amazon-jp-live-data-sync/scripts/normalize_live_reports.py'),
                        *args, '--period-start', self.start, '--report-end', self.end,
                        '--exported-at', date.today().isoformat() + 'T00:00:00', '--sku-scope', 'A',
                        '--output-dir', str(self.root / 'live')], check=True, capture_output=True)

    def review(self, extra=()):
        path = self.root / 'metrics.csv'
        write_csv(path, list(self.metadata), [self.metadata])
        return subprocess.run([sys.executable, str(ROOT / 'skills/amazon-jp-performance-reviewer/scripts/review_performance.py'),
                               '--workspace', str(self.root), '--launch-id', 'L1',
                               '--metrics', str(path), '--report-manifest', str(self.root / 'live/report_manifest.csv'),
                               '--output-prefix', str(self.root / 'review'), *extra], capture_output=True, text=True)

    def decision(self):
        with (self.root / 'review.decisions.csv').open() as f:
            return next(csv.DictReader(f))['decision']

    def test_healthy_review_derives_metrics_without_manual_values(self):
        self.normalize()
        result = self.review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.decision(), 'scale')
        with (self.root / 'review.verified_metrics.csv').open() as f:
            row = next(csv.DictReader(f))
        self.assertEqual(float(row['days_of_supply']), 40)
        self.assertEqual(float(row['ad_spend_jpy']), 700)
        self.assertEqual(float(row['acos_pct']), 10)

    def test_bad_reports_cannot_be_overridden_by_healthy_manual_metrics(self):
        self.raw['business'][0].update(orders='0', sales_jpy='0')
        self.raw['inventory'][0]['fulfillable_qty'] = '0'
        self.raw['returns'][0]['return_qty'] = '10'
        self.raw['search-terms'][0].update(spend_jpy='5000', orders='0', sales_jpy='0')
        self.raw['reviews'][0]['rating'] = '1'
        self.metadata.update(sessions='100', orders='10', sales_jpy='10000', ad_spend_jpy='1000',
                             acos_pct='10', tacos_pct='10', rating='4.5', returns='0', days_of_supply='40')
        self.normalize()
        result = self.review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.decision(), {'pause', 'needs_proof', 'optimize'})
        actions = (self.root / 'review.actions.csv').read_text()
        self.assertIn('inspect_return_reasons', actions)
        self.assertIn('reduce_bid_or_add_negatives', actions)

    def test_substituted_inventory_is_rejected(self):
        self.normalize()
        other = self.root / 'other-inventory.csv'
        write_csv(other, ['sku', 'days_of_supply'], [{'sku': 'A', 'days_of_supply': '999'}])
        self.assertNotEqual(self.review(['--inventory', str(other)]).returncode, 0)
        self.assertFalse((self.root / 'review.decisions.csv').exists())

    def test_one_day_report_cannot_back_a_weekly_review(self):
        self.normalize()
        manifest = self.root / 'live/report_manifest.csv'
        with manifest.open() as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row['period_start'] = self.end
        write_csv(manifest, fields, rows)
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'needs_proof')

    def test_future_export_is_rejected(self):
        self.normalize()
        manifest = self.root / 'live/report_manifest.csv'
        with manifest.open() as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        rows[0]['exported_at'] = (date.today() + timedelta(days=365)).isoformat()
        write_csv(manifest, fields, rows)
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'needs_proof')

    def test_unmapped_asin_reviews_cannot_support_scale(self):
        self.raw['reviews'][0]['asin'] = 'OTHER-ASIN'
        self.normalize()
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'needs_proof')

    def test_event_dates_must_be_inside_the_declared_period(self):
        self.raw['reviews'][0]['review_date'] = date.today().isoformat()
        self.normalize()
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'needs_proof')

    def test_manual_margin_cannot_turn_loss_into_scale_or_promote(self):
        self.raw['search-terms'][0].update(spend_jpy='3500', sales_jpy='7000')
        self.metadata['break_even_acos_pct'] = '99'
        self.normalize()
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'optimize')
        self.assertNotIn('promote_exact', (self.root / 'review.alerts.csv').read_text())
        with (self.root / 'review.verified_metrics.csv').open() as stream:
            self.assertEqual(float(next(csv.DictReader(stream))['break_even_acos_pct']), 40)

    def test_efficient_terms_do_not_promote_while_paused_or_missing_proof(self):
        for rating in ('1', '4.5'):
            self.raw['reviews'][0]['rating'] = rating
            self.raw['reviews'][0]['asin'] = 'ASIN-A' if rating == '1' else 'UNMAPPED'
            self.normalize()
            self.assertEqual(self.review().returncode, 0)
            self.assertIn(self.decision(), {'pause', 'needs_proof'})
            self.assertNotIn('promote_exact', (self.root / 'review.alerts.csv').read_text())

    def test_missing_or_tampered_approved_economics_prevents_scale(self):
        self.normalize()
        self.approved['economics'].write_text('sku,target_acos_pct\nA,99\n')
        self.assertEqual(self.review().returncode, 0)
        self.assertEqual(self.decision(), 'needs_proof')


class ReleaseAndRecoveryTests(unittest.TestCase):
    def test_conflicting_decisions_never_release_downstream(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'decision.csv'
            for status in ('blocked', 'needs_proof', 'pass'):
                write_csv(path, ['sku', 'decision', 'status'], [
                    {'sku': 'A', 'decision': 'pass', 'status': 'pass'},
                    {'sku': 'A', 'decision': status, 'status': status}])
                self.assertFalse(ads.has_pass(path, 'A'))
                self.assertFalse(ads.has_pass(path, 'A', 'status'))
                self.assertFalse(fba.has_pass(path, 'A'))
                self.assertFalse(seller.has_gate_pass(path, 'A'))
            write_csv(path, ['sku', 'decision'], [{'sku': 'A', 'decision': 'pass'}, {'sku': 'B', 'decision': 'blocked'}])
            self.assertTrue(ads.has_pass(path, 'A'))

    def test_final_gate_retry_repairs_logs_without_repeating_decision(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            approved_workspace(root)
            # Commit-repair test starts with valid audited upstream approvals.
            state_path = root / 'workflow_state.json'
            state = json.loads(state_path.read_text())
            before = len(state['gate_decisions'])
            proof, decision = root / 'proof.txt', root / 'decision.csv'
            proof.write_text('proof')
            week = (date.today() - timedelta(days=7)).isoformat()
            row = {'sku': 'A', 'launch_id': 'L1', 'gate': 'G12', 'decision': 'scale', 'gate_decision': 'pass',
                   'week_start': week, 'review_id': f'L1:A:{week}'}
            write_csv(decision, list(row), [row])
            args = (folder, 'L1', 'A', 'G12', 'pass', 'owner', 'approver')
            kwargs = {'evidence_files': [str(proof)], 'decision_file': str(decision)}
            original = record_gate.replace_csv
            calls = 0
            def fail_projection(path, rows):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError('disk error')
                return original(path, rows)
            with patch.object(record_gate, 'replace_csv', side_effect=fail_projection):
                with self.assertRaises(OSError):
                    record_gate.record(*args, **kwargs)
            self.assertEqual(record_gate.record(*args, **kwargs)['lifecycle_state'], 'optimizing')
            self.assertEqual(record_gate.record(*args, **kwargs)['lifecycle_state'], 'optimizing')
            with (root / 'gate_decisions.csv').open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), before + 1)
            proof.write_text('different evidence')
            with self.assertRaises(ValueError):
                record_gate.record(*args, **kwargs)

    def test_empty_ads_snapshot_removes_previous_instructions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'negative.csv'
            ads.write_csv(path, [{'target': 'obsolete'}])
            ads.write_csv(path, [])
            with path.open() as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, ['target'])
                self.assertEqual(list(reader), [])
            fresh = Path(folder) / 'feedback.csv'
            ads.write_csv(fresh, [], ['sku', 'action'])
            self.assertEqual(fresh.read_text().strip(), 'sku,action')


class UpstreamValidationTests(unittest.TestCase):
    def test_missing_or_failed_sample_never_passes_supplier(self):
        base = {'sku': 'A', 'supplier_name': 'Supplier', 'unit_cost_jpy': '100', 'moq': '100',
                'lead_time_days': '10', 'certifications': 'proof', 'sample_status': 'pass'}
        self.assertEqual(qc.supplier_score(base)['decision'], 'pass')
        for field in base:
            row = dict(base)
            row.pop(field)
            self.assertNotEqual(qc.supplier_score(row)['decision'], 'pass', field)
        for status in ('fail', 'rejected'):
            self.assertEqual(qc.supplier_score({**base, 'sample_status': status})['decision'], 'blocked')
        for field in ('unit_cost_jpy', 'moq', 'lead_time_days'):
            for value in ('-10', 'NaN', 'inf', 'invalid'):
                self.assertNotEqual(qc.supplier_score({**base, field: value})['decision'], 'pass')

    def test_negative_and_invalid_measurements_are_rejected(self):
        for field in ('orders', 'moq', 'lead_time_days', 'package_weight_g'):
            for value in ('-10', 'NaN', 'inf', '1.2.3', 'abc10'):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    ingestor.clean_value(field, value)
        self.assertEqual(ingestor.clean_value('orders', '1,000'), '1000')
        self.assertEqual(ingestor.clean_value('package_weight_g', '10.5'), '10.5')
        self.assertEqual(ingestor.clean_value('search_volume_growth_yoy_pct', '-10%'), '-10')

    def test_supplier_normalization_preserves_sample_status(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'suppliers.csv'
            row = {'SKU': 'A', 'Supplier': 'Supplier', 'Unit Cost JPY': '100', 'MOQ': '100',
                   'Lead Time Days': '10', 'Certifications': 'proof', 'Sample Status': 'approved'}
            write_csv(path, list(row), [row])
            output, _ = ingestor.normalize_file('supplier_quotes', path, folder)
            with open(output) as f:
                result = next(csv.DictReader(f))
            self.assertEqual(qc.supplier_score(result)['decision'], 'pass')


if __name__ == '__main__':
    unittest.main()
