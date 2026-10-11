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
def boundary(kind,record=None):
 record=record or {}
 debt=record.get('quality_debt',[])
 review=record.get('review',{}) or record.get('visual_review',{}) or {}
 return {'admission':record.get('status','review_candidate'),'motion':review.get('full_motion','pending') if isinstance(review,dict) else 'pending','medical':(record.get('medical_review') or {}).get('status','pending') if isinstance(record.get('medical_review'),dict) else record.get('medical_review','pending'),'listening':'pending' if kind in ('audio','music_score') else 'not_applicable','quality_debt':debt}
def paper_rows(workspace,out):
 root=workspace/'assets/paper-theatre';cat=read(root/'catalog.json');rows=[]
 exclusions_path=out/'collections/exclusions.json'
 exclusions=read(exclusions_path).get('items',{}) if exclusions_path.is_file() else {}
 local_curation=root/'curation.json'
 assessments=read(local_curation).get('assets',{}) if local_curation.is_file() else {}
 for item in cat.get('items',[]):
  recpath=root/item['record'];rec=read(recpath);entry=f"paper:{rec['id']}@{rec.get('revision',item.get('revision','unknown'))}"
  if entry in exclusions or assessments.get(entry,{}).get('status') in {'needs_rebuild','superseded'} or rec.get('status')=='reference_only': continue
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
  rows.append({'id':entry,'portable_record':str(record_rel),'portable_record_sha256':sha(out/record_rel),'source_id':rec['id'],'revision':rec.get('revision',item.get('revision')),'kind':rec.get('kind','image'),'title':rec.get('title',rec['id']),'payload':payload,'provenance':{'source_type':(source.get('original_manifest') or {}).get('source_type',source.get('kind','workbench_registered')),'source_ref':source,'record_ref':str(recpath.relative_to(workspace))},'review_boundary':boundary(rec.get('kind'),rec),'reuse_scope':rec.get('reuse_scope',{'kind':'unclassified'}),'content_bounds':rec.get('content_bounds'),'content_bounds_format':rec.get('content_bounds_format'),'tags':rec.get('tags',[]),'usage':rec.get('usage',[]),'asset_bundle':rec.get('asset_bundle',[]),'assembly':rec.get('assembly')})
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args(); workspace=a.workspace.resolve();out=a.root.resolve();out.mkdir(parents=True,exist_ok=True)
 existing={}
 for catalog in ('assets.jsonl',):
  path=out/'catalog'/catalog
  if path.is_file():
   for line in path.read_text(encoding='utf-8').splitlines():
    if line.strip():
     row=json.loads(line);existing[row['id']]=row
 incoming=paper_rows(workspace,out)
 existing.update({row['id']:row for row in incoming})
 rows=list(existing.values())
 curation_path=out/'collections/curation.json'
 curation=read(curation_path).get('assets',{}) if curation_path.is_file() else {}
 exclusions_path=out/'collections/exclusions.json'
 exclusions=read(exclusions_path).get('items',{}) if exclusions_path.is_file() else {}
 for row in rows:
  if row['id'] in curation:
   row['curation']=curation[row['id']]
   if curation[row['id']].get('display_title'): row['title']=curation[row['id']]['display_title']
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
 # This repository is a usable catalog, not an archive. Withdrawn, superseded,
 # and reference-only material is omitted instead of being written to a second
 # catalog that future callers might accidentally discover.
 active=[row for row in rows if row.get('id') not in exclusions and row.get('review_boundary',{}).get('admission')!='reference_only' and row.get('curation',{}).get('status') not in {'needs_rebuild','superseded'}]
 (out/'catalog/assets.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in active),encoding='utf-8')
 stale_reference=out/'catalog/reference-assets.jsonl'
 if stale_reference.exists(): stale_reference.unlink()
 summary={'schema':'medical_video_asset_sync/v1','generated_at':datetime.now(timezone.utc).isoformat(),'workspace':str(workspace),'asset_count':len(active),'reference_count':0,'registered_versions':len(active),'by_kind':{},'by_series':{},'payload_files':sum(len(x['payload']) for x in active),'repo':str(out)}
 for x in active:
  summary['by_kind'][x['kind']]=summary['by_kind'].get(x['kind'],0)+1
  key=x.get('canonical_series_id')
  if key: summary['by_series'][key]=summary['by_series'].get(key,0)+1
 (out/'catalog/sync-readback.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'catalog/README.md').write_text('# 统一资产登记\n\n`assets.jsonl` 只收录当前可复用候选。历史关键帧、烘焙合图、错误透明、无法独立运动或被替代的版本不进入本仓库；原因写入 README 与覆盖文档，原件不作为库存保留。每行一个资产版本，载荷相对于仓库根；文件校验不签发质量批准。\n',encoding='utf-8')
 if (out/'contracts/opl_capability_package_manifest.json').is_file():
  from materialize_package import materialize
  materialize(out)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
