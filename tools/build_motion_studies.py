#!/usr/bin/env python3
"""Prepare/freeze four self-contained motion studies using exact source bytes.

Preparation never signs creative acceptance. Freeze requires the human/model
review file produced after inspecting current renders. Existing revisions are
never overwritten; the animation_element/v1 hash covers metadata and files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/motion-studies'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


GENERATED = {
    'walk_a': ('exec-a2c67a86-30e9-4f3e-9293-ac1ee0e4b7b1.png',
               '同一绿衫红裤男性八格步态，明确接触、承重、抬脚经过与前摆；采用前四帧，与反侧摆臂配对。'),
    'walk_b': ('exec-511ae7bb-dca3-4648-94b3-17a60d880900.png',
               '四格另一半步态；近侧手臂向前、远侧手臂向后，保持同一人物。'),
    'sit': ('exec-e0c8ec2e-fdb7-4015-8c18-4fb2ca5f03b4.png',
            '同一绿衫红裤男性站立、降低、坐定、前倾、起身、站稳八格透明完整姿态。'),
    'care': ('exec-b43b64b8-4fd8-46d2-bba0-dd52d4894914.png',
             '同一男性与短发照护者八格双人姿态：接近、示意、前倾、起立、稳立、伴行、落定、松手。'),
    'hand': ('exec-9b1bf5c5-a6cf-489b-9627-8901827f56d5.png',
             '成人单手自然握持空槽与芥黄袖口；无刀、无食物，作为真实接触层。'),
    'spatula_hand': ('exec-c575988f-383d-4ce8-8468-ac254180deee.png',
                     '成人单手握木锅铲的完整透明接触单元。'),
    'food': ('exec-6239f8a7-19b0-4d5c-a99c-54bdd240d958.png',
             '两件分离食材：水平胡萝卜段和同视角单片胡萝卜圆片。'),
}


def prepare(generated, out):
    from PIL import Image
    rows=[json.loads(s) for s in (ROOT/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]

    def existing(source_id):
        # Each requested source is unique for these component identities.
        matches=[r for r in rows if r['source_id']==source_id]
        from query_assets import select_versions
        row=select_versions(ROOT,matches,all_versions=False)[0]
        record=read(ROOT/row['portable_record'])
        file=next(p for p in row['payload'] if p['path'].endswith('/'+record['entry']))
        return ROOT/file['path'],row,record

    def start(identifier, title, kind):
        folder=out/identifier
        if folder.exists():
            raise ValueError(f'目标已存在，保留原件：{folder}')
        folder.mkdir(parents=True)
        for filename in ('index.html','runtime.mjs','viewer.mjs'):
            shutil.copy2(SOURCE/filename,folder/filename)
        return folder,{'schema':'mac_motion_study/v1','id':identifier,'title':title,'type':kind,
                       'images':{},'source_assets':[],'generation':[],
                       'scope':'公共虚构角色与日常动作样本。无旁白、无作者身份；当前镜头另按具体故事审看。',
                       'fps':24,'review_times':[]}

    def add(folder, recipe, key, source, bounds=None):
        dest=folder/'assets'/f'{key}.png';dest.parent.mkdir(exist_ok=True)
        shutil.copy2(source,dest)
        im=Image.open(dest).convert('RGBA')
        measured=im.getchannel('A').point(lambda a:255 if a>=25 else 0).getbbox()
        if not measured:raise ValueError(f'空图：{source}')
        recipe['images'][key]={'path':f'assets/{key}.png','bounds':list(bounds or measured),
                               'size':list(im.size),'sha256':sha(dest)}
        return im.size

    def gen(folder, recipe, key):
        filename,summary=GENERATED[key]
        size=add(folder,recipe,key,generated/filename)
        recipe['generation'].append({'image':key,'tool':'built_in_imagegen','source_filename':filename,
                                      'request_summary':summary,'sha256':sha(generated/filename),
                                      'processing':'original bytes; frame extraction only at runtime; no alpha threshold rewrite'})
        return size

    def old(folder,recipe,key,source_id):
        path,row,record=existing(source_id)
        add(folder,recipe,key,path,record.get('content_bounds'))
        recipe['source_assets'].append({'image':key,'asset_id':row['id'],'sha256':sha(path)})
        return record

    def grid(key,size,columns,rows,reference,origins=None):
        w,h=size
        result=[]
        for i in range(columns*rows):
            x0=round((i%columns)*w/columns);x1=round((i%columns+1)*w/columns)
            y0=round((i//columns)*h/rows);y1=round((i//columns+1)*h/rows)
            result.append({'image':key,'rect':[x0,y0,x1-x0,y1-y0],
                           'origin':origins[i] if origins else [(x1-x0)/2,(y1-y0)*.96],
                           'reference_height':reference})
        return result

    folders=[]
    folder,r=start('mac_walk_cycle_v1','同身份成年男性双侧步态循环','walk')
    a=gen(folder,r,'walk_a');b=gen(folder,r,'walk_b')
    stand=old(folder,r,'stand','character_adult_man_stand_v1')
    r.update(duration=6.0,display_height=470,x=280,end_x=1000,ground=620,
             description='站稳→两次完整双侧步态→站稳；八个真实完整姿态逐帧表演，脚底与地面共同配准。',
             frames=grid('walk_a',a,4,2,550)[:4]+grid('walk_b',b,4,1,755),
             phase_names=['右侧接触','承重','经过','抬升','对侧接触','对侧承重','对侧经过','对侧抬升','站稳'],
             ready_frame=8,finish_frame=8,loop={'start':.6,'end':4.6,'period':2,'frames':list(range(8))},
             events=[{'name':name,'time':time,'kind':'foot_contact'} for name,time in
                     [('start',.6),('right_contact_1',.6),('left_contact_1',1.6),('right_contact_2',2.6),('left_contact_2',3.6),('stop',4.6)]],
             review_times=[0,.6,.85,1.1,1.35,1.6,1.85,2.1,2.35,2.59,2.6,4.59,4.6,6])
    # The wide sheet has unequal drawing footprints. Crop at the actual gaps,
    # not the nominal columns: a complete shoe crosses the first grid division.
    for i,(left,right,anchor,baseline) in enumerate([(0,350,180,578),(350,640,145,578),
                                                   (640,960,158,575),(960,1285,162,573)]):
        r['frames'][i].update(rect=[left,0,right-left,606],origin=[anchor,baseline],reference_height=550)
    for i,(left,right,anchor) in enumerate([(0,553,300),(553,973,225),(973,1458,281),(1458,1942,289)]):
        r['frames'][4+i].update(rect=[left,0,right-left,b[1]],origin=[anchor,790])
    w,h=r['images']['stand']['size'];bounds=stand['content_bounds']
    r['frames'].append({'image':'stand','rect':[0,0,w,h],'origin':[(bounds[0]+bounds[2])/2,bounds[3]],
                        'reference_height':bounds[3]-bounds[1],'flip':True})
    write(folder/'sequence.json',r);folders.append(folder)

    folder,r=start('mac_sit_stand_cycle_v1','同身份坐下、坐定与起立完整过渡','sit')
    size=gen(folder,r,'sit');old(folder,r,'chair','reserve_chair_v1')
    origins=[[138,731],[138,716],[138,711],[138,737],[126,677],[132,670],[135,691],[140,711]]
    r.update(duration=6.0,display_height=480,x=640,ground=620,
             description='站立→前倾屈膝→降低→坐定停留→前倾→髋膝伸展→站稳；人物保持同一体量。',
             frames=grid('sit',size,4,2,678,origins),
             phase_names=['站立','屈膝准备','降低','坐定','坐姿保持','前倾起身','伸展','站稳'],
             keys=[{'time':time,'frame':i} for i,time in enumerate([0,.8,1.15,1.5,2.25,3.1,3.45,3.8])],
             events=[{'name':name,'time':time,'kind':'contact'} for name,time in
                     [('prepare',.8),('seat_contact',1.5),('rise_prepare',3.1),('standing_stable',3.8)]],
             chair={'x':695,'y':436,'width':360},review_times=[0,.79,.8,1.15,1.5,2.25,3.1,3.45,3.8,6])
    # Remove only blank gutters from each source rectangle. No source alpha or
    # figure pixel is rewritten; the next row's head must not leak into a cell.
    for i,frame in enumerate(r['frames']):
        if i<4:frame['rect'][3]=752
        else:frame['rect'][1]+=8;frame['rect'][3]-=8;frame['origin'][1]-=8
    write(folder/'sequence.json',r);folders.append(folder)

    folder,r=start('mac_care_assistance_v1','双人照护：接近、协助起身、伴行与松手','care')
    size=gen(folder,r,'care')
    r.update(duration=6.5,display_height=520,x=640,ground=625,
             description='照护者接近并示意，患者主动前倾、借自身双腿和扶手起身，轻扶伴行，站稳后松手。',
             frames=grid('care',size,2,4,366),
             phase_names=['接近','示意','前倾与接触','主动起立','稳立支撑','伴行','落定','松手'],
             keys=[{'time':time,'frame':i} for i,time in enumerate([0,.7,1.3,1.65,2.0,3.0,3.5,4.2])],
             events=[{'name':name,'time':time,'kind':'contact'} for name,time in
                     [('offer',.7),('support_contact',1.3),('self_rise',1.65),('standing_stable',2),('accompany_step',3),('release',4.2)]],
             review_times=[0,.7,1.3,1.65,2,3,3.5,4.2,6.5],
             scope='日常轻扶陪伴的虚构表演；不作失能者转移、术后搬运或急救操作教学。完整双人/椅子关键姿态为整体帧，不能独立改动接触双方。')
    for i,frame in enumerate(r['frames']):
        top,bottom,baseline=[(0,388,377),(388,760,754),(760,1148,1143),(1148,1536,1531)][i//2]
        frame.update(rect=[512*(i%2),top,512,bottom-top],origin=[256,baseline-top])
    write(folder/'sequence.json',r);folders.append(folder)

    folder,r=start('mac_cooking_action_v1','连续备餐：切配、入锅、翻动与盛出','cooking')
    for key in ('hand','spatula_hand','food'):gen(folder,r,key)
    for key,sid in [('board','reserve_chopping_board_v1'),('knife','reserve_kitchen_knife_v1'),
                    ('cooker','reserve_induction_cooktop_v1'),('pan','reserve_frying_pan_v1'),('plate','reserve_plate_v1')]:
        old(folder,r,key,sid)
    food_size=r['images']['food']['size']
    # Two source regions, preserved pixels, independent runtime objects.
    r['images']['food']['bounds']=[30,80,1230,600]
    r['images']['slice']={**r['images']['food'],'bounds':[1480,80,2070,600]}
    r.update(duration=9.0,description='三次刀刃接触后依次出现三片；三片原物入锅、被锅铲连续翻动，最后三片盛入餐盘。',
             transfer={'start':3.4,'end':4.6},stir={'start':4.6,'end':6.6},serve={'start':6.8,'end':8.0},
             events=[{'name':f'cut_{i+1}','time':t,'kind':'cut','index':i} for i,t in enumerate([.9,1.7,2.5])]+
                    [{'name':name,'time':time,'kind':'contact'} for name,time in
                     [('gather',3.4),('pan_entry',4.6),('stir_start',4.6),('stir_stop',6.6),('serve',8)]],
             review_times=[0,.56,.9,1.18,1.7,2.5,3.4,3.7,4,4.3,4.6,5,5.4,5.8,6.2,6.6,6.8,7.2,7.6,8,9],
             scope='道具与食材的日常动作样本；不把动画时长解释成实际加热时间，不推断温度、熟度或营养疗效。手、器具和食材独立可调，接触后才生成切片，转运保持三片身份与数量。')
    write(folder/'sequence.json',r);folders.append(folder)

    for folder in folders:
        recipe=read(folder/'sequence.json')
        write(folder/'provenance.json',{'schema':'mac_motion_sources/v1','generation':recipe.pop('generation'),
                                       'source_assets':recipe['source_assets'],
                                       'license':'Original code: Apache-2.0. Source media retain their registered provenance and reuse scope.'})
        write(folder/'sequence.json',recipe)
        (folder/'USAGE.md').write_text(f"# {recipe['title']}\n\n{recipe['description']}\n\n"
            "用本机 HTTP 服务打开 index.html，可播放、随机拖动时间轴及换浅/深/彩底。\n"
            "源码不依赖远程库；runtime.mjs 导出的 renderStudy 接收 Canvas、图像映射、sequence 和秒数。\n"
            "改镜头时可以换坐标、时长、对象或重做姿态；帧来自完整人物原件，未把人物拆成几何肢体。\n\n"
            f"{recipe['scope']}\n\n样本无声；不提供听感批准。当前镜头审查在取用后重新进行。\n",encoding='utf-8')
    print(json.dumps({'status':'prepared','folders':[str(p) for p in folders]},ensure_ascii=False))


def freeze(folder, root):
    recipe=read(folder/'sequence.json');review=read(folder/'review.json')
    if review.get('status')!='passed' or review.get('sequence_sha256')!=sha(folder/'sequence.json'):
        raise ValueError('缺少绑定当前 sequence 的实际审看结果')
    for rel,expected in {**review['inputs'],**review['media']}.items():
        if sha(folder/rel)!=expected:raise ValueError(f'审看后输入改变：{rel}')
    for rel in ('samples/sample.mp4','samples/contact-sheet.jpg'):
        if not (folder/rel).is_file():raise ValueError(f'缺少真实样例：{rel}')
    descriptors=[]
    for path in sorted(folder.rglob('*')):
        if not path.is_file() or 'render-frames' in path.parts or path.name.startswith('live-') and path.suffix=='.png':continue
        rel=path.relative_to(folder).as_posix()
        role='source' if path.suffix in {'.mjs','.html'} else 'sample' if path.suffix=='.mp4' else 'poster' if rel.endswith('contact-sheet.jpg') else 'evidence' if rel in {'review.json','provenance.json'} else 'payload'
        descriptors.append({'path':rel,'role':role,'sha256':sha(path),'bytes':path.stat().st_size})
    discovery={'category':'motion','aliases':[recipe['title'],recipe['type'],'连续动作',recipe['id']],
               'actions':{'walk':['连续步态','步行循环','双侧摆臂'], 'sit':['坐站过渡','坐下','起立'],
                          'care':['照护全过程','辅助起身','陪伴行走','解除支撑'],
                          'cooking':['连续烹饪','切配','翻炒','盛出']}[recipe['type']],
               'medium':'code','story_roles':['连续动作','人物互动' if recipe['type']!='cooking' else '日常饮食'],
               'display_title':recipe['title'],'renderers':['canvas2d'],'sample_duration_seconds':recipe['duration']}
    metadata={'id':recipe['id'],'title':recipe['title'],'kind':'motion_recipe','entry':'index.html',
              'reuse_scope':{'kind':'general'},'source':{'kind':'original_animation','generation_receipt':'provenance.json'},
              'tags':['paper_collage','continuous_action',recipe['type']],'discovery':discovery,
              'status':'reusable_candidate','usage_notes':recipe['scope'],
              'review':{'static_alpha':'checked_on_light_dark_color_composites','full_motion':'passed',
                        'current_shot':'pending','medical':'not_applicable','full_listening':'not_applicable',
                        'evidence_ref':'review.json'},'medical_review':'not_applicable',
              'quality_debt':['current_shot_review_pending'],
              'registration':{'coordinate_space':'sequence_frames_and_runtime_world',
                              'frames_ref':'sequence.json','ground':recipe.get('ground'),
                              'contact_events_ref':'sequence.json#events'},'files':descriptors}
    from apply_character_anchors import canonical_revision
    revision=canonical_revision(metadata)
    record={'schema':'animation_element/v1',**metadata,'revision':revision}
    payload_root=root/'payloads/paper-theatre'/recipe['id']/revision
    record_path=root/'records/paper-theatre'/recipe['id']/revision/'record.json'
    if payload_root.exists():raise ValueError(f'不可覆盖已有版本：{payload_root}')
    for item in descriptors:
        target=payload_root/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(folder/item['path'],target)
    write(record_path,record)
    row={'id':f"paper:{recipe['id']}@{revision}",'source_id':recipe['id'],'revision':revision,
         'title':recipe['title'],'kind':'motion_recipe','reuse_scope':{'kind':'general'},'tags':record['tags'],
         'series_ids':[],'discovery':discovery,'registration':record['registration'],
         'payload':[{**item,'path':(payload_root/item['path']).relative_to(root).as_posix()} for item in descriptors],
         'portable_record':record_path.relative_to(root).as_posix(),'portable_record_sha256':sha(record_path),
         'provenance':{'source_type':'original_animation','source_ref':{'recorded_in':'provenance.json'}},
         'review_boundary':{'admission':'reusable_candidate','motion':'passed','medical':'not_applicable',
                            'listening':'not_applicable','quality_debt':['current_shot_review_pending']}}
    with (root/'catalog/assets.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','freeze'])
    parser.add_argument('--generated-dir',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--folder',type=Path)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.generated_dir,args.out)
    else:print(json.dumps(freeze(args.folder,args.root),ensure_ascii=False))


if __name__=='__main__':main()
