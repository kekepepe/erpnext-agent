#!/usr/bin/env python3
"""Configure N3 native report roles and business-page onboarding display.

Read-only by default. Never changes standard Report definitions or native roles.
"""
import argparse,json,os
from pathlib import Path
from phase0_api import ERPNextAPI,validate_disposable_url
ROOT=Path(__file__).resolve().parents[1]
REPORTS={'Stock Balance':('stock_manager','Stock Ledger Entry'),'Stock Ledger':('stock_manager','Stock Ledger Entry'),'Purchase Analytics':('purchase_manager',None),'Sales Analytics':('sales_manager',None),'Accounts Receivable':('finance_reviewer','GL Entry'),'Accounts Payable':('finance_reviewer','GL Entry'),'General Ledger':('finance_reviewer','GL Entry')}
METHOD='frappe.core.page.permission_manager.permission_manager'

def configure(api,apply=False):
    config=json.loads((ROOT/'phase0/release-access.json').read_text());changes=[]
    settings=api.get_doc('System Settings','System Settings')
    if settings.get('enable_onboarding'):
        if not apply:raise ValueError('Native onboarding still obscures narrow business pages')
        api.update('System Settings','System Settings',{'enable_onboarding':0})
        changes.append('System Settings:enable_onboarding=0')
    for report,(who,ledger) in REPORTS.items():
        native=api.get_doc('Report',report)
        if native['is_standard']!='Yes':raise ValueError('Native report changed '+report)
        role=config['users'][who]['role']
        existing=api.list_docs('Custom Role',['name'],[['report','=',report]],2)
        if len(existing)>1:raise ValueError('Ambiguous report override '+report)
        document=api.get_doc('Custom Role',existing[0]['name']) if existing else None
        preserved={r['role'] for r in native['roles']}
        if document:preserved|={r['role'] for r in document['roles'] if not r['role'].startswith('R1')}
        wanted=preserved|{role}
        if document is None or {r['role'] for r in document['roles']}!=wanted:
            if not apply:raise ValueError('Missing/drifted report override '+report)
            payload={'report':report,'ref_doctype':native['ref_doctype'],'roles':[{'role':r} for r in sorted(wanted)]}
            if document:api.update('Custom Role',document['name'],payload)
            else:api.insert('Custom Role',payload)
            changes.append(report)
        sources={native['ref_doctype'],ledger}-{None}
        if who=='finance_reviewer':sources.add('Journal Entry')
        for dt in sources:
            permissions=api.call(METHOD+'.get_permissions',{'doctype':dt})
            rows=[p for p in permissions if p['role']==role and p.get('permlevel',0)==0]
            if not rows:
                if not apply:raise ValueError('Missing report source permission '+dt)
                api.call(METHOD+'.add',{'parent':dt,'role':role,'permlevel':0})
                permissions=api.call(METHOD+'.get_permissions',{'doctype':dt})
                rows=[p for p in permissions if p['role']==role and p.get('permlevel',0)==0]
            for row in rows:
                expected={'read':1,'report':1}
                if dt in ('Stock Ledger Entry','GL Entry','Journal Entry'):expected.update(write=0,create=0,submit=0,cancel=0,delete=0,share=0,export=0,email=0)
                if any(row.get(k,0)!=v for k,v in expected.items()):
                    if not apply:raise ValueError('Drifted ledger access '+dt)
                    api.update('Custom DocPerm',row['name'],expected);changes.append(dt+':'+role)
    print(json.dumps({'report_configuration_changes':changes},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
    url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
    validate_disposable_url(url)
    a=ERPNextAPI(url);a.login('Administrator',os.environ.get('PHASE0_PASSWORD','admin'));configure(a,args.apply)
if __name__=='__main__':main()
