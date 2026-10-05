#!/usr/bin/env python3
"""Generate a static source inventory from the pinned Docker image, without DB access."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = '''
import hashlib,json
from pathlib import Path
labels=set();inventory={};doctypes=0
for app in ['frappe','erpnext']:
 root=Path('apps')/app/app
 for path in root.rglob('*'):
  if not path.is_file() or path.suffix not in ['.py','.js','.html','.vue','.json'] or '/public/dist/' in str(path): continue
  data=path.read_bytes();inventory[str(path)]=hashlib.sha256(data).hexdigest()
  if path.suffix!='.json' or '/doctype/' not in str(path): continue
  try: d=json.loads(data)
  except ValueError: continue
  if not isinstance(d,dict) or d.get('doctype')!='DocType': continue
  doctypes+=1
  for field in d.get('fields',[]):
   if field.get('label'): labels.add(field['label'])
   if field.get('fieldtype')=='Select': labels.update(x for x in field.get('options','').split('\\n') if x)
print(json.dumps({'labels':sorted(labels),'source_sha256':inventory,'doctype_files':doctypes},ensure_ascii=False))
'''
result = subprocess.run(
    ['docker','compose','-f',str(ROOT/'phase0/compose.yaml'),'exec','-T','backend','env/bin/python','-c',CODE],
    check=True, capture_output=True, text=True,
)
data = json.loads(result.stdout)
if any('tokens truncated' in label for label in data['labels']):
    raise RuntimeError('Source inventory contains a truncated label')
destination = ROOT/'phase0/localization'
(destination/'source-labels.json').write_text(json.dumps(data['labels'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(destination/'source-inventory.json').write_text(json.dumps({k:v for k,v in data.items() if k!='labels'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'doctype_files':data['doctype_files'],'source_files':len(data['source_sha256']),'labels':len(data['labels'])}))
