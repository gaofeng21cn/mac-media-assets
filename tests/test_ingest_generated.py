"""Exercise generated intake through the real workbench import interface."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

PUBLIC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PUBLIC/'tools'))
from ingest_generated import ingest
from sync_from_workbench import paper_rows
from apply_character_anchors import canonical_revision


class IntakeTests(unittest.TestCase):
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
