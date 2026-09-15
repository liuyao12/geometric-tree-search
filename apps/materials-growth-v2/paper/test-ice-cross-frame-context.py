import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('context',Path(__file__).with_name('ice-cross-frame-context.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def cloud(x):return dict(vectors=[[x,0,0]],colors=[['X']])
class ContextTest(unittest.TestCase):
    def test_source_frame_exclusion_and_missing_base(self):
        motifs=[dict(base=0,cloudM=[cloud(x),cloud(100*x)]) for x in [0,.01,.5]]
        motifs.append(dict(base=1,cloudM=[cloud(0),cloud(0)]))
        library=dict(motifs=motifs,markingRadiusAngstrom=.15,trainingRegistrations=[
            dict(id='a',selected=[dict(motif=0),dict(motif=1),dict(motif=3)]),dict(id='b',selected=[dict(motif=2)])])
        r=m.calibrate(library)
        self.assertEqual([v['neighbor'] for v in r['results']],[2,2,1,None])
        self.assertEqual(r['summary']['noCrossFrameContext'],1)
        self.assertEqual(r['summary']['withinExistingTolerance'],0)
    def test_permutation_bottleneck(self):
        a=dict(vectors=[[0,0,0],[1,0,0]],colors=[['X'],['X']])
        b=dict(vectors=[[1.1,0,0],[.1,0,0]],colors=[['X'],['X']])
        self.assertAlmostEqual(m.bottleneck(a,b),.1)
if __name__=='__main__':unittest.main()
