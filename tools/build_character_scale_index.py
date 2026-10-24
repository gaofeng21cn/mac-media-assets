#!/usr/bin/env python3
"""Prepare design-height proposals; preserve curated exact-version calibrations."""
from __future__ import annotations

import json
from pathlib import Path
from query_assets import select_versions


HEIGHTS = {
    "adult_man": 175,
    "adult_woman": 163,
    "young_man": 175,
    "older_man": 168,
    "older_woman": 158,
    "pregnant_woman": 163,
    "teen_boy": 165,
    "teen_girl": 160,
    "child_boy": 128,
    "child_girl": 125,
    "clinician_man": 175,
    "clinician_woman": 165,
    "dr_mie": 165,
}


def role(row: dict) -> str | None:
    discovery = row.get("discovery") or {}
    value = discovery.get("character_role")
    if value in HEIGHTS:
        return value
    text = " ".join(str(v) for v in [row.get("source_id"), row.get("title"), row.get("id")] if v).lower()
    source_id = str(row.get("source_id") or "")
    if source_id.startswith("reserve_person_"):
        return "adult_woman"
    if source_id.startswith("mac_") or "hand" in source_id or "head_silhouette" in source_id:
        return None
    for key in HEIGHTS:
        if key in text:
            return key
    return None


def pose(row: dict) -> str:
    discovery = row.get("discovery") or {}
    for value in [discovery.get("pose"), *(discovery.get("actions") or [])]:
        if value:
            return str(value)
    return "see_record"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = [json.loads(line) for line in (root / "catalog/assets.jsonl").read_text().splitlines() if line.strip()]
    path = root / "collections/character-scale.json"
    previous = json.loads(path.read_text()) if path.is_file() else {}
    existing = previous.get('assets', {}) if previous.get('schema') == 'character_scale_index/v2' else {}
    coverage = json.loads((root / 'collections/character-coverage.json').read_text())
    identity_path = root / 'collections/character-identity-baseline.json'
    identities = json.loads(identity_path.read_text()) if identity_path.is_file() else {}
    families = {member['asset_id']: family for family, spec in identities.get('families', {}).items()
                for member in spec.get('members', {}).values() if member.get('asset_id')}
    poses = {identifier: pose_id for item in coverage.get('roles', {}).values()
             for pose_id, identifier in item.get('current_assets', {}).items() if identifier}
    assets: dict[str, dict] = {}
    for row in select_versions(root, rows):
        if (row.get("discovery") or {}).get("category") != "characters":
            continue
        key = role(row)
        if not key:
            continue
        source_id = row.get("source_id")
        if not source_id:
            continue
        record = json.loads((root / row['portable_record']).read_text())
        payload = next(part for part in record['files'] if part['path'] == record['entry'])
        curated = record.get('human_scale') or (record.get('asset') or {}).get('human_scale')
        assets[row['id']] = existing.get(row['id']) or ({**curated, 'source_asset_id': row['id'],
                                                       'source_sha256': payload['sha256']} if curated else {
            "nominal_height_cm": HEIGHTS[key],
            "height_status": "proposed_design_assumption",
            "scale_family": families.get(row['id']) or (row.get('discovery') or {}).get('identity_family') or source_id,
            "pose": poses.get(row['id']) or pose(row),
            "measurement": "角色设计身高候选，须随原件审定；未标定姿态不可由外框换算身高",
            "subject": "character",
            "source_asset_id": row['id'],
            "source_sha256": payload['sha256'],
            "calibration": {"status": "pending"},
        })
        if assets[row['id']].get('height_status') == 'proposed_design_assumption' and row['id'] in families:
            assets[row['id']]['scale_family'] = families[row['id']]
    output = {
        "schema": "character_scale_index/v2",
        "scope": "public_mac_media_assets",
        "method": "Exact-version design-height proposals, not measured adult averages or scene approval. Curate body spans before metric staging.",
        "assets": dict(sorted(assets.items())),
    }
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"path": str(path), "assets": len(assets)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
