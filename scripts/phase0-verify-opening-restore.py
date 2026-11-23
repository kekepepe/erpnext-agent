"""Fingerprint the synthetic migration's postings, approvals, users and attachments via native REST."""
import argparse
import hashlib
import json
import os
import importlib.util
import subprocess
from urllib.parse import urlencode
from pathlib import Path
from phase0_api import ERPNextAPI

ROOT = Path(__file__).resolve().parents[1]
CO = "R1合成发布验证公司"
DT = ("Stock Reconciliation","Sales Invoice","Purchase Invoice","Payment Entry","Journal Entry")
INVOICE = "ACC-SINV-2026-00001"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(port, seed_files):
    api = ERPNextAPI(f"http://localhost:{port}")
    api.login("Administrator", os.environ.get("PHASE0_PASSWORD","admin"))
    if api.list_docs("Company", ["name"], [], 2) != [{"name":CO}]:
        raise ValueError("仅支持专用合成站点")
    state = {}
    for dt in DT:
        state[dt]=[]
        for r in api.list_docs(dt, ["name"], [], 10):
            doc = api.get_doc(dt,r["name"])
            if doc["docstatus"]!=1 or doc["company"]!=CO:
                raise ValueError("单据状态或公司不符")
            # compare stored business fields, child allocations, actual workflow actors & timestamps
            fields = ("name","docstatus","owner","modified_by","modified","company","workflow_state",
                      "posting_date","grand_total","outstanding_amount","items","accounts","references",
                      "paid_amount","received_amount","is_opening","expense_account","user_remark")
            saved = {k:doc[k] for k in fields if k in doc}
            versions = api.list_docs("Version", ["name","owner","data","creation"],[["ref_doctype","=",dt],["docname","=",r["name"]]],100)
            saved["versions"]=sorted(versions,key=lambda x:x["name"])
            if dt!="Journal Entry" and not versions:
                raise ValueError("缺少审批审计记录")
            state[dt].append(saved)
        state[dt].sort(key=lambda x:x["name"])
    if [len(state[dt]) for dt in DT] != [1,1,1,2,1]:
        raise ValueError("预期合成批次应为六张单据")
    state["roles"]={}
    users=json.loads((ROOT/"phase0/release-access.json").read_text())["users"]
    for role,u in users.items():
        doc=api.get_doc("User",u["email"])
        roles=sorted(r["role"] for r in doc["roles"])
        if not doc["enabled"] or roles!=[u["role"]]:
            raise ValueError("演练账号或角色漂移")
        state["roles"][role]=roles
    state["files"]={}
    for private in (0,1):
        name=f"m1-restore-{'private' if private else 'public'}.txt"
        body="M1 SYNTHETIC RESTORE CHECK "+str(private)
        filters=[["file_name","=",name],["attached_to_doctype","=","Sales Invoice"],["attached_to_name","=",INVOICE]]
        files=api.list_docs("File",["name","file_url","is_private"],filters,2)
        if not files and seed_files and port==18082:
            api.insert("File",dict(file_name=name,content=body,is_private=private,attached_to_doctype="Sales Invoice",attached_to_name=INVOICE))
            files=api.list_docs("File",["name","file_url","is_private"],filters,2)
        if len(files)!=1 or files[0]["is_private"]!=private:
            raise ValueError("附件归属或公私属性不符")
        url=files[0]["file_url"]
        if not url.startswith("/private/files/" if private else "/files/") or api.get_text(url)!=body:
            raise ValueError("附件内容或位置不符")
        state["files"][name]=dict(files[0],sha256=digest(body.encode()))
    digest_state=digest(json.dumps(state,sort_keys=True,ensure_ascii=False).encode())
    return dict(posted=6,users=len(users),audit_versions=sum(len(d["versions"]) for dt in DT for d in state[dt]),
                files=2,state_sha256=digest_state)


def smoke(pdf_path):
    """Exercise the restored site with real sessions and the native print service."""
    api=ERPNextAPI("http://localhost:18084")
    api.login("Administrator", os.environ.get("PHASE0_PASSWORD","admin"))
    spec=importlib.util.spec_from_file_location("reporting",ROOT/"scripts/phase0-validate-reporting.py")
    reporting=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reporting)
    cfg=json.loads((ROOT/"phase0/reporting-validation.json").read_text())
    cfg.update(company=CO,to_date="2026-10-31",report_date="2026-10-31")
    reports=dict(reporting.report_filters(cfg))
    for name, filters in reports.items():
        api.run_report(name,filters)
    users=json.loads((ROOT/"phase0/release-access.json").read_text())["users"]
    for who,user in users.items():
        role=ERPNextAPI(api.base_url)
        role.login(user["email"],os.environ.get("PHASE0_ROLE_PASSWORD","p0-local-only"))
        if who=="sales":
            try:
                role.get_doc("Purchase Invoice","ACC-PINV-2026-00001")
            except RuntimeError as error:
                if "PermissionError" not in str(error):
                    raise
            else:
                raise ValueError("恢复后销售可越权查看采购发票")
    query=urlencode(dict(doctype="Sales Invoice",name=INVOICE,format="Standard",no_letterhead=1,_lang="zh"))
    with api.opener.open(api.base_url+"/api/method/frappe.utils.print_format.download_pdf?"+query,timeout=60) as response:
        data=response.read()
        if response.headers.get_content_type()!="application/pdf" or not data.startswith(b"%PDF-"):
            raise ValueError("原生 PDF 导出失败")
    with pdf_path.open("xb") as stream:
        stream.write(data)
    text=subprocess.check_output(["pdftotext","-layout",str(pdf_path),"-"],text=True)
    if not all(token in text for token in (INVOICE,"M1-DEMO-SI-01","CNY 19.00")):
        raise ValueError("恢复后 PDF 与合成原单不符")
    return dict(reports=len(reports),role_logins=len(users),sales_read_purchase="DENIED",native_pdf_bytes=len(data))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,choices=(18082,18084),required=True)
    p.add_argument("--seed-files",action="store_true",help="only at source: attach two synthetic text files")
    p.add_argument("--compare",type=Path)
    p.add_argument("--smoke-pdf",type=Path,help="only at restored site: also verify reports, access and native PDF")
    args=p.parse_args()
    if args.smoke_pdf and args.port!=18084:
        p.error("恢复检查只允许在 18084 运行")
    if args.seed_files and args.port!=18082:
        p.error("附件只能写入演练源站")
    result=capture(args.port,args.seed_files)
    if args.compare and json.loads(args.compare.read_text())!=result:
        raise SystemExit("恢复站与备份前原生凭证/审批/身份/文件指纹不一致")
    if args.smoke_pdf:
        result["smoke"]=smoke(args.smoke_pdf)
    print(json.dumps(result))
