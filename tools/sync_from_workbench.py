#!/usr/bin/env python3
"""Build a unified, content-addressed local projection from the workbench asset libraries."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone

KINDS={"environment","environment_plate","transparent_subject","medical_cutout","image","motion_recipe","component","code_component","audio","music_score","brand"}
SERIES_FILE=Path(__file__).resolve().parents[1]/'collections/series.json'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def canonical_series(value, aliases): return aliases.get(value, value) if value else None
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def clone(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  if dst.is_file() and sha(dst)==sha(src): return 'existing'
  dst.unlink()
 try: os.link(src,dst); return 'hardlink'
 except OSError: shutil.copy2(src,dst); return 'copy'
def boundary(kind,record=None,reference=False):
 record=record or {}
 if reference:
  return {'admission':'reference_only','motion':'not_approved_static_reference','medical':'not_approved','listening':'not_applicable'}
 debt=record.get('quality_debt',[])
 review=record.get('review',{}) or record.get('visual_review',{}) or {}
 return {'admission':record.get('status','review_candidate'),'motion':review.get('full_motion','pending') if isinstance(review,dict) else 'pending','medical':(record.get('medical_review') or {}).get('status','pending') if isinstance(record.get('medical_review'),dict) else record.get('medical_review','pending'),'listening':'pending' if kind in ('audio','music_score') else 'not_applicable','quality_debt':debt}
def paper_rows(workspace,out):
 root=workspace/'assets/paper-theatre';cat=read(root/'catalog.json');rows=[]
 for item in cat.get('items',[]):
  recpath=root/item['record'];rec=read(recpath);entry=f"paper:{rec['id']}@{rec.get('revision',item.get('revision','unknown'))}"
  payload=[]
  for f in rec.get('files',[]):
   src=recpath.parent/f['path']
   if not src.is_file(): continue
   rel=Path('payloads/paper-theatre')/rec['id']/rec.get('revision',item.get('revision','unknown'))/f['path']
   clone(src,out/rel)
   payload.append({'path':str(rel),'role':f.get('role','payload'),'sha256':f.get('sha256') or sha(src),'bytes':f.get('bytes',src.stat().st_size)})
  record_rel=Path('records/paper-theatre')/rec['id']/rec.get('revision',item.get('revision','unknown'))/'record.json'
  (out/record_rel).parent.mkdir(parents=True,exist_ok=True)
  (out/record_rel).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  source=rec.get('source',{})
  rows.append({'id':entry,'portable_record':str(record_rel),'portable_record_sha256':sha(out/record_rel),'source_id':rec['id'],'revision':rec.get('revision',item.get('revision')),'kind':rec.get('kind','image'),'title':rec.get('title',rec['id']),'payload':payload,'provenance':{'source_type':(source.get('original_manifest') or {}).get('source_type',source.get('kind','workbench_registered')),'source_ref':source,'record_ref':str(recpath.relative_to(workspace))},'review_boundary':boundary(rec.get('kind'),rec),'reuse_scope':rec.get('reuse_scope',{'kind':'unclassified'}),'content_bounds':rec.get('content_bounds'),'tags':rec.get('tags',[]),'usage':rec.get('usage',[])})
 return rows

def keyframe_rows(workspace,out):
 root=workspace/'assets/keyframes';cat=read(root/'catalog.json');rows=[]
 for a in cat.get('assets',[]):
  src=root/a['file']
  if not src.is_file(): continue
  sid=a['id'];rel=Path('payloads/keyframes')/sid/a['file'].replace('/','__');clone(src,out/rel)
  rows.append({'id':'keyframe:'+sid,'source_id':sid,'revision':'workbench-keyframe-v1','kind':'reference_frame','title':a.get('title',sid),'payload':[{'path':str(rel),'role':'reference','sha256':sha(src),'bytes':src.stat().st_size}], 'provenance':{'source_type':a.get('source',{}).get('kind','workbench_keyframe'),'source_ref':a.get('source',{}),'record_ref':'assets/keyframes/catalog.json'},'review_boundary':boundary('reference_frame',reference=True)|{'historical_image_review':a.get('historical_image_review'),'related_video_review':a.get('related_video_review')},'reuse_scope':{'kind':'reference_only','series_id':a.get('series_id')},'content_bounds':None,'dimensions':a.get('dimensions'),'tags':a.get('tags',[]),'purpose':a.get('purpose'),'style':a.get('style'),'usage':a.get('usage_records',[])})
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args(); workspace=a.workspace.resolve();out=a.root.resolve();out.mkdir(parents=True,exist_ok=True)
 rows=paper_rows(workspace,out)+keyframe_rows(workspace,out)
 series_config=read(SERIES_FILE) if SERIES_FILE.is_file() else {}
 aliases=series_config.get('aliases',{})
 for row in rows:
  candidates=[]
  scope=row.get('reuse_scope',{}) or {}
  source=row.get('provenance',{}).get('source_ref',{}) or {}
  for value in (scope.get('series_id'), scope.get('series'), source.get('series_id'), source.get('series')):
   if value and value not in candidates: candidates.append(value)
  row['series_ids']=candidates
  row['canonical_series_id']=next((canonical_series(value,aliases) for value in candidates if canonical_series(value,aliases)),None)
 rows.sort(key=lambda x:x['id'])
 (out/'catalog/assets.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
 summary={'schema':'medical_video_asset_sync/v1','generated_at':datetime.now(timezone.utc).isoformat(),'workspace':str(workspace),'asset_count':len(rows),'by_kind':{},'by_series':{},'payload_files':sum(len(x['payload']) for x in rows),'repo':str(out)}
 for x in rows:
  summary['by_kind'][x['kind']]=summary['by_kind'].get(x['kind'],0)+1
  key=x.get('canonical_series_id')
  if key: summary['by_series'][key]=summary['by_series'].get(key,0)+1
 (out/'catalog/sync-readback.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'catalog/README.md').write_text('# 统一资产登记\n\n每行一个资产版本。`payload` 路径相对于外挂仓库根目录；`review_boundary` 明确静态参考、连续动作、医学与听感的边界。\n',encoding='utf-8')
 if (out/'contracts/opl_capability_package_manifest.json').is_file():
  from materialize_package import materialize
  materialize(out)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
