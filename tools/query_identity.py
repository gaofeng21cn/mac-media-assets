#!/usr/bin/env python3
"""Read-only query over the production identity baseline.

Answers which registered identity a role may use, which revisions were
withdrawn for looking like a different person, and which production figures
were never admitted to the library.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'collections/character-identity-baseline.json'


def load(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def find(registry, source_id=None, asset_id=None, role=None, family=None):
    hits = []
    for family_id, spec in (registry.get('families') or {}).items():
        if family and family != family_id:
            continue
        for member_id, member in (spec.get('members') or {}).items():
            if source_id and member_id != source_id:
                continue
            if asset_id and member.get('asset_id') != asset_id:
                continue
            if role and registry.get('role_baseline', {}).get(role) != family_id:
                continue
            hits.append({
                'family': family_id,
                'label': spec.get('label'),
                'source_id': member_id,
                'pose': member.get('pose'),
                'asset_id': member.get('asset_id'),
                'revision': member.get('revision'),
                'payload_sha256': member.get('payload_sha256'),
                'note': member.get('note', ''),
            })
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--source-id')
    parser.add_argument('--asset-id')
    parser.add_argument('--role')
    parser.add_argument('--family')
    parser.add_argument('--not-admitted', action='store_true')
    parser.add_argument('--withdrawn', action='store_true')
    args = parser.parse_args()
    registry = load(Path(args.root) / 'collections/character-identity-baseline.json')
    if args.not_admitted:
        print(json.dumps(registry.get('not_admitted_production_assets'), ensure_ascii=False, indent=2))
        return 0
    if args.withdrawn:
        print(json.dumps(registry.get('withdrawn_members'), ensure_ascii=False, indent=2))
        return 0
    hits = find(registry, source_id=args.source_id, asset_id=args.asset_id,
                role=args.role, family=args.family)
    if not hits:
        print(json.dumps({'status': 'no_match',
                          'note': '该查询只定位生产可用身份；没有登记身份不得直接当作生产人物。'}, ensure_ascii=False))
        return 2
    print(json.dumps({'status': 'ok', 'count': len(hits), 'hits': hits}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
