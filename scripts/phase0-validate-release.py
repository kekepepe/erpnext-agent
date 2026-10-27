#!/usr/bin/env python3
"""Verify N1 native tax calculation on four isolated drafts; never submit.

Default mode is read-only. --create-drafts creates missing synthetic fixtures
through native REST, rejects duplicates/conflicts and reuses matching drafts.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from phase0_api import ERPNextAPI

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_config',ROOT/'scripts/phase0-configure-release.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def validate(api, config, create=False):
    module.configure(api,config,False)
    company=config['company']['company_name']
    evidence=[]
    for dt,direction,partyfield,party in [('Quotation','销售','party_name',config['customer']),('Purchase Order','采购','supplier',config['supplier'])]:
        for inclusive in (0,1):
            template='R1合成'+direction+('含税' if inclusive else '未税')+' - R1D'
            marker=f'R1-N1 {dt} inclusive={inclusive}; synthetic only'
            names=api.list_docs(dt,['name'],[['company','=',company],[partyfield,'=',party]],100)
            matches=[]
            for row in names:
                doc=api.get_doc(dt,row['name'])
                if doc.get('terms')==marker: matches.append(doc)
            if len(matches)>1: raise ValueError('Duplicate synthetic draft signature')
            amount=105 if inclusive else 100
            if matches: doc=matches[0]
            else:
                if not create: raise ValueError('Missing native tax calculation draft '+marker)
                tax_dt=direction=='销售' and 'Sales Taxes and Charges Template' or 'Purchase Taxes and Charges Template'
                tax=api.get_doc(tax_dt,template)['taxes'][0]
                keys=('charge_type','account_head','description','rate','included_in_print_rate','category','add_deduct_tax')
                payload={'company':company,'currency':'CNY','conversion_rate':1,'transaction_date':'2026-10-09','terms':marker,'taxes_and_charges':template,'taxes':[{k:tax[k] for k in keys if k in tax}], 'items':[{'item_code':config['item']['item_code'],'qty':1,'uom':'Piece','conversion_factor':1,'rate':amount,'warehouse':config['warehouses'][0]+' - R1D'}],partyfield:party}
                if dt=='Quotation': payload.update({'quotation_to':'Customer','selling_price_list':config['selling_price_list'],'ignore_pricing_rule':1})
                else: payload.update({'schedule_date':'2026-10-09','buying_price_list':config['buying_price_list'],'ignore_pricing_rule':1})
                doc=api.insert(dt,payload)
            if doc['docstatus']!=0 or doc['company']!=company or doc['currency']!='CNY' or doc['taxes_and_charges']!=template:
                raise ValueError('Tax fixture identity/status conflict')
            item=doc['items'][0]
            if len(doc['items'])!=1 or item['item_code']!=config['item']['item_code'] or item['qty']!=1 or item['rate']!=amount:
                raise ValueError('Tax fixture item conflict')
            for field,expected in [('net_total',100),('total_taxes_and_charges',5),('grand_total',105)]:
                if round(float(doc[field]),2)!=expected: raise ValueError(f'{dt} {field}: expected {expected}, got {doc[field]}')
            evidence.append({'doctype':dt,'name':doc['name'],'docstatus':doc['docstatus'],'inclusive':inclusive,'net':doc['net_total'],'tax':doc['total_taxes_and_charges'],'gross':doc['grand_total']})
    # N2 preserves cancelled audit/ledger history in this same synthetic company.
    balances={}
    for row in api.list_docs('GL Entry',['account','debit','credit'],[['company','=',company]],1000):
        balances[row['account']]=balances.get(row['account'],0)+float(row['debit'])-float(row['credit'])
    if any(round(value,2) for value in balances.values()):
        raise ValueError('Unexpected active GL balance in isolated configuration company')
    for warehouse in config['warehouses']:
        for row in api.list_docs('Bin',['actual_qty','stock_value'],[['warehouse','=',warehouse+' - R1D']],1000):
            if float(row['actual_qty']) or round(float(row['stock_value']),2):
                raise ValueError('Unexpected active stock balance in isolated configuration company')
    print('TAX '+json.dumps(evidence,ensure_ascii=False,sort_keys=True))
    print('OK: four native tax drafts match 100 net + 5 synthetic tax = 105 gross; cancelled N2 history retained, GL/stock balances zero')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--create-drafts',action='store_true');args=parser.parse_args()
    url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
    if urlparse(url).hostname not in {'localhost','127.0.0.1'}: raise ValueError('Disposable localhost only')
    api=ERPNextAPI(url);api.login(os.environ.get('PHASE0_USERNAME','Administrator'),os.environ.get('PHASE0_PASSWORD','admin'))
    validate(api,json.loads((ROOT/'phase0/release-baseline.json').read_text()),args.create_drafts)


if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError) as error: print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)
