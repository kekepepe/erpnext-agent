#!/usr/bin/env python3
"""Apply/verify isolated N1 synthetic native configuration, never production data.

All calls use reviewed native REST boundaries. No SQL, core edit, global default
change, submitted transaction, migration or permission change.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from phase0_api import ERPNextAPI

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'phase0/release-baseline.json'


def subset(actual, expected):
    if isinstance(expected, dict):
        return all(key in actual and subset(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(subset(a, e) for a, e in zip(actual, expected))
    return actual == expected


def configure(api, config, apply=False):
    company = config['company']['company_name']
    suffix = ' - ' + config['company']['abbr']
    if company != 'R1合成发布验证公司' or suffix != ' - R1D':
        raise ValueError('Only the isolated R1 synthetic namespace is permitted')
    created = []

    def ensure(dt, name, payload):
        current = api.get_doc(dt, name)
        if current is None:
            if not apply:
                raise ValueError(f'Missing {dt}: {name}; apply the reviewed synthetic fixture first')
            current = api.insert(dt, payload)
            if current['name'] != name:
                raise ValueError(f'Unexpected native name for {dt}: {current["name"]}')
            created.append(dt + ': ' + name)
        if not subset(current, payload):
            raise ValueError(f'Conflicting existing configuration: {dt} {name}; refusing overwrite')
        return current

    c = ensure('Company', company, config['company'])
    settings = api.get_doc('System Settings', 'System Settings')
    wanted_language = config['system']['language']
    wanted_time_zone = config['system']['time_zone']
    if not settings:
        raise ValueError('Missing native System Settings')
    wanted_system = {'language': wanted_language, 'time_zone': wanted_time_zone}
    missing_system = {key: value for key, value in wanted_system.items() if not settings.get(key)}
    conflicts = {
        key: settings.get(key)
        for key, value in wanted_system.items()
        if settings.get(key) and settings.get(key) != value
    }
    if conflicts:
        raise ValueError('Conflicting native System Settings; refusing overwrite: '+json.dumps(conflicts,ensure_ascii=False,sort_keys=True))
    if missing_system:
        if not apply:
            raise ValueError('Missing native System Settings baseline; apply the reviewed synthetic baseline first')
        # A fresh site has both mandatory fields empty.  Save them together so
        # native DocType validation never observes a partially configured row.
        api.update('System Settings', 'System Settings', missing_system)
        created.append('System Settings: '+','.join(key+'='+value for key,value in sorted(missing_system.items())))
    global_defaults = api.get_doc('Global Defaults', 'Global Defaults')
    wanted_currency = config['global_defaults']['default_currency']
    if not global_defaults:
        raise ValueError('Missing native Global Defaults')
    if global_defaults.get('default_currency') != wanted_currency:
        companies = api.list_docs('Company',['name'],[],100)
        if {row['name'] for row in companies} != {company}:
            raise ValueError('Conflicting global currency with non-R1 companies; refusing overwrite')
        if not apply:
            raise ValueError('Global default currency is not the reviewed R1 baseline')
        api.update('Global Defaults','Global Defaults',{'default_currency':wanted_currency})
        created.append('Global Defaults: default_currency='+wanted_currency)
    # Reuse a covering annual fiscal year read-only; do not rewrite shared years.
    years = api.list_docs('Fiscal Year', ['name'], [['year_start_date', '=', config['fiscal_start']], ['year_end_date', '=', config['fiscal_end']], ['disabled', '=', 0]], 100)
    covering = []
    for year in years:
        doc = api.get_doc('Fiscal Year', year['name'])
        companies = {row['company'] for row in doc.get('companies', [])}
        if not companies or company in companies:
            covering.append(year['name'])
    if not covering:
        year = ensure('Fiscal Year', 'R1合成财年2026', {'year':'R1合成财年2026','year_start_date':config['fiscal_start'],'year_end_date':config['fiscal_end'],'disabled':0,'companies':[{'company':company}]})
        covering = [year['name']]

    warehouses = [ensure('Warehouse', name + suffix, {'warehouse_name':name,'company':company,'is_group':0,'disabled':0})['name'] for name in config['warehouses']]
    # Native company creation may create extra unused warehouse leaves. Disable
    # only its generated leaves after proving they are empty; never delete them.
    extras = api.list_docs('Warehouse', ['name','is_group','disabled'], [['company','=',company]], 100)
    for row in extras:
        if row['name'] in warehouses or row['is_group'] or row.get('disabled'):
            continue
        if api.list_docs('Stock Ledger Entry',['name'],[['warehouse','=',row['name']]],1):
            raise ValueError('Unexpected ledger in autogenerated R1 warehouse; stop')
        if not apply:
            raise ValueError('Unexpected enabled R1 warehouse: '+row['name'])
        api.update('Warehouse',row['name'],{'disabled':1})
        created.append('disabled empty native warehouse: '+row['name'])

    accounts = api.list_docs('Account',['name','root_type','account_type','is_group','account_currency'],[['company','=',company]],500)
    account_names = {row['name']:row for row in accounts}
    for field, kind in [('default_receivable_account','Receivable'),('default_payable_account','Payable')]:
        value = c.get(field)
        if value not in account_names or account_names[value]['account_type'] != kind:
            raise ValueError('Missing valid native company account '+field)
    if not c.get('stock_received_but_not_billed') or not c.get('stock_adjustment_account'):
        raise ValueError('Perpetual inventory default accounts are missing')
    tax_groups = [a for a in accounts if a['is_group'] and a['account_type']=='Tax']
    if len(tax_groups)!=1:
        raise ValueError('Expected one native Tax account group; inspect chart before continuing')
    tax_account = ensure('Account','R1合成税费'+suffix,{'account_name':'R1合成税费','company':company,'parent_account':tax_groups[0]['name'],'account_type':'Tax','is_group':0})['name']
    tax_templates = {}
    for dt, direction in [('Sales Taxes and Charges Template','销售'),('Purchase Taxes and Charges Template','采购')]:
        for inclusive in (0,1):
            title = 'R1合成'+direction+('含税' if inclusive else '未税')
            row = {'charge_type':'On Net Total','account_head':tax_account,'description':'仅合成计算税费，不是生产税率','rate':config['synthetic_tax_rate'],'included_in_print_rate':inclusive}
            if direction=='采购': row.update({'category':'Total','add_deduct_tax':'Add'})
            payload = {'title':title,'company':company,'disabled':0,'is_default':0,'taxes':[row]}
            tax_templates[direction+str(inclusive)] = ensure(dt,title+suffix,payload)['name']

    ensure('Item Group', config['item']['item_group'], {'item_group_name':config['item']['item_group'],'parent_item_group':'All Item Groups','is_group':0})
    for uom in config['item']['uoms']:
        ensure('UOM',uom['uom'],{'uom_name':uom['uom'],'must_be_whole_number':1})
    ensure('Item',config['item']['item_code'],config['item'])
    terms = ensure('Payment Term','R1合成30天账期',{'payment_term_name':'R1合成30天账期','invoice_portion':100,'due_date_based_on':'Day(s) after invoice date','credit_days':config['credit_days']})['name']
    term_template = ensure('Payment Terms Template','R1合成30天账期模板',{'template_name':'R1合成30天账期模板','terms':[{'payment_term':terms,'invoice_portion':100,'due_date_based_on':'Day(s) after invoice date','credit_days':config['credit_days']}]})['name']
    ensure('Supplier',config['supplier'],{'supplier_name':config['supplier'],'supplier_type':'Company','supplier_group':'All Supplier Groups','country':'China','default_currency':'CNY','payment_terms':term_template})
    ensure('Customer Group','R1合成客户组',{'customer_group_name':'R1合成客户组','parent_customer_group':'All Customer Groups','is_group':0})
    ensure('Customer',config['customer'],{'customer_name':config['customer'],'customer_type':'Company','customer_group':'R1合成客户组','territory':'China','default_currency':'CNY','payment_terms':term_template,'credit_limits':[{'company':company,'credit_limit':config['credit_limit'],'bypass_credit_limit_check':0}]})
    for direction, name, rate in [('buying',config['buying_price_list'],config['buying_rate']),('selling',config['selling_price_list'],config['selling_rate'])]:
        ensure('Price List',name,{'price_list_name':name,'currency':'CNY','enabled':1,'buying':int(direction=='buying'),'selling':int(direction=='selling')})
        rows=api.list_docs('Item Price',['name'],[['item_code','=',config['item']['item_code']],['price_list','=',name],['uom','=','Piece']],100)
        if len(rows)>1: raise ValueError('Duplicate synthetic item price')
        payload={'item_code':config['item']['item_code'],'price_list':name,'uom':'Piece','currency':'CNY','price_list_rate':rate}
        if rows:
            if not subset(api.get_doc('Item Price',rows[0]['name']),payload): raise ValueError('Conflicting item price')
        elif apply:
            created.append('Item Price: '+api.insert('Item Price',payload)['name'])
        else: raise ValueError('Missing synthetic item price')

    print(json.dumps({'company':company,'currency':c['default_currency'],'language':wanted_language,'time_zone':wanted_time_zone,'perpetual_inventory':c['enable_perpetual_inventory'],'fiscal_years':covering,'warehouses':warehouses,'native_accounts':len(accounts),'tax_templates':tax_templates,'customer_credit_limit':config['credit_limit'],'credit_days':config['credit_days'],'created_or_changed':created},ensure_ascii=False,sort_keys=True))
    print('OK: N1 isolated native configuration readback passed; no submitted transaction or P0 balance change')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
    if urlparse(url).hostname not in {'localhost','127.0.0.1'}:
        raise ValueError('Disposable localhost only; no production endpoint')
    config=json.loads(CONFIG.read_text())
    api=ERPNextAPI(url)
    api.login(os.environ.get('PHASE0_USERNAME','Administrator'),os.environ.get('PHASE0_PASSWORD','admin'))
    configure(api,config,args.apply)


if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError) as error:
        print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)
