#!/usr/bin/env python3
"""Register imagegen cutouts with measured bounds, source receipt and review boundary.

This is a curation helper, not creative approval. It refuses a file whose alpha
is unusable so a glow or opaque-background render cannot quietly enter the
reusable inventory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def measure(path: Path) -> dict:
    try:
        from PIL import Image
    except ImportError as error:
        raise SystemExit("Pillow is required to measure alpha: %s" % error)
    rgba = Image.open(path).convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    pixels = alpha.load()
    corners = [pixels[0, 0], pixels[width - 1, 0], pixels[0, height - 1], pixels[width - 1, height - 1]]
    histogram = alpha.histogram()
    opaque = sum(histogram[250:])
    translucent = sum(histogram[25:250])
    box = alpha.getbbox()
    return {
        "width": width,
        "height": height,
        "corners": corners,
        "bbox": list(box) if box else None,
        "opaque_ratio": round(opaque / max(1, width * height), 4),
        "translucent_ratio": round(translucent / max(1, width * height), 4),
        # A cutout that is fully opaque in the corners has a baked background
        # and cannot be treated as a movable paper layer.
        "is_cutout": all(value < 24 for value in corners),
        # A large translucent skirt around the subject is the halo defect that
        # previously made cached paper pieces unusable on coloured grounds.
        "halo_suspected": translucent / max(1, width * height) > 0.06,
    }


def ingest(root: Path, spec: Path) -> dict:
    value = json.loads(spec.read_text(encoding="utf-8"))
    items = value.get("assets", [value])
    results, rejected = [], []
    for item in items:
        source = Path(item["source"]).expanduser().resolve()
        identifier = item["id"]
        if not source.is_file():
            rejected.append({"id": identifier, "reason": "missing source %s" % source})
            continue
        measurement = measure(source)
        if item.get("kind") == "transparent_subject" and not measurement["is_cutout"]:
            rejected.append({"id": identifier, "reason": "corners are opaque; baked background cannot be a movable layer", "measurement": measurement})
            continue
        if measurement["halo_suspected"] and item.get("allow_halo") is not True:
            rejected.append({"id": identifier, "reason": "translucent halo above threshold", "measurement": measurement})
            continue
        revision = hashlib.sha256(source.read_bytes() + identifier.encode()).hexdigest()[:12]
        base = root / "payloads" / "paper-theatre" / identifier / revision
        payload = base / "files" / "payload.png"
        payload.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, payload)
        receipt = base / "evidence" / "generation-receipt.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({
            "tool": item.get("tool", "built_in_imagegen"),
            "prompt": item.get("prompt", ""),
            "source_path": str(source),
            "measured": measurement,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        record_dir = root / "records" / "paper-theatre" / identifier / revision
        record_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "schema": "animation_element/v1",
            "id": identifier,
            "title": item["title"],
            "kind": item.get("kind", "transparent_subject"),
            "tags": item.get("tags", []),
            "entry": "files/payload.png",
            "reuse_scope": {"kind": item.get("reuse_scope", "general")},
            "status": "pending_review",
            "usage_notes": item.get("usage_notes", ""),
            "source": {"kind": "imagegen", "generation": item.get("tool", "built_in_imagegen"),
                       "plan_id": identifier, "prompt": item.get("prompt", "")},
            "content_bounds": measurement["bbox"],
            "content_bounds_format": "pixel_xyxy_right_bottom_exclusive",
            "alpha_measurement": measurement,
            "quality_debt": item.get("quality_debt", ["static_candidate_only", "continuous_motion_pending"]),
            "medical_review": item.get("medical_review", "pending" if item.get("category") == "anatomy" else "not_applicable"),
            "review": {"static_alpha": "measured_on_ingest", "full_motion": "pending"},
            "revision": revision,
            "files": [
                {"path": "files/payload.png", "role": "payload", "sha256": sha(payload), "bytes": payload.stat().st_size},
                {"path": "evidence/generation-receipt.json", "role": "evidence", "sha256": sha(receipt), "bytes": receipt.stat().st_size},
            ],
        }
        record_path = record_dir / "record.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        catalog_path = root / "catalog.json"
        catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {"schema": "animation_element_library/v1", "items": []}
        relative = str(record_path.relative_to(root))
        if not any(row.get("record") == relative for row in catalog["items"]):
            catalog["items"].append({"id": identifier, "revision": revision, "record": relative})
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append({"id": identifier, "revision": revision, "record": relative,
                        "bounds": measurement["bbox"], "is_cutout": measurement["is_cutout"]})
    return {"schema": "mac_generated_ingest/v1", "registered": results, "rejected": rejected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True, help="JSON describing generated cutouts")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(ingest(args.root.resolve(), args.spec.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
