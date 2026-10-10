"""Semantic hygiene, complete base domains and exact proposal equivalence."""
import copy,unittest
import quantifier_family_cases as S
import quantifier_family_patterns as P
import quantifier_family_search as R
import quantifier_family_join as J
import check_quantifier_families as A
import movable_proof_regions as M
import logic as L
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate

class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=S.registry()[0][0];cat=inventory(s);m=M.Model(cat,s['target'],s['bound'],s['hypotheses']);r=R.search(m)
        decorate(s,cat,r);cls.library=P.promote(s,cat,r);cls.donor=(s,cat,r)

    def test_independent_mining_and_all_ground_bindings(self):
        s,cat,r=self.donor
        for t in self.library:self.assertEqual(M.freeze(t['pattern']),A.pattern_for(M.freeze(cat['rules']),M.freeze(t['source']['members'])))
        for spec in S.registry()[2][:4]:
            c=inventory(spec)
            for t in self.library:
                for p in t['pattern']:
                    for row in c['rules']:self.assertEqual(M.freeze(P.matches(p,row)),M.freeze(A.matching(M.freeze(p),M.freeze(row))))

    def test_capture_is_not_alpha_renaming_a_free_variable(self):
        x=L.V('x');v=L.V('v');relation=lambda a,b:('pred','R',(a,b))
        ctx=P.context(P.normal(L.All('v',relation(x,v))),x)
        actual=L.substitute(L.All('v',relation(x,v)),'x',v)
        self.assertEqual(P.fill(ctx,v),P.normal(actual))
        self.assertNotEqual(P.fill(ctx,v),P.normal(L.All('v',relation(v,v))))
        self.assertEqual(P.normal(L.All('x',L.All('x',relation(x,x)))),P.normal(L.All('a',L.All('b',relation(L.V('b'),L.V('b'))))))
        self.assertNotEqual(P.normal(L.All('a',relation(L.V('a'),v))),P.normal(L.All('v',relation(L.V('a'),v))))

    def test_full_enumeration_matches_all_pools_and_fixed_tree(self):
        for spec in S.registry()[2][:4]:
            c=inventory(spec);m=M.Model(c,spec['target'],spec['bound'],spec['hypotheses']);s=m.initial();g=M.Graph(m,s);snapshot=g.fingerprint()
            one,two=J.Join(m,self.library),J.Join(m,self.library,enumerated=True)
            kind,p,keys=g.decision(s);self.assertEqual(one(m,s,g,p,self.library),two(m,s,g,p,self.library));self.assertEqual(snapshot,g.fingerprint())
            a=R.search(M.Model(c,spec['target'],spec['bound'],spec['hypotheses']),self.library,'fixed')
            b=R.search(M.Model(c,spec['target'],spec['bound'],spec['hypotheses']),self.library,'fixed',indexed=False)
            self.assertEqual(a['search_tree'],b['search_tree']);self.assertEqual(a['placements'],b['placements'])

    def test_all_tiny_exact_states_and_rollback(self):
        spec=S.case('quantifier-tiny',ground=True,bound=2);c=inventory(spec);m=M.Model(c,spec['target'],spec['bound'],spec['hypotheses']);seen=0
        def visit(s,g):
            nonlocal seen
            seen+=1;explicit=A.A.domains(M.freeze(c['rules']),spec,M.freeze(s.order))
            self.assertEqual({p:list(d) for p,d in g.domains.items()},explicit)
            snapshot=g.fingerprint();state=s.copy();kind,p,keys=g.decision(s)
            if kind in ('dead','empty'):return
            for k in keys:
                child,cg=s.copy(),g.copy();cg.update(m,child,child.place(m.placement(k)));visit(child,cg)
                self.assertEqual(s,state);self.assertEqual(g.fingerprint(),snapshot)
        visit(m.initial(),M.Graph(m,m.initial()));self.assertGreater(seen,1)

    def test_scope_and_snapshot_are_actual_values(self):
        spec=S.case('quantifier-open',open_scope=True);c=inventory(spec);m=M.Model(c,spec['target'],spec['bound'],spec['hypotheses']);s=m.initial();g=M.Graph(m,s)
        self.assertEqual(s.marks[(-1000,0)],1)
        for d in g.domains.values():
            self.assertTrue(all(k[1]<0 or c['rules'][k[1]]['kind']!='generalize' for k in d))
        r=R.search(m,self.library,'fixed');self.assertEqual(r['status'],'exhausted_finite_region')
        join=J.Join(m,self.library);m.target=('bot',)
        with self.assertRaises(ValueError):join.finish()
        library=copy.deepcopy(self.library);m=M.Model(c,spec['target'],spec['bound'],spec['hypotheses']);join=J.Join(m,library);library[0]['pattern'][0]['kind']='generalize'
        with self.assertRaises(ValueError):join.finish()
        r=R.search(m,self.library,'fixed',attempts=1);self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNotNone(r['search_tree'])

if __name__=='__main__':unittest.main()
