#!/usr/bin/env python3
"""Build and verify the production identity baseline for the paper-theatre series.

Identity families are decided by looking at the real originals, never by file
name or revision order. The registry names one production identity per role so
that a scene can be re-cast without mixing faces, outfits or drawing styles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = 'collections/character-identity-baseline.json'

# family id -> declared members. `pose` is the narrative role of the member.
FAMILIES = {
    'adult_woman_cn_mustard': {
        'label': '中国成年女性·芥黄开衫青绿长裤（生产女性患者基线）',
        'style': 'watercolor_paper_craft',
        'note': '库内中文成年女性唯一贯穿身份；stand/walk/seated/reach/side 与库内 character_adult_woman_* 同一人。',
        'members': {
            'reserve_person_stand_v1': 'stand',
            'reserve_person_walk_v1': 'walk',
            'reserve_person_seated_v1': 'seated',
            'reserve_person_reach_v1': 'reach',
            'reserve_person_side_v1': 'side_stand',
            'character_adult_woman_reach_v2': 'reach',
            'character_adult_woman_lying_v2': 'lying',
            'character_adult_woman_care_reach_v2': 'care_reach',
            'character_carer_calling_v1': 'calling',
        },
    },
    'adult_man_cn_green_red': {
        'label': '中国成年男性·绿衫红裤（生产男性患者基线）',
        'style': 'watercolor_paper_craft',
        'note': '与四套连续动作包同一身份；生产 75 集已在用。',
        'members': {
            'character_adult_man_stand_v1': 'stand',
            'character_adult_man_walk_v1': 'walk',
            'character_adult_man_seated_v1': 'seated',
            'character_adult_man_reach_v1': 'reach',
            'character_adult_man_upper_abdomen_stool_v1': 'seated_upper_abdomen_stool',
            'character_man_alert_armchair_v1': 'seated_alert_armchair',
            'character_man_unresponsive_armchair_v1': 'seated_head_down_armchair',
            'male_patient_walk_20261023': 'walk',
            'male_patient_seated_identity_20261023': 'seated',
        },
    },
    'clinician_man_cn': {
        'label': '中国男性医生·白大褂蓝衬衫',
        'style': 'watercolor_paper_craft',
        'note': '承担其他身份的医生；主讲身份由作者私有库承担。',
        'members': {
            'character_clinician_man_stand_v1': 'stand_explain',
            'character_clinician_man_seated_consult_v1': 'seated_consult',
            'character_clinician_man_walk_v1': 'walk',
            'character_clinician_man_reach_v1': 'reach',
        },
    },
    'clinician_woman_cn': {
        'label': '中国女性医生·白大褂灰绿内搭',
        'style': 'watercolor_paper_craft',
        'note': '承担其他身份的医生；主讲身份由作者私有库承担。',
        'members': {
            'character_clinician_woman_stand_v2': 'stand_explain',
            'character_clinician_woman_seated_consult_v2': 'seated_consult',
            'character_clinician_woman_walk_v2': 'walk',
            'character_clinician_woman_reach_v2': 'reach',
        },
    },
    'child_girl_cn': {
        'label': '中国女童·黄毛衣蓝裤', 'style': 'watercolor_paper_craft',
        'note': '',
        'members': {s: p for s, p in [
            ('character_child_girl_stand_v1', 'stand'), ('character_child_girl_seated_v1', 'seated'),
            ('character_child_girl_walk_v1', 'walk'), ('character_child_girl_reach_v1', 'reach')]},
    },
    'child_boy_cn': {
        'label': '中国男童·砖红毛衣深蓝裤', 'style': 'watercolor_paper_craft',
        'note': '',
        'members': {s: p for s, p in [
            ('character_child_boy_stand_v1', 'stand'), ('character_child_boy_seated_v1', 'seated'),
            ('character_child_boy_walk_v1', 'walk'), ('character_child_boy_reach_v1', 'reach')]},
    },
    'teen_girl_cn': {
        'label': '中国青少年女性·黄开衫长直发', 'style': 'watercolor_paper_craft',
        'note': 'character_teen_girl_stand_v1 存在另一张不同发型/外套的修订版，见 withdrawn_members。',
        'members': {s: p for s, p in [
            ('character_teen_girl_stand_v1', 'stand'), ('character_teen_girl_seated_v1', 'seated'),
            ('character_teen_girl_walk_v1', 'walk'), ('character_teen_girl_reach_v1', 'reach')]},
    },
    'teen_boy_cn': {
        'label': '中国男性青少年·蓝夹克', 'style': 'watercolor_paper_craft',
        'note': '',
        'members': {s: p for s, p in [
            ('character_teen_boy_stand_v1', 'stand'), ('character_teen_boy_seated_v1', 'seated'),
            ('character_teen_boy_walk_v1', 'walk'), ('character_teen_boy_reach_v1', 'reach')]},
    },
    'young_man_cn': {
        'label': '中国年轻成年男性·藏青毛衣卡其裤', 'style': 'watercolor_paper_craft',
        'note': '',
        'members': {s: p for s, p in [
            ('character_young_man_stand_v1', 'stand'), ('character_young_man_seated_v1', 'seated'),
            ('character_young_man_walk_v1', 'walk'), ('character_young_man_reach_v1', 'reach')]},
    },
    'older_man_cn': {
        'label': '中国老年男性·白发深绿衬衫', 'style': 'watercolor_paper_craft',
        'note': '扶杖与轮椅为带器整件；站坐转换只有中间姿态，完整坐立过程见公共动作包。',
        'members': {s: p for s, p in [
            ('character_older_man_stand_v1', 'stand'), ('character_older_man_seated_v1', 'seated'),
            ('character_older_man_walk_v1', 'walk'), ('character_older_man_reach_v1', 'reach'),
            ('character_older_man_sit_transition_v1', 'sit_transition'),
            ('character_older_man_cane_v1', 'stand_with_cane'),
            ('character_older_man_wheelchair_v1', 'seated_wheelchair')]},
    },
    'older_woman_cn': {
        'label': '中国老年女性·白发浅绿开衫', 'style': 'watercolor_paper_craft',
        'note': '站坐转换只有中间姿态，完整坐立过程见公共动作包。',
        'members': {s: p for s, p in [
            ('character_older_woman_stand_v1', 'stand'), ('character_older_woman_seated_v1', 'seated'),
            ('character_older_woman_walk_v1', 'walk'), ('character_older_woman_reach_v1', 'reach'),
            ('character_older_woman_sit_transition_v1', 'sit_transition')]},
    },
    'pregnant_woman_cn': {
        'label': '中国孕妇·芥黄开衫青绿长裤（体型变体）', 'style': 'watercolor_paper_craft',
        'note': '与 adult_woman_cn_mustard 视觉同源（同一套服装与发型）；同镜出现需明确区分体型，不得当成两个人。',
        'members': {s: p for s, p in [
            ('character_pregnant_woman_stand_v1', 'stand'), ('character_pregnant_woman_seated_v1', 'seated'),
            ('character_pregnant_woman_walk_v1', 'walk'), ('character_pregnant_woman_reach_v1', 'reach')]},
    },
    'generic_presenter_blue_suit': {
        'label': '通用讲解者·蓝色西装（独立身份）', 'style': 'watercolor_paper_craft',
        'note': '原属通用人物，被登记为成年女性会与患者基线串人；单列为独立身份。',
        'members': {'reserve_person_pointing_v1': 'pointing'},
    },
    'generic_lying_blue_tank': {
        'label': '通用卧姿人物·蓝白背心（独立身份）', 'style': 'watercolor_paper_craft',
        'note': '原属通用人物；与成年女性基线不是同一人，单列。',
        'members': {'reserve_person_lying_v1': 'lying'},
    },
}

# families that are visually distinct from the role baseline
EXTRA_FAMILIES = {
    'adult_woman_cn_abpm': {
        'label': '中国成年女性患者·动态血压袖带佩戴（独立身份）',
        'style': 'watercolor_paper_craft',
        'note': '浅蓝上衣蓝裤女性，与芥黄开衫家族不是同一人；只表达已佩戴袖带状态。',
        'members': {'abpm_patient_20261023': 'stand_with_cuff'},
    },
    'older_brother_cn': {
        'label': '中国中老年男性家属·眼镜蓝衬衫卡其裤（独立身份）',
        'style': 'watercolor_paper_craft',
        'note': '家属身份，不属于任何患者基线。',
        'members': {'character_older_brother_stand_v1': 'stand'},
    },
}

# per member notes: visible differences inside one identity family
MEMBER_NOTES = {
    'character_adult_man_upper_abdomen_stool_v1': '同一人物，深蓝长裤坐木凳整件；与红裤版本下装不同。',
    'character_man_alert_armchair_v1': '同一人物，深蓝长裤坐扶手椅整件；与红裤版本下装不同。',
    'character_man_unresponsive_armchair_v1': '同一人物，深蓝长裤低头坐扶手椅整件；与红裤版本下装不同。',
    'character_pregnant_woman_stand_v1': '与芥黄开衫成年女性视觉同源，此处为妊娠体型；同镜出现需明确体型区分。',
}

# production figures that were used in episodes but never admitted to the library
NOT_ADMITTED = {
    'body': {
        'episodes': 74,
        'sha256': '1dc69e2dbfdf2d7088667a1dcd1ffb1361e291225288df6b738790cf2a712d23',
        'observed': '短发欧美女性，水彩写实，全身完整纸件，1024x1536 透明底。',
        'reason': '从未入库：无族裔、身份家族、锚点与审看边界；与面向国内观众的既定中国形象方向相反；与整季纸剪贴语言不一致。',
        'replacement': 'adult_woman_cn_mustard',
    },
    'walking': {
        'episodes': 74,
        'sha256': '47304cbbb39051be899472e2f25d407c045dfac6713183f1a992a54794d37fc4',
        'observed': '长发欧美女性，水彩写实，步行单幅，1254x1254 透明底。',
        'reason': '从未入库：无族裔、身份家族、锚点与审看边界；与国内受众方向和整季风格均不一致。',
        'replacement': 'adult_woman_cn_mustard',
    },
    'body-paper-study-v1': {
        'episodes': 5,
        'sha256': None,
        'observed': '固定正面站姿整身一层。',
        'reason': '库内已按“缺少纸件结构与可表演部件”列入淘汰，生产仍在使用。',
        'replacement': 'adult_woman_cn_mustard',
    },
}

# role -> production family. The presenter identity stays in the author library.
ROLE_BASELINE = {
    'adult_woman': 'adult_woman_cn_mustard',
    'adult_man': 'adult_man_cn_green_red',
    'child_girl': 'child_girl_cn',
    'child_boy': 'child_boy_cn',
    'teen_girl': 'teen_girl_cn',
    'teen_boy': 'teen_boy_cn',
    'young_man': 'young_man_cn',
    'older_man': 'older_man_cn',
    'older_woman': 'older_woman_cn',
    'pregnant_woman': 'pregnant_woman_cn',
    'clinician_man': 'clinician_man_cn',
    'clinician_woman': 'clinician_woman_cn',
}


def load(path, default):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value, type(default)) else default
    except (OSError, ValueError):
        return default


def catalog_rows(root):
    text = (root / 'catalog/assets.jsonl').read_text(encoding='utf-8')
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def coverage_revisions(root):
    coverage = load(root / 'collections/character-coverage.json', {})
    chosen = {}
    for role_id, role in (coverage.get('roles') or {}).items():
        for pose, asset_id in (role.get('current_assets') or {}).items():
            if '@' in str(asset_id):
                source_id = str(asset_id).split('@')[0]
                chosen[source_id.removeprefix('paper:')] = str(asset_id).split('@')[-1]
    return chosen


def duplicate_registrations(root):
    """Find source ids registered twice; identical bytes mean a duplicate row, not a new identity."""
    rows = catalog_rows(root)
    by_source = {}
    for row in rows:
        by_source.setdefault(row.get('source_id'), []).append(row)
    coverage = coverage_revisions(root)
    duplicates = {}
    divergent = {}
    for source_id, items in by_source.items():
        if len(items) < 2:
            continue
        digests = {tuple(sorted(part['sha256'] for part in row.get('payload', [])
                               if part.get('role') == 'payload')) for row in items}
        recommended = coverage.get(source_id)
        if len(digests) == 1:
            keep = next((row for row in items if row.get('revision') == recommended), items[-1])
            duplicates[source_id] = {
                'reason': '同一原件的重复登记修订，载荷字节完全相同；保留推荐版本，另一个退出推荐。',
                'keep': keep.get('id'),
                'duplicate': [row.get('id') for row in items if row.get('id') != keep.get('id')],
            }
        else:
            divergent[source_id] = [row.get('id') for row in items]
    return duplicates, divergent


def resolve(root, source_id, coverage_rev):
    rows = [r for r in catalog_rows(root) if r.get('source_id') == source_id]
    if not rows:
        return None, 'missing_from_catalog'
    for row in rows:
        if row.get('revision') == coverage_rev:
            return row, 'coverage_current'
    if len(rows) == 1:
        return rows[0], 'single_revision'
    return rows[-1], 'latest_by_catalog_order'


def build(root=ROOT):
    coverage_rev = coverage_revisions(root)
    duplicates, divergent = duplicate_registrations(root)
    families = {}
    problems = []
    for family_id, spec in {**FAMILIES, **EXTRA_FAMILIES}.items():
        members = {}
        for source_id, pose in spec['members'].items():
            row, how = resolve(root, source_id, coverage_rev.get(source_id, ''))
            if row is None:
                problems.append(f'{family_id}:{source_id}:missing_from_catalog')
                continue
            payload = next((p for p in row.get('payload', []) if p.get('role') == 'payload'), {})
            members[source_id] = {
                'asset_id': row.get('id'),
                'revision': row.get('revision'),
                'pose': pose,
                'payload_sha256': payload.get('sha256'),
                'content_bounds': row.get('content_bounds'),
                'revision_selection': how,
                'note': MEMBER_NOTES.get(source_id, ''),
            }
        families[family_id] = {
            'label': spec['label'],
            'style': spec['style'],
            'note': spec.get('note', ''),
            'verified_on': '2026-10-24',
            'verification': '已逐张查看原件（浅底合成）比对脸部、发型、服装与体型；不是按文件名或修订顺序推断。',
            'members': members,
        }
    registry = {
        'schema': 'mac_character_identity_baseline/v1',
        'families_order': sorted({**FAMILIES, **EXTRA_FAMILIES}),
        'policy': '生产只使用本表登记的身份；跨镜连续表演在同一身份家族内选姿态。未登记的素材不得作为生产人物推荐。',
        'families': families,
        'role_baseline': ROLE_BASELINE,
        'presenter_identity': {
            'author_id': 'dr_mie',
            'location': '作者私有库 assets/authors/dr_mie/library/（不进入公共库）',
            'rule': '所有医生身份默认解析到讲者；承担其他身份的医生必须显式选择 clinician_man_cn / clinician_woman_cn。',
        },
        'duplicate_registrations': duplicates,
        'divergent_registrations': divergent,
        'not_admitted_production_assets': NOT_ADMITTED,
        'problems': problems,
    }
    return registry


def verify(root=ROOT, registry=None):
    if registry is None:
        try:
            registry = json.loads((root / OUT).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return ['baseline_file_missing']
    errors = []
    if not isinstance(registry, dict) or registry.get('schema') != 'mac_character_identity_baseline/v1':
        return ['baseline_missing_or_wrong_schema']
    rows = catalog_rows(root)
    by_id = {r.get('id'): r for r in rows}
    for family_id, family in (registry.get('families') or {}).items():
        for source_id, member in (family.get('members') or {}).items():
            row = by_id.get(member.get('asset_id'))
            if row is None:
                errors.append(f'{family_id}:{source_id}:asset_not_in_catalog')
                continue
            if row.get('revision') != member.get('revision'):
                errors.append(f'{family_id}:{source_id}:revision_mismatch')
            payload = next((p for p in row.get('payload', []) if p.get('role') == 'payload'), {})
            if payload.get('sha256') != member.get('payload_sha256'):
                errors.append(f'{family_id}:{source_id}:payload_sha_mismatch')
    for role, family_id in (registry.get('role_baseline') or {}).items():
        if family_id not in (registry.get('families') or {}):
            errors.append(f'role_baseline_unknown_family:{role}:{family_id}')
    for source_id, entry in (registry.get('duplicate_registrations') or {}).items():
        rows = [row for row in catalog_rows(root) if row.get('source_id') == source_id]
        digests = {tuple(sorted(part['sha256'] for part in row.get('payload', [])
                               if part.get('role') == 'payload')) for row in rows}
        if len(digests) != 1:
            errors.append(f'duplicate_claim_payload_differs:{source_id}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    registry = build(root)
    errors = verify(root, registry) + registry.get('problems', [])
    if args.check:
        stored = verify(root)
        try:
            current = json.loads((root / OUT).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            current = None
        stale = current != registry
        print(json.dumps({'status': 'passed' if not stored and not stale else 'stale',
                          'stored_errors': stored, 'rebuild_differs': stale,
                          'families': len(registry.get('families') or {})},
                         ensure_ascii=False))
        return 0 if not stored and not stale else 2
    (root / OUT).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT).write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'written', 'path': OUT, 'families': len(registry['families']),
                      'members': sum(len(f['members']) for f in registry['families'].values()),
                      'errors': errors}, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == '__main__':
    raise SystemExit(main())
