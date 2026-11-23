"""Replay the fixed M1 synthetic batch on a dedicated, otherwise empty R1 site only."""
from decimal import Decimal
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import time

from phase0_api import ERPNextAPI

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "phase0/migration"
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ("scripts/phase0-" + name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

preflight = module("preflight-migration")
report = module("export-opening")
ROLES = json.loads((ROOT / "phase0/release-access.json").read_text())["users"]
DOCTYPES = ["Stock Reconciliation", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"]


def detail_rows(detail, section):
    data = detail[section]
    return data if isinstance(data, list) else [data]


def invoices(detail):
    for kind, section in (("ar","receivable"), ("ap","payable")):
        for index, row in enumerate(detail_rows(detail, section)):
            yield kind, (kind if index == 0 else f"{kind}_{index+1}"), row


def positive(value):
    amount = Decimal(str(value))
    if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal(".01")):
        raise ValueError("演练金额或数量无效")
    return amount


def stock_line(cfg, row):
    factor = positive(row.get("factor", 1))
    unit = cfg["units"][row.get("stock_unit",row["unit"])]
    quantity = positive(row["quantity"]) * factor
    rate = positive(row["unit_cost"]) / factor
    if quantity != quantity.to_integral_value() or rate != rate.quantize(Decimal(".01")):
        raise ValueError("换算后数量或单价精度异常")
    return (cfg["stock"][row["item"]],cfg["warehouses"][row["warehouse"]],unit,quantity,rate)


def validate_details(cfg, detail, source):
    if detail["batch"] != "M1-DEMO-" + cfg["cutoff"].replace("-",""):
        raise ValueError("批次或截止日不符")
    co = cfg["company"]
    details = {}
    for row in detail_rows(detail, "stock"):
        item, warehouse, unit, qty, rate = stock_line(cfg, row)
        identity = ("stock",co,item,warehouse,unit)
        if identity in details:
            raise ValueError("库存明细重复")
        details[identity] = {"quantity":qty,"amount":qty*rate}
    refs = set()
    cash_net = Decimal(0)
    for kind, _, row in invoices(detail):
        for ref in (row["ref"],row["payment_ref"]):
            if not ref.startswith("M1-DEMO-") or ref in refs:
                raise ValueError("外部单号重复或超出演练范围")
            refs.add(ref)
        settled = positive(row["settled"])
        remaining = positive(row["gross"]) - settled
        if remaining <= 0:
            raise ValueError("未结发票必须有未结余额")
        cash_net += settled if kind == "ar" else -settled
        key = (kind,co,cfg[kind][row["party"]],"","")
        details.setdefault(key,{"amount":Decimal(0)})["amount"] += remaining
    if details != {k:v for k,v in source.items() if k[0]!="gl"} or cash_net:
        raise ValueError("来源库存、未结发票或净收付控制与样例不符")


def specifications(cfg, detail, company, temp):
    center = company["cost_center"]
    base = dict(company=cfg["company"], posting_date=cfg["cutoff"], set_posting_time=1)
    items = []
    for row in detail_rows(detail,"stock"):
        item, warehouse, _, qty, rate = stock_line(cfg,row)
        items.append(dict(item_code=item,warehouse=warehouse,qty=float(qty),valuation_rate=float(rate)))
    yield ("stock","Stock Reconciliation","stock","stock_manager",
           dict(base,purpose="Opening Stock",expense_account=temp,cost_center=center,items=items))
    for kind, key, row in invoices(detail):
        if kind=="ar":
            dt,manager,party,ref,account = "Sales Invoice","sales_manager","customer","po_no","income_account"
        else:
            dt,manager,party,ref,account = "Purchase Invoice","purchase_manager","supplier","bill_no","expense_account"
        yield (key,dt,"finance",manager,dict(base,is_opening="Yes",currency="CNY",disable_rounded_total=1,
               update_stock=0,due_date=cfg["cutoff"],**{party:cfg[kind][row["party"]],ref:row["ref"]},
               items=[dict(item_name="合成期初未结单",description=row["ref"],qty=1,rate=row["gross"],
                           uom="Piece",conversion_factor=1,cost_center=center,**{account:temp})]))


def check_subset(doc, wanted):
    if isinstance(wanted, dict):
        return isinstance(doc, dict) and all(check_subset(doc.get(k), v) for k,v in wanted.items())
    if isinstance(wanted, list):
        return isinstance(doc, list) and len(doc)==len(wanted) and all(check_subset(d,w) for d,w in zip(doc,wanted))
    return doc == wanted


def run(port, apply, stop_after, expanded=False):
    cfg = json.loads((FIX / ("mapping-expanded.json" if expanded else "mapping-clean-site.json")).read_text())
    source = preflight.prepare(cfg, FIX / ("opening-expanded.csv" if expanded else "opening-mapping-example.csv"))
    detail = json.loads((FIX / ("vouchers-expanded.json" if expanded else "opening-vouchers-example.json")).read_text())
    validate_details(cfg, detail, source)
    co, cutoff = cfg["company"], cfg["cutoff"]
    url = "http://localhost:" + str(port)
    admin = ERPNextAPI(url)
    admin.login("Administrator", os.environ.get("PHASE0_PASSWORD", "admin"))
    if admin.list_docs("Company", ["name"], [], 2) != [{"name":co}]:
        raise ValueError("需要独立的单一合成公司站点")
    preflight.check_native(admin, cfg, source)
    for row in detail_rows(detail, "stock"):
        item, _, unit, _, _ = stock_line(cfg, row)
        doc = admin.get_doc("Item", item)
        native_factors = {r["uom"]:Decimal(str(r["conversion_factor"])) for r in doc["uoms"]}
        if doc["stock_uom"] != unit or native_factors.get(cfg["units"][row["unit"]]) != Decimal(str(row.get("factor",1))):
            raise ValueError("来源包装换算与 ERP 商品单位不符")
    company = admin.get_doc("Company", co)
    temps = admin.list_docs("Account", ["name"], [["company","=",co],["account_type","=","Temporary"],["is_group","=",0]],2)
    if len(temps)!=1:
        raise ValueError("期初过渡科目不唯一")
    temp = temps[0]["name"]
    roles = {"admin":admin}
    def session(who):
        if who not in roles:
            roles[who] = ERPNextAPI(url)
            roles[who].login(ROLES[who]["email"], os.environ.get("PHASE0_ROLE_PASSWORD","p0-local-only"))
        return roles[who]

    docs = {}
    seen = {}
    ref_fields = {"Payment Entry":"reference_no", "Sales Invoice":"po_no",
                  "Purchase Invoice":"bill_no", "Journal Entry":"user_remark"}
    expected_refs = {dt:set() for dt in DOCTYPES}
    expected_refs["Stock Reconciliation"].add(None)
    expected_refs["Journal Entry"].add(detail["batch"])
    for kind, _, row in invoices(detail):
        expected_refs["Sales Invoice" if kind=="ar" else "Purchase Invoice"].add(row["ref"])
        expected_refs["Payment Entry"].add(row["payment_ref"])
    for dt in DOCTYPES:
        field = ref_fields.get(dt)
        rows = admin.list_docs(dt, ["name",field] if field else ["name"], [], len(expected_refs[dt])+1)
        for row in rows:
            key = dt,row.get(field)
            if key in seen or key[1] not in expected_refs[dt]:
                raise ValueError("站点有重复或批次外单据：" + dt)
            seen[key] = admin.get_doc(dt,row["name"])
    if not seen:
        before, _, _ = report.collect(admin, cfg)
        if any(any(v.values()) for v in before.values()):
            raise ValueError("新批次需要零余额起点")
    n_created = 0
    def ensure(key, dt, maker, manager, body):
        nonlocal n_created
        doc = seen.get((dt, body.get(ref_fields.get(dt))))
        if doc is None:
            if not apply:
                raise ValueError("尚缺期初单据：" + key)
            doc = session(maker).insert(dt,body)
            n_created += 1
        expected = dict(body)
        expected.pop("set_posting_time", None)
        if not check_subset(doc, expected) or doc["owner"] != ("Administrator" if maker=="admin" else ROLES[maker]["email"]) or doc["docstatus"]==2:
            raise ValueError("原生单据与批次引用或业务字段不一致：" + key)
        if dt in ("Sales Invoice","Purchase Invoice") and (doc["grand_total"]!=body["items"][0]["rate"] or doc.get("taxes")):
            raise ValueError("原生期初发票金额或税额异常")
        if doc["docstatus"]==0 and not apply:
            raise ValueError("存在未完成审批：" + key)
        if dt == "Journal Entry":
            if doc["docstatus"]==0:
                admin.submit(doc)  # isolated migration-only closing voucher, no R1 workflow for JE
        else:
            while doc["docstatus"]==0:
                state = doc["workflow_state"]
                if state=="Pending" and dt=="Payment Entry":
                    actor, action, dest = manager, "批准", "Approved"
                elif state=="Pending":
                    actor, action, dest = manager, "转财务复核", "待财务复核"
                elif state=="待财务复核":
                    actor, action, dest = "finance_reviewer", "财务批准", "Approved"
                else:
                    raise ValueError("批次草稿状态冲突")
                session(actor).call("frappe.model.workflow.apply_workflow", {"doc":doc,"action":action})
                for _ in range(75):
                    doc = admin.get_doc(dt,doc["name"])
                    if doc["workflow_state"]==dest:
                        break
                    time.sleep(.2)
                else:
                    raise ValueError("审批返回状态未知，停止并在重试时回读")
        doc = admin.get_doc(dt,doc["name"])
        if doc["docstatus"] != 1:
            raise ValueError("未完成原生过账")
        docs[key] = doc
        print(key, dt, doc["name"], flush=True)
        if stop_after==key:
            raise SystemExit("预定演练中断：已过账，下一轮从 ERP 回读")
    for spec in specifications(cfg,detail,company,temp):
        ensure(*spec)
    for kind, key, row in invoices(detail):
        inv, incoming = docs[key], kind=="ar"
        amount = row["settled"]
        trade = inv["debit_to" if incoming else "credit_to"]
        cash = company["default_cash_account"]
        ensure(key+"_payment", "Payment Entry","finance","finance_reviewer",
               dict(company=co, posting_date=cutoff, reference_date=cutoff, reference_no=row["payment_ref"],
                    payment_type="Receive" if incoming else "Pay", party_type="Customer" if incoming else "Supplier",
                    party=cfg[kind][row["party"]], paid_from=trade if incoming else cash,
                    paid_to=cash if incoming else trade, paid_amount=amount, received_amount=amount,
                    source_exchange_rate=1,target_exchange_rate=1,
                    references=[dict(reference_doctype=inv["doctype"],reference_name=inv["name"],allocated_amount=amount)]))
    equity=cfg["gl"]["期初权益"]
    amount=source["gl",co,equity,"",""]["credit"]
    ensure("equity", "Journal Entry", "admin", None,
           dict(company=co, posting_date=cutoff, is_opening="Yes", voucher_type="Opening Entry",
                user_remark=detail["batch"],accounts=[dict(account=temp,debit_in_account_currency=float(amount)),
                                                      dict(account=equity,credit_in_account_currency=float(amount))]))
    for _, key, row in invoices(detail):
        inv = admin.get_doc(docs[key]["doctype"],docs[key]["name"])
        if Decimal(str(inv["outstanding_amount"])) != positive(row["gross"])-positive(row["settled"]):
            raise ValueError("原生未结发票回读金额不符")
    target, _, _ = report.collect(admin, cfg)
    if target!=source:
        raise ValueError("过账后原生四表与独立来源不符")
    print(json.dumps({"submitted":len(docs),"created":n_created,"reconciled_rows":len(target),"cutoff":cutoff}))


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,choices=(18082,18083),required=True)
    p.add_argument("--expanded",action="store_true",help="两仓、多单位、多发票的十一月合成批次")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--stop-after",choices=("stock","ar","ap","ar_payment","ap_payment"))
    args=p.parse_args()
    # Single local writer per site, including interrupted-response recovery runs.
    import tempfile
    with (Path(tempfile.gettempdir()) / f"m1-opening-{args.port}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args.port,args.apply,args.stop_after,args.expanded)
