#!/usr/bin/env python3
"""Prepare a reviewed ABPM fitting study without touching the shared catalog."""
from pathlib import Path
import argparse,hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
ID='mac_abpm_wear_cycle_v1'
SOURCE=ROOT/'work/abpm-wear-20261024'/ID/'assets/abpm-wear-sheet.png'
def prepare(stage,source):
 from PIL import Image
 folder=stage/ID;(folder/'assets').mkdir(parents=True,exist_ok=True)
 target=folder/'assets/abpm-wear-sheet.png'
 if source.resolve()!=target.resolve():shutil.copy2(source,target)
 sha=hashlib.sha256(target.read_bytes()).hexdigest()
 size=list(Image.open(target).size)
 # These are visually located gutters, not a guessed 3x2 regular grid.
 rects=[[70,0,480,516],[550,0,485,516],[1035,0,501,516],
        [70,516,480,508],[550,516,485,508],[1035,516,501,508]]
 # One source-pixel scale, registered by the complete unit's floor baseline.
 # Shoe toes are slightly forward of the chair legs in this mild perspective.
 grounds=[[105,514],[130,514],[152,514],[105,502],[130,503],[152,504]]
 hand_edges=[456,419,458,None,None,497]
 stages=[
  ('prepare',0,1.5,0,False,False,'核对与准备',['露出上臂，选合适袖带','装配由工作人员完成'],'裸露上臂，先看清袖带、气管和记录器'),
  ('wrap',1.5,3,1,True,False,'佩戴袖带',['袖带直接贴合裸露上臂','避开肘窝，保持位置合适'],'袖带的实际大小、位置和松紧按设备说明核对'),
  ('secure',3,4.5,2,True,True,'固定记录器',['记录器放入腰侧固定袋','气管连续连接，避免受压'],'核对袖带—气管—记录器的连续连接'),
  ('trial',4.5,6,3,True,True,'完成试测',['确认设备正常记录','充气时手臂放松、安静不动'],'试测时保持安静，工作人员确认记录正常'),
  ('record',6,10.5,4,True,True,'按约定记录日夜',['按要求记录作息与症状','避免设备受潮，勿自行调整'],'测量时停止活动，手臂放松；其余按约定正常生活'),
  ('return',10.5,12,5,False,False,'次日按约交回',['由工作人员结束记录','取回袖带与相连记录器'],'完成约定记录后交回设备，由工作人员拆除'),
 ]
 seq={'schema':'mac_motion_study/v1','id':ID,'title':'动态血压：佩戴、固定、试测、日夜记录与交回',
  'type':'abpm_wear_cycle','images':{'sheet':{'path':'assets/abpm-wear-sheet.png','size':size,'sha256':sha}},
  'duration':12,'fps':24,'frames':[{'rect':rect,'ground':ground,'hand_entry_right':edge,'coordinate_space':'frame_pixels','complete_contact_unit':True}for rect,ground,edge in zip(rects,grounds,hand_edges)],
  'display':{'scale':1.05,'ground':[170,625],'scale_policy':'All frames use the same source-pixel scale and chair-floor registration. No independent body/chair/device scaling.'},
  'stages':[dict(zip(['key','start','end','frame','cuff_worn','recorder_secured','title','lines','caption'],s))for s in stages],
  'review_times':sorted({0,12,*[round(s[1]+d,3)for s in stages for d in [-.042,0,.042]if 0<=s[1]+d<=12],*[round((s[1]+s[2])/2,3)for s in stages],7.8,8.8,10.45}),
  'events':[{'name':s[0],'time':s[1],'kind':'contact'if s[0]in {'wrap','secure','return'}else'record'}for s in stages],
  'description':'完整同身份患者与真实椅面、台面承托单元依次展示佩戴与归还。日夜记录时钟压缩 24 小时，不展示血压数值或采样频率。',
  'scope':'六个完整姿态的纸上分格演示，不以交叉溶解或肢体变形冒充连续写实穿戴。患者、椅子、台面与器械为烘焙完整接触单元，不能独立拆动。通用非品牌装配关系，不覆盖具体设备按钮、型号、充气压力、袖带尺寸或个体适应证。',
  'medical_review':'pending','source_assets':[{'asset_id':'paper:abpm_patient_20261023@da1da29c83fad06b55a3','role':'identity_reference_only','not_reused_reason':'原件袖带覆在毛衣上；新的裸露上臂接触单元用于佩戴演示'}],
  'source_generation':{'tool':'built_in_imagegen','source':'assets/abpm-wear-sheet.png','receipt_id':'exec-dd3b5da0-2bf7-4513-aed1-7bca1da655de','sha256':sha,'identity_reference':'paper:abpm_patient_20261023@da1da29c83fad06b55a3','relationship':'same_identity_new_short_sleeve_contact_sheet','license':'generated_original','no_brand':True},
  'current_review':'pending','full_listening':'not_applicable'}
 (folder/'sequence.json').write_text(json.dumps(seq,ensure_ascii=False,indent=2)+'\n')
 shutil.copy2(ROOT/'tools/abpm_wear_runtime.mjs',folder/'runtime.mjs')
 for name in ['viewer.mjs','index.html']:shutil.copy2(ROOT/'work/action-contact-repair-20261024/mac_abpm_recording_v1'/name,folder/name)
 print(json.dumps({'status':'prepared','folder':str(folder),'frames':6,'sha256':sha}))
 return folder
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,default=ROOT/'work/abpm-wear-20261024');p.add_argument('--source',type=Path,default=SOURCE);a=p.parse_args();prepare(a.stage,a.source)
