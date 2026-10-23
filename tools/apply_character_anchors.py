#!/usr/bin/env python3
"""Apply reviewed character anchors to immutable package records as new revisions."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_revision(record: dict) -> str:
    # Shared animation_element/v1 identity contract: metadata plus the exact
    # ordered file descriptors; schema and revision are envelope fields.
    body = {key: value for key, value in record.items() if key not in {"schema", "revision"}}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:20]


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def apply(root: Path = ROOT, check: bool = False) -> dict:
    anchors = read(root / "collections/character-anchors.json").get("assets", {})
    rows = [json.loads(line) for line in (root / "catalog/assets.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    changed = []
    missing = []
    current = {}
    for source_id, registration in anchors.items():
        candidates = [item for item in rows if item.get("source_id") == source_id]
        if not candidates:
            missing.append(source_id)
            continue
        # Revision hashes have no chronological order. Prefer the exact
        # reviewed registration first; only create a revision when no indexed
        # record already carries that registration.
        matching = []
        for candidate in candidates:
            record = read(root / candidate["portable_record"])
            recorded = record.get("registration") or (record.get("asset") or {}).get("registration") or {}
            if recorded == registration and canonical_revision(record) == candidate["revision"]:
                matching.append(candidate)
        if matching:
            current[source_id] = matching[-1]["id"]
            continue
        row = candidates[-1]
        record_path = root / row["portable_record"]
        record = read(record_path)
        changed.append(source_id)
        if check:
            continue
        payload_map = {}
        for item in record["files"]:
            mapped = next((payload for payload in row["payload"] if payload["path"].endswith("/" + item["path"])), None)
            if not mapped:
                raise ValueError(f"缺少旧载荷映射: {source_id}:{item['path']}")
            old = (root / mapped["path"]).resolve()
            if not old.is_file() or digest(old) != item["sha256"]:
                raise ValueError(f"旧载荷不可读或哈希不一致: {source_id}:{item['path']}")
            payload_map[item["path"]] = old
        updated = copy.deepcopy(record)
        updated.pop("revision", None)
        updated["registration"] = registration
        if isinstance(updated.get("asset"), dict):
            updated["asset"]["registration"] = registration
        revision = canonical_revision(updated)
        updated["revision"] = revision
        destination = root / "records/paper-theatre" / source_id / revision
        destination_payload = root / "payloads/paper-theatre" / source_id / revision
        if destination.exists():
            raise ValueError(f"目标版本已存在: {source_id}@{revision}")
        destination.mkdir(parents=True)
        mapped_paths = {}
        for item in record["files"]:
            old = payload_map[item["path"]]
            new_record_path = destination / item["path"]
            new_payload_path = destination_payload / item["path"]
            new_record_path.parent.mkdir(parents=True, exist_ok=True)
            new_payload_path.parent.mkdir(parents=True, exist_ok=True)
            new_record_path.write_bytes(old.read_bytes())
            new_payload_path.write_bytes(old.read_bytes())
            mapped_paths[item["path"]] = new_payload_path.relative_to(root).as_posix()
        record_file = destination / "record.json"
        write(record_file, updated)
        new_row = copy.deepcopy(row)
        new_row.update(
            id=f"paper:{source_id}@{revision}",
            revision=revision,
            portable_record=record_file.relative_to(root).as_posix(),
            portable_record_sha256=digest(record_file),
            content_bounds=updated.get("content_bounds"),
            content_bounds_format=updated.get("content_bounds_format"),
        )
        if isinstance(new_row.get("provenance"), dict):
            new_row["provenance"]["record_ref"] = record_file.relative_to(root).as_posix()
        for payload in new_row["payload"]:
            matched = next((item for item in record["files"] if payload["path"].endswith("/" + item["path"])), None)
            if not matched:
                raise ValueError(f"缺少载荷映射: {source_id}:{payload['path']}")
            payload["path"] = mapped_paths[matched["path"]]
        rows.append(new_row)
        current[source_id] = new_row["id"]
    if check:
        return {"status": "passed" if not changed and not missing else "stale",
                "changed": changed, "missing": missing, "current": current}
    if not check:
        # Retain malformed revisions for recovery, but never offer or import
        # them as production candidates. Do not rewrite their original bytes.
        curation_path = root / "collections/curation.json"
        curation = read(curation_path)
        for row in rows:
            if row.get("source_id") not in anchors:
                continue
            record = read(root / row["portable_record"])
            if canonical_revision(record) != row["revision"]:
                assessment = {
                    "status": "superseded",
                    "reason": "旧锚点修订未按 animation_element/v1 载荷身份计算，无法精确导入；使用覆盖表中的修正版。",
                    "replacement_id": current.get(row["source_id"]),
                }
                row["curation"] = assessment
                curation["assets"][row["id"]] = assessment
        write(curation_path, curation)
    if not check:
        (root / "catalog/assets.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in rows),
            encoding="utf-8",
        )
        discovery_path = root / "collections/discovery.json"
        discovery = read(discovery_path)
        for item in rows:
            if item["source_id"] in anchors and item.get("discovery"):
                discovery["assets"][item["source_id"]] = item["discovery"]
        write(discovery_path, discovery)
    if not check:
        coverage_path = root / "collections/character-coverage.json"
        coverage = read(coverage_path)
        by_id = {row["id"]: row["source_id"] for row in rows}
        for role in coverage.get("roles", {}).values():
            for pose, asset_id in role.get("current_assets", {}).items():
                source_id = by_id.get(asset_id, asset_id)
                if source_id in current:
                    role["current_assets"][pose] = current[source_id]
        write(coverage_path, coverage)
    return {"status": "updated" if changed else "unchanged", "changed": changed,
            "missing": missing, "current": current}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = apply(args.root.resolve(), args.check)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"updated", "unchanged", "passed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
