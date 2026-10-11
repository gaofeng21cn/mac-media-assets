#!/usr/bin/env python3
"""Read-only discovery; author-owned material needs an explicit identity."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def query(root=ROOT, *, text=None, kind=None, series=None, scope=None,
          usable_for=None, author_id=None, include_author_assets=False,
          include_reference=False):
    aliases = json.loads((root / 'collections/series.json').read_text()).get('aliases', {})
    rows = [json.loads(line) for line in (root / 'catalog/assets.jsonl').read_text().splitlines() if line.strip()]
    references = root / 'catalog/reference-assets.jsonl'
    if (include_reference or kind == 'reference_frame') and references.is_file():
        rows.extend(json.loads(line) for line in references.read_text().splitlines() if line.strip())
    out = []
    for row in rows:
        reuse = row.get('reuse_scope') or {}
        if reuse.get('kind') == 'author' and not include_author_assets and reuse.get('id') != author_id:
            continue
        if not include_reference and kind != 'reference_frame' and (
                row.get('review_boundary', {}).get('admission') == 'reference_only'
                or row.get('curation', {}).get('status') in {'needs_rebuild', 'superseded'}):
            continue
        serialized = json.dumps(row, ensure_ascii=False).lower()
        if text and text.lower() not in serialized:
            continue
        if kind and row.get('kind') != kind:
            continue
        if scope and reuse.get('kind') != scope:
            continue
        source = row.get('provenance', {}).get('source_ref') or {}
        values = set(row.get('series_ids', []))
        values.update(value for value in [row.get('canonical_series_id'), reuse.get('series_id'),
                                          reuse.get('series'), source.get('series_id'), source.get('series')] if value)
        if series and aliases.get(series, series) not in {aliases.get(value, value) for value in values}:
            continue
        if usable_for and usable_for.lower() not in serialized:
            continue
        out.append(row)
    return out


def main():
    parser = argparse.ArgumentParser()
    for name in ('query', 'kind', 'series', 'scope', 'usable-for', 'author-id'):
        parser.add_argument('--' + name)
    parser.add_argument('--include-author-assets', action='store_true', help='策展只读发现；不授予复用权限')
    parser.add_argument('--include-reference', action='store_true', help='显式查看历史参考和退出推荐的版本；不作为可用素材')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    rows = query(text=args.query, kind=args.kind, series=args.series, scope=args.scope,
                 usable_for=args.usable_for, author_id=args.author_id,
                 include_author_assets=args.include_author_assets,
                 include_reference=args.include_reference)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print('id\tkind\ttitle\tscope\tadmission')
        for row in rows:
            print('\t'.join([row['id'], row['kind'], row['title'], row.get('reuse_scope', {}).get('kind', ''),
                             row.get('review_boundary', {}).get('admission', '')]))


if __name__ == '__main__':
    main()
