"""Apply/reverse only declared UI patches, rejecting source/version drift.

Run during image build, never against a live mounted checkout. --check is read-only.
All files are validated before any write. No fuzzy matching, no DB operations.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def transform(data, spec, reverse=False):
    expected = spec["after_sha256" if reverse else "before_sha256"]
    if digest(data) != expected:
        raise ValueError("Source hash mismatch: " + spec["path"])
    text = data.decode("utf-8")
    replacements = list(reversed(spec["replacements"])) if reverse else spec["replacements"]
    for old, new in replacements:
        count = spec.get("counts", {}).get(old, 1)
        if reverse:
            old, new = new, old
        # Explicit expected occurrence count handles parent and child audit rows.
        if text.count(old) != count:
            raise ValueError("Replacement count mismatch: " + spec["path"])
        text = text.replace(old, new)
    result = text.encode("utf-8")
    target = spec.get("before_sha256" if reverse else "after_sha256")
    if target and digest(result) != target:
        raise ValueError("Result hash mismatch: " + spec["path"])
    return result


def plans(root, manifest, reverse=False):
    root = root.resolve()
    pending = []
    for spec in manifest["files"]:
        path = (root / spec["path"]).resolve()
        if not path.is_relative_to(root) or not spec["path"].startswith("apps/frappe/frappe/public/js/"):
            raise ValueError("Patch target outside approved presentation paths")
        pending.append((path, transform(path.read_bytes(), spec, reverse)))
    return pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if not args.check and any(not spec.get("after_sha256") for spec in manifest["files"]):
        raise ValueError("Pinned result hashes are required before applying")
    pending = plans(args.root, manifest, args.reverse)
    if not args.check:
        for path, data in pending:
            path.write_bytes(data)
    print(json.dumps({str(path.relative_to(args.root.resolve())): digest(data) for path, data in pending}, indent=2))


if __name__ == "__main__":
    main()
