"""Point-engine invariants; these fixtures are not theorem-search observations."""
import unittest
from certificate_boundary_search import formula_basis
from native_receptor_cases import cases
from native_receptor_points import Model,search,center,assignment
from turtle import Graph
def fixture(i=2):
    spec=cases()[i];basis,variables=formula_basis(spec)
    return Model(spec,dict(status='complete',basis=basis,variables=variables,tautologies=[],queries=[]))
def scan(model,state):
    return {p:{k for k,c in model.cache.items() if any(q==p for q,_ in c.occupancy) and state.legal(c)} for p in state.frontier()}
class Invariants(unittest.TestCase):
    def test_all_roots_and_complete_updates(self):
        m=fixture();s=m.initial();g=Graph(m,s)
        self.assertEqual(len(g.domains),6);self.assertEqual(g.domains,scan(m,s))
        for _ in range(6):
            kind,p,keys=g.decision(s)
            if kind in ('dead','empty'):break
            g.update(m,s,s.place(m.placement(keys[0])))
            self.assertEqual(g.domains,scan(m,s))
            self.assertEqual({k:{p for p,d in g.domains.items() if k in d} for k in g.edges},g.edges)
    def test_mark_only_dependency_reaches_backwards(self):
        m=fixture();s=m.initial();g=Graph(m,s);source=center(0,'command')
        earlier=g.domains[source].copy()
        # Change only an off-frontier formula port; no occupancy changes.
        changed=dict(assignment(0,'formula',m.spec['target']));s.marks.update(changed);g.update(m,s,set(changed))
        self.assertNotEqual(g.domains[source],earlier);self.assertEqual(g.domains,scan(m,s))
    def test_dead_before_forced_and_generation_before_degree(self):
        m=fixture();s=m.initial();g=Graph(m,s);points=sorted(g.domains);g.domains[points[-1]]=set();g.domains[points[0]]={next(iter(g.domains[points[0]]))}
        self.assertEqual(g.decision(s)[0],'dead')
        g=Graph(m,s);s.generations={p:7 for p in g.domains};s.generations[points[0]]=0
        self.assertEqual(g.decision(s)[1],points[0])
        g.domains[points[-1]]={next(iter(g.domains[points[-1]]))};self.assertEqual(g.decision(s)[1],points[-1])
    def test_bound_and_root_rollback(self):
        for i,status in [(2,'finite_marked_proof_region'),(4,'exhausted_finite_marked_region'),(5,'exhausted_finite_marked_region')]:
            m=fixture(i);r=search(m);self.assertEqual(r['status'],status);self.assertTrue(r['root_restored'])
        self.assertEqual(search(fixture(),attempts=0)['status'],'unknown_search_budget')
    def test_internal_conflicts_and_unfinished_compiler(self):
        m=fixture();self.assertTrue(m.conflicts)
        for c in m.cache.values():self.assertEqual(len(dict(c.marks)),len(c.marks))
        with self.assertRaises(ValueError):Model(m.spec,dict(status='unknown_native_compilation'))
if __name__=='__main__':unittest.main()
