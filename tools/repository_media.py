#!/usr/bin/env python3
"""Own repository-wide media intake, durable objects and the Git growth boundary."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from media_store import ROOT, contained, locked, matches, read, sha, storage
from optimize_media import POLICY, canonical, prepare_asset, rewrite, text_references, write

MEDIA = {'.png','.jpg','.jpeg','.webp','.gif','.tif','.tiff','.avif','.wav','.flac','.mp3','.m4a','.ogg','.mp4','.mov','.zip','.gz','.7z','.psd'}
SKIP = {'.git','node_modules','__pycache__','.venv','work','output','.playwright-cli'}


def state_root():
    return Path(os.environ.get('MAC_MEDIA_STATE') or Path.home()/'.local/share/mac-media-assets').expanduser().resolve()


def local_config(root):
    path = state_root()/'libraries.json'
    return read(path).get('libraries',{}).get(str(Path(root).resolve()),{}) if path.is_file() else {}


def object_root(root):
    return Path(local_config(root).get('object_root',state_root()/'media')).expanduser().resolve()


def object_path(root, item):
    digest = item['sha256']
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('对象哈希无效')
    return object_root(root)/'objects'/digest[:2]/digest


def object_available(root, item):
    path = object_path(root,item)
    if path.is_file():
        if not matches(path,item):
            raise ValueError('持久媒体对象字节不一致：'+item['sha256'])
        return path
    return None


def put(root, source, item):
    if not matches(source,item):
        raise ValueError('入库来源字节不一致：'+str(source))
    target = object_path(root,item)
    if target.is_file():
        if not matches(target,item):raise ValueError('同哈希对象存在不同字节')
        return target
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.object-',dir=target.parent,delete=False) as output:
        temporary=Path(output.name)
        try:
            with source.open('rb') as incoming:shutil.copyfileobj(incoming,output)
            output.flush()
        except BaseException:
            temporary.unlink(missing_ok=True);raise
    try:
        if not matches(temporary,item):raise ValueError('对象复制校验失败')
        temporary.chmod(0o444);temporary.replace(target)
    finally:temporary.unlink(missing_ok=True)
    return target


def legacy_blob_paths(root, ref):
    # The baseline only supplies path membership. Blob sizes would hydrate
    # historical media in the release controller's blobless clone.
    result = subprocess.run(['git', '-C', str(root), 'ls-tree', '-rz', ref],
                            capture_output=True, check=True)
    paths = set()
    for part in result.stdout.split(b'\0'):
        if not part:
            continue
        header, path = part.split(b'\t', 1)
        _, kind, _ = header.split()
        if kind == b'blob':
            paths.add(os.fsdecode(path))
    return paths


def media_file(path):
    if path.suffix.lower() in MEDIA:return True
    with path.open('rb') as stream:head=stream.read(16)
    return (head.startswith((b'\x89PNG',b'\xff\xd8\xff',b'GIF8',b'fLaC',b'OggS',b'PK\x03\x04',b'II*\0',b'MM\0*'))
            or (head.startswith(b'RIFF') and head[8:12] in {b'WEBP',b'WAVE'}) or head[4:8]==b'ftyp')


def staged_media(root, name, oid):
    if Path(name).suffix.lower() in MEDIA:return True
    command=subprocess.Popen(['git','-C',str(root),'cat-file','blob',oid],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:head=command.stdout.read(16)
    finally:
        command.stdout.close();command.terminate();command.wait()
    return (head.startswith((b'\x89PNG',b'\xff\xd8\xff',b'GIF8',b'fLaC',b'OggS',b'PK\x03\x04'))
            or (head.startswith(b'RIFF') and head[8:12] in {b'WEBP',b'WAVE'}) or head[4:8]==b'ftyp')


def repository_files(root):
    for folder,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if d not in SKIP and not d.startswith('.git')]
        for name in files:
            path=Path(folder)/name
            if path.is_file():yield path


def audit(root=ROOT, *, require_published=False):
    root=Path(root).resolve();policy=storage(root).get('repository_storage')
    if not policy:return {'status':'disabled','errors':[]}
    errors=[];baseline=set()
    if (root/'.git').exists():baseline=legacy_blob_paths(root,policy['legacy_git_ref'])
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    managed={p['path'] for r in rows for p in r['payload'] if p.get('storage')=='object'}
    raw=[];metadata_bytes=0
    for path in repository_files(root):
        name=str(path.relative_to(root))
        if name in baseline or name in managed:continue
        if media_file(path):raw.append(name)
        else:metadata_bytes+=path.stat().st_size
    objects={p['sha256']:p for r in rows for p in r['payload'] if p.get('storage')=='object'}
    published=storage(root).get('object_source',{}).get('published_sha256',[])
    missing_objects=[]
    for digest,item in objects.items():
        if object_available(root,item) is None and digest not in published:
            missing_objects.append(digest)
        if require_published and digest not in published:errors.append('媒体对象尚未发布：'+digest)
    if require_published and objects and not re.fullmatch('sha256:[a-f0-9]{64}',storage(root).get('object_source',{}).get('manifest_digest','')):
        errors.append('媒体OCI缺少固定manifest digest')
    # The core budget includes unchanged metadata too; historical media have a frozen allowance.
    core=sum(p.stat().st_size for p in repository_files(root) if not media_file(p))
    return {'status':'passed' if not errors else 'blocked','errors':errors,
            'unprocessed_media':raw,'object_files':len(objects),'object_bytes':sum(x['bytes'] for x in objects.values()),
            'missing_objects_pending_publication':missing_objects,'core_bytes':core,'legacy_git_ref':policy.get('legacy_git_ref')}


def row_for_record(library, record_path, record):
    from sync_from_workbench import boundary
    return {'id':'paper:'+record['id']+'@'+record['revision'],'source_id':record['id'],'revision':record['revision'],
            'portable_record':str(record_path.relative_to(library)),'portable_record_sha256':sha(record_path),
            'kind':record.get('kind','image'),'title':record.get('title',record['id']),
            'payload':[{**p,'path':str(record_path.parent.relative_to(library)/p['path'])} for p in record['files']],
            'reuse_scope':record.get('reuse_scope',{}),'review_boundary':boundary(record.get('kind'),record),
            **{k:record[k] for k in ['content_bounds','content_bounds_format','tags','asset_bundle','assembly','discovery'] if k in record},
            'provenance':{'source_type':record.get('source',{}).get('kind','registered'),'source_ref':record.get('source',{})}}


def prepare_admission(root, library, record_path, cache=None, *, existing=False, direct=False):
    from sync_from_workbench import public_reusable
    record=read(record_path)
    if not public_reusable(record) or (not existing and not direct and record.get('reuse_scope',{}).get('kind') not in {'general','topic'}):
        return None
    if record.get('status')=='reference_only' and not existing:return None
    from query_assets import load_curation
    decisions=read(library/'curation.json').get('assets',{}) if (library/'curation.json').is_file() else {}
    identifier='paper:'+record['id']+'@'+record['revision']
    if decisions.get(identifier,{}).get('status') in {'superseded','needs_rebuild'} and not existing:return None
    row=row_for_record(library,record_path,record)
    if library==root and str(record_path.relative_to(root)).startswith('records/'):
        catalog_rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
        row=next((r for r in catalog_rows if r['portable_record']==str(record_path.relative_to(root))),row)
    result=prepare_asset(library,row,cache,validate_movable=False)
    derived=result['record'];newrow=result['row']
    for part in newrow['payload']:
        part['storage']='object'
    # Archive masters outside Git before changing any repository path.
    for part in record['files']:
        suffix='/'+record['id']+'/'+record['revision']+'/'+part['path']
        source=next((contained(library,p['path']) for p in row['payload'] if p['path'].endswith(suffix)),record_path.parent/part['path'])
        put(root,source,part)
    for part in newrow['payload']:
        put(root,Path(result['resolved'][part['path']]),part)
    newrow['repository_storage']={'kind':'content_addressed_object','policy':POLICY,'source_asset_id':identifier}
    newrow['_normalization_map']={identifier:newrow['id'],record['revision']:derived['revision'],**result['hash_map'],
        row['portable_record']:newrow['portable_record'],
        **{old['path']:new['path'] for old,new in zip(row['payload'],newrow['payload'])}}
    return newrow,record,derived


def direct_record(root, path):
    """Record observable file facts; creative meaning stays pending."""
    digest=sha(path);identifier='direct_'+digest[:20]
    ext=path.suffix.lower()
    with path.open('rb') as stream:header=stream.read(16)
    if header.startswith(b'\x89PNG'):ext='.png'
    elif header.startswith(b'\xff\xd8\xff'):ext='.jpg'
    elif header.startswith(b'RIFF') and header[8:12]==b'WEBP':ext='.webp'
    elif header.startswith(b'RIFF') and header[8:12]==b'WAVE':ext='.wav'
    elif header.startswith(b'fLaC'):ext='.flac'
    kind='audio' if ext in {'.wav','.flac','.mp3','.m4a','.ogg'} else 'image' if ext in MEDIA-{'.wav','.flac','.mp3','.m4a','.ogg','.mp4','.mov','.zip','.gz','.7z','.psd'} else 'component'
    record={'schema':'animation_element/v1','id':identifier,'title':path.stem,'kind':kind,
        'entry':'files/payload'+ext,'reuse_scope':{'kind':'unclassified'},
        'source':{'kind':'local_direct_write','observed_path':str(path.relative_to(root)),'source_sha256':digest},
        'status':'pending_review','usage_notes':'用途待策展；文件格式、原始路径和字节来源已登记。',
        'review':{'static':'pending','full_motion':'pending','current_shot':'pending'},
        'files':[{'path':'files/payload'+ext,'role':'payload','sha256':digest,'bytes':path.stat().st_size}]}
    if kind=='image':
        try:
            from PIL import Image
            with Image.open(path) as image:
                bounds=image.convert('RGBA').getchannel('A').getbbox()
                record.update(content_bounds=list(bounds) if bounds else None,content_bounds_format='pixel_xyxy_right_bottom_exclusive')
        except (ImportError,OSError):pass
    record['revision']=canonical(record)
    target=root/'entries'/identifier/record['revision']/'record.json'
    write(target,record)
    payload=target.parent/record['entry'];payload.parent.mkdir(parents=True,exist_ok=True)
    if not payload.exists():
        try:os.link(path,payload)
        except OSError:shutil.copy2(path,payload)
    return target


def refresh_views(root, rows):
    for row in rows:
        for part in row['payload']:
            if part.get('storage')!='object':continue
            source=object_available(root,part)
            if source is None:continue
            target=contained(root,part['path'])
            if target.is_file() and matches(target,part):continue
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():raise ValueError('使用版路径已有不同字节：'+part['path'])
            try:os.link(source,target)
            except OSError:shutil.copy2(source,target)


def reconcile(root=ROOT, *, source_library=None, source_record=None, cache=None):
    root=Path(root).resolve();policy=storage(root).get('repository_storage')
    if not policy:return {'status':'disabled','processed':[],'errors':[]}
    base=object_root(root);base.mkdir(parents=True,exist_ok=True)
    with locked(base/'repository-writer'):
        rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
        current={r['id']:r for r in rows}
        original_ids=set(current)
        receipt_path=base/'libraries'/hashlib.sha256(str(root).encode()).hexdigest()/'intake.json'
        receipt=read(receipt_path) if receipt_path.is_file() else {'processed':{}}
        candidates=[];direct_paths={}
        for source in ([] if source_record else local_config(root).get('sources',[])):
            library=Path(source['library']);catalog=library/'catalog.json'
            if not catalog.is_file():continue
            known=set(source.get('existing_records',[]));backlog=set(source.get('backlog_records',[]))
            for item in read(catalog).get('items',[]):
                if item['record'] not in known or item['record'] in backlog:
                    candidates.append((library,contained(library,item['record'])))
        if source_library and source_record:candidates.append((Path(source_library).resolve(),Path(source_record).resolve()))
        baseline=legacy_blob_paths(root,policy['legacy_git_ref']) if (root/'.git').exists() else set()
        if not source_record:
            candidates.extend((root,path) for path in (root/'entries').glob('*/*/record.json') if str(path.relative_to(root)) not in baseline)
            for row in rows:
                if row.get('repository_storage'):continue
                path=contained(root,row['portable_record'])
                if path.is_file() and all(contained(root,p['path']).is_file() for p in row['payload']):candidates.append((root,path))
            registered={p['path'] for row in rows for p in row['payload']}
            for library,path in candidates:
                if library==root and str(path.relative_to(root)).startswith('entries/'):
                    registered.update(str((path.parent/p['path']).relative_to(root)) for p in read(path)['files'])
            for path in list(repository_files(root)):
                name=str(path.relative_to(root))
                if name in baseline or name in registered or not media_file(path):continue
                record_path=direct_record(root,path);candidates.append((root,record_path));direct_paths[str(record_path)]=path
        jobs=[];warnings=[]
        for library,path in dict.fromkeys(candidates):
            if not path.is_relative_to(library):warnings.append('来源记录越界：'+str(path));continue
            fingerprint=sha(path);previous=receipt['processed'].get(str(path))
            if previous and previous['asset_id'] in current:
                if previous['source_record_sha256']!=fingerprint:warnings.append('来源记录已改变，保留当前版本：'+str(path))
                continue
            jobs.append((library,path,fingerprint))
        def prepare(job):
            library,path,fingerprint=job
            try:
                return job,prepare_admission(root,library,path,cache,existing=library==root,direct=library==root),None
            except (OSError,ValueError,subprocess.SubprocessError) as error:
                return job,None,str(error)
        with ThreadPoolExecutor(max_workers=4) as executor:prepared=list(executor.map(prepare,jobs))
        processed=[];aliases={};mapping={};retired=[];preserve_rows=set()
        report_path=root/'catalog/delivery-report.json'
        prior=read(report_path) if report_path.is_file() else {'policy':POLICY,'aliases':{}}
        for (library,path,fingerprint),admission,error in prepared:
            if error:warnings.append(str(path)+': '+error);continue
            if admission is None:continue
            row,record,derived=admission
            source_id=row['repository_storage']['source_asset_id']
            # Distinct source records can converge on one delivered revision.
            # Bind the catalog to its first accepted bytes in candidate order.
            previous=current.get(row['id'])
            already_materialized=bool(previous and previous.get('repository_storage'))
            stored=contained(root,row['portable_record'])
            try:
                if already_materialized and (
                        previous['portable_record']!=row['portable_record']
                        or sha(stored)!=previous['portable_record_sha256']
                        or read(stored)!=derived or previous['payload']!=row['payload']):
                    raise ValueError('同一素材版本的登记或载荷不同：'+row['id'])
                if not already_materialized or source_id!=row['id']:
                    master=base/'masters'/record['id']/record['revision']/'record.json'
                    write(master,record)
                if not already_materialized:
                    write(stored,derived)
                    row['portable_record_sha256']=sha(stored)
            except (OSError, ValueError) as error:
                warnings.append(str(path)+': '+str(error))
                continue
            receipt['processed'][str(path)]={'source_record_sha256':fingerprint,'asset_id':row['id']}
            if already_materialized:
                if row['id'] in original_ids:
                    preserve_rows.add(row['id'])
                if source_id==row['id'] and library!=root:continue
            mapping.update(row.pop('_normalization_map'))
            if not already_materialized or source_id!=row['id']:
                current.pop(source_id,None);aliases[source_id]=row['id']
            if not already_materialized:
                current[row['id']]=row
                processed.append({'source_asset_id':source_id,'asset_id':row['id']})
            if library==root:
                original=next((r for r in rows if r['portable_record']==str(path.relative_to(root))),None)
                if original:retired.extend(root/p['path'] for p in original['payload'])
                else:retired.extend(path.parent/p['path'] for p in read(path)['files'])
                if str(path) in direct_paths:
                    raw=direct_paths[str(path)];retired.append(raw)
                    mapping[str(raw.relative_to(root))]=row['payload'][0]['path']
        prior['aliases']={old:aliases.get(new,new) for old,new in prior.get('aliases',{}).items()}
        prior['aliases'].update(aliases)
        if mapping:
            from query_assets import effective_row,load_curation
            for path in (root/'collections').rglob('*.json'):
                write(path,rewrite(read(path),mapping))
            curation=load_curation(root)
            rows=[]
            for original in sorted(current.values(),key=lambda r:r['id']):
                projected=original if original['id'] in preserve_rows else rewrite(original,mapping)
                # File descriptors already name final bytes. The same image may
                # also occur unchanged as provenance evidence in another asset.
                projected['payload']=original['payload']
                projected['portable_record_sha256']=original['portable_record_sha256']
                rows.append(effective_row(projected,curation))
            for row in rows:
                if row.get('repository_storage') and row['id'] not in preserve_rows:
                    source=next((old for old,new in aliases.items() if new==row['id']),row['repository_storage']['source_asset_id'])
                    row['repository_storage']['source_asset_id']=source
                    if row.get('delivery'):row['delivery']['source_asset_id']=source
            active={part['path'] for row in rows for part in row['payload']}
            for raw in dict.fromkeys(retired):
                if str(raw.relative_to(root)) not in active and raw.is_file():raw.unlink()
            # Live code and preview references follow actual compressed filenames.
            for folder in ['tools','docs']:
                for path in (root/folder).rglob('*'):
                    if not path.is_file() or path.suffix not in {'.json','.js','.mjs','.ts','.html','.css','.md','.py'}:continue
                    body=path.read_text();updated=text_references(body,str(path.relative_to(root)),mapping)
                    if updated!=body:path.write_text(updated)
            (root/'catalog/assets.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
            write(report_path,prior)
        else:rows=list(current.values())
        refresh_views(root,rows)
        receipt.pop('quarantine',None);write(receipt_path,receipt)
        check={'status':'deferred_to_package_build','errors':[]} if source_record else audit(root)
        return {'status':'completed_with_notes' if warnings else 'completed','processed':processed,'errors':check['errors'],
                'notes':warnings,'object_root':str(base),'repository':check}


def configure(root, library, backlog):
    root=Path(root).resolve();library=Path(library).resolve()
    path=state_root()/'libraries.json';value=read(path) if path.is_file() else {'libraries':{}}
    source={'library':str(library),'existing_records':[x['record'] for x in read(library/'catalog.json')['items']],
            'backlog_records':[x['library']['record'] for x in read(Path(backlog))] if backlog else []}
    value['libraries'][str(root)]={'object_root':str(state_root()/'media'),'sources':[source]}
    write(path,value)
    return {'status':'configured','source_count':len(source['existing_records']),'backlog_count':len(source['backlog_records'])}


def notify_library(library, records, cache=None):
    """Generated intake uses the same registered repository owner as direct writers."""
    library=Path(library).resolve();path=state_root()/'libraries.json'
    if not path.is_file():return []
    results=[]
    for root,config in read(path).get('libraries',{}).items():
        if any(Path(source['library']).resolve()==library for source in config.get('sources',[])):
            for record in records:
                results.append(reconcile(Path(root),source_library=library,source_record=library/record,cache=cache))
    return results


def media_layout(root, items, directory):
    """Build a standard OCI layout; ORAS handles registry transfer."""
    directory=Path(directory);blobs=directory/'blobs/sha256';blobs.mkdir(parents=True,exist_ok=True)
    def descriptor(body, media_type, title=None):
        digest=hashlib.sha256(body).hexdigest();target=blobs/digest
        if not target.exists():target.write_bytes(body)
        value={'mediaType':media_type,'digest':'sha256:'+digest,'size':len(body)}
        if title:value['annotations']={'org.opencontainers.image.title':title}
        return value
    index={'schema':'mac_media_objects/v1','objects':[{k:p[k] for k in ['sha256','bytes']} for _,p in sorted(items.items())]}
    index_bytes=(json.dumps(index,ensure_ascii=False,sort_keys=True)+'\n').encode()
    layers=[descriptor(index_bytes,'application/vnd.onepersonlab.mac-media-index.v1+json','objects.json')]
    for digest,item in sorted(items.items()):
        source=object_available(root,item)
        if source is None:raise ValueError('发布来源对象缺失')
        target=blobs/digest
        if not target.exists():
            try:os.link(source,target)
            except OSError:shutil.copy2(source,target)
        layers.append({'mediaType':'application/octet-stream','digest':'sha256:'+digest,'size':item['bytes'],
                       'annotations':{'org.opencontainers.image.title':digest}})
    manifest={'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json',
        'artifactType':'application/vnd.onepersonlab.mac-media.v1','config':descriptor(b'{}','application/vnd.oci.empty.v1+json'),
        'layers':layers,'annotations':{'org.opencontainers.image.source':storage(root)['source']['repository']}}
    body=(json.dumps(manifest,sort_keys=True)+'\n').encode()
    entry=descriptor(body,manifest['mediaType']);entry['annotations']={'org.opencontainers.image.ref.name':'media'}
    write(directory/'oci-layout',{'imageLayoutVersion':'1.0.0'})
    write(directory/'index.json',{'schemaVersion':2,'manifests':[entry]})
    return entry['digest']


def publish(root, framework):
    root=Path(root).resolve();result=reconcile(root)
    if result['errors']:raise ValueError('媒体对象尚未完整保存：'+'; '.join(result['errors']))
    spec=storage(root)
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    items={p['sha256']:p for r in rows for p in r['payload'] if p.get('storage')=='object'}
    if not items:return {'status':'no_new_objects'}
    repository=spec['repository_storage']['object_repository']
    if not re.fullmatch(r'ghcr\.io/[a-z0-9_.-]+/[a-z0-9_./-]+',repository):raise ValueError('媒体OCI仓库格式无效')
    with tempfile.TemporaryDirectory(prefix='mac-media-publication-') as folder:
        manifest=media_layout(root,items,Path(folder)/'layout')
        reference=repository+':media-'+manifest.removeprefix('sha256:')[:24]
        verify=['node',str(Path(framework)/'scripts/oci-publication-preflight.mjs'),'--ref',reference,
            '--artifact-type','application/vnd.onepersonlab.mac-media.v1','--source-url',spec['source']['repository'],
            '--verify-only','--digest-only','--expected-digest',manifest]
        before=subprocess.run(verify,capture_output=True,text=True,timeout=120)
        if before.returncode:
            if 'OCI artifact is not authenticated readable at ' not in before.stderr:
                raise ValueError('OCI现状核对失败；未重试写入')
            subprocess.run(['oras','cp','--from-oci-layout',str(Path(folder)/'layout')+':media',reference],
                           capture_output=True,text=True,check=True,timeout=900)
            subprocess.run(verify,capture_output=True,text=True,check=True,timeout=120)
        # Public asset consumers use anonymous reads. The package is already the
        # existing public MAC capability; media tags are supplemental artifacts.
        subprocess.run([*verify,'--anonymous'],capture_output=True,text=True,check=True,timeout=120)
    spec['object_source']={'repository':repository,'manifest_digest':manifest,'published_sha256':sorted(items)}
    write(root/'catalog/media-storage.json',spec)
    return {'status':'published','object_count':len(items),'manifest_digest':manifest}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['reconcile','audit','configure','publish'])
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--source-library',type=Path);parser.add_argument('--source-record',type=Path)
    parser.add_argument('--backlog',type=Path);parser.add_argument('--cache',type=Path);parser.add_argument('--require-published',action='store_true');parser.add_argument('--framework',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='reconcile':result=reconcile(args.root,source_library=args.source_library,source_record=args.source_record,cache=args.cache)
        elif args.command=='configure':result=configure(args.root,args.source_library,args.backlog)
        elif args.command=='publish':result=publish(args.root,args.framework or os.environ.get('OPL_FRAMEWORK_ROOT','../one-person-lab'))
        else:result=audit(args.root,require_published=args.require_published)
        print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(2 if result.get('errors') else 0)
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'blocked','errors':[str(error)]},ensure_ascii=False));raise SystemExit(2)


if __name__=='__main__':main()
