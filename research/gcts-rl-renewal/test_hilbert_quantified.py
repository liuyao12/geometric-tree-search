"""Quantifier scope and capture-avoidance regressions for new productions."""
import unittest
import logic as L
import quantified_proof_rules as Q
import hilbert_incidence_tiles as F
import hilbert_quantified_tiles as B
from serialized_kernel import canonical,check
from audit_serialized_kernel import replay
class QuantifiedTests(unittest.TestCase):
    def probe(self,theory,blocks):
        r=('pred',next(iter(theory['predicates'])),tuple(L.V('z'+str(i)) for i in range(next(iter(theory['predicates'].values())))))
        a=L.Imp(r,r);payload=canonical(dict(protocol='gcts-fol-1',theory=theory,target=a,blocks=blocks,proof=[dict(rule='tautology',formula=a)]))
        self.assertEqual(check(payload,max_work=None)['status'],'accepted');self.assertEqual(replay(payload)['status'],'accepted')
    def test_generic_quantified_blocks(self):
        p=('pred','P',(L.V('x'),));g=('pred','G',());r=('pred','R',())
        bs=[Q.exists_intro(g,'x',p,L.V('w')),Q.exists_eliminate(g,'x',p,r),Q.forall_scope(g,'x',p,r),Q.forall_distribute(g,'x',p),Q.forall_instantiate(g,'x',p,L.V('w'))]
        self.probe(dict(functions={},predicates={'P':1,'G':0,'R':0},axioms={},schemas=[]),bs)
    def test_eigenvariable_cannot_escape(self):
        p=('pred','P',(L.V('x'),));g=('pred','G',())
        with self.assertRaises(ValueError):Q.exists_eliminate(g,'x',p,p)
        with self.assertRaises(ValueError):Q.exists_eliminate(p,'x',p,g)
        with self.assertRaises(ValueError):Q.forall_scope(p,'x',p,g)
    def test_hygienic_outer_grounding(self):
        theory,metadata=F.foundation();rows,_=B.instances(theory,metadata,dict(point=['p0','p1'],line=['l0','l1']))
        selected=next(r for r in rows if r['axiom']=='I.2-uniqueness' and list(r['bindings'].values())==['p1','p0','l1','l0'] and r['head']==0)
        # Simultaneous role assignment is recovered by sequential CURRENT
        # binders, despite capture renaming of the later bound role.
        self.assertEqual(selected['instance'][2],L.Eq(L.V('l1'),L.V('l0')))
        self.probe(theory,[B.source_block(theory,selected,F.pred('Line','u'))])
    def test_reject_generalization_with_free_input(self):
        p=('pred','P',(L.V('x'),));theory=dict(functions={},predicates={'P':1},axioms={},schemas=[])
        b=dict(name='bad',premises=[p],conclusion=L.All('x',p),proof=[dict(rule='assumption',formula=p,index=0),dict(rule='generalize',formula=L.All('x',p),variable='x',source=0)])
        a=L.Imp(p,p);payload=canonical(dict(protocol='gcts-fol-1',theory=theory,target=a,blocks=[b],proof=[dict(rule='tautology',formula=a)]))
        self.assertEqual(check(payload,max_work=None)['status'],'rejected');self.assertEqual(replay(payload)['status'],'rejected')
if __name__=='__main__':unittest.main()
