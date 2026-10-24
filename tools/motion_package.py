#!/usr/bin/env python3
"""Shared packaging for library-owned continuous action packages.

Every pack keeps its own editable source, the real rendered sample and the
review record that binds them. This module writes the sample sheets and
registers the package; the pack itself decides what it shows.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_samples(folder):
    """Contact sheet, background review and a phone-width frame from the real render."""
    from PIL import Image, ImageDraw
    folder = Path(folder)
    samples = folder / 'samples'
    sequence = json.loads((folder / 'sequence.json').read_text())
    keyframes = sorted((samples / 'keyframes').glob('*.png'))
    times = sequence['review_times']
    cells = []
    for time, path in zip(times, keyframes):
        image = Image.open(path).convert('RGB')
        width = 310
        height = int(image.size[1] * width / image.size[0])
        image = image.resize((width, height))
        label = Image.new('RGB', (width, 14), (255, 255, 255))
        ImageDraw.Draw(label).text((2, 1), f'{time:.2f}s', fill=(0, 0, 0))
        cell = Image.new('RGB', (width, height + 14), (255, 255, 255))
        cell.paste(label, (0, 0))
        cell.paste(image, (0, 14))
        cells.append(cell)
    columns = 4
    rows = (len(cells) + columns - 1) // columns
    cell_h = max(cell.size[1] for cell in cells)
    cell_w = max(cell.size[0] for cell in cells)
    sheet = Image.new('RGB', (columns * cell_w, rows * cell_h), (250, 250, 250))
    for index, cell in enumerate(cells):
        sheet.paste(cell, ((index % columns) * cell_w, (index // columns) * cell_h))
    sheet.save(samples / 'contact-sheet.jpg', quality=90)

    backgrounds = [Image.open(samples / f'background-{name}.png').convert('RGB')
                   for name in ('light', 'dark', 'color')]
    width = 380
    height = int(backgrounds[0].size[1] * width / backgrounds[0].size[0])
    strip = Image.new('RGB', (width * 3 + 40, height + 10), (250, 250, 250))
    for index, background in enumerate(backgrounds):
        strip.paste(background.resize((width, height)), (10 + index * (width + 10), 5))
    strip.save(samples / 'background-review.jpg', quality=90)

    reading_time = next((event['time'] for event in sequence.get('events', [])
                         if event['name'] == 'reading_ready'), None)
    reading_index = (min(range(len(times)), key=lambda index: abs(times[index] - reading_time))
                     if reading_time is not None else min(10, len(keyframes) - 1))
    reading = Image.open(keyframes[reading_index]).convert('RGB').resize((400, 226))
    reading.save(samples / 'phone-reading.png')
    return samples


def freeze(folder, root=ROOT, *, source_assets, discovery, tags, scope, checked,
           defects_found_and_fixed, not_reviewed, usage_note, id, title):
    """Register one prepared study folder as a reusable motion recipe."""
    folder = Path(folder)
    root = Path(root)
    sequence = json.loads((folder / 'sequence.json').read_text())
    technical = json.loads((folder / 'samples/technical.json').read_text())
    render_inputs = ['index.html', 'runtime.mjs', 'viewer.mjs', 'sequence.json',
                     *dict.fromkeys(item['path'] for item in sequence['images'].values())]
    current_inputs = {relative: sha(folder / relative) for relative in render_inputs}
    if technical.get('inputs') != current_inputs:
        raise ValueError('当前源码或原图与实际渲染输入不一致；先重新渲染与审看')
    if (technical.get('status') != 'passed' or not technical.get('random_seek_equal')
            or technical.get('browser_errors') or technical.get('frames') != math.ceil(sequence['duration'] * sequence['fps'])):
        raise ValueError('实际渲染尚未通过，不能登记动作通过')
    samples = build_samples(folder)
    inputs = {}
    for relative in ['index.html', 'runtime.mjs', 'viewer.mjs', 'sequence.json',
                     *[f'assets/{path.name}' for path in sorted((folder / 'assets').glob('*.png'))]]:
        inputs[relative] = sha(folder / relative)
    media = {}
    for path in sorted(samples.rglob('*')):
        if path.is_file() and path.suffix in {'.png', '.jpg', '.mp4'}:
            media[str(path.relative_to(folder))] = sha(path)
    technical = json.loads((samples / 'technical.json').read_text())
    provenance = {
        'schema': 'mac_motion_sources/v1',
        'generation': source_assets.get('generation', []),
        'source_assets': source_assets.get('library', []),
        'note': source_assets.get('note', ''),
    }
    write(folder / 'provenance.json', provenance)
    review = {
        'schema': 'mac_motion_review/v1',
        'status': 'passed',
        'reviewer': 'Codex model visual review',
        'reviewed_at': '2026-10-24',
        'sequence_sha256': sha(folder / 'sequence.json'),
        'inputs': inputs,
        'media': media,
        'technical': {
            'frames': technical.get('frames'), 'fps': technical.get('fps'),
            'duration': technical.get('duration'),
            'random_seek_equal': technical.get('random_seek_equal'),
            'browser_errors': technical.get('browser_errors'),
        },
        'checked': checked,
        'defects_found_and_fixed': defects_found_and_fixed,
        'not_reviewed': not_reviewed,
    }
    write(folder / 'review.json', review)
    (folder / 'USAGE.md').write_text(
        f'# {title}\n\n{scope}\n\n## 取用\n\n```bash\n'
        f'python3 scripts/media_asset_library.py use --root <公共库路径> \\\n'
        f'  --project <本集工程路径> --id paper:{id}@<revision>\n```\n\n{usage_note}\n',
        encoding='utf-8')

    from apply_character_anchors import canonical_revision
    descriptors = []
    for path in sorted(folder.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(folder).as_posix()
        role = ('source' if path.suffix in {'.mjs', '.html'}
                else 'sample' if path.suffix == '.mp4'
                else 'poster' if relative.endswith('contact-sheet.jpg')
                else 'evidence' if relative in {'review.json', 'provenance.json'}
                else 'payload')
        descriptors.append({'path': relative, 'role': role, 'sha256': sha(path),
                            'bytes': path.stat().st_size})
    medical_review = sequence.get('medical_review', 'not_applicable')
    quality_debt = ['current_shot_review_pending']
    if medical_review == 'pending':
        quality_debt.append('medical_review_pending')
    metadata = {
        'id': id, 'title': title, 'kind': 'motion_recipe', 'entry': 'index.html',
        'reuse_scope': {'kind': 'general'},
        'source': {'kind': 'original_animation', 'generation_receipt': 'provenance.json'},
        'tags': tags, 'discovery': discovery, 'status': 'reusable_candidate',
        'usage_notes': scope,
        'review': {'static_alpha': 'checked_on_light_dark_color_composites', 'full_motion': 'passed',
                   'current_shot': 'pending', 'medical': medical_review,
                   'full_listening': 'not_applicable', 'evidence_ref': 'review.json'},
        'medical_review': medical_review, 'quality_debt': quality_debt,
        'registration': {'coordinate_space': 'sequence_frames_and_runtime_world',
                        'frames_ref': 'sequence.json',
                        'contact_events_ref': 'sequence.json#events'},
        'files': descriptors,
    }
    revision = canonical_revision(metadata)
    record = {'schema': 'animation_element/v1', **metadata, 'revision': revision}
    payload_root = root / 'payloads/paper-theatre' / id / revision
    if payload_root.exists():
        raise ValueError(f'不可覆盖已有版本：{payload_root}')
    for item in descriptors:
        target = payload_root / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(folder / item['path'], target)
    record_path = root / 'records/paper-theatre' / id / revision / 'record.json'
    write(record_path, record)
    row = {
        'id': f'paper:{id}@{revision}', 'source_id': id, 'revision': revision, 'title': title,
        'kind': 'motion_recipe', 'reuse_scope': {'kind': 'general'}, 'tags': tags,
        'series_ids': [], 'discovery': discovery, 'registration': record['registration'],
        'payload': [{**item, 'path': (payload_root / item['path']).relative_to(root).as_posix()}
                    for item in descriptors],
        'portable_record': record_path.relative_to(root).as_posix(),
        'portable_record_sha256': sha(record_path),
        'provenance': {'source_type': 'original_animation',
                       'source_ref': {'recorded_in': 'provenance.json'}},
        'review_boundary': {'admission': 'reusable_candidate', 'motion': 'passed',
                           'medical': medical_review, 'listening': 'not_applicable',
                           'quality_debt': quality_debt},
    }
    catalog = root / 'catalog/assets.jsonl'
    rows = [json.loads(line) for line in catalog.read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(item['id'] == row['id'] for item in rows):
        raise ValueError('同一精确资产版本已存在')
    rows.append(row)
    rows.sort(key=lambda item: item['id'])
    catalog.write_text(''.join(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n'
                               for item in rows), encoding='utf-8')
    discovery_path = root / 'collections/discovery.json'
    collection = json.loads(discovery_path.read_text(encoding='utf-8'))
    collection['assets'][id] = discovery
    discovery_path.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'registered', 'id': row['id'], 'files': len(descriptors)}, ensure_ascii=False))
    return row
