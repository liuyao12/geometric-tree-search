import copy,unittest
import partial_proof_policy as N,proof_clusters as H,proof_policy_problems as P
import semantic_proof_catalogs as C
import audit_partial_proof_policy as V
from audit_serialized_kernel import freeze

class PartialAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);cls.library+=H.promote(c,r,p['length'],cls.library,p['id'])['templates']
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound']);cls.r=N.search(cls.c,3,cls.library,policy=N.Policy(),attempt_limit=2)
    def replay(self,r):return V.replay(freeze(self.c),3,freeze(r),freeze(self.library),[0]*12,1,False)
    def test_partial_prefix_independently_replays(self):self.assertEqual(self.replay(self.r)['open_suffixes'],1)
    def test_missing_partial_tree_rejects(self):
        r=copy.deepcopy(self.r);r['partial_tree']=None
        with self.assertRaises(ValueError):self.replay(r)
    def test_unknown_cannot_be_relabelled_exhausted(self):
        r=copy.deepcopy(self.r);r['status']='exhausted_finite_proof_envelope'
        with self.assertRaises(ValueError):self.replay(r)
    def test_unknown_cannot_be_relabelled_proved(self):
        r=copy.deepcopy(self.r);r['status']='finite_exact_proof_tiling'
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_viability_rejects(self):
        r=copy.deepcopy(self.r);r['partial_tree']['viable']=False
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_occupancy_rejects(self):
        r=copy.deepcopy(self.r);r['partial_tree']['depth']+=1
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_transaction_step_rejects(self):
        r=copy.deepcopy(self.r);r['partial_tree']['children'][0]['tree']['proposals'][0]['trace']['steps'][0]['role']='global_forced'
        with self.assertRaises(ValueError):self.replay(r)
    def test_missing_executed_step_rejects(self):
        r=copy.deepcopy(self.r);r['partial_tree']['children'][0]['tree']['proposals'][0]['trace']['steps']=[]
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_counter_rejects(self):
        r=copy.deepcopy(self.r);r['stats']['validation_placements']+=1
        with self.assertRaises(ValueError):self.replay(r)
    def test_independent_local_update(self):
        u=N.update([0]*12,0,self.r,None,3);w,b=V.update_audit([0]*12,0,freeze(self.r),None,3,freeze(u),'local');self.assertEqual(w,u['weights_after']);self.assertEqual(b,u['baseline_after'])
    def test_tampered_progress_return_rejects(self):
        u=N.update([0]*12,0,self.r,None,3);u['credits'][0]['viable_gain']+=1
        with self.assertRaises(ValueError):V.update_audit([0]*12,0,freeze(self.r),None,3,freeze(u),'local')
    def test_tampered_weight_rejects(self):
        u=N.update([0]*12,0,self.r,None,3);u['weights_after'][0]+=.01
        with self.assertRaises(ValueError):V.update_audit([0]*12,0,freeze(self.r),None,3,freeze(u),'local')
    def test_tampered_theorem_bonus_rejects(self):
        u=N.update([0]*12,0,self.r,None,3);u['credits'][0]['verified_continuation']=True
        with self.assertRaises(ValueError):V.update_audit([0]*12,0,freeze(self.r),None,3,freeze(u),'local')

if __name__=='__main__':unittest.main()
