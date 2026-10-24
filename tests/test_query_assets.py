"""Check actual discovery boundaries against the independently stored catalog."""
import sys
import json
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from query_assets import query, all_catalog_rows
from sync_from_workbench import public_reusable
from apply_character_anchors import canonical_revision, apply as apply_anchors


class DiscoveryTests(unittest.TestCase):
    def test_default_preserves_generic_discovery_without_other_author_brands(self):
        rows=query()
        self.assertTrue(rows)
        self.assertFalse(any(row['reuse_scope'].get('kind')=='author' for row in rows))
        owned=query(author_id='example_author',include_author_assets=True)
        self.assertFalse(any(row['reuse_scope'].get('kind')=='author' for row in owned))

    def test_public_sync_excludes_author_content_and_branded_samples(self):
        self.assertFalse(public_reusable({'kind':'image','reuse_scope':{'kind':'author'}}))
        self.assertFalse(public_reusable({'kind':'brand','reuse_scope':{'kind':'general'}}))
        self.assertFalse(public_reusable({'kind':'motion_recipe','source':{'sample_has_brand':True}}))
        self.assertTrue(public_reusable({'kind':'image','reuse_scope':{'kind':'general'}}))

    def test_aliases_find_same_series_and_catalog_contains_only_usable_candidates(self):
        a=query(series='pituitary_paper_theatre')
        b=query(series='pituitary_tumor_s01')
        self.assertEqual({row['id'] for row in a},{row['id'] for row in b})
        self.assertTrue(a)
        self.assertFalse(query(kind='reference_frame'))

    def test_default_discovery_excludes_reference_and_withdrawn_versions(self):
        rows = query()
        self.assertFalse(any(row['review_boundary']['admission']=='reference_only' for row in rows))
        self.assertFalse(any(row.get('curation', {}).get('status') in {'needs_rebuild','superseded'} for row in rows))
        self.assertFalse(any(row.get('curation', {}).get('status') in {'needs_rebuild','superseded'} for row in rows))



class SemanticDiscoveryTests(unittest.TestCase):
    def test_chinese_names_emotions_and_provenance_noise(self):
        expected={'甲状腺':'six_paper_thyroid_neck','磁共振':'reserve_mri_v1',
                  '探索':'mac_music_curious_v1','紧张':'mac_music_tension_v1'}
        for word,identifier in expected.items():
            self.assertIn(identifier,{r['source_id'] for r in query(text=word)})
        self.assertNotIn('paper_clinic_environment',{r['source_id'] for r in query(text='MRI')})

    def test_facets_and_collection_select_real_members(self):
        self.assertTrue(query(category='配乐',text='探索'))
        self.assertTrue(all(r['discovery']['category']=='characters' for r in query(category='characters')))
        self.assertEqual({r['source_id'] for r in query(collection='door')},
                         {'reserve_door_frame_v1','reserve_door_leaf_v1'})
        self.assertEqual(query(collection='missing'),[])
        self.assertIn('mac_sfx_bottle_cap_v1',
                      {r['source_id'] for r in query(category='sfx',action='旋盖')})

    def test_cooking_collection_exposes_all_independent_parts(self):
        self.assertEqual(
            {r['source_id'] for r in query(collection='cooking_prep')},
            {
                'reserve_kitchen_counter_v2', 'reserve_chopping_board_v1',
                'reserve_kitchen_knife_v1', 'reserve_induction_cooktop_v1',
                'reserve_frying_pan_v1', 'reserve_wooden_spatula_v1',
                'reserve_broccoli_v1', 'reserve_oil_v1',
            },
        )
        self.assertEqual(query(asset_id='reserve_thyroid_simple_v1'), [])

    def test_missing_and_scalar_facets_do_not_stop_discovery(self):
        import tempfile,json
        from unittest.mock import patch
        import query_assets
        original=query_assets.load
        def imperfect(path,default):
            if path.name=='discovery.json':return {'assets':{'reserve_mri_v1':{'aliases':'磁共振'}}}
            return original(path,default)
        with patch.object(query_assets,'load',side_effect=imperfect):
            self.assertTrue(query(text='磁共振'))
            self.assertTrue(query(text='独立MRI'))


class CharacterDiscoveryTests(unittest.TestCase):
    def test_motion_role_discovery_keeps_static_pose_selection_precise(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'collections').mkdir()
            (root/'catalog').mkdir()
            (root/'collections/character-coverage.json').write_text(json.dumps({'roles': {
                'older_man': {'label': '老年男性', 'current_assets': {'seated': 'paper:seat@current'}},
                'young_man': {'label': '年轻成年男性', 'current_assets': {}}
            }}))
            rows = [
                {'id': 'paper:seat@current', 'source_id': 'seat', 'kind': 'image'},
                {'id': 'paper:rise@current', 'source_id': 'rise', 'kind': 'motion_recipe',
                 'discovery': {'category': 'motion', 'character_role': 'older_man',
                               'poses': ['stand', 'seated'], 'actions': ['坐站过渡']}},
                {'id': 'paper:young_rise@current', 'source_id': 'young_rise', 'kind': 'motion_recipe',
                 'discovery': {'category': 'motion', 'character_role': 'young_man',
                               'poses': ['stand', 'seated'], 'actions': ['坐站过渡']}}
            ]
            for row in rows:
                row.update(title=row['source_id'], revision='current', payload=[])
            (root/'catalog/assets.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
            self.assertEqual([r['id'] for r in query(root, character_role='老年男性', pose='坐姿')],
                             ['paper:seat@current'])
            for selectors in ({'category': 'motion'}, {'kind': 'motion_recipe'}, {'action': '坐站过渡'}):
                self.assertEqual([r['id'] for r in query(root, character_role='老年男性', pose='坐姿', **selectors)],
                                 ['paper:rise@current'])
            self.assertEqual(query(root, category='motion', character_role='老年男性', pose='lying'), [])
            self.assertEqual(query(root, category='motion', character_role='不存在'), [])

    def test_chinese_pose_alias_and_text_cli_accept_list_medium(self):
        import subprocess
        self.assertEqual({r['id'] for r in query(character_role='医生', pose='伸手')},
                         {r['id'] for r in query(character_role='医生', pose='reach')})
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root/'tools/query_assets.py'),
                                 '--character-role', '女性医生', '--pose', '坐姿问诊'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('paper_collage', result.stdout)

    def test_specific_age_roles_do_not_match_substring_aliases(self):
        adult = query(character_role='成年男性', pose='stand')
        young = query(character_role='年轻成年男性', pose='stand')
        self.assertEqual([row['source_id'] for row in adult], ['character_adult_man_stand_v1'])
        self.assertEqual([row['source_id'] for row in young], ['character_young_man_stand_v1'])

    def test_character_filters_return_one_reviewed_version(self):
        rows = query(character_role='老年男性', pose='walk')
        self.assertEqual([row['source_id'] for row in rows], ['character_older_man_walk_v1'])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['discovery'])

    def test_missing_pose_is_explicitly_empty(self):
        self.assertEqual(query(character_role='儿童', pose='kneeling'), [])

    def test_default_discovery_prefers_coverage_version_and_exact_history_stays_visible(self):
        current = query(character_role='成年男性', pose='stand')
        self.assertEqual(len(current), 1)
        root = Path(__file__).resolve().parents[1]
        expected = json.loads((root / 'collections/character-coverage.json').read_text())['roles']['adult_man']['current_assets']['stand']
        self.assertEqual(current[0]['id'], expected)
        exact = query(asset_id=current[0]['id'])
        self.assertEqual([row['id'] for row in exact], [current[0]['id']])
        # Retired duplicate registrations are no longer in the usable catalog.
        absent = query(asset_id='paper:character_adult_man_stand_v1@absent')
        self.assertEqual(absent, [])
        by_source = query(asset_id='character_adult_man_stand_v1')
        self.assertEqual([row['id'] for row in by_source], [current[0]['id']])

    def test_generic_adult_woman_has_complete_contact_anchors(self):
        rows = query(character_role='成年女性')
        self.assertTrue(rows)
        root = Path(__file__).resolve().parents[1]
        coverage = json.loads((root / 'collections/character-coverage.json').read_text())
        expected = {asset_id for asset_id in coverage['roles']['adult_woman']['current_assets'].values() if asset_id}
        self.assertEqual({row['id'] for row in rows}, expected)
        by_id = {row['id']: row for row in rows}
        selected = coverage['roles']['adult_woman']['current_assets']
        for pose in coverage['roles']['adult_woman']['required_poses']:
            anchors = by_id[selected[pose]]['registration']['anchors']
            self.assertIn('head', anchors)
            if pose == 'reach':
                self.assertTrue(any(key == 'hand' or key.startswith('hand_') for key in anchors))

    def test_current_characters_use_reconstructable_revisions_and_idempotent_anchors(self):
        root = Path(__file__).resolve().parents[1]
        targets = json.loads((root / 'collections/character-anchors.json').read_text())['assets']
        result = apply_anchors(root, check=True)
        self.assertEqual(result['status'], 'passed')
        rows = {row['id']: row for row in all_catalog_rows(root)}
        for source_id, expected in targets.items():
            row = rows[result['current'][source_id]]
            record = json.loads((root / row['portable_record']).read_text())
            self.assertEqual(row['revision'], canonical_revision(record))
            self.assertEqual(record['registration'], expected)

if __name__=='__main__':unittest.main()
