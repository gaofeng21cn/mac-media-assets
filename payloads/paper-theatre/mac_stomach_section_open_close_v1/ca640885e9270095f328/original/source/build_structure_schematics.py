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
    wall = path('M290 385 C255 480 300 670 440 785 L595 890 '
                'C690 805 772 585 728 420 C688 290 555 284 500 352 '
                'C430 288 325 300 290 385 Z', '#d89483')
    # Anatomical right is on the left of this frontal schematic.
    ra = path('M320 390 Q360 332 446 375 L452 494 Q365 516 320 470 Z', '#b9d3e0')
    la = path('M536 372 Q620 326 688 402 L682 477 Q600 496 540 470 Z', '#e8bd9a')
    rv = path('M324 526 Q380 500 459 530 Q455 640 549 780 '
              'C423 728 342 650 324 526 Z', '#b9d3e0')
    lv = path('M545 530 Q604 502 670 534 Q702 678 595 812 '
              'Q510 687 545 530 Z', '#f5e7cc')
    septum = path('M500 500 Q472 656 581 832', 'none', '#bb7462', 22)
    cava = path('M340 170 L340 373 M340 461 L340 628', 'none', '#8ba7b5', 46)
    aorta = path('M578 383 L578 263 Q582 161 661 164 Q739 169 740 257 L740 334',
                 'none', '#c98577', 48, 'stroke-linecap="round"')
    pulmonary = path('M454 392 L454 262 Q484 236 526 249 L632 282 M490 252 L377 255',
                     'none', '#8ba7b5', 36, 'stroke-linecap="round"')
    veins = path('M686 409 L784 377 M680 447 L779 445', 'none', '#c98577', 26)
    vessels = cava + aorta + pulmonary + veins
    return ({'heart_wall': wall, 'four_chambers': ra + la + rv + lv + septum,
             'great_vessels': vessels}, wall + vessels,
            {'focus': {'x': .51, 'y': .55}, 'septum': {'x': .50, 'y': .62}, 'apex': {'x': .58, 'y': .87}},
            '心脏正面四腔关系示意，画面左为解剖右；右房右室与左房左室分别表达。血管为连接概览，未表达瓣膜细节、血流动画或真实比例。')


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
    simple = trachea + bronchus + left + right
    right_fissures = path('M343 500 Q398 518 480 527 M348 704 Q410 606 480 568',
                           'none', '#b46f60', 6)
    left_fissure = path('M681 690 Q631 595 551 528', 'none', '#b46f60', 6)
    return ({'trachea_bronchi': trachea + bronchus,
             'right_lung_anatomical': left + right_fissures,
             'left_lung_anatomical': right + left_fissure}, simple,
            {'focus': {'x': .5, 'y': .55}, 'carina': {'x': .5, 'y': .30}},
            '肺与气管支气管正面示意，解剖右肺在画面左，三叶由两条裂隙提示；解剖左肺在画面右。不表达支气管肺段、肺功能或病变。')


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
    # Anterior view: fundus/body are image-right; outlet turns image-left.
    wall = path('M574 180 L638 180 L638 290 C734 242 832 326 844 448 '
                'C868 614 758 796 598 820 C444 846 328 760 306 650 '
                'L274 650 L274 590 L364 590 C428 598 486 557 514 496 '
                'C548 424 562 348 574 290 Z', '#d89483')
    lumen = path('M592 205 L619 205 L619 322 C706 272 798 344 812 450 '
                 'C830 599 736 758 593 786 C466 810 360 740 338 628 '
                 'L290 628 L290 610 L364 610 C440 618 512 566 540 503 '
                 'C574 430 583 354 592 300 Z', '#f5e7cc', '#b28b54', 4)
    openings = path('M574 292 L638 292 M318 590 L318 650', 'none', '#bb7462', 10)
    simple = wall
    return ({'stomach_wall': wall, 'gastric_lumen': lumen, 'cardia_pylorus': openings}, simple,
            {'focus': {'x': .59, 'y': .54}, 'cardia': {'x': .59, 'y': .29},
             'pylorus': {'x': .31, 'y': .61}},
            '胃正面关系示意，画面右侧为胃底和胃体，食管入口在上，幽门向画面左侧延续；胃腔与胃壁分别揭示。不表达胃壁组织层、真实容积或胃排空功能。')


def intestine():
    colon_line = ('M300 723 L300 330 Q300 273 360 293 '
                  'Q515 365 666 298 Q728 274 728 340 L728 688 '
                  'Q730 760 654 766 Q566 770 532 842 L532 903')
    colon = path(colon_line, 'none', '#c98577', 96, 'stroke-linecap="round"')
    colon += path(colon_line, 'none', '#e8bd9a', 72, 'stroke-linecap="round"')
    loops = path('M380 408 C454 370 648 390 650 442 '
                 'C650 486 386 446 382 496 C378 546 648 506 650 560 '
                 'C652 608 380 572 382 626 C384 674 637 642 644 695 '
                 'Q626 743 390 701', 'none', '#d89483', 42, 'stroke-linecap="round"')
    appendix = path('M300 744 Q302 800 270 818', 'none', '#c98577', 15,
                    'stroke-linecap="round"')
    simple_loops = path('M393 440 Q631 400 632 472 Q631 520 393 534 '
                        'Q372 606 620 620 Q650 680 396 695',
                        'none', '#d89483', 52, 'stroke-linecap="round"')
    return ({'colon': colon + appendix, 'small_intestine': loops}, colon + simple_loops,
            {'focus': {'x': .5, 'y': .53}, 'small_intestine': {'x': .5, 'y': .55}},
            '正面肠道关系示意：结肠构成外围，上行结肠在画面左，小肠盘曲于内；直肠向下。示意层数与曲数不代表真实长度。')


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
    # Local islet tissue, not an organ outline incorrectly labelled as an islet.
    surround = ''
    for cx, cy in [(234,290),(512,192),(789,293),(827,658),(642,834),(297,785),(181,549)]:
        for dx, dy in [(-42,-24),(40,-24),(0,44)]:
            surround += ellipse(cx+dx,cy+dy,47,43,'#e6c992','#b6a071',4)
        surround += ellipse(cx,cy,15,13,'#f5e7cc','#b6a071',3)
    boundary = ellipse(512,512,246,238,'#f2e0c2','#b6a071',5)
    cells = ''
    for i,(cx,cy,rx,ry) in enumerate([(370,414,47,43),(482,378,50,43),(596,403,49,44),
        (680,490,44,46),(617,580,46,42),(648,659,40,40),(536,680,48,42),
        (423,646,47,43),(350,555,45,43),(453,520,49,45),(556,507,45,43)]):
        cells += ellipse(cx,cy,rx,ry,'#d89483' if i%3 else '#e8bd9a','#a77466',3)
        cells += ellipse(cx+7,cy-3,10,9,'#905447','none',0)
    capillaries = path('M265 468 Q324 478 391 476 Q470 456 510 442 '
                        'Q564 429 610 455 Q659 483 730 456 '
                        'M391 476 Q397 566 477 584 Q529 600 574 570 '
                        'M477 584 Q476 648 497 749',
                        'none','#8ba7b5',13,'stroke-linecap="round"')
    simple = boundary + cells
    return ({'exocrine_surroundings': surround, 'endocrine_cells': boundary+cells,
             'capillary_network': capillaries}, simple,
            {'focus': {'x': .5, 'y': .5}, 'islet': {'x': .5, 'y': .5}},
            '胰岛局部组织关系示意：中央为成簇内分泌细胞，周围为外分泌腺泡，毛细血管在细胞间分支。颜色不指定细胞类型，数量与分布不代表真实比例；不是胰腺整器官总览，不表达分泌或血糖调节。')


def alveolus():
    # One connected duct/sac makes the air-space continuity explicit.
    wall = path('M462 164 L562 164 L562 329 C702 344 794 450 794 591 '
                'C794 750 675 842 513 842 C351 842 232 747 232 586 '
                'C232 449 326 345 462 329 Z', '#d89483')
    lumen = path('M483 184 L541 184 L541 351 C674 360 769 458 769 591 '
                 'C769 734 661 817 513 817 C365 817 257 731 257 586 '
                 'C257 458 350 361 483 351 Z', '#f5e7cc','#bb7462',4)
    capillary = path('M254 346 C170 438 166 578 215 698 Q270 833 428 882 '
                     'M609 876 C769 829 856 711 858 569 Q859 434 768 354',
                     'none','#8ba7b5',18,'stroke-linecap="round"')
    capillary += path('M264 376 C194 476 199 606 244 685 Q296 800 433 853 '
                      'M604 849 Q745 800 813 672 C855 553 827 445 748 374',
                      'none','#c98577',14,'stroke-linecap="round"')
    return ({'alveolar_wall': wall, 'continuous_air_space': lumen,
             'perialveolar_capillaries': capillary}, wall+lumen,
            {'focus': {'x': .5, 'y': .57}, 'airway_opening': {'x': .5, 'y': .17}},
            '单个肺泡与相连气道的放大关系示意：气腔连续、薄壁在外、毛细血管环绕壁外。壁厚与血管间距为说明而夸张，双色仅区分血管路径，不表达氧含量、流向或气体交换数值。')


def blood_cell():
    tilt = 'transform="rotate(-16 512 512)"'
    disc = ellipse(512, 512, 330, 238, '#c98577', STROKE, 5, tilt)
    membrane = ellipse(512, 512, 330, 238, 'none', '#905447', 8, tilt)
    cytoplasm = ellipse(512, 512, 330, 238, '#c98577', '#905447', 5, tilt)
    centre = ellipse(512, 512, 158, 104, '#e8bd9a', '#b28b54', 4, tilt)
    simple = disc
    return ({'cytoplasm': cytoplasm, 'membrane': membrane, 'central_pallor': centre}, simple,
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
            {'focus': {'x': .52, 'y': .48}, 'nipple': {'x': 700/1024, 'y': 556/1024}},
            '乳腺侧视外形示意，附腺体区与乳管走向；不表示肿块大小、分期或触诊结论。')


def foot_joint():
    tibia = path('M416 150 L528 150 L539 429 Q493 465 432 438 Z', '#e6c992')
    fibula = path('M368 153 L401 153 L414 482 L378 505 Z', '#d9c58a')
    talus = path('M416 478 Q455 455 527 468 Q568 486 567 535 '
                 'L480 572 L408 547 Q396 507 416 478 Z', '#e6c992')
    calcaneus = path('M361 559 Q412 538 480 584 Q529 620 515 682 '
                    'L360 705 Q322 648 338 602 Z', '#e6c992')
    midfoot = path('M573 535 L645 578 L626 645 L526 648 L510 589 Z', '#e6c992')
    metatarsals = path('M655 591 L789 668 L771 704 L640 660 Z', '#e6c992')
    toes = path('M800 672 Q856 688 855 725 L789 723 L782 708 Z', '#e6c992')
    # Narrow cartilage boundaries follow the articular surfaces.
    joint = path('M430 451 Q481 475 535 445 M415 475 Q465 450 524 465',
                 'none', '#b9d3e0', 7, 'stroke-linecap="round"')
    ligament = path('M390 478 L438 562 M400 488 L363 611', 'none', '#9dafa3', 10)
    bones = tibia + fibula + talus + calcaneus + midfoot + metatarsals + toes
    return ({'bones': bones, 'joint_space': joint, 'ligaments': ligament}, bones,
            {'focus': {'x': .47, 'y': .48}, 'ankle_joint': {'x': .46, 'y': .45}},
            '踝足侧面关系示意：胫腓骨位于距骨上方、跟骨位于后下方，前足向画面右伸展；关节间隙为窄边界，不画成覆盖骨面的空洞。')


def pelvic_organs():
    pelvis_bone = path('M205 310 Q212 224 311 254 L375 324 L343 495 '
                      'L381 695 L323 759 Q247 646 235 491 Z', '#e6c992')
    pelvis_bone += path('M819 310 Q812 224 713 254 L649 324 L681 495 '
                       'L643 695 L701 759 Q777 646 789 491 Z', '#e6c992')
    uterus = path('M512 377 C455 335 402 370 425 437 Q452 511 488 550 '
                  'L489 596 L535 596 L536 550 Q572 511 599 437 '
                  'C622 370 569 335 512 377 Z', '#d89483')
    uterus += path('M489 596 L489 690 L535 690 L535 596', '#e8bd9a')
    tubes = path('M435 391 Q369 335 314 382 Q286 413 333 439 '
                 'M589 391 Q655 335 710 382 Q738 413 691 439',
                 'none', '#c98577', 15, 'stroke-linecap="round"')
    ovaries = ellipse(338,454,43,29,'#e8bd9a')+ellipse(686,454,43,29,'#e8bd9a')
    bladder = path('M399 627 C393 552 631 552 625 627 Q617 704 512 722 '
                   'Q407 704 399 627 Z', '#9dafa3', extra='opacity="0.72"')
    rectum = path('M562 507 Q611 610 574 760', 'none', '#b28b54', 30,
                  'stroke-dasharray="16 12" opacity="0.7"')
    return ({'pelvis_bone': pelvis_bone, 'rectum_posterior_projection': rectum,
             'uterus_tubes_ovaries': uterus+tubes+ovaries, 'bladder_anterior_projection': bladder},
            pelvis_bone+uterus+tubes+ovaries,
            {'focus': {'x': .5, 'y': .51}, 'ovary_left': {'x': 338/1024, 'y': 454/1024}},
            '女性盆腔正面投影示意，子宫连输卵管与两侧卵巢；膀胱为前方半透明投影，直肠为后方虚线投影。前后深度需结合侧视图解释，非同一冠状切面。')


def head_sagittal():
    skull = path('M362 171 C502 115 692 161 758 292 Q793 356 779 409 '
                 'L838 476 Q854 501 797 512 L797 550 Q824 567 793 586 '
                 'Q800 648 741 674 L690 696 L690 844 L435 844 '
                 'L435 735 C338 693 286 604 286 465 C282 331 300 209 362 171 Z', '#e6c992')
    cerebrum = path('M359 484 C320 397 341 272 438 228 C547 175 694 228 732 331 '
                    'C763 407 723 460 666 492 Q597 530 532 507 '
                    'Q443 534 359 484 Z', '#d89483')
    cerebellum = ellipse(408,565,76,62,'#c98577')
    brainstem = path('M493 488 Q540 489 545 538 L554 660 L521 683 '
                     'L505 576 Q477 552 475 525 Z','#e8bd9a')
    stalk = path('M622 475 L638 516','none','#bb7462',9,'stroke-linecap="round"')
    pituitary = ellipse(642,526,18,13,'#c98577')
    sinuses = path('M743 362 Q770 380 761 409 L737 403 Z','#b9d3e0','#8ba7b5',4)
    sinuses += path('M697 488 Q730 472 748 494 L733 527 L697 521 Z','#b9d3e0','#8ba7b5',4)
    return ({'head_profile': skull, 'brain_and_brainstem': cerebrum+cerebellum+brainstem,
             'pituitary_and_stalk': stalk+pituitary, 'paranasal_sinuses': sinuses}, skull,
            {'focus': {'x': .53, 'y': .48}, 'pituitary': {'x': 642/1024, 'y': 526/1024}},
            '头部向画面右的矢状位关系示意：大脑在颅内、小脑在后下、脑干向下，垂体经柄位于脑底，鼻旁窦位于面部后方。仅作位置说明，非影像切面；细节需独立近景，不表达脑沟回、垂体真实大小或病变。')


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
        if payload_root.exists() or record_path.exists():
            raise ValueError(f'不可覆盖已有版本：{item["id"]}@{revision}')
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
            'asset_bundle': metadata['asset_bundle'],
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
