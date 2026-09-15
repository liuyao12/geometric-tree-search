import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('learner',Path(__file__).with_name('learn-ice-context-substitutions.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def cloud(x):return dict(vectors=[[x,0,0]],colors=[['X']])
class SubstitutionTest(unittest.TestCase):
    def test_no_chaining_no_cross_base_and_either_endpoint(self):
        motifs=[dict(base=0,cloudM=[cloud(.1*i),cloud(10*i)]) for i in range(3)]
        motifs.extend([dict(base=1,cloudM=[cloud(0),cloud(0)]),
                       dict(base=0,cloudM=[cloud(100),cloud(20.1)])])
        report=module.learn(dict(markingRadiusAngstrom=.15,motifs=motifs))
        self.assertEqual(report['neighbors'],[[0,1],[0,1,2],[1,2,4],[3],[2,4]])
        self.assertEqual(report['summary']['directedPairs'],11)
if __name__=='__main__':unittest.main()
