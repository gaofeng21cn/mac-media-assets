#!/usr/bin/env python3
"""Read-only semantic discovery. Curated facets assist progress, never approve a shot."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path, default):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, type(default)) else default
    except (OSError, ValueError):
        return default


def seq(value):
    return value if isinstance(value, list) else [] if value is None else [value]


def mapping(value):
    return value if isinstance(value, dict) else {}


def maturity(root, row):
    record = load(root / row.get('portable_record', '__missing__'), {})
    review = record.get('review') or {}
    static = review.get('static_alpha') or (record.get('asset') or {}).get('visual_review', {}).get('status')
    return {'source': 'registered', 'static': 'reviewed' if static in
            {'checked_on_light_dark_contact_sheet', 'checked_on_light_dark_color_composites', 'passed'} else 'pending',
            'assembly': 'see_collection_samples',
            'motion': row.get('review_boundary', {}).get('motion', 'pending'),
            'medical': row.get('review_boundary', {}).get('medical', 'pending'),
            'listening': row.get('review_boundary', {}).get('listening', 'pending'),
            'current_shot': 'pending'}


def query(root=ROOT, *, text=None, kind=None, series=None, scope=None,
          usable_for=None, author_id=None, include_author_assets=False,
          category=None, action=None, story_role=None, medium=None,
          collection=None, maturity_stage=None, include_provenance=False, limit=None):
    root = Path(root)
    aliases = load(root / 'collections/series.json', {}).get('aliases', {})
    discovery = load(root / 'collections/discovery.json', {}).get('assets', {})
    taxonomy = load(root / 'collections/taxonomy.json', {}).get('categories', [])
    category_ids = {item['label']: item['id'] for item in taxonomy}
    categories = {item['id']: item['label'] for item in taxonomy}
    category = category_ids.get(category, category)
    collections = load(root / 'collections/assemblies.json', {}).get('assemblies', []) + load(root / 'collections/event-kits.json', {}).get('kits', [])
    members = None
    if collection:
        selected = next((item for item in collections if item['id'] == collection), None)
        if not selected:
            return []
        members = {part['source_id'] for part in selected.get('parts', [])}
    rows = [json.loads(line) for line in (root / 'catalog/assets.jsonl').read_text().splitlines() if line.strip()]
    out = []
    for original in rows:
        row = dict(original)
        reuse = row.get('reuse_scope') or {}
        if reuse.get('kind') == 'author' and not include_author_assets and reuse.get('id') != author_id:
            continue
        if row.get('review_boundary', {}).get('admission') == 'reference_only' or row.get('curation', {}).get('status') in {'needs_rebuild', 'superseded'}:
            continue
        if kind and row.get('kind') != kind:
            continue
        if scope and reuse.get('kind') != scope:
            continue
        source = row.get('provenance', {}).get('source_ref') or {}
        values = set(row.get('series_ids', []))
        values.update(value for value in [row.get('canonical_series_id'), reuse.get('series_id'),
                                         reuse.get('series'), source.get('series_id'), source.get('series')] if value)
        values.update(reuse.get('topics') or [])
        if series and aliases.get(series, series) not in {aliases.get(value, value) for value in values}:
            continue
        if members is not None and row.get('source_id') not in members:
            continue
        fields = dict(mapping(discovery.get(row.get('source_id'), row.get('discovery', {}))))
        # Semantic tags can survive a revision; measured geometry cannot.
        if fields.get('geometry_revision') and fields['geometry_revision'] != row.get('revision'):
            fields.pop('visible_bounds', None)
            fields.pop('original_image_size', None)
        if category and fields.get('category') != category:
            continue
        for desired, key in [(action, 'actions'), (story_role, 'story_roles')]:
            candidates = seq(fields.get(key)) + (seq(fields.get('aliases')) if key == 'actions' else [])
            if desired and not any(desired.casefold() in str(value).casefold() for value in candidates):
                break
        else:
            if medium and fields.get('medium') != medium:
                continue
            record = load(root / row.get('portable_record', '__missing__'), {})
            names = [row.get('title', ''), row.get('source_id', ''), fields.get('display_title', '')] + seq(fields.get('aliases'))
            facets = (seq(row.get('tags')) + seq(fields.get('objects')) + seq(fields.get('topics')) +
                      seq(fields.get('story_roles')) + seq(fields.get('actions')) +
                      [categories.get(fields.get('category'), ''), fields.get('usage_notes', ''), record.get('usage_notes', '')])
            primary = '\n'.join(map(str, names)).casefold()
            secondary = '\n'.join(map(str, facets)).casefold()
            terms = (text or '').casefold().split()
            score = 0
            for term in terms:
                if term in primary:
                    score += 10
                elif term in secondary:
                    score += 3
                elif include_provenance and term in json.dumps(row.get('provenance', {}), ensure_ascii=False).casefold():
                    score += 1
                else:
                    break
            else:
                if usable_for and usable_for.casefold() not in primary + '\n' + secondary:
                    continue
                row['discovery'] = fields
                row['display_title'] = fields.get('display_title', row['title'])
                row['maturity'] = maturity(root, row)
                if maturity_stage and row['maturity'].get(maturity_stage) != 'reviewed':
                    continue
                row['search_match'] = {'score': score, 'source': 'curated_names_and_use' if not include_provenance else 'curated_with_provenance'}
                out.append(row)
    if text:
        out.sort(key=lambda row: (-row['search_match']['score'], row['display_title']))
    return out[:limit] if limit is not None else out


def main():
    parser = argparse.ArgumentParser()
    for name in ('query', 'kind', 'series', 'scope', 'usable-for', 'author-id', 'category', 'action', 'story-role', 'medium', 'collection', 'maturity'):
        parser.add_argument('--' + name)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--include-provenance', action='store_true')
    parser.add_argument('--include-author-assets', action='store_true', help='策展只读发现；不授予复用权限')
    parser.add_argument('--include-reference', action='store_true', help='公共库不包含参考区；兼容旧调用，不扩大结果')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    rows = query(text=args.query, kind=args.kind, series=args.series, scope=args.scope,
                 usable_for=args.usable_for, author_id=args.author_id, include_author_assets=args.include_author_assets,
                 category=args.category, action=args.action, story_role=args.story_role, medium=args.medium,
                 collection=args.collection, maturity_stage=args.maturity, include_provenance=args.include_provenance, limit=args.limit)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print('id\tcategory\ttitle\tmedium\tcurrent_shot')
        for row in rows:
            print('\t'.join([row['id'], row['discovery'].get('category', '待策展'), row['display_title'], row['discovery'].get('medium', ''), row['maturity']['current_shot']]))


if __name__ == '__main__':
    main()
