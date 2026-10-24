#!/usr/bin/env python3
"""Verify the external medical-video asset catalog without changing it."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from apply_character_anchors import canonical_revision


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
    source_revisions: dict[str, set[str]] = {}
    payloads = 0
    historical_invalid_revisions = 0
    for row in rows:
        rid = row.get("id")
        if row.get("kind") == "brand" or (row.get("reuse_scope") or {}).get("kind") == "author":
            errors.append(f"private_author_asset:{rid}")
        if not rid or rid in ids:
            errors.append(f"duplicate_or_missing_id:{rid}")
        ids.add(rid)
        if row.get('source_id') and row.get('revision'):
            source_revisions.setdefault(row['source_id'], set()).add(row['revision'])
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
                if canonical_revision(record) != row.get('revision'):
                    if row.get('curation', {}).get('status') == 'superseded':
                        historical_invalid_revisions += 1
                    else:
                        errors.append(f"record_revision:{rid}")
                for original in record.get('files', []):
                    suffix = '/' + row['source_id'] + '/' + row['revision'] + '/' + original['path']
                    mapped = [item for item in row.get('payload', []) if item['path'].endswith(suffix)]
                    if len(mapped) != 1 or mapped[0]['sha256'] != original['sha256'] or mapped[0]['bytes'] != original['bytes']:
                        errors.append(f"record_payload_mapping:{rid}:{original['path']}")
                paths = {item['path'] for item in record.get('files', [])}
                for part in record.get('asset_bundle', []):
                    if part.get('path') not in paths:
                        errors.append(f"missing_bundle_part:{rid}:{part.get('asset_id')}")
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
    anchors_path = root / "collections/character-anchors.json"
    coverage_path = root / "collections/character-coverage.json"
    scale_path = root / "collections/character-scale.json"
    if scale_path.is_file():
        scale = json.loads(scale_path.read_text(encoding="utf-8"))
        scale_assets = scale.get("assets") or {}
        for identifier, value in scale_assets.items():
            if not isinstance(value.get("nominal_height_cm"), (int, float)) or value["nominal_height_cm"] <= 0:
                errors.append(f"character_scale_invalid:{identifier}")
            row = next((item for item in rows if item['id'] == identifier), None)
            if not row or value.get('source_asset_id') != identifier:
                errors.append(f"character_scale_identity:{identifier}")
            elif value.get('source_sha256') not in {part['sha256'] for part in row['payload']}:
                errors.append(f"character_scale_payload:{identifier}")
    if anchors_path.is_file():
        anchors = json.loads(anchors_path.read_text(encoding="utf-8")).get("assets", {})
        for source_id, registration in anchors.items():
            matches = []
            for row in rows:
                if row.get("source_id") != source_id:
                    continue
                record_path = root / row.get("portable_record", "")
                if not record_path.is_file():
                    continue
                record = json.loads(record_path.read_text(encoding="utf-8"))
                recorded = record.get("registration") or (record.get("asset") or {}).get("registration") or {}
                if recorded == registration and canonical_revision(record) == row.get("revision"):
                    matches.append(row)
            if len(matches) != 1:
                errors.append(f"character_anchor_revision:{source_id}:{len(matches)}")
    if coverage_path.is_file():
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        for role_id, role in (coverage.get("roles") or {}).items():
            for pose, asset_id in (role.get("current_assets") or {}).items():
                if asset_id and asset_id not in ids:
                    errors.append(f"character_coverage_asset:{role_id}:{pose}:{asset_id}")
                elif asset_id:
                    row = next(row for row in rows if row["id"] == asset_id)
                    if row.get('curation', {}).get('status') in {'superseded', 'needs_rebuild'}:
                        errors.append(f"character_coverage_withdrawn:{role_id}:{pose}:{asset_id}")
                    wanted = anchors.get(row.get('source_id')) if anchors_path.is_file() else None
                    record = json.loads((root / row['portable_record']).read_text(encoding='utf-8'))
                    recorded = record.get('registration') or (record.get('asset') or {}).get('registration') or {}
                    if wanted and recorded != wanted:
                        errors.append(f"character_coverage_stale_anchors:{role_id}:{pose}:{asset_id}")
    # Optional collections guard resource identity, not creative field completion.
    for filename, field in [('assemblies.json', 'assemblies'), ('event-kits.json', 'kits')]:
        source = root / 'collections' / filename
        if not source.is_file():
            continue
        for collection in json.loads(source.read_text()).get(field, []):
            for part in collection.get('parts', []):
                if part.get('asset_id') not in ids:
                    errors.append(f"collection_resource:{filename}:{part.get('asset_id')}")
    result = {
        "schema": "medical_video_asset_verify/v1",
        "status": "passed" if not errors else "diagnostic",
        "assets": len(rows), "asset_identities": len(source_revisions),
        "registered_versions": len(rows), "reference_versions": 0, "payload_files": payloads,
        "historical_invalid_revisions_excluded": historical_invalid_revisions,
        "errors": errors,
        "note": "仅证明登记、载荷和哈希一致；不证明艺术、连续动作、听感、医学或发布质量",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
