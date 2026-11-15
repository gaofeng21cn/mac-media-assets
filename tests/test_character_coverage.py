import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_character_coverage import audit


class CharacterCoverageTests(unittest.TestCase):
    def test_rejected_registered_pose_is_not_available(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'collections').mkdir()
            (root/'catalog').mkdir()
            coverage = {'roles': {'child_boy': {'label': '男童', 'required_poses': ['stand', 'seated'],
                        'current_assets': {'stand': 'paper:stand@one', 'seated': 'paper:sit@two'}}}}
            (root/'collections/character-coverage.json').write_text(json.dumps(coverage))
            (root/'collections/curation.json').write_text(json.dumps({'assets': {'paper:sit@two':
                       {'status': 'needs_rebuild', 'reason': '同尺度试装座高不合理'}}}))
            (root/'catalog/assets.jsonl').write_text('\n'.join(json.dumps({'id': identifier})
                       for identifier in ['paper:stand@one', 'paper:sit@two']))
            result = audit(root)
            self.assertEqual(result['registered_pose_slots'], 2)
            self.assertEqual(result['available_pose_slots'], 1)
            self.assertEqual(result['missing_pose_slots'], 0)
            self.assertEqual(result['unusable_registered_pose_slots'], 1)
            self.assertEqual(result['unusable_registered_poses'][0]['asset_id'], 'paper:sit@two')


if __name__ == '__main__':
    unittest.main()
