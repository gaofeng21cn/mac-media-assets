#!/usr/bin/env python3
"""Exact-byte media retrieval. Discovery is offline; only fetch writes the cache.

The installed package contains records and tools. Original media stay at a
pinned source commit, or in a user-supplied full library. Project imports copy
bytes out of this disposable cache and remain independent of cache eviction.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import time
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def relative(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or '\\' in value or p.as_posix() != value:
        raise ValueError('媒体路径必须是库内规范相对路径')
    return value


def contained(root, value):
    path = Path(root) / relative(value)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('媒体路径越出库或缓存')
    return path


def cache_root(value=None):
    return Path(value or os.environ.get('MAC_MEDIA_CACHE') or
                Path.home() / '.cache/mac-media-assets').expanduser().resolve()


def storage(root=ROOT):
    path = Path(root) / 'catalog/media-storage.json'
    return read(path) if path.is_file() else {}


def blob(cache, item):
    digest = item['sha256']
    if not re.fullmatch('[a-f0-9]{64}', digest) or not isinstance(item['bytes'], int) or item['bytes'] < 0:
        raise ValueError('无效的媒体字节描述')
    return cache / 'blobs' / digest[:2] / digest


def matches(path, item):
    return path.is_file() and path.stat().st_size == item['bytes'] and sha(path) == item['sha256']


def locate(root, item, cache=None, *, verify=True):
    """Read-only: never creates a directory, downloads, or rewrites a package."""
    local = contained(root, item['path'])
    if local.is_file():
        if verify and not matches(local, item):
            raise ValueError('原件字节与所选版本不一致：' + item['path'])
        return local
    offline_pointer = cache_root(cache) / 'offline/current.json'
    if offline_pointer.is_file():
        offline = read(offline_pointer)
        directory = contained(cache_root(cache) / 'offline', offline['directory'])
        original = contained(directory, item['path'])
        if original.is_file():
            if verify and not matches(original, item):
                raise ValueError('离线安装字节与所选版本不一致：' + item['path'])
            return original
    cached = blob(cache_root(cache), item)
    if cached.is_file():
        if verify and not matches(cached, item):
            raise ValueError('缓存字节与所选版本不一致：' + item['path'])
        return cached
    return None


def select(root=ROOT, identifiers=None, **facets):
    from query_assets import query
    if identifiers:
        rows = []
        for identifier in identifiers:
            found = query(root, asset_id=identifier)
            if not found:
                raise ValueError('素材不存在或已撤回：' + identifier)
            rows.extend(found)
        return list({row['id']: row for row in rows}.values())
    return query(root, **facets)


def plan(root, rows, cache=None):
    cache = cache_root(cache)
    seen, needed = {}, {}
    files = []
    for row in rows:
        for item in row.get('payload', []):
            path = locate(root, item, cache)
            seen[item['sha256']] = item
            if path is None:
                needed[item['sha256']] = item
            files.append({'asset_id': row['id'], **item, 'available': path is not None,
                          'resolved_path': str(path) if path else None})
    return {'schema': 'mac_media_plan/v1', 'read_only': True,
            'asset_ids': [row['id'] for row in rows], 'files': files,
            'logical_bytes': sum(x['bytes'] for x in files),
            'unique_bytes': sum(x['bytes'] for x in seen.values()),
            'download_bytes': sum(x['bytes'] for x in needed.values()),
            'cache': str(cache)}


@contextmanager
def locked(cache):
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / '.lock').open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0); handle.write(b'0'); handle.flush(); handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def source_url(spec, item):
    source = spec.get('source', {})
    repo, revision = source.get('repository', ''), source.get('revision', '')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git', repo) or not re.fullmatch('[a-f0-9]{40}', revision):
        raise ValueError('媒体来源需要公开仓库与完整不可变提交')
    slug = repo.removeprefix('https://github.com/').removesuffix('.git')
    return 'https://raw.githubusercontent.com/' + slug + '/' + revision + '/' + quote(relative(item['path']), safe='/')


def cache_status(cache=None):
    cache = cache_root(cache)
    objects = list((cache / 'blobs').glob('*/*')) if cache.exists() else []
    snapshots = list((cache / 'snapshots').glob('*/receipt.json')) if cache.exists() else []
    offline = None
    pointer = cache / 'offline/current.json'
    if pointer.is_file():
        directory = contained(cache / 'offline', read(pointer)['directory'])
        marker = directory / 'offline-installation.json'
        if marker.is_file():
            receipt = read(marker)
            offline = {'directory': str(directory), 'installed_media_bytes': receipt.get('physical_media_bytes',receipt['size_bytes']),
                       'referenced_media_bytes':receipt['size_bytes'],
                       'file_count': receipt['file_count'], 'prunable': False}
    return {'root': str(cache), 'bytes': sum(p.stat().st_size for p in objects if p.is_file()),
            'blobs': len(objects), 'snapshots': len(snapshots),
            'offline_installation': offline,
            'pinned_snapshots': sum(bool(read(p).get('pinned')) for p in snapshots)}


def fetch(root, rows, cache=None, *, offline=False, source_root=None, pin=False, max_bytes=None):
    root, cache = Path(root).resolve(), cache_root(cache)
    # Re-read current exact-version decisions even for programmatic callers.
    rows = select(root, [row['id'] for row in rows]) if rows else []
    spec = storage(root)
    with locked(cache):
        pending = plan(root, rows, cache)
        limit = max_bytes if max_bytes is not None else spec.get('cache_limit_bytes', 2 * 1024**3)
        if cache_status(cache)['bytes'] + pending['download_bytes'] > limit:
            raise ValueError('共享缓存预算不足；可先预览 cache-prune 或提高 cache_limit_bytes')
        resolved = {}
        for item in pending['files']:
            found = locate(root, item, cache)
            if found is None:
                target = blob(cache, item)
                target.parent.mkdir(parents=True, exist_ok=True)
                if offline and source_root is None:
                    raise FileNotFoundError('离线缓存缺少所选媒体：' + item['path'])
                with tempfile.NamedTemporaryFile(prefix='.download-', dir=target.parent, delete=False) as output:
                    temporary = Path(output.name)
                    try:
                        if source_root is not None:
                            incoming = contained(source_root, item['path']).open('rb')
                        else:
                            incoming = urlopen(source_url(spec, item), timeout=30)
                        with incoming:
                            size = 0
                            while True:
                                block = incoming.read(min(1024 * 1024, item['bytes'] - size + 1))
                                if not block:
                                    break
                                size += len(block)
                                if size > item['bytes']:
                                    raise ValueError('下载超过已登记的文件长度')
                                output.write(block)
                        output.flush()
                        if not matches(temporary, item):
                            raise ValueError('下载字节或哈希与所选精确版本不一致')
                        temporary.chmod(0o444)
                        os.replace(temporary, target)
                    finally:
                        temporary.unlink(missing_ok=True)
                found = target
            resolved[item['path']] = found
        # A complete, disposable relative-path view for HTML/motion previews.
        snapshot_key = hashlib.sha256(json.dumps(sorted(pending['asset_ids'])).encode()).hexdigest()
        snapshot = cache / 'snapshots' / snapshot_key
        snapshot.mkdir(parents=True, exist_ok=True)
        for value, original in resolved.items():
            destination = snapshot / relative(value)
            if not destination.parent.resolve().is_relative_to(snapshot.resolve()):
                raise ValueError('缓存快照的父目录越界')
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_symlink() and destination.resolve() != original.resolve():
                raise ValueError('缓存快照指向了其他文件')
            if not destination.exists():
                try:
                    destination.symlink_to(os.path.relpath(original, destination.parent))
                except OSError:
                    shutil.copy2(original, destination)
        receipt_path = snapshot / 'receipt.json'
        previous = read(receipt_path) if receipt_path.is_file() else {}
        receipt = {'asset_ids': pending['asset_ids'], 'last_used': time.time(),
                   'pinned': pin or previous.get('pinned', False),
                   'blobs': sorted({item['sha256'] for item in pending['files']
                                    if resolved[item['path']].is_relative_to(cache / 'blobs')})}
        staged_receipt = snapshot / '.receipt.tmp'
        staged_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        staged_receipt.replace(receipt_path)
        return {**pending, 'read_only': False, 'status': 'available',
                'snapshot': str(snapshot), 'resolved': {k: str(v) for k, v in resolved.items()}}


def prune(cache=None, target_bytes=0, *, apply=False):
    """Remove only unpinned, disposable media cache; project copies are outside it."""
    cache = cache_root(cache)
    def decide():
        receipts = {p.parent: read(p) for p in (cache / 'snapshots').glob('*/receipt.json')}
        objects = {p.name: p for p in (cache / 'blobs').glob('*/*') if p.is_file()}
        sizes = {k: p.stat().st_size for k, p in objects.items()}
        retained = dict(receipts)
        removed = []
        def live():
            return {digest for item in retained.values() for digest in item['blobs']}
        for folder, receipt in sorted(receipts.items(), key=lambda pair: pair[1]['last_used']):
            if sum(sizes.get(k, 0) for k in live()) <= target_bytes:
                break
            if not receipt.get('pinned'):
                removed.append(folder); retained.pop(folder)
        dead = [p for digest, p in objects.items() if digest not in live()]
        result = {'read_only': not apply, 'removed_snapshots': [str(p) for p in removed],
                  'reclaim_bytes': sum(p.stat().st_size for p in dead),
                  'retained_bytes': sum(sizes.get(k, 0) for k in live()),
                  'target_bytes': target_bytes, 'pinned_snapshots': sum(bool(v.get('pinned')) for v in retained.values())}
        if apply:
            for folder in removed:
                shutil.rmtree(folder)
            for path in dead:
                path.unlink()
        return result
    if apply:
        with locked(cache):
            return decide()
    return decide()


def audit(root=ROOT):
    from query_assets import all_catalog_rows, query
    rows, current = all_catalog_rows(root), query(root)
    parts = [item for row in rows for item in row['payload']]
    unique = {item['sha256']: item for item in parts}
    suffixes = {}
    for item in parts:
        ext = Path(item['path']).suffix
        suffixes[ext] = suffixes.get(ext, 0) + item['bytes']
    return {'read_only': True, 'registered_versions': len(rows), 'current_candidates': len(current),
            'logical_bytes': sum(x['bytes'] for x in parts),
            'unique_bytes': sum(x['bytes'] for x in unique.values()),
            'current_logical_bytes': sum(x['bytes'] for row in current for x in row['payload']),
            'bytes_by_extension': dict(sorted(suffixes.items(), key=lambda x: -x[1]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['audit', 'plan', 'fetch', 'cache-status', 'cache-prune'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--id', action='append')
    parser.add_argument('--category')
    parser.add_argument('--query')
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--pin', action='store_true')
    parser.add_argument('--max-bytes', type=int)
    parser.add_argument('--target-bytes', type=int, default=0)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'audit':
            result = audit(args.root)
        elif args.command == 'cache-status':
            result = cache_status(args.cache)
        elif args.command == 'cache-prune':
            result = prune(args.cache, args.target_bytes, apply=args.apply)
        else:
            if args.command == 'fetch' and not (args.id or args.category or args.query):
                parser.error('fetch 需要精确素材、分类或查询条件；不会默认下载全库')
            rows = select(args.root, args.id, category=args.category, text=args.query)
            result = plan(args.root, rows, args.cache) if args.command == 'plan' else fetch(
                args.root, rows, args.cache, offline=args.offline, source_root=args.source_root,
                pin=args.pin, max_bytes=args.max_bytes)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'status': 'diagnostic', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
