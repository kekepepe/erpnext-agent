#!/usr/bin/env python3
"""Source-control R1 native roles, company/warehouse permissions and Workflows.

Read-only unless --apply. Only localhost disposable synthetic namespaces; preserve
native/P0 role rules. No SQL, direct DB, business data or passwords in fixtures.
"""
import argparse
import json
import os
from pathlib import Path
from phase0_api import ERPNextAPI, validate_disposable_url

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'phase0/release-access.json'
PERM_METHOD = 'frappe.core.page.permission_manager.permission_manager'
TYPES = {
    'Purchase Order': ('purchase', 'purchase_manager'),
    'Sales Order': ('sales', 'sales_manager'),
    'Payment Entry': ('finance', 'finance_reviewer'),
    'Purchase Receipt': ('stock', 'stock_manager'),
    'Delivery Note': ('stock', 'stock_manager'),
    'Purchase Invoice': ('finance', 'purchase_manager'),
    'Sales Invoice': ('finance', 'sales_manager'),
    'Stock Entry': ('stock', 'stock_manager'),
    'Stock Reconciliation': ('stock', 'stock_manager'),
}
LEGACY = {
    'Purchase Order': ('P0 Purchase Order Approval', 'Purchase Manager'),
    'Sales Order': ('P0 Sales Order Approval', 'Sales Manager'),
    'Payment Entry': ('P0 Payment Entry Approval', 'Accounts Manager'),
}
FIELDS = ('read','write','create','submit','cancel','delete','amend','share','export','print','email','report')
MASTERS = ('Company','Warehouse','Account','Cost Center','Currency','Item','Item Group','UOM','Supplier','Supplier Group','Customer','Customer Group','Address','Contact','Price List','Item Price','Payment Term','Payment Terms Template','Purchase Taxes and Charges Template','Sales Taxes and Charges Template','Tax Category','Mode of Payment','Fiscal Year','Stock Entry Type','Workflow State','Workflow Action Master')


def workflow_spec(dt, config):
    company = repr(config['company'])
    prefix = f'doc.company == {company} and doc.owner != frappe.session.user'
    independent = prefix + ' and doc.modified_by != frappe.session.user'
    r = lambda who: config['users'][who]['role']
    maker, manager = TYPES[dt]
    states = [dict(state='Pending',doc_status='0',allow_edit='All'),
              dict(state='Approved',doc_status='1',allow_edit=r(manager)),
              dict(state='Rejected',doc_status='2',allow_edit=r(manager))]
    transitions = []
    def state(name,status,who):
        states.append(dict(state=name,doc_status=str(status),allow_edit=r(who)))
    def transition(start,action,end,who,condition=prefix):
        transitions.append(dict(state=start,action=action,next_state=end,allowed=r(who),condition=condition,allow_self_approval=0))
    if dt in ('Purchase Order','Sales Order','Payment Entry'):
        threshold = config['payment_threshold'] if dt == 'Payment Entry' else config['order_threshold']
        low = f'-{threshold} <= doc.paid_amount <= {threshold} and -{threshold} <= doc.received_amount <= {threshold}' if dt == 'Payment Entry' else f'0 <= doc.grand_total <= {threshold}'
        high = f'(doc.paid_amount < -{threshold} or doc.paid_amount > {threshold} or doc.received_amount < -{threshold} or doc.received_amount > {threshold})' if dt == 'Payment Entry' else f'doc.grand_total > {threshold}'
        state('待负责人复核',0,'owner')
        transition('Pending','批准','Approved',manager,prefix + ' and ' + low)
        transition('Pending','转负责人复核','待负责人复核',manager,prefix + ' and ' + high)
        transition('待负责人复核','负责人批准','Approved','owner',independent + ' and ' + high)
        transition('Approved','撤销','Rejected',manager)
    elif dt in ('Purchase Receipt','Delivery Note'):
        business = 'purchase_manager' if dt == 'Purchase Receipt' else 'sales_manager'
        state('待业务经理复核',0,business);state('待财务复核',0,'finance_reviewer')
        transition('Pending','批准','Approved',manager,prefix+' and not doc.is_return')
        transition('Pending','退货库存复核','待业务经理复核',manager,prefix+' and doc.is_return and doc.return_against')
        transition('待业务经理复核','业务复核','待财务复核',business,independent)
        transition('待财务复核','财务批准','Approved','finance_reviewer',independent)
    else:
        state('待财务复核',0,'finance_reviewer')
        if dt == 'Stock Entry':
            transition('Pending','批准','Approved',manager,prefix+' and doc.purpose == "Material Transfer"')
            transition('Pending','转财务复核','待财务复核',manager,prefix+' and doc.purpose != "Material Transfer"')
        else:
            transition('Pending','转财务复核','待财务复核',manager)
        transition('待财务复核','财务批准','Approved','finance_reviewer',independent)
    if dt not in ('Purchase Order','Sales Order','Payment Entry'):
        business = ('purchase_manager' if dt in ('Purchase Receipt','Purchase Invoice') else
                    'sales_manager' if dt in ('Delivery Note','Sales Invoice') else 'stock_manager')
        state('待财务撤销复核',1,'finance_reviewer')
        transition('Approved','申请撤销','待财务撤销复核',business)
        transition('待财务撤销复核','财务撤销','Rejected','finance_reviewer',independent)
    # Reviewers can return intermediate drafts; edits require maker resubmission.
    for row in states:
        if row['doc_status']=='0' and row['state']!='Pending':
            transitions.append(dict(state=row['state'],action='退回重填',next_state='Pending',allowed=row['allow_edit'],condition=prefix,allow_self_approval=0))
    # Keep legacy synthetic branches and already-submitted P0 documents compatible.
    name, legacy_role = LEGACY.get(dt, (f'R1 {dt} Approval','System Manager'))
    outside = f'doc.company == {repr("Phase Zero Hardware Trading Demo")}'
    transitions += [dict(state='Pending',action='Approve',next_state='Approved',allowed=legacy_role,condition=outside,allow_self_approval=0),
                    dict(state='Approved',action='Reject',next_state='Rejected',allowed=legacy_role,condition=outside,allow_self_approval=0)]
    return dict(workflow_name=name,document_type=dt,is_active=1,send_email_alert=0,
                workflow_state_field='workflow_state',states=states,transitions=transitions)


def permission_spec(dt, who):
    maker, manager = TYPES[dt]
    read = who in {maker,manager,'finance_reviewer','owner'}
    if who == 'stock_manager' and dt in ('Purchase Order','Sales Order','Purchase Receipt','Delivery Note'):
        read = True
    if who == 'purchase_manager' and dt in ('Purchase Receipt','Purchase Invoice'):
        read = True
    if who == 'sales_manager' and dt in ('Delivery Note','Sales Invoice'):
        read = True
    # Stock makers need submitted source orders; finance makers need invoice/order links.
    if who == 'stock' and dt in ('Purchase Order','Sales Order','Purchase Receipt','Delivery Note'):
        read = True
    if who == 'finance' and dt in ('Purchase Order','Sales Order','Purchase Receipt','Delivery Note'):
        read = True
    approver = who == manager or (who == 'owner' and dt in LEGACY) or (who=='finance_reviewer' and dt not in ('Purchase Order','Sales Order'))
    if who=='purchase_manager' and dt=='Purchase Receipt': approver=True
    if who=='sales_manager' and dt=='Delivery Note': approver=True
    return dict(read=int(read),write=int(who==maker or approver),create=int(who==maker),
                submit=int(approver),cancel=int(approver),delete=0,amend=int(who==maker),
                share=0,export=0,print=int(read),email=0,report=int(read))


def subset(actual, expected):
    if isinstance(expected,dict): return isinstance(actual,dict) and all(subset(actual.get(k),v) for k,v in expected.items())
    if isinstance(expected,list): return isinstance(actual,list) and len(actual)==len(expected) and all(subset(a,e) for a,e in zip(actual,expected))
    return actual==expected


def configure(api,config,apply):
    if config['company']!='R1合成发布验证公司' or any(not row['email'].endswith('@example.invalid') or not row['role'].startswith('R1') for row in config['users'].values()):
        raise ValueError('Synthetic namespace required')
    changes=[]
    def ensure(dt,name,payload):
        doc=api.get_doc(dt,name) if name else None
        if doc is not None and subset(doc,payload): return doc
        if not apply: raise ValueError(f'Missing/drifted {dt}: {name}')
        if doc is None: result=api.insert(dt,payload)
        else: result=api.update(dt,name,payload)
        if not subset(result,payload): raise ValueError(f'Readback mismatch: {dt} {name}')
        changes.append(f'{dt}:{name}');return result
    for who,row in config['users'].items():
        ensure('Role',row['role'],dict(role_name=row['role'],desk_access=1,is_custom=1))
        current=api.get_doc('User',row['email'])
        payload=dict(email=row['email'],first_name='首版'+row['role'][2:],language='zh',enabled=1,user_type='System User',send_welcome_email=0)
        expected_roles={row['role']}
        if current and {r['role'] for r in current.get('roles',[])}!=expected_roles:
            raise ValueError(f'Unexpected roles for {row["email"]}; refuse overwrite')
        if not current:
            if not apply: raise ValueError(f'Missing User {row["email"]}')
            payload['roles']=[{'role':row['role']}]
            payload['new_password']=os.environ.get('PHASE0_ROLE_PASSWORD','p0-local-only')
            api.insert('User',payload);changes.append('User:'+row['email'])
        else: ensure('User',row['email'],payload)
        # Explicit company restriction applies to every linked company field.
        for allow,value in [('Company',config['company'])]+([('Warehouse',w) for w in config['warehouses']] if who in ('stock','stock_manager') else []):
            found=api.list_docs('User Permission',['name'],[['user','=',row['email']],['allow','=',allow],['for_value','=',value]])
            payload=dict(user=row['email'],allow=allow,for_value=value,apply_to_all_doctypes=1)
            ensure('User Permission',found[0]['name'] if found else '',payload)
    for row in json.loads((ROOT/'phase0/access-validation.json').read_text())['users'].values():
        # The long-lived discovery site has P0 users that still need their
        # original company boundary.  A clean release site intentionally does
        # not recreate those historical fixtures.
        if not api.get_doc('User',row['email']):
            continue
        found=api.list_docs('User Permission',['name'],[['user','=',row['email']],['allow','=','Company'],['for_value','=','Phase Zero Hardware Trading Demo']])
        ensure('User Permission',found[0]['name'] if found else '',dict(user=row['email'],allow='Company',for_value='Phase Zero Hardware Trading Demo',apply_to_all_doctypes=1))
    # Native custom permission manager copies original rules before adding ours.
    for dt in (*TYPES,*MASTERS):
        existing=api.call(PERM_METHOD+'.get_permissions',{'doctype':dt})
        for who,row in config['users'].items():
            wanted=permission_spec(dt,who) if dt in TYPES else dict(read=1,write=0,create=0,submit=0,cancel=0,delete=0,amend=0,share=0,export=0,print=0,email=0,report=0)
            if not wanted['read']: continue
            found=[p for p in existing if p['role']==row['role'] and int(p['permlevel'])==0]
            if not found:
                if not apply: raise ValueError(f'Missing permission {dt}/{row["role"]}')
                api.call(PERM_METHOD+'.add',{'parent':dt,'role':row['role'],'permlevel':0})
                existing=api.call(PERM_METHOD+'.get_permissions',{'doctype':dt})
                found=[p for p in existing if p['role']==row['role'] and int(p['permlevel'])==0]
            if not subset(found[0],wanted): ensure('Custom DocPerm',found[0]['name'],wanted)
    for dt in TYPES:
        if not api.get_doc('DocType',dt).get('track_changes'):
            ensure('Property Setter',dt+'-main-track_changes',dict(doctype_or_field='DocType',doc_type=dt,property='track_changes',property_type='Check',value='1'))
        wanted=workflow_spec(dt,config)
        for state in wanted['states']:
            if not api.get_doc('Workflow State',state['state']):
                if not apply: raise ValueError('Missing Workflow State '+state['state'])
                api.insert('Workflow State',{'workflow_state_name':state['state']});changes.append('Workflow State:'+state['state'])
        for action in sorted({t['action'] for t in wanted['transitions']}):
            if not api.get_doc('Workflow Action Master',action):
                if not apply: raise ValueError('Missing Workflow Action '+action)
                api.insert('Workflow Action Master',{'workflow_action_name':action});changes.append('Workflow Action:'+action)
        ensure('Workflow',wanted['workflow_name'],wanted)
    audit=api.get_doc('Log Settings','Log Settings')
    retained={'Version','Comment','Permission Log'}
    if any(row.get('ref_doctype') in retained and int(row.get('days') or 0)>0 for row in audit.get('logs_to_clear',[])):
        raise ValueError('Business approval/configuration audit must not be automatically purged')
    return {'company':config['company'],'roles':len(config['users']),'workflows':len(TYPES),'audit_retention':'NO_AUTOMATIC_BUSINESS_AUDIT_PURGE','changed':changes}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
    validate_disposable_url(url)
    api=ERPNextAPI(url);api.login('Administrator',os.environ.get('PHASE0_PASSWORD','admin'))
    print(json.dumps(configure(api,json.loads(CONFIG.read_text()),args.apply),ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
