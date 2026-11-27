"""Exercise real encoders, reference rewriting and the existing asset revision contract."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import struct
import wave
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import optimize_media
import media_store
import materialize_package
from PIL import Image

class CompressionTests(unittest.TestCase):
    def test_compressed_record_reconstructs_and_preserves_alpha_references_and_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'stage';root.mkdir();original=root/'payloads/paper-theatre/picture/old';original.mkdir(parents=True)
            im=Image.new('RGBA',(128,128),(180,90,40,160));im.save(original/'picture.png')
            (original/'scene.json').write_text('{"image":"picture.png"}')
            shutil.copy2(original/'picture.png',original/'duplicate.png')
            record={'schema':'animation_element/v1','id':'picture','entry':'picture.png','kind':'image','registration':{'anchor':[.5,1]},'files':[],'revision':'old'}
            for name in ['picture.png','duplicate.png','scene.json']:
                p=original/name;record['files'].append({'path':name,'role':'payload','sha256':media_store.sha(p),'bytes':p.stat().st_size})
            ref='records/paper-theatre/picture/old/record.json';optimize_media.write(root/ref,record)
            row={'id':'paper:picture@old','source_id':'picture','revision':'old','kind':'image','portable_record':ref,'portable_record_sha256':media_store.sha(root/ref),'payload':[{**p,'path':'payloads/paper-theatre/picture/old/'+p['path']} for p in record['files']]}
            (root/'catalog').mkdir();(root/'catalog/assets.jsonl').write_text(json.dumps(row)+'\n')
            optimize_media.write(root/'catalog/media-storage.json',{'profile':'full'})
            optimize_media.write(root/'collections/example.json',{'asset_id':row['id'],'revision':'old','path':row['payload'][0]['path']})
            for name in ['plugin.json','.codex-plugin/plugin.json','.agents/plugins/marketplace.json']:
                optimize_media.write(root/name,{})
            optimize_media.write(root/'opl-package.json',{'schema_version':'opl.package.v2','identity':{
                'id':'mac-media-assets','version':'1.0.0','intent':'extension',
                'name':{'zh-CN':'测试','en-US':'Test'},'summary':{'zh-CN':'测试','en-US':'Test'},
                'publisher':'test'}})
            optimize_media.write(root/'contracts/opl_capability_package_manifest.json',
                                 json.loads((root/'opl-package.json').read_text()))
            report=optimize_media.optimize(root,1)
            changed=json.loads((root/'catalog/assets.jsonl').read_text());stored=media_store.read(root/changed['portable_record'])
            self.assertEqual(stored['revision'],optimize_media.canonical(stored))
            self.assertEqual(stored['entry'],'picture.webp')
            self.assertEqual(stored['registration'],record['registration'])
            self.assertEqual(stored['delivery']['source_asset_id'],row['id'])
            entry=root/changed['payload'][0]['path']
            self.assertEqual(Image.open(entry).convert('RGBA').tobytes(),im.tobytes())
            self.assertEqual(changed['delivery']['encoding_review'], 'lossless_verified')
            scene=next(root/p['path'] for p in changed['payload'] if p['path'].endswith('scene.json'))
            self.assertEqual(json.loads(scene.read_text())['image'],'picture.webp')
            collection=media_store.read(root/'collections/example.json')
            self.assertEqual(collection['asset_id'],changed['id']);self.assertEqual(collection['revision'],changed['revision'])
            self.assertEqual(report['registered_versions'],1)
            duplicate=entry.with_name('duplicate.webp')
            self.assertEqual(entry.stat().st_ino,duplicate.stat().st_ino)
            self.assertLess(report['installed_media_bytes'],report['referenced_media_bytes'])
            self.assertTrue(materialize_package.materialize(root,check=True,profile='full'))

    def test_opaque_character_layer_is_rejected_but_not_treated_as_transparent(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'opaque.png';Image.new('RGBA',(128,128),(230,230,230,255)).save(source)
            item={'path':'opaque.png','bytes':source.stat().st_size,'sha256':media_store.sha(source)}
            with self.assertRaisesRegex(ValueError,'独立运动图层没有透明区域'):
                optimize_media.encode((item,source,False,True),root)

    def test_text_rewrite_handles_relative_module_references(self):
        body='const a="../assets/paper.png"; const b=`assets/paper.png`; // original.png'
        actual=optimize_media.text_references(body,'src/viewer.mjs',{'assets/paper.png':'assets/paper.webp'})
        self.assertIn('"../assets/paper.webp"',actual)
        self.assertIn('`assets/paper.webp`',actual)
        self.assertIn('// original.png',actual)

    def test_cached_encoding_is_exact_for_hidden_rgb_and_icc_and_does_not_reencode(self):
        from PIL import ImageCms
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'image.png'; cache = root/'cache'
            image = Image.new('RGBA', (128, 128), (193, 61, 23, 0))
            image.paste((35, 170, 96, 177), (10, 10, 110, 110))
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
            image.save(source, icc_profile=icc)
            item = {'path':'image.png', 'sha256':media_store.sha(source), 'bytes':source.stat().st_size}
            encoded, detail = optimize_media.encode_cached(item, source, True, cache)
            self.assertEqual(detail['codec'], 'webp_lossless')
            with Image.open(encoded) as actual:
                self.assertEqual(actual.convert('RGBA').tobytes(), image.tobytes())
                self.assertEqual(actual.info['icc_profile'], icc)
            with patch.object(optimize_media, 'run', side_effect=AssertionError('must reuse encoding')):
                again, _ = optimize_media.encode_cached(item, source, True, cache)
            self.assertEqual(again, encoded)
            encoded.chmod(0o644); encoded.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, '缓存字节'):
                optimize_media.encode_cached(item, source, True, cache)

    def test_encoding_cache_is_counted_and_pruned_without_touching_the_master_or_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'image.png'; cache = root/'cache'
            Image.new('RGBA', (128,128), (35,170,96,177)).save(source)
            item = {'path':'image.png', 'sha256':media_store.sha(source), 'bytes':source.stat().st_size}
            encoded, _ = optimize_media.encode_cached(item, source, True, cache)
            project = root/'project.webp'; shutil.copy2(encoded, project)
            original = source.read_bytes(); copied = project.read_bytes()
            self.assertGreater(media_store.cache_status(cache)['encoding_cache_bytes'], 0)
            plan = media_store.prune(cache)
            self.assertGreater(plan['reclaim_encoding_bytes'], 0)
            self.assertTrue(encoded.exists())
            media_store.prune(cache, apply=True)
            self.assertFalse(encoded.exists())
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(project.read_bytes(), copied)

    def test_large_audio_keeps_every_pcm_sample_instead_of_selecting_aac(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'music.wav'
            with wave.open(str(source), 'wb') as audio:
                audio.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
                audio.writeframes(b''.join(struct.pack('<hh', (i % 1000)-500, 500-(i % 1000)) for i in range(144000)))
            item = {'path':'music.wav', 'sha256':media_store.sha(source), 'bytes':source.stat().st_size}
            encoded, detail = optimize_media.encode_cached(item, source, False, root/'cache')
            self.assertEqual(encoded.suffix, '.flac')
            self.assertEqual(detail['codec'], 'flac')
            self.assertEqual(optimize_media.audio_identity(source), optimize_media.audio_identity(encoded))

    def test_png_gamma_is_preserved_by_retaining_the_original(self):
        from PIL.PngImagePlugin import PngInfo
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'gamma.png'
            info = PngInfo(); info.add(b'gAMA', struct.pack('>I', 45455))
            Image.new('RGBA', (32, 32), (40, 30, 20, 200)).save(source, pnginfo=info)
            item = {'path':'gamma.png', 'sha256':media_store.sha(source), 'bytes':source.stat().st_size}
            encoded, detail = optimize_media.encode_cached(item, source, False, root/'cache')
            self.assertEqual(encoded, source)
            self.assertEqual(detail['reason'], 'png_color_metadata')

    def test_stage_cache_cannot_admit_the_same_opaque_image_as_a_movable_layer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'stage.png'
            Image.new('RGBA', (128, 128), (230, 230, 230, 255)).save(source)
            item = {'path':'stage.png', 'sha256':media_store.sha(source), 'bytes':source.stat().st_size}
            optimize_media.encode_cached(item, source, False, root/'cache')
            with self.assertRaisesRegex(ValueError, '独立运动图层没有透明区域'):
                optimize_media.encode_cached(item, source, True, root/'cache')

if __name__=='__main__':unittest.main()
