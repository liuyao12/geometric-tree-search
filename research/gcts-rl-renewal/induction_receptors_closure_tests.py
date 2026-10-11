"""Scope tests for the separate generic closure infrastructure."""
import copy,unittest
from induction_receptors_closure import close_ground,expand,eigen_close
from audit_semantic_proofs import whole_replay

class Closure(unittest.TestCase):
    def fixture(self):
        a=['fun','a',[]];p=['pred','P',[a]];eq=['eq',a,a]
        return dict(protocol='gcts-fol-1',theory=dict(functions=dict(a=0),predicates=dict(P=1),axioms=dict(given=p),schemas=[]),blocks=[],proof=[dict(rule='refl',formula=eq)],target=eq)
    def test_unneeded_hypothesis_still_discharged(self):
        r=close_ground(self.fixture(),['given'],['a'])
        self.assertEqual(whole_replay(r['request'])['status'],'accepted')
        self.assertEqual(r['request']['theory']['axioms'],{})
        self.assertEqual(r['request']['target'][0],'all')
    def test_constant_in_retained_axiom_is_not_an_eigenvariable(self):
        r=self.fixture()
        self.assertRaises(ValueError,eigen_close,r,['a'])
    def test_fresh_bound_variable_names(self):
        r=self.fixture();r['proof'][0]['formula']=['all','eigen0',r['target']]
        # The renamer is syntactic; native rule validity remains a separate gate.
        r['target']=r['proof'][0]['formula'];r['theory']['axioms']={}
        q,b=eigen_close(r,['a']);self.assertEqual(b['a'],'eigen1')
        self.assertEqual(q['target'][1],'eigen1')
    def test_bad_local_source_cannot_alias_python_negative_index(self):
        r=self.fixture();eq=r['target'];d=dict(name='copy',premises=[eq],conclusion=eq,proof=[dict(rule='assumption',formula=eq,index=0)])
        r['blocks']=[d];r['proof'].append(dict(rule='block',formula=eq,name='copy',inputs=[-1]))
        self.assertRaises(ValueError,expand,r)

if __name__=='__main__':unittest.main()
