"""Check actual discovery boundaries against the independently stored catalog."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from query_assets import query
from sync_from_workbench import public_reusable


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

if __name__=='__main__':unittest.main()
