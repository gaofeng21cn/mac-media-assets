#!/usr/bin/env python3
"""Prepare identity-preserving contact units; source pixels never get repainted."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'work/role-contact-20261024/candidates'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runs(values):
    spans, start = [], None
    for i, value in enumerate(values):
        if value and start is None:
            start = i
        elif not value and start is not None:
            spans.append((start, i)); start = None
    if start is not None:
        spans.append((start, len(values)))
    return spans


def frames_from_source(source, columns=4, row_count=2):
    image = Image.open(source).convert('RGBA')
    mask = np.array(image.getchannel('A')) >= 25
    def split(profile, count):
        boundaries=[0]
        for i in range(1,count):
            centre=len(profile)*i/count
            gaps=[(a,b)for a,b in runs(~profile)
                  if abs((a+b)/2-centre)<len(profile)/count*.3]
            if not gaps:
                raise ValueError('source has no transparent gutter')
            a,b=max(gaps,key=lambda pair:pair[1]-pair[0]);boundaries.append((a+b)//2)
        boundaries.append(len(profile))
        return list(zip(boundaries,boundaries[1:]))
    rectangles=[]
    try:
        for col,(left,right)in enumerate(split(mask.any(axis=0),columns)):
            for row,(top,bottom)in enumerate(split(mask[:,left:right].any(axis=1),row_count)):
                rectangles.append((row*columns+col,left,top,right,bottom))
    except ValueError:
        rectangles=[]
        for row,(top,bottom)in enumerate(split(mask.any(axis=1),row_count)):
            for col,(left,right)in enumerate(split(mask[top:bottom].any(axis=0),columns)):
                rectangles.append((row*columns+col,left,top,right,bottom))
    frames=[None]*(columns*row_count)
    for index,left,top,right,bottom in rectangles:
        crop=mask[top:bottom,left:right];ys,xs=np.nonzero(crop)
        bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        frames[index]={'image':'sheet','rect':[left,top,right-left,bottom-top],
            'content_bounds':bounds}
    first=frames[0]; x,y,w,h=first['rect'];crop=mask[y:y+h,x:x+w];b=first['content_bounds']
    top_x=float(np.median(np.nonzero(crop[b[1]:b[1]+4])[1]))
    bottom_x=float(np.median(np.nonzero(crop[b[3]-4:b[3]])[1]))
    return image,frames,[[top_x,b[1]],[bottom_x,b[3]]]


def prepare(references, annotations, stage=STAGE):
    plans=[]
    for ref in references:
        identifier='mac_'+ref['role']+'_seat_report_stand_v1'
        folder=Path(stage)/identifier;folder.mkdir(parents=True,exist_ok=True)
        (folder/'assets').mkdir(exist_ok=True)
        source=Path(ref['generated_source']);shutil.copy2(source,folder/'assets/sheet.png')
        for name in ['index.html','viewer.mjs']:
            shutil.copy2(ROOT/'tools/motion-studies'/name,folder/name)
        shutil.copy2(ROOT/'tools/role_contact_runtime.mjs',folder/'runtime.mjs')
        image,frames,points=frames_from_source(source)
        annotation=annotations['assets'][identifier]
        if annotation['source_sha256']!=sha(source) or annotation['frame_rects']!=[f['rect']for f in frames]:
            raise ValueError('Reviewed furniture points do not belong to these exact source frames')
        for frame,point in zip(frames,annotation['anchors'],strict=True):
            if not (0<=point[0]<=frame['rect'][2] and 0<=point[1]<=frame['rect'][3]):
                raise ValueError('Furniture point must be inside its source frame')
            frame['origin']=point;frame['anchor_basis']=annotation['landmark']
        (folder/'registration.json').write_text(json.dumps(annotation,ensure_ascii=False,indent=2)+'\n')
        points=annotation['body_calibration_review']['reviewed_points']
        span=abs(points[1][1]-points[0][1])
        calibration=annotation['body_calibration_review']
        if (calibration['design_height_cm'] != ref['height_cm']
                or calibration['span_basis'] != 'vertical_y_distance'
                or span != calibration['span_pixels'] or span <= 0):
            raise ValueError('Reviewed body ruler must match the identity height and vertical source span')
        if not all(0 <= x <= frames[0]['rect'][2] and 0 <= y <= frames[0]['rect'][3] for x,y in points):
            raise ValueError('Reviewed body points must belong to the first source frame')
        times=[0,.7,1.4,2.1,3.2,4.1,5.2,6.1]
        phases=['站稳','准备落座','下降','坐定','接触报告','持纸','准备起身','站立持纸']
        sequence={'schema':'mac_motion_study/v1','id':identifier,
            'title':ref['label']+'·落座、取报告与起身','type':'role_contact_unit',
            'scope':'同身份完整人物与家具接触单元；纸上八姿态切换，支持落座、取纸与起身。不是步态循环或临床转移教学；改变家具或持握关系须重做对应姿态。',
            'fps':24,'duration':8,'images':{'sheet':{'path':'assets/sheet.png','size':list(image.size),
                'sha256':sha(source)}},'frames':frames,'scene_pixels_per_cm':3,'x':360,'ground':610,
            'body_calibration':{'status':'source_span_calibrated','design_height_cm':ref['height_cm'],
                'frame':0,'source_body_points':points,'span_cm':ref['height_cm'],
                'source_pixels_per_cm':span/ref['height_cm'],
                'basis':'Reviewed standing first-frame visible crown to common shoe-ground vertical span; this ruler is retained for every seated/reaching/rising pose.'},
            'identity_master':{'asset_id':ref['source_id'],'sha256':sha(ref['reference'])},
            'phase_names':phases,'paper_states':['on_table']*5+['held']*3,
            'keys':[{'time':t,'frame':i}for i,t in enumerate(times)],
            'events':[{'time':t,'name':phases[i],'kind':'contact'}for i,t in enumerate(times)],
            'review_times':sorted(set([8]+[round(t+offset,2)for t in times for offset in [-.01,0,.01]if t+offset>=0])),
            'medical_review':'pending'}
        (folder/'sequence.json').write_text(json.dumps(sequence,ensure_ascii=False,indent=2)+'\n')
        plans.append({'folder':str(folder),'id':identifier,'title':sequence['title'],'scope':sequence['scope'],
            'source_assets':{'library':[sequence['identity_master']],
                'generation':[{'tool':'built_in_imagegen','source_sha256':sha(source),'identity_reference':ref['source_id']}],
                'note':'Complete source image bytes retained; only explicit frame rectangles are used.'},
            'discovery':{'category':'motion','character_role':ref['role'],'poses':['stand','seated','reach'],
                'aliases':[ref['label'],'落座','取报告','起身'],
                'actions':['坐站过渡','取报告','持物'],'medium':'code','renderers':['canvas2d']},
            'tags':['complete_character','same_identity','contact_unit','seated_reach_stand'],
            'checked':['八姿态源图与母版身份、身体体量、椅面承托、脚底和报告持有关系。',
                       '所有状态和切换两侧、原尺寸、手机宽及浅深彩底；实际渲染与随机seek。'],
            'defects_found_and_fixed':['以人物和家具完整接触单元替代独立缩放，坐姿保留站姿身体标尺。'],
            'not_reviewed':['独立医学终审与当前生产镜头pending；普通自主日常动作，不批准临床转移。'],
            'usage_note':'显式调用renderStudy；同一身体标尺与帧内家具锚点共同变换，完整单元不可拆成独立椅子或手臂。'})
    return plans


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--references',required=True);parser.add_argument('--anchors',required=True);parser.add_argument('--stage',default=str(STAGE))
    args=parser.parse_args();plans=prepare(json.loads(Path(args.references).read_text()),json.loads(Path(args.anchors).read_text()),Path(args.stage))
    Path(args.stage).parent.joinpath('registration-plan.json').write_text(json.dumps({'plans':plans},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prepared':len(plans)},ensure_ascii=False))
