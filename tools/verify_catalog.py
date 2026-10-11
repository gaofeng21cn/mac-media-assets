#!/usr/bin/env python3
"""Verify the external medical-video asset catalog without changing it."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    catalog = root / "catalog/assets.jsonl"
    collections = root / "collections/series.json"
    rows = [json.loads(line) for line in catalog.read_text(encoding="utf-8").splitlines() if line.strip()]
    known = json.loads(collections.read_text(encoding="utf-8"))
    series_ids = set(known.get("series", {})) | set(known.get("aliases", {}))
    errors: list[str] = []
    ids: set[str] = set()
    payloads = 0
    for row in rows:
        rid = row.get("id")
        if not rid or rid in ids:
            errors.append(f"duplicate_or_missing_id:{rid}")
        ids.add(rid)
        if row.get('portable_record'):
            record_path = (root / row['portable_record']).resolve()
            if not record_path.is_relative_to(root) or not record_path.is_file():
                errors.append(f"missing_or_outside_record:{rid}")
            else:
                record = json.loads(record_path.read_text())
                if record.get('id') != row.get('source_id') or record.get('revision') != row.get('revision'):
                    errors.append(f"record_identity:{rid}")
                if digest(record_path) != row.get('portable_record_sha256'):
                    errors.append(f"record_sha256:{rid}")
        for item in row.get("payload", []):
            payloads += 1
            path = (root / item.get("path", "")).resolve()
            if not path.is_relative_to(root):
                errors.append(f"payload_outside_root:{rid}")
                continue
            if not path.is_file():
                errors.append(f"missing:{item.get('path')}")
                continue
            actual = digest(path)
            if actual != item.get("sha256"):
                errors.append(f"sha256:{item.get('path')}")
            if path.stat().st_size != item.get("bytes"):
                errors.append(f"bytes:{item.get('path')}")
        for sid in row.get("series_ids", []):
            if sid not in series_ids:
                errors.append(f"unknown_series:{sid}:{rid}")
    result = {
        "schema": "medical_video_asset_verify/v1",
        "status": "passed" if not errors else "diagnostic",
        "assets": len(rows), "payload_files": payloads,
        "errors": errors,
        "note": "仅证明登记、载荷和哈希一致；不证明艺术、连续动作、听感、医学或发布质量",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
