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


def validate_review(review, inputs, media, sequence):
    """Check the binding and declared scope of a separately authored review.

    These checks cannot decide visual quality. The reviewer supplies the verdict
    after inspecting the media; a render receipt or preparation checklist cannot.
    """
    if not isinstance(review, dict) or review.get('schema') != 'mac_motion_review/v2':
        raise ValueError('需要独立的 mac_motion_review/v2 审看记录')
    if review.get('inputs') != inputs or review.get('media') != media:
        raise ValueError('审看记录未完整绑定当前输入和样片；重新审看后再冻结')
    if review.get('sequence_sha256') != inputs['sequence.json']:
        raise ValueError('审看记录未绑定当前 sequence')
    if review.get('status') not in {'pending', 'passed', 'rejected'}:
        raise ValueError('无效的审看状态')
    domains = review.get('domains', {})
    if not isinstance(domains, dict):
        raise ValueError('审看范围必须是对象')
    for name in ('static_alpha', 'full_motion'):
        if domains.get(name, 'pending') not in {'pending', 'passed', 'rejected', 'not_applicable'}:
            raise ValueError('无效的审看范围：' + name)
    if review['status'] == 'passed' or 'passed' in domains.values():
        for name in ('reviewer', 'reviewed_at', 'review_method', 'observations', 'reviewed_files'):
            if not review.get(name):
                raise ValueError('独立审看记录缺少：' + name)
        from datetime import date
        date.fromisoformat(review['reviewed_at'])
        if not set(review['reviewed_files']).issubset(media):
            raise ValueError('审看文件不属于当前样片')
        if domains.get('full_motion') == 'passed':
            if 'samples/sample.mp4' not in review['reviewed_files']:
                raise ValueError('完整动作结论缺少当前 MP4 审看范围')
            windows = sorted(review.get('motion_windows', []))
            end = 0
            for start, stop in windows:
                if not all(isinstance(n, (int, float)) and math.isfinite(n) for n in (start, stop)):
                    raise ValueError('无效的审看时码')
                if start > end or start < 0 or stop <= start or stop > sequence['duration']:
                    raise ValueError('完整动作审看范围存在缺口或越界')
                end = max(end, stop)
            if end != sequence['duration']:
                raise ValueError('完整动作审看范围未覆盖全片')
    if review['status'] == 'passed' and domains.get('full_motion') != 'passed':
        raise ValueError('整体动作通过需要明确的完整动作结论')
    return review


def bound_files(folder):
    folder = Path(folder)
    sequence = json.loads((folder / 'sequence.json').read_text())
    inputs = {relative: sha(folder / relative) for relative in
              ['index.html', 'runtime.mjs', 'viewer.mjs', 'sequence.json',
               *dict.fromkeys(item['path'] for item in sequence['images'].values())]}
    media = {str(path.relative_to(folder)): sha(path)
             for path in sorted((folder / 'samples').rglob('*'))
             if path.is_file() and path.suffix in {'.png', '.jpg', '.mp4'}}
    return inputs, media


def freeze(folder, root=ROOT, *, source_assets, discovery, tags, scope, review_targets,
           preparation_notes, not_reviewed, usage_note, id, title):
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
        raise ValueError('实际渲染尚未通过，不能冻结动作包')
    samples = build_samples(folder)
    inputs, media = bound_files(folder)
    provenance = {
        'schema': 'mac_motion_sources/v1',
        'generation': source_assets.get('generation', []),
        'source_assets': source_assets.get('library', []),
        'note': source_assets.get('note', ''),
    }
    write(folder / 'provenance.json', provenance)
    # Preparation notes are requests, never post-render verdicts.
    write(folder / 'review-request.json', {
        'review_targets': review_targets, 'preparation_notes': preparation_notes,
        'not_reviewed': not_reviewed, 'inputs': inputs, 'media': media,
    })
    review_path = folder / 'review.json'
    if review_path.exists():
        review = validate_review(json.loads(review_path.read_text()), inputs, media, sequence)
    else:
        review = {
            'schema': 'mac_motion_review/v2', 'status': 'pending',
            'sequence_sha256': inputs['sequence.json'], 'inputs': inputs, 'media': media,
            'domains': {'static_alpha': 'pending', 'full_motion': 'pending'},
            'not_reviewed': not_reviewed,
        }
        write(review_path, review)
    if review['status'] == 'rejected' or 'rejected' in review.get('domains', {}).values():
        raise ValueError('已拒用的动作包不能登记为可复用候选')
    domains = review.get('domains', {})
    motion = domains.get('full_motion', 'pending')
    static = domains.get('static_alpha', 'pending')
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
    if motion != 'passed':
        quality_debt.append('full_motion_review_pending')
    if static != 'passed':
        quality_debt.append('static_review_pending')
    if medical_review == 'pending':
        quality_debt.append('medical_review_pending')
    metadata = {
        'id': id, 'title': title, 'kind': 'motion_recipe', 'entry': 'index.html',
        'reuse_scope': {'kind': 'general'},
        'source': {'kind': 'original_animation', 'generation_receipt': 'provenance.json'},
        'tags': tags, 'discovery': discovery, 'status': 'reusable_candidate',
        'usage_notes': scope,
        'review': {'static_alpha': static, 'full_motion': motion,
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
        'review_boundary': {'admission': 'reusable_candidate', 'motion': motion, 'static': static,
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
