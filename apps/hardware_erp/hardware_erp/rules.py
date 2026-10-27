"""Pure, testable approval invariants; no framework/database dependency."""
import json

# Fields managed by framework lifecycle, not editable business inputs.
AUDIT_FIELDS = {'doctype', 'name', 'owner', 'creation', 'modified', 'modified_by',
                'docstatus', 'parent', 'parenttype', 'parentfield', '__islocal', '__unsaved'}


def fingerprint(document, state_field='workflow_state'):
    def normalize(value):
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items()
                    if key not in AUDIT_FIELDS and key != state_field and not key.startswith('_')}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return None if value == "" else value
    return json.dumps(normalize(document), sort_keys=True, ensure_ascii=False, default=str)


def require_transition(old_state, new_state, old_status, new_status, target_status):
    if int(new_status) != int(target_status):
        raise ValueError('提交或撤销必须经过相应审批状态，禁止直接改变单据状态')
    if old_state == new_state and int(old_status) != int(new_status):
        raise ValueError('禁止绕过审批直接提交或撤销')
