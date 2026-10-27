#!/usr/bin/env python3
"""Reproduce native approval boundary gaps on localhost synthetic Purchase Orders.

Read-only by default. --exercise temporarily narrows the existing Workflow, creates
synthetic orders, then cancels submitted orders/deletes unused drafts and restores
configuration. Exit 2 means a release-blocking bypass was reproduced, not a pass.
No database access, submitted accounting documents, secrets, or production data.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from phase0_api import ERPNextAPI

COMPANY = 'R1合成发布验证公司'
WORKFLOW = 'P0 Purchase Order Approval'
WORKFLOW_KEYS = ('is_active', 'send_email_alert', 'workflow_state_field', 'states', 'transitions')
MAKER = 'p0.purchase@example.invalid'
MANAGER = 'p0.approver@example.invalid'
SETTER = 'Purchase Order-items-permlevel'


def login(url, user, password):
    api = ERPNextAPI(url)
    api.login(user, password)
    return api


def summary(doc):
    return {key: doc.get(key) for key in (
        'name', 'company', 'currency', 'grand_total', 'docstatus',
        'workflow_state', 'owner', 'modified_by')}


def semantic_workflow(doc):
    """Compare configuration, retaining child identifiers but excluding audit timestamps."""
    result = {key: copy.deepcopy(doc[key]) for key in WORKFLOW_KEYS}
    for table in ('states', 'transitions'):
        for row in result[table]:
            for key in ('modified', 'modified_by'):
                row.pop(key, None)
    return result


def probe(args):
    parsed = urlparse(args.base_url)
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1') or parsed.port != 8080:
        raise ValueError('This probe is limited to the disposable localhost:8080 site')
    admin = login(args.base_url, 'Administrator', os.environ.get('PHASE0_PASSWORD', 'admin'))
    original = admin.get_doc('Workflow', WORKFLOW)
    if not original or original['is_active'] != 1:
        raise ValueError('Expected existing active P0 Purchase Order Workflow')
    active = admin.list_docs('Workflow', ['name'], [['document_type', '=', 'Purchase Order'], ['is_active', '=', 1]])
    if active != [{'name': WORKFLOW}]:
        raise ValueError('Unexpected active Workflow configuration; refuse mutation')
    if admin.get_doc('Property Setter', SETTER):
        raise ValueError('Existing items permission override; refuse overwrite')
    if not admin.get_doc('Company', COMPANY):
        raise ValueError('Run N1 synthetic configuration first')
    for user in (MAKER, MANAGER):
        doc = admin.get_doc('User', user)
        roles = {r['role'] for r in doc['roles']}
        if not doc.get('enabled') or 'System Manager' in roles or 'Purchase User' not in roles:
            raise ValueError('Unexpected synthetic user configuration')
        if user == MANAGER and 'Purchase Manager' not in roles:
            raise ValueError('Synthetic manager lacks Purchase Manager role')
    if not args.exercise:
        return {'status': 'READ_ONLY_READY', 'workflow': WORKFLOW, 'company': COMPANY}

    # Refuse to replace a later implementation with a historical probe.
    if [(r['state'], str(r['doc_status'])) for r in original['states']] != [
        ('Pending', '0'), ('Approved', '1'), ('Rejected', '2')]:
        raise ValueError('Workflow has changed; review the probe before reuse')
    if len(original['transitions']) != 2 or any(r.get('condition') for r in original['transitions']):
        raise ValueError('Workflow conditions have changed; refuse overwrite')
    backup = {key: copy.deepcopy(original[key]) for key in WORKFLOW_KEYS}
    backup_path = Path('/private/tmp') / f'r1-n2-workflow-backup-{uuid4().hex}.json'
    backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2) + '\n')
    narrowed = copy.deepcopy(backup)
    narrowed['transitions'][0]['condition'] = (
        f'doc.company != {COMPANY!r} or (doc.currency == "CNY" and '
        'doc.grand_total >= 0 and doc.grand_total <= 10000 and doc.owner != frappe.session.user)'
    )
    role_password = os.environ.get('PHASE0_ROLE_PASSWORD', 'p0-local-only')
    maker = login(args.base_url, MAKER, role_password)
    manager = login(args.base_url, MANAGER, role_password)
    evidence = {'status': 'EXERCISING', 'cases': [], 'cleanup': [], 'workflow_restored': False,
                'field_guard_restored': False, 'backup_path': str(backup_path)}
    created = []
    setter_created = False
    tomorrow = (date.today() + timedelta(days=7)).isoformat()

    def create(amount, case):
        doc = maker.insert('Purchase Order', {
            'company': COMPANY, 'supplier': 'R1合成供应商', 'currency': 'CNY',
            'transaction_date': date.today().isoformat(), 'schedule_date': tomorrow,
            'buying_price_list': 'R1合成采购价目表',
            'terms': f'R1-N2-PROBE {case} {uuid4().hex}; synthetic only',
            'items': [{'item_code': 'R1-DEMO-SCREW', 'qty': 1, 'rate': amount,
                       'warehouse': 'R1测试主仓 - R1D', 'schedule_date': tomorrow}],
        })
        created.append(doc['name'])
        if doc['docstatus'] != 0 or doc['workflow_state'] != 'Pending' or doc['grand_total'] != amount:
            raise RuntimeError('Fixture amount/state mismatch')
        return doc

    def attempt(case, action, doc):
        entry = {'case': case, 'before': summary(doc)}
        try:
            after = action()
            entry.update(result='ALLOWED', after=summary(after))
        except RuntimeError as error:
            # Only actual permission/workflow refusals qualify as negative evidence.
            if not any(kind in str(error) for kind in ('PermissionError', 'WorkflowTransitionError', 'WorkflowPermissionError', 'ApprovalBoundaryError')):
                raise
            entry.update(result='DENIED', error_type=next(kind for kind in (
                'WorkflowTransitionError', 'WorkflowPermissionError', 'ApprovalBoundaryError', 'PermissionError') if kind in str(error)))
            entry['after'] = summary(admin.get_doc('Purchase Order', doc['name']))
        evidence['cases'].append(entry)

    try:
        admin.update('Workflow', WORKFLOW, narrowed)
        doc = create(10000, 'normal-boundary')
        attempt('normal_10000', lambda: manager.call('frappe.model.workflow.apply_workflow', {'doc': doc, 'action': 'Approve'}), doc)
        doc = create(10000.01, 'normal-over-boundary')
        attempt('normal_10000_01', lambda: manager.call('frappe.model.workflow.apply_workflow', {'doc': doc, 'action': 'Approve'}), doc)
        doc = create(10000, 'mutate-and-submit')
        rows = copy.deepcopy(doc['items']); rows[0]['rate'] = 10000.01
        attempt('rest_mutate_and_submit', lambda: manager.update('Purchase Order', doc['name'], {
            'items': rows, 'workflow_state': 'Approved', 'docstatus': 1}), doc)
        doc = create(10000.01, 'direct-submit')
        attempt('manager_direct_submit', lambda: manager.submit(doc), doc)
        doc = create(10000.01, 'maker-direct-submit')
        attempt('maker_direct_submit', lambda: maker.submit(doc), doc)
        # A native field permission guard protects inputs but cannot force transitions.
        doc = create(10000.01, 'locked-items-direct-submit')
        admin.insert('Property Setter', {'doctype_or_field': 'DocField', 'doc_type': 'Purchase Order',
            'field_name': 'items', 'property': 'permlevel', 'property_type': 'Int', 'value': '2'})
        setter_created = True
        attempt('manager_direct_submit_with_items_locked', lambda: manager.submit(doc), doc)
    finally:
        # Restore controls even when a case or cleanup operation fails.
        try:
            if setter_created:
                admin.request('DELETE', admin.resource_path('Property Setter', SETTER))
            evidence['field_guard_restored'] = admin.get_doc('Property Setter', SETTER) is None
            for name in created:
                doc = admin.get_doc('Purchase Order', name)
                if doc['docstatus'] == 1:
                    admin.call('frappe.model.workflow.apply_workflow', {'doc': doc, 'action': 'Reject'})
                    final = admin.get_doc('Purchase Order', name)
                    if final['docstatus'] != 2:
                        raise RuntimeError('Submitted probe order was not cancelled')
                    evidence['cleanup'].append({'name': name, 'docstatus': 2})
                elif doc['docstatus'] == 0:
                    admin.request('DELETE', admin.resource_path('Purchase Order', name))
                    if admin.get_doc('Purchase Order', name) is not None:
                        raise RuntimeError('Unused draft cleanup failed')
                    evidence['cleanup'].append({'name': name, 'draft_deleted': True})
        finally:
            admin.update('Workflow', WORKFLOW, backup)
            evidence['workflow_restored'] = semantic_workflow(admin.get_doc('Workflow', WORKFLOW)) == semantic_workflow(original)
            if not evidence['workflow_restored']:
                raise RuntimeError(f'Workflow restore mismatch; recovery data: {backup_path}')
    cases = {row['case']: row for row in evidence['cases']}
    if cases['normal_10000']['result'] != 'ALLOWED' or cases['normal_10000_01']['result'] != 'DENIED':
        raise RuntimeError('Normal threshold control failed; cannot interpret bypass cases')
    gaps = [name for name, row in cases.items() if name not in ('normal_10000', 'normal_10000_01')
            and row['result'] == 'ALLOWED' and row['after']['docstatus'] == 1
            and row['after']['grand_total'] > 10000]
    evidence.update(status='BLOCKED_NATIVE_APPROVAL' if gaps else 'NO_BYPASS_REPRODUCED', bypass_cases=gaps)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--exercise', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = probe(args)
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    if args.output:
        args.output.write_text(output)
    print(output, end='')
    return 2 if result['status'] == 'BLOCKED_NATIVE_APPROVAL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
