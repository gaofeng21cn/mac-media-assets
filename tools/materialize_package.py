#!/usr/bin/env python3
"""Refresh/check the independent capability's content lock, never creative approval."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def verify_remote_source(root, rows, spec):
    """A slim build may omit media only when its pinned Git tree owns the bytes."""
    from media_store import contained, source_url
    remote = {item['path']: item for row in rows
              if row['source_id'] not in spec.get('bundled_source_ids', [])
              for item in row['payload']}
    if not remote:
        return
    source_url(spec, next(iter(remote.values())))
    if not (root/'.git').exists():
        return  # Installed directory: its Framework content lock owns the index.
    completed = subprocess.run(['git', '-C', str(root), 'ls-tree', '-rlz', spec['source']['revision']],
                               capture_output=True, check=True)
    tree = {}
    for value in completed.stdout.split(b'\0'):
        if not value:
            continue
        header, path = value.split(b'\t', 1)
        mode, kind, oid, size = header.split()
        if kind == b'blob':
            tree[path.decode()] = (oid.decode(), int(size))
    for name, item in remote.items():
        if name not in tree or tree[name][1] != item['bytes']:
            raise ValueError('远端固定提交尚不包含媒体；先发布来源或将小文件随包：' + name)
        path = contained(root, name)
        if path.is_file():
            git_hash = hashlib.sha1(('blob '+str(item['bytes'])+'\0').encode())
            content_hash = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024*1024), b''):
                    git_hash.update(block); content_hash.update(block)
            if git_hash.hexdigest() != tree[name][0] or content_hash.hexdigest() != item['sha256']:
                raise ValueError('固定来源与登记媒体字节不一致：' + name)


def build_manifest(root=ROOT, profile='catalog'):
    manifest_path = root / 'contracts/opl_capability_package_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    spec = json.loads((root / 'catalog/media-storage.json').read_text()) if (root / 'catalog/media-storage.json').is_file() else {}
    bundled = set(spec.get('bundled_source_ids', []))
    rows = [json.loads(line) for line in (root/'catalog/assets.jsonl').read_text().splitlines() if line.strip()]
    if profile == 'catalog':
        verify_remote_source(root, rows, spec)
    payload_paths = []
    if profile == 'full':
        payload_paths = sorted({part['path'] for row in rows for part in row['payload']})
    else:
        payload_paths = sorted({part['path'] for row in rows if row['source_id'] in bundled for part in row['payload']})
    record_paths = sorted({row['portable_record'] for row in rows})
    paths = sorted(['plugin.json', '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json', 'app-contribution-adapter.json'] + payload_paths + record_paths +
                   [str(path.relative_to(root)) for folder in
                    ['skills','tools','catalog','collections','schemas','docs']
                    for path in (root/folder).rglob('*') if path.is_file() and '__pycache__' not in path.parts])
    digest = hashlib.sha256()
    for relative in paths:
        encoded = relative.encode()
        body = (root/relative).read_bytes()
        digest.update(len(encoded).to_bytes(8,'big'))
        digest.update(encoded)
        digest.update(len(body).to_bytes(8,'big'))
        digest.update(body)
    lock = {'algorithm':'sha256','canonicalization':'ordered_path_length_file_length_bytes',
            'paths':paths,'digest':'sha256:'+digest.hexdigest()}
    manifest['content_lock'] = lock
    return manifest


def materialize(root=ROOT, check=False, profile='catalog'):
    manifest_path = root / 'contracts/opl_capability_package_manifest.json'
    manifest = build_manifest(root, profile)
    if check:
        return json.loads(manifest_path.read_text()) == manifest and json.loads((root/'opl-package.json').read_text()) == manifest
    for path in [manifest_path, root/'opl-package.json']:
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return True


def export(root, destination, profile='catalog'):
    """Stage the existing OPL descriptor's exact files; this is not a publisher."""
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(root.resolve()):
        raise ValueError('导出目标须是库外尚不存在的目录')
    manifest = build_manifest(root, profile)
    paths = manifest['content_lock']['paths'] + ['opl-package.json', 'contracts/opl_capability_package_manifest.json']
    for optional in ['README.md', 'README.en.md', 'LICENSE', 'NOTICE']:
        if (root/optional).is_file():
            paths.append(optional)
    for value in paths:
        target = destination/value
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/value, target)
    if profile == 'full':
        storage = json.loads((destination/'catalog/media-storage.json').read_text())
        storage['profile'] = 'full'
        (destination/'catalog/media-storage.json').write_text(json.dumps(storage,ensure_ascii=False,indent=2)+'\n')
        materialize(destination,profile='full')
        if storage.get('offline_media_optimization') and not storage.get('delivery_policy'):
            from optimize_media import optimize
            optimize(destination)
    else:
        for name in ['opl-package.json','contracts/opl_capability_package_manifest.json']:
            (destination/name).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    actual=[p for p in destination.rglob('*') if p.is_file()]
    unique={(p.stat().st_dev,p.stat().st_ino):p for p in actual}
    return {'directory': str(destination), 'files': len(actual),
            'bytes':sum(p.stat().st_size for p in unique.values()),
            'referenced_file_bytes':sum(p.stat().st_size for p in actual)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--profile', choices=['catalog', 'full'], default='catalog')
    parser.add_argument('--export', type=Path)
    args = parser.parse_args()
    if args.profile == 'full' and not args.export:
        parser.error('完整版使用 --profile full --export <新目录>，保留源码的默认轻量内容锁')
    valid = materialize(check=args.check) if args.profile == 'catalog' else True
    result = {'status':'passed' if valid else 'stale', 'creative_approval':False, 'profile': args.profile}
    if args.export and valid:
        result['export'] = export(ROOT, args.export, args.profile)
    print(json.dumps(result))
    raise SystemExit(0 if valid else 2)
