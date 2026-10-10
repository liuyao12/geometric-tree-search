import copy,json,itertools,unittest
from pathlib import Path
import factored_receptors as F
import propositional_receptors as R
import check_propositional_receptors as A
import check_factored_receptors as C
from turtle import Graph as GroundGraph

DOC=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'
class FactoredTests(unittest.TestCase):
    def test_both_complete_rule_inventories(self):
        for kind in ('plain','negated'):
            u=F.Universe(kind);params,rules=C.inventory(kind)
            self.assertEqual(tuple(params),u.pool);self.assertEqual(list(u.rules),rules)
        self.assertEqual(list(F.Universe().rules),R.basis()['rules'])
    def test_bound_schema_unification_equals_exhaustive(self):
        u=F.Universe();by={}
        for rid in range(u.schema_count):by.setdefault(u.rule(rid)['output'],[]).append(rid)
        for a,rids in by.items():self.assertEqual(u.bound_schemas(a),rids)
        self.assertEqual(u.bound_schemas(R.P),[])
    def test_all_domain_mask_products_and_diagonals(self):
        for a,b in itertools.product(range(16),repeat=2):
            d=F.Domain(3,1,[(5,6,a,b)]);expected=[(3,5,(i-1,j-1)) for i in range(4) for j in range(4) if a>>i&1 and b>>j&1 and i!=j]
            self.assertEqual(list(d),expected);self.assertEqual(d.count,len(expected))
            for k in expected:self.assertIn(k,d)
            self.assertNotIn((3,5,(10**8,0)),d)
    def test_partial_point_domains_incidence_and_exact_rollback(self):
        u=F.Universe();target=R.Q;hyp=(R.P,R.imp(R.P,R.Q));fm=F.Model(u,target,3,hyp);gm=R.Model(R.basis(),target,3,hyp)
        s=fm.initial();f=F.Graph(fm,s);g=GroundGraph(gm,s);visited=0
        def walk(s,f,g,depth):
            nonlocal visited
            visited+=1
            self.assertEqual({p:set(d) for p,d in f.domains.items()},g.domains)
            for p,d in f.domains.items():
                self.assertEqual(d.count,len(g.domains[p]))
                for k in d:self.assertEqual(f.candidate_points(k),g.edges[k])
            ff=f.fingerprint();gg=g.fingerprint();before=copy.deepcopy(s)
            if depth:
                for k in list(g.edges)[:8]:
                    ss=s.copy();fs=f.copy();gs=g.copy();changed=ss.place(fm.placement(k));fs.update(fm,ss,changed);gs.update(gm,ss,changed);walk(ss,fs,gs,depth-1)
                    self.assertEqual(s,before);self.assertEqual(f.fingerprint(),ff);self.assertEqual(g.fingerprint(),gg)
        walk(s,f,g,2);self.assertGreater(visited,8)
    def test_remote_mark_only_port_removes_candidates(self):
        u=F.Universe();m=F.Model(u,R.Q,4,(R.P,R.imp(R.P,R.Q)));s=m.initial();g=F.Graph(m,s)
        key=next(k for d in g.domains.values() for k in d if k[0]==3 and 0 in k[2]);old=set(g.domains[R.cell(0)])
        g.update(m,s,s.place(m.placement(key)));self.assertNotEqual(old,set(g.domains[R.cell(0)]));self.assertNotIn(R.scope(0),g.domains)
    def test_global_dead_forced_generation_order(self):
        m=F.Model(F.Universe(),R.Q,3);s=m.initial();g=F.Graph(m,s)
        g.domains={R.cell(0):F.Domain(0,0,[(0,2,None,None)]),R.cell(1):F.Domain(1,0,[(0,1,None,None)]),R.cell(2):F.Domain(2,0,[])}
        self.assertEqual(g.decision(s)[:2],('dead',R.cell(2)));g.domains[R.cell(2)]=F.Domain(2,0,[(0,2,None,None)])
        self.assertEqual(g.decision(s)[:2],('forced',R.cell(1)));g.domains[R.cell(1)]=F.Domain(1,0,[(0,3,None,None)])
        s.generations={R.cell(0):2,R.cell(1):0,R.cell(2):1};self.assertEqual(g.decision(s)[:2],('branch',R.cell(1)))
    def test_complete_identity_search_tree_and_points(self):
        u=F.Universe();m=F.Model(u,R.imp(R.P,R.P),5);r=F.search(m)
        prior=json.loads((DOC/'propositional-receptors-001.json').read_text())['donor']
        self.assertEqual(A.frozen(r['search_tree']),A.frozen(prior['search_tree']))
        self.assertEqual(r['metrics']['nodes'],220);rules=C.inventory('plain')[1]
        tiles=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in r['placements']]
        self.assertEqual(C.certificate(rules,m.target,5,(),r['placements'],tiles)['status'],'accepted')
        C.tree(rules,m.target,5,(),A.frozen(r))
    def test_unknown_is_not_exhaustion(self):
        self.assertEqual(F.search(F.Model(F.Universe(),R.P,1))['status'],'exhausted_finite_envelope')
        self.assertEqual(F.search(F.Model(F.Universe(),R.imp(R.P,R.P),5),node_limit=0)['status'],'unknown_search_budget')
    def test_full_formula_prefix_terminator(self):
        m=F.Model(F.Universe(),R.imp(R.P,R.P),5);s=m.initial();g=F.Graph(m,s);key=next(iter(g.domains[R.cell(0)]));s.place(m.placement(key));s.marks[R.scope(0)]=1
        with self.assertRaises(ValueError):g.update(m,s,set())
    def test_family_parameter_and_full_expansion(self):
        family=A.frozen(json.loads((DOC/'propositional-receptors-001.json').read_text())['discovered_family'])
        u=F.Universe('negated',family);m=F.Model(u,R.imp(R.neg(R.P),R.neg(R.P)),1);r=F.search(m)
        self.assertEqual(len(r['proof']),1);self.assertEqual(A.logical(r['proof'],m.target)['primitive_lines'],5)

if __name__=='__main__':unittest.main()
