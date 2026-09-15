import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-ice-family-sharing.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SharingTest(unittest.TestCase):
    def test_shared_base_and_correlated_endpoints(self):
        library = dict(motifs=[dict(base=0,cloudM=[1,2]),dict(base=0,cloudM=[3,4]),
                               dict(base=0,cloudM=[1,2]),dict(base=1,cloudM=[5,6])],
            trainingRegistrations=[dict(id='a',selected=[dict(motif=0),dict(motif=2)]),
                                   dict(id='b',selected=[dict(motif=1),dict(motif=3)])])
        provenance = dict(configurations=[dict(id='a',phase='A',split='train'),
                                         dict(id='b',phase='B',split='train')])
        result = module.audit(library,provenance)
        self.assertEqual(result['baseSharingHistogram'],{'1':1,'2':1})
        self.assertEqual(result['pairwise'][0]['sharedBases'],1)
        self.assertEqual(result['summary']['exactObservedPairs'],3)
        self.assertEqual(result['summary']['exactCartesianPairs'],5)
        self.assertEqual(result['summary']['unobservedExactCartesianPairs'],2)
        provenance['configurations'][0]['split']='dev'
        with self.assertRaises(AssertionError):
            module.audit(library,provenance)


if __name__ == '__main__':
    unittest.main()
