#!/usr/bin/env python3
"""Own the optional complete offline media installation of this same Package."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
from urllib.request import urlopen
from media_store import ROOT, cache_root, contained, locked, matches, read, relative, sha, storage


def index_identity(root=ROOT):
    return sha(Path(root)/'catalog/assets.jsonl')


def installation_identity(root=ROOT):
    descriptor=read(Path(root)/'opl-package.json')
    return hashlib.sha256((index_identity(root)+descriptor['content_lock'].get('digest','')+descriptor['version']).encode()).hexdigest()


def inspect(root=ROOT, cache=None):
    root,cache=Path(root),cache_root(cache)
    version=read(root/'opl-package.json')['version']
    pointer=cache/'offline/current.json'
    rows=[]
    if pointer.is_file():
        record=read(pointer);location=contained(cache/'offline',record['directory'])
        marker=location/'offline-installation.json'
        if marker.is_file():
            receipt=read(marker)
            if receipt.get('package_id')=='mac-media-assets' and receipt.get('catalog_sha256')==record['catalog_sha256']:
                rows=[{'installation_id':'media:offline','profile':'offline','kind':'data_directory',
                       'version':receipt['version'],'mode':'release','location':str(location),'active':False,
                       'revision':sha(marker),'supported_actions':['uninstall'],
                       'catalog_sha256':receipt['catalog_sha256'],'file_count':receipt['file_count'],
                       'size_bytes':receipt['size_bytes']}]
    current=bool(rows and read(Path(rows[0]['location'])/'offline-installation.json').get('installation_fingerprint')==installation_identity(root))
    return {'package_id':'mac-media-assets','version':version,'installations':rows,
            'installed_profiles':['offline'] if current else [],'active_installation_status':'inactive'}


def _copy(source,destination,item):
    if not matches(source,item):raise ValueError('离线来源与登记字节不一致：'+item['path'])
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)


def install(root=ROOT,cache=None,source_root=None):
    root,cache=Path(root).resolve(),cache_root(cache)
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    # Historical bytes remain archival; normal query/use still enforces withdrawal.
    wanted={part['path']:part for row in rows for part in row['payload']}
    identity=index_identity(root)
    installation=installation_identity(root)
    with locked(cache):
        before=inspect(root,cache)
        if before['installed_profiles']:
            return {**before,'status':'already_installed'}
        offline=cache/'offline';offline.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.install-',dir=offline) as temporary:
            stage=Path(temporary)/'library';stage.mkdir()
            manifest=read(root/'opl-package.json')
            # Retain callable tools and every source/review record independently.
            for name in manifest['content_lock']['paths']+['opl-package.json']:
                if name in wanted:continue
                destination=contained(stage,name);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(contained(root,name),destination)
            # The installed carrier owns opl-package.json; repository-only
            # projection metadata is not part of its content lock.
            owner_manifest=stage/'contracts/opl_capability_package_manifest.json'
            owner_manifest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/'opl-package.json',owner_manifest)
            missing={}
            for name,item in wanted.items():
                source=contained(root,name)
                if not source.is_file() and source_root is not None:source=contained(source_root,name)
                if source.is_file():
                    _copy(source,contained(stage,name),item)
                else:missing[name]=item
            if missing:
                source=storage(root).get('source',{})
                repository,revision=source.get('repository',''),source.get('revision','')
                if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git',repository) or not re.fullmatch('[a-f0-9]{40}',revision):
                    raise ValueError('离线完整版需要完整固定来源提交')
                slug=repository.removeprefix('https://github.com/').removesuffix('.git')
                # One immutable tree stream avoids thousands of small requests.
                with urlopen('https://codeload.github.com/'+slug+'/tar.gz/'+revision,timeout=60) as stream:
                    with tarfile.open(fileobj=stream,mode='r|gz') as archive:
                        for member in archive:
                            name=member.name.split('/',1)[-1]
                            if name not in missing:continue
                            item=missing[name]
                            if not member.isfile() or member.size!=item['bytes']:
                                raise ValueError('离线归档成员类型或长度不一致')
                            destination=contained(stage,name);destination.parent.mkdir(parents=True,exist_ok=True)
                            with archive.extractfile(member) as incoming,destination.open('wb') as output:
                                shutil.copyfileobj(incoming,output,1024*1024)
                            if not matches(destination,item):raise ValueError('离线归档成员哈希不一致')
                            del missing[name]
                            if not missing:break
                if missing:raise ValueError('固定来源缺少离线媒体，原安装保留')
            # A complete standalone directory also carries its own full lock;
            # the default catalog descriptor is never changed by this install.
            spec=storage(stage);spec['profile']='full'
            (stage/'catalog/media-storage.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
            from materialize_package import materialize
            materialize(stage,profile='full')
            receipt={'package_id':'mac-media-assets','profile':'offline','version':manifest['version'],
                     'installation_fingerprint':installation,'core_content_digest':manifest['content_lock'].get('digest'),
                     'catalog_sha256':identity,'file_count':len(wanted),'size_bytes':sum(x['bytes'] for x in wanted.values()),
                     'verification':'all_registered_media_length_and_sha256','medical_review':'unchanged'}
            (stage/'offline-installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            destination=offline/'versions'/installation;destination.parent.mkdir(exist_ok=True)
            if destination.exists():raise ValueError('同一索引已有离线目录，请先检查其安装记录')
            stage.rename(destination)
            pointer=offline/'.current.tmp';pointer.write_text(json.dumps({'directory':'versions/'+installation,'catalog_sha256':identity})+'\n');pointer.replace(offline/'current.json')
            for previous in before['installations']:
                old=Path(previous['location'])
                if old!=destination and old.is_relative_to(offline/'versions'):
                    shutil.rmtree(old)
        return {**inspect(root,cache),'status':'installed'}


def uninstall(root=ROOT,cache=None,expected_revision=None):
    cache=cache_root(cache)
    with locked(cache):
        current=inspect(root,cache)
        if not current['installations']:return {**current,'status':'already_absent'}
        row=current['installations'][0]
        if expected_revision!=row['revision']:raise ValueError('离线安装已变化，请刷新后重试')
        location=Path(row['location'])
        # Only this owner's marked installation; never the source or a project.
        if not location.is_relative_to(cache/'offline/versions'):raise ValueError('离线安装目录越界')
        (cache/'offline/current.json').unlink();shutil.rmtree(location)
        return {**inspect(root,cache),'status':'uninstalled'}


def execute(request,root=ROOT,cache=None,source_root=None):
    if request.get('package_id','mac-media-assets')!='mac-media-assets':raise ValueError('素材库身份不一致')
    operation=request.get('operation','inspect')
    if operation=='inspect':return inspect(root,cache)
    if request.get('profile','offline')!='offline':raise ValueError('未知的素材安装方式')
    if operation in {'install','update'}:
        if request.get('version')!=read(Path(root)/'opl-package.json')['version']:raise ValueError('所选版本已变化')
        return install(root,cache,source_root)
    if operation=='uninstall':return uninstall(root,cache,request.get('expected_revision'))
    raise ValueError('不支持的安装动作')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stdin',action='store_true');parser.add_argument('--operation',default='inspect');parser.add_argument('--source-root',type=Path);parser.add_argument('--cache',type=Path)
    args=parser.parse_args()
    try:
        request=json.load(sys.stdin) if args.stdin else {'operation':args.operation,'version':read(ROOT/'opl-package.json')['version']}
        print(json.dumps(execute(request,cache=args.cache,source_root=args.source_root),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,tarfile.TarError) as error:
        print(json.dumps({'package_id':'mac-media-assets','status':'diagnostic','installations':[], 'error':str(error)},ensure_ascii=False));raise SystemExit(2)
