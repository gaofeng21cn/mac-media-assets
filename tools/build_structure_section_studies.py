#!/usr/bin/env python3
"""Prepare anatomy-bound continuous section windows; never register sources.

Each original layer is copied byte-for-byte. Windows are tied to an actual
source outline or a named local relation. A projection is labelled as a reveal,
and an existing cross-section is never presented as a rotating 3-D organ.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def window(path,pivot,*,basis,angle=0):
    return {'path':path,'pivot':pivot,'angle':angle,'basis':basis}

def ellipse(cx,cy,rx,ry):
    return f'M{cx-rx} {cy} a{rx} {ry} 0 1 0 {rx*2} 0 a{rx} {ry} 0 1 0 {-rx*2} 0 Z'

def specification(key):
    section={'kind':'local_relation_reveal','display_kind':'同位局部揭层','context_before':[],
             'cover':[],'interior':[],'context_after':[],'context_regions':[],
             'underlay_alpha':.24,'windows':[]}
    reason=''
    if key=='heart':
        section.update(kind='two_dimensional_section',display_kind='二维剖面开合',cover=['heart_wall'],
            interior=['four_chambers'],context_after=['great_vessels'],revealed_labels=['四个心腔','房室相对位置','室间隔示意'])
        section['windows']=[
            window('M320 390 Q360 332 446 375 L452 494 Q365 516 320 470 Z',[384,430],basis='原件右心房边界'),
            window('M536 372 Q620 326 688 402 L682 477 Q600 496 540 470 Z',[610,430],basis='原件左心房边界'),
            window('M324 526 Q380 500 459 530 Q455 640 549 780 C423 728 342 650 324 526 Z',[428,630],basis='原件右心室边界'),
            window('M545 530 Q604 502 670 534 Q702 678 595 812 Q510 687 545 530 Z',[600,650],basis='原件左心室边界')]
        note='正面四腔剖面剪纸开合；不表达瓣膜与血流运动。'
    elif key=='kidney':
        section.update(kind='two_dimensional_section',display_kind='冠状剖面开合',cover=['cortex'],
            interior=['medulla','collecting_system'],revealed_labels=['髓质锥体','肾盂与肾盏','输尿管延续'])
        section['windows']=[window('M593 178 C464 91 280 149 224 340 C166 531 218 762 383 822 C492 863 627 805 647 703 C663 626 594 609 569 541 C545 478 604 450 640 394 C692 313 685 239 593 178 Z',[445,490],basis='原件含肾门的完整冠状切面轮廓，保持肾盂到输尿管连续')]
        section['context_regions']=[{'id':'collecting_system','outside_path':'M593 178 C464 91 280 149 224 340 C166 531 218 762 383 822 C492 863 627 805 647 703 C663 626 594 609 569 541 C545 478 604 450 640 394 C692 313 685 239 593 178 Z'}]
        note='既有冠状剖面内部连续打开；不表达肾单位与滤过。'
    elif key=='stomach':
        section.update(kind='two_dimensional_section',display_kind='二维剖面开合',cover=['stomach_wall'],
            interior=['gastric_lumen','cardia_pylorus'],revealed_labels=['胃腔','食管入口','幽门位置'])
        section['windows']=[window('M592 205 L619 205 L619 322 C706 272 798 344 812 450 C830 599 736 758 593 786 C466 810 360 740 338 628 L290 628 L290 610 L364 610 C440 618 512 566 540 503 C574 430 583 354 592 300 Z',[585,510],basis='原件连续胃腔轮廓')]
        note='胃壁剪纸窗口连续开合，胃腔保持连通；不表达蠕动。'
    elif key=='gallbladder':
        section.update(kind='two_dimensional_section',display_kind='二维剖面开合',cover=['gallbladder_wall'],
            interior=['bile'],context_after=['cystic_duct'],revealed_labels=['胆囊内部胆汁示意','胆囊管连接位置'])
        section['windows']=[window('M512 300 C566 300 598 370 612 440 C636 500 652 542 652 566 C652 664 598 726 512 742 C426 726 372 664 372 566 C372 542 388 500 412 440 C426 370 458 300 512 300 Z',[512,530],basis='原件胆囊内容区域边界')]
        note='胆囊壁局部窗口连续开合；不表达结石、功能或流动。'
    elif key=='breast':
        section.update(kind='two_dimensional_section',display_kind='侧视局部剖面',cover=['breast_outline'],
            interior=['gland_tissue','ducts'],revealed_labels=['腺体区','乳管走向','乳头位置'])
        section['windows']=[window('M370 560 C370 400 500 310 616 336 C712 358 742 452 704 536 C664 624 512 646 370 596 Z',[550,495],basis='原件乳房侧视轮廓，保留胸壁不动')]
        section['context_regions']=[{'id':'ducts','path':ellipse(700,556,32,26)}]
        note='乳房侧视剪纸揭面；腺体区和乳管为位置示意。'
    elif key=='pancreas':
        section.update(kind='two_dimensional_section',display_kind='二维局部剖面',cover=['organ'],
            interior=['duct','branches'],revealed_labels=['主胰管','胰管分支'])
        section['windows']=[window('M200 320 C130 360 151 509 214 581 C252 636 317 605 324 553 C383 570 440 519 511 489 C626 455 719 404 830 367 C875 338 836 288 782 310 C660 335 552 323 439 349 C352 364 293 298 200 320 Z',[490,450],basis='原件胰腺轮廓内的管道关系区域')]
        note='胰腺局部剪纸揭面；只示胰管位置，不表达分泌。'
    elif key=='alveolus':
        section.update(kind='two_dimensional_section',display_kind='二维剖面开合',cover=['alveolar_wall'],
            interior=['continuous_air_space'],context_before=['perialveolar_capillaries'],revealed_labels=['连续气腔','相连气道','壁外毛细血管'])
        section['windows']=[window('M483 184 L541 184 L541 351 C674 360 769 458 769 591 C769 734 661 817 513 817 C365 817 257 731 257 586 C257 458 350 361 483 351 Z',[513,550],basis='原件气道与肺泡连通气腔边界')]
        note='肺泡与气道连续气腔揭开；不表达呼吸或气体交换。'
    elif key=='artery_wall':
        section.update(kind='cross_section_sector',display_kind='横断面扇区展开',context_before=['adventitia'],
            interior=['media','intima','lumen'],sector={'cx':512,'cy':512,'rx':365,'ry':320},
            revealed_labels=['中膜','内膜','管腔'])
        reason='原件已是三层壁横断面，不含外观到切面的形态；提供横断面内的连续扇区分层展开。'
        note='既有横断面的连续扇区展开；不冒充三维血管切开。'
    elif key=='blood_cell':
        section.update(display_kind='中央淡区连续揭示',context_before=['cytoplasm'],interior=['central_pallor'],
            context_after=['membrane'],revealed_labels=['正视中央淡区','完整胞质与细胞膜'])
        section['windows']=[window(ellipse(512,512,158,104),[512,512],angle=-16,basis='原件倾斜中央淡区轮廓')]
        reason='central_pallor 是正视中央淡区，原件没有膜截面或细胞内部剖面；不能把淡区冒充内腔。'
        note='中央淡区是正视外观，仍为细胞；不是切开的内腔。'
    elif key=='thyroid':
        section.update(display_kind='峡部前后层揭开',context_before=['trachea'],
            cover=['lobe_left','lobe_right','isthmus'],underlay_alpha=.08,
            revealed_labels=['峡部后方气管','两侧甲状腺叶保持原位'])
        section['windows']=[window('M424 482 Q512 502 600 482 L605 548 Q512 566 419 548 Z',[512,520],basis='原件峡部前层边界')]
        reason='只有正面甲状腺与后方气管，不含腺体内部；提供峡部前后层揭开。'
        note='峡部前层示意揭开以看后方气管；不是手术步骤。'
    elif key=='lungs':
        section.update(display_kind='近端支气管位置揭层',context_before=['trachea_bronchi'],
            cover=['right_lung_anatomical','left_lung_anatomical'],underlay_alpha=.1,
            revealed_labels=['气管分叉','近端左右支气管'])
        section['windows']=[window('M350 320 L465 309 L493 395 L366 401 Z',[420,355],basis='画面左肺门上部近端支气管范围'),
                            window('M559 309 L674 320 L658 401 L531 395 Z',[604,355],basis='画面右肺门上部近端支气管范围')]
        reason='肺叶仅有外形与裂隙，支气管原件只到近端；不能演示肺内剖面或气道分支。'
        note='仅揭示已有近端支气管位置；未提供肺内分支。'
    elif key=='liver':
        section.update(display_kind='肝胆下缘位置揭层',context_before=['gallbladder'],cover=['right_lobe','left_lobe'],
            interior=['bile_duct'],revealed_labels=['胆管走向','胆囊与肝下缘'])
        section['windows']=[window('M470 480 Q550 470 634 441 L647 492 Q555 535 472 541 Z',[560,500],basis='原件肝下缘与胆管相交的局部区域')]
        reason='没有肝内实质或门静脉分层，只有肝胆外形与胆管走向；提供下缘位置揭层。'
        note='肝下缘局部位置揭层；不表达肝内切面或分段。'
    elif key=='intestine':
        section.update(display_kind='结肠内小肠位置揭示',context_before=['colon'],interior=['small_intestine'],
            revealed_labels=['外围结肠','内部小肠盘曲'])
        section['windows']=[window('M350 340 Q515 375 680 340 L680 760 Q515 735 350 760 Z',[515,550],basis='原件外围结肠之间的中央小肠区域')]
        reason='只有肠道正面位置图，没有肠壁或肠腔层；提供同位的小肠位置揭示。'
        note='外围结肠内的小肠位置揭示；不是肠壁切开。'
    elif key=='pituitary':
        section.update(display_kind='鞍区关系图局部揭示',context_before=['sinus','sella','hypothalamus'],
            interior=['gland','stalk','chiasm'],revealed_labels=['垂体','垂体柄','视交叉位置'])
        section['windows']=[window(ellipse(510,571,138,74),[510,571],basis='原件垂体位置轮廓'),
            window('M490 318 Q489 415 499 500 L524 500 Q520 415 538 318 Z',[512,410],basis='原件垂体柄轮廓'),
            window(ellipse(382,409,112,30),[382,409],basis='原件视交叉位置轮廓')]
        reason='原件是概念性邻近位置图，不是有皮骨外层的真实矢状切面；提供原位关系图揭示。'
        note='鞍区位置图的局部揭示；不表示手术入路或切面。'
    elif key=='islet':
        section.update(display_kind='胰岛血管关系揭层',context_before=['exocrine_surroundings','endocrine_cells'],
            interior=['capillary_network'],revealed_labels=['细胞间毛细血管','局部胰岛细胞簇'])
        section['windows']=[window(ellipse(512,512,253,247),[512,512],basis='原件胰岛细胞簇局部范围，包含血管进出边缘')]
        reason='原件是局部组织关系投影，没有组织外壳或纵深层；提供血管关系同位揭层。'
        note='胰岛局部血管关系揭层；不表达分泌与血流。'
    elif key=='foot_joint':
        section.update(display_kind='踝关节位置揭层',context_before=['bones'],interior=['joint_space','ligaments'],
            revealed_labels=['踝关节边界','韧带位置'])
        section['windows']=[window('M346 425 Q460 405 555 427 L553 525 L455 632 L340 632 Z',[445,525],basis='原件距骨周围关节边界与韧带所在区域')]
        reason='没有皮肤、软组织外层或骨截面，只有骨、关节边界与韧带位置；提供位置揭层。'
        note='踝关节边界与韧带的原位揭层；不是骨关节切开。'
    elif key=='pelvic_organs':
        section.update(display_kind='盆腔前后投影揭层',context_before=['pelvis_bone','rectum_posterior_projection','uterus_tubes_ovaries'],
            cover=['bladder_anterior_projection'],underlay_alpha=.06,
            revealed_labels=['前方膀胱投影隐去','后方直肠虚线投影','子宫保持原位'])
        section['windows']=[window('M399 627 C393 552 631 552 625 627 Q617 704 512 722 Q407 704 399 627 Z',[512,638],basis='原件前方膀胱投影边界')]
        reason='前后器官用半透明/虚线投影表达，并非同一冠状切面；只能揭开投影，不能称盆腔切开。'
        note='前方投影局部隐去以看后方；不是同一冠状切面。'
    elif key=='head_sagittal':
        section.update(display_kind='头部位置图揭层',cover=['head_profile'],
            interior=['brain_and_brainstem','pituitary_and_stalk','paranasal_sinuses'],
            revealed_labels=['大脑、小脑与脑干','垂体与柄位置','鼻旁窦位置'])
        section['windows']=[window('M362 171 C502 115 692 161 758 292 Q793 356 779 409 L838 476 Q854 501 797 512 L797 550 Q824 567 793 586 Q800 648 741 674 L690 696 L690 710 L435 710 C338 693 286 604 286 465 C282 331 300 209 362 171 Z',[570,430],basis='原件头部侧面颅面区域；颈部不揭开')]
        reason='没有骨/脑膜/脑实质切面层，只有头部侧面位置示意；提供同位的颅面位置图揭层。'
        note='侧面位置图同位揭层；不表示真实颅骨或脑切面。'
    else:raise ValueError(key)
    if section['kind']=='two_dimensional_section':
        # A cut face remains tissue, including on a dark background. Reuse the
        # opaque source face rather than creating a transparent anatomical void.
        section['underlay_alpha']=1
    section['source_limit_reason']=reason
    return section,note

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def prepare(root,stage):
    from PIL import Image
    matrix=read(root/'collections/structure-purpose-matrix.json')
    rows={r['id']:r for r in map(json.loads,(root/'catalog/assets.jsonl').read_text().splitlines())}
    candidates=[]
    for key,s in matrix['structures'].items():
        row=rows[s['jobs']['close_up']['asset_id']];record=read(root/row['portable_record'])
        if row.get('curation',{}).get('status') in {'superseded','needs_rebuild'}:raise ValueError('矩阵版本已退出推荐')
        assert sha(root/row['portable_record'])==row['portable_record_sha256']
        folder=stage/f'mac_{key}_section_open_close_v1';folder.mkdir(parents=True,exist_ok=True)
        for name in ('index.html','viewer.mjs'):shutil.copy2(root/'tools/motion-studies'/name,folder/name)
        shutil.copy2(root/'tools/structure_section_runtime.mjs',folder/'runtime.mjs')
        original=[]
        for f in record['files']:
            found=[p for p in row['payload'] if p['path'].endswith('/'+f['path'])]
            if len(found)!=1:raise ValueError('载荷映射不唯一')
            source=root/found[0]['path']
            assert sha(source)==f['sha256']==found[0]['sha256']
            dest=folder/'original'/f['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
            original.append({'path':str(dest.relative_to(folder)),'sha256':sha(dest)})
        shutil.copy2(root/row['portable_record'],folder/'original/library-record.json')
        images={};bounds=[];parts=record['asset_bundle']
        for p in parts:
            reg=p['registration'];assert reg['shared_viewbox']==[0,0,1024,1024] and reg['canvas_origin']=={'x':0,'y':0}
            dest=folder/'assets'/f'{p["asset_id"]}.png';dest.parent.mkdir(exist_ok=True);shutil.copy2(folder/'original'/p['path'],dest)
            im=Image.open(dest).convert('RGBA');assert im.size==(1024,1024) and list(im.getchannel('A').getbbox())==p['content_bounds']
            images[p['asset_id']]={'path':str(dest.relative_to(folder)),'sha256':sha(dest),'size':[1024,1024],
                                   'bounds':p['content_bounds'],'registration':reg};bounds.append(p['content_bounds'])
        section,note=specification(key)
        ids=section['context_before']+section['cover']+section['interior']+section['context_after']+[p['id'] for p in section['context_regions']]
        assert set(ids)<=set(images)
        title=s['label']+'·'+section['display_kind']+'连续开合'
        sequence={'schema':'mac_motion_study/v1','id':folder.name,'type':'structure_section','label':s['label'],'title':title,
            'description':'保持同一原点，按本结构边界连续打开，查看原件内部或同位关系，随后关闭并恢复。',
            'scope':record.get('usage_notes','')+' '+note+' '+section['source_limit_reason'],
            'medical_review':'pending','fps':24,'duration':6.2,'images':images,'section':section,'presentation_note':note,
            'timing':{'open_start':.7,'open_end':2.5,'close_start':3.5,'close_end':5.3},
            'composite_bounds':[min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds)],
            'source_assets':[{'asset_id':row['id'],'portable_record_sha256':sha(root/row['portable_record'])}],
            'events':[{'name':name,'time':t,'kind':'section_boundary'} for name,t in [('closed',0),('open_start',.7),('fully_open',2.5),('close_start',3.5),('fully_restored',5.3)]],
            'review_times':[0,.66,.7,.74,.9,1.2,1.6,2,2.46,2.5,3,3.46,3.5,3.54,3.9,4.3,4.7,5.26,5.3,5.34,6.2]}
        write(folder/'sequence.json',sequence)
        write(folder/'provenance.json',{'schema':'mac_structure_section_sources/v1','source_asset_id':row['id'],
            'original_files':original,'original_record_sha256':sha(root/row['portable_record']),
            'source_byte_policy':'copied unchanged; clipping at render time only','boundary_basis':section,
            'license':'Source assets retain registered provenance. Original runtime: Apache-2.0.'})
        (folder/'USAGE.md').write_text(f'# {title}\n\n{sequence["scope"]}\n\n'
            '本地HTTP打开index.html；默认静止，可拖动时间轴与换底。renderStudy(ctx, images, sequence, seconds)可接入Canvas。\n'
            'section.windows保存绑定原图轮廓的边界、枢轴和依据；边界在原图坐标中连续打开与关闭。'
            '图层与边界共用同一原点、同一相机，原图SVG/PNG保持原字节。不能按层bounds分别居中。\n'
            '真正外壁-内部示意使用二维开合；横断面使用扇区展开，位置投影使用同位揭层，不能改名冒充三维切开。'
            '改边界、源图或用途后重新审看与医学终审。无音频。\n',encoding='utf-8')
        candidates.append({'id':folder.name,'structure':key,'label':s['label'],'folder':str(folder),'parts':len(parts),
            'source_asset_id':row['id'],'operation':section['kind'],'display_kind':section['display_kind'],
            'source_limit_reason':section['source_limit_reason'],'original_file_count':len(original),
            'medical_review':'pending','current_shot':'pending'})
    write(stage/'candidates.json',{'schema':'mac_structure_section_candidates/v1','candidates':candidates})
    print(json.dumps({'status':'prepared','structures':len(candidates),'operations':{k:sum(r['operation']==k for r in candidates) for k in sorted({r['operation'] for r in candidates})}},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--stage',type=Path,default=ROOT/'work/structure-section-20261024/candidates');args=p.parse_args()
    prepare(args.root.resolve(),args.stage.resolve())

if __name__=='__main__':main()
