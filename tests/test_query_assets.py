"""Check actual discovery boundaries against the independently stored catalog."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from query_assets import query


class DiscoveryTests(unittest.TestCase):
    def test_default_preserves_generic_discovery_without_other_author_brands(self):
        rows=query()
        self.assertTrue(rows)
        self.assertFalse(any(row['reuse_scope'].get('kind')=='author' for row in rows))
        owned=query(author_id='dr_mie')
        self.assertTrue(any(row['reuse_scope'].get('kind')=='author' for row in owned))

    def test_aliases_find_same_series_and_reference_stays_reference(self):
        a=query(series='pituitary_paper_theatre')
        b=query(series='pituitary_tumor_s01')
        self.assertEqual({row['id'] for row in a},{row['id'] for row in b})
        self.assertTrue(a)
        refs=query(kind='reference_frame')
        self.assertTrue(refs)
        self.assertTrue(all(row['review_boundary']['admission']=='reference_only' for row in refs))

    def test_default_discovery_excludes_reference_and_withdrawn_versions(self):
        rows = query()
        self.assertFalse(any(row['review_boundary']['admission']=='reference_only' for row in rows))
        self.assertFalse(any(row.get('curation', {}).get('status') in {'needs_rebuild','superseded'} for row in rows))
        preserved = query(include_reference=True)
        self.assertTrue(any(row['review_boundary']['admission']=='reference_only' for row in preserved))
        self.assertTrue(any(row.get('curation', {}).get('status')=='needs_rebuild' for row in preserved))


if __name__=='__main__':unittest.main()
