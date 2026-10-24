"""Reject stale browser evidence before a motion package can be registered."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_structure_schematics

SPEC = importlib.util.spec_from_file_location('motion_package', Path(__file__).resolve().parents[1] / 'tools/motion_package.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MotionPackageTests(unittest.TestCase):
    def test_structure_registration_cannot_overwrite_a_frozen_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'catalog').mkdir()
            (root / 'collections').mkdir()
            (root / 'catalog/assets.jsonl').write_text('')
            (root / 'collections/discovery.json').write_text('{"assets":{}}')
            source = root / 'source.svg'
            source.write_text('<svg/>')
            item = {'id': 'sample', 'label': '样例', 'mode': 'simple', 'bundle': [], 'note': 'test',
                    'files': [{'source': source, 'path': 'source.svg', 'role': 'source'}]}
            first = build_structure_schematics.register([item], root)[0]
            original = (root / first['portable_record']).read_bytes()
            with self.assertRaisesRegex(ValueError, '不可覆盖已有版本'):
                build_structure_schematics.register([item], root)
            self.assertEqual((root / first['portable_record']).read_bytes(), original)

    def test_changed_render_input_cannot_be_frozen(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'samples').mkdir()
            (folder / 'sequence.json').write_text(json.dumps({'images': {}, 'duration': 1, 'fps': 24}))
            for name in ['index.html', 'viewer.mjs', 'runtime.mjs']:
                (folder / name).write_text('current source')
            (folder / 'samples/technical.json').write_text(json.dumps({'inputs': {}, 'status': 'passed'}))
            with self.assertRaisesRegex(ValueError, '实际渲染输入不一致'):
                MODULE.freeze(folder, id='sample', title='样例', root=folder,
                              source_assets={}, discovery={}, tags=[], scope='test', checked=[],
                              defects_found_and_fixed=[], not_reviewed=[], usage_note='')
            self.assertFalse((folder / 'payloads').exists())


if __name__ == '__main__':
    unittest.main()
