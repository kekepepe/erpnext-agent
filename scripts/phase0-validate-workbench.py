"""Validate navigation against real session permissions on the disposable site."""
import json
import os
from pathlib import Path
from phase0_api import ERPNextAPI, validate_disposable_url

base = validate_disposable_url(os.environ.get('PHASE0_BASE_URL', 'http://localhost:8080'))
config = json.loads((Path(__file__).resolve().parents[1] / 'phase0/release-access.json').read_text())
method = 'erpnext_zh.workbench.get_context'
guest = ERPNextAPI(base)
try:
    guest.call(method, {})
except RuntimeError as exc:
    assert 'HTTP 403' in str(exc), 'Expected guest permission rejection'
else:
    raise AssertionError('Guest unexpectedly accepted')
print('PASS guest rejected')
for key, user in config['users'].items():
    api = ERPNextAPI(base)
    api.login(user['email'], os.environ.get('PHASE0_ROLE_PASSWORD', 'p0-local-only'))
    data = api.call(method, {})
    assert data['user'] == user['email']
    assert len(data['recent']) <= 12
    for doc in data['recent']:
        assert api.get_doc(doc['doctype'], doc['name'])
    items = [i for g in data['groups'] for i in g['items']]
    for item in items:
        if item.get('doctype') and not item.get('single'):
            api.list_docs(item['doctype'], ['name'], [[field, '=', value] for field, value in item.get('filters', {}).items()], limit=1)
    assert not any(i.get('doctype') in ('User', 'Role', 'Workflow', 'System Settings') for i in items), key
    # The page must be readable by real business roles, not only Administrator.
    response = api.request('GET', '/api/method/frappe.desk.desk_page.getpage?name=hardware-workbench')
    assert response['docs'][0]['name'] == 'hardware-workbench'
    print(f'PASS {key}: {len(items)} entries, {len(data["recent"])} authorized recent documents')
