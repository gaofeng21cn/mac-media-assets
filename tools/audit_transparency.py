#!/usr/bin/env python3
"""Measure actual alpha by asset role; scene plates and review frames stay opaque."""
import argparse
import json
from pathlib import Path
from PIL import Image
from media_store import ROOT, contained, read


def audit(root=ROOT):
    measurements={}; findings=[]; references=0
    for row in [json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]:
        record=read(contained(root,row['portable_record']))
        parts=record.get('asset_bundle') or [record.get('asset') or {'path':record.get('entry')}]
        background=row['kind'] in {'environment','environment_plate'} or row.get('discovery',{}).get('category') in {'stage','environment'}
        if row['kind'] in {'motion_recipe','code_component'}:
            parts=[{'path':p['path']} for p in record['files'] if p.get('role')=='payload' and p['path'].lower().endswith(('.png','.webp')) and not p['path'].startswith('samples/')]
        for part in parts:
            path=part.get('path')
            if not path or Path(path).suffix.lower() not in {'.png','.webp','.jpg','.jpeg'}:continue
            descriptor=next(p for p in record['files'] if p['path']==path)
            item=next(p for p in row['payload'] if p['path'].endswith('/'+path))
            digest=descriptor['sha256'];references+=1
            if digest not in measurements:
                with Image.open(contained(root,item['path'])) as source:
                    alpha=source.convert('RGBA').getchannel('A');hist=alpha.histogram();pixels=source.width*source.height
                    measurements[digest]={'size':list(source.size),'alpha_min':alpha.getextrema()[0],'transparent_ratio':hist[0]/pixels,'opaque_ratio':hist[255]/pixels,
                        'corner_alpha':[alpha.getpixel(point) for point in [(0,0),(source.width-1,0),(0,source.height-1),(source.width-1,source.height-1)]]}
            stats=measurements[digest]
            if stats['alpha_min']==255:
                # Cached render snapshots are evidence about a scene, not pieces.
                role='background_plate' if background else 'render_snapshot' if path.startswith('.render-') else 'needs_role_review'
                findings.append({'asset_id':row['id'],'file':item['path'],'role':role,**stats})
    return {'unique_images':len(measurements),'image_references':references,'fully_opaque_references':len(findings),
            'needs_role_review':sum(item['role']=='needs_role_review' for item in findings),'findings':findings,
            'note':'Alpha only; fake checkerboard, halos and scene suitability require actual composites.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=audit(args.root)
    if args.output:args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='findings'},ensure_ascii=False))
    raise SystemExit(2 if result['needs_role_review'] else 0)
