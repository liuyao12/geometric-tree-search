#!/usr/bin/env python3
import copy,json,unittest
from pathlib import Path
from verify_p9_42947_pair_obstructions import verify

class PairObstructions(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((Path(__file__).resolve().parents[1]/'data/3d-p9-42947-pair-obstructions-2026-09-21.json').read_text())
    def test_complete_geometry(self):
        r=verify(self.data)
        self.assertTrue(r['verified']);self.assertEqual(r['relativePairSchemas'],24)
        self.assertEqual([x['coveringPlacementsChecked'] for x in r['obstructions']],[72,72])
    def test_missing_orientation(self):
        self.data['orientations'].pop()
        with self.assertRaises(ValueError):verify(self.data)
    def test_changed_prototype(self):
        self.data['prototype'][0][0]+=1
        with self.assertRaises(ValueError):verify(self.data)
    def test_legal_cover_not_negative(self):
        self.data['obstructions'][0]['pair'][1]['translation']=[20,20,20]
        with self.assertRaisesRegex(ValueError,'legal placement'):verify(self.data)
    def test_wrong_dead_voxel(self):
        self.data['obstructions'][0]['deadVoxel']=[100,100,100]
        with self.assertRaises(ValueError):verify(self.data)
    def test_occupied_dead_voxel(self):
        self.data['obstructions'][0]['deadVoxel']=self.data['orientations'][0][0]
        with self.assertRaisesRegex(ValueError,'occupied'):verify(self.data)
    def test_reflections_and_noninteger_translations(self):
        bad=copy.deepcopy(self.data);bad['allowReflections']=True
        with self.assertRaises(ValueError):verify(bad)
        self.data['obstructions'][0]['pair'][1]['translation']=[1,2,2]
        with self.assertRaises(ValueError):verify(self.data)

if __name__=='__main__':unittest.main()
