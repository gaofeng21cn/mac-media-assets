#!/usr/bin/env python3
"""Synthesise the action sound accents the library was missing.

The library only carried paper and office sounds, so the four continuous
motion packages had nothing to land on: no footstep, no chair, no device
confirmation, no cooking. These are deterministic procedural originals in the
same spirit as the existing sfx packs, and the source lives here so the bytes
can be rebuilt instead of being trusted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'work' / 'action-sfx-20261024'
SR = 48000


def one_pole_lowpass(signal, cutoff, sr=SR):
    alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff / sr)
    out = np.empty_like(signal)
    acc = 0.0
    for index, value in enumerate(signal):
        acc += alpha * (value - acc)
        out[index] = acc
    return out


def bandpass(signal, low, high, sr=SR):
    return signal - one_pole_lowpass(signal, low, sr) - one_pole_lowpass(signal, high, sr)


def envelope(length, attack, decay, sr=SR):
    times = np.arange(length) / sr
    env = np.minimum(1.0, times / max(attack, 1e-6))
    env *= np.exp(-times / max(decay, 1e-6))
    return env


def normalise(signal, peak=0.82):
    highest = float(np.max(np.abs(signal))) or 1.0
    return signal * (peak / highest)


def write_wav(path: Path, signal, sr=SR):
    data = np.clip(normalise(signal), -1.0, 1.0)
    pcm = (data * 32767.0).astype('<i2')
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())
    return pcm.nbytes


def footstep(seed, soft=True):
    rng = np.random.default_rng(seed)
    length = int(SR * 0.32)
    noise = rng.standard_normal(length)
    body = one_pole_lowpass(noise, 900 if soft else 1600)
    body *= envelope(length, 0.004, 0.055)
    times = np.arange(length) / SR
    base = 72 + (seed % 5) * 4
    thump = np.sin(2 * np.pi * (base - 18 * times) * times) * envelope(length, 0.002, 0.07) * 0.55
    grit = rng.standard_normal(length) * envelope(length, 0.001, 0.018) * 0.22
    return body * 0.9 + thump + grit


def chair_sit(seed):
    rng = np.random.default_rng(seed)
    length = int(SR * 0.75)
    noise = rng.standard_normal(length)
    body = one_pole_lowpass(noise, 260) * envelope(length, 0.004, 0.16)
    creak = bandpass(noise, 420, 2100) * 0.35
    creak *= np.clip(np.sin(2 * np.pi * (3.2 + 1.6 * rng.random()) * np.arange(length) / SR), 0, 1)
    creak *= envelope(length, 0.02, 0.22)
    settle = one_pole_lowpass(rng.standard_normal(length), 700) * envelope(length, 0.01, 0.09) * 0.5
    return body + creak + settle


def cloth_rustle(seed):
    rng = np.random.default_rng(seed)
    length = int(SR * 0.9)
    noise = rng.standard_normal(length)
    high = noise - one_pole_lowpass(noise, 2600)
    times = np.arange(length) / SR
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * 2.1 * times + rng.random() * 6.28)
    return high * swell * 0.7


def device_beep(seed, base=None):
    rng = np.random.default_rng(seed)
    base = float(base or (1900 + (seed % 7) * 95))
    length = int(SR * 0.42)
    out = np.zeros(length)
    for start, freq, span in ((0.0, base, 0.09), (0.17, base * 1.26, 0.15)):
        begin = int(start * SR)
        end = min(length, begin + int(span * SR))
        times = np.arange(end - begin) / SR
        tone = np.sin(2 * np.pi * freq * times) + 0.25 * np.sin(2 * np.pi * freq * 2 * times)
        out[begin:end] += tone * envelope(end - begin, 0.006, 0.16) * 0.8
    out[: int(0.002 * SR)] += rng.standard_normal(int(0.002 * SR)) * 0.12
    tail = int(SR * 0.02)
    out[-tail:] += rng.standard_normal(tail) * np.exp(-np.arange(tail) / (tail * 0.25)) * 0.05
    return out


def cooking_sizzle(seed):
    rng = np.random.default_rng(seed)
    length = int(SR * 2.4)
    noise = rng.standard_normal(length)
    bed = bandpass(noise, 1800, 9000) * 0.5
    times = np.arange(length) / SR
    bed *= 0.65 + 0.35 * np.sin(2 * np.pi * 1.3 * times + rng.random() * 6.28)
    crackle = np.zeros(length)
    for _ in range(int(90 * rng.random() + 60)):
        at = int(rng.random() * (length - 400))
        span = int(SR * rng.uniform(0.002, 0.012))
        crackle[at:at + span] += rng.standard_normal(span) * np.exp(-np.arange(span) / (span * 0.3)) * 0.5
    return bed + crackle


PACKS = [
    {
        'source_id': 'mac_sfx_footstep_soft_v1',
        'title': '拟音：脚步（纸舞台轻步）',
        'aliases': ['脚步', '走路', '迈步', 'footstep', 'steps'],
        'events': ['人物行走', '起身走动', '伴随移动'],
        'duration': 0.32,
        'seeds': [9401, 9402, 9403],
        'render': footstep,
    },
    {
        'source_id': 'mac_sfx_chair_sit_v1',
        'title': '拟音：落座（椅面承重）',
        'aliases': ['落座', '坐下', '椅子', 'chair', 'sit'],
        'events': ['坐定', '坐站过渡落定', '起身落座'],
        'duration': 0.75,
        'seeds': [9404, 9405, 9406],
        'render': chair_sit,
    },
    {
        'source_id': 'mac_sfx_cloth_rustle_v1',
        'title': '拟音：衣料摩擦',
        'aliases': ['衣料', '衣服', '摩擦', 'cloth', 'rustle'],
        'events': ['转身', '伸手取物', '起身'],
        'duration': 0.9,
        'seeds': [9407, 9408, 9409],
        'render': cloth_rustle,
    },
    {
        'source_id': 'mac_sfx_device_confirm_v1',
        'title': '拟音：器械完成提示音',
        'aliases': ['提示音', '完成', '测量完成', 'beep', 'device'],
        'events': ['血糖仪读数完成', '血压测量完成', '设备提示'],
        'duration': 0.42,
        'seeds': [9410, 9411, 9412],
        'render': device_beep,
    },
    {
        'source_id': 'mac_sfx_cooking_sizzle_v1',
        'title': '拟音：烹饪油声',
        'aliases': ['油声', '煎炒', '下锅', 'sizzle', 'cooking'],
        'events': ['入锅翻动', '连续备餐', '厨房场景'],
        'duration': 2.4,
        'seeds': [9413, 9414, 9415],
        'render': cooking_sizzle,
    },
]


def canonical_revision(record):
    body = {key: value for key, value in record.items() if key not in {'schema', 'revision'}}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:20]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_pack(pack, stage: Path):
    audio_dir = stage / pack['source_id'] / 'audio'
    audio_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for index, seed in enumerate(pack['seeds'], start=1):
        signal = pack['render'](seed)
        path = audio_dir / f"{pack['source_id'].removeprefix('mac_sfx_').removesuffix('_v1')}-{index}.wav"
        write_wav(path, signal)
        size = path.stat().st_size
        files.append({'path': f'audio/{path.name}', 'role': 'payload', 'sha256': digest(path), 'bytes': size,
                      'seed': seed, 'duration_seconds': len(signal) / SR})
    parameters = {
        'id': pack['source_id'],
        'kind': 'original_procedural_material_accent',
        'not_field_recording': True,
        'sample_rate': SR,
        'duration': pack['duration'],
        'seeds': pack['seeds'],
        'license': 'MIT original composition and code',
        'usage': 'contact-aligned, quiet, optional; listen in current mix',
        'listening_review': 'pending',
    }
    parameters_path = audio_dir / 'parameters.json'
    parameters_path.write_text(json.dumps(parameters, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    files.append({'path': 'audio/parameters.json', 'role': 'evidence', 'sha256': digest(parameters_path),
                  'bytes': parameters_path.stat().st_size})
    return files


def record_for(pack, files):
    record = {
        'schema': 'animation_element/v1',
        'id': pack['source_id'],
        'title': pack['title'],
        'kind': 'audio',
        'tags': ['audio', 'sfx', 'action_accent', 'procedural_original', '20261024'],
        'discovery': {
            'category': 'sfx',
            'display_title': pack['title'],
            'aliases': pack['aliases'],
            'objects': [pack['title'], *pack['aliases']],
            'story_roles': pack['events'],
            'actions': pack['events'],
            'medium': 'audio',
            'material': None,
            'renderers': [],
            'style': [],
            'topics': [],
            'usage_notes': '动作接触对齐后低混入；与四套连续动作包配套使用；当前集独立审听。',
            'view': '按当前镜头选择',
            'compatibility': {'dependencies': '代码包先查实际依赖；图像可供多种后端使用',
                             'params': '可调整；content bounds 与接触点不固定画面构图'},
        },
        'entry': files[0]['path'],
        'reuse_scope': {'kind': 'general'},
        'status': 'reusable_candidate',
        'usage_notes': '程序合成，不是实地录音；用于动作接触点对齐，音量需按当前混音审听。',
        'source': {'kind': 'procedural_original', 'license': 'MIT original code/composition',
                   'generator': 'tools/build_action_sfx.py'},
        'content_bounds': None,
        'content_bounds_format': None,
        'medical_review': 'not_applicable',
        'review': {'listening': 'pending', 'full_motion': 'pending', 'current_shot': 'pending'},
        'quality_debt': ['listening_review_pending'],
        'files': files,
    }
    record['revision'] = canonical_revision(record)
    return record


def register(root: Path, stage: Path):
    rows = []
    for pack in PACKS:
        files = build_pack(pack, stage)
        record = record_for(pack, files)
        revision = record['revision']
        record_rel = Path('records/paper-theatre') / pack['source_id'] / revision / 'record.json'
        target = root / record_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        payload = []
        for item in files:
            source = stage / pack['source_id'] / item['path']
            rel = Path('payloads/paper-theatre') / pack['source_id'] / revision / item['path']
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, root / rel)
            payload.append({'path': str(rel), 'role': item['role'], 'sha256': item['sha256'], 'bytes': item['bytes']})
        entry = f"paper:{pack['source_id']}@{revision}"
        rows.append({
            'id': entry,
            'portable_record': str(record_rel),
            'portable_record_sha256': digest(root / record_rel),
            'source_id': pack['source_id'],
            'revision': revision,
            'kind': 'audio',
            'title': pack['title'],
            'payload': payload,
            'provenance': {'source_type': 'procedural_original',
                           'source_ref': record['source'], 'record_ref': str(record_rel)},
            'review_boundary': {'admission': 'reusable_candidate', 'motion': 'pending', 'medical': 'not_applicable',
                                'listening': 'pending', 'quality_debt': ['listening_review_pending']},
            'reuse_scope': {'kind': 'general'},
            'content_bounds': None,
            'content_bounds_format': None,
            'tags': record['tags'],
            'usage': [],
            'asset_bundle': [],
            'assembly': None,
            'discovery': record['discovery'],
        })
    return rows


def integrate(root: Path, rows):
    catalog = root / 'catalog/assets.jsonl'
    existing = [json.loads(line) for line in catalog.read_text(encoding='utf-8').splitlines() if line.strip()]
    by_id = {row['id']: row for row in existing}
    added = []
    for row in rows:
        if row['id'] in by_id:
            continue
        by_id[row['id']] = row
        added.append(row['id'])
    merged = sorted(by_id.values(), key=lambda item: item['id'])
    catalog.write_text(''.join(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n' for item in merged),
                       encoding='utf-8')
    discovery_path = root / 'collections/discovery.json'
    discovery = json.loads(discovery_path.read_text(encoding='utf-8'))
    for row in rows:
        discovery['assets'][row['source_id']] = row['discovery']
    discovery_path.write_text(json.dumps(discovery, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    audio_path = root / 'collections/audio.json'
    audio = json.loads(audio_path.read_text(encoding='utf-8'))
    # a re-registration replaces the stale entry for the same source identity
    audio['assets'] = [item for item in audio.get('assets', [])
                       if item.get('source_id') not in {row['source_id'] for row in rows}]
    for row in rows:
        audio.setdefault('assets', []).append({
            'asset_id': row['id'],
            'source_id': row['source_id'],
            'category': 'sfx',
            'title': row['title'],
            'emotion_or_event': row['discovery']['aliases'],
            'variants_or_tracks': [
                {'path': item['path'], 'duration_seconds': round(item['bytes'] / 2 / SR, 3),
                 'sample_rate': str(SR), 'channels': 1}
                for item in row['payload'] if item['role'] == 'payload'
            ],
            'listening_review': 'pending',
            'note': '程序合成动作拟音；与四套连续动作包配套，先在当前混音里审听。',
        })
    audio_path.write_text(json.dumps(audio, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return added


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--stage', default=str(STAGE))
    parser.add_argument('--register', action='store_true', help='write records, payloads and catalog rows')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    stage = Path(args.stage)
    if args.register:
        rows = register(root, stage)
        added = integrate(root, rows)
        print(json.dumps({'status': 'registered', 'packs': len(rows), 'added': added}, ensure_ascii=False))
        return 0
    for pack in PACKS:
        files = build_pack(pack, stage)
        print(json.dumps({'source_id': pack['source_id'], 'variants': len(files) - 1,
                          'files': [item['path'] for item in files]}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
