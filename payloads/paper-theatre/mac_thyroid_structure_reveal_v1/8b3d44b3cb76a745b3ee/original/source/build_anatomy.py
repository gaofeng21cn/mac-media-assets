#!/usr/bin/env python3
"""Original editable anatomy schematics with shared-viewbox registered layers."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
sys.path.insert(0, str(WORKSPACE / 'scripts'))
from animation_library import archive


def path(d, fill, stroke='#664c45', width=5, extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" {extra}/>'


def svg(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">' + body + '</svg>'


def thyroid():
    trachea = '<rect x="454" y="112" width="116" height="754" rx="45" fill="#d5d4bf" stroke="#6e7971" stroke-width="5"/>'
    trachea += ''.join(f'<path d="M460 {y} Q512 {y+18} 564 {y}" fill="none" stroke="#9dafa3" stroke-width="12"/>' for y in range(170, 850, 72))
    left = path('M430 264 C387 180 279 225 245 354 C213 473 218 677 292 723 C358 763 422 674 438 571 C453 468 456 333 430 264 Z', '#c78470')
    right = path('M594 264 C637 180 745 225 779 354 C811 473 806 677 732 723 C666 763 602 674 586 571 C571 468 568 333 594 264 Z', '#c78470')
    isthmus = path('M424 482 Q512 502 600 482 L605 548 Q512 566 419 548 Z', '#bb7462')
    simple = trachea + left + right + isthmus
    return {'trachea': trachea, 'lobe_left': left, 'lobe_right': right, 'isthmus': isthmus}, simple, {
        'focus': {'x': .5, 'y': .51}, 'isthmus': {'x': .5, 'y': .515}}, '正面甲状腺与后方气管的简化空间关系；不含甲状软骨、血管、神经或病灶。左右为画面左右，不能据此判断手术层次。'


def kidney():
    outline = 'M593 178 C464 91 280 149 224 340 C166 531 218 762 383 822 C492 863 627 805 647 703 C663 626 594 609 569 541 C545 478 604 450 640 394 C692 313 685 239 593 178 Z'
    cortex = path(outline, '#d89483')
    inner = path('M564 228 C452 169 322 226 280 372 C235 522 274 703 397 758 C479 793 569 760 588 697 C596 668 553 629 528 568 C499 496 533 428 586 367 C628 318 625 266 564 228 Z', '#edb6a5', '#a96859', 4)
    cortex += inner
    pyramids = ''.join(path(d, '#ad6557', '#905447', 3) for d in [
        'M350 248 Q395 217 446 230 L471 390 Z',
        'M280 360 Q290 301 332 271 L443 415 Z',
        'M264 451 Q261 412 279 383 L435 461 Z',
        'M282 589 Q262 551 263 501 L438 517 Z',
        'M334 696 Q296 660 283 620 L455 563 Z',
        'M471 751 Q418 768 371 733 L486 598 Z',
        'M573 690 Q563 731 516 747 L515 598 Z'])
    collecting = path('M472 382 Q486 422 518 431 Q544 461 541 491 Q545 548 569 565 Q603 589 611 628 L616 884 L586 884 L581 637 Q578 613 548 599 Q518 582 500 560 Q476 538 475 508 Q457 476 473 445 Q475 414 472 382 Z', '#f5dca7', '#b28b54', 4)
    collecting += ''.join(f'<path d="{d}" fill="none" stroke="#f5dca7" stroke-width="18" stroke-linecap="round"/>' for d in [
        'M485 439 L468 394', 'M482 457 L450 419', 'M478 478 L441 463',
        'M483 509 L442 518', 'M497 546 L460 562', 'M516 568 L489 599'])
    simple = path(outline, '#cf8977') + path('M588 584 Q608 610 609 649 L614 884 L586 884 L582 642 Q578 617 565 605 Z', '#e6c992')
    return {'cortex': cortex, 'medulla': pyramids, 'collecting_system': collecting}, simple, {
        'focus': {'x': .44, 'y': .48}, 'renal_pelvis': {'x': .506, 'y': .50},
        'ureter_end': {'x': .587, 'y': .86}}, '单肾冠状切面，分开皮质背景、髓质锥体和肾盂/肾盏/输尿管；不表示肾单位微观滤过、血管或精确肾盏数。远景版仅表达肾与输尿管身份。'


def vessel():
    def ring(rx, ry, irx, iry, fill):
        outer = f'M{512-rx} 512 a{rx} {ry} 0 1 0 {2*rx} 0 a{rx} {ry} 0 1 0 {-2*rx} 0 Z'
        inner = f'M{512-irx} 512 a{irx} {iry} 0 1 0 {2*irx} 0 a{irx} {iry} 0 1 0 {-2*irx} 0 Z'
        return path(outer + inner, fill, '#805c50', 4, 'fill-rule="evenodd"')
    adventitia = ring(365, 320, 307, 268, '#d7bb91')
    media = ring(307, 268, 238, 207, '#c98577')
    intima = ring(238, 207, 214, 185, '#e8bd9a')
    lumen = '<ellipse cx="512" cy="512" rx="214" ry="185" fill="#f5e7cc"/>'
    simple = ring(365, 320, 230, 200, '#c98577') + '<ellipse cx="512" cy="512" rx="230" ry="200" fill="#f5e7cc"/>'
    return {'adventitia': adventitia, 'media': media, 'intima': intima, 'lumen': lumen}, simple, {
        'focus': {'x': .5, 'y': .5}, 'lumen': {'x': .5, 'y': .5}}, '动脉横断面三层壁与管腔，外膜、中膜、内膜逐层套叠；层厚只为可读性，无狭窄/斑块或病理含义，不能用于厚度测量。'


def main():
    output = []
    images = []
    for organ, label, make in [('thyroid', '甲状腺', thyroid), ('kidney', '肾脏', kidney), ('artery', '动脉壁', vessel)]:
        layers, simple, anchors, note = make()
        for mode in ['simple', 'detailed_layers']:
            identifier = f'reserve_{organ}_{mode}_v1'
            folder = HERE / 'anatomy' / identifier
            folder.mkdir(parents=True, exist_ok=True)
            pieces = {'payload': simple} if mode == 'simple' else layers
            files, bundle = [], []
            for name, body in pieces.items():
                vector = folder / f'{name}.svg'
                vector.write_text(svg(body))
                raster = folder / f'{name}.png'
                subprocess.run(['rsvg-convert', str(vector), '-o', str(raster)], check=True)
                bounds = list(Image.open(raster).getchannel('A').getbbox())
                files.extend([{'source': str(vector), 'path': f'source/{name}.svg', 'role': 'source'},
                              {'source': str(raster), 'path': f'files/{name}.png', 'role': 'payload'}])
                bundle.append({'asset_id': name, 'path': f'files/{name}.png', 'source_type': 'original_vector',
                               'visual_meaning': label + '·' + name, 'medical': True,
                               'content_bounds': bounds, 'content_bounds_format': 'pixel_xyxy_right_bottom_exclusive',
                               'registration': {'pivot': {'x': 0, 'y': 0}, 'anchors': anchors,
                                                'canvas_origin': {'x': 0, 'y': 0}, 'shared_viewbox': [0, 0, 1024, 1024]}})
            preview = folder / 'preview.svg'
            preview.write_text(svg(''.join(pieces.values())))
            preview_png = folder / 'preview.png'
            subprocess.run(['rsvg-convert', str(preview), '-o', str(preview_png)], check=True)
            files.extend([{'source': str(preview), 'path': 'source/preview.svg', 'role': 'source'},
                          {'source': str(preview_png), 'path': 'samples/preview.png', 'role': 'poster'},
                          {'source': str(Path(__file__).resolve()), 'path': 'source/build_anatomy.py', 'role': 'source'}])
            instructions = folder / 'USAGE.md'
            instructions.write_text(f'# {label}·{mode}\n\n{note}\n\n所有图层共用1024×1024画布与原点。同图层坐标、缩放和旋转必须共用；bounds只描述可见内容，不可将每层独立裁切后居中。详版用于能读取内部关系的近景，远景选择simple版。可揭示/高亮独立层，不将横断面与外观当作可连续旋转的三维形体。\n\n这是原创可编辑结构图，已核对基础空间关系；当前镜头与医生医学终审仍待完成。\n')
            files.append({'source': str(instructions), 'path': 'USAGE.md', 'role': 'evidence'})
            metadata = {'id': identifier, 'title': f'{label}·' + ('远景简化版' if mode == 'simple' else '近景配准分层版'),
                        'kind': 'medical_cutout', 'entry': 'samples/preview.png', 'asset_bundle': bundle,
                        'reuse_scope': {'kind': 'general'}, 'status': 'reusable_candidate',
                        'source': {'kind': 'original_vector', 'generator': 'source/build_anatomy.py'},
                        'tags': ['anatomy', organ, mode, 'registered_layers', 'reserve_20261023'],
                        'discovery': {'category': 'anatomy', 'aliases': [label, '配准分层' if mode != 'simple' else '远景简化'],
                                      'actions': ['逐层揭示', '局部放大'], 'detail_level': mode,
                                      'story_roles': ['结构解释', '位置关系']},
                        'assembly': {'shared_viewbox': [0, 0, 1024, 1024], 'order': list(pieces),
                                     'operation': 'shared_transform_reveal', 'pre_registered': True},
                        'content_bounds': list(Image.open(preview_png).getchannel('A').getbbox()),
                        'content_bounds_format': 'pixel_xyxy_right_bottom_exclusive',
                        'usage_notes': note, 'medical_review': 'pending',
                        'review': {'static_alpha': 'measured', 'full_motion': 'pending', 'current_shot': 'pending'},
                        'quality_debt': ['medical_review_pending', 'current_shot_scale_pending']}
            result = archive(HERE / 'staging/assets/paper-theatre', metadata, files)
            output.append({**result, 'organ': organ, 'mode': mode, 'parts': len(bundle)})
            images.append((metadata['title'], preview_png))
    page = Image.new('RGB', (1500, 1000), '#f0e9da')
    draw = ImageDraw.Draw(page)
    for i, (title, file) in enumerate(images):
        image = Image.open(file).convert('RGBA')
        image.thumbnail((440, 440))
        x, y = (i // 2) * 500, (i % 2) * 500
        tile = Image.new('RGBA', (490, 460), '#f0e9da')
        tile.alpha_composite(image, ((490 - image.width) // 2, (460 - image.height) // 2))
        page.paste(tile.convert('RGB'), (x, y + 35))
        draw.text((x + 12, y + 8), f'{output[i]["organ"]} / {output[i]["mode"]}', fill='#333333')
    page.save(HERE / 'review/anatomy.jpg', quality=95)
    (HERE / 'registered-anatomy.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'packages': len(output), 'independent_parts': sum(item['parts'] for item in output)}))


if __name__ == '__main__':
    main()
