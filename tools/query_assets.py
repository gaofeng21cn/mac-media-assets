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


def all_catalog_rows(root):
    return [json.loads(line) for line in
            (Path(root) / 'catalog/assets.jsonl').read_text(encoding='utf-8').splitlines()
            if line.strip()]


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
          collection=None, maturity_stage=None, layering=None,
          include_provenance=False, limit=None, character_role=None,
          pose=None, asset_id=None, all_versions=False):
    root = Path(root)
    pose = {'伸手': 'reach', '接取': 'reach', '递接': 'reach', '伸手接取': 'reach',
            '行走': 'walk', '站立': 'stand', '站姿': 'stand', '坐姿': 'seated', '坐下': 'seated', '躺卧': 'lying', '躺姿': 'lying',
            '问诊': 'seated_consult'}.get(pose, pose)
    aliases = load(root / 'collections/series.json', {}).get('aliases', {})
    discovery = load(root / 'collections/discovery.json', {}).get('assets', {})
    coverage = load(root / 'collections/character-coverage.json', {})
    layer_contracts = load(root / 'collections/layer-contracts.json', {}).get('contracts', {})
    taxonomy = load(root / 'collections/taxonomy.json', {}).get('categories', [])
    character_scale = load(root / 'collections/character-scale.json', {}).get('assets', {})
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
    catalog_rows = all_catalog_rows(root)
    rows = select_versions(root, catalog_rows, all_versions=all_versions)
    if asset_id:
        exact = [row for row in catalog_rows if row.get('id') == asset_id]
        if exact:
            rows = exact
        else:
            # A stable source ID means "the reviewed current version"; the
            # full paper:ID@revision form remains an exact historical lookup.
            rows = select_versions(
                root,
                [row for row in catalog_rows if row.get('source_id') == asset_id],
                all_versions=False,
            )
    role_asset_ids = None
    requested_roles = set()
    wants_motion = category == 'motion' or kind == 'motion_recipe' or action is not None
    if character_role or pose:
        role_asset_ids = set()
        for role_id, role in (coverage.get('roles') or {}).items():
            if character_role:
                requested = character_role.strip().casefold()
                role_names = {str(value).strip().casefold() for value in
                              [role_id, role.get('label', ''), *(role.get('aliases') or [])]}
                if requested not in role_names:
                    continue
            requested_roles.add(role_id)
            for pose_id, selected_asset_id in (role.get('current_assets') or {}).items():
                accepted_poses = {pose_id, coverage.get('pose_labels', {}).get(pose_id)}
                if pose_id == 'stand_explain':
                    accepted_poses.add('stand')
                if pose_id == 'seated_consult':
                    accepted_poses.add('seated')
                if selected_asset_id and (not pose or pose in accepted_poses):
                    role_asset_ids.add(selected_asset_id)
    out = []
    for original in rows:
        row = dict(original)
        fields = dict(mapping(discovery.get(row.get('source_id'), row.get('discovery', {}))))
        role_motion = (wants_motion and row.get('kind') == 'motion_recipe'
                       and fields.get('character_role') in requested_roles
                       and (not pose or pose in fields.get('poses', [])))
        if role_asset_ids is not None and row.get('id') not in role_asset_ids and row.get('source_id') not in role_asset_ids and not role_motion:
            continue
        reuse = row.get('reuse_scope') or {}
        if reuse.get('kind') == 'author' and not include_author_assets and reuse.get('id') != author_id:
            continue
        exact_history = asset_id is not None and row.get('id') == asset_id
        if row.get('review_boundary', {}).get('admission') == 'reference_only' or (
                row.get('curation', {}).get('status') in {'needs_rebuild', 'superseded'} and not exact_history):
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
        contract = mapping(layer_contracts.get(row.get('source_id')))
        if contract:
            fields['layer_contract'] = contract
            fields['layering'] = contract.get('layering')
            facets_layer = seq(contract.get('movable_layers')) + seq(contract.get('anchors'))
            if facets_layer:
                fields['actions'] = list(dict.fromkeys(seq(fields.get('actions')) + facets_layer))
        if layering and mapping(layer_contracts.get(row.get('source_id'))).get('layering') != layering:
            continue
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
            if medium and medium not in seq(fields.get('medium')):
                continue
            record = load(root / row.get('portable_record', '__missing__'), {})
            names = [row.get('title', ''), row.get('source_id', ''), fields.get('display_title', '')] + seq(fields.get('aliases'))
            facets = (seq(row.get('tags')) + seq(fields.get('objects')) + seq(fields.get('topics')) +
                      seq(fields.get('story_roles')) + seq(fields.get('actions')) +
                      seq(fields.get('layer_contract', {}).get('movable_layers')) +
                      seq(fields.get('layer_contract', {}).get('anchors')) +
                      [fields.get('layering', '')] +
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
                if row.get('id') in character_scale:
                    row['human_scale'] = character_scale[row['id']]
                row['registration'] = record.get('registration') or (record.get('asset') or {}).get('registration') or {}
                row['display_title'] = fields.get('display_title', row['title'])
                row['maturity'] = maturity(root, row)
                if maturity_stage and row['maturity'].get(maturity_stage) != 'reviewed':
                    continue
                row['search_match'] = {'score': score, 'source': 'curated_names_and_use' if not include_provenance else 'curated_with_provenance'}
                out.append(row)
    if text:
        out.sort(key=lambda row: (-row['search_match']['score'], row['display_title']))
    else:
        out.sort(key=lambda row: row.get('display_title', row.get('title', '')))
    return out[:limit] if limit is not None else out


def select_versions(root, rows, *, all_versions=False):
    """Select one current version per asset identity without discarding history."""
    if all_versions:
        return rows
    anchors = load(Path(root) / 'collections/character-anchors.json', {}).get('assets', {})
    coverage = load(Path(root) / 'collections/character-coverage.json', {})
    coverage_ids = {
        asset_id
        for role in (coverage.get('roles') or {}).values()
        for asset_id in (role.get('current_assets') or {}).values()
        if asset_id
    }
    grouped = {}
    curation = load(Path(root) / 'collections/curation.json', {}).get('assets', {})
    for row in rows:
        if curation.get(row.get('id'), row.get('curation', {})).get('status') in {'superseded', 'needs_rebuild'}:
            continue
        grouped.setdefault(row.get('source_id'), []).append(row)
    selected = []
    for source_id, candidates in grouped.items():
        exact = [row for row in candidates if row.get('id') in coverage_ids]
        if exact:
            selected.append(exact[-1])
            continue
        wanted = anchors.get(source_id)
        matching = []
        if wanted:
            for row in candidates:
                record = load(Path(root) / row.get('portable_record', '__missing__'), {})
                registration = record.get('registration') or (record.get('asset') or {}).get('registration') or {}
                if registration == wanted:
                    matching.append(row)
        if matching:
            selected.append(matching[-1])
        else:
            selected.append(candidates[-1])
    order = {row.get('id'): index for index, row in enumerate(rows)}
    return sorted(selected, key=lambda row: order.get(row.get('id'), len(order)))


def main():
    parser = argparse.ArgumentParser()
    for name in ('query', 'kind', 'series', 'scope', 'usable-for', 'author-id', 'category', 'action', 'story-role', 'medium', 'collection', 'maturity', 'layering', 'character-role', 'pose', 'id'):
        parser.add_argument('--' + name)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--include-provenance', action='store_true')
    parser.add_argument('--include-author-assets', action='store_true', help='策展只读发现；不授予复用权限')
    parser.add_argument('--include-reference', action='store_true', help='公共库不包含参考区；兼容旧调用，不扩大结果')
    parser.add_argument('--all-versions', action='store_true', help='显式查看历史修订，不用于默认制作选择')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    rows = query(text=args.query, kind=args.kind, series=args.series, scope=args.scope,
                 usable_for=args.usable_for, author_id=args.author_id, include_author_assets=args.include_author_assets,
                 category=args.category, action=args.action, story_role=args.story_role, medium=args.medium,
                 collection=args.collection, maturity_stage=args.maturity, layering=args.layering,
                 include_provenance=args.include_provenance, limit=args.limit,
                 character_role=getattr(args, 'character_role'), pose=args.pose,
                 asset_id=getattr(args, 'id'), all_versions=args.all_versions)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print('id\tcategory\ttitle\tmedium\tlayering\tcurrent_shot')
        for row in rows:
            print('\t'.join([row['id'], row['discovery'].get('category', '待策展'), row['display_title'],
                             ', '.join(map(str, seq(row['discovery'].get('medium')))), row['discovery'].get('layering', ''),
                             row['maturity']['current_shot']]))


if __name__ == '__main__':
    main()
