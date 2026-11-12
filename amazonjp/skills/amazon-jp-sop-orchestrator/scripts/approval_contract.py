"""Local, human-reviewed artifact contract shared by the bundled JP skills.

workflow_state.json is the trust boundary, not an authentication service. Keep the
workspace and approved evidence under the operator's access controls.
"""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def read_rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def gate_validator():
    path = Path(__file__).resolve().parents[2] / 'amazon-jp-launch-gate/scripts/evaluate_launch_gate.py'
    spec = importlib.util.spec_from_file_location('jp_gate_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApprovalContext:
    def __init__(self, workspace, launch_id, sku, stage):
        self.workspace = Path(workspace).resolve()
        self.launch_id, self.sku = launch_id, sku
        state = json.loads((self.workspace / 'workflow_state.json').read_text())
        current = state.get('launches', {}).get(launch_id, {})
        if not launch_id or not sku or current.get('sku') != sku or current.get('current_gate') != stage:
            raise ValueError(f'{launch_id}/{sku} must be at {stage} in this workspace')
        self.approvals = current.get('approvals', {})
        required = [f"G{i}" for i in range(int(stage[1:]))]
        for gate in required:
            approval = self.approvals.get(gate, {})
            if not approval.get('run_id') or not approval.get('artifacts'):
                raise ValueError(f'{gate} has no bound approval for {launch_id}; record a new audited launch')
            events = [row for row in state.get('gate_decisions', []) if row.get('run_id') == approval['run_id']
                      and row.get('launch_id') == launch_id and row.get('sku') == sku and row.get('gate') == gate
                      and row.get('decision') == 'pass' and row.get('approver')]
            if len(events) != 1:
                raise ValueError(f'{gate} approval does not match its audit event')
            for artifact in approval['artifacts']:
                path = self.workspace / artifact['artifact_path']
                if hashlib.sha256(path.read_bytes()).hexdigest() != artifact['checksum']:
                    raise ValueError(f'{gate} approved artifact changed: {path.name}')

    def artifact(self, gate, path):
        resolved = Path(path).resolve()
        if not any((self.workspace / row['artifact_path']).resolve() == resolved
                   for row in self.approvals.get(gate, {}).get('artifacts', [])):
            raise ValueError(f'{resolved.name} is not an approved {gate} artifact for {self.launch_id}')
        return resolved

    def decision(self, gate, path):
        approved = self.approvals.get(gate, {}).get('decision_file', '')
        if not approved or (self.workspace / approved).resolve() != Path(path).resolve():
            raise ValueError(f'decision file is not the approved {gate} decision for {self.launch_id}')
        return self.artifact(gate, path)

    def named_artifact(self, gate, name):
        matches = [self.workspace / row['artifact_path'] for row in self.approvals.get(gate, {}).get('artifacts', [])
                   if (Path(row['artifact_path']).name.endswith(name) if name.startswith('.') else Path(row['artifact_path']).name == name)]
        if len(matches) != 1:
            raise ValueError(f'{gate} requires exactly one approved {name}')
        return matches[0]

    def economics(self):
        matrix = self.named_artifact('G6', 'evidence_matrix.csv')
        costs = self.named_artifact('G6', 'landed_cost_model.csv')
        result = [row for row in gate_validator().evaluate_all(read_rows(matrix), read_rows(costs), 35, matrix.parent)
                  if row['sku'] == self.sku]
        if len(result) != 1 or result[0]['decision'] != 'pass':
            raise ValueError('approved G6 evidence no longer passes')
        return result[0]['economics'][0]


def target_acos(break_even_pct, provided=''):
    value = float(provided) if str(provided).strip() else min(float(break_even_pct) * .8, 35)
    if not math.isfinite(value) or not 0 < value <= float(break_even_pct):
        raise ValueError('target_acos_pct must be positive and no higher than approved break-even ACOS')
    return value
