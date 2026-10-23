#!/usr/bin/env python3
"""Report character role/pose coverage without treating labels as image evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, type(default)) else default
    except (OSError, ValueError):
        return default


def audit(root: Path = ROOT) -> dict:
    coverage = load(root / "collections/character-coverage.json", {})
    rows = [
        json.loads(line)
        for line in (root / "catalog/assets.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {row.get("id"): row for row in rows}
    roles = []
    missing = []
    contact_gaps = []
    for role_id, role in (coverage.get("roles") or {}).items():
        assets = role.get("current_assets") or {}
        poses = []
        for pose in role.get("required_poses", []):
            asset_id = assets.get(pose)
            asset = by_id.get(asset_id) if asset_id else None
            record = load(root / asset.get("portable_record", "__missing__"), {}) if asset else {}
            registration = record.get("registration") or (record.get("asset") or {}).get("registration") or {}
            anchors = registration.get("anchors") or {}
            required_anchors = ["head"] + (
                ["feet"]
                if pose in {"stand", "walk", "stand_explain"}
                else ["seat"]
                if pose in {"seated", "seated_consult"}
                else ["hand"]
                if pose == "reach"
                else ["body"]
                if pose == "lying"
                else []
            )
            missing_anchors = [
                name for name in required_anchors
                if name not in anchors
                and not (name == "hand" and any(key.startswith("hand_") for key in anchors))
            ]
            if asset and missing_anchors:
                contact_gaps.append(
                    {
                        "role_id": role_id,
                        "role": role.get("label", role_id),
                        "pose": pose,
                        "asset_id": asset_id,
                        "missing_anchors": missing_anchors,
                    }
                )
            poses.append(
                {
                    "pose": pose,
                    "label": (coverage.get("pose_labels") or {}).get(pose, pose),
                    "asset_id": asset_id,
                    "source_id": asset.get("source_id") if asset else None,
                    "registered": bool(asset),
                    "kind": asset.get("kind") if asset else None,
                    "revision": asset.get("revision") if asset else None,
                    "anchors": sorted(anchors),
                    "missing_anchors": missing_anchors,
                }
            )
            if not asset:
                missing.append(
                    {
                        "role_id": role_id,
                        "role": role.get("label", role_id),
                        "pose": pose,
                        "label": (coverage.get("pose_labels") or {}).get(pose, pose),
                    }
                )
        roles.append(
            {
                "role_id": role_id,
                "role": role.get("label", role_id),
                "required_pose_count": len(role.get("required_poses", [])),
                "available_pose_count": sum(1 for item in poses if item["registered"]),
                "poses": poses,
            }
        )
    return {
        "schema": "mac_character_coverage_audit/v1",
        "roles_checked": len(roles),
        "required_pose_slots": sum(role["required_pose_count"] for role in roles),
        "available_pose_slots": sum(role["available_pose_count"] for role in roles),
        "missing_pose_slots": len(missing),
        "registered_pose_slots_without_required_anchors": len(contact_gaps),
        "roles": roles,
        "missing": missing,
        "contact_anchor_gaps": contact_gaps,
        "note": "覆盖表只定位素材缺口；姿态和接触仍需查看原件与当前镜头。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
