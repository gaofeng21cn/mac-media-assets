#!/usr/bin/env python3
"""Prepare or check the asset package and its offline export."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from media_store import ROOT, contained, read, storage
from query_assets import all_catalog_rows

PACKAGE_MANIFEST = 'opl-package.json'
MANIFEST_COPY = 'contracts/opl_capability_package_manifest.json'
OFFLINE_DIGEST = 'contracts/offline-content.json'


def read_package_manifest(root):
    manifest = read(Path(root) / PACKAGE_MANIFEST)
    if (manifest.get('schema_version') != 'opl.package.v2'
            or manifest.get('identity', {}).get('id') != 'mac-media-assets'
            or not manifest['identity'].get('version')):
        raise ValueError('素材包必须使用 opl.package.v2，且包含素材库身份和版本')
    return manifest


def verify_remote_source(root, rows, spec):
    """A slim build may omit media only when its pinned Git tree owns the bytes."""
    from media_store import source_url
    remote = {item['path']: item for row in rows
              if row['source_id'] not in spec.get('bundled_source_ids', [])
              for item in row['payload']}
    if not remote:
        return
    from media_store import locate
    object_items = {name:item for name,item in remote.items() if item.get('storage') == 'object'}
    for name,item in object_items.items():
        if locate(root,item) is None:
            source_url(spec,item)
    remote = {name:item for name,item in remote.items() if item.get('storage') != 'object'}
    if not remote:
        return
    source_url(spec, next(iter(remote.values())))
    if not (root/'.git').exists():
        return  # Installed directory: no local Git tree to inspect.
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


def collection_docs_evidence_refs(root):
    refs = set()
    collections_dir = root / 'collections'
    if not collections_dir.is_dir():
        return refs

    def walk(node):
        if isinstance(node, dict):
            ref = node.get('evidence_ref')
            if isinstance(ref, str):
                rel = ref.split('#', 1)[0]
                if rel.startswith('docs/'):
                    refs.add(rel)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in collections_dir.glob('*.json'):
        try:
            walk(json.loads(path.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            continue
    return refs


def package_paths(root=ROOT, profile='catalog', rows=None):
    """List files belonging to the selected asset package profile."""
    root = Path(root)
    bundled = set(storage(root).get('bundled_source_ids', []))
    if rows is None:
        rows = all_catalog_rows(root)
    paths = {PACKAGE_MANIFEST, 'plugin.json', '.codex-plugin/plugin.json',
             '.agents/plugins/marketplace.json', 'catalog/assets.jsonl'}
    paths.update(row['portable_record'] for row in rows)
    paths.update(part['path'] for row in rows if profile == 'full' or row['source_id'] in bundled
                 for part in row['payload'])
    evidence_refs = collection_docs_evidence_refs(root)
    icon = read(root / PACKAGE_MANIFEST)['identity'].get('icon')
    if icon:
        paths.add(icon.removeprefix('./'))
    paths.update(
        str(path.relative_to(root))
        for folder in ['skills', 'tools', 'catalog', 'collections', 'schemas']
        for path in (root / folder).rglob('*')
        if path.is_file() and '__pycache__' not in path.parts
        and path.name != '.DS_Store' and path.suffix != '.pyc'
    )
    paths.update(
        str(path.relative_to(root))
        for path in (root / 'docs').rglob('*')
        if path.is_file()
        and (path.suffix == '.md' or str(path.relative_to(root)) in evidence_refs)
    )
    return sorted(paths)


def content_digest(root, paths):
    """Fingerprint the package paths and their bytes."""
    digest = hashlib.sha256()
    for name in paths:
        encoded = name.encode('utf-8')
        with contained(root, name).open('rb') as source:
            digest.update(len(encoded).to_bytes(8, 'big'))
            digest.update(encoded)
            digest.update(source.seek(0, 2).to_bytes(8, 'big'))
            source.seek(0)
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
    return 'sha256:' + digest.hexdigest()


def materialize(root=ROOT, check=False, profile='catalog'):
    root = Path(root)
    manifest = read_package_manifest(root)
    if profile == 'catalog' and (root/'.git').exists():
        from repository_media import audit, reconcile
        result = audit(root) if check else reconcile(root)
        if result.get('errors'):
            if check:
                return False
            raise ValueError('仓库媒体处理未完成：' + '; '.join(result['errors']))
    rows = all_catalog_rows(root)
    paths = package_paths(root, profile, rows)
    if profile == 'catalog':
        verify_remote_source(root, rows, storage(root))
    missing = [name for name in paths if not contained(root, name).is_file()]
    if missing:
        if check:
            return False
        raise ValueError('包缺少文件：' + ', '.join(missing))
    manifest_path = root / MANIFEST_COPY
    digest_path = root / OFFLINE_DIGEST
    if check:
        if not manifest_path.is_file() or read(manifest_path) != manifest:
            return False
        return profile != 'full' or (
            digest_path.is_file()
            and read(digest_path) == {'digest': content_digest(root, paths)}
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / PACKAGE_MANIFEST, manifest_path)
    if profile == 'full':
        digest_path.write_text(json.dumps({'digest': content_digest(root, paths)}) + '\n', encoding='utf-8')
    return True


def export(root, destination, profile='catalog', cache=None):
    """Stage the existing OPL descriptor's exact files; this is not a publisher."""
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(root.resolve()):
        raise ValueError('导出目标须是库外尚不存在的目录')
    if (root/'.git').exists():
        materialize(root)
    rows = all_catalog_rows(root)
    paths = package_paths(root, profile, rows)
    parts = {part['path']: part for row in rows for part in row['payload']}
    for optional in ['README.md', 'README.en.md', 'LICENSE', 'NOTICE']:
        if (root/optional).is_file():
            paths.append(optional)
    for value in paths:
        target = contained(destination, value)
        target.parent.mkdir(parents=True, exist_ok=True)
        source = contained(root, value)
        if not source.is_file():
            from media_store import locate
            part = parts.get(value)
            source = locate(root, part, cache) if part else None
            if source is None:
                raise ValueError('导出缺少已登记媒体：' + value)
        shutil.copy2(source, target)
    if profile == 'full':
        spec = storage(destination)
        spec['profile'] = 'full'
        (destination/'catalog/media-storage.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
        materialize(destination,profile='full')
        if spec.get('offline_media_optimization') and not spec.get('delivery_policy'):
            from optimize_media import optimize
            optimize(destination, cache=cache)
    else:
        materialize(destination)
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
        parser.error('完整版使用 --profile full --export <新目录>')
    valid = materialize(check=args.check) if args.profile == 'catalog' else True
    result = {'status':'passed' if valid else 'stale', 'creative_approval':False, 'profile': args.profile}
    if args.export and valid:
        result['export'] = export(ROOT, args.export, args.profile)
    print(json.dumps(result))
    raise SystemExit(0 if valid else 2)
