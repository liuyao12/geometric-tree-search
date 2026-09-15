import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('symmetry',Path(__file__).with_name('ice-base-symmetry-audit.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SymmetryTest(unittest.TestCase):
    def test_tetrahedron_partition_and_proper_rotations(self):
        base=dict(anchors=[[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]],species=['X']*4,t=[1]*4,componentSites=[[0,1],[2,3]])
        r=m.self_maps(base,1e-8)
        self.assertEqual(len(r['maps']),4)
        self.assertTrue(all(row['numericallyExact'] for row in r['maps']))
        self.assertEqual(r['rank'],3)
        base['anchors'][0][0]+=.02
        perturbed=m.self_maps(base,.15)
        self.assertEqual(sum(row['numericallyExact'] for row in perturbed['maps']),1)
        self.assertGreater(len(perturbed['maps']),1)
if __name__=='__main__':unittest.main()
