"""Geometry-only controls for the existing joint-pose local optimizer."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
spec=importlib.util.spec_from_file_location('pose',Path(__file__).with_name('ice-joint-pose.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class MinimaxTest(unittest.TestCase):
    def test_average_and_maximum_are_different_objectives(self):
        source=np.array([[0.,0,0],[1.,0,0],[2.,0,0]])
        target=np.array([[0.,0,0],[1.,0,0],[2.3,0,0]])
        zero=np.zeros((1,1,3));translation=np.array([.1,0,0])
        self.assertAlmostEqual(np.linalg.norm(source+translation-target,axis=1).max(),.2)
        r=m.solve(source,target,zero,zero,np.eye(3),translation,.151,1.)
        self.assertEqual(r['status'],'witness')
        R=np.array(r['rotationRow']);t=np.array(r['translation'])
        self.assertLessEqual(np.linalg.norm(source@R+t-target,axis=1).max(),.151)
        self.assertAlmostEqual(r['geometryMaximum'],.15,places=6)
        self.assertAlmostEqual(np.linalg.det(R),1.,places=10)

    def test_infeasible_result_is_unknown_not_proof(self):
        x=np.array([[0.,0,0],[1.,0,0],[2.,0,0]]);y=x.copy();y[2,0]=3
        zero=np.zeros((1,1,3))
        r=m.solve(x,y,zero,zero,np.eye(3),np.zeros(3),.1,1.)
        self.assertEqual(r['status'],'local-search-unknown')
        self.assertGreater(r['geometryMaximum'],.1)

if __name__=='__main__':unittest.main()
