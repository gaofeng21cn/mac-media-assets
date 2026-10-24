#!/usr/bin/env python3
"""Prepare editable, registered structure reveals without changing the catalog.

Reads the current purpose matrix's exact close-up identities. Source raster,
vector and registration bytes are copied unchanged. Main registration is owned
by the integrating task; this tool writes candidates and readback evidence only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    'trachea':'气管', 'lobe_left':'画面左叶', 'lobe_right':'画面右叶', 'isthmus':'峡部',
    'cortex':'皮质背景', 'medulla':'髓质锥体', 'collecting_system':'肾盂、肾盏与输尿管',
    'adventitia':'外膜', 'media':'中膜', 'intima':'内膜', 'lumen':'管腔',
    'organ':'胰腺主体', 'duct':'主胰管', 'branches':'胰管分支',
    'sinus':'蝶窦', 'sella':'蝶鞍', 'gland':'垂体', 'stalk':'垂体柄',
    'hypothalamus':'下丘脑位置', 'chiasm':'视交叉位置',
    'heart_wall':'心脏轮廓', 'four_chambers':'四个心腔', 'great_vessels':'相连大血管',
    'trachea_bronchi':'气管与支气管', 'right_lung_anatomical':'右肺（画面左）',
    'left_lung_anatomical':'左肺（画面右）', 'right_lobe':'肝右叶（画面左）',
    'left_lobe':'肝左叶（画面右）', 'gallbladder':'胆囊', 'bile_duct':'胆管位置',
    'stomach_wall':'胃壁', 'gastric_lumen':'胃腔', 'cardia_pylorus':'贲门与幽门位置',
    'colon':'外围结肠', 'small_intestine':'内部小肠', 'gallbladder_wall':'胆囊壁',
    'bile':'胆汁示意', 'cystic_duct':'胆囊管', 'exocrine_surroundings':'周围外分泌腺泡',
    'endocrine_cells':'成簇内分泌细胞', 'capillary_network':'细胞间毛细血管',
    'alveolar_wall':'肺泡壁', 'continuous_air_space':'连续气腔',
    'perialveolar_capillaries':'壁外毛细血管', 'cytoplasm':'胞质', 'membrane':'细胞膜',
    'central_pallor':'中央淡区', 'breast_outline':'乳腺侧视外形', 'gland_tissue':'腺体区',
    'ducts':'乳管走向', 'bones':'胫腓骨、距骨与足骨', 'joint_space':'踝关节边界',
    'ligaments':'韧带位置', 'pelvis_bone':'骨盆', 'rectum_posterior_projection':'后方直肠虚线投影',
    'uterus_tubes_ovaries':'子宫、输卵管与卵巢', 'bladder_anterior_projection':'前方膀胱半透明投影',
    'head_profile':'头部侧面外形', 'brain_and_brainstem':'大脑、小脑与脑干',
    'pituitary_and_stalk':'垂体与垂体柄', 'paranasal_sinuses':'鼻旁窦位置',
}
NOTES = {
    'thyroid':'正面位置关系；左右按画面描述。',
    'kidney':'单肾冠状切面；不表达微观滤过。',
    'artery_wall':'横断面三层壁与管腔；层厚不作测量。',
    'pancreas':'胰腺与胰管关系；不表达分泌过程。',
    'pituitary':'邻近位置示意；大小与间距非测量依据。',
    'heart':'四腔与相连大血管；不表达血流与瓣膜运动。',
    'lungs':'正面示意；解剖右肺位于画面左。',
    'liver':'正面关系示意；不表达肝内分段。',
    'stomach':'胃壁与相通胃腔；不表达蠕动。',
    'intestine':'外围结肠与内部小肠；曲数不代表长度。',
    'gallbladder':'胆囊壁、胆汁与胆囊管；不表达功能。',
    'islet':'局部组织放大；颜色不指定细胞类型。',
    'alveolus':'气腔连续、薄壁在外、血管环绕壁外。',
    'blood_cell':'中央淡区仍是细胞；不是穿通空洞。',
    'breast':'侧视位置示意；不表达肿块或触诊。',
    'foot_joint':'侧面骨与关节边界；不表达活动范围。',
    'pelvic_organs':'正面投影；前后关系结合侧视图解释。',
    'head_sagittal':'头部矢状位置示意；非真实影像切面。',
}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prepare(root,stage,only=None):
    from PIL import Image
    matrix=read(root/'collections/structure-purpose-matrix.json')
    rows={r['id']:r for r in map(json.loads,(root/'catalog/assets.jsonl').read_text().splitlines())}
    candidates=[]
    for key,structure in matrix['structures'].items():
        if only and key!=only:continue
        row=rows[structure['jobs']['close_up']['asset_id']]
        if (row.get('curation') or {}).get('status') in {'superseded','needs_rebuild'}:
            raise ValueError(f'矩阵指向退出推荐的版本：{row["id"]}')
        source_record=root/row['portable_record']; record=read(source_record)
        if sha(source_record)!=row['portable_record_sha256']:raise ValueError('原记录哈希变化')
        bundle=record['asset_bundle'];order=record['assembly']['order']
        if len(bundle)<2 or set(order)!={p['asset_id'] for p in bundle}:raise ValueError('没有独立分层')
        folder=stage/f'mac_{key}_structure_reveal_v1';folder.mkdir(parents=True,exist_ok=True)
        (folder/'assets').mkdir(exist_ok=True)
        for name in ('index.html','viewer.mjs'):
            shutil.copy2(root/'tools/motion-studies'/name,folder/name)
        shutil.copy2(root/'tools/structure_reveal_runtime.mjs',folder/'runtime.mjs')
        # Preserve every original descriptor, including editable SVG and its
        # source builder. No generated media or registration gets rewritten.
        original=[]
        for descriptor in record['files']:
            matches=[p for p in row['payload'] if p['path'].endswith('/'+descriptor['path'])]
            if len(matches)!=1:raise ValueError('原载荷映射不唯一')
            source=root/matches[0]['path']
            if sha(source)!=descriptor['sha256'] or sha(source)!=matches[0]['sha256']:
                raise ValueError(f'原件字节变化：{source}')
            dest=folder/'original'/descriptor['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,dest);original.append({'path':str(dest.relative_to(folder)),'sha256':sha(dest)})
        shutil.copy2(source_record,folder/'original/library-record.json')
        parts={p['asset_id']:p for p in bundle}; images={};layers=[];bounds=[]
        for name in order:
            part=parts[name];registration=part.get('registration') or {}
            view=registration.get('shared_viewbox')
            if (view!=[0,0,1024,1024] or registration.get('pivot')!={'x':0,'y':0}
                    or registration.get('canvas_origin')!={'x':0,'y':0}):
                raise ValueError(f'分层不在共同原点：{row["id"]}/{name}')
            source=folder/'original'/part['path'];dest=folder/'assets'/f'{name}.png'
            shutil.copy2(source,dest);im=Image.open(dest).convert('RGBA')
            actual=list(im.getchannel('A').getbbox())
            if im.size!=(1024,1024) or actual!=part['content_bounds']:
                raise ValueError(f'图层尺寸或bounds不匹配：{name}')
            b=part['content_bounds'];bounds.append(b)
            # The crop is a CAMERA focus only. A minimum context window keeps
            # tiny features from becoming a disconnected isolated shape.
            cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
            width=max(280,b[2]-b[0]+100);height=max(280,b[3]-b[1]+100)
            focus=[cx-width/2,cy-height/2,cx+width/2,cy+height/2]
            layers.append({'id':name,'label':LABELS[name],'content_bounds':b,
                           'focus_bounds':focus,'shared_viewbox':view,
                           'registration':registration})
            images[name]={'path':f'assets/{name}.png','size':list(im.size),'bounds':b,'sha256':sha(dest)}
        n=len(layers);reveal_start=1.0;reveal_step=.8;focus_start=reveal_start+n*reveal_step+.4
        focus_step=1.2;return_start=focus_start+n*focus_step;duration=return_start+.8
        events=[{'name':'overview','time':0,'kind':'reference'}]
        times=[0,.96]
        for i,part in enumerate(layers):
            start=reveal_start+i*reveal_step
            events.append({'name':f'reveal_{part["id"]}','time':start,'kind':'reveal'})
            times.extend([round(start,3),round(start+.32,3)])
        for i,part in enumerate(layers):
            start=focus_start+i*focus_step
            events.append({'name':f'focus_{part["id"]}','time':start,'kind':'focus'})
            times.extend([round(start,3),round(start+.3,3),round(start+1.1,3)])
        times.extend([round(return_start,3),round(duration,3)])
        sequence={'schema':'mac_motion_study/v1','id':folder.name,'type':'structure_reveal',
                  'title':structure['label']+'·逐层揭示与局部高亮','label':structure['label'],
                  'description':'总览定位→共同坐标系逐层出现→原位高亮与局部近景→回到总览。',
                  'scope':record.get('usage_notes','')+' 仅二维揭示和高亮；不表示连续剖开、三维旋转或生理运动。',
                  'medical_review':'pending','fps':24,'duration':duration,'images':images,'layers':layers,
                  'source_assets':[{'asset_id':row['id'],'portable_record_sha256':sha(source_record)}],
                  'composite_bounds':[min(b[0] for b in bounds),min(b[1] for b in bounds),
                                      max(b[2] for b in bounds),max(b[3] for b in bounds)],
                  'timing':{'reveal_start':reveal_start,'reveal_step':reveal_step,'focus_start':focus_start,
                            'focus_step':focus_step,'return_start':return_start},
                  'presentation_note':NOTES[key], 'events':events,'review_times':sorted(set(times))}
        write(folder/'sequence.json',sequence)
        write(folder/'provenance.json',{'schema':'mac_structure_reveal_sources/v1','source_asset_id':row['id'],
               'portable_record':row['portable_record'],'portable_record_sha256':sha(source_record),
               'original_files':original,'source_byte_policy':'copied unchanged; no alpha rewrite',
               'license':'Source media retain registered provenance; original runtime: Apache-2.0.'})
        (folder/'USAGE.md').write_text(
            f'# {sequence["title"]}\n\n{sequence["scope"]}\n\n'
            '通过本地 HTTP 打开 index.html；默认静止，可拖动时间轴与切换浅/深/彩底。\n'
            '`runtime.mjs` 的 `renderStudy(ctx, images, sequence, seconds)` 可直接接入 Canvas。\n'
            '`sequence.json.layers` 定义独立层、顺序、中文名称和近景；`timing` 定义节奏。\n'
            '全部层沿用 1024×1024 同一原点，主图/定位图各自对整组使用同一变换；'
            '不得按各层 bounds 单独居中或缩放。局部高亮仅改透明度与整组相机。\n\n'
            f'精确原件：`{row["id"]}`。原始 SVG/PNG、记录和全部字节在 `original/`。\n'
            '取用后可调整时间、层序、显示标签与共同相机；改结构必须另存版本并重新医学审核。\n'
            '无音频；不提供听感结论。医学与当前镜头终审仍待完成。\n',encoding='utf-8')
        candidates.append({'structure':key,'label':structure['label'],'id':folder.name,'folder':str(folder),
                           'source_asset_id':row['id'],'parts':n,'original_file_count':len(original),
                           'original_bytes_verified':True,'registration':'shared_origin_preserved',
                           'medical_review':'pending','current_shot':'pending'})
    write(stage/'candidates.json',{'schema':'mac_structure_reveal_candidates/v1','candidates':candidates})
    print(json.dumps({'status':'prepared','structures':len(candidates),'layers':sum(c['parts'] for c in candidates)},ensure_ascii=False))

def samples(stage):
    from motion_package import build_samples
    for row in read(stage/'candidates.json')['candidates']:
        build_samples(row['folder'])
    print(json.dumps({'status':'sheets_built'},ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','samples']);parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--stage',type=Path,default=ROOT/'work/structure-reveal-20261024/candidates')
    parser.add_argument('--only')
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.root.resolve(),args.stage.resolve(),args.only)
    else:samples(args.stage.resolve())

if __name__=='__main__':main()
