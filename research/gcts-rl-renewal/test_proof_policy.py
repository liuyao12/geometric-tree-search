import copy,math,json,unittest
import proof_cluster_policy as R,proof_clusters as H,proof_policy_problems as P
import semantic_proof_catalogs as C,semantic_proof_tiles as S
import audit_semantic_proofs as A
from turtle import Graph
from serialized_kernel import canonical,problem_hash

class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);cls.library+=H.promote(c,r,p['length'],cls.library,p['id'])['templates']
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound'])
    def run_search(self,policy=None,**kw):return R.search(self.c,self.p['length'],self.library,policy=policy,**kw)
    def test_zero_weights_and_no_imported_policy(self):self.assertEqual(R.Policy().weights,[0.0]*len(R.FEATURES))
    def test_zero_softmax_uniform_and_normalized(self):
        p=R.softmax([0]*3,[[1,2,0],[0,0,1],[0,1,1]]);self.assertEqual(p,[1/3]*3)
    def test_softmax_gradient_by_finite_difference(self):
        weights=[.2,-.1,.3];fs=[[1,.5,0],[0,1,.7],[-.2,0,1]];prob=R.softmax(weights,fs);gradient=[fs[1][k]-sum(p*f[k] for p,f in zip(prob,fs)) for k in range(3)]
        for k,g in enumerate(gradient):
            a=list(weights);b=list(weights);a[k]+=1e-6;b[k]-=1e-6;numeric=(math.log(R.softmax(a,fs)[1])-math.log(R.softmax(b,fs)[1]))/2e-6;self.assertAlmostEqual(numeric,g,places=8)
    def test_declared_random_stream(self):
        r=R.Random(1);self.assertEqual(r.draw(),(1015568748+.5)/2**32);self.assertEqual(r.draw(),(1586005467+.5)/2**32)
    def test_weights_are_frozen_during_search(self):
        policy=R.Policy(weights=[.1]*len(R.FEATURES));before=list(policy.weights);r=self.run_search(policy);self.assertEqual(policy.weights,before);self.assertEqual(r['policy_weights'],before)
    def test_fixed_prior_matches_frozen_historical_search(self):
        a=self.run_search();b=H.search(self.c,self.p['length'],self.library)
        for k in ('placements','nodes','base_attempts','samples','solution_transactions','search_tree'):self.assertEqual(a[k],b[k])
    def test_empty_library_matches_plain_reference(self):
        a=R.search(self.c,self.p['length']);b=H.search(self.c,self.p['length'])
        for k in ('placements','nodes','base_attempts','samples'):self.assertEqual(a[k],b[k])
    def test_deferral_preserves_complete_base_fallback(self):
        weights=[-6.0]*len(R.FEATURES);weights[0]=6;weights[3]=6;r=self.run_search(R.Policy(weights=weights));base=H.search(self.c,self.p['length']);self.assertFalse(r['solution_transactions']);self.assertEqual(r['placements'],base['placements']);self.assertEqual(r['nodes'],base['nodes'])
    def test_features_and_policy_do_not_mutate_domains(self):
        m=S.Model(self.c,self.p['length']);s=m.initial();g=Graph(m,s);kind,p,keys=g.decision(s);g.update(m,s,s.place(m.placement(keys[0])));kind,p,keys=g.decision(s);items,_=H.Index(self.c,self.p['length'],self.library).offered(m,s,g,p,None);before=(copy.deepcopy(s),g.fingerprint());R.Policy().choose(m,s,g,p,items);self.assertEqual(s,before[0]);self.assertEqual(g.fingerprint(),before[1])
    def test_all_policy_members_remain_base_candidates(self):
        r=self.run_search(R.Policy());m=S.Model(self.c,self.p['length'])
        for trial in r['transaction_samples']:
            for key in trial['item']['members']:self.assertIn(key,m.cache)
    def test_attempt_cutoff_stays_unknown(self):
        r=self.run_search(R.Policy(),attempt_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['search_tree']);self.assertEqual(r['base_attempts'],0)
    def test_unknown_training_has_no_parameter_or_baseline_update(self):
        r=self.run_search(R.Policy(),attempt_limit=0);w=[.3]*len(R.FEATURES);u=R.update(w,.4,r,None);self.assertFalse(u['updated']);self.assertEqual(u['weights_after'],w);self.assertEqual(u['baseline_after'],.4);self.assertFalse(u['credits'])
    def test_unreached_sampled_suffix_cannot_receive_credit(self):
        r=self.run_search(R.Policy(seed=1,stochastic=True));self.assertEqual(len(r['policy_events'][0]['draws']),2);a=R.update(r['policy_weights'],0,r,{'status':'accepted'});bad=copy.deepcopy(r);bad['policy_events'][0]['draws'][1]['gradient']=[1000000]*len(R.FEATURES);b=R.update(r['policy_weights'],0,bad,{'status':'accepted'});self.assertEqual(a['weights_after'],b['weights_after']);self.assertEqual(len(a['credits']),1)
    def test_credit_requires_full_native_acceptance(self):
        r=self.run_search(R.Policy());credits=R.branch_returns(r,{'status':'unknown'});self.assertTrue(credits);self.assertTrue(all(not x['verified_continuation'] and x['value']<=0 for x in credits))
    def test_credit_recounts_all_actual_base_attempts(self):
        r=self.run_search(R.Policy());bad=copy.deepcopy(r);bad['base_attempts']+=1
        with self.assertRaises(ValueError):R.branch_returns(bad,{'status':'accepted'})
    def test_training_and_evaluation_statements_are_disjoint(self):
        def pins(ps):return {problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target'])) for p in ps}
        self.assertFalse(pins(P.training())&pins(P.evaluation()));self.assertEqual(len(P.training()),8)
    def test_freeze_evaluation_does_not_consume_random_stream(self):
        policy=R.Policy(seed=19);self.run_search(policy);self.assertEqual(policy.random.state,19);self.assertTrue(all(d['uniform'] is None for e in policy.events for d in e['draws']))
    def test_stochastic_draws_are_reproducible(self):
        a=self.run_search(R.Policy(seed=7,stochastic=True));b=self.run_search(R.Policy(seed=7,stochastic=True));self.assertEqual(a['policy_events'],b['policy_events']);self.assertEqual(a['placements'],b['placements'])
    def test_zero_proposal_cap_preserves_base_search(self):
        r=self.run_search(R.Policy(limit=0),proposal_limit=0);b=H.search(self.c,self.p['length']);self.assertEqual(r['nodes'],b['nodes']);self.assertFalse(r['solution_transactions'])
    def test_index_truncation_never_claims_incomplete_base_domain(self):
        r=self.run_search(R.Policy(),index_limit=0);self.assertFalse(r['index_complete']);self.assertEqual(r['status'],'finite_exact_proof_tiling');self.assertFalse(r['solution_transactions'])
    def test_nonfinite_or_wrong_dimension_weights_reject(self):
        for w in ([0],[float('nan')]*len(R.FEATURES),[float('inf')]*len(R.FEATURES)):
            with self.assertRaises(ValueError):R.Policy(weights=w)
    def test_projected_update_stays_finite_within_bounds(self):
        r=self.run_search(R.Policy(seed=1,stochastic=True));u=R.update(r['policy_weights'],0,r,{'status':'accepted'},rate=10000);self.assertTrue(all(math.isfinite(w) and -6<=w<=6 for w in u['weights_after']))
    def test_policy_episode_controller_must_be_fresh(self):
        p=R.Policy();self.run_search(p)
        with self.assertRaises(ValueError):self.run_search(p)
    def test_found_hierarchy_expands_under_unchanged_problem(self):
        r=self.run_search(R.Policy());h=H.hierarchical_certificate(self.c,r,self.p['length'],self.library);self.assertEqual(A.whole_replay(json.loads(canonical(h['request'])),problem_hash(r['decoded']['request']))['status'],'accepted')

if __name__=='__main__':unittest.main()
