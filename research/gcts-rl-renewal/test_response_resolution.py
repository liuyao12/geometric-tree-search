import unittest
from turtle import Policy
from boundary_responses import declarations
from response_resolution import MODES,features,training_boundaries
from audit_response_resolution import declared_features,chosen_valid

class ResolutionTests(unittest.TestCase):
    def test_context_comes_from_boundary_before_search(self):
        for b in (*declarations(),*training_boundaries(declarations()[0].allowed)):
            self.assertEqual([features(b,m) for m in MODES],declared_features(b))
    def test_zero_and_frozen_policy_choices_have_independent_reconstruction(self):
        import random
        b=declarations()[0];fs=declared_features(b)
        for weights in ({},{'mode:small:bias':2},{'mode:hierarchy:area':-1,'mode:base:bias':1}):
            ss=[sum(weights.get(k,0)*v for k,v in f.items()) for f in fs];top=max(ss)
            i=random.Random(121000).choice([i for i,v in enumerate(ss) if v==top])
            row={'result':{'seed':121000},'features':fs,'scores':ss,'mode':MODES[i]}
            self.assertTrue(chosen_valid(row,b,weights));row['mode']=next(m for m in MODES if m!=row['mode'])
            self.assertFalse(chosen_valid(row,b,weights))
    def test_training_is_declared_and_fresh_policy_starts_empty(self):
        bs=training_boundaries(declarations()[0].allowed);self.assertEqual(len(bs),7)
        self.assertEqual(len({b.identity for b in bs}),7);self.assertEqual(dict(Policy().weights),{})

if __name__=='__main__':unittest.main()
