#!/usr/bin/env python3
"""Loopback-only Business API for rehearsing synthetic receipt and shipment drafts."""

import argparse
import json
import re
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4


PREFIX = "/api/business/v1"
FRONTEND = Path(__file__).resolve().parents[1] / "prototypes" / "w6"
ASSETS = {
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
}
COMPANIES = [{"id": "demo-company", "label": "五金演示公司"}]
PARTNERS = {
    "purchase_receipt": [
        {"id": "demo-supplier-01", "label": "合成供应商一"},
        {"id": "demo-supplier-02", "label": "合成供应商二"},
    ],
    "sales_delivery": [
        {"id": "demo-customer-01", "label": "合成客户一"},
        {"id": "demo-customer-02", "label": "合成客户二"},
    ],
}
WAREHOUSES = [
    {"id": "demo-warehouse-main", "label": "合成主仓"},
    {"id": "demo-warehouse-aux", "label": "合成分仓"},
]
PRODUCTS = [
    {"id": "DEMO-BOLT-01", "label": "六角螺栓", "englishName": "Hex bolt",
     "specification": "M8 × 30 mm", "model": "HB-830", "uom": "件"},
    {"id": "DEMO-NUT-01", "label": "六角螺母", "englishName": "Hex nut",
     "specification": "M8", "model": "HN-08", "uom": "件"},
    {"id": "DEMO-CHAIN-01", "label": "不锈钢链条", "englishName": "Stainless steel chain",
     "specification": "Ø 4 mm", "model": "SC-04", "uom": "米"},
]
QUANTITY = re.compile(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,6})?")
DRAFT_ROUTE = re.compile(r"/drafts/(DEMO-[0-9a-f]{32})")
IDEMPOTENCY_KEY = re.compile(r"[A-Za-z0-9._-]{1,128}")


class ApiError(Exception):
    def __init__(self, status, code, message, issues=None):
        super().__init__(message)
        self.status = status
        self.error = {"code": code, "message": message, "issues": issues or []}


def entry_options(kind):
    if not isinstance(kind, str) or kind not in PARTNERS:
        raise ApiError(400, "INVALID_KIND", "请选择采购入库或销售出库。")
    return {
        "companies": COMPANIES, "partners": PARTNERS[kind],
        "warehouses": WAREHOUSES, "products": PRODUCTS,
        "defaults": {"companyId": COMPANIES[0]["id"], "postingDate": date.today().isoformat()},
        "capabilities": {"saveDraft": True},
    }


def check_fields(value, fields, path, issues):
    for field in sorted(value.keys() - fields):
        issues.append({"path": f"{path}{field}", "message": "此字段不在录单范围内。"})


def validate_draft(body, updating):
    if not isinstance(body, dict):
        raise ApiError(400, "INVALID_REQUEST", "草稿应为 JSON 对象。")
    options = entry_options(body.get("kind"))
    issues = []

    def check_id(value, path, choices):
        if not isinstance(value, str) or value not in {entry["id"] for entry in choices}:
            issues.append({"path": path, "message": "请选择有效选项。"})

    def issue(path, message):
        issues.append({"path": path, "message": message})

    fields = {"kind", "companyId", "partnerId", "postingDate", "lines"}
    check_fields(body, fields | {"revision"} if updating else fields, "", issues)
    check_id(body.get("companyId"), "companyId", options["companies"])
    check_id(body.get("partnerId"), "partnerId", options["partners"])
    posting_date = body.get("postingDate")
    try:
        if not isinstance(posting_date, str) or date.fromisoformat(posting_date).isoformat() != posting_date:
            raise ValueError
    except ValueError:
        issue("postingDate", "请输入有效的单据日期。")

    revision = body.get("revision")
    if updating and (type(revision) is not int or revision < 1):
        issue("revision", "缺少有效的草稿版本。")

    lines = body.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
        issue("lines", "请输入 1 至 100 行商品。")
    else:
        for index, line in enumerate(lines):
            path = f"lines.{index}"
            if not isinstance(line, dict):
                issue(path, "商品行格式无效。")
                continue
            check_fields(line, {"productId", "warehouseId", "quantity"}, f"{path}.", issues)
            check_id(line.get("productId"), f"{path}.productId", options["products"])
            check_id(line.get("warehouseId"), f"{path}.warehouseId", options["warehouses"])
            quantity = line.get("quantity")
            if (not isinstance(quantity, str) or not QUANTITY.fullmatch(quantity)
                    or not quantity.replace(".", "").strip("0")):
                issue(f"{path}.quantity", "数量须大于零，整数最多九位，小数最多六位。")
    if issues:
        raise ApiError(422, "VALIDATION_ERROR", "请修正录单内容。", issues)


class DraftStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.drafts = {}
        self.requests = {}

    def get(self, draft_id):
        try:
            return self.drafts[draft_id]
        except KeyError:
            raise ApiError(404, "DRAFT_NOT_FOUND", "找不到草稿。") from None

    def save(self, body, key, draft_id=None):
        if not key or not IDEMPOTENCY_KEY.fullmatch(key):
            raise ApiError(400, "INVALID_IDEMPOTENCY_KEY", "缺少有效的保存标识。")
        with self.lock:
            operation = (draft_id, key)
            if operation in self.requests:
                previous, result = self.requests[operation]
                if body != previous:
                    raise ApiError(409, "IDEMPOTENCY_CONFLICT", "保存标识已用于其他内容。")
                return result

            validate_draft(body, updating=draft_id is not None)
            if draft_id is None:
                draft_id = f"DEMO-{uuid4().hex}"
                revision = 1
            else:
                current = self.get(draft_id)
                if current["kind"] != body["kind"]:
                    raise ApiError(409, "KIND_CONFLICT", "已保存草稿的单据类型不能更改。")
                if current["revision"] != body["revision"]:
                    raise ApiError(409, "STALE_REVISION", "草稿已更新，请核对最新版本后重试。")
                revision = current["revision"] + 1

            result = {**body, "id": draft_id, "revision": revision, "status": "draft"}
            self.drafts[draft_id] = result
            self.requests[operation] = (body, result)
            return result


class PilotServer(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, PilotHandler)
        self.store = DraftStore()


class PilotHandler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json"):
        if content_type == "application/json":
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        if self.headers.get_content_type() != "application/json":
            raise ApiError(415, "JSON_REQUIRED", "请发送 JSON 格式的草稿。")
        raw_length = self.headers.get("Content-Length", "")
        if not re.fullmatch(r"[0-9]{1,7}", raw_length):
            raise ApiError(400, "INVALID_REQUEST", "缺少有效的请求长度。")
        length = int(raw_length)
        if length > 65536:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", "单次录单内容过大。")
        try:
            return json.loads(self.rfile.read(length).decode())
        except (ValueError, RecursionError):
            raise ApiError(400, "INVALID_REQUEST", "草稿 JSON 格式无效。") from None

    def dispatch(self):
        host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != host:
            raise ApiError(403, "FORBIDDEN", "请从本机演示入口访问。")
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            raise ApiError(403, "FORBIDDEN", "请求来源与本机演示入口不一致。")

        parsed = urlsplit(self.path)
        path = parsed.path
        if self.command == "GET" and path in ASSETS:
            name, content_type = ASSETS[path]
            return self.reply(200, (FRONTEND / name).read_bytes(), content_type)

        route = path.removeprefix(PREFIX) if path.startswith(f"{PREFIX}/") else ""
        draft_match = DRAFT_ROUTE.fullmatch(route)
        if self.command == "GET" and route == "/entry-options":
            kinds = parse_qs(parsed.query).get("kind", [])
            data = entry_options(kinds[0] if len(kinds) == 1 else None)
            return self.reply(200, {"data": data})
        if self.command == "GET" and draft_match:
            return self.reply(200, {"data": self.server.store.get(draft_match[1])})
        if (self.command == "POST" and route == "/drafts") or (self.command == "PUT" and draft_match):
            draft_id = draft_match[1] if draft_match else None
            data = self.server.store.save(self.read_body(), self.headers.get("Idempotency-Key"), draft_id)
            return self.reply(200 if draft_id else 201, {"data": data})
        raise ApiError(404, "NOT_FOUND", "找不到此功能。")

    def handle_route(self):
        try:
            self.dispatch()
        except ApiError as error:
            self.reply(error.status, {"error": error.error})
        except FileNotFoundError:
            self.reply(404, {"error": {"code": "NOT_FOUND", "message": "页面资源尚未就绪。", "issues": []}})

    do_GET = do_POST = do_PUT = handle_route


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8093)
    args = parser.parse_args()
    with PilotServer(("127.0.0.1", args.port)) as server:
        print(f"W6 合成录单试点运行于 http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
