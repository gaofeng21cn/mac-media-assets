#!/usr/bin/env python3
"""Refresh/check the independent capability's content lock, never creative approval."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def materialize(root=ROOT, check=False):
    manifest_path = root / 'contracts/opl_capability_package_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    paths = sorted(['plugin.json', '.codex-plugin/plugin.json'] +
                   [str(path.relative_to(root)) for folder in
                    ['skills','tools','catalog','collections','schemas','records','payloads','docs']
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
    if check:
        return manifest.get('content_lock') == lock and json.loads((root/'opl-package.json').read_text()) == manifest
    manifest['content_lock'] = lock
    for path in [manifest_path, root/'opl-package.json']:
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    valid = materialize(check=args.check)
    print(json.dumps({'status':'passed' if valid else 'stale', 'creative_approval':False}))
    raise SystemExit(0 if valid else 2)
