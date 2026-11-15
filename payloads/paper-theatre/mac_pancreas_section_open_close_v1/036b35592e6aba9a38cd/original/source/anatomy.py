#!/usr/bin/env python3
"""Original editable relational diagrams, kept separate from medical approval."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[2]
sys.path.insert(0,str(WORKSPACE/'scripts'))
from animation_library import archive,write

GROUPS={
 'thyroid': {
  'label':'甲状腺', 'note':'前面观双叶与峡部轮廓；远景仅辨认甲状腺，不显示气管环、内部组织或手术关系。',
  'parts':{
   'gland':'<path d="M480 485 C450 405 448 285 370 270 C260 250 245 380 275 520 C295 665 375 752 440 700 C470 674 478 590 480 555 L544 555 C546 590 554 674 584 700 C649 752 729 665 749 520 C779 380 764 250 654 270 C576 285 574 405 544 485 Z" fill="#cf7969" stroke="#8e5147" stroke-width="10"/>'}},
 'pituitary': {
  'label':'垂体邻近关系',
  'note':'概念性相对位置示意：垂体经柄连接上方下丘脑，视交叉在上方偏前，蝶窦在鞍底下方。它不是患者影像或精确矢状断面；不含颈内动脉、神经束或手术通道，不能用作入路示教。',
  'parts':{
   'sinus':'<path d="M302 674 Q510 625 720 674 L702 820 Q510 900 322 820 Z" fill="#ecd9b0" stroke="#997a50" stroke-width="12"/>',
   'sella':'<path d="M323 575 L341 635 Q510 704 680 635 L698 575" fill="none" stroke="#a5a0a0" stroke-width="30" stroke-linecap="round"/>',
   'gland':'<ellipse cx="510" cy="571" rx="138" ry="74" fill="#d78b84" stroke="#9c5753" stroke-width="10"/>',
   'stalk':'<path d="M490 318 Q489 415 499 500 L524 500 Q520 415 538 318 Z" fill="#8bb6a6" stroke="#507e72" stroke-width="9"/>',
   'hypothalamus':'<path d="M382 227 Q510 168 643 227 Q628 308 544 332 L480 332 Q399 305 382 227 Z" fill="#9bbda9" stroke="#507e72" stroke-width="10"/>',
   'chiasm':'<ellipse cx="382" cy="409" rx="112" ry="30" fill="#e4b35f" stroke="#a97c32" stroke-width="9"/>'}},
 'pancreas': {
  'label':'胰腺与胰管',
  'note':'概念性胰腺外形与主胰管示意，画面左侧为胰头、右侧为胰尾；并非患者影像。胰管分支只表达汇流关系，不表达精确分支数；不包含胆管、十二指肠、胰岛或微观细胞，不能演示手术、病灶或内分泌细胞比例。',
  'parts':{
   'organ':'<path d="M200 320 C130 360 151 509 214 581 C252 636 317 605 324 553 C383 570 440 519 511 489 C626 455 719 404 830 367 C875 338 836 288 782 310 C660 335 552 323 439 349 C352 364 293 298 200 320 Z" fill="#e0a185" stroke="#9c6855" stroke-width="11"/>',
   'duct':'<path d="M810 345 Q690 389 590 409 T393 473 Q285 484 240 529" fill="none" stroke="#e9d8ae" stroke-width="24" stroke-linecap="round"/><path d="M810 345 Q690 389 590 409 T393 473 Q285 484 240 529" fill="none" stroke="#a77746" stroke-width="5"/>',
   'branches':'<g stroke="#bd8c57" stroke-width="6" fill="none" stroke-linecap="round"><path d="M322 470 L281 385 M381 474 L389 414 M446 452 L451 388 M509 433 L528 375 M583 410 L611 359 M647 397 L665 352 M284 491 L264 569 M393 470 L412 509 M477 444 L495 480"/></g>'}}
}


def svg(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">'+body+'</svg>'


def build():
    output=[]
    for organ,spec in GROUPS.items():
        modes=['simple'] if organ=='thyroid' else ['simple','layers']
        for mode in modes:
            identifier=('reserve_thyroid_simple_v2' if organ=='thyroid' else f'reserve_{organ}_relations_{mode}_v1')
            folder=HERE/'vectors'/identifier
            folder.mkdir(parents=True,exist_ok=True)
            parts=spec['parts'] if mode=='layers' else {'whole':spec['parts']['gland'] if organ=='thyroid' else spec['parts']['organ'] if organ=='pancreas' else spec['parts']['gland']+spec['parts']['stalk']+spec['parts']['hypothalamus']}
            bundle=[];files=[];images=[]
            for name,body in parts.items():
                source=folder/(name+'.svg');source.write_text(svg(body))
                target=folder/(name+'.png')
                subprocess.run(['/opt/homebrew/bin/rsvg-convert',str(source),'-o',str(target)],check=True)
                im=Image.open(target).convert('RGBA');images.append(im)
                bounds=list(im.getchannel('A').getbbox())
                bundle.append({'asset_id':name,'path':f'files/{name}.png','source_type':'original_vector',
                    'visual_meaning':spec['label']+'·'+name,'medical':True,'content_bounds':bounds,
                    'content_bounds_format':'pixel_xyxy_right_bottom_exclusive',
                    'registration':{'pivot':{'x':0,'y':0},'canvas_origin':{'x':0,'y':0},
                                    'shared_viewbox':[0,0,1024,1024], 'anchors':{'focus':{'x':.5,'y':.5}}}})
                files.extend([{'source':str(source),'path':f'source/{name}.svg','role':'source'},
                              {'source':str(target),'path':f'files/{name}.png','role':'payload'}])
            preview=Image.new('RGBA',(1024,1024))
            for image in images:preview.alpha_composite(image)
            preview.save(folder/'preview.png')
            usage=folder/'USAGE.md'
            usage.write_text('# '+spec['label']+'\n\n'+spec['note']+'\n\n所有层保持共同1024×1024原点、相同缩放与平移，按列表顺序叠加。不得按各层bounds分别居中。逐层显隐是可运行装配功能；医学终审和当前镜头仍待审。\n')
            files.extend([{'source':str(folder/'preview.png'),'path':'samples/preview.png','role':'poster'},
                          {'source':str(usage),'path':'USAGE.md','role':'evidence'},
                          {'source':str(Path(__file__)),'path':'source/anatomy.py','role':'source'}])
            title=spec['label']+('·远景轮廓简化版' if mode=='simple' else '·同视角关系分层版')
            meta={'id':identifier,'title':title,'kind':'medical_cutout','entry':'samples/preview.png',
                  'asset_bundle':bundle,'reuse_scope':{'kind':'general'},'status':'reusable_candidate',
                  'source':{'kind':'original_vector','license':'original_work','generator':'source/anatomy.py'},
                  'discovery':{'category':'anatomy','aliases':[spec['label'],'远景简化' if mode=='simple' else '配准分层'],
                               'detail_level':'simplified' if mode=='simple' else 'registered_relations',
                               'actions':['整体定位'] if mode=='simple' else ['逐层揭示','位置关系'],
                               'medium':'editable_vector','story_roles':['结构定位','结构解释']},
                  'assembly':{'shared_viewbox':[0,0,1024,1024],'order':list(parts),'operation':'shared_transform_reveal','pre_registered':True},
                  'content_bounds':list(preview.getchannel('A').getbbox()),
                  'content_bounds_format':'pixel_xyxy_right_bottom_exclusive','usage_notes':spec['note'],
                  'medical_review':'pending','review':{'static_alpha':'measured','full_motion':'pending','current_shot':'pending'},
                  'quality_debt':['medical_review_pending','current_shot_scale_pending']}
            result=archive(HERE/'staging/assets/paper-theatre',meta,files)
            output.append({**result,'organ':organ,'mode':mode,'parts':len(bundle)})
    write(HERE/'registered-anatomy.json',output)
    print(json.dumps(output,ensure_ascii=False))


if __name__=='__main__':build()
