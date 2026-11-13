"""Exercise real encoders, reference rewriting and the existing asset revision contract."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
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
            for name in ['plugin.json','.codex-plugin/plugin.json','.agents/plugins/marketplace.json','app-contribution-adapter.json']:
                optimize_media.write(root/name,{})
            optimize_media.write(root/'contracts/opl_capability_package_manifest.json',{'version':'1.0.0'})
            report=optimize_media.optimize(root,1)
            changed=json.loads((root/'catalog/assets.jsonl').read_text());stored=media_store.read(root/changed['portable_record'])
            self.assertEqual(stored['revision'],optimize_media.canonical(stored))
            self.assertEqual(stored['entry'],'picture.webp')
            self.assertEqual(stored['registration'],record['registration'])
            self.assertEqual(stored['delivery']['source_asset_id'],row['id'])
            entry=root/changed['payload'][0]['path']
            self.assertEqual(Image.open(entry).convert('RGBA').getchannel('A').tobytes(),im.getchannel('A').tobytes())
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

if __name__=='__main__':unittest.main()
