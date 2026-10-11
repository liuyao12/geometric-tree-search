"""Factorization, scope and native-registration-independent model invariants."""
import copy,unittest
from certificate_boundary_search import formula_basis
from native_receptor_cases import cases
from native_receptor_points import Model as Primitive,search as primitive_search
from semantic_lemma_inventory import mine,specialize,used_definitions
from semantic_receptor_points import Model,search
from turtle import Graph

def compiled(spec):
    b,v=formula_basis(spec);return dict(status='complete',basis=b,variables=v,tautologies=[])
def library():
    rows=[]
    for spec in [cases()[2],cases()[6]]:
        c=compiled(spec);out=primitive_search(Primitive(spec,c))
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=out['proof'],target=spec['target'])
        rows.append(mine(request,[],dict(scope='unit model fixture, not native admission')))
    return rows
def admitted(lib,spec):
    # Only these unit combinatorial probes use mocked native admission.
    return dict(**specialize(lib,compiled(spec)['basis']),status='native_accepted')

class Semantics(unittest.TestCase):
    def test_no_coordinates_or_donor_atoms_in_templates(self):
        for f in library():
            self.assertNotIn('donor_atoms',f['template'])
            self.assertTrue(all(c['rule']!='axiom' for c in f['template']['proof']))
            self.assertNotIn('pred',str(f['template']))
    def test_rebind_to_compound_incidence_formulas(self):
        spec=copy.deepcopy(cases()[3]);inventory=admitted(library(),spec)
        self.assertTrue(inventory['interfaces'])
        for r in inventory['definitions']:
            for p in r['definition']['premises']:self.assertIn(p,compiled(spec)['basis'])
    def test_complete_source_choices_and_fillers(self):
        spec=cases()[6];m=Model(spec,compiled(spec),admitted(library(),spec))
        self.assertEqual(len(m.initial().roots),spec['length']*(2+m.arity))
        for j in range(spec['length']):
            for d in m.interfaces:
                mode=m.mode[d['name']]
                for r in range(m.arity):
                    rows=[v for k,v in m.metadata.items() if k[0]==j and k[1]==r+2 and v['mode']==mode]
                    if r<len(d['definition']['premises']):self.assertEqual(sorted(x['source'] for x in rows),list(range(j)))
                    else:self.assertEqual(len(rows),1);self.assertIsNone(rows[0]['source'])
    def test_factored_proof_and_exact_rollback(self):
        spec=cases()[2];m=Model(spec,compiled(spec),admitted(library(),spec));out=search(m,seconds=30)
        self.assertEqual(out['status'],'finite_marked_proof_region');self.assertTrue(out['root_restored'])
        self.assertEqual(len(out['placements']),len(m.initial().roots))
        self.assertEqual(out['proof'],m.decode(out['placements']))
        self.assertEqual(out['proof'][-1]['formula'],spec['target'])
    def test_unfinished_inventory_never_filters(self):
        spec=cases()[2];inv=admitted(library(),spec);inv['status']='unknown_native_inventory'
        with self.assertRaises(ValueError):Model(spec,compiled(spec),inv)
    def test_no_input_is_an_assigned_value(self):
        spec=cases()[2];m=Model(spec,compiled(spec),admitted(library(),spec))
        filler=next(c for k,c in m.cache.items() if m.metadata[k]['kind']=='unused_input')
        self.assertIn(-1,dict(filler.marks).values());self.assertIn(0,dict(filler.marks).values())
        s=m.initial();g=Graph(m,s);before=g.fingerprint();s2=s.copy();g2=g.copy();g2.update(m,s2,s2.place(filler));self.assertEqual(g.fingerprint(),before)
    def test_used_definition_closure_preserves_registry_order(self):
        inventory=dict(definitions=[
            dict(name='first',definition=dict(name='first',proof=[])),
            dict(name='unused',definition=dict(name='unused',proof=[])),
            dict(name='second',definition=dict(name='second',proof=[dict(rule='block',name='first')]))])
        inventory['native_blocks']=[d['definition'] for d in inventory['definitions']]
        out=used_definitions(inventory,[dict(rule='block',name='second')])
        self.assertEqual([d['name'] for d in out],['first','second'])
        self.assertEqual(len(inventory['definitions']),3)
        with self.assertRaises(ValueError):used_definitions(inventory,[dict(rule='block',name='missing')])
    def test_smt_agrees_with_tiny_complete_point_search(self):
        from semantic_point_smt import solve,verify_selected
        for length in (2,3):
            spec=copy.deepcopy(cases()[2]);spec['length']=length
            m=Model(spec,compiled(spec),admitted(library(),spec))
            tree=search(m,attempts=10000,seconds=30);smt=solve(m,seconds=10)
            self.assertEqual(tree['status']=='finite_marked_proof_region',smt['status']=='smt_exact_point_region')
            self.assertNotIn(tree['status'],['unknown_search_budget'])
            if smt['proof']:verify_selected(m,smt['placements'])
            else:self.assertEqual(smt['status'],'solver_unsat_finite_point_region')
if __name__=='__main__':unittest.main()
