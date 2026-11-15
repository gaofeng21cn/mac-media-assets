#!/usr/bin/env python3
"""Prepare the same lossless revision for intake, project use and full exports."""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from media_store import ROOT, contained, fetch, select, storage
from optimize_media import POLICY, prepare_asset, rewrite


def prepare(root, identifier, cache=None, *, offline=False, max_bytes=None):
    root = Path(root)
    # Always resolve withdrawal from the owner, including on an encoding cache hit.
    rows = select(root, [identifier])
    row = next((item for item in rows if item['id'] == identifier), None)
    if row is None:
        raise ValueError('需要精确素材版本 ID')
    if storage(root).get('delivery_policy'):
        # A prebuilt installation is consumed directly, without a second encode.
        return {'status': 'already_prepared', 'row': row}
    resolved = {}
    if any(not contained(root, part['path']).is_file() for part in row['payload']):
        resolved = fetch(root, rows, cache, offline=offline, max_bytes=max_bytes)['resolved']
    result = prepare_asset(root, row, cache, resolved)
    scale_path = root / 'collections/character-scale.json'
    scale = json.loads(scale_path.read_text()).get('assets', {}).get(identifier) if scale_path.is_file() else None
    if scale:
        result['human_scale'] = rewrite(scale, {identifier: result['row']['id'],
            row['revision']: result['row']['revision'], **result['hash_map']})
    return {'status': 'prepared', 'policy': POLICY, 'source_asset_id': identifier, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--id', required=True)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--max-bytes', type=int)
    args = parser.parse_args()
    try:
        result = prepare(args.root, args.id, args.cache, offline=args.offline, max_bytes=args.max_bytes)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'diagnostic', 'reason': str(error)}, ensure_ascii=False))
        raise SystemExit(2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
