"""Source writes and routine checks automatically converge on compressed assets."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import repository_media as repository
import media_store
import materialize_package
from optimize_media import canonical,prepare_asset,write


class RepositoryMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.root=self.base/'repo';self.root.mkdir()
        self.env=patch.dict(os.environ,{'MAC_MEDIA_STATE':str(self.base/'state')});self.env.start();self.addCleanup(self.env.stop)
        write(self.root/'catalog/media-storage.json',{'profile':'catalog'})
        (self.root/'catalog/assets.jsonl').write_text('')
        for name in ['plugin.json','.codex-plugin/plugin.json','.agents/plugins/marketplace.json','app-contribution-adapter.json']:
            write(self.root/name,{})
        write(self.root/'contracts/opl_capability_package_manifest.json',{'version':'1.0.0'})
        subprocess.run(['git','init',str(self.root)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','baseline'],check=True,capture_output=True)
        ref=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        write(self.root/'catalog/media-storage.json',{'profile':'catalog','repository_storage':{
            'legacy_git_ref':ref,'core_limit_bytes':10*1024**2,'object_limit_bytes':10*1024**2,
            'object_repository':'ghcr.io/owner/media'}})
        self.cache=self.base/'cache'

    def direct_write(self,library=None,identifier='direct_piece'):
        library=library or self.root
        image=self.base/(identifier+'.png')
        im=Image.new('RGBA',(128,128),(91,42,17,0));im.paste((90,160,30,255),(20,20,110,110));im.save(image)
        record={'schema':'animation_element/v1','id':identifier,'title':'直接写入纸件','kind':'image',
                'entry':'files/payload.png','reuse_scope':{'kind':'general'},'status':'reusable_candidate',
                'source':{'kind':'imagegen'},'content_bounds':[20,20,110,110],
                'content_bounds_format':'pixel_xyxy_right_bottom_exclusive',
                'files':[{'path':'files/payload.png','sha256':media_store.sha(image),'bytes':image.stat().st_size,'role':'payload'}]}
        record['revision']=canonical(record)
        path=library/'entries'/identifier/record['revision']/'record.json'
        write(path,record);(path.parent/'files').mkdir();shutil.copy2(image,path.parent/'files/payload.png')
        return record,path,image

    def test_build_sweeps_direct_registered_media_into_durable_objects_and_is_repeatable(self):
        record,path,source=self.direct_write()
        original=source.read_bytes()
        self.assertTrue(materialize_package.materialize(self.root))
        rows=[json.loads(s) for s in (self.root/'catalog/assets.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),1);row=rows[0];self.assertEqual(row['payload'][0]['storage'],'object')
        self.assertTrue(row['payload'][0]['path'].endswith('.webp'))
        self.assertFalse((path.parent/'files/payload.png').exists())
        self.assertTrue((self.root/row['payload'][0]['path']).exists())
        actual=media_store.locate(self.root,row['payload'][0],self.cache)
        self.assertEqual(Image.open(actual).convert('RGBA').tobytes(),Image.open(source).convert('RGBA').tobytes())
        master=repository.object_path(self.root,record['files'][0]);self.assertEqual(master.read_bytes(),original)
        before=(self.root/'catalog/assets.jsonl').read_bytes()
        self.assertEqual(repository.reconcile(self.root,cache=self.cache)['processed'],[])
        self.assertEqual((self.root/'catalog/assets.jsonl').read_bytes(),before)
        self.assertEqual(repository.audit(self.root)['errors'],[])
        with patch.object(media_store,'urlopen',side_effect=AssertionError('offline use cannot download')):
            fetched=media_store.fetch(self.root,[row],self.cache,offline=True)
        self.assertTrue(fetched['resolved'])
        self.assertTrue(repository.audit(self.root,require_published=True)['errors'])

    def test_check_is_read_only_and_new_naked_media_are_preserved_outside_git(self):
        record,path,source=self.direct_write()
        before=(path.parent/'files/payload.png').read_bytes()
        self.assertTrue(repository.audit(self.root)['unprocessed_media'])
        self.assertEqual((path.parent/'files/payload.png').read_bytes(),before)
        naked=self.root/'unregistered.dat';naked.write_bytes(before)
        result=repository.reconcile(self.root,cache=self.cache)
        self.assertEqual(len(result['processed']),2)
        self.assertEqual(result['errors'],[]);self.assertFalse(naked.exists())
        self.assertTrue(repository.object_path(self.root,record['files'][0]).is_file())
        self.assertEqual(repository.reconcile(self.root,cache=self.cache)['errors'],[])

    def test_disguised_direct_media_are_normalized_without_blocking_the_batch(self):
        _,_,source=self.direct_write()
        naked=self.root/'not-an-image.dat';shutil.copy2(source,naked)
        subprocess.run(['git','-C',str(self.root),'add','-f',str(naked)],check=True,capture_output=True)
        result=repository.reconcile(self.root,cache=self.cache)
        self.assertFalse(naked.exists())
        self.assertEqual(result['errors'],[])
        self.assertEqual(len(result['processed']),2)

    def test_backlog_and_future_source_records_are_discovered_without_changing_the_writer(self):
        library=self.base/'workbench/assets/paper-theatre'
        first,path,_=self.direct_write(library,'backlog')
        write(library/'catalog.json',{'items':[{'record':str(path.relative_to(library))}]})
        backlog=self.base/'backlog.json';write(backlog,[{'library':{'record':str(path.relative_to(library))}}])
        repository.configure(self.root,library,backlog)
        self.assertEqual(len(repository.reconcile(self.root,cache=self.cache)['processed']),1)
        second,path2,_=self.direct_write(library,'new_after_setup')
        write(library/'catalog.json',{'items':[{'record':str(path.relative_to(library))},{'record':str(path2.relative_to(library))}]})
        result=repository.reconcile(self.root,cache=self.cache)
        self.assertEqual(len(result['processed']),1)
        self.assertEqual(result['processed'][0]['source_asset_id'],'paper:new_after_setup@'+second['revision'])
        self.assertEqual(repository.reconcile(self.root,cache=self.cache)['processed'],[])

    def test_rescanning_delivered_revision_preserves_its_canonical_projection(self):
        self.direct_write()
        repository.reconcile(self.root,cache=self.cache)
        catalog=self.root/'catalog/assets.jsonl'
        row=json.loads(catalog.read_text())
        row['discovery']={'category':'lifestyle','aliases':['Existing alias']}
        row['provenance']['record_ref']='existing-source/record.json'
        catalog.write_text(json.dumps(row)+'\n')
        record_path=self.root/row['portable_record']
        stored=record_path.read_bytes()
        record=json.loads(stored)
        library=self.base/'workbench'
        duplicate=library/'entries'/record['id']/record['revision']/'record.json'
        write(duplicate,dict(reversed(tuple(record.items()))))
        for part, payload in zip(record['files'],row['payload']):
            destination=duplicate.parent/part['path']
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(self.root/payload['path'],destination)
        write(library/'catalog.json',{'items':[]})
        repository.configure(self.root,library,None)
        write(library/'catalog.json',{'items':[{'record':str(duplicate.relative_to(library))}]})
        local_duplicate=self.root/duplicate.relative_to(library)
        shutil.copytree(duplicate.parent,local_duplicate.parent)
        self.direct_write(identifier='new_piece')

        result=repository.reconcile(self.root,cache=self.cache)

        self.assertEqual(result['errors'],[])
        self.assertEqual(result['notes'],[])
        persisted={item['id']:item for item in map(json.loads,catalog.read_text().splitlines())}
        self.assertEqual(persisted[row['id']],row)
        self.assertEqual(record_path.read_bytes(),stored)
        self.assertTrue(all(not (local_duplicate.parent/part['path']).exists() for part in record['files']))
        self.assertNotIn(row['id'],media_store.read(self.root/'catalog/delivery-report.json')['aliases'])
        self.assertEqual(len(result['processed']),1)
        self.assertTrue(result['processed'][0]['asset_id'].startswith('paper:new_piece@'))
        self.assertEqual(repository.reconcile(self.root,cache=self.cache)['processed'],[])

    def test_original_import_updates_references_to_an_already_delivered_revision(self):
        library=self.base/'workbench'
        record,source_path,_=self.direct_write(library)
        source_id='paper:'+record['id']+'@'+record['revision']
        prepared=prepare_asset(library,repository.row_for_record(library,source_path,record),self.cache)
        delivered=prepared['record'];asset_id=prepared['row']['id']
        self.assertNotEqual(asset_id,source_id)
        delivered_path=source_path.parent.parent/delivered['revision']/'record.json'
        write(delivered_path,delivered)
        for part in prepared['row']['payload']:
            target=delivered_path.parent/Path(part['path']).relative_to(
                'payloads/paper-theatre/'+record['id']+'/'+delivered['revision'])
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(prepared['resolved'][part['path']],target)
        repository.reconcile(self.root,source_library=library,source_record=delivered_path,cache=self.cache)
        catalog=self.root/'catalog/assets.jsonl'
        row=json.loads(catalog.read_text());row['usage']=['Existing guidance']
        catalog.write_text(json.dumps(row)+'\n')
        collection=self.root/'collections/character-scale.json'
        write(collection,{'assets':{source_id:{'source_asset_id':source_id,'source_sha256':record['files'][0]['sha256']}}})

        result=repository.reconcile(self.root,source_library=library,source_record=source_path,cache=self.cache)

        self.assertEqual(result['notes'],[])
        self.assertEqual(json.loads(catalog.read_text()),row)
        self.assertEqual(media_store.read(collection),{'assets':{asset_id:{
            'source_asset_id':asset_id,'source_sha256':row['payload'][0]['sha256']}}})
        self.assertEqual(media_store.read(self.root/'catalog/delivery-report.json')['aliases'][source_id],asset_id)
        self.assertEqual(repository.reconcile(self.root,source_library=library,source_record=source_path,cache=self.cache)['processed'],[])

    def test_same_scan_original_and_delivered_records_share_one_exact_projection(self):
        library = self.base / 'workbench'
        original, source_path, _ = self.direct_write(library)
        source_row = repository.row_for_record(library, source_path, original)
        prepared = prepare_asset(library, source_row, self.cache)
        delivered = prepared['record']
        delivered_row = prepared['row']
        self.assertNotEqual(source_row['id'], delivered_row['id'])
        delivered_path = source_path.parent.parent / delivered['revision'] / 'record.json'
        write(delivered_path, dict(reversed(tuple(delivered.items()))))
        self.assertNotEqual(media_store.sha(delivered_path), delivered_row['portable_record_sha256'])
        for part in delivered['files']:
            stored_path = str(Path('payloads/paper-theatre') / original['id'] / delivered['revision'] / part['path'])
            output = delivered_path.parent / part['path']
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(prepared['resolved'][stored_path], output)
        write(library / 'catalog.json', {'items': []})
        repository.configure(self.root, library, None)
        write(library / 'catalog.json', {'items': [
            {'record': str(path.relative_to(library))} for path in (source_path, delivered_path)
        ]})

        result = repository.reconcile(self.root, cache=self.cache)

        self.assertEqual(result['notes'], [])
        self.assertEqual(result['processed'], [{'source_asset_id': source_row['id'], 'asset_id': delivered_row['id']}])
        catalog = self.root / 'catalog/assets.jsonl'
        before = catalog.read_bytes()
        row = json.loads(before)
        self.assertEqual(row['id'], delivered_row['id'])
        self.assertEqual(row['repository_storage']['source_asset_id'], source_row['id'])
        self.assertEqual(row['portable_record_sha256'], delivered_row['portable_record_sha256'])
        self.assertEqual(media_store.sha(self.root / row['portable_record']), row['portable_record_sha256'])
        self.assertEqual(repository.reconcile(self.root, cache=self.cache)['processed'], [])
        self.assertEqual(catalog.read_bytes(), before)

    def test_master_retention_is_independent_of_disposable_encoding_cache(self):
        record,path,source=self.direct_write()
        result=repository.reconcile(self.root,cache=self.cache)
        self.assertEqual(result['errors'],[])
        master=repository.object_path(self.root,record['files'][0]);before=master.read_bytes()
        media_store.prune(self.cache,apply=True)
        self.assertEqual(master.read_bytes(),before)
        self.assertEqual(source.read_bytes(),before)

    def test_verify_catalog_rejects_orphan_binary_under_records(self):
        write(self.root / 'app-contribution-adapter.json', {'reads': {'mac.media.v1#review': {'kind': 'command'}}})
        write(self.root / 'opl-package.json', {
            'codex_surface': {'app_contribution_adapter': {'manifest': 'app-contribution-adapter.json'}},
            'content_lock': {'paths': ['app-contribution-adapter.json']},
        })
        stray = self.root / 'records/paper-theatre/stray_item/rev1/files/payload.png'
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_bytes(b'not-a-record-json')
        write(self.root / 'collections/series.json', {'series': {}, 'aliases': {}})
        write(self.root / 'collections/curation.json', {'assets': {}})
        res = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / 'tools/verify_catalog.py'),
             '--root', str(self.root), '--metadata-only'],
            capture_output=True, text=True,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('orphan_record_file:records/paper-theatre/stray_item/rev1/files/payload.png', res.stdout)


if __name__=='__main__':unittest.main()
