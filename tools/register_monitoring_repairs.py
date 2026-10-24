#!/usr/bin/env python3
"""Freeze contact-repaired public monitoring actions after actual frame review."""
from pathlib import Path
import json
import motion_package
ROOT=Path(__file__).resolve().parents[1]
def register(identifier, folder=None, root=ROOT):
 folder=Path(folder) if folder else ROOT/'work/action-contact-repair-20261024'/identifier
 r=json.loads((folder/'sequence.json').read_text())
 repairs={
 'mac_bp_cuff_action_v1':['空筒已佩戴件换为贴合前层，袖带从衣袖移到裸露上臂。','前臂与主机由同一台面承托，气管按前层原图接口一起变换。'],
 'mac_abpm_recording_v1':['补原有已佩戴状态之后的日夜记录时间线。','采样点只代表时点，不伪造血压值或测量频率。'],
 }
 return motion_package.freeze(folder,root,id=identifier,title=r['title'],scope=r['scope'],
  source_assets={'library':r['source_assets'],'generation':[],'note':'复用精确公开原件；运行源码为原创，样片无作者/品牌。'},
  discovery={'category':'motion','aliases':[r['title'],identifier],'actions':['器械操作','连续监测']if identifier.startswith('mac_bp')else['动态血压','日夜记录','24小时监测'],'medium':'code','renderers':['canvas2d']},
  tags=['paper_collage','monitoring','contact_repair_20261024'],
  checked=['原尺寸关键动作、接触极值、切换前后及浅深彩底和手机宽查看。','全部浏览器帧已渲染；随机拖动确定性和无报错已回读。'],
  defects_found_and_fixed=repairs[identifier],
  not_reviewed=['独立医学终审及当前生产镜头 pending；样片无声，不批准听感。'],
  usage_note='复制后显式接入 renderStudy，时间由镜头传入；本包医疗审核 pending。')
if __name__=='__main__':
 for name in ['mac_bp_cuff_action_v1','mac_abpm_recording_v1']:register(name)

