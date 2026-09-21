#!/usr/bin/env python3
import copy,json,unittest
from pathlib import Path
from verify_voxel_pair_certificate import audit_geometry
ROOT=Path(__file__).resolve().parents[1]
class PairGeometry(unittest.TestCase):
 def setUp(self):
  b=ROOT/'data/p10-346304-pair-obstruction'
  self.data=json.loads((b/'pair.input.json').read_text());self.base=json.loads((b/'manifest.json').read_text())['voxels']
 def test_orbit(self):self.assertEqual(audit_geometry(self.data,self.base),{'volume':10,'orientations':8,'properRotations':24,'relativePairSchemas':48})
 def test_changed_problem(self):
  edits=[lambda d:d['model']['orientations'].pop(),lambda d:d['model']['orientations'].append(d['model']['orientations'][0]),lambda d:d['model']['orientations'][0]['cells'][0].update(weight=7),lambda d:d['model']['orientations'][0].update(marks=[{'pos':[0,0,0],'value':1}]),lambda d:d['pair'].__setitem__(1,d['pair'][0]),lambda d:d['pair'][1].update(translation=[1,0,0]),lambda d:d['model'].update(allowReflections=True),lambda d:d.update(pairExclusions=[d['pair']])]
  for edit in edits:
   d=copy.deepcopy(self.data);edit(d)
   with self.assertRaises(ValueError):audit_geometry(d,self.base)
if __name__=='__main__':unittest.main()
