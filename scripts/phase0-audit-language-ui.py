#!/usr/bin/env python3
"""Read-only, reproducible UI source triage; candidates are NOT verified defects.

Extractors run against installed Core inside Docker. Only static source strings
and the Chinese dictionary are retained, never boot/session or user records.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "phase0/localization"
LATIN = re.compile(r"[A-Za-z]")


class Prose(HTMLParser):
    """Ignore markup, executable examples and link destinations, not prose."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "code", "pre"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "code", "pre"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, value):
        if not self.hidden:
            self.parts.append(value)


def visible(value):
    parser = Prose()
    value = re.sub(r"\{\{.*?\}\}|\{%.*?%\}", "", value)
    parser.feed(value)
    text = " ".join(parser.parts)
    text = re.sub(r"https?://\S+|\{\{.*?\}\}|\{%.*?%\}|\{\d+[^}]*\}", "", text)
    return text.strip()


def python_messages(source):
    """Only literal calls; f-strings/dynamic expressions remain unextracted."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
        if name not in {"_", "__", "gettext"} or not node.args:
            continue
        value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            context = next((k.value.value for k in node.keywords if k.arg == "context"
                            and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)), None)
            yield node.lineno, value.value, context


def collect():
    from babel.messages.extract import extract_javascript
    rows, hashes, errors = [], {}, []
    counts = Counter()
    for app in ("frappe", "erpnext"):
        for path in sorted((Path("apps") / app / app).rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".js", ".html", ".vue", ".json"} or "/public/dist/" in str(path):
                continue
            raw = path.read_bytes()
            hashes[str(path)] = hashlib.sha256(raw).hexdigest()
            source = raw.decode("utf-8")
            counts[path.suffix] += 1

            def add(line, kind, text, context=None):
                if text and LATIN.search(visible(text)):
                    rows.append(dict(path=str(path), line=line, kind=kind, source=text, context=context))

            try:
                if path.suffix == ".py":
                    for line, text, context in python_messages(source):
                        add(line, "gettext", text, context)
                elif path.suffix == ".js":
                    for line, name, message, comments in extract_javascript(io.BytesIO(raw), {"__", "_", "gettext"}, [], {"template_string": True}):
                        values = message if isinstance(message, tuple) else (message,)
                        if values and isinstance(values[0], str):
                            # Frappe __(text, replacements, context).
                            context = values[2] if len(values) > 2 and isinstance(values[2], str) else None
                            add(line, "gettext", values[0], context)
                    # Conservative, deliberately heuristic direct UI sinks.
                    pattern = r'''(?:\.(?:text|html)\(\s*|\b(?:label|title|message|placeholder|description)\s*:\s*)(["'])([^\n]*?)\1'''
                    for match in re.finditer(pattern, source):
                        add(source.count("\n", 0, match.start()) + 1, "direct_ui_candidate", match[2])
                elif path.suffix == ".json":
                    value = json.loads(source)
                    def walk(node):
                        if isinstance(node, dict):
                            for key, text in node.items():
                                if key in {"label", "description", "title", "message", "placeholder", "content", "html"} and isinstance(text, str):
                                    needle = json.dumps(text, ensure_ascii=False)
                                    offset = source.find(needle)
                                    add(source.count("\n", 0, offset) + 1 if offset >= 0 else None, "metadata_" + key, text)
                                elif key == "options" and node.get("fieldtype") == "Select" and isinstance(text, str):
                                    offset = source.find(json.dumps(text, ensure_ascii=False))
                                    for option in text.splitlines():
                                        add(source.count("\n", 0, offset) + 1 if offset >= 0 else None, "metadata_option", option)
                                elif key == "options" and node.get("fieldtype") == "HTML" and isinstance(text, str):
                                    offset = source.find(json.dumps(text, ensure_ascii=False))
                                    add(source.count("\n", 0, offset) + 1 if offset >= 0 else None, "metadata_html_help", text)
                                else:
                                    walk(text)
                        elif isinstance(node, list):
                            for child in node:
                                walk(child)
                    walk(value)
                else:
                    # Raw template prose is not proof of a missing translation:
                    # it may already sit inside a runtime gettext expression.
                    for line, text in enumerate(source.splitlines(), 1):
                        if ">" in text and "<" in text and LATIN.search(visible(text)):
                            add(line, "template_candidate", text.strip())
            except (SyntaxError, ValueError, TypeError) as error:
                errors.append(dict(path=str(path), error=type(error).__name__))
    return dict(rows=rows, hashes=hashes, file_counts=dict(sorted(counts.items())), extraction_errors=errors)


def classify(row, messages):
    if row["kind"] in {"direct_ui_candidate", "template_candidate"}:
        return "needs_runtime_review", None
    key = row["source"] + (":" + row["context"] if row.get("context") else "")
    target = messages.get(key, messages.get(row["source"]))
    if not target or target == row["source"]:
        return "missing_or_identity", target
    return ("latin_in_translation" if LATIN.search(visible(target)) else "translated"), target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.collect:
        print(json.dumps(collect(), ensure_ascii=False))
        return
    result = subprocess.run(["docker", "compose", "-f", str(ROOT / "phase0/compose.yaml"),
                             "exec", "-T", "backend", "env/bin/python", "-", "--collect"],
                            input=Path(__file__).read_text(), text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    baseline = json.loads((DATA / "source-inventory.json").read_text())["source_sha256"]
    # Preserve the immutable upstream baseline; allow only reviewed patched hashes.
    patch_manifest = json.loads((DATA / "patches/manifest.json").read_text())
    patched = []
    for spec in patch_manifest["files"]:
        if baseline.get(spec["path"]) != spec["before_sha256"]:
            raise RuntimeError("Patch baseline differs from original source inventory")
        if data["hashes"].get(spec["path"]) == spec["after_sha256"]:
            baseline[spec["path"]] = spec["after_sha256"]
            patched.append(spec["path"])
    if data.pop("hashes") != baseline:
        raise RuntimeError("Core source differs from pinned inventory; review before auditing")
    spec = importlib.util.spec_from_file_location("localize", ROOT / "scripts/phase0-localize.py")
    localize = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(localize)
    api = localize.ERPNextAPI(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
    api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))
    session = localize.boot(api, force_chinese=False)
    if session["lang"] != "zh":
        raise RuntimeError("Actual session is not Chinese")
    summary = Counter()
    for row in data["rows"]:
        state, target = classify(row, session["__messages"])
        row.update(state=state, translation=target)
        summary[state] += 1
    # Keep the actionable triage queue compact; summary covers all occurrences.
    data["rows"] = [row for row in data["rows"] if row["state"] != "translated"]
    data.update(schema_version=1, core_hashes_match=True, session_language="zh",
                approved_patched_files=patched,
                summary=dict(sorted(summary.items())),
                limitations=["Static candidates are not verified user-visible defects.",
                             "Dynamic keys, Vue scripts, context expressions and template conditions need manual/runtime review.",
                             "Direct UI regex and line-based template scan are heuristic; JSON repeated strings use first matching line.",
                             "Technical identifiers, examples and business input must not be blindly translated."])
    (DATA / "ui-source-audit.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
