#!/usr/bin/env python3
"""Audit/apply Simplified Chinese presentation through native ERPNext APIs.

No direct database access, core edits, renaming, transaction writes or privilege changes.
User identifiers and personal data are never included in audit output.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

from opencc import OpenCC
from babel.messages.pofile import read_po
from phase0_api import ERPNextAPI

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "phase0" / "localization"
LATIN = re.compile(r"[A-Za-z]")
TECHNICAL_VALUE = re.compile(r"(?:.*(?:\.YYYY\.|\.YY\.|\.MM\.|#{2,}).*|[AB][0-9]{1,2}|[ABO]{1,2}[+-]|C5E|DT-|HR-EMP-|PMO-|POS-CLO-|CODE-39|EAN(?:-8|-13)?|GS1|GTIN-14|ISBN-10|ISBN-13|UPC-A)")
PLACEHOLDER = re.compile(r"\{\d+[^}]*\}")
DISPLAY_TYPES = [
    "Print Format", "Report", "Role", "Module Def", "Workspace", "Workspace Sidebar",
    "Language", "UOM", "Company", "Supplier", "Customer", "Warehouse", "Account",
    "Cost Center", "Item Group", "Item", "Price List", "Workflow", "Workflow State",
    "Workflow Action Master", "User",
]


def presentation_signature(value):
    """Compare sanitized rich text without repeatedly fighting native link safety."""
    class Signature(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, data):
            self.parts.append(("text", data))
        def handle_starttag(self, tag, attrs):
            for key, target in attrs:
                if key in ("href", "src"):
                    self.parts.append((key, target))
    parser = Signature()
    parser.feed(value)
    return [("text", "".join(value for key, value in parser.parts if key == "text"))] + [part for part in parser.parts if part[0] != "text"]


def localize_help_prose(value, text_map=None):
    """Translate known Print Format help prose, preserving markup/code/URLs.

    Applied only to the two known native help keys, never arbitrary business HTML.
    """
    class Help(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.hidden = 0
            self.parts = []
        def handle_starttag(self, tag, attrs):
            self.parts.append(self.get_starttag_text())
            if tag in {"code", "pre", "script", "style"}:
                self.hidden += 1
        def handle_startendtag(self, tag, attrs):
            self.parts.append(self.get_starttag_text())
        def handle_endtag(self, tag):
            self.parts.append("</" + tag + ">")
            if tag in {"code", "pre", "script", "style"} and self.hidden:
                self.hidden -= 1
        def handle_data(self, data):
            if not self.hidden:
                if text_map is not None:
                    data = text_map.get(data, data)
                for source, target in (("Boostrap CSS", "页面样式"), ("Bootstrap CSS", "页面样式"),
                                       ("Jinja", "打印模板"), ("CSS", "样式")):
                    data = re.sub(r"(?<![A-Za-z])" + re.escape(source) + r"(?![A-Za-z])", target, data)
            self.parts.append(data)
        def handle_entityref(self, name):
            self.parts.append("&" + name + ";")
        def handle_charref(self, name):
            self.parts.append("&#" + name + ";")
        def handle_comment(self, data):
            self.parts.append("<!--" + data + "-->")
    parser = Help()
    parser.feed(value)
    return "".join(parser.parts)


def boot(api, force_chinese=True):
    html = api.get_text("/app?_lang=zh" if force_chinese else "/app")
    token = re.search(r'frappe.csrf_token\s*=\s*["\']([^"\']+)', html)
    if token:
        api.csrf_token = token.group(1)
    return json.JSONDecoder().raw_decode(html.split("frappe.boot = ", 1)[1])[0]


def dictionary(api):
    convert = OpenCC("t2s").convert
    original = boot(api)["__messages"]
    entries = {key: convert(value) for key, value in original.items()}
    for filename in ("frappe-zh-v15.csv", "erpnext-zh-v15.csv"):
      with (DATA / "vendor" / filename).open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 2 or not row[1]:
                continue
            source, target = row[0].replace("\\n", "\n"), convert(row[1].replace("\\n", "\n"))
            # Old templates with changed placeholders/markup are unsafe as overlays.
            if "<" in source or sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(target)):
                continue
            key = source + (":" + row[2] if len(row) > 2 and row[2] else "")
            entries.setdefault(key, target)
    for filename in ("frappe-zh-v16.po", "erpnext-zh-v16.po"):
        with (DATA / "vendor" / filename).open("rb") as f:
            catalog = read_po(f)
        for message in catalog:
            if not message.id or not isinstance(message.id, str) or not isinstance(message.string, str) or not message.string:
                continue
            source, target = message.id, convert(message.string)
            if sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(target)):
                continue
            key = source + (":" + message.context if message.context else "")
            entries[key] = target
            if message.context:
                entries.setdefault(source, target)
    entries.update(json.loads((DATA / "overrides.json").read_text(encoding="utf-8")))
    entries.update(json.loads((DATA / "catalog-names.json").read_text(encoding="utf-8")))
    terms = json.loads((DATA / "terms.json").read_text(encoding="utf-8"))
    labels = json.loads((DATA / "source-labels.json").read_text(encoding="utf-8"))
    canonical = lambda value: " ".join(value.casefold().split())
    good = {canonical(key): value for key, value in entries.items() if not LATIN.search(value)}
    for label in labels:
        target = entries.get(label, label)
        if canonical(label) in good:
            target = good[canonical(label)]
        if re.search(r"[\u4e00-\u9fff]", target) and "<" not in target:
            for term in sorted(terms, key=len, reverse=True):
                target = re.sub(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", terms[term], target)
        if target != label:
            entries[label] = target
    entries.update(json.loads((DATA / "field-labels.json").read_text(encoding="utf-8")))
    entries.update(json.loads((DATA / "ui-overrides.json").read_text(encoding="utf-8")))
    # Official translated help corrupts some example punctuation. Build these
    # two keys from pinned native originals, translating prose only.
    help_prose = json.loads((DATA / "print-help-prose.json").read_text(encoding="utf-8"))
    for source in json.loads((DATA / "print-help-source.json").read_text(encoding="utf-8")).values():
        entries[source] = localize_help_prose(source, help_prose)
    # Composite standard-format names are display values, never record renames.
    for row in api.list_docs("Print Format", ["name"], [], 1000):
        name = row["name"]
        if name.endswith(" Standard"):
            base = name.removesuffix(" Standard") if hasattr(name, "removesuffix") else name[:-9]
            entries[name] = entries.get(base, base) + "（标准）"
        elif name.endswith(" with Item Image"):
            base = name[:-16]
            entries[name] = entries.get(base, base) + "（含商品图片）"
    return original, entries


def audit(api, entries):
    result = {}
    labels = json.loads((DATA / "source-labels.json").read_text(encoding="utf-8"))
    residual = [label for label in labels if LATIN.search(entries.get(label, label))]
    result["source_fields_and_options"] = {
        "total": len(labels),
        "english_names": [label for label in residual if not TECHNICAL_VALUE.fullmatch(label)],
        "preserved_technical_values": [label for label in residual if TECHNICAL_VALUE.fullmatch(label)],
    }
    for dt in ["DocType", "Report", "Workspace", "Workspace Sidebar", "Print Format", "Role", "Module Def", "Workflow", "Workflow State", "Workflow Action Master"]:
        rows = api.list_docs(dt, ["name"], [], 5000)
        missing = sorted(row["name"] for row in rows if LATIN.search(entries.get(row["name"], row["name"])))
        result[dt] = {"total": len(rows), "english_names": missing}
    return result


def upsert(api, dt, name, payload):
    existing = api.get_doc(dt, name)
    if existing:
        if any(existing.get(key) != value for key, value in payload.items()):
            api.update(dt, name, payload)
            return 1
        return 0
    api.insert(dt, {"name": name, **payload})
    return 1


def verify_prints(api, entries):
    """Render all ten formats against submitted synthetic fixtures through native HTTP."""
    results = {}
    types = ["Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice", "Payment Entry", "Stock Entry", "Stock Reconciliation"]
    for dt in types:
        rows = api.list_docs(dt, ["name"], [["docstatus", "=", 1], ["company", "=", "Phase Zero Hardware Trading Demo"]], 1)
        if not rows:
            raise RuntimeError("No submitted synthetic print fixture for " + dt)
        name = rows[0]["name"]
        query = urllib.parse.urlencode({"doctype": dt, "name": name, "format": entries[dt] + "（简体中文）", "no_letterhead": 1, "_lang": "zh"})
        rendered = api.get_text("/printview?" + query)
        for marker in [entries[dt], name, "单据编号", "公司", "状态"]:
            if marker not in rendered:
                raise RuntimeError("Chinese print is missing " + marker)
        results[dt] = {"fixture": name, "bytes": len(rendered.encode("utf-8"))}
    print(json.dumps({"chinese_print_previews": results}, ensure_ascii=False))


def apply(api, original, entries):
    count = 0
    rows = api.list_docs("Translation", ["name", "source_text", "translated_text", "context"], [["language", "=", "zh"]], 20000)
    existing = {(row["source_text"] + (":" + row["context"] if row.get("context") else "")): row for row in rows}
    new = []
    for key, target in entries.items():
        if original.get(key) == target:
            continue
        # Store exact contextual keys; Frappe resolves source:context verbatim.
        source, context = key, ""
        payload = {"doctype": "Translation", "language": "zh", "source_text": source, "translated_text": target, "context": context}
        if key in existing:
            if existing[key]["translated_text"] != target:
                if "<" in target and presentation_signature(existing[key]["translated_text"]) == presentation_signature(target):
                    continue
                api.update("Translation", existing[key]["name"], {"translated_text": target})
                count += 1
        else:
            new.append(payload)
    for start in range(0, len(new), 200):
        api.call("frappe.client.insert_many", {"docs": new[start:start+200]})
        count += len(new[start:start+200])
        print(f"TRANSLATIONS applied={count}", flush=True)
    api.update("System Settings", "System Settings", {"language": "zh"})
    users = api.list_docs("User", ["name", "language", "enabled", "first_name"], [], 1000)
    user_changes = 0
    for user in users:
        if user["name"] == "Guest" or not user.get("enabled"):
            continue
        if user.get("language") != "zh":
            api.update("User", user["name"], {"language": "zh"})
            user_changes += 1
        if user["name"] == "Administrator" or user["name"].endswith("@example.invalid"):
            first_name = entries.get(user.get("first_name"), user.get("first_name"))
            if first_name != user.get("first_name"):
                api.update("User", user["name"], {"first_name": first_name})
    scripts = 0
    for dt in DISPLAY_TYPES:
        meta = api.get_doc("DocType", dt)
        if not meta:
            continue
        upsert(api, "Property Setter", f"{dt}-main-translated_doctype", {
            "doctype_or_field": "DocType", "doc_type": dt, "property": "translated_doctype", "property_type": "Check", "value": "1"
        })
        fields = ["name", meta.get("title_field")]
        fields = [field for field in fields if field]
        script = "const dt = " + json.dumps(dt) + ";\n"
        script += "const settings = frappe.listview_settings[dt] || {};\n"
        script += "settings.formatters = Object.assign({}, settings.formatters);\n"
        for field in fields:
            script += "settings.formatters[" + json.dumps(field) + "] = value => frappe.utils.escape_html(__(String(value || '')));\n"
        script += "frappe.listview_settings[dt] = settings;\n"
        scripts += upsert(api, "Client Script", "简体中文列表名称-" + dt, {"dt": dt, "view": "List", "enabled": 1, "script": script})
    print(json.dumps({"translation_changes": count, "user_language_changes": user_changes, "list_script_changes": scripts}, ensure_ascii=False))
    template = (DATA / "print.html").read_text(encoding="utf-8")
    for row in api.list_docs("Print Format", ["name", "default_print_language", "standard"], [], 1000):
        # Native standard formats are protected; editing them exports into Core.
        # Controlled Chinese formats/defaults below replace them for business use.
        if row.get("standard") != "Yes" and row.get("default_print_language") != "zh":
            api.update("Print Format", row["name"], {"default_print_language": "zh"})
    for dt in ["Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice", "Payment Entry", "Stock Entry", "Stock Reconciliation"]:
        name = entries[dt] + "（简体中文）"
        upsert(api, "Print Format", name, {"doc_type": dt, "standard": "No", "custom_format": 1, "print_format_type": "Jinja", "default_print_language": "zh", "html": template})
        upsert(api, "Property Setter", f"{dt}-main-default_print_format", {"doctype_or_field": "DocType", "doc_type": dt, "property": "default_print_format", "property_type": "Data", "value": name})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true", help="Fail on untranslated installed names/field labels in the actual session")
    args = parser.parse_args()
    api = ERPNextAPI(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
    api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))
    original, entries = dictionary(api)
    print(json.dumps({"native_translations": len(original), "overlay_translations": len(entries), "catalog_audit": audit(api, entries)}, ensure_ascii=False, indent=2), flush=True)
    if args.apply:
        apply(api, original, entries)
        actual = boot(api)
        if actual["lang"] != "zh":
            raise RuntimeError("Session is not Simplified Chinese")
        print("OK: Simplified Chinese overlay applied; identifiers and transactions unchanged")
    if args.verify:
        # A fresh login avoids a request-local translation cache from before writes.
        api = ERPNextAPI(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
        api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))
        actual = boot(api, force_chinese=False)
        if api.get_doc("System Settings", "System Settings").get("language") != "zh":
            raise RuntimeError("Native site default is not Simplified Chinese")
        users = api.list_docs("User", ["name", "language", "enabled"], [], 1000)
        if any(row.get("enabled") and row["name"] != "Guest" and row.get("language") != "zh" for row in users):
            raise RuntimeError("An enabled user's native language is not Simplified Chinese")
        coverage = audit(api, actual["__messages"])
        print(json.dumps({"actual_session_language": actual["lang"], "actual_catalog_audit": coverage}, ensure_ascii=False, indent=2))
        if actual["lang"] != "zh" or any(row["english_names"] for row in coverage.values()):
            raise RuntimeError("Actual installed session still has English system names")
        required_ui = json.loads((DATA / "ui-overrides.json").read_text(encoding="utf-8"))
        help_prose = json.loads((DATA / "print-help-prose.json").read_text(encoding="utf-8"))
        for source in json.loads((DATA / "print-help-source.json").read_text(encoding="utf-8")).values():
            required_ui[source] = localize_help_prose(source, help_prose)
        if any(presentation_signature(actual["__messages"].get(key, "")) != presentation_signature(target)
               for key, target in required_ui.items()):
            raise RuntimeError("Actual session UI translations differ from the controlled overlay")
        print(json.dumps({"actual_ui_translations_verified": len(required_ui)}))
        verify_prints(api, actual["__messages"])
        print("OK: installed Simplified Chinese catalog and field coverage verified")


if __name__ == "__main__":
    main()
