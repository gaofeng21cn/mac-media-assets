#!/usr/bin/env python3
"""Project exact-version curation into the catalog for existing consumers."""
import argparse
import json
from pathlib import Path
from query_assets import ROOT, all_catalog_rows, effective_row, load_curation


def apply(root=ROOT, check=False):
    root = Path(root)
    decisions = load_curation(root)
    rows = all_catalog_rows(root)
    projected = [effective_row(row, decisions) for row in rows]
    changed = [row['id'] for row, updated in zip(rows, projected) if row != updated]
    if changed and not check:
        (root / 'catalog/assets.jsonl').write_text(''.join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in projected))
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    changed = apply(args.root, args.check)
    print(json.dumps({'status': 'stale' if changed and args.check else 'updated' if changed else 'unchanged',
                      'changed': changed}, ensure_ascii=False))
    raise SystemExit(2 if changed and args.check else 0)
