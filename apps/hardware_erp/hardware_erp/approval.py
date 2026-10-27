"""Server-side guard at native document service entry points.

No custom endpoint, SQL, direct database API, client-only checks or core patches.
Workflow/permissions remain native. P0 discovery transactions are deliberately
isolated; every other company must have an active Workflow on these DocTypes.
"""
import frappe
from frappe.model.workflow import get_workflow, is_transition_condition_satisfied
from .rules import fingerprint, require_transition

P0_COMPANY = 'Phase Zero Hardware Trading Demo'
MAKERS = {
    'Purchase Order': 'R1采购经办', 'Sales Order': 'R1销售经办',
    'Payment Entry': 'R1财务经办', 'Purchase Invoice': 'R1财务经办',
    'Sales Invoice': 'R1财务经办', 'Purchase Receipt': 'R1库存经办',
    'Delivery Note': 'R1库存经办', 'Stock Entry': 'R1库存经办',
    'Stock Reconciliation': 'R1库存经办',
}


class ApprovalBoundaryError(frappe.ValidationError):
    pass


def deny(message):
    frappe.throw(message, ApprovalBoundaryError)


def context(doc):
    old = doc.get_doc_before_save()
    # Changing a protected document's company cannot escape to the P0 namespace.
    if doc.company == P0_COMPANY and (old is None or old.company == P0_COMPANY):
        return None
    if old is not None and (old.company != doc.company or old.owner != doc.owner):
        deny('审批单据的公司和创建人不得变更')
    if doc.get('currency') and doc.currency != 'CNY':
        deny('首版审批仅支持人民币单据')
    if doc.doctype == 'Payment Entry' and (doc.get('paid_amount', 0) < 0 or doc.get('received_amount', 0) < 0):
        deny('收付款金额不得为负；退款请使用付款类型，冲回使用原单撤销或退货贷项')
    workflow_name = doc.meta.get_workflow()
    if not workflow_name:
        deny('审批配置缺失，禁止保存、提交或撤销该类单据')
    workflow = get_workflow(doc.doctype)
    state_field = workflow.workflow_state_field
    new_state = doc.get(state_field) or workflow.states[0].state
    old_state = old.get(state_field) if old is not None else workflow.states[0].state
    old_status = int(old.docstatus) if old is not None else 0
    matching = [row for row in workflow.states if row.state == new_state]
    if len(matching) != 1:
        deny('审批状态不存在或不唯一')
    try:
        require_transition(old_state, new_state, old_status, int(doc.docstatus), matching[0].doc_status)
    except ValueError as error:
        deny(str(error))
    if old is None and (new_state != workflow.states[0].state or int(doc.docstatus) != 0):
        deny('新单据只能从待审批草稿创建')
    return old, workflow, old_state, new_state


def check_before_validation(doc, method=None):
    ctx = context(doc)
    if ctx is None:
        return
    old, workflow, old_state, new_state = ctx
    if old is None:
        if MAKERS[doc.doctype] not in frappe.get_roles():
            deny('当前身份不能创建此类业务单据')
        return
    changed = fingerprint(old.as_dict(), workflow.workflow_state_field) != fingerprint(doc.as_dict(), workflow.workflow_state_field)
    if changed and (old_state != workflow.states[0].state or new_state != old_state):
        deny('审批期间不得同时修改业务内容；请退回待审批草稿后重新审批')
    if old_state == new_state:
        state = next(row for row in workflow.states if row.state == old_state)
        editable_role = MAKERS[doc.doctype] if old_state == workflow.states[0].state else state.allow_edit
        if editable_role not in frappe.get_roles():
            deny('当前身份不能编辑此审批阶段的业务内容')
    else:
        validate_actor(doc, ctx)


def validate_actor(doc, ctx):
    old, workflow, old_state, new_state = ctx
    user = frappe.session.user
    if user == 'Administrator':
        deny('管理员不得承担日常业务审批，请使用独立职能审批身份')
    if user == doc.owner:
        deny('创建人不得审批、复核或撤销自己的单据')
    roles = set(frappe.get_roles())
    # Thresholds are frozen business policy, not removable Workflow conditions.
    if int(doc.docstatus) == 1 and int(old.docstatus) == 0:
        if doc.doctype in ('Purchase Order', 'Sales Order', 'Payment Entry'):
            amount = max(abs(doc.paid_amount), abs(doc.received_amount)) if doc.doctype == 'Payment Entry' else doc.grand_total
            limit = 20000 if doc.doctype == 'Payment Entry' else 10000
            if amount > limit and (old_state != '待负责人复核' or 'R1业务负责人' not in roles or old.modified_by == user):
                deny('超额单据必须先经理复核，再由独立业务负责人批准')
        if doc.doctype in ('Purchase Invoice','Sales Invoice','Stock Reconciliation') or (doc.doctype=='Stock Entry' and doc.purpose!='Material Transfer') or (doc.doctype in ('Purchase Receipt','Delivery Note') and doc.is_return):
            if old_state != '待财务复核' or 'R1财务复核' not in roles or old.modified_by == user:
                deny('该单据必须经过独立财务复核')
    condition_doc = frappe.get_doc(doc.as_dict())
    condition_doc.modified_by = old.modified_by
    candidates = [row for row in workflow.transitions
                  if row.state == old_state and row.next_state == new_state
                  and row.allowed in roles and not row.allow_self_approval
                  and is_transition_condition_satisfied(row, condition_doc)]
    if len(candidates) != 1:
        deny('审批身份、金额阈值或独立复核条件不满足')


def check_transition(doc, method=None):
    # Executes after native amount calculation for submit, before auto-state mapping.
    ctx = context(doc)
    if ctx is not None:
        if method == 'before_cancel':
            old, workflow, _, _ = ctx
            if fingerprint(old.as_dict(), workflow.workflow_state_field) != fingerprint(doc.as_dict(), workflow.workflow_state_field):
                deny('撤销审批不得同时修改原单业务内容')
        validate_actor(doc, ctx)
