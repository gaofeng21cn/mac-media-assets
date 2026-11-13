import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import offline_installation as offline
import media_store


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.core=self.base/'core';self.source=self.base/'full';self.cache=self.base/'cache'
        (self.core/'catalog').mkdir(parents=True);(self.core/'contracts').mkdir()
        self.body=b'complete offline original'
        self.item={'path':'payloads/a/original.bin','bytes':len(self.body),'sha256':hashlib.sha256(self.body).hexdigest()}
        self.row={'id':'paper:a@one','source_id':'a','revision':'one','title':'A','kind':'image','payload':[self.item]}
        (self.core/'catalog/assets.jsonl').write_text(json.dumps(self.row)+'\n')
        (self.core/'catalog/media-storage.json').write_text(json.dumps({'source':{'repository':'https://github.com/owner/repo.git','revision':'a'*40}}))
        self.row['portable_record']='records/a/one/record.json'
        (self.core/'catalog/assets.jsonl').write_text(json.dumps(self.row)+'\n')
        core_files=['plugin.json','.codex-plugin/plugin.json','.agents/plugins/marketplace.json','app-contribution-adapter.json',self.row['portable_record']]
        for name in core_files:
            file=self.core/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('{}')
        descriptor={'package_id':'mac-media-assets','version':'1.0.0','content_lock':{'paths':['catalog/assets.jsonl','catalog/media-storage.json',*core_files]}}
        for name in ['opl-package.json','contracts/opl_capability_package_manifest.json']:(self.core/name).write_text(json.dumps(descriptor))
        p=self.source/self.item['path'];p.parent.mkdir(parents=True);p.write_bytes(self.body)

    def test_full_install_is_self_contained_and_survives_general_cache_pruning(self):
        result=offline.install(self.core,self.cache,self.source)
        self.assertEqual(result['status'],'installed');self.assertEqual(result['installed_profiles'],['offline'])
        self.assertEqual(result['installations'][0]['file_count'],1)
        (self.source/self.item['path']).unlink()
        media_store.prune(self.cache,apply=True)
        self.assertEqual(media_store.locate(self.core,self.item,self.cache).read_bytes(),self.body)
        self.assertEqual(offline.install(self.core,self.cache)['status'],'already_installed')

    def test_one_archive_is_verified_by_each_declared_file_without_extracting_other_members(self):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as archive:
            member=tarfile.TarInfo('repo-sha/'+self.item['path']);member.size=len(self.body);archive.addfile(member,io.BytesIO(self.body))
            evil=tarfile.TarInfo('repo-sha/../../escape');evil.size=1;archive.addfile(evil,io.BytesIO(b'x'))
        data.seek(0)
        with patch.object(offline,'urlopen',return_value=data) as request:
            result=offline.install(self.core,self.cache)
        self.assertEqual(result['status'],'installed');self.assertEqual(request.call_count,1)
        self.assertFalse((self.base/'escape').exists())

    def test_source_corruption_does_not_create_installed_pointer(self):
        (self.source/self.item['path']).write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'字节不一致'):offline.install(self.core,self.cache,self.source)
        self.assertFalse((self.cache/'offline/current.json').exists())

    def test_uninstall_binds_the_owner_revision_and_preserves_source(self):
        result=offline.install(self.core,self.cache,self.source);row=result['installations'][0]
        with self.assertRaisesRegex(ValueError,'已变化'):offline.uninstall(self.core,self.cache,'stale')
        self.assertTrue(Path(row['location']).exists())
        self.assertEqual(offline.uninstall(self.core,self.cache,row['revision'])['installations'],[])
        self.assertTrue((self.source/self.item['path']).exists())

    def test_unknown_identity_version_and_profile_are_rejected(self):
        for change in [{'package_id':'other'},{'version':'9.0.0'},{'profile':'unknown'}]:
            with self.assertRaises(ValueError):offline.execute({'operation':'install','version':'1.0.0',**change},self.core,self.cache,self.source)


if __name__=='__main__':unittest.main()
