#!/usr/bin/env python3
"""Original editable structure schematics: simplified outline plus registered layers.

The purpose matrix needs two different jobs per object: a silhouette that still
reads at phone width, and a close-up whose layers share one viewbox so the
same transform can reveal them one by one. Both come from the same vector
source, so the two versions cannot drift apart.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'work' / 'structure-schematics-20261024'
STROKE = '#664c45'


def path(d, fill, stroke=STROKE, width=5, extra=''):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linejoin="round" {extra}/>')


def ellipse(cx, cy, rx, ry, fill, stroke=STROKE, width=5, extra=''):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}" {extra}/>')


def rect(x, y, w, h, rx, fill, stroke=STROKE, width=5, extra=''):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}" {extra}/>')


def svg(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" '
            'viewBox="0 0 1024 1024">' + body + '</svg>')


def heart():
    aorta = path('M470 250 Q452 176 470 120 L566 120 Q584 178 566 250 Z', '#c98577')
    pulm_a = path('M596 268 Q640 226 690 268 L690 322 Q640 292 596 322 Z', '#c98577')
    pulm_v = path('M428 268 Q384 226 334 268 L334 322 Q384 292 428 322 Z', '#c98577')
    vessels = aorta + pulm_a + pulm_v
    wall = path('M512 872 C300 760 214 592 246 452 C268 348 372 300 512 396 '
                'C652 300 756 348 778 452 C810 592 724 760 512 872 Z', '#d89483')
    septum = path('M512 420 L512 800 L546 800 L546 420 Z', '#bb7462', '#905447', 3)
    left_cavity = path('M512 470 C430 438 358 452 330 520 C304 584 350 664 512 742 Z', '#f5e7cc', '#b28b54', 4)
    right_cavity = path('M512 470 C594 438 666 452 694 520 C720 584 674 664 512 742 Z', '#f5e7cc', '#b28b54', 4)
    simple = vessels + wall
    return ({'heart_wall': wall, 'ventricles': septum + left_cavity + right_cavity,
             'great_vessels': vessels}, simple,
            {'focus': {'x': .5, 'y': .56}, 'septum': {'x': .5, 'y': .58}, 'apex': {'x': .5, 'y': .85}},
            '心脏正面示意，区分心壁、左右心腔、室间隔与出入大血管；不做血流方向、瓣膜形态或收缩期变化示意。')


def lungs():
    trachea = rect(474, 96, 76, 190, 34, '#d5d4bf', '#6e7971', 5)
    trachea += ''.join(f'<path d="M482 {y} Q512 {y+14} 542 {y}" fill="none" stroke="#9dafa3" stroke-width="10"/>'
                       for y in range(140, 270, 48))
    bronchus = path('M512 268 L512 320 M512 300 L392 352 M512 300 L632 352', 'none', '#9dafa3', 16,
                    'stroke-linecap="round"')
    left = path('M452 322 C352 356 300 486 314 632 C328 776 420 856 470 806 '
                'C508 766 486 646 470 528 C456 424 470 336 452 322 Z', '#d89483')
    right = path('M572 322 C672 356 724 486 710 632 C696 776 604 856 554 806 '
                 'C516 766 538 646 554 528 C568 424 554 336 572 322 Z', '#d89483')
    simple = trachea + left + right
    return ({'trachea_bronchi': trachea + bronchus, 'left_lung': left, 'right_lung': right}, simple,
            {'focus': {'x': .5, 'y': .55}, 'carina': {'x': .5, 'y': .30}},
            '肺与气管支气管示意，左右为画面左右；不表示肺叶分段、肺功能或病变。')


def liver():
    right = path('M224 402 C206 292 306 202 462 214 C586 224 678 292 700 356 '
                 'C716 402 686 452 616 478 C520 514 360 522 268 486 Q236 458 224 402 Z', '#bb7462')
    left = path('M700 356 C782 372 828 428 806 478 C782 530 704 520 662 484 '
                'C640 460 664 384 700 356 Z', '#bb7462')
    gallbladder = path('M436 500 C418 552 430 606 470 626 C510 606 522 552 504 500 Z', '#9dafa3')
    duct = path('M498 512 Q560 500 616 470', 'none', '#e6c992', 14, 'stroke-linecap="round"')
    simple = right + left
    return ({'right_lobe': right, 'left_lobe': left, 'gallbladder': gallbladder, 'bile_duct': duct}, simple,
            {'focus': {'x': .46, 'y': .38}, 'gallbladder': {'x': .47, 'y': .55}},
            '肝脏外形示意，区分左右叶、胆囊与胆道走向；不表示肝内血管分段、肝功能或病灶。')


def stomach():
    cardia = path('M470 214 Q512 200 552 216', 'none', '#bb7462', 12, 'stroke-linecap="round"')
    wall = path('M470 214 C400 250 356 350 380 452 C402 548 486 596 566 622 '
                'C650 650 692 700 668 762 C644 822 556 844 494 812 '
                'C432 780 404 714 372 660 C322 570 316 430 372 330 C406 268 440 232 470 214 Z', '#d89483')
    lumen = path('M492 262 C440 292 410 366 424 444 C438 520 508 558 572 578 '
                 'C636 598 656 676 624 720 C600 752 546 760 506 738 '
                 'C462 712 442 656 414 616 C376 556 362 452 402 380 C424 340 460 288 492 262 Z', '#f5e7cc', '#b28b54', 4)
    pylorus = path('M664 742 Q700 756 716 786', 'none', '#bb7462', 12, 'stroke-linecap="round"')
    simple = path('M470 214 C400 250 356 350 380 452 C402 548 486 596 566 622 '
                  'C650 650 692 700 668 762 C644 822 556 844 494 812 '
                  'C432 780 404 714 372 660 C322 570 316 430 372 330 C406 268 440 232 470 214 Z', '#d89483')
    return ({'stomach_wall': wall, 'gastric_lumen': lumen, 'cardia_pylorus': cardia + pylorus}, simple,
            {'focus': {'x': .52, 'y': .55}, 'pylorus': {'x': .69, 'y': .76}},
            '胃外形与腔面示意，区分胃壁、胃腔与贲门幽门走向；不表示胃分层解剖、胃酸或疾病。')


def intestine():
    tube = path('M300 250 Q520 210 726 268 Q820 296 792 372 Q764 440 640 424 '
                'Q540 410 560 486 Q580 560 700 566 Q800 572 806 664 Q812 758 700 790 '
                'Q600 818 470 780 Q340 742 322 654 Q304 566 400 548 Q480 532 470 470 '
                'Q460 408 356 404 Q268 400 268 330 Q268 276 300 250 Z', '#d89483')
    inner = path('M318 268 Q520 232 708 288 Q788 312 766 366 Q744 416 636 402 '
                 'Q528 388 546 478 Q562 538 690 544 Q782 550 786 658 Q790 742 694 768 '
                 'Q600 794 482 762 Q360 728 342 652 Q326 578 404 562 Q470 548 458 476 '
                 'Q446 426 356 424 Q288 420 288 336 Q288 286 318 268 Z', '#f5e7cc', '#b28b54', 4)
    simple = path('M300 250 Q520 210 726 268 Q820 296 792 372 Q764 440 640 424 '
                  'Q540 410 560 486 Q580 560 700 566 Q800 572 806 664 Q812 758 700 790 '
                  'Q600 818 470 780 Q340 742 322 654 Q304 566 400 548 Q480 532 470 470 '
                  'Q460 408 356 404 Q268 400 268 330 Q268 276 300 250 Z', '#d89483')
    return ({'bowel_wall': tube, 'bowel_lumen': inner}, simple,
            {'focus': {'x': .52, 'y': .52}, 'loop': {'x': .56, 'y': .52}},
            '肠道盘曲外形与腔面示意；不区分小肠各段、结肠分段或吸收部位。')


def gallbladder():
    wall = path('M512 196 C556 196 590 250 602 322 C642 406 672 486 672 552 '
                'C672 692 610 790 512 812 C414 790 352 692 352 552 '
                'C352 486 382 406 422 322 C434 250 468 196 512 196 Z', '#9dafa3')
    bile = path('M512 300 C566 300 598 370 612 440 C636 500 652 542 652 566 '
                'C652 664 598 726 512 742 C426 726 372 664 372 566 '
                'C372 542 388 500 412 440 C426 370 458 300 512 300 Z', '#e6c992', '#b28b54', 4)
    duct = path('M512 196 Q512 150 560 132', 'none', '#9dafa3', 16, 'stroke-linecap="round"')
    simple = wall
    return ({'gallbladder_wall': wall, 'bile': bile, 'cystic_duct': duct}, simple,
            {'focus': {'x': .5, 'y': .52}, 'duct_end': {'x': .55, 'y': .16}},
            '胆囊外形与胆汁示意；不表示胆囊内结石、胆道梗阻或胆囊功能。')


def islet():
    pancreas = path('M196 560 C280 486 380 462 470 486 C560 510 660 500 748 452 '
                    'C812 416 856 452 832 512 C790 606 660 690 512 700 '
                    'C380 708 268 664 196 560 Z', '#e6c992')
    head = path('M196 560 C246 512 300 484 352 474 C300 520 268 566 254 618 '
                'C226 610 206 590 196 560 Z', '#d9c58a', '#b28b54', 4)
    clusters = ''.join(ellipse(cx, cy, rx, ry, '#c98577', '#905447', 4) for cx, cy, rx, ry in [
        (330, 560, 42, 32), (470, 600, 46, 34), (610, 556, 40, 30), (700, 500, 34, 26)])
    cells = ''.join(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#f5e7cc"/>' for cx, cy in [
        (318, 552), (342, 566), (458, 592), (484, 606), (600, 548), (622, 562), (692, 494), (710, 506)])
    simple = pancreas
    return ({'pancreas': pancreas + head, 'islets': clusters, 'islet_cells': cells}, simple,
            {'focus': {'x': .46, 'y': .56}, 'islet': {'x': .46, 'y': .58}},
            '胰腺与胰岛位置示意，胰岛细胞为示意点；不表示胰岛数量、细胞比例或血糖调节机制。')


def alveolus():
    sacs = []
    for cx, cy, r in [(360, 400, 132), (520, 330, 150), (676, 412, 128), (430, 560, 146),
                      (600, 590, 138), (512, 720, 120)]:
        sacs.append(ellipse(cx, cy, r, r * 0.86, '#d89483'))
    wall = ''.join(sacs)
    inner = ''.join(ellipse(cx, cy, r * 0.72, r * 0.58, '#f5e7cc', '#b28b54', 4)
                    for cx, cy, r in [(360, 400, 132), (520, 330, 150), (676, 412, 128),
                                      (430, 560, 146), (600, 590, 138), (512, 720, 120)])
    capillary = path('M250 800 Q420 720 512 760 Q620 806 790 720', 'none', '#c98577', 18,
                     'stroke-linecap="round"')
    simple = wall
    return ({'alveolar_sacs': wall, 'air_space': inner, 'capillary': capillary}, simple,
            {'focus': {'x': .5, 'y': .55}, 'capillary_end': {'x': .77, 'y': .70}},
            '肺泡囊与气腔示意，附一层毛细血管走向；不表示气体交换比例、肺泡数量或通气功能。')


def blood_cell():
    tilt = 'transform="rotate(-16 512 512)"'
    disc = ellipse(512, 512, 330, 238, '#c98577', STROKE, 5, tilt)
    membrane = ellipse(512, 512, 330, 238, 'none', '#905447', 8, tilt)
    cytoplasm = ellipse(512, 512, 258, 178, '#d89483', '#b28b54', 4, tilt)
    centre = ellipse(512, 512, 158, 104, '#e8bd9a', '#b28b54', 4, tilt)
    simple = disc
    return ({'membrane': membrane, 'cytoplasm': cytoplasm, 'central_pallor': centre}, simple,
            {'focus': {'x': .5, 'y': .5}, 'centre': {'x': .5, 'y': .5}},
            '红细胞双凹圆盘正视示意，区分膜、胞质与中央淡区；不表示血红蛋白含量、形态学分类或血液病。')


def breast():
    chest = rect(250, 170, 130, 700, 26, '#e6c992')
    dome = path('M370 560 C370 400 500 310 616 336 C712 358 742 452 704 536 '
                'C664 624 512 646 370 596 Z', '#e8bd9a')
    gland = path('M404 560 C404 434 512 362 606 380 C680 394 706 460 678 522 '
                 'C644 588 520 606 404 572 Z', '#f2e0c2', '#c8a882', 4)
    ducts = ''.join(f'<path d="M{nx} 560 Q{nx-70} 470 {int(nx/2)+40} 424" fill="none" '
                    'stroke="#c98577" stroke-width="10" stroke-linecap="round"/>' for nx in (676, 700))
    nipple = ellipse(700, 556, 30, 24, '#d89483')
    simple = chest + dome
    return ({'breast_outline': chest + dome, 'gland_tissue': gland, 'ducts': ducts + nipple}, simple,
            {'focus': {'x': .52, 'y': .48}, 'nipple': {'x': .68, 'y': .68}},
            '乳腺侧视外形示意，附腺体区与乳管走向；不表示肿块大小、分期或触诊结论。')


def foot_joint():
    tibia = path('M420 150 L520 150 L520 470 L470 500 L420 470 Z', '#e6c992')
    talus = ellipse(500, 540, 92, 74, '#d89483')
    calcaneus = path('M520 560 Q640 560 636 660 Q632 744 540 740 Q486 736 486 676 Z', '#d89483')
    foot = path('M420 600 Q500 640 560 686 Q636 740 760 752 Q830 760 838 812 Q844 860 760 866 '
                'Q560 880 420 790 Q352 742 356 664 Q360 610 420 600 Z', '#d89483')
    joint = ellipse(486, 548, 96, 78, '#f5e7cc', '#b28b54', 4)
    ligament = path('M470 470 Q520 500 556 470 M462 520 Q512 552 560 520', 'none', '#9dafa3', 12,
                    'stroke-linecap="round"')
    simple = tibia + talus + foot
    return ({'bones': tibia + talus + calcaneus + foot, 'joint_space': joint, 'ligaments': ligament}, simple,
            {'focus': {'x': .49, 'y': .55}, 'ankle_joint': {'x': .48, 'y': .53}},
            '踝足骨性结构示意，区分骨面、关节间隙与韧带走向；不表示关节间隙正常宽度、骨密度或病变。')


def pelvic_organs():
    bladder = path('M430 520 C430 430 594 430 594 520 C594 596 546 640 512 640 C478 640 430 596 430 520 Z', '#9dafa3')
    uterus = path('M512 300 C560 300 588 344 584 400 C580 452 546 476 512 476 C478 476 444 452 440 400 C436 344 464 300 512 300 Z', '#d89483')
    ovaries = ellipse(430, 392, 52, 40, '#e8bd9a') + ellipse(594, 392, 52, 40, '#e8bd9a')
    rectum = path('M512 700 C560 700 592 760 588 820 C584 876 540 900 512 900 C484 900 440 876 436 820 C432 760 464 700 512 700 Z', '#d9c58a')
    pelvis_bone = path('M286 840 Q262 566 412 470 Q512 414 612 470 Q762 566 738 840 '
                         'L654 840 Q668 626 578 566 Q512 528 446 566 Q356 626 370 840 Z', '#e6c992')
    simple = pelvis_bone + bladder + uterus + ovaries + rectum
    return ({'pelvis_bone': pelvis_bone, 'bladder': bladder, 'uterus': uterus,
             'ovaries': ovaries, 'rectum': rectum}, simple,
            {'focus': {'x': .5, 'y': .55}, 'ovary_left': {'x': .42, 'y': .38}},
            '盆腔器官位置示意（膀胱、子宫、卵巢、直肠），不表示比例、周期变化或病灶。')


def head_sagittal():
    skull = path('M400 176 C576 150 724 246 742 386 C750 452 724 486 748 528 '
                 'C772 570 758 606 706 618 C678 626 664 664 642 696 C610 748 552 786 470 802 '
                 'L392 802 C318 700 288 556 310 420 C330 292 340 190 400 176 Z', '#e6c992')
    brain = path('M430 560 C388 462 418 356 506 312 C584 274 676 292 716 360 '
                 'C748 414 724 486 684 528 C636 578 534 596 462 572 C436 564 440 580 430 560 Z', '#d89483')
    pituitary = ellipse(552, 566, 38, 28, '#c98577')
    sinuses = path('M606 656 Q672 656 690 714 Q634 738 596 700 Z', '#b9d3e0', '#8ba7b5', 4)
    simple = skull
    return ({'skull_profile': skull, 'brain': brain, 'pituitary': pituitary, 'sinus': sinuses}, simple,
            {'focus': {'x': .52, 'y': .52}, 'pituitary': {'x': .54, 'y': .55}},
            '头部矢状位示意，区分颅骨、脑、垂体与鼻窦位置；不表示脑沟回细节、垂体大小或病变。')


STRUCTURES = [
    ('heart', '心脏', heart),
    ('lungs', '肺与气管', lungs),
    ('liver', '肝脏', liver),
    ('stomach', '胃', stomach),
    ('intestine', '肠道', intestine),
    ('gallbladder', '胆囊', gallbladder),
    ('islet', '胰岛', islet),
    ('alveolus', '肺泡', alveolus),
    ('blood_cell', '红细胞', blood_cell),
    ('breast', '乳腺', breast),
    ('foot_joint', '足关节', foot_joint),
    ('pelvic_organs', '盆腔器官', pelvic_organs),
    ('head_sagittal', '头部矢状位', head_sagittal),
]


def build(root=ROOT, stage=STAGE):
    from PIL import Image
    stage = Path(stage)
    root = Path(root)
    rsvg = shutil.which('rsvg-convert') or '/opt/homebrew/bin/rsvg-convert'
    produced = []
    for organ, label, make in STRUCTURES:
        layers, simple, anchors, note = make()
        for mode in ('simple', 'detailed_layers'):
            identifier = f'reserve_{organ}_{mode}_v1'
            folder = stage / identifier
            folder.mkdir(parents=True, exist_ok=True)
            pieces = {'payload': simple} if mode == 'simple' else layers
            files, bundle = [], []
            for name, body in pieces.items():
                vector = folder / f'{name}.svg'
                vector.write_text(svg(body))
                raster = folder / f'{name}.png'
                subprocess.run([rsvg, str(vector), '-o', str(raster)], check=True)
                bounds = list(Image.open(raster).getchannel('A').getbbox())
                files.extend([{'source': str(vector), 'path': f'source/{name}.svg', 'role': 'source'},
                              {'source': str(raster), 'path': f'files/{name}.png', 'role': 'payload'}])
                bundle.append({'asset_id': name, 'path': f'files/{name}.png', 'source_type': 'original_vector',
                               'visual_meaning': f'{label}·{name}', 'medical': True,
                               'content_bounds': bounds,
                               'content_bounds_format': 'pixel_xyxy_right_bottom_exclusive',
                               'registration': {'pivot': {'x': 0, 'y': 0}, 'anchors': anchors,
                                                'canvas_origin': {'x': 0, 'y': 0},
                                                'shared_viewbox': [0, 0, 1024, 1024]}})
            preview = folder / 'preview.svg'
            preview.write_text(svg(''.join(pieces.values())))
            preview_png = folder / 'preview.png'
            subprocess.run([rsvg, str(preview), '-o', str(preview_png)], check=True)
            files.extend([{'source': str(preview), 'path': 'source/preview.svg', 'role': 'source'},
                          {'source': str(preview_png), 'path': 'samples/preview.png', 'role': 'poster'},
                          {'source': str(Path(__file__).resolve()), 'path': 'source/build_structure_schematics.py',
                           'role': 'source'}])
            usage = folder / 'USAGE.md'
            usage.write_text(
                f'# {label}·{"远景简化版" if mode == "simple" else "近景配准分层版"}\n\n{note}\n\n'
                '所有图层共用1024×1024画布与原点；同图层坐标、缩放与旋转必须共用，bounds 只描述可见内容，'
                '不可将每层独立裁切后居中。详版用于能读取内部关系的近景，远景选择 simple 版；'
                '可逐层揭示或高亮独立层，不把横断面与外观当作可连续旋转的三维形体。\n\n'
                '这是原创可编辑结构示意图，只核对基础空间关系；医学正确性与当前镜头仍待医生终审。\n')
            files.append({'source': str(usage), 'path': 'USAGE.md', 'role': 'evidence'})
            produced.append({'id': identifier, 'label': label, 'mode': mode, 'folder': folder,
                             'files': files, 'bundle': bundle, 'anchors': anchors, 'note': note,
                             'preview': preview_png})
    return produced


def register(produced, root=ROOT):
    from apply_character_anchors import canonical_revision
    root = Path(root)
    rows = []
    for item in produced:
        metadata = {
            'id': item['id'],
            'title': f"{item['label']}·" + ('远景简化版' if item['mode'] == 'simple' else '近景配准分层版'),
            'kind': 'medical_cutout', 'entry': 'samples/preview.png', 'asset_bundle': item['bundle'],
            'reuse_scope': {'kind': 'general'}, 'status': 'reusable_candidate',
            'source': {'kind': 'original_vector', 'generator': 'source/build_structure_schematics.py'},
            'tags': ['anatomy', item['id'], item['mode'], 'registered_layers', 'reserve_20261024'],
            'discovery': {'category': 'anatomy', 'aliases': [item['label'], item['mode']],
                          'actions': ['逐层揭示', '局部放大'], 'detail_level': item['mode'],
                          'story_roles': ['结构解释', '位置关系']},
            'assembly': {'shared_viewbox': [0, 0, 1024, 1024],
                         'order': [part['asset_id'] for part in item['bundle']],
                         'operation': 'shared_transform_reveal', 'pre_registered': True},
            'content_bounds': None, 'content_bounds_format': 'pixel_xyxy_right_bottom_exclusive',
            'usage_notes': item['note'], 'medical_review': 'pending',
            'review': {'static_alpha': 'measured', 'full_motion': 'pending', 'current_shot': 'pending'},
            'quality_debt': ['medical_review_pending', 'current_shot_scale_pending'],
        }
        descriptors = [{'path': part['path'], 'role': part['role'],
                        'sha256': hashlib.sha256(Path(part['source']).read_bytes()).hexdigest(),
                        'bytes': Path(part['source']).stat().st_size} for part in item['files']]
        metadata['files'] = descriptors
        revision = canonical_revision(metadata)
        record = {'schema': 'animation_element/v1', **metadata, 'revision': revision}
        payload_root = root / 'payloads/paper-theatre' / item['id'] / revision
        record_path = root / 'records/paper-theatre' / item['id'] / revision / 'record.json'
        record_path.parent.mkdir(parents=True, exist_ok=True)
        for part in item['files']:
            target = payload_root / part['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(part['source'], target)
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        rows.append({
            'id': f"paper:{item['id']}@{revision}", 'source_id': item['id'], 'revision': revision,
            'title': metadata['title'], 'kind': 'medical_cutout',
            'reuse_scope': {'kind': 'general'}, 'tags': metadata['tags'], 'series_ids': [],
            'discovery': metadata['discovery'], 'assembly': metadata['assembly'],
            'registration': {'coordinate_space': 'shared_viewbox_layers',
                            'shared_viewbox': [0, 0, 1024, 1024],
                            'contact_events_ref': None},
            'payload': [{'path': (payload_root / part['path']).relative_to(root).as_posix(),
                         'role': part['role'], 'sha256': part['sha256'], 'bytes': part['bytes']}
                        for part in descriptors],
            'portable_record': record_path.relative_to(root).as_posix(),
            'portable_record_sha256': hashlib.sha256(record_path.read_bytes()).hexdigest(),
            'provenance': {'source_type': 'original_vector',
                           'source_ref': {'generator': 'source/build_structure_schematics.py'}},
            'review_boundary': {'admission': 'reusable_candidate', 'motion': 'pending',
                               'medical': 'pending', 'listening': 'not_applicable',
                               'quality_debt': ['medical_review_pending', 'current_shot_scale_pending']},
        })
    catalog = root / 'catalog/assets.jsonl'
    existing = [json.loads(line) for line in catalog.read_text(encoding='utf-8').splitlines() if line.strip()]
    by_id = {row['id']: row for row in existing}
    for row in rows:
        by_id[row['id']] = row
    merged = sorted(by_id.values(), key=lambda item: item['id'])
    catalog.write_text(''.join(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n' for item in merged),
                       encoding='utf-8')
    discovery_path = root / 'collections/discovery.json'
    collection = json.loads(discovery_path.read_text(encoding='utf-8'))
    for row in rows:
        collection['assets'][row['source_id']] = row['discovery']
    discovery_path.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--stage', default=str(STAGE))
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    produced = build(args.root, args.stage)
    print(json.dumps({'structures': len(produced), 'packages': len(produced)}, ensure_ascii=False))
    if args.register:
        rows = register(produced, args.root)
        print(json.dumps({'registered': len(rows),
                          'ids': [row['id'] for row in rows][:4]}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
