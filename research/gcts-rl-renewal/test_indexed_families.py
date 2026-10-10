"""Complete tiny domains/pools/solutions, cold cache scope and partial fallback."""
import copy,unittest
import indexed_family_join as J
import indexed_family_search as I
import check_indexed_families as V
import check_resumable_clusters as W
import resumable_clusters as R
import movable_proof_regions as M
from run_indexed_families import run,semantic
from resumable_cases import branch

class Indexed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=branch('index-test-donor');c,r=run(s);cls.library=R.promote(s,c,r,maximum=3)
    def test_all_tiny_pools_domains_solutions_and_rollback(self):
        s=branch('index-test-tiny');c=__import__('run_adaptive_clusters').inventory(s);m=M.Model(c,s['target'],s['bound'],s['hypotheses']);join=J.Join(m,self.library);templates={t['name']:t for t in self.library};seen=set();actual=set();other=set()
        def visit(state,g):
            ds=W.A.domains(c['rules'],s,state.order);self.assertEqual({p:set(v) for p,v in g.domains.items()},{p:set(v) for p,v in ds.items()});kind,p,keys=g.decision(state);self.assertEqual((kind,p),W.A.decide(ds)[:2]);snapshot=state.copy();pin=g.fingerprint()
            if kind=='empty':actual.add(tuple(sorted(state.order)));return
            if kind=='dead':return
            if kind=='branch':
                items,counts=join(m,state,g,p,self.library,32);expected,work=W.proposal_pool(c['rules'],s,templates,state.order,p,32);self.assertEqual(M.freeze(items),M.freeze(expected));self.assertEqual(counts,work)
            for key in keys:
                child,cg=state.copy(),g.copy();cg.update(m,child,child.place(m.placement(key)));visit(child,cg);self.assertEqual(state,snapshot);self.assertEqual(g.fingerprint(),pin)
        def independent(chosen):
            kind,p,keys=W.A.decide(W.A.domains(c['rules'],s,chosen))
            if kind=='empty':other.add(tuple(sorted(chosen)));return
            if kind=='dead':return
            for key in keys:independent(chosen+(key,))
        state=m.initial();visit(state,M.Graph(m,state));independent(());self.assertTrue(actual);self.assertEqual(actual,other)
    def test_compound_queries_and_full_fixed_tree(self):
        s=branch('index-test-compound',compound=True,tail=1,decoys=1);c,a=run(s,self.library,'fixed',indexed=False);_,b=run(s,self.library,'fixed');self.assertEqual(semantic(a),semantic(b));W.result(c['rules'],s,{t['name']:t for t in self.library},b);V.index(dict(spec=s,catalog=c),b,{t['name']:t for t in self.library},True)
    def test_repeated_lookup_changes_no_state_and_same_pool(self):
        s=branch('index-test-cache');c=__import__('run_adaptive_clusters').inventory(s);m=M.Model(c,s['target'],s['bound'],s['hypotheses']);state=m.initial();g=M.Graph(m,state);p=g.decision(state)[1];join=J.Join(m,self.library);snap=state.copy();pin=g.fingerprint();a=join(m,state,g,p,self.library,32);b=join(m,state,g,p,self.library,32);self.assertEqual(a,b);self.assertEqual(state,snap);self.assertEqual(g.fingerprint(),pin);self.assertGreater(join.metrics['query_cache_hits'],0);self.assertGreater(join.metrics['aggregate_cache_hits'],0)
    def test_model_or_library_changes_reject_snapshot(self):
        s=branch('index-test-snapshot');c=__import__('run_adaptive_clusters').inventory(s);m=M.Model(c,s['target'],s['bound'],s['hypotheses']);lib=copy.deepcopy(self.library);join=J.Join(m,lib);m.target=('bot',)
        with self.assertRaises(ValueError):join.finish()
        m.target=M.freeze(s['target']);lib[0]['level']+=1
        with self.assertRaises(ValueError):join.finish()
        other=M.Model(c,s['target'],s['bound'],s['hypotheses'])
        with self.assertRaises(ValueError):join(other,other.initial(),M.Graph(other,other.initial()),(0,0),lib,32)
    def test_negative_full_fallback_and_budget_unknown(self):
        s=branch('index-test-short',tail=1,bound=2);c,a=run(s,self.library,'fixed',indexed=False);_,b=run(s,self.library,'fixed');self.assertEqual(semantic(a),semantic(b));self.assertEqual(b['status'],'exhausted_finite_region')
        s=branch('index-test-budget');c,r=run(s,self.library,'fixed',attempts=1);self.assertEqual(r['status'],'unknown_search_budget');W.result(c['rules'],s,{t['name']:t for t in self.library},r);V.index(dict(spec=s,catalog=c),r,{t['name']:t for t in self.library},True)
if __name__=='__main__':unittest.main()
