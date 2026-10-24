#!/usr/bin/env python3
"""Prepare the reviewed six-pose complete bed contact unit, preserving source bytes."""
import argparse
import json
import shutil
from pathlib import Path
from build_role_contact_studies import ROOT, frames_from_source, sha

EXPECTED_SOURCE_SHA256 = 'ed814df39b58278c68bf663580b2a017dc70e06be66e3cfcfc706f947a3dde20'
FOLDER = ROOT / 'work/bed-contact-20261024/mac_older_woman_bed_rest_v1'


def prepare(source, annotation, folder=FOLDER):
    if sha(source) != EXPECTED_SOURCE_SHA256:
        raise ValueError('Source is not the reviewed six-pose bed sheet')
    folder.mkdir(parents=True, exist_ok=True);(folder/'assets').mkdir(exist_ok=True)
    image,frames,_=frames_from_source(source,3,2)
    if annotation['source_sha256'] != sha(source) or annotation['frame_rects'] != [f['rect'] for f in frames]:
        raise ValueError('Reviewed bed points do not belong to these exact source frames')
    for frame,point in zip(frames,annotation['anchors'],strict=True):
        if not (0 <= point[0] <= frame['rect'][2] and 0 <= point[1] <= frame['rect'][3]):
            raise ValueError('Bed point must be inside its source frame')
        frame['origin']=point
        frame['anchor_basis']=annotation['landmark']
    calibration=annotation['body_calibration_review']
    points=calibration['reviewed_points'];span=abs(points[1][1]-points[0][1])
    if calibration['design_height_cm'] != 158 or span != calibration['span_pixels'] or span <= 0 or not calibration['span_basis'].startswith('vertical_y_distance'):
        raise ValueError('Reviewed body ruler must retain the standing vertical span')
    (folder/'registration.json').write_text(json.dumps(annotation,ensure_ascii=False,indent=2)+'\n')
    shutil.copy2(source,folder/'assets/sheet.png')
    for name in ['index.html','viewer.mjs']:shutil.copy2(ROOT/'tools/motion-studies'/name,folder/name)
    shutil.copy2(ROOT/'tools/role_contact_runtime.mjs',folder/'runtime.mjs')
    phases=['床边站稳','床沿坐定','支撑侧卧','枕上侧卧休息','回到床沿','床边站稳']
    times=[0,1.5,3,4.5,7,8.5]
    r={'schema':'mac_motion_study/v1','id':folder.name,'title':'老年女性·床沿落座、侧卧休息与起身',
       'type':'bed_contact_unit','fps':24,'duration':10,'images':{'sheet':{'path':'assets/sheet.png','size':list(image.size),'sha256':sha(source)}},
       'frames':frames,'phase_names':phases,'paper_states':['not_applicable']*6,'keys':[{'time':t,'frame':i}for i,t in enumerate(times)],
       'events':[{'time':t,'name':name,'kind':'support'}for t,name in zip(times,phases)],
       'review_times':sorted(set([10]+[round(t+dt,2)for t in times for dt in [-.01,0,.01]if t+dt>=0])),
       'x':920,'ground':610,'scene_pixels_per_cm':3,
       'body_calibration':{'status':'source_span_calibrated','source_body_points':points,'design_height_cm':158,'span_cm':158,
         'source_pixels_per_cm':float(span/158),'basis':calibration['basis']},
       'medical_review':'pending',
       'scope':'同身份完整人物与低床接触单元；普通自主休息的六姿态纸上表演，不是失能搬运、术后转移或个体安全指导。人物、枕头、床与承托不能独立拆动。'}
    (folder/'sequence.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    plan={'folder':str(folder),'id':r['id'],'title':r['title'],'scope':r['scope'],
      'source_assets':{'library':[{'asset_id':'paper:character_older_woman_stand_v1@533448a63caf5fd9b120','role':'identity_reference'}],
         'generation':[{'tool':'built_in_imagegen','source_sha256':sha(source)}]},
      'discovery':{'category':'motion','character_role':'older_woman','poses':['stand','seated','lying'],'aliases':['床','侧卧','老年女性','休息'],
         'actions':['床沿落座','侧卧休息','起身'],'medium':'code','renderers':['canvas2d']},
      'tags':['bed_support','complete_contact_unit','same_identity'],
      'checked':['六姿态完整原图、头枕和床垫承托、床沿双脚落地、固定同一床脚、原尺寸/手机宽/三底色。'],
      'defects_found_and_fixed':['完整人物和床同一视角与身体标尺，避免按床或卧姿外框独立拉伸。'],
      'not_reviewed':['独立医生终审和当前镜头pending；不作临床转移教学。'],
      'usage_note':'完整接触单元调用renderStudy，共同缩放；不拆人物和床。'}
    folder.parent.joinpath('registration-request.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--anchors',required=True);parser.add_argument('--stage',default=str(FOLDER))
    args=parser.parse_args();prepare(Path(args.source),json.loads(Path(args.anchors).read_text()),Path(args.stage))
