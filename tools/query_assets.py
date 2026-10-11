#!/usr/bin/env python3
import argparse,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'catalog/assets.jsonl'
series_catalog=json.loads((root/'collections/series.json').read_text(encoding='utf-8'))
aliases=series_catalog.get('aliases', {})
ap=argparse.ArgumentParser();ap.add_argument('--query');ap.add_argument('--kind');ap.add_argument('--series');ap.add_argument('--scope');ap.add_argument('--usable-for');ap.add_argument('--json',action='store_true');a=ap.parse_args()
rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def text(r):return json.dumps(r,ensure_ascii=False)
def row_series(r):
    values=set(r.get('series_ids', []))
    value=r.get('canonical_series_id')
    if value: values.add(value)
    scope=r.get('reuse_scope', {}) or {}
    for key in ('series_id', 'series'):
        if scope.get(key): values.add(scope[key])
    source=r.get('provenance', {}).get('source_ref', {}) or {}
    for key in ('series_id', 'series'):
        if source.get(key): values.add(source[key])
    return {aliases.get(v, v) for v in values} | values

out=[]
for r in rows:
 if a.query and a.query.lower() not in text(r).lower():continue
 if a.kind and r.get('kind')!=a.kind:continue
 if a.series and aliases.get(a.series, a.series) not in row_series(r):continue
 if a.scope and r.get('reuse_scope',{}).get('kind')!=a.scope:continue
 if a.usable_for and a.usable_for.lower() not in text(r).lower():continue
 out.append(r)
if a.json: print(json.dumps(out,ensure_ascii=False,indent=2))
else:
 print('id\tkind\ttitle\tscope\tadmission')
 for r in out: print('\t'.join([r['id'],r['kind'],r['title'],r.get('reuse_scope',{}).get('kind',''),r.get('review_boundary',{}).get('admission','')]))
