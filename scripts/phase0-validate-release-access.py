#!/usr/bin/env python3
"""R1 role/approval acceptance on native APIs; readonly unless --exercise.

Synthetic only. Exercise creates/reuses controlled fixtures, preserves negative
check drafts and cancels positive transactions through independent reviewers.
Runtime manifest contains synthetic identifiers, no passwords or private data.
"""
import argparse
import copy
import importlib.util
import json
import os
import time
from datetime import date,timedelta
from pathlib import Path
from phase0_api import ERPNextAPI,validate_disposable_url

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'phase0/release-access.json').read_text())
MANIFEST=Path(os.environ.get('PHASE0_APPROVAL_MANIFEST',ROOT/'phase0/evidence/n2-access-runtime.json')).resolve()
spec=importlib.util.spec_from_file_location('access_config',ROOT/'scripts/phase0-configure-access.py')
config_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(config_module)
COMPANY=CONFIG['company'];WAREHOUSE=CONFIG['warehouses'][0]
TODAY=date.today().isoformat();FUTURE=(date.today()+timedelta(days=7)).isoformat()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exercise',action='store_true');args=parser.parse_args()
    url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
    validate_disposable_url(url)
    admin=ERPNextAPI(url);admin.login('Administrator',os.environ.get('PHASE0_PASSWORD','admin'))
    config_module.configure(admin,CONFIG,False)
    sessions={}
    for who,user in CONFIG['users'].items():
        session=ERPNextAPI(url);session.login(user['email'],os.environ.get('PHASE0_ROLE_PASSWORD','p0-local-only'));sessions[who]=session
    manifest=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'company':COMPANY,'documents':{},'checks':[]}
    if manifest['company']!=COMPANY:raise ValueError('Manifest company conflict')
    checks=[];created=[]
    def save():
        manifest['checks']=checks
        if args.exercise:MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    def deny(label,call,kinds=('PermissionError','ApprovalBoundaryError','WorkflowTransitionError','WorkflowPermissionError')):
        try:call()
        except RuntimeError as error:
            match=next((kind for kind in kinds if kind in str(error)),None)
            if not match:raise
            checks.append({'check':label,'result':'DENIED','error_type':match});return
        raise RuntimeError('Unexpected authorization: '+label)
    def current(key):
        row=manifest['documents'].get(key)
        if not row:return None
        doc=admin.get_doc(row['doctype'],row['name'])
        if not doc or doc['company']!=COMPANY:raise ValueError('Missing or conflicting fixture '+key)
        return doc
    def ensure(key,dt,who,payload):
        doc=current(key)
        if doc:return doc
        if not args.exercise:raise ValueError('Missing acceptance fixture '+key)
        body=payload() if callable(payload) else copy.deepcopy(payload)
        body.pop('name',None);body.update(company=COMPANY)
        doc=sessions[who].insert(dt,body)
        if doc['owner']!=CONFIG['users'][who]['email'] or doc['docstatus']!=0:raise ValueError('Fixture identity mismatch')
        manifest['documents'][key]={'doctype':dt,'name':doc['name'],'owner':doc['owner']};created.append(key);save();return doc
    def act(who,doc,action,target):
        if not args.exercise:raise ValueError('Incomplete approval fixture '+doc['name'])
        result=sessions[who].call('frappe.model.workflow.apply_workflow',{'doc':doc,'action':action})
        if result is None:
            for _ in range(100):
                result=admin.get_doc(doc['doctype'],doc['name'])
                if result['workflow_state']==target:break
                time.sleep(.2)
        if result['workflow_state']!=target:raise ValueError('Unexpected transition outcome '+doc['name'])
        checks.append({'check':action,'doctype':doc['doctype'],'name':doc['name'],'actor':who,'state':target,'docstatus':result['docstatus']})
        return result
    def approve(doc):
        if doc['docstatus']==2:return doc
        dt=doc['doctype'];_,manager=config_module.TYPES[dt]
        while doc['docstatus']==0:
            state=doc['workflow_state']
            if state=='Pending':
                if dt in ('Purchase Order','Sales Order','Payment Entry'):
                    amount=max(abs(doc['paid_amount']),abs(doc['received_amount'])) if dt=='Payment Entry' else doc['grand_total']
                    threshold=CONFIG['payment_threshold'] if dt=='Payment Entry' else CONFIG['order_threshold']
                    action,target=('转负责人复核','待负责人复核') if amount>threshold else ('批准','Approved')
                elif dt in ('Purchase Receipt','Delivery Note'):
                    action,target=('退货库存复核','待业务经理复核') if doc['is_return'] else ('批准','Approved')
                elif dt=='Stock Entry' and doc['purpose']=='Material Transfer':action,target='批准','Approved'
                else:action,target='转财务复核','待财务复核'
                doc=act(manager,doc,action,target)
            elif state=='待负责人复核':doc=act('owner',doc,'负责人批准','Approved')
            elif state=='待业务经理复核':doc=act('purchase_manager' if dt=='Purchase Receipt' else 'sales_manager',doc,'业务复核','待财务复核')
            elif state=='待财务复核':doc=act('finance_reviewer',doc,'财务批准','Approved')
            else:raise ValueError('Unknown pending state '+state)
        return doc
    def cancel(doc):
        if doc['docstatus']==2:return doc
        if doc['docstatus']!=1:raise ValueError('Cannot cancel an unapproved fixture')
        dt=doc['doctype'];_,manager=config_module.TYPES[dt]
        if dt in config_module.LEGACY:return act(manager,doc,'撤销','Rejected')
        business='purchase_manager' if dt in ('Purchase Receipt','Purchase Invoice') else 'sales_manager' if dt in ('Delivery Note','Sales Invoice') else 'stock_manager'
        if doc['workflow_state']=='Approved':doc=act(business,doc,'申请撤销','待财务撤销复核')
        return act('finance_reviewer',doc,'财务撤销','Rejected')
    def order(dt,amount,qty=1,customer='R1审批验证客户'):
        return dict(company=COMPANY,currency='CNY',transaction_date=TODAY,schedule_date=FUTURE,delivery_date=FUTURE,
            supplier='R1合成供应商',customer=customer,buying_price_list='R1合成采购价目表',selling_price_list='R1合成销售价目表',
            items=[dict(item_code='R1-DEMO-SCREW',qty=qty,rate=amount,warehouse=WAREHOUSE,schedule_date=FUTURE,delivery_date=FUTURE)])
    if not admin.get_doc('Customer','R1审批验证客户'):
        if not args.exercise:raise ValueError('Missing isolated threshold-test customer')
        admin.insert('Customer',dict(customer_name='R1审批验证客户',customer_type='Company',customer_group='R1合成客户组',territory='China',default_currency='CNY',credit_limits=[dict(company=COMPANY,credit_limit=100000,bypass_credit_limit_check=0)]))
    # Persistent draft negative fixtures are exercised on every rerun.
    for dt,who,manager,other in [('Purchase Order','purchase','purchase_manager','sales'),('Sales Order','sales','sales_manager','purchase')]:
        for amount in (10000,10000.01):
            key=dt+' boundary '+str(amount)
            doc=ensure(key,dt,who,order(dt,amount))
            if args.exercise and doc['docstatus']!=2:
                deny(key+' maker direct submit',lambda:sessions[who].submit(doc))
                deny(key+' reviewer direct submit',lambda:sessions[manager].submit(doc))
                deny(key+' wrong function approve',lambda:sessions[other].call('frappe.model.workflow.apply_workflow',{'doc':doc,'action':'批准'}))
                doc=approve(doc);doc=cancel(doc)
            if doc['docstatus']!=2:raise ValueError('Boundary fixture not cancelled')
        draft=ensure(dt+' negative draft',dt,who,order(dt,10000))
        if draft['docstatus']!=0:raise ValueError('Negative fixture must remain draft')
        rows=copy.deepcopy(draft['items']);rows[0]['rate']=10000.01
        if args.exercise:
            deny(dt+' mutate during approve',lambda:sessions[manager].update(dt,draft['name'],{'items':rows,'workflow_state':'Approved','docstatus':1}))
            deny(dt+' client save bypass',lambda:sessions[manager].call('frappe.client.save',{'doc':dict(draft,workflow_state='Approved',docstatus=1,items=rows,flags={'ignore_permissions':True,'ignore_validate':True})}))
            deny(dt+' company escape',lambda:sessions[who].update(dt,draft['name'],{'company':'Phase Zero Hardware Trading Demo'}))
            deny(dt+' maker approve',lambda:sessions[who].call('frappe.model.workflow.apply_workflow',{'doc':draft,'action':'批准'}))
            deny(dt+' delete',lambda:sessions[who].request('DELETE',sessions[who].resource_path(dt,draft['name'])))
        after=admin.get_doc(dt,draft['name'])
        if after['grand_total']!=10000 or after['docstatus']!=0:raise ValueError('Negative operation mutated fixture')
    if args.exercise:
        # Even an accidental dual-role assignment must not enable self approval.
        email=CONFIG['users']['purchase']['email'];user=admin.get_doc('User',email)
        original_roles=[{'role':row['role']} for row in user['roles']]
        try:
            admin.update('User',email,{'roles':original_roles+[{'role':CONFIG['users']['purchase_manager']['role']}]})
            dual=ERPNextAPI(url);dual.login(email,os.environ.get('PHASE0_ROLE_PASSWORD','p0-local-only'))
            draft=current('Purchase Order negative draft')
            deny('dual role self approval',lambda:dual.update('Purchase Order',draft['name'],{'workflow_state':'Approved','docstatus':1}))
        finally:admin.update('User',email,{'roles':original_roles})
    credit=ensure('credit limit draft','Sales Order','sales',order('Sales Order',1000.01,customer='R1合成客户'))
    if args.exercise:
        deny('credit limit native block',lambda:sessions['sales_manager'].call('frappe.model.workflow.apply_workflow',{'doc':credit,'action':'批准'}),('信用额度已超过',))
    if admin.get_doc('Sales Order',credit['name'])['docstatus']!=0:raise ValueError('Credit limit unexpectedly submitted')
    returned=ensure('approval return reentry','Purchase Order','purchase',order('Purchase Order',10000.01))
    if args.exercise and returned['docstatus']==0:
        if returned['workflow_state']=='Pending':returned=act('purchase_manager',returned,'转负责人复核','待负责人复核')
        deny('intermediate price editing',lambda:sessions['owner'].update('Purchase Order',returned['name'],{'items':[dict(row,rate=20000) for row in returned['items']]}))
        returned=act('owner',returned,'退回重填','Pending')
        returned=sessions['purchase'].update('Purchase Order',returned['name'],{'items':[dict(row,rate=20000) for row in returned['items']]})
        returned=approve(returned)
    if args.exercise and returned['docstatus']==1:
        forged=dict(returned,items=[dict(row,rate=1) for row in returned['items']])
        deny('cancel content mutation',lambda:sessions['purchase_manager'].update('Purchase Order',returned['name'],{'items':forged['items'],'workflow_state':'Rejected','docstatus':2}))
        returned=cancel(returned)
    if returned['docstatus']!=2:raise ValueError('Return/reentry fixture incomplete')
    company_doc=admin.get_doc('Company',COMPANY)
    def payment(amount):
        return dict(payment_type='Receive',party_type='Customer',party='R1审批验证客户',company=COMPANY,posting_date=TODAY,
            paid_from=company_doc['default_receivable_account'],paid_to=company_doc['default_cash_account'],
            paid_amount=amount,received_amount=amount,source_exchange_rate=1,target_exchange_rate=1,reference_no='R1-N2',reference_date=TODAY)
    for amount in (20000,20000.01):
        doc=ensure('payment boundary '+str(amount),'Payment Entry','finance',payment(amount))
        if args.exercise and doc['docstatus']!=2:
            deny('payment maker direct submit '+str(amount),lambda:sessions['finance'].submit(doc))
            deny('payment reviewer direct submit '+str(amount),lambda:sessions['finance_reviewer'].submit(doc))
            doc=approve(doc);deny('payment direct cancellation '+str(amount),lambda:sessions['finance_reviewer'].cancel(doc));doc=cancel(doc)
        if doc['docstatus']!=2:raise ValueError('Payment fixture not cancelled')
    # Native receiving -> invoice -> shipping -> returns, with separate makers.
    def mapped(who,method,source):
        doc=sessions[who].call(method,{'source_name':source['name']})
        doc.pop('name',None);doc['posting_date']=TODAY
        return doc
    positive_keys=[]
    def flow(key,dt,who,payload):
        doc=ensure(key,dt,who,payload)
        positive_keys.append(key)
        if args.exercise and doc['docstatus']==0:
            deny(key+' maker bypass',lambda:sessions[who].submit(doc))
            doc=approve(doc)
        return doc
    po=flow('flow purchase order','Purchase Order','purchase',order('Purchase Order',60,2))
    pr=flow('flow purchase receipt','Purchase Receipt','stock',lambda:mapped('stock','erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt',po))
    pi=flow('flow purchase invoice','Purchase Invoice','finance',lambda:mapped('finance','erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice',pr))
    so=flow('flow sales order','Sales Order','sales',order('Sales Order',100,1,customer='R1合成客户'))
    dn=flow('flow delivery note','Delivery Note','stock',lambda:mapped('stock','erpnext.selling.doctype.sales_order.sales_order.make_delivery_note',so))
    si=flow('flow sales invoice','Sales Invoice','finance',lambda:mapped('finance','erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice',dn))
    dnr=flow('flow delivery return','Delivery Note','stock',lambda:mapped('stock','erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return',dn))
    sir=flow('flow sales credit','Sales Invoice','finance',lambda:mapped('finance','erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return',si))
    prr=flow('flow purchase return','Purchase Receipt','stock',lambda:mapped('stock','erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return',pr))
    pir=flow('flow purchase debit','Purchase Invoice','finance',lambda:mapped('finance','erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_debit_note',pi))
    se=flow('flow material receipt','Stock Entry','stock',dict(stock_entry_type='Material Receipt',purpose='Material Receipt',posting_date=TODAY,items=[dict(item_code='R1-DEMO-SCREW',qty=2,t_warehouse=WAREHOUSE,basic_rate=60,expense_account=company_doc['stock_adjustment_account'],cost_center=company_doc['cost_center'])]))
    transfer=flow('flow transfer','Stock Entry','stock',dict(stock_entry_type='Material Transfer',purpose='Material Transfer',posting_date=TODAY,items=[dict(item_code='R1-DEMO-SCREW',qty=1,s_warehouse=WAREHOUSE,t_warehouse=CONFIG['warehouses'][1])]))
    sr=flow('flow stock reconciliation','Stock Reconciliation','stock',dict(purpose='Stock Reconciliation',posting_date=TODAY,expense_account=company_doc['stock_adjustment_account'],cost_center=company_doc['cost_center'],items=[dict(item_code='R1-DEMO-SCREW',warehouse=WAREHOUSE,qty=2,valuation_rate=60)]))
    audit_sr=flow('flow stock audit','Stock Reconciliation','stock',dict(purpose='Stock Reconciliation',posting_date=TODAY,expense_account=company_doc['stock_adjustment_account'],cost_center=company_doc['cost_center'],items=[dict(item_code='R1-DEMO-SCREW',warehouse=WAREHOUSE,qty=1,valuation_rate=60)]))
    if args.exercise:
        # Reverse dependencies before originals; preserve all native audit/ledger traces.
        for key in ('flow stock audit','flow stock reconciliation','flow transfer','flow material receipt',
                    'flow purchase debit','flow purchase return','flow sales credit','flow delivery return',
                    'flow sales invoice','flow delivery note','flow sales order',
                    'flow purchase invoice','flow purchase receipt','flow purchase order'):
            doc=current(key)
            if doc['docstatus']==1:
                _,manager=config_module.TYPES[doc['doctype']]
                deny(key+' direct cancel',lambda:sessions[manager].cancel(doc))
                cancel(doc)
    for key in positive_keys:
        if current(key)['docstatus']!=2:raise ValueError('Uncancelled flow fixture '+key)
    for warehouse in CONFIG['warehouses']:
        bins=admin.list_docs('Bin',['actual_qty'],[['item_code','=','R1-DEMO-SCREW'],['warehouse','=',warehouse]],10)
        if any(float(row['actual_qty'])!=0 for row in bins):raise ValueError('Synthetic stock did not return to zero')
    balances={}
    for row in admin.list_docs('GL Entry',['account','debit','credit'],[['company','=',COMPANY]],1000):
        balances[row['account']]=balances.get(row['account'],0)+float(row['debit'])-float(row['credit'])
    if any(round(value,2)!=0 for value in balances.values()):raise ValueError('Synthetic GL did not return to zero per account')
    if args.exercise:
        deny('negative payment amount',lambda:sessions['finance'].insert('Payment Entry',payment(-1)),('ValidationError','NonNegativeError','ApprovalBoundaryError'))
        for who in sessions:
            deny(who+' cross-company read',lambda:sessions[who].get_doc('Company','Phase Zero Hardware Trading Demo'))
            deny(who+' user administration',lambda:sessions[who].update('User','Administrator',{'first_name':admin.get_doc('User','Administrator')['first_name']}))
        deny('stock outside warehouse',lambda:sessions['stock'].get_doc('Warehouse','P0 Main Warehouse - PZH'))
        price=admin.list_docs('Item Price',['name'],[['item_code','=','R1-DEMO-SCREW']],1)[0]['name']
        deny('maker price maintenance',lambda:sessions['purchase'].update('Item Price',price,{'price_list_rate':999}))
    # All submitted probe vouchers retain non-deletable ordinary-user audit.
    for key,row in manifest['documents'].items():
        doc=admin.get_doc(row['doctype'],row['name'])
        if doc['docstatus']==2:
            versions=admin.list_docs('Version',['name'],[['ref_doctype','=',row['doctype']],['docname','=',row['name']]],100)
            comments=admin.list_docs('Comment',['name','owner','creation','content'],[['reference_doctype','=',row['doctype']],['reference_name','=',row['name']],['comment_type','=','Workflow']],100)
            if not versions and not comments:raise ValueError('No approval audit for '+key)
            if key=='flow stock audit' and not versions:raise ValueError('Stock Reconciliation version tracking not active')
            manifest.setdefault('audits',{})[key]={'versions':len(versions),'workflow_comments':comments}
            if args.exercise:
                audit_dt,audit_name=('Version',versions[0]['name']) if versions else ('Comment',comments[0]['name'])
                deny(key+' audit delete',lambda:sessions['purchase'].request('DELETE',sessions['purchase'].resource_path(audit_dt,audit_name)))
    save()
    print(json.dumps({'created':created,'checks':len(checks),'cases':len(manifest['documents']),'manifest':str(MANIFEST)},ensure_ascii=False,sort_keys=True))
    print('OK: R1 boundary approvals, API rejection, isolation and audit checks passed')

if __name__=='__main__':main()
