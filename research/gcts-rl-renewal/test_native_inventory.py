"""Meaningful cluster reuse, rollback and fallback invariants."""
import unittest
from certificate_boundary_search import formula_basis
from native_receptor_points import Model,search as base
from native_inventory_cases import donors,evaluation
from native_inference_inventory import mine,combine,aggregate,Join
from native_inventory_search import search
from native_inventory_policy import vector,update,FEATURES
from turtle import Graph
def model(spec):
    basis,variables=formula_basis(spec);return Model(spec,dict(status='complete',basis=basis,variables=variables,tautologies=[]))
def library():
    rows=[]
    for spec in donors():
        m=model(spec);r=base(m);rows+=mine(m,r['placements'],spec['id'])
    return combine(rows)
class Invariants(unittest.TestCase):
    def test_abstraction_and_rebinding(self):
        lib=library();self.assertEqual(len(lib),12)
        for f in lib:
            self.assertEqual(set(f['template']),{'nodes','holes'})
            for n in f['template']['nodes']:self.assertEqual(set(n),{'rule','inputs'})
        m=model(evaluation()[2]);s=m.initial();g=Graph(m,s);kind,p,keys=g.decision(s);items,work=Join(m,lib)(s,g,p)
        self.assertTrue(any(i and i['kind']=='family' for i in items))
        for i in items[1:]:self.assertIsNotNone(aggregate(m,i['members'],s))
    def test_reused_constituent_is_not_counted_twice(self):
        m=model(donors()[0]);r=base(m);s=m.initial();members=r['placements'][:2];a=aggregate(m,members,s);s.place(m.placement(members[0]));b=aggregate(m,members+[members[0]],s)
        self.assertEqual(a['new_occupancy']-b['new_occupancy'],12);self.assertEqual(len(b['members']),2)
    def test_original_fallback_and_reference_scheduler(self):
        m=model(evaluation()[0]);r=search(m,library(),'fixed',attempts=2000)
        self.assertEqual(r['status'],'finite_marked_proof_region');self.assertTrue(r['root_restored'])
        def visit(t):
            if 'alternatives' in t:
                keys=next(x['keys'] for x in t['census'] if tuple(x['point'])==tuple(t['point']))
                self.assertEqual(set(map(tuple,t['alternatives'])),set(map(tuple,keys)))
                if t['kind']=='forced':self.assertEqual(len(t['alternatives']),1)
            for c in t['children']:visit(c['tree'])
        visit(r['tree'])
    def test_unknown_and_negative_controls(self):
        for spec,status in [(evaluation()[-1],'unknown_search_budget'),(evaluation()[-2],'exhausted_finite_marked_region')]:
            r=search(model(spec),library(),'fixed',attempts=spec.get('attempts',2000));self.assertEqual(r['status'],status);self.assertTrue(r['root_restored'])
    def test_fresh_gradient_and_zero_episode(self):
        w=[0.]*len(FEATURES);after,b,record=update(w,[],1.,0.)
        self.assertEqual(after,w);self.assertEqual(record['gradient'],w)
        event=dict(features=[[0.]*len(w),[1.]+[0.]*(len(w)-1)],probabilities=[0.5,0.5],index=1)
        after,b,record=update(w,[event],1.,0.);self.assertGreater(after[0],0)
if __name__=='__main__':unittest.main()
