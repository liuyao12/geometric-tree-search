"""Policy derivatives, exact ordering/fallback and independent adversarial replay."""
import copy,math,random,unittest
import test_induction_clusters as Q
import induction_cluster_policy as R,audit_induction_cluster_policy as A
from audit_serialized_kernel import freeze

class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Q.MotifTests.setUpClass()
        cls.c=Q.MotifTests.tiny;cls.library=Q.MotifTests.tiny_library
        cls.source=Q.MotifTests.source;cls.source_library=Q.MotifTests.library
        cls.policy=R.initial_policy(cls.library)
    def pair(self,**kw):
        for fn,audit in ((R.point_search,A.point_run),(R.csp_search,A.csp_run)):
            r=fn(self.c,3,self.library,seconds=5,policy=self.policy,**kw)
            report=audit(freeze(self.c),3,freeze(r),freeze(self.library));yield r,report
    def nodes(self,t):
        yield t
        for child in t.get('children',[]):yield from self.nodes(child['tree'])
    def test_features_are_independently_exact_for_all_source_motifs(self):
        model=R.H.Model(self.source,7,self.source_library)
        for d in model.descriptions.values():
            if len(d['members'])<2:continue
            for filled in (set(),{0,1},{0,2,4,6}):
                x=R.feature_vector(self.source,7,d['members'],filled)
                self.assertEqual(x,A.features(freeze(self.source),7,d['members'],filled));self.assertTrue(all(0<=k<=1024 for k in x))
    def test_no_formula_literals_or_variable_labels_in_features(self):
        c=copy.deepcopy(self.source);c['formulas']=['opaque' for f in c['formulas']]
        model=R.H.Model(self.source,7,self.source_library)
        d=next(d for d in model.descriptions.values() if len(d['members'])>1)
        self.assertEqual(R.feature_vector(c,7,d['members'],{0}),R.feature_vector(self.source,7,d['members'],{0}))
    def test_zero_policy_equals_fixed_complete_search_prefix(self):
        for fn,old in ((R.point_search,R.H.search),(R.csp_search,R.H.csp_search)):
            a=fn(self.c,3,self.library,policy=self.policy,seconds=5);b=old(self.c,3,self.library,seconds=5)
            def strip(t):return {k:strip(v) if isinstance(v,dict) else [strip(x) if isinstance(x,dict) else x for x in v] if isinstance(v,list) else v for k,v in t.items() if k!='policy'}
            self.assertEqual(strip(a['search_tree']),strip(b['search_tree']));self.assertEqual(a['placements'],b['placements'])
    def test_full_fallback_succeeds_even_with_adverse_integer_scores(self):
        for j in range(len(R.FEATURES)):
            p=copy.deepcopy(self.policy);p['weights'][j]=-2000000
            for fn in (R.point_search,R.csp_search):
                r=fn(self.c,3,self.library,policy=p,seconds=5)
                self.assertEqual(r['status'],'finite_exact_proof_tiling')
    def test_stochastic_permutations_and_all_expanded_attempts_replay(self):
        for seed in (0,1,17):
            for r,report in self.pair(stochastic=True,seed=seed):
                self.assertTrue(report['exact_solution']);self.assertGreater(r['policy_work']['sampled_draws'],0)
    def test_softmax_score_gradient_matches_finite_difference(self):
        f={0:tuple(range(11)),1:tuple(1024-3*j for j in range(11)),2:tuple(50*j for j in range(11))}
        p=copy.deepcopy(self.policy);p['weights']=[10000*j for j in range(11)]
        order,details,grads=R.ordered([0,1,2],f,p,True,random.Random(41));chosen=order[0]
        for j in range(11):
            lo=copy.deepcopy(p);hi=copy.deepcopy(p);lo['weights'][j]-=1;hi['weights'][j]+=1
            derivative=(math.log(R.probabilities([0,1,2],f,hi)[chosen])-math.log(R.probabilities([0,1,2],f,lo)[chosen]))/(2/1000000)
            self.assertAlmostEqual(derivative,grads[chosen][j],places=7)
    def test_exact_greedy_ranking_and_stable_zero_ties(self):
        f={0:(1024,)+(0,)*10,1:(0,)*11,2:(512,)+(0,)*10};p=copy.deepcopy(self.policy);p['weights'][0]=1
        self.assertEqual(R.ordered([1,2,0],f,p,False,None)[0],[0,2,1]);p['weights'][0]=0
        self.assertEqual(R.ordered([1,2,0],f,p,False,None)[0],[1,2,0])
    def test_attempt_cutoff_has_no_unexecuted_gradient_credit(self):
        for r,_ in self.pair(stochastic=True,seed=1,attempt_limit=0):
            self.assertEqual(r['status'],'unknown_search_budget');self.assertEqual(r['executed_score_gradients'],[])
    def test_wall_cutoff_remains_unknown_in_both_encodings(self):
        for fn,audit in ((R.point_search,A.point_run),(R.csp_search,A.csp_run)):
            r=fn(self.c,3,self.library,seconds=0,policy=self.policy,stochastic=True)
            self.assertEqual(r['status'],'unknown_search_budget');audit(freeze(self.c),3,freeze(r),freeze(self.library))
    def test_sampling_without_policy_or_foreign_library_is_rejected(self):
        with self.assertRaises(ValueError):R.point_search(self.c,3,self.library,stochastic=True)
        p=copy.deepcopy(self.policy);p['library_sha256']='0'*64
        with self.assertRaises(ValueError):R.csp_search(self.c,3,self.library,policy=p)
        p=copy.deepcopy(self.policy);p['weights'][0]=True
        with self.assertRaises(ValueError):R.point_search(self.c,3,self.library,policy=p)
    def test_mutated_draw_order_or_features_are_rejected(self):
        for fn,audit in ((R.point_search,A.point_run),(R.csp_search,A.csp_run)):
            r=fn(self.c,3,self.library,seconds=5,policy=self.policy,stochastic=True,seed=9)
            for mutation in ('draw','order','features'):
                bad=copy.deepcopy(r);t=next(t for t in self.nodes(bad['search_tree']) if t.get('policy',{}).get('order'))
                if mutation=='draw':t['policy']['draws'][0]=0.0
                elif mutation=='order':t['policy']['order'][0]=-1
                else:t['policy']['features_sha256']='0'*64
                with self.assertRaises(ValueError):audit(freeze(self.c),3,freeze(bad),freeze(self.library))
    def test_mutated_gradient_and_hidden_proposal_are_rejected(self):
        for fn,audit in ((R.point_search,A.point_run),(R.csp_search,A.csp_run)):
            r=fn(self.c,3,self.library,seconds=5,policy=self.policy,stochastic=True)
            for field in ('gradient','count'):
                bad=copy.deepcopy(r)
                if field=='gradient':bad['executed_score_gradients'][0][0]+=0.25
                else:bad['policy_work']['feature_evaluations']+=1
                with self.assertRaises(ValueError):audit(freeze(self.c),3,freeze(bad),freeze(self.library))
    def test_episode_update_replays_reward_and_each_parameter(self):
        r=R.point_search(self.c,3,self.library,seconds=5,policy=self.policy,stochastic=True,seed=3)
        after,record=R.update(self.policy,r);independent=A.update(freeze(self.policy),freeze(r),freeze(record))
        self.assertEqual(freeze(after),freeze(independent));self.assertTrue(all(type(w) is int for w in after['weights']))
        for field in ('reward','weight','event'):
            bad=copy.deepcopy(record)
            if field=='reward':bad['reward']+=0.1
            elif field=='weight':bad['after_weights'][0]+=1
            else:bad['events']+=1
            with self.assertRaises(ValueError):A.update(freeze(self.policy),freeze(r),freeze(bad))
    def test_fixed_controls_have_no_imported_policy_or_gradient(self):
        for fn,audit in ((R.point_search,A.point_run),(R.csp_search,A.csp_run)):
            r=fn(self.c,3,self.library,seconds=5)
            self.assertIsNone(r['policy']);self.assertEqual(r['executed_score_gradients'],[])
            audit(freeze(self.c),3,freeze(r),freeze(self.library))

if __name__=='__main__':unittest.main(verbosity=2)
