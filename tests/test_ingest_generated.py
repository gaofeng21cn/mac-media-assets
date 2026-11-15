"""Exercise generated intake through the real workbench import interface."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import shutil
import io
from unittest.mock import patch
from PIL import Image

PUBLIC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PUBLIC/'tools'))
from ingest_generated import ingest
from sync_from_workbench import paper_rows
from apply_character_anchors import canonical_revision
import optimize_media
from prepare_media import prepare


class IntakeTests(unittest.TestCase):
    def test_intake_use_and_full_export_share_one_lossless_revision_and_keep_the_master(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary); cache = workspace/'cache'
            source = workspace/'source.png'
            image = Image.new('RGBA', (256, 256), (91, 42, 17, 0))
            image.paste((79, 134, 69, 255), (40, 30, 220, 230)); image.save(source)
            original_bytes = source.read_bytes()
            spec = workspace/'spec.json'
            spec.write_text(json.dumps({'id':'new_piece', 'title':'新增纸件', 'source':str(source)}))
            registered = ingest(workspace/'assets/paper-theatre', spec, cache)
            self.assertEqual(registered['registered'][0]['delivery']['status'], 'prepared')
            public = workspace/'public'
            with patch.object(optimize_media, 'encode', side_effect=AssertionError('intake already encoded')):
                rows = paper_rows(workspace, public, cache)
            (public/'catalog').mkdir()
            (public/'catalog/assets.jsonl').write_text(json.dumps(rows[0])+'\n')
            optimize_media.write(public/'catalog/media-storage.json', {'profile':'catalog'})
            for name in ['plugin.json','.codex-plugin/plugin.json','.agents/plugins/marketplace.json','app-contribution-adapter.json']:
                optimize_media.write(public/name, {})
            optimize_media.write(public/'contracts/opl_capability_package_manifest.json', {'version':'1.0.0'})
            with patch.object(optimize_media, 'encode', side_effect=AssertionError('use must reuse encoding')):
                used = prepare(public, rows[0]['id'], cache)
            self.assertEqual(used['row']['id'], registered['registered'][0]['delivery']['asset_id'])
            self.assertTrue(used['record']['entry'].endswith('.webp'))
            entry = next(path for name,path in used['resolved'].items() if name.endswith('/files/payload.webp'))
            self.assertEqual(Image.open(entry).convert('RGBA').tobytes(), image.tobytes())
            full = workspace/'full'; shutil.copytree(public, full)
            with patch.object(optimize_media, 'encode', side_effect=AssertionError('full export must reuse encoding')):
                optimize_media.optimize(full, cache=cache)
            delivered = json.loads((full/'catalog/assets.jsonl').read_text())
            self.assertEqual(delivered['id'], used['row']['id'])
            for part in delivered['payload']:
                self.assertEqual((full/part['path']).read_bytes(), Path(used['resolved'][part['path']]).read_bytes())
            # A slim installation downloads hash-named blobs; it must derive
            # the same formats, filenames and revision as a local full source.
            slim = workspace/'slim'; shutil.copytree(public, slim)
            shutil.rmtree(slim/'payloads')
            optimize_media.write(slim/'catalog/media-storage.json', {
                'source':{'repository':'https://github.com/owner/repo.git', 'revision':'a'*40}})
            bodies = {part['path']:(public/part['path']).read_bytes() for part in rows[0]['payload']}
            with patch('media_store.urlopen', side_effect=lambda url,**kw: io.BytesIO(next(body for name,body in bodies.items() if url.endswith(name)))):
                downloaded = prepare(slim, rows[0]['id'], workspace/'download-cache')
            self.assertEqual(downloaded['row']['id'], used['row']['id'])
            for part in used['row']['payload']:
                self.assertEqual(Path(downloaded['resolved'][part['path']]).read_bytes(), Path(used['resolved'][part['path']]).read_bytes())
            self.assertEqual(source.read_bytes(), original_bytes)
            self.assertEqual((public/rows[0]['payload'][0]['path']).read_bytes(), original_bytes)
            # Current withdrawal also revokes an already prepared cache hit.
            optimize_media.write(public/'collections/curation.json', {'assets':{rows[0]['id']:{'status':'needs_rebuild'}}})
            with self.assertRaisesRegex(ValueError, '撤回'):
                prepare(public, rows[0]['id'], cache)

    def test_relative_source_builds_a_reusable_exact_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace/'intake/piece.png'
            source.parent.mkdir()
            image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            image.paste((40, 80, 60, 255), (4, 3, 12, 14))
            image.save(source)
            registration = {'pivot': {'x': .5, 'y': .5}, 'anchors': {'contact': {'x': .5, 'y': .5}}}
            spec = source.parent/'spec.json'
            spec.write_text(json.dumps({'id':'trial_piece', 'title':'试件',
                'source':'piece.png', 'registration':registration}))
            library = workspace/'assets/paper-theatre'
            value = ingest(library, spec)
            self.assertEqual(value['rejected'], [])
            package = value['registered'][0]
            self.assertTrue(package['record'].startswith('entries/'))
            exported = workspace/'public'
            rows = paper_rows(workspace, exported)
            self.assertEqual(len(rows), 1)
            asset = json.loads((exported/rows[0]['portable_record']).read_text())
            self.assertEqual(canonical_revision(asset), package['revision'])
            self.assertEqual(asset['content_bounds'], [4, 3, 12, 14])
            self.assertEqual(asset['registration'], registration)
            image_ref = next(item for item in rows[0]['payload'] if item['role']=='payload')
            self.assertEqual(hashlib.sha256((exported/image_ref['path']).read_bytes()).digest(),
                             hashlib.sha256(source.read_bytes()).digest())

    def test_default_subject_rejects_opaque_background_and_empty_image(self):
        for color in [(255, 255, 255, 255), (0, 0, 0, 0)]:
            with self.subTest(color=color), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                Image.new('RGBA', (16, 16), color).save(folder/'source.png')
                (folder/'spec.json').write_text('{"id":"piece","title":"试件","source":"source.png"}')
                value = ingest(folder/'library', folder/'spec.json')
                self.assertEqual(value['registered'], [])
                self.assertEqual(len(value['rejected']), 1)


if __name__ == '__main__':
    unittest.main()
