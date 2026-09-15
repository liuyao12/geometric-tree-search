import importlib.util
from pathlib import Path
import unittest
import numpy as np
spec=importlib.util.spec_from_file_location('ambient',Path(__file__).with_name('ice-ambient-context.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AmbientTest(unittest.TestCase):
    def test_graph_order_and_rigid_motion(self):
        c=dict(positions=[[0,0,0],[1,0,0],[0,1,0],[1,1,.1]],species=['X']*4,cell=(np.eye(3)*10).tolist(),pbc=[True]*3)
        cover=dict(components=[[i] for i in range(4)],componentPairs=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]])
        before=list(m.contexts(c,cover));after=list(m.contexts(c,dict(cover,componentPairs=list(reversed(cover['componentPairs'])))))
        self.assertEqual(before,after)
        rotation=np.array([[0,-1,0],[1,0,0],[0,0,1]])
        moved=dict(c,positions=(np.array(c['positions'])@rotation+[3,4,5]).tolist(),cell=(np.array(c['cell'])@rotation).tolist())
        for a,b in zip(before,m.contexts(moved,cover)):
            self.assertTrue(np.allclose(np.array(a['vectors'])@rotation,b['vectors']))
            self.assertEqual(len(a['vectors']),4)
        one=list(m.junction.junctions(c,cover,[0,3,5,2]))
        two=list(m.junction.junctions(c,cover,[0,4,5,1]))
        self.assertNotEqual(one[0]['vectors'],two[0]['vectors'])
        self.assertEqual(before,list(m.contexts(c,cover)))
if __name__=='__main__':unittest.main()
