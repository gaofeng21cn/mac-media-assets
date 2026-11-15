#!/usr/bin/env python3
"""Register original, small editable medical-process components with honest review scope."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from apply_character_anchors import canonical_revision

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'blood': ['https://www.nhlbi.nih.gov/health/atherosclerosis'],
    'gas': ['https://www.nhlbi.nih.gov/health/lungs/breathing-benefits'],
    'insulin': ['https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes'],
    'feedback': ['https://www.niddk.nih.gov/health-information/endocrine-diseases/hypothyroidism'],
    'inflammation': ['https://medlineplus.gov/ency/article/000821.htm'],
    'metastasis': ['https://www.cancer.gov/types/metastatic-cancer'],
    'risk': ['https://www.cochrane.org/about-us/evidence-based-health-care'],
    'screening': ['https://www.cancer.gov/about-cancer/screening/patient-screening-overview-pdq'],
    'endoscope': ['https://www.niddk.nih.gov/health-information/diagnostic-tests/colonoscopy'],
    'skin': ['https://medlineplus.gov/ency/anatomyvideos/000029.htm'],
    'spine': ['https://orthoinfo.aaos.org/en/diseases--conditions/herniated-disk-in-the-lower-back/'],
    'eye': ['https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/nearsightedness-myopia'],
}
# These mappings are editorial decisions, not keyword-based quality verdicts.
SPECS = [
    ('blood','血管斑块、管腔与血流关系','pathology',['心血管'],['动脉粥样硬化','冠心病'],['理解疾病机制'],['管腔变窄','血流方向'],['非血流动力学模拟；不由颗粒速度推算灌注、压差或狭窄程度。']),
    ('gas','肺泡与毛细血管气体交换','physiology',['呼吸'],['呼吸','氧合'],['理解身体功能'],['氧气进入血液','二氧化碳进入肺泡'],['二维局部关系；不表达通气灌注定量或氧疗处方。']),
    ('insulin','胰岛素信号与葡萄糖转运','physiology',['内分泌与代谢'],['糖尿病','胰岛素抵抗'],['理解身体功能','理解用药作用'],['受体结合','葡萄糖转运'],['表达胰岛素敏感组织的简化过程；不能推广为所有组织的唯一摄糖机制。']),
    ('feedback','激素轴的负反馈关系','physiology',['内分泌与代谢'],['激素','负反馈'],['理解身体功能'],['下游反馈','上游抑制'],['是关系图，不是任何具体激素轴的完整生理模型；具体轴须补真实名称与证据。']),
    ('inflammation','炎症与免疫细胞局部募集','pathology',['感染与免疫'],['炎症','免疫'],['理解疾病机制'],['细胞募集','跨血管壁迁移'],['简化局部反应；不表达感染病原体、疾病分型或治疗指征。']),
    ('metastasis','原发病灶与远处转移过程','pathology',['肿瘤'],['癌症','肿瘤转移'],['理解疾病机制'],['脱离原发部位','进入循环','远处定植'],['展示一种可能路径；不表示所有进入循环的细胞都会转移，不代表时间、概率或癌种特定路径。']),
    ('risk','相同分母下的绝对风险比较','communication',['跨系统'],['风险沟通','治疗获益'],['比较治疗选择'],['人群点阵','绝对人数比较'],['样例10/100与5/100为演示数据；实际使用须绑定真实终点、相同人群及随访时段。']),
    ('screening','筛查结果与疾病状态四格关系','communication',['跨系统'],['癌症筛查','假阳性','假阴性'],['理解检查结果'],['真实状态分组','检测结果分组'],['样例为演示人数，不是任何检查的准确率；不能把阳性结果等同确诊。']),
    ('endoscope','内镜观察与靶向取样局部关系','procedures',['消化'],['肠镜','活检'],['准备检查','理解检查过程'],['镜端观察','靶向取样','回收标本'],['仅为肠腔局部示意；不表达全身进镜路线、息肉切除或操作规范培训。']),
    ('skin','皮肤分层与屏障受损','anatomy',['皮肤'],['皮肤','伤口'],['理解结构','理解疾病机制'],['正常屏障','局部受损'],['不表达伤口深度分级、感染诊断或敷料更换步骤。']),
    ('spine','腰椎、椎间盘与神经根局部关系','anatomy',['骨骼肌肉与康复'],['腰椎间盘突出','腰痛'],['理解结构','理解疾病机制'],['局部突出','邻近关系'],['侧面局部示意；不能从图形位置推断责任节段、影像诊断或手术路径。']),
    ('eye','眼球成像与近视焦点位置','anatomy',['眼'],['近视','屈光'],['理解结构','理解身体功能'],['光线聚焦','视网膜位置对比'],['简化光学关系；不表达个体屈光度、眼轴数值或治疗效果。']),
]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def build(root=ROOT):
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    discovery=json.loads((root/'collections/discovery.json').read_text())
    storage=json.loads((root/'catalog/media-storage.json').read_text())
    added=[]
    for scene,title,category,systems,topics,tasks,actions,limits in SPECS:
        identifier='mac_process_'+scene+'_v1'
        spec={'schema':'mac_medical_process/v1','scene':scene,'title':title,'duration':10,
              'viewport':[1280,720],'medical_review':'pending'}
        if scene=='risk':spec['example']={'population':100,'before':10,'after':5}
        if scene=='screening':spec['example']={'population':100,'disease':10,'truePositive':8,'falsePositive':9}
        fields={'category':category,'display_title':title,'aliases':topics+actions,
                'topics':topics,'medical_systems':systems,'patient_tasks':tasks,
                'mechanisms':actions,'story_roles':tasks,'actions':actions,
                'medium':'code','renderers':['canvas2d'],'component_family':'medical_process',
                'usage_notes':'；'.join(limits),'audiences':['成人','患者与家属']}
        data={name:(root/'tools/medical-processes'/name).read_bytes() for name in ['runtime.mjs','viewer.mjs','index.html']}
        data['component.json']=(json.dumps(spec,ensure_ascii=False,indent=2)+'\n').encode()
        data['sources.json']=(json.dumps({'kind':'original_diagram','references':SOURCES[scene],
            'license':'Apache-2.0','reference_use':'医学事实参考；图形与代码原创，未复制网页媒体。'},ensure_ascii=False,indent=2)+'\n').encode()
        data['USAGE.md']=(f'# {title}\n\n通过 index.html 查看完整10秒动作；拖动时间轴可随机定位。\n\n'
            '在单集 Canvas 中 import {render} from "./runtime.mjs"，调用 render(ctx, time, component)。'
            '可修改 component.json 的示例参数；共享的是科学关系组件，各集自行导演。\n\n'
            '## 用途与限制\n\n'+'\n'.join('- '+s for s in limits)+'\n\n'
            '医学、连续动态、静态和当前镜头审查分别为 pending；技术运行不升级审核结论。\n').encode()
        files=[{'path':name,'role':'source' if name.endswith(('.mjs','.html')) else 'evidence' if name in {'sources.json','USAGE.md'} else 'payload',
                'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)} for name,body in sorted(data.items())]
        record={'schema':'animation_element/v1','id':identifier,'title':title,'kind':'code_component','entry':'index.html',
                'reuse_scope':{'kind':'general'},'source':{'kind':'original_diagram','license':'Apache-2.0','evidence_ref':'sources.json'},
                'discovery':fields,'tags':['medical_process','editable','canvas2d'],
                'review':{'static_alpha':'pending','full_motion':'pending','medical':'pending','full_listening':'not_applicable','current_shot':'pending'},
                'medical_review':'pending','usage_notes':'；'.join(limits),'files':files}
        revision=canonical_revision(record);record['revision']=revision
        folder=Path('payloads/paper-theatre')/identifier/revision
        for name,body in data.items():
            path=root/folder/name
            if path.exists() and path.read_bytes()!=body:raise ValueError('不能覆盖已登记原件')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
        record_path=Path('records/paper-theatre')/identifier/revision/'record.json';write(root/record_path,record)
        row={'id':f'paper:{identifier}@{revision}','source_id':identifier,'revision':revision,'title':title,
             'kind':'code_component','reuse_scope':{'kind':'general'},'series_ids':[],'tags':record['tags'],'discovery':fields,
             'portable_record':record_path.as_posix(),'portable_record_sha256':hashlib.sha256((root/record_path).read_bytes()).hexdigest(),
             'payload':[{**item,'path':(folder/item['path']).as_posix()} for item in files],
             'provenance':{'source_type':'original_diagram','source_ref':{'recorded_in':'sources.json'}},
             'review_boundary':{'admission':'reusable_candidate','static':'pending','motion':'pending','medical':'pending',
                                'listening':'not_applicable','quality_debt':['medical_review_pending','current_shot_review_pending']}}
        if not any(r['id']==row['id'] for r in rows):rows.append(row)
        discovery['assets'][identifier]=fields
        if identifier not in storage['bundled_source_ids']:storage['bundled_source_ids'].append(identifier)
        added.append(row['id'])
    (root/'catalog/assets.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in sorted(rows,key=lambda x:x['id'])))
    write(root/'collections/discovery.json',discovery);write(root/'catalog/media-storage.json',storage)
    return {'registered':added,'bytes':sum(p['bytes'] for r in rows if r['id'] in added for p in r['payload'])}


if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
