import copy,unittest
import proof_cluster_policy as R,proof_clusters as H,proof_policy_problems as P
import semantic_proof_catalogs as C
import audit_proof_policy as B,audit_proof_clusters as G
from audit_serialized_kernel import freeze

class PolicyAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);cls.library+=H.promote(c,r,p['length'],cls.library,p['id'])['templates']
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound']);cls.r=R.search(cls.c,cls.p['length'],cls.library,policy=R.Policy(seed=1,stochastic=True))
    def replay(self,r=None):
        return B.run(freeze(self.c),self.p['length'],freeze(r or self.r),freeze(self.library),[0.0]*len(R.FEATURES),1,True)
    def test_full_policy_and_tree_replay(self):self.assertTrue(self.replay()['solved'])
    def test_tampered_uniform_draw_rejects(self):
        r=copy.deepcopy(self.r);r['policy_events'][0]['draws'][0]['uniform']+=.01
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_feature_gradient_rejects(self):
        r=copy.deepcopy(self.r);r['policy_events'][0]['draws'][0]['gradient'][0]+=.01
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_pool_binding_rejects(self):
        r=copy.deepcopy(self.r);r['policy_events'][0]['pool_sha256']='0'*64
        with self.assertRaises(ValueError):self.replay(r)
    def test_tampered_tree_event_rejects(self):
        r=copy.deepcopy(self.r);r['search_tree']['children'][0]['tree']['policy_event']=7
        with self.assertRaises(ValueError):self.replay(r)
    def test_independent_update_chain(self):
        r=freeze(self.r);u=R.update([0.0]*len(R.FEATURES),0,self.r,{'status':'accepted'});w,b=B.update_audit([0.0]*len(R.FEATURES),0,r,{'status':'accepted'},freeze(u));self.assertEqual(w,u['weights_after']);self.assertEqual(b,u['baseline_after'])
    def test_tampered_delayed_return_rejects(self):
        u=R.update([0.0]*len(R.FEATURES),0,self.r,{'status':'accepted'});u['credits'][0]['base_attempts']+=1
        with self.assertRaises(ValueError):B.update_audit([0.0]*len(R.FEATURES),0,freeze(self.r),{'status':'accepted'},freeze(u))
    def test_tampered_projected_update_rejects(self):
        u=R.update([0.0]*len(R.FEATURES),0,self.r,{'status':'accepted'});u['weights_after'][0]+=.1
        with self.assertRaises(ValueError):B.update_audit([0.0]*len(R.FEATURES),0,freeze(self.r),{'status':'accepted'},freeze(u))
    def test_external_training_declarations_are_independent(self):
        expected=B.external_training()
        for p in P.training():self.assertTrue(all(freeze(p[k])==freeze(v) for k,v in expected[p['id']].items()))

if __name__=='__main__':unittest.main()
