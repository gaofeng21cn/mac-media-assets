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
import wave
from concurrent.futures import ThreadPoolExecutor
from media_store import ROOT, cache_root, contained, locked, matches, read, sha

POLICY = 'webp-exact-flac-verified-v2'
TEXT = {'.json', '.yaml', '.yml', '.html', '.js', '.mjs', '.ts', '.css', '.md', '.py', '.txt', '.svg'}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.write-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


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


def png_chunks(source):
    body = source.read_bytes()
    offset = 8
    chunks = {}
    while offset + 12 <= len(body):
        length = struct.unpack('>I', body[offset:offset+4])[0]
        name = body[offset+4:offset+8]
        chunks[name] = body[offset+8:offset+8+length]
        offset += length + 12
    return chunks


def audio_identity(path):
    description = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                                  '-show_entries', 'stream=sample_rate,channels', '-of', 'json', str(path)]).stdout)
    samples = run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path), '-map', '0:a:0',
                   '-c:a', 'pcm_s32le', '-f', 'hash', '-hash', 'sha256', '-']).stdout
    return description['streams'], samples


def encode(job, temporary):
    item, source, _lossless, movable = job
    digest = item['sha256']
    ext = source.suffix.lower()
    destination = temporary / (digest + ('.webp' if ext == '.png' else '.flac'))
    if not matches(source, item):
        raise ValueError('压缩来源已变化：' + item['path'])
    if ext == '.png':
        chunks = png_chunks(source)
        width, height = struct.unpack('>II', chunks[b'IHDR'][:8])
        if chunks[b'IHDR'][8] > 8 or b'acTL' in chunks:
            return digest, source, {'codec': 'original', 'reason': 'bit_depth_or_animation'}
        # WebP carries ICC, EXIF and XMP, but cannot carry PNG gamma/chromaticity.
        if (b'gAMA' in chunks or b'cHRM' in chunks) and b'iCCP' not in chunks:
            return digest, source, {'codec': 'original', 'reason': 'png_color_metadata'}
        run(['cwebp', '-quiet', '-m', '4', '-metadata', 'all', '-lossless', '-exact', '-q', '100',
             str(source), '-o', str(destination)])
        try:
            from PIL import Image
            with Image.open(source) as a, Image.open(destination) as b:
                original, encoded = a.convert('RGBA').tobytes(), b.convert('RGBA').tobytes()
                if a.info.get('icc_profile') != b.info.get('icc_profile'):
                    raise ValueError('颜色配置改变：' + item['path'])
        except ImportError:
            def rgba(path):
                return run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                            '-f', 'rawvideo', '-pix_fmt', 'rgba', '-']).stdout
            original, encoded = rgba(source), rgba(destination)
            if b'iCCP' in chunks:
                return digest, source, {'codec': 'original', 'reason': 'icc_verification_unavailable'}
        if len(original) != width * height * 4 or original != encoded:
            raise ValueError('无损图像像素或Alpha改变：' + item['path'])
        if movable and min(original[3::4]) == 255:
            raise ValueError('独立运动图层没有透明区域，不能把整图背景压缩后当部件：' + item['path'])
        detail = {'codec': 'webp_lossless', 'rgba': 'exact', 'alpha': 'exact',
                  'color_metadata': 'preserved', 'width': width, 'height': height}
    else:
        try:
            with wave.open(str(source), 'rb') as audio:
                if audio.getsampwidth() > 3:
                    return digest, source, {'codec': 'original', 'reason': 'audio_bit_depth'}
        except (wave.Error, EOFError):
            return digest, source, {'codec': 'original', 'reason': 'non_pcm_audio'}
        run(['flac', '-s', '-8', '-V', '--keep-foreign-metadata', '-o', str(destination), str(source)])
        if audio_identity(source) != audio_identity(destination):
            raise ValueError('无损音频采样或声道改变：' + item['path'])
        detail = {'codec': 'flac', 'sample_verification': 'decoded_pcm_sha256_rate_channels'}
    if destination.stat().st_size >= item['bytes']:
        return digest, source, {'codec': 'original', 'reason': 'compression_not_smaller'}
    return digest, destination, detail


def encode_cached(item, source, movable=False, cache=None):
    """One verified encoding per source hash and policy, shared by every consumer."""
    if not matches(source, item):
        raise ValueError('压缩来源已变化：' + item['path'])
    directory = cache_root(cache) / 'encodings' / POLICY / item['sha256']
    with locked(directory):
        receipt_path = directory / 'receipt.json'
        if receipt_path.is_file():
            receipt = read(receipt_path)
            if receipt['detail'].get('codec') == 'original':
                result = source
            else:
                result = contained(directory, receipt['output']['path'])
                if not matches(result, receipt['output']):
                    raise ValueError('无损使用版缓存字节已变化：' + item['path'])
            if movable and receipt['detail'].get('alpha_min') == 255:
                raise ValueError('独立运动图层没有透明区域：' + item['path'])
            return result, receipt['detail']
        require_encoders()
        with tempfile.TemporaryDirectory(prefix='.encode-', dir=directory) as folder:
            _, output, detail = encode((item, source, True, movable), Path(folder))
            # Admission is per use; a stage and a movable layer may share pixels.
            if source.suffix.lower() == '.png':
                try:
                    from PIL import Image
                    with Image.open(source) as image:
                        detail['alpha_min'] = image.convert('RGBA').getchannel('A').getextrema()[0]
                except ImportError:
                    detail['alpha_min'] = min(run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(source),
                                                  '-f', 'rawvideo', '-pix_fmt', 'rgba', '-']).stdout[3::4])
                if movable and detail['alpha_min'] == 255:
                    raise ValueError('独立运动图层没有透明区域：' + item['path'])
            descriptor = None
            result = source
            if output != source:
                result = directory / output.name
                output.replace(result)
                result.chmod(0o444)
                descriptor = {'path': result.name, 'sha256': sha(result), 'bytes': result.stat().st_size}
            write(receipt_path, {'output': descriptor, 'detail': detail})
            return result, detail


def prepare_asset(root, row, cache=None, resolved=None, *, validate_movable=True):
    """Derive a revision without changing its source; used by intake, use and export."""
    root = Path(root)
    record_path = contained(root, row['portable_record'])
    if row.get('portable_record_sha256') and sha(record_path) != row['portable_record_sha256']:
        raise ValueError('资产原记录字节已变化')
    record = read(record_path)
    if record['id'] != row['source_id'] or record['revision'] != row['revision']:
        raise ValueError('资产原记录身份不一致')
    resolved = resolved or {}
    mapping, sources, details, hashes = {}, {}, [], {}
    category = row.get('discovery', {}).get('category')
    layers = record.get('asset_bundle') or [record.get('asset') or {'path': record.get('entry')}]
    movable_paths = {part.get('path') for part in layers} if row['kind'] in {'image', 'transparent_subject', 'medical_cutout'} and category not in {'stage', 'environment'} else set()
    for part in record['files']:
        suffix = '/' + row['source_id'] + '/' + row['revision'] + '/' + part['path']
        payloads = [p for p in row['payload'] if p['path'].endswith(suffix)]
        if len(payloads) != 1 or payloads[0]['sha256'] != part['sha256'] or payloads[0]['bytes'] != part['bytes']:
            raise ValueError('缺少精确载荷映射：' + part['path'])
        payload = payloads[0]
        source = Path(resolved[payload['path']]) if payload['path'] in resolved else contained(root, payload['path'])
        if not matches(source, part):
            raise ValueError('素材源文件字节已变化：' + part['path'])
        # Hash-addressed downloads have no suffix. Give the encoder its real format.
        output, detail = source, {'codec': 'original'}
        if part.get('role') != 'evidence' and Path(part['path']).suffix.lower() in {'.png', '.wav'}:
            movable = validate_movable and (part['path'] in movable_paths or (row['kind'] == 'motion_recipe' and part['path'].startswith(('assets/', 'original/files/'))))
            if source.suffix.lower() != Path(part['path']).suffix.lower():
                with tempfile.TemporaryDirectory(prefix='mac-encode-input-') as folder:
                    named = Path(folder) / Path(part['path']).name
                    try:
                        os.link(source, named)
                    except OSError:
                        shutil.copy2(source, named)
                    output, detail = encode_cached(part, named, movable, cache)
                    if output == named:
                        output = source
            else:
                output, detail = encode_cached(part, source, movable, cache)
        target = str(Path(part['path']).with_suffix(output.suffix)) if output != source else part['path']
        mapping[part['path']] = target
        sources[part['path']] = output
        if output != source:
            details.append({'path': part['path'], 'encoded_path': target, 'source_sha256': part['sha256'], **detail})
            hashes[part['sha256']] = sha(output)
    new_record = rewrite(copy.deepcopy(record), {**mapping, **hashes})
    if 'source' in record:
        new_record['source'] = copy.deepcopy(record['source'])
    files, resolved_outputs = [], {}
    for part in record['files']:
        source = sources[part['path']]
        target = mapping[part['path']]
        if Path(part['path']).suffix.lower() in TEXT and part.get('role') != 'evidence':
            body = source.read_text()
            if Path(part['path']).suffix.lower() == '.json':
                updated = json.dumps(rewrite(json.loads(body), {**mapping, **hashes}), ensure_ascii=False, indent=2) + '\n'
            else:
                updated = text_references(body, part['path'], {**mapping, **hashes})
            # Avoid creating a new revision just for JSON whitespace.
            if updated != body and (Path(part['path']).suffix.lower() != '.json' or json.loads(updated) != json.loads(body)):
                digest = hashlib.sha256(updated.encode()).hexdigest()
                directory = cache_root(cache) / 'encodings' / POLICY / 'text'
                with locked(directory):
                    source = directory / (digest + Path(part['path']).suffix)
                    if not source.exists():
                        source.write_text(updated)
                        source.chmod(0o444)
                    if sha(source) != digest:
                        raise ValueError('使用版代码缓存字节已变化')
        descriptor = {'path': target, 'role': part.get('role', 'payload'), 'sha256': sha(source), 'bytes': source.stat().st_size}
        files.append(descriptor)
        resolved_outputs[target] = str(source)
        if descriptor['sha256'] != part['sha256']:
            hashes[part['sha256']] = descriptor['sha256']
    new_record['files'] = files
    # Geometry remains valid after exact pixel preservation, while its checksum
    # must name the bytes actually consumed by the project.
    for owner in [new_record, new_record.get('asset') or {}, *new_record.get('asset_bundle', [])]:
        if owner.get('human_scale'):
            owner['human_scale'] = rewrite(owner['human_scale'], hashes)
    if files != record['files']:
        new_record['delivery'] = {'policy': POLICY, 'source_asset_id': row['id'],
                                  'source_record_sha256': row['portable_record_sha256'], 'encodings': details}
        new_record['revision'] = canonical(new_record)
    new_id = 'paper:' + row['source_id'] + '@' + new_record['revision']
    prefix = 'payloads/paper-theatre/' + row['source_id'] + '/' + new_record['revision']
    result = {**row, 'id': new_id, 'revision': new_record['revision'],
              'portable_record': 'records/paper-theatre/' + row['source_id'] + '/' + new_record['revision'] + '/record.json',
              'portable_record_sha256': hashlib.sha256((json.dumps(new_record, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest(),
              'payload': [{**part, 'path': prefix + '/' + part['path']} for part in files]}
    if files != record['files']:
        result['delivery'] = {'policy': POLICY, 'source_asset_id': row['id'], 'encoding_review': 'lossless_verified'}
    return {'row': result, 'record': new_record,
            'resolved': {prefix + '/' + path: source for path, source in resolved_outputs.items()},
            'path_map': mapping, 'hash_map': hashes}


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


def optimize(root=ROOT, jobs=4, cache=None):
    """Mutate only a staged standalone full export, never the source repository."""
    root=Path(root).resolve()
    if (root/'.git').exists():raise ValueError('压缩只写独立导出目录，不重写源码原件')
    rows=[json.loads(s) for s in (root/'catalog/assets.jsonl').read_text().splitlines() if s.strip()]
    original_catalog=sha(root/'catalog/assets.jsonl')
    spec=read(root/'catalog/media-storage.json')
    existing_aliases = read(root/'catalog/delivery-report.json').get('aliases', {}) if (root/'catalog/delivery-report.json').is_file() else {}
    if spec.get('delivery_policy')==POLICY:return read(root/'catalog/delivery-report.json')
    parts={p['path']:p for row in rows for p in row['payload']}
    id_map = {}; revision_map = {}; path_map = {}; hash_map = {}; new_rows = []
    encoded_files = {}
    with tempfile.TemporaryDirectory(prefix='.delivery-', dir=root.parent) as folder:
        temp = Path(folder)
        def prepare(row):
            return prepare_asset(root, row, cache)
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            prepared = list(executor.map(prepare, rows))
        for row, value in zip(rows, prepared):
            new_record = value['record']; result = value['row']
            record_ref = result['portable_record']
            write(root / record_ref, new_record)
            result['portable_record_sha256'] = sha(root / record_ref)
            for part in result['payload']:
                target = temp / part['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(value['resolved'][part['path']], target)
            new_rows.append(result)
            id_map[row['id']] = result['id']; revision_map[row['revision']] = result['revision']
            path_map[row['portable_record']] = record_ref
            prefix = 'payloads/paper-theatre/' + row['source_id'] + '/' + row['revision'] + '/'
            new_prefix = 'payloads/paper-theatre/' + row['source_id'] + '/' + result['revision'] + '/'
            for old in row['payload']:
                path_map[old['path']] = new_prefix + value['path_map'][old['path'].removeprefix(prefix)]
            hash_map.update(value['hash_map'])
            for detail in new_record.get('delivery', {}).get('encodings', []):
                encoded_files[detail['source_sha256']] = detail
        shutil.rmtree(root / 'payloads')
        (temp / 'payloads').rename(root / 'payloads')
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
            'registered_versions':len(new_rows),'encoded_unique_files':len(encoded_files),
            'codecs':{codec:sum(info['codec']==codec for info in encoded_files.values()) for codec in sorted({info['codec'] for info in encoded_files.values()})},
            'semantic_review':'current_shot_required','aliases':{**{old:id_map.get(current,current) for old,current in existing_aliases.items()},**id_map}}
    write(root/'catalog/delivery-report.json',report)
    from materialize_package import materialize
    materialize(root,profile='full')
    return report


def require_encoders():
    missing=[name for name in ('cwebp','ffmpeg','ffprobe','flac') if not shutil.which(name)]
    if missing:raise ValueError('从原件构建压缩包需要 '+', '.join(missing)+'；可直接安装已预构建的完整版，无需本机转码')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--export',type=Path,required=True);parser.add_argument('--jobs',type=int,default=4);parser.add_argument('--archive',type=Path);parser.add_argument('--cache',type=Path)
    args=parser.parse_args()
    from materialize_package import export
    export(args.root,args.export,'full',cache=args.cache)
    result=optimize(args.export,max(1,min(args.jobs,8)),args.cache)
    if args.archive:
        if args.archive.exists():raise ValueError('压缩包目标已存在，保留现有文件')
        with tarfile.open(args.archive,'w:gz',compresslevel=6) as archive:
            archive.add(args.export,arcname='mac-media-assets')
        result={**result,'archive':str(args.archive),'archive_bytes':args.archive.stat().st_size,'archive_sha256':sha(args.archive)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
