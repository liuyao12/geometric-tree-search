"""All tiny solutions, exact parent copies, expiry, hierarchy and budget scope."""
import copy,unittest
import resumable_clusters as R
import movable_proof_regions as M
import check_resumable_clusters as V
from resumable_cases import registry,branch
from run_resumable_clusters import run
from run_adaptive_clusters import inventory

class Resumable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=registry()[0][0];c,r=run(s);cls.library=R.promote(s,c,r,maximum=3)
    def test_all_tiny_solutions_and_exact_parent_rollback(self):
        s=branch('resume-tiny');c=inventory(s);m=M.Model(c,s['target'],s['bound'],s['hypotheses']);original=set();hinted=set();templates={t['name']:t for t in self.library}
        def visit(state,g,active=None):
            ds=V.A.domains(c['rules'],s,state.order)
            self.assertEqual({p:set(d) for p,d in g.domains.items()},{p:set(d) for p,d in ds.items()})
            kind,p,keys=g.decision(state);self.assertEqual((kind,p),V.A.decide(ds)[:2])
            if kind=='empty':hinted.add(tuple(sorted(state.order)));return
            if kind=='dead':return
            active,review=R.review(m,state,g,active,kind,p,keys)
            if kind=='branch' and active is None:
                items,_=R.C.proposals(m,state,g,p,self.library,32)
                if items:
                    item,_=R.C.choose(items,m,state,R.FIXED_WEIGHTS,False,__import__('random').Random(0));V.V.item(c['rules'],s,templates,item,state.order)
                    active,review=R.review(m,state,g,dict(id=0,item=item,waiting=False),kind,p,keys)
            choices=list(R.ordered(keys,review.get('pending',()) if active else ())) if kind=='branch' else list(keys)
            self.assertEqual(set(choices),set(keys));self.assertEqual(len(choices),len(keys));snapshot=state.copy();fingerprint=g.fingerprint()
            for k in choices:
                child,cg=state.copy(),g.copy();cg.update(m,child,child.place(m.placement(k)));visit(child,cg,active)
                self.assertEqual(state,snapshot);self.assertEqual(g.fingerprint(),fingerprint)
        def other(chosen):
            kind,p,keys=V.A.decide(V.A.domains(c['rules'],s,chosen))
            if kind=='empty':original.add(tuple(sorted(chosen)));return
            if kind=='dead':return
            for k in keys:other(chosen+(k,))
        visit(m.initial(),M.Graph(m,m.initial()));other(())
        self.assertTrue(original);self.assertEqual(original,hinted)
    def test_interrupt_resume_and_actual_child(self):
        s=registry()[0][1];c,r=run(s,self.library,'fixed');self.assertTrue(r['solution_hints'])
        self.assertGreater(r['metrics']['hint_suspended'],0);self.assertGreater(r['metrics']['hint_resumed'],0)
        V.result(c['rules'],s,{t['name']:t for t in self.library},r)
        big=R.promote(s,c,r,self.library,maximum=5);self.assertTrue(any(t['level']==2 and t['children'] for t in big))
    def test_negative_fallback_and_expiry(self):
        s=branch('resume-no-tail',tail=1,bound=2);c,base=run(s);_,hint=run(s,self.library,'fixed')
        self.assertEqual(base['status'],hint['status']);self.assertEqual(hint['status'],'exhausted_finite_region')
        V.result(c['rules'],s,{t['name']:t for t in self.library},hint)
    def test_unknown_budget_is_checked_partial_tree(self):
        s=branch('resume-budget');c,r=run(s,self.library,'fixed',attempts=1)
        self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['proof'])
        V.result(c['rules'],s,{t['name']:t for t in self.library},r)
    def test_corrupt_pending_set_and_capacity_reject(self):
        s=branch('resume-bad');c,r=run(s,self.library,'fixed');bad=copy.deepcopy(r)
        values=bad['hints'][0]['item']['occupancy'];bad['hints'][0]['item']['occupancy']=((values[0][0],11),)+values[1:]
        with self.assertRaises(ValueError):V.result(c['rules'],s,{t['name']:t for t in self.library},bad)

if __name__=='__main__':unittest.main()
