"""Request decisions must not create a second legality or proof system."""
import copy,sys,unittest
from unittest.mock import patch
import proposal_gate as G
import proposal_gate_search as S
import proposal_gate_cases as K
import quantifier_family_patterns as P
import check_proposal_gate as V
import run_proposal_gate as R

def original_tree(t):
    return {k:([{a:(original_tree(b) if a=='tree' else b) for a,b in child.items()} for child in value]
        if k=='children' else value) for k,value in t.items() if k!='gate_event'}

class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[];cls.known={}
        for i,s in enumerate(K.registry()[0]):
            c,r=R.run(s,cls.library,'fixed' if cls.library else 'base')
            added=P.promote(s,c,r,cls.library,maximum=6 if i==2 else 5)
            cls.library.extend(added);cls.known.update((t['name'],t) for t in added)
    def audit(self,s,r):
        rules,forms=V.A.A.inventory(s)
        return V.result(rules,dict(s,_formulas=forms),self.known,r)
    def test_defer_constructs_nothing_and_preserves_entire_base_tree(self):
        for s in K.registry()[1][:4]:
            _,base=R.run(s,self.library)
            with patch.object(S,'Join',side_effect=AssertionError('defer constructed an index')):
                _,off=R.run(s,self.library,'gated',gate_weights=[0.]*8)
            self.assertIsNone(off['index']);self.assertFalse(off['hints'])
            self.assertEqual(original_tree(off['search_tree']),base['search_tree'])
            self.assertEqual(off['placements'],base['placements']);self.assertEqual(off['metrics']['attempts'],base['metrics']['attempts'])
            self.audit(s,off)
    def test_always_query_preserves_entire_fixed_tree(self):
        for s in K.registry()[1][:4]:
            _,fixed=R.run(s,self.library,'fixed');_,on=R.run(s,self.library,'gated',gate_weights=[6.]+[0.]*7)
            self.assertEqual(original_tree(on['search_tree']),fixed['search_tree'])
            self.assertEqual(on['placements'],fixed['placements']);self.assertEqual(on['hints'],fixed['hints'])
            self.audit(s,on)
    def test_independent_replay_rejects_request_corruptions(self):
        s=K.registry()[1][0];_,r=R.run(s,self.library,'gated',gate_weights=[0.]*8,stochastic=True,seed=14300)
        for field,value in [('features',[0.]*8),('draw',-1.),('selected',3),('probabilities',[1.,0.]),('gradient',[99.]*8)]:
            bad=copy.deepcopy(r);bad['gate_events'][0][field]=value
            with self.assertRaises((ValueError,IndexError,KeyError)):self.audit(s,bad)
        bad=copy.deepcopy(r);del bad['search_tree']['gate_event']
        with self.assertRaises((ValueError,IndexError,KeyError)):self.audit(s,bad)
    def test_clock_reward_binding_and_update_algebra(self):
        s=K.registry()[1][0];_,r=R.run(s,self.library,'gated',gate_weights=[0.]*8,stochastic=True,seed=14300)
        after,b,u=G.update([0.]*8,0.,r);expected,eb=V.update([0.]*8,0.,r,u)
        V.V.close(after,expected);self.assertEqual(b,eb)
        u['observed_total_seconds']+=1
        with self.assertRaises(ValueError):V.update([0.]*8,0.,r,u)
    def test_scope_negative_and_budget_unknown_remain_distinct(self):
        s=K.registry()[1][6];_,r=R.run(s,self.library,'gated',gate_weights=[6.]+[0.]*7)
        self.assertEqual(r['status'],'exhausted_finite_region');self.audit(s,r)
        s=K.registry()[1][0];c=R.inventory(s);m=R.M.Model(c,s['target'],s['bound'],s['hypotheses'])
        r=S.search(m,self.library,'gated',gate_weights=[6.]+[0.]*7,attempts=1)
        self.assertEqual(r['status'],'unknown_search_budget');self.audit(s,r)

if __name__=='__main__':unittest.main()
