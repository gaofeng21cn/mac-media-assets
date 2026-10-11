#!/usr/bin/env python3
"""Measure source audio for selection, not subjective listening approval."""
import argparse, json, math, subprocess, wave, array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def describe(root=ROOT):
 rows=[json.loads(l) for l in (root/'catalog/assets.jsonl').read_text().splitlines() if l.strip()]
 discovery=json.loads((root/'collections/discovery.json').read_text()).get('assets',{})
 out=[]
 for row in rows:
  if row['kind'] not in {'audio','music_score'}:continue
  paths=[p['path'] for p in row['payload'] if p['path'].endswith(('.wav','.mp3'))]
  parameter_files=[p['path'] for p in row['payload'] if p['path'].endswith(('performance.json','parameters.json'))]
  parameters=json.loads((root/parameter_files[0]).read_text()) if parameter_files else {}
  scores=[]
  for ref in paths:
   p=root/ref
   result=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=sample_rate,channels','-of','json',str(p)],capture_output=True,text=True)
   spec=json.loads(result.stdout) if result.returncode==0 else {}
   scores.append({'path':ref,'duration_seconds':float(spec.get('format',{}).get('duration',0)), 'sample_rate':spec.get('streams',[{}])[0].get('sample_rate'),'channels':spec.get('streams',[{}])[0].get('channels')})
  field=discovery.get(row['source_id'],{});kind=field.get('category','bgm')
  duration=parameters.get('duration') or max((s['duration_seconds'] for s in scores),default=0)
  density=[{'stem':t.get('stem'),'note_onsets':len(t.get('notes',[])),
            'onsets_per_second':round(len(t.get('notes',[]))/duration,3) if duration else None}
           for t in parameters.get('tracks',[])]
  out.append({'asset_id':row['id'],'source_id':row['source_id'],'category':kind,'title':field.get('display_title',row['title']), 'emotion_or_event':field.get('aliases',[]),'bpm':parameters.get('bpm'), 'density':'MIDI起音密度只描述谱面，听感密度按分轨试听判断','onset_density_by_stem':density,'edit_points_seconds':[round(n*16*60/parameters['bpm'],3) for n in range(int(duration/(16*60/parameters['bpm']))+1)] if parameters.get('bpm') else [],'stems':list(dict.fromkeys(t.get('stem') for t in parameters.get('tracks',[]) if t.get('stem'))), 'variants_or_tracks':scores,'editable_midi':any(p['path'].endswith('.mid') for p in row['payload']),'contact_sync':'由本镜头命名接触事件驱动' if kind=='sfx' else '按旁白空隙与情绪转折调整分轨','mix_role':'旁白下的可选配乐' if kind=='bgm' else '可选材质回应', 'ending':'逐轨试听尾音，短镜头优先选事件变体；不要任意截断音乐尾音','technical_analysis':'duration_and_format_measured','listening_review':'pending','current_mix':'pending'})
 return {'schema':'mac_audio_discovery/v1','assets':out,'policy':'技术测量不替代审听。配乐不是固定循环，拟音不是每次移动都响。'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
 if args.refresh:
  value=describe();(ROOT/'collections/audio.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 else:value=json.loads((ROOT/'collections/audio.json').read_text())
 print(json.dumps({'assets':len(value['assets']),'categories':{kind:sum(r['category']==kind for r in value['assets']) for kind in ['bgm','sfx']},'listening_review':'pending'},ensure_ascii=False))
