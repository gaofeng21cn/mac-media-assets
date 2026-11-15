"""Exercise metadata-only installation, exact-byte retrieval and disposable cache."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import media_store as store
import materialize_package


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'core';self.remote=self.base/'source';self.cache=self.base/'cache'
        self.body=b'one shared immutable original'
        self.rows=[]
        for name in ['first','second']:
            item={'path':f'payloads/{name}/same.dat','bytes':len(self.body),'sha256':hashlib.sha256(self.body).hexdigest()}
            path=self.remote/item['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.body)
            self.rows.append({'id':f'paper:{name}@current','source_id':name,'revision':'current','title':name,'kind':'image','payload':[item]})
        (self.root/'catalog').mkdir(parents=True)
        (self.root/'catalog/assets.jsonl').write_text('\n'.join(json.dumps(r) for r in self.rows))

    def test_plan_is_read_only_and_counts_shared_bytes_once(self):
        result=store.plan(self.root,self.rows,self.cache)
        self.assertEqual(result['download_bytes'],len(self.body))
        self.assertEqual(result['logical_bytes'],2*len(self.body))
        self.assertFalse(self.cache.exists())

    def test_exact_import_survives_eviction_of_its_cache(self):
        found=store.fetch(self.root,self.rows,self.cache,source_root=self.remote)
        self.assertEqual(store.cache_status(self.cache)['blobs'],1)
        independent=self.base/'project.dat';independent.write_bytes(Path(next(iter(found['resolved'].values()))).read_bytes())
        before=store.cache_status(self.cache)
        self.assertEqual(store.prune(self.cache)['reclaim_bytes'],len(self.body))
        self.assertEqual(store.cache_status(self.cache),before)
        store.prune(self.cache,apply=True)
        self.assertEqual(independent.read_bytes(),self.body)
        self.assertEqual(store.cache_status(self.cache)['bytes'],0)

    def test_cache_hit_is_offline_and_repeatable_and_pins_survive_prune(self):
        first=store.fetch(self.root,[self.rows[0]],self.cache,source_root=self.remote,pin=True)
        with patch.object(store,'urlopen',side_effect=AssertionError('network forbidden')):
            second=store.fetch(self.root,[self.rows[0]],self.cache,offline=True)
        self.assertEqual(first['snapshot'],second['snapshot'])
        self.assertEqual(second['download_bytes'],0)
        self.assertEqual(store.prune(self.cache,apply=True)['reclaim_bytes'],0)

    def test_corruption_missing_offline_and_oversized_inputs_do_not_get_admitted(self):
        with self.assertRaises(FileNotFoundError):store.fetch(self.root,[self.rows[0]],self.cache,offline=True)
        target=self.remote/self.rows[0]['payload'][0]['path'];target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'哈希'):store.fetch(self.root,[self.rows[0]],self.cache,source_root=self.remote)
        self.assertEqual(store.cache_status(self.cache)['bytes'],0)
        self.assertEqual(list(self.cache.rglob('.download-*')),[])
        with self.assertRaisesRegex(ValueError,'预算'):store.fetch(self.root,self.rows,self.cache,source_root=self.remote,max_bytes=1)

    def test_current_withdrawal_cannot_be_bypassed_with_stale_rows(self):
        (self.root/'collections').mkdir()
        (self.root/'collections/curation.json').write_text(json.dumps({'assets':{self.rows[0]['id']:{'status':'needs_rebuild'}}}))
        with self.assertRaisesRegex(ValueError,'撤回'):store.fetch(self.root,[self.rows[0]],self.cache,source_root=self.remote)

    def test_paths_and_source_versions_are_bound(self):
        for value in ['../secret','/absolute','a/../b','a\\b','./a']:
            with self.subTest(value=value),self.assertRaises(ValueError):store.relative(value)
        item=self.rows[0]['payload'][0]
        with self.assertRaises(ValueError):store.source_url({'source':{'repository':'https://example.com','revision':'main'}},item)
        url=store.source_url({'source':{'repository':'https://github.com/owner/repo.git','revision':'a'*40}},item)
        self.assertIn('/'+'a'*40+'/',url)

    def test_corrupt_cached_original_is_detected_before_reuse(self):
        store.fetch(self.root,[self.rows[0]],self.cache,source_root=self.remote)
        path=store.blob(self.cache,self.rows[0]['payload'][0]);path.chmod(0o644);path.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'缓存字节'):store.fetch(self.root,[self.rows[0]],self.cache,offline=True)


class DistributionBudgetTests(unittest.TestCase):
    def test_remote_pin_is_verified_against_git_objects_before_media_are_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'payloads/item.dat';path.parent.mkdir();path.write_bytes(b'original')
            subprocess.run(['git','init',str(root)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(root),'add','.'],check=True,capture_output=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','fixture'],check=True,capture_output=True)
            revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            item={'path':'payloads/item.dat','bytes':8,'sha256':hashlib.sha256(b'original').hexdigest()}
            rows=[{'source_id':'original','payload':[item]}]
            spec={'source':{'repository':'https://github.com/owner/repo.git','revision':revision}}
            materialize_package.verify_remote_source(root,rows,spec)
            path.write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError,'字节不一致'):materialize_package.verify_remote_source(root,rows,spec)
            with self.assertRaisesRegex(ValueError,'尚不包含'):materialize_package.verify_remote_source(root,[{'source_id':'new','payload':[{**item,'path':'payloads/new.dat'}]}],spec)

    def test_core_is_small_and_bundled_components_are_complete(self):
        root=Path(__file__).resolve().parents[1]
        self.assertTrue(materialize_package.materialize(root,check=True))
        descriptor=json.loads((root/'opl-package.json').read_text())
        paths=descriptor['content_lock']['paths']
        self.assertLess(sum((root/p).stat().st_size for p in paths),50*1024**2)
        spec=store.storage(root)
        self.assertTrue(spec['bundled_source_ids'])
        for row in store.select(root,spec['bundled_source_ids']):
            self.assertTrue(all(p['path'] in paths for p in row['payload']))


if __name__=='__main__':unittest.main()
