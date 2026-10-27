#!/usr/bin/env python3
"""Read-only N3 native report access and ten Chinese PDF exports.

Artifacts remain outside repository. Poppler renders every exported page; human
visual review is required in addition to text/data checks. No authored PDFs.
"""
import argparse,hashlib,importlib.util,json,os,subprocess,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from phase0_api import ERPNextAPI,validate_disposable_url
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',default='/private/tmp/p09-output');args=p.parse_args()
 out=Path(args.output_dir).resolve()
 if out==ROOT or ROOT in out.parents:raise ValueError('Runtime PDFs must remain outside public repository')
 out.mkdir(parents=True,exist_ok=True)
 url=os.environ.get('PHASE0_BASE_URL','http://localhost:8080')
 validate_disposable_url(url)
 a=ERPNextAPI(url);a.login('Administrator',os.environ.get('PHASE0_PASSWORD','admin'))
 reports=load('reports','scripts/phase0-configure-reports.py');reports.configure(a)
 reporting=load('reporting','scripts/phase0-validate-reporting.py')
 config=json.loads((ROOT/'phase0/reporting-validation.json').read_text());config.update(company='R1合成发布验证公司',to_date='2026-12-31',report_date='2026-12-31')
 access=json.loads((ROOT/'phase0/release-access.json').read_text());evidence={'reports':[],'pdfs':[]};seen=set()
 for report,filters in reporting.report_filters(config):
  if report in seen:continue
  seen.add(report);who,_=reports.REPORTS[report];b=ERPNextAPI(url);b.login(access['users'][who]['email'],os.environ.get('PHASE0_ROLE_PASSWORD','p0-local-only'))
  result=b.run_report(report,filters)
  evidence['reports'].append({'report':report,'actor':who,'rows':len(result['result']),'filters':filters})
  foreign=dict(filters,company='Phase Zero Hardware Trading Demo')
  try:foreign_result=b.run_report(report,foreign)
  except RuntimeError as error:
   if 'PermissionError' not in str(error):raise
   outcome='DENIED'
  else:
   # Native reports may return no rows rather than raise under User Permissions.
   for row in reporting.dict_rows(foreign_result):
    if any(row.get(k) for k in ('item_code','voucher_no','party','entity')) or any(float(row.get(k) or 0) for k in ('bal_qty','bal_val','stock_value','debit','credit','outstanding','total')):
     raise ValueError('Cross-company report data exposed '+report)
   outcome='EMPTY'
  evidence['reports'][-1]['cross_company']=outcome
 localize=load('localize','scripts/phase0-localize.py');_,dictionary=localize.dictionary(a)
 for i,dt in enumerate(['Quotation','Purchase Order','Purchase Receipt','Purchase Invoice','Sales Order','Delivery Note','Sales Invoice','Payment Entry','Stock Entry','Stock Reconciliation'],1):
  rows=a.list_docs(dt,['name'],[['company','=','Phase Zero Hardware Trading Demo'],['docstatus','=',1]],1)
  if not rows:raise ValueError('Missing submitted print fixture '+dt)
  doc=a.get_doc(dt,rows[0]['name']);title=dictionary[dt];fmt=title+'（简体中文）'
  q=urllib.parse.urlencode(dict(doctype=dt,name=doc['name'],format=fmt,no_letterhead=1,_lang='zh'))
  with a.opener.open(urllib.request.Request(url+'/api/method/frappe.utils.print_format.download_pdf?'+q),timeout=60) as response:
   data=response.read()
   if response.headers.get_content_type()!='application/pdf' or not data.startswith(b'%PDF-'):raise ValueError('Invalid native PDF '+dt)
  prefix=out/f'{i:02d}';pdf=prefix.with_suffix('.pdf');pdf.write_bytes(data)
  subprocess.run(['pdftotext','-layout',str(pdf),str(prefix.with_suffix('.txt'))],check=True)
  text=prefix.with_suffix('.txt').read_text();compact=unicodedata.normalize('NFKC',''.join(text.split())).translate(str.maketrans({'⻆':'角','⺠':'民','⻛':'风','⻓':'长','㬵':'胶'}))
  expected=[title,doc['name'],'CNY']
  for row in doc.get('items',[]):
   expected.append(dictionary.get(row.get('item_name'),row.get('item_name') or row['item_code']))
   for field in ('warehouse','s_warehouse','t_warehouse'):
    if row.get(field):expected.append(dictionary.get(row[field],row[field]))
   for value in (row.get('qty'),row.get('rate',row.get('basic_rate',row.get('valuation_rate'))),row.get('amount')):
    if value is not None:expected.append(str(float(value)))
  for field in ('grand_total','paid_amount','received_amount','total_amount','difference_amount'):
   if doc.get(field) is not None:expected.append(str(float(doc[field])))
  if doc.get('return_against'):expected.append(doc['return_against'])
  if any(unicodedata.normalize('NFKC',''.join(value.split())) not in compact for value in expected):raise ValueError('PDF data missing '+dt+' '+str([v for v in expected if unicodedata.normalize('NFKC',''.join(v.split())) not in compact]))
  subprocess.run(['pdftoppm','-r','90','-png',str(pdf),str(prefix)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  pages=list(out.glob(f'{i:02d}-*.png'))
  evidence['pdfs'].append({'doctype':dt,'name':doc['name'],'format':fmt,'sha256':hashlib.sha256(data).hexdigest(),'pages':len(pages),'text_data_check':'PASS'})
 (out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'reports':len(evidence['reports']),'pdfs':len(evidence['pdfs']),'pages':sum(v['pages'] for v in evidence['pdfs']),'artifact_dir':str(out)},ensure_ascii=False))
 print('OK: native role report access and PDF text/data checks passed; inspect every rendered page')
if __name__=='__main__':main()
