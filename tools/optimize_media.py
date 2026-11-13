#!/usr/bin/env python3
"""Build a complete compressed library with independent, reconstructable revisions."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import posixpath
import shutil
import struct
import subprocess
import tempfile
import tarfile
from concurrent.futures import ThreadPoolExecutor
from media_store import ROOT, contained, matches, read, sha

POLICY = 'webp90-alpha100-aac192-or-flac-v1'
TEXT = {'.json', '.yaml', '.yml', '.html', '.js', '.mjs', '.ts', '.css', '.md', '.py', '.txt', '.svg'}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def rewrite(value, mapping):
    if isinstance(value, dict):
        return {mapping.get(k, k): rewrite(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite(v, mapping) for v in value]
    if isinstance(value, str):
        return mapping.get(value, value)
    return value


def canonical(record):
    body={k:v for k,v in record.items() if k not in {'schema', 'revision'}}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:20]


def run(args):
    return subprocess.run(args, check=True, capture_output=True, timeout=120)


def encode(job, temporary):
    item, source, lossless, movable = job
    digest=item['sha256']; ext=source.suffix.lower(); destination=temporary/(digest+('.webp' if ext=='.png' else '.flac'))
    if not matches(source,item):
        raise ValueError('压缩来源已变化：'+item['path'])
    if ext=='.png':
        header=source.read_bytes()[:33];width,height=struct.unpack('>II',header[16:24])
        if header[24]>8 or b'acTL' in source.read_bytes():
            return digest, source, {'codec':'original','reason':'bit_depth_or_animation'}
        args=['cwebp','-quiet','-m','4','-metadata','all']
        args+=['-lossless','-exact','-q','100'] if lossless else ['-q','90','-alpha_q','100']
        run([*args,str(source),'-o',str(destination)])
        try:
            from PIL import Image
            with Image.open(source) as a, Image.open(destination) as b:
                original,encoded=a.convert('RGBA').tobytes(),b.convert('RGBA').tobytes()
        except ImportError:
            def rgba(path):
                return run(['ffmpeg','-v','error','-nostdin','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-']).stdout
            original,encoded=rgba(source),rgba(destination)
        if len(original)!=width*height*4 or len(encoded)!=len(original) or original[3::4]!=encoded[3::4]:
            raise ValueError('画布或Alpha改变：'+item['path'])
        if movable and min(original[3::4])==255:
            raise ValueError('独立运动图层没有透明区域，不能把整图背景压缩后当部件：'+item['path'])
        if lossless and original!=encoded:
            raise ValueError('无损图像像素改变：'+item['path'])
        detail={'codec':'webp_lossless' if lossless else 'webp_q90','alpha':'exact','width':width,'height':height}
    else:
        run(['flac','-s','-8','-V','--keep-foreign-metadata','-o',str(destination),str(source)])
        detail={'codec':'flac','sample_verification':'encoder_verify'}
        # Precise short transients and individual rhythmic stems keep FLAC.
        name=source.stem.lower()
        if item['bytes']>500_000 and 'pulse' not in name and 'motif' not in name and 'loop' not in name:
            aac=temporary/(digest+'.m4a')
            run(['ffmpeg','-v','error','-nostdin','-i',str(source),'-map','0:a:0','-c:a','aac','-b:a','192k','-movflags','+faststart',str(aac)])
            # Retain FLAC when AAC's additional saving is negligible.
            if aac.stat().st_size<destination.stat().st_size*.85:
                destination=aac; detail={'codec':'aac_192k','listening_review':'pending'}
    if destination.stat().st_size>=item['bytes']:
        return digest,source,{'codec':'original','reason':'compression_not_smaller'}
    return digest,destination,detail


def text_references(body, relative, mapping):
    """Rewrite only known quoted URLs/paths, including parent-relative module URLs."""
    parent=posixpath.dirname(relative)
    pairs={}
    for old,new in mapping.items():
        if old==new:continue
        pairs[old]=new
        pairs[posixpath.relpath(old,parent or '.')]=posixpath.relpath(new,parent or '.')
    for old,new in sorted(pairs.items(),key=lambda p:-len(p[0])):
        for quote in ('"', "'", '`'):
            body=body.replace(quote+old+quote,quote+new+quote)
        body=body.replace('url('+old+')','url('+new+')')
    return body


def optimize(root=ROOT, jobs=4):
    """Mutate only a staged standalone full export, never the source repository."""
    root=Path(root).resolve()
    if (root/'.git').exists():raise ValueError('压缩只写独立导出目录，不重写源码原件')
    require_encoders()
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    original_catalog=sha(root/'catalog/assets.jsonl')
    spec=read(root/'catalog/media-storage.json')
    if spec.get('delivery_policy')==POLICY:return read(root/'catalog/delivery-report.json')
    parts={p['path']:p for row in rows for p in row['payload']}
    # Vector-derived medical diagrams retain exact pixels and line edges.
    lossless={p['sha256'] for row in rows if row['kind']=='medical_cutout' for p in row['payload'] if p['path'].endswith('.png')}
    media={p['sha256']:p for p in parts.values() if Path(p['path']).suffix.lower() in {'.png','.wav'}}
    movable=set()
    for row in rows:
        record=read(contained(root,row['portable_record']))
        if row.get('kind') in {'image','transparent_subject','medical_cutout'} and row.get('discovery',{}).get('category') not in {'stage','environment'}:
            layers=record.get('asset_bundle') or [record.get('asset') or {'path':record.get('entry')}]
            paths={layer.get('path') for layer in layers}
            movable.update(p['sha256'] for p in record['files'] if p['path'] in paths and p['path'].lower().endswith('.png'))
        if row.get('kind')=='motion_recipe':
            movable.update(p['sha256'] for p in record['files'] if p['path'].startswith(('assets/','original/files/')) and p['path'].lower().endswith('.png'))
    id_map={}; revision_map={}; path_map={}; hash_map={}; new_rows=[]
    with tempfile.TemporaryDirectory(prefix='.encode-',dir=root.parent) as folder:
        temp=Path(folder)
        work=[(p,contained(root,p['path']),h in lossless,h in movable) for h,p in media.items()]
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            encoded={digest:(source,info) for digest,source,info in executor.map(lambda job:encode(job,temp),work)}
        stage=temp/'payloads';stage.mkdir()
        for row in rows:
            record=read(contained(root,row['portable_record']))
            old_prefix='payloads/paper-theatre/'+row['source_id']+'/'+row['revision']
            mapping={}; sources={}; details=[]
            for part in record['files']:
                source=contained(root,old_prefix+'/'+part['path'])
                output,detail=encoded.get(part['sha256'],(source,{'codec':'original'}))
                target=str(Path(part['path']).with_suffix(output.suffix)) if output!=source else part['path']
                mapping[part['path']]=target; sources[part['path']]=output
                if output!=source:details.append({'path':part['path'],'encoded_path':target,'source_sha256':part['sha256'],**detail})
            new_record=rewrite(copy.deepcopy(record),mapping)
            files=[]; staged=stage/(row['source_id']+'-'+row['revision']);staged.mkdir()
            for part in record['files']:
                target=contained(staged,mapping[part['path']]);target.parent.mkdir(parents=True,exist_ok=True)
                source=sources[part['path']]
                # Evidence stays unchanged. Executable sources and live manifests
                # follow actual encoded filenames rather than renamed PNG bytes.
                if source.suffix.lower() in TEXT and part.get('role')!='evidence':
                    body=source.read_text()
                    if source.suffix.lower()=='.json':
                        body=json.dumps(rewrite(json.loads(body),mapping),ensure_ascii=False,indent=2)+'\n'
                    else:body=text_references(body,part['path'],mapping)
                    target.write_text(body)
                else:shutil.copy2(source,target)
                descriptor={'path':mapping[part['path']],'role':part.get('role','payload'),'sha256':sha(target),'bytes':target.stat().st_size}
                files.append(descriptor)
                if target.suffix in {'.webp','.flac','.m4a'}:hash_map[part['sha256']]=descriptor['sha256']
            new_record['files']=files
            changed=files!=record['files']
            if changed:
                new_record['delivery']={'policy':POLICY,'source_asset_id':row['id'],'source_record_sha256':row['portable_record_sha256'],'encodings':details}
            revision=canonical(new_record);new_record['revision']=revision
            new_id='paper:'+row['source_id']+'@'+revision
            prefix='payloads/paper-theatre/'+row['source_id']+'/'+revision
            # Old input tree is retained until every asset has been encoded.
            final=temp/'final'/row['source_id']/revision;final.parent.mkdir(parents=True,exist_ok=True);staged.rename(final)
            record_ref='records/paper-theatre/'+row['source_id']+'/'+revision+'/record.json'
            write(root/record_ref,new_record)
            result={**row,'id':new_id,'revision':revision,'portable_record':record_ref,'portable_record_sha256':sha(root/record_ref),
                    'payload':[{**p,'path':prefix+'/'+p['path']} for p in files]}
            if changed:
                result['delivery']={'policy':POLICY,'source_asset_id':row['id'],'encoding_review':'pending' if any(d['codec'] in {'webp_q90','aac_192k'} for d in details) else 'lossless_verified'}
            new_rows.append(result);id_map[row['id']]=new_id;revision_map[row['revision']]=revision;path_map[row['portable_record']]=record_ref
            for old,new in zip(record['files'],files):path_map[old_prefix+'/'+old['path']]=prefix+'/'+new['path']
        # Retire the staged original media and duplicate portable source copies.
        shutil.rmtree(root/'payloads')
        (root/'payloads').mkdir();(temp/'final').rename(root/'payloads/paper-theatre')
    mapping={**id_map,**revision_map,**path_map,**hash_map}
    relative_mapping={**mapping,**{'../../'+old:'../../'+new for old,new in path_map.items()}}
    # All collections refer to the new exact revisions, including scale hashes.
    for path in (root/'collections').rglob('*.json'):
        write(path,rewrite(read(path),mapping))
    for path in (root/'tools').rglob('*'):
        if not path.is_file() or path.suffix not in TEXT:continue
        if path.suffix=='.json':write(path,rewrite(read(path),relative_mapping))
        else:path.write_text(text_references(path.read_text(),str(path.relative_to(root)),path_map))
    new_rows=rewrite(new_rows,mapping)
    # Keep provenance pointed at the original source identity, not at itself.
    for old,result in zip(rows,new_rows):
        if 'delivery' in result:result['delivery']['source_asset_id']=old['id']
    from query_assets import effective_row, load_curation
    curation=load_curation(root)
    new_rows=[effective_row(row,curation) for row in new_rows]
    (root/'catalog/assets.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n' for row in new_rows))
    keep={row['portable_record'] for row in new_rows}
    for path in (root/'records').rglob('*'):
        if path.is_file() and str(path.relative_to(root)) not in keep:path.unlink()
    # Deduplicate byte-identical files within this read-only installation only.
    physical={};logical=0
    for row in new_rows:
        for part in row['payload']:
            file=contained(root,part['path']);logical+=part['bytes']
            if part['sha256'] in physical:
                file.unlink();os.link(physical[part['sha256']],file)
            else:physical[part['sha256']]=file
            file.chmod(0o444)
    spec.update(profile='full',delivery_policy=POLICY,source_catalog_sha256=original_catalog)
    write(root/'catalog/media-storage.json',spec)
    report={'policy':POLICY,'source_catalog_sha256':original_catalog,'original_media_bytes':sum(p['bytes'] for p in parts.values()),
            'installed_media_bytes':sum(p.stat().st_size for p in physical.values()),'referenced_media_bytes':logical,
            'duplicate_content_eliminated_bytes':logical-sum(p.stat().st_size for p in physical.values()),
            'registered_versions':len(new_rows),'encoded_unique_files':sum(info['codec']!='original' for _,info in encoded.values()),
            'codecs':{codec:sum(info['codec']==codec for _,info in encoded.values()) for codec in sorted({info['codec'] for _,info in encoded.values()})},
            'semantic_review':'current_shot_required','aliases':id_map}
    write(root/'catalog/delivery-report.json',report)
    from materialize_package import materialize
    materialize(root,profile='full')
    return report


def require_encoders():
    missing=[name for name in ('cwebp','ffmpeg','flac') if not shutil.which(name)]
    if missing:raise ValueError('从原件构建压缩包需要 '+', '.join(missing)+'；可直接安装已预构建的完整版，无需本机转码')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--export',type=Path,required=True);parser.add_argument('--jobs',type=int,default=4);parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    from materialize_package import export
    export(args.root,args.export,'full')
    result=optimize(args.export,max(1,min(args.jobs,8)))
    if args.archive:
        if args.archive.exists():raise ValueError('压缩包目标已存在，保留现有文件')
        with tarfile.open(args.archive,'w:gz',compresslevel=6) as archive:
            archive.add(args.export,arcname='mac-media-assets')
        result={**result,'archive':str(args.archive),'archive_bytes':args.archive.stat().st_size,'archive_sha256':sha(args.archive)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
