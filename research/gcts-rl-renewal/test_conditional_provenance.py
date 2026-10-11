"""Serialized independently timed component records retain exact bindings."""
import copy,gzip,json,unittest
from pathlib import Path
from types import SimpleNamespace
from audit_conditional_failure_markings import check_combined

OUT=Path(__file__).resolve().parents[2]/'.gcts-active/conditional-attachments-20261011'

class Provenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d=json.loads(gzip.decompress((OUT/'forked-semantic-pilot.json.gz').read_bytes()))
        cls.parent=SimpleNamespace(spec=d['case'],compiled=d['compiled'],inventory=d['inventory'])
        cls.models=d['models']

    def test_actual_serialized_component_measurements(self):
        a=self.models
        self.assertNotEqual(a['unary']['compile_seconds'],a['combined']['compile_seconds'])
        self.assertEqual(check_combined(self.parent,a['unary'],a['conditional'],a['combined'])['status'],'passed')

    def test_wrong_combined_measurement_cannot_rebind_hash(self):
        a=self.models;bad=copy.deepcopy(a['combined']);bad['compile_seconds']+=1
        with self.assertRaises(ValueError):check_combined(self.parent,a['unary'],a['conditional'],bad)

    def test_wrong_component_point_not_masked_by_measurement(self):
        a=self.models;bad=copy.deepcopy(a['unary']);bad['placements'][0]['marks'][0][1]+=1
        with self.assertRaises(ValueError):check_combined(self.parent,bad,a['conditional'],a['combined'])

if __name__=='__main__':unittest.main()
