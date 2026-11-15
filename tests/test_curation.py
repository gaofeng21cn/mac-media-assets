"""A stale catalog cannot override a current withdrawal or review correction."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from query_assets import query
from apply_curation import apply


class CurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'catalog').mkdir()
        (self.root / 'collections').mkdir()
        self.row = {'id': 'paper:chair@old', 'source_id': 'chair', 'revision': 'old',
                    'title': 'Chair', 'kind': 'motion_recipe', 'payload': [],
                    'review_boundary': {'admission': 'reusable_candidate', 'motion': 'passed'}}
        self.catalog = self.root / 'catalog/assets.jsonl'
        self.catalog.write_text(json.dumps(self.row) + '\n')
        self.decisions = self.root / 'collections/curation.json'
        self.decisions.write_text(json.dumps({'assets': {self.row['id']: {
            'status': 'needs_rebuild', 'review_boundary': {'motion': 'rejected'}}}}))
        (self.root / 'collections/assemblies.json').write_text(json.dumps({'assemblies': [
            {'id': 'seat', 'parts': [{'asset_id': self.row['id'], 'source_id': 'chair'}]}]}))

    def test_withdrawal_applies_to_default_exact_source_and_collection_queries(self):
        for options in ({}, {'asset_id': self.row['id']}, {'asset_id': 'chair'}, {'collection': 'seat'}):
            self.assertEqual(query(self.root, **options), [])
        self.assertEqual(len(query(self.root, include_withdrawn=True)), 1)
        history = query(self.root, asset_id=self.row['id'], include_withdrawn=True)
        self.assertFalse(history[0]['available_for_use'])
        self.assertEqual(history[0]['maturity']['motion'], 'rejected')
        self.assertEqual(apply(self.root, check=True), [self.row['id']])
        apply(self.root)
        self.assertEqual(apply(self.root, check=True), [])

    def test_collection_never_substitutes_a_same_name_revision(self):
        self.decisions.write_text('{"assets":{}}')
        self.catalog.write_text(json.dumps({**self.row, 'id': 'paper:chair@new', 'revision': 'new'}))
        self.assertEqual(query(self.root, collection='seat'), [])

    def test_collection_keeps_its_exact_available_revision(self):
        self.decisions.write_text('{"assets":{}}')
        self.catalog.write_text(json.dumps(self.row) + '\n' + json.dumps({**self.row, 'id': 'paper:chair@new', 'revision': 'new'}))
        self.assertEqual([r['id'] for r in query(self.root, collection='seat')], [self.row['id']])

    def test_broken_curation_fails_closed(self):
        for value in ('{', '[]', '{"assets": []}', '{"assets":{"paper:chair@old":null}}'):
            self.decisions.write_text(value)
            with self.assertRaises(ValueError):
                query(self.root)

    def test_current_review_overrides_immutable_record_pass(self):
        self.decisions.write_text(json.dumps({'assets': {self.row['id']: {
            'status': 'active', 'review_boundary': {'motion': 'pending', 'static': 'pending'}}}}))
        found = query(self.root, asset_id=self.row['id'])[0]
        self.assertEqual(found['maturity']['motion'], 'pending')
        self.assertEqual(query(self.root, maturity_stage='motion'), [])

    def test_sync_does_not_revive_withdrawn_or_stale_review(self):
        workspace = self.root / 'workbench'
        source = workspace / 'assets/paper-theatre'
        source.mkdir(parents=True)
        (source / 'catalog.json').write_text('{"items": []}')
        script = Path(__file__).resolve().parents[1] / 'tools/sync_from_workbench.py'
        subprocess.run([sys.executable, str(script), '--workspace', str(workspace), '--root', str(self.root)], check=True, capture_output=True)
        self.assertEqual(query(self.root), [])
        self.catalog.write_text(json.dumps(self.row))
        self.decisions.write_text(json.dumps({'assets': {self.row['id']: {
            'status': 'active', 'review_boundary': {'motion': 'pending'}}}}))
        subprocess.run([sys.executable, str(script), '--workspace', str(workspace), '--root', str(self.root)], check=True, capture_output=True)
        self.assertEqual(query(self.root)[0]['review_boundary']['motion'], 'pending')
