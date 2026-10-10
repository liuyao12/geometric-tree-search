import copy,unittest
import partial_proof_policy as N,proof_cluster_policy as R,proof_clusters as H,proof_policy_problems as P
import semantic_proof_catalogs as C
import audit_partial_proof_policy as V
from audit_serialized_kernel import freeze

class PartialPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);cls.library+=H.promote(c,r,p['length'],cls.library,p['id'])['templates']
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound'])
    def search(self,limit=50000,weights=None,seconds=5):return N.search(self.c,self.p['length'],self.library,policy=N.Policy(weights=weights),attempt_limit=limit,seconds=seconds)
    def audit(self,r):return V.replay(freeze(self.c),self.p['length'],freeze(r),freeze(self.library),r['policy_weights'],1,False)
    def test_complete_trace_matches_frozen_search(self):
        a=self.search();b=R.search(self.c,self.p['length'],self.library,policy=R.Policy())
        for k in ('placements','nodes','base_attempts','policy_events','solution_transactions'):self.assertEqual(a[k],b[k])
        self.assertIsNone(a['partial_tree']);self.assertTrue(self.audit(a)['solved'])
    def test_complete_reward_matches_control(self):
        a=self.search();b=R.search(self.c,self.p['length'],self.library,policy=R.Policy());native={'status':'accepted'}
        self.assertEqual(N.update([0]*12,0,a,native,3,'complete'),R.update([0]*12,0,b,native))
    def test_untouched_attempt_cutoff_remains_unknown(self):
        r=self.search(limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['search_tree']);self.assertNotIn('decoded',r);self.assertEqual(self.audit(r)['open_suffixes'],1)
    def test_wall_cutoff_is_explicit_entry(self):
        r=self.search(seconds=0);self.assertEqual(r['partial_tree']['kind'],'cutoff');self.assertEqual(r['base_attempts'],0);self.assertEqual(self.audit(r)['open_suffixes'],1)
    def test_interrupt_inside_transaction_rolls_back(self):
        r=self.search(limit=2);report=self.audit(r);self.assertEqual(report['base_attempts'],2);self.assertEqual(report['open_suffixes'],1)
        tr=r['partial_tree']['children'][0]['tree']['proposals'][0]['trace'];self.assertEqual(tr['status'],'unknown_transaction_budget');self.assertEqual(len(tr['steps']),1)
        credit=N.local_returns(r,None,3)[0];self.assertEqual(credit['viable_gain'],0);self.assertEqual(credit['base_attempts'],1);self.assertFalse(credit['verified_continuation'])
    def test_zero_step_interruption_has_no_credit(self):
        r=self.search(limit=1);self.audit(r);self.assertEqual(N.local_returns(r,None,3),[])
    def test_local_can_update_unknown_without_positive_theorem_label(self):
        r=self.search(limit=2);u=N.update([0]*12,0,r,None,3);self.assertTrue(u['updated']);self.assertNotEqual(u['weights_after'],[0]*12);self.assertTrue(all(not x['verified_continuation'] for x in u['credits']));self.assertEqual(r['status'],'unknown_search_budget')
    def test_complete_control_discards_unknown_credit(self):
        r=self.search(limit=2);u=N.update([0]*12,.4,r,None,3,'complete');self.assertFalse(u['updated']);self.assertEqual(u['weights_after'],[0]*12);self.assertEqual(u['baseline_after'],.4)
    def test_deferral_progress_counts_viable_base_states(self):
        r=self.search(limit=2,weights=[5]+[0]*11);self.audit(r);credit=N.local_returns(r,None,3)[0];self.assertEqual(credit['action_status'],'base_fallback');self.assertEqual(credit['base_attempts'],1);self.assertGreaterEqual(credit['viable_gain'],0)
    def test_unreached_sampled_suffix_is_censored(self):
        r=self.search();credits=N.local_returns(r,{'status':'accepted'},3);self.assertEqual(len(credits),1);self.assertEqual(credits[0]['draw'],0)
    def test_terminal_bonus_requires_native_acceptance(self):
        r=self.search();a=N.local_returns(r,None,3);b=N.local_returns(r,{'status':'accepted'},3);self.assertAlmostEqual(b[0]['value']-a[0]['value'],1);self.assertFalse(a[0]['verified_continuation'])
    def test_full_observed_work_required(self):
        r=self.search(limit=2);r['base_attempts']+=1
        with self.assertRaises(ValueError):N.local_returns(r,None,3)
    def test_both_signals_use_same_frozen_feature_vector(self):self.assertIs(N.Policy,R.Policy);self.assertEqual(N.FEATURES,R.FEATURES)
    def test_empty_library_retains_base_fallback(self):
        a=N.search(self.c,3);b=R.search(self.c,3)
        self.assertEqual((a['nodes'],a['base_attempts'],a['placements']),(b['nodes'],b['base_attempts'],b['placements']))
    def test_invalid_signal_rejects(self):
        with self.assertRaises(ValueError):N.update([0]*12,0,self.search(),None,3,'invalid')

if __name__=='__main__':unittest.main()
