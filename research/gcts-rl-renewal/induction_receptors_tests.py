"""Fixtures test transforms and scope. No arithmetic target is searched here."""
import copy,itertools,unittest
import logic as L
from induction_receptors_catalog import Proof,deduce,freeze,term_grammar,catalog
from serialized_kernel import check,canonical
from induction_receptors_points import Model
from turtle import Graph
from audit_semantic_inventory import LiteralDomains,legal,advance

class InductionReceptors(unittest.TestCase):
    def test_complete_term_counts(self):
        ts=term_grammar(dict(zero=0,succ=1,add=2),['n'],4)
        self.assertEqual(len(ts),24)
        self.assertIn(L.F('add',L.F('zero'),L.F('succ',L.V('n'))),ts)
    def test_deduction_generalization_hygiene(self):
        th=dict(functions=dict(zero=0),predicates={},axioms={},schemas=[]);H=L.Eq(L.F('zero'),L.F('zero'));p=L.Eq(L.V('n'),L.V('n'));out=Proof()
        i=out.emit('assumption',H,index=0);out.emit('generalize',L.All('n',H),variable='n',source=i)
        lines=deduce(out.lines,H);request=dict(protocol='gcts-fol-1',theory=th,blocks=[],proof=lines,target=lines[-1]['formula'])
        self.assertEqual(check(canonical(request),max_work=None)['status'],'accepted')
        self.assertIn('distribute',[c['rule'] for c in lines])
        self.assertRaises(ValueError,deduce,out.lines,p)
    def test_tiny_point_graph_all_subsets(self):
        z=L.F('zero');s=dict(id='fixture',theory=dict(functions=dict(zero=0),predicates={},axioms={},schemas=[]),target=L.Eq(z,z),length=1,term_bound=1)
        c=catalog(s);m=Model(s,c,dict(status='native_accepted'));r=m.record();tiles={tuple(t['key']):t for t in r['placements']};literal=LiteralDomains(tiles);keys=list(m.cache)
        self.assertEqual(len(keys),4)
        root=dict(totals={},marks=dict(m.initial().marks),generations=dict(m.initial().generations),roots=dict(m.initial().roots),selected=set(),order=[],tile_generations=[])
        for mask in range(1<<len(keys)):
            a=copy.deepcopy(root);state=m.initial();g=Graph(m,state)
            for i,k in enumerate(keys):
                if not mask&(1<<i):continue
                self.assertEqual(state.legal(m.placement(k)),legal(tiles[k],a));g.update(m,state,state.place(m.placement(k)));a=advance(tiles[k],a)
            self.assertEqual(g.domains,{p:set(v) for p,v in literal(a).items()})
    def test_unknown_admission_blocks_search(self):
        z=L.F('zero');s=dict(id='fixture',theory=dict(functions=dict(zero=0),predicates={},axioms={},schemas=[]),target=L.Eq(z,z),length=1,term_bound=1)
        self.assertRaises(ValueError,Model,s,catalog(s),dict(status='unknown_native_inventory'))
    def test_target_scope_and_local_assumption(self):
        out=Proof();p=L.Eq(L.V('n'),L.V('n'));out.emit('assumption',p,index=1)
        self.assertRaises(ValueError,deduce,out.lines,p)
        z=L.F('zero');s=dict(id='fixture',theory=dict(functions=dict(zero=0),predicates={},axioms={},schemas=[]),target=L.Eq(z,L.V('n')),length=1,term_bound=1)
        self.assertRaises(ValueError,catalog,s)

if __name__=='__main__':unittest.main()
