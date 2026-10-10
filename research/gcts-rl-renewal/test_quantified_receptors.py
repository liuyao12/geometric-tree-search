import copy,itertools,unittest
import logic as L
import quantified_receptors as Q
import check_quantified_receptors as A
from quantified_receptor_cases import registry
from serialized_kernel import canonical,check
from audit_serialized_kernel import replay

class QuantifiedReceptorTests(unittest.TestCase):
    def setUp(self):self.cases,self.bindings=registry();self.spec=self.cases[0]
    def model(self,c=None):
        c=c or self.spec;cat=Q.inventory(c['theory'],c['hypotheses'],c['terms'],c['variables'],c['rounds'],generalization_rounds=c['generalization_rounds']);return Q.Model(cat,c['target'],c['length'],c['hypotheses'])
    def test_all_independent_inventories(self):
        for c in self.cases:
            m=self.model(c);rs,fs=A.inventory(c);self.assertEqual(m.catalog['rules'],rs);self.assertEqual(m.catalog['formulas'],fs)
    def test_all_mask_products_and_repeated_inputs(self):
        for a,b,d in itertools.product(range(16),range(16),(False,True)):
            domain=Q.Domain(4,0,[(2,(a,b),d)]);expected=[(4,2,(i,j)) for i in range(4) for j in range(4) if a&(1<<i) and b&(1<<j) and (not d or i!=j)]
            self.assertEqual(list(domain),expected);self.assertEqual(len(domain),len(expected))
            for key in [(4,2,(i,j)) for i in range(4) for j in range(4)]+[(4,2,(10**8,0))]:self.assertEqual(key in domain,key in expected)
        for a in range(16):self.assertEqual(len(Q.Domain(4,0,[(0,(a,),False)])),len(list(Q.bits(a))))
        self.assertEqual(list(Q.Domain(0,0,[(3,(),False)])),[(0,3,())])
    def test_full_domains_reverse_incidence_and_rollback(self):
        m=self.model();s=m.initial();g=Q.Graph(m,s);rs,_=A.inventory(self.spec);seen=0
        def visit(s,g,depth):
            nonlocal seen
            seen+=1;expected=A.domains(rs,self.spec,s.order)
            self.assertEqual({p:list(d) for p,d in g.domains.items()},expected)
            for p,ks in expected.items():
                for k in ks:self.assertEqual(g.candidate_points(k),{p});self.assertTrue(s.legal(m.placement(k)))
            if not depth:return
            original=(s.copy(),g.fingerprint());kind,p,keys=g.decision(s)
            for key in list(keys)[:3]:
                ss=s.copy();gg=g.copy();gg.update(m,ss,ss.place(m.placement(key)));visit(ss,gg,depth-1)
                self.assertEqual(s,original[0]);self.assertEqual(g.fingerprint(),original[1])
        visit(s,g,3);self.assertGreater(seen,5)
    def test_actual_scope_zero_and_missing_are_different(self):
        c=self.cases[2];m=self.model(c);s=m.initial();g=Q.Graph(m,s);self.assertEqual(g.decision(s)[0],'dead')
        rid=next(i for i,r in enumerate(m.catalog['rules']) if r['kind']=='generalize' and r['output']==m.target);tile=m.placement((0,rid,(-1,)))
        self.assertIn((Q.scope(0),0),tile.marks);self.assertEqual(s.marks[Q.scope(0)],1);self.assertFalse(s.legal(tile))
        for v in (None,0):
            ss=s.copy()
            if v is None:del ss.marks[Q.scope(0)]
            else:ss.marks[Q.scope(0)]=v
            with self.assertRaises(ValueError):Q.Graph(m,ss)
    def test_root_generations_and_global_order(self):
        m=self.model();s=m.initial();g=Q.Graph(m,s);g.domains={(0,0):Q.Domain(0,0,[(0,(),False)]),(2,0):Q.Domain(1,0,[])}
        self.assertEqual(g.decision(s)[0],'dead');g.domains.pop((2,0));self.assertEqual(g.decision(s)[0],'forced')
        g.domains={(0,0):Q.Domain(0,0,[(i,(),False) for i in range(5)]),(2,0):Q.Domain(1,0,[(i,(),False) for i in range(2)])};s.generations[(0,0)]=0;s.generations[(2,0)]=1;self.assertEqual(g.decision(s)[1],(0,0))
        m=self.model();r=Q.search(m);self.assertEqual(r['tile_generations'],[1]*m.length)
    def test_capture_avoidance_and_diagonal_countermodel(self):
        good,bad=self.cases[3:5];self.assertIsNotNone(Q.search(self.model(good))['proof']);self.assertEqual(Q.search(self.model(bad))['status'],'exhausted_finite_envelope')
        relation=lambda x,y:x!=y
        self.assertTrue(all(any(relation(x,y) for y in range(2)) for x in range(2)));self.assertFalse(any(relation(y,y) for y in range(2)))
        self.assertEqual(good['target'][1][1],'fresh0')
    def test_goal_not_in_catalog_construction(self):
        c=copy.deepcopy(self.spec);c['target']=('bot',);self.assertEqual(self.model(c).catalog,self.model().catalog)
    def test_open_hypothesis_deduction_and_independent_replay(self):
        c=self.cases[1];m=self.model(c);r=Q.search(m);compiled=Q.compile_request(r['proof'],m.target,m.hypotheses,c['theory'],True);request=compiled['request']
        self.assertEqual(request['theory']['axioms'],{});self.assertEqual(replay(canonical(request))['status'],'accepted');self.assertEqual(request['target'][1],c['hypotheses'][0])
        bad=copy.deepcopy(request);bad['proof'][-1]['formula']=('bot',);self.assertEqual(check(canonical(bad),max_work=None)['status'],'rejected')
    def test_scope_rejects_invalid_local_block(self):
        p=self.cases[2]['hypotheses'][0];a=L.All('x',p);probe=L.Imp(('bot',),('bot',));req=dict(protocol='gcts-fol-1',theory=self.cases[2]['theory'],target=probe,blocks=[dict(name='bad',premises=[p],conclusion=a,proof=[dict(rule='assumption',formula=p,index=0),dict(rule='generalize',formula=a,variable='x',source=0)])],proof=[dict(rule='tautology',formula=probe)])
        self.assertEqual(check(canonical(req),max_work=None)['status'],'rejected');self.assertEqual(replay(canonical(req))['status'],'rejected')
    def test_learned_family_full_instance_expansion(self):
        source=Q.search(self.model());f=dict(name='universal-mp',proof=source['proof'],premises=self.spec['hypotheses'],conclusion=self.spec['target'],guards=('x',));c=self.cases[-1]
        cat=Q.inventory(c['theory'],c['hypotheses'],c['terms'],c['variables'],c['rounds'],family=f,bindings=[self.bindings['geometry']],generalization_rounds=c['generalization_rounds']);rs,_=A.inventory(c,f,[self.bindings['geometry']]);self.assertEqual(cat['rules'],rs)
        m=Q.Model(cat,c['target'],1,c['hypotheses']);r=Q.search(m);self.assertEqual(r['proof'][0]['kind'],'family');self.assertEqual(A.proof(r['proof'],m.target,m.hypotheses,c['theory'])['primitive_lines'],6)
        self.assertEqual(replay(canonical(Q.compile_request(r['proof'],m.target,m.hypotheses,c['theory'],True)['request']))['status'],'accepted')
    def test_unknown_not_exhaustion(self):
        r=Q.search(self.model(),node_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['search_tree'])
    def test_point_certificate_and_changed_word(self):
        m=self.model();r=Q.search(m);rs,_=A.inventory(self.spec);tiles=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in r['placements']]
        self.assertEqual(A.certificate(rs,self.spec,r,tiles)['status'],'accepted');A.tree(rs,self.spec,r)
        bad=copy.deepcopy(tiles);p,v=bad[0]['marks'][0];bad[0]['marks']=((p,'!'),)+bad[0]['marks'][1:]
        with self.assertRaises(ValueError):A.certificate(rs,self.spec,r,bad)
if __name__=='__main__':unittest.main()
