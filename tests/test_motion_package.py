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
                              source_assets={}, discovery={}, tags=[], scope='test', review_targets=[],
                              preparation_notes=[], not_reviewed=[], usage_note='')
            self.assertFalse((folder / 'payloads').exists())

    def test_render_success_alone_creates_pending_candidate(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / 'study'
            (folder / 'samples').mkdir(parents=True)
            (root / 'catalog').mkdir()
            (root / 'catalog/assets.jsonl').write_text('')
            (root / 'collections').mkdir()
            (root / 'collections/discovery.json').write_text('{"assets":{}}')
            sequence = {'images': {}, 'duration': 1, 'fps': 24}
            (folder / 'sequence.json').write_text(json.dumps(sequence))
            for name in ['index.html', 'runtime.mjs', 'viewer.mjs']:
                (folder / name).write_text('render source')
            inputs, _ = MODULE.bound_files(folder)
            (folder / 'samples/technical.json').write_text(json.dumps({
                'inputs': inputs, 'status': 'passed', 'random_seek_equal': True,
                'browser_errors': [], 'frames': 24}))
            with patch.object(MODULE, 'build_samples', return_value=folder / 'samples'):
                row = MODULE.freeze(folder, root=root, id='sample', title='Sample',
                    source_assets={}, discovery={}, tags=[], scope='test',
                    review_targets=['contact'], preparation_notes=['prepared'],
                    not_reviewed=['motion'], usage_note='')
            self.assertEqual(row['review_boundary']['motion'], 'pending')
            self.assertEqual(row['review_boundary']['static'], 'pending')
            review = json.loads((folder / 'review.json').read_text())
            self.assertEqual(review['status'], 'pending')
            self.assertNotIn('reviewer', review)
            self.assertEqual(json.loads((folder / 'review-request.json').read_text())['preparation_notes'], ['prepared'])

    def test_independent_review_requires_current_media_and_complete_scope(self):
        import copy
        inputs = {'sequence.json': 'current'}
        media = {'samples/sample.mp4': 'current-video', 'samples/contact-sheet.jpg': 'current-sheet'}
        sequence = {'duration': 4}
        review = {'schema': 'mac_motion_review/v2', 'status': 'passed',
                  'inputs': inputs, 'media': media, 'sequence_sha256': 'current',
                  'domains': {'static_alpha': 'pending', 'full_motion': 'passed'},
                  'reviewer': 'reviewer', 'reviewed_at': '2026-11-01',
                  'review_method': 'full motion inspection', 'observations': ['contact observed'],
                  'reviewed_files': ['samples/sample.mp4'], 'motion_windows': [[0, 2], [2, 4]]}
        self.assertEqual(MODULE.validate_review(review, inputs, media, sequence), review)
        for change in ({'media': {}}, {'reviewed_files': ['samples/contact-sheet.jpg']},
                       {'motion_windows': [[0, 1], [2, 4]]}, {'motion_windows': [[0, 5]]},
                       {'reviewer': ''}, {'domains': {'full_motion': 'pending'}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                MODULE.validate_review({**copy.deepcopy(review), **change}, inputs, media, sequence)


if __name__ == '__main__':
    unittest.main()
