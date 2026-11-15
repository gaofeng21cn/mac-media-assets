#!/usr/bin/env python3
"""Build the overview / close-up / simplified matrix for medical structures.

Every structure needs three different jobs: recognise the whole, read the
inside, and still read at phone width. The matrix records which of the three
exist today and which are genuinely missing, instead of counting assets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = 'collections/structure-purpose-matrix.json'

STRUCTURES = {
    'thyroid': {
        'label': '甲状腺',
        'overview': 'six_paper_thyroid_neck',
        'close_up': 'reserve_thyroid_detailed_layers_v1',
        'simplified': 'reserve_thyroid_simple_v2',
    },
    'kidney': {
        'label': '肾脏',
        'overview': 'six_paper_kidneys_alpha',
        'close_up': 'reserve_kidney_detailed_layers_v1',
        'simplified': 'reserve_kidney_simple_v1',
    },
    'artery_wall': {
        'label': '动脉壁',
        'overview': 'reserve_vessel_v1',
        'close_up': 'reserve_artery_detailed_layers_v1',
        'simplified': 'reserve_artery_simple_v1',
    },
    'pancreas': {
        'label': '胰腺与胰管',
        'overview': 'reserve_pancreas_v1',
        'close_up': 'reserve_pancreas_relations_layers_v1',
        'simplified': 'reserve_pancreas_relations_simple_v1',
    },
    'pituitary': {
        'label': '垂体与邻近结构',
        'overview': 'pituitary_anatomy_collage',
        'close_up': 'reserve_pituitary_relations_layers_v1',
        'simplified': 'reserve_pituitary_relations_simple_v1',
    },
    'heart': {
        'label': '心脏',
        'overview': 'reserve_heart_v1',
        'close_up': 'reserve_heart_cut_v1',
        'simplified': None,
        'missing_reason': {'simplified': '只有外观与四腔切面两版；手机宽下没有单一轮廓版。'},
    },
    'lungs': {
        'label': '肺与气管',
        'overview': 'reserve_lungs_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅总览，未做同视角配准的局部层。',
                           'simplified': '只有整幅总览，未做小尺寸轮廓版。'},
    },
    'liver': {
        'label': '肝脏',
        'overview': 'reserve_liver_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅总览，未做同视角配准的局部层。',
                           'simplified': '只有整幅总览，未做小尺寸轮廓版。'},
    },
    'stomach': {
        'label': '胃',
        'overview': 'reserve_stomach_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅总览，未做同视角配准的局部层。',
                           'simplified': '只有整幅总览，未做小尺寸轮廓版。'},
    },
    'intestine': {
        'label': '肠道',
        'overview': 'reserve_intestine_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅总览，未做同视角配准的局部层。',
                           'simplified': '只有整幅总览，未做小尺寸轮廓版。'},
    },
    'gallbladder': {
        'label': '胆囊',
        'overview': 'reserve_gallbladder_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅总览，未做同视角配准的局部层。',
                           'simplified': '只有整幅总览，未做小尺寸轮廓版。'},
    },
    'islet': {
        'label': '胰岛',
        'overview': 'reserve_islet_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅局部，未配同视角切面层。',
                           'simplified': '只有整幅局部，未做小尺寸轮廓版。'},
    },
    'alveolus': {
        'label': '肺泡',
        'overview': 'reserve_alveolus_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅局部，未配同视角切面层。',
                           'simplified': '只有整幅局部，未做小尺寸轮廓版。'},
    },
    'blood_cell': {
        'label': '红细胞',
        'overview': 'reserve_blood_cell_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅局部，未配同视角切面层。',
                           'simplified': '只有整幅局部，未做小尺寸轮廓版。'},
    },
    'breast': {
        'label': '乳腺',
        'overview': 'six_paper_breast_section',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅切面，未做同视角配准的分层。',
                           'simplified': '只有整幅切面，未做小尺寸轮廓版。'},
    },
    'foot_joint': {
        'label': '足关节',
        'overview': 'six_paper_foot_joint',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅纸件，未做同视角配准的分层。',
                           'simplified': '只有整幅纸件，未做小尺寸轮廓版。'},
    },
    'pelvic_organs': {
        'label': '盆腔器官',
        'overview': 'six_paper_pelvic_organs',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '只有整幅纸件，未做同视角配准的分层。',
                           'simplified': '只有整幅纸件，未做小尺寸轮廓版。'},
    },
    'head_sagittal': {
        'label': '头部矢状位',
        'overview': 'pituitary_sagittal_layered_v1',
        'close_up': None,
        'simplified': None,
        'missing_reason': {'close_up': '标题写“分层”，实为单层整幅，未做可拆同视角配准层。',
                           'simplified': '只有整幅，未做小尺寸轮廓版。'},
    },
}

# structures that also received an original editable schematic pair
SCHEMATIC_PREFIX = {
    'heart': 'heart', 'lungs': 'lungs', 'liver': 'liver', 'stomach': 'stomach',
    'intestine': 'intestine', 'gallbladder': 'gallbladder', 'islet': 'islet',
    'alveolus': 'alveolus', 'blood_cell': 'blood_cell', 'breast': 'breast',
    'foot_joint': 'foot_joint', 'pelvic_organs': 'pelvic_organs', 'head_sagittal': 'head_sagittal',
}

JOBS = ('overview', 'close_up', 'simplified')
JOB_LABEL = {'overview': '总览', 'close_up': '解释近景', 'simplified': '小尺寸简化版'}


def catalog_rows(root):
    text = (root / 'catalog/assets.jsonl').read_text(encoding='utf-8')
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def build(root=ROOT):
    rows = catalog_rows(root)
    curation = json.loads((root / 'collections/curation.json').read_text()).get('assets', {})
    rows = [row for row in rows if curation.get(row['id'], row.get('curation', {})).get('status')
            not in {'superseded', 'needs_rebuild'}]
    by_source = {}
    for row in rows:
        by_source.setdefault(row.get('source_id'), []).append(row)
    structures = {}
    problems = []
    available = {row.get('source_id') for row in rows}
    for key, spec in STRUCTURES.items():
        entry = {'label': spec['label'], 'jobs': {}}
        prefix = SCHEMATIC_PREFIX.get(key)
        for job in JOBS:
            source_id = spec.get(job)
            if prefix and job == 'close_up' and f'reserve_{prefix}_detailed_layers_v1' in available:
                source_id = f'reserve_{prefix}_detailed_layers_v1'
            if prefix and job == 'simplified' and f'reserve_{prefix}_simple_v1' in available:
                source_id = f'reserve_{prefix}_simple_v1'
            if not source_id:
                entry['jobs'][job] = {
                    'status': 'missing',
                    'label': JOB_LABEL[job],
                    'reason': (spec.get('missing_reason') or {}).get(job, '未准备该用途的素材。'),
                }
                continue
            matches = by_source.get(source_id)
            if not matches:
                problems.append(f'{key}:{job}:{source_id}:missing_from_catalog')
                entry['jobs'][job] = {'status': 'missing', 'label': JOB_LABEL[job],
                                      'reason': '登记表中指向的原件不在目录里。'}
                continue
            row = matches[-1]
            record = json.loads((root / row['portable_record']).read_text())
            bundle = record.get('asset_bundle') or row.get('asset_bundle') or []
            entry['jobs'][job] = {
                'status': 'present',
                'label': JOB_LABEL[job],
                'source_id': source_id,
                'asset_id': row.get('id'),
                'parts': len(bundle) or 1,
                'layered': len(bundle) > 1,
                'current_shot': 'pending',
                'medical_review': 'pending',
            }
        entry['complete'] = all(entry['jobs'][job]['status'] == 'present' for job in JOBS)
        structures[key] = entry
    complete = [k for k, v in structures.items() if v['complete']]
    missing_jobs = {}
    for key, entry in structures.items():
        for job in JOBS:
            if entry['jobs'][job]['status'] == 'missing':
                missing_jobs.setdefault(job, []).append(key)
    return {
        'schema': 'mac_structure_purpose_matrix/v1',
        'policy': '总览、解释近景与小尺寸简化版是三种用途，不是同一张图的三种尺寸；缩小原件不等于简化版。矩阵只说明登记情况，不批准医学正确性。',
        'built_on': '2026-10-24',
        'structures': structures,
        'summary': {
            'structures': len(structures),
            'complete_for_all_three_jobs': len(complete),
            'complete_list': sorted(complete),
            'missing_by_job': {JOB_LABEL[j]: sorted(v) for j, v in missing_jobs.items()},
        },
        'problems': problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    matrix = build(root)
    if args.check:
        path = root / OUT
        try:
            stored = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            stored = None
        same = stored == matrix
        print(json.dumps({'status': 'passed' if same and not matrix['problems'] else 'stale',
                          'rebuild_differs': not same,
                          'structures': matrix['summary']['structures'],
                          'complete': matrix['summary']['complete_for_all_three_jobs'],
                          'problems': matrix['problems']}, ensure_ascii=False))
        return 0 if same and not matrix['problems'] else 2
    (root / OUT).write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'written', 'path': OUT,
                      'structures': matrix['summary']['structures'],
                      'complete': matrix['summary']['complete_for_all_three_jobs'],
                      'missing_by_job': matrix['summary']['missing_by_job'],
                      'problems': matrix['problems']}, ensure_ascii=False))
    return 0 if not matrix['problems'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
