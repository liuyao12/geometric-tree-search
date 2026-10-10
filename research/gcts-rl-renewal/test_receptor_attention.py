import copy
import random
import unittest
import receptor_attention as P
import receptor_attention_search as S
import check_receptor_attention as V
from quantifier_family_cases import case
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate
import quantifier_family_patterns as QP
import movable_proof_regions as M

def run(spec,library=(),weights=None,stochastic=False,seed=0):
    cat=inventory(spec);model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    r=S.search(model,library,'policy' if weights is not None else 'base',weights,stochastic,seed)
    decorate(spec,cat,r);r['total_seconds']=r['seconds']+r.get('positive_check_seconds',0)+.001
    return cat,model,r

class TestAttention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donor=case('quantifier-donor-one');c,m,r=run(cls.donor)
        cls.library=QP.promote(cls.donor,c,r,maximum=5)

    def audit(self,spec,cat,r):
        _,forms=V.V.A.A.inventory(spec)
        return V.result(cat['rules'],dict(spec,_formulas=forms),{t['name']:t for t in self.library},r)

    def test_renaming_invariance_and_exact_support(self):
        vectors=[]
        for name in ('alpha','different-name'):
            s=case(name);c,m,r=run(s,self.library,[0.]*12)
            self.audit(s,c,r);vectors.append([e['features'] for e in r['policy_events']])
        self.assertEqual(vectors[0],vectors[1])

    def test_zero_full_base_fallback(self):
        spec=case('zero');cat,_,r=run(spec,self.library,[0.]*12)
        _,_,base=run(spec)
        self.assertEqual(r['placements'],base['placements'])
        self.assertFalse(r['hints']);self.assertTrue(all(e['selected']==0 for e in r['policy_events']))
        self.audit(spec,cat,r)

    def test_sampled_choices_and_independent_rejection(self):
        spec=case('sampled');cat,_,r=run(spec,self.library,[0.]*12,True,55)
        self.audit(spec,cat,r)
        for key in ('scores','probabilities','gradient','features'):
            bad=copy.deepcopy(r);e=next(e for e in bad['policy_events'] if e['items'])
            if key=='features':e[key][0]=[9.]*12
            else:e[key][0]+=1
            with self.assertRaises(ValueError):self.audit(spec,cat,bad)
        bad=copy.deepcopy(r);bad['attention_support']['distances']=[]
        with self.assertRaises(ValueError):self.audit(spec,cat,bad)

    def test_on_policy_update_uses_sum_and_cost(self):
        spec=case('update');cat,_,r=run(spec,self.library,[0.]*12,True,58)
        self.audit(spec,cat,r);after,baseline,u=P.update([0.]*12,.5,r)
        self.assertEqual((after,baseline),V.update([0.]*12,.5,r,u))
        bad=copy.deepcopy(u);bad['reward']+=.01
        with self.assertRaises(ValueError):V.update([0.]*12,.5,r,bad)

    def test_scoring_never_changes_point_values(self):
        spec=case('marks');cat,m,_=run(spec)
        state=m.initial();g=M.Graph(m,state);before=(state.copy(),g.fingerprint())
        support=P.Support(m);P.choose([],support,state,g,[0.]*12,True,random.Random(1))
        self.assertEqual(state,before[0]);self.assertEqual(g.fingerprint(),before[1])
        a,b=g.decision(state),M.Graph(m,state).decision(state)
        self.assertEqual((a[0],a[1],tuple(a[2])),(b[0],b[1],tuple(b[2])))
        templates={t['name']:t for t in self.library}
        self.assertEqual(V.deferral_bound([0.]*12,templates)['status'],'not_certified')
        weights=[0.]*12;weights[0]=-1.;weights[-1]=1.
        bound=V.deferral_bound(weights,templates)
        self.assertEqual(bound['status'],'certified_always_defer')
        self.assertEqual(bound['strict_margin'],2.)

if __name__=='__main__':unittest.main()
