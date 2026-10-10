"""Policy feedback cannot change proof legality, propagation or fallback."""
import copy,unittest
from unittest.mock import patch
import family_router as P
import family_router_cases as K
import run_family_router as R
import check_family_router as C
import audit_quantifier_families as Old
import quantifier_family_search as Search
import quantifier_family_patterns as Patterns

class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for i,s in enumerate(K.registry()[0]):
            cat,r=R.run(s,cls.library,'fixed' if cls.library else 'base');cls.library.extend(Patterns.promote(s,cat,r,cls.library,maximum=6 if i==2 else 5))
    def context(self,s):
        cat=R.inventory(s);m=R.M.Model(cat,s['target'],s['bound'],s['hypotheses']);st=m.initial()
        return cat,P.context(m,st,R.M.Graph(m,st))
    def test_complete_initial_context_and_name_independence(self):
        for s in K.registry()[1]+K.registry()[2][-3:]:
            cat,c=self.context(s);rules,ss=Old.grammar(dict(spec=s,catalog=cat));q=C.context(rules,ss)
            C.V.V.close(c['features'],q['features']);self.assertEqual(c['point'],q['point']);self.assertEqual(c['kind'],q['kind'])
        from quantifier_family_cases import case
        self.assertEqual(self.context(case('x'))[1],self.context(case('a-long-name-with-different-symbol-spellings'))[1])
    def test_zero_route_builds_no_index_and_preserves_full_base_tree(self):
        s=K.registry()[1][0];_,c=self.context(s);p=dict(centers=[c['features']],weights=[1.],bandwidth=.03)
        _,base=R.run(s,self.library)
        with patch.object(Search,'Join',side_effect=AssertionError('zero requested a family')):_,off=R.run(s,self.library,'zero',p)
        self.assertEqual(off['search_tree'],base['search_tree']);self.assertEqual(off['placements'],base['placements']);self.assertIsNone(off['index'])
    def test_positive_route_preserves_full_fixed_controller(self):
        s=K.registry()[1][0];_,c=self.context(s);p=dict(centers=[c['features']],weights=[1.],bandwidth=.03)
        _,fixed=R.run(s,self.library,'fixed');_,on=R.run(s,self.library,'router',p)
        self.assertEqual(on['search_tree'],fixed['search_tree']);self.assertEqual(on['hints'],fixed['hints']);self.assertEqual(on['placements'],fixed['placements'])
    def test_feedback_can_learn_both_actions_from_zero(self):
        contexts=[dict(features=[0.]*8),dict(features=[1.]*8)];p=P.fit(contexts,[[.2,.4],[.4,.2]])
        self.assertEqual(p['training_decisions'],[1,0]);self.assertEqual(p['initial_weights'],[0.,0.])
        # The independent update checks the full observed-return gradient.
        u=p['selection']['candidates'][0]['updates'][0]
        C.step([0.,0.],contexts[0]['features'],p['centers'],[.2,.4],.03,u)
        bad=copy.deepcopy(u);bad['weights_after'][0]+=1
        with self.assertRaises(ValueError):C.step([0.,0.],contexts[0]['features'],p['centers'],[.2,.4],.03,bad)
    def test_router_dimensions_and_selected_action_are_checked(self):
        x=[0.]*8;event=P.decision(x,[x],[1.],.03)
        C.decision(x,[x],[1.],.03,event)
        event['selected']=0
        with self.assertRaises(ValueError):C.decision(x,[x],[1.],.03,event)
        with self.assertRaises(ValueError):P.decision(x,[x[:-1]],[1.],.03)
if __name__=='__main__':unittest.main()
