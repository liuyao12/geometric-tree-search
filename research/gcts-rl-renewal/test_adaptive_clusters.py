"""Meaningful differential, capacity, adaptation and rollback tests."""
import copy
import unittest

import adaptive_receptor_clusters as C
import check_adaptive_clusters as V
import movable_proof_regions as M
from run_adaptive_clusters import case,inventory,run


class AdaptiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=case('fresh-unit-donor',3,3)
        catalog,result=run(spec)
        cls.library=C.promote(spec,catalog,result,maximum=3)

    def test_complete_domains_and_all_tiny_certificates(self):
        spec=case('tiny',2,3);catalog=inventory(spec)
        model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        state=model.initial();graph=M.Graph(model,state)
        point_solutions=set();independent_solutions=set()
        def visit(s,g):
            explicit=V.A.domains(catalog['rules'],spec,s.order)
            self.assertEqual({p:set(d) for p,d in g.domains.items()},{p:set(d) for p,d in explicit.items()})
            self.assertEqual((g.decision(s)[0],g.decision(s)[1]),V.A.decide(explicit)[:2])
            kind,p,keys=g.decision(s)
            if kind=='empty':point_solutions.add(tuple(sorted(s.order)));return
            if kind=='dead':return
            for k in keys:
                child,cg=s.copy(),g.copy();cg.update(model,child,child.place(model.placement(k)));visit(child,cg)
        def other(chosen):
            kind,p,keys=V.A.decide(V.A.domains(catalog['rules'],spec,chosen))
            if kind=='empty':independent_solutions.add(tuple(sorted(chosen)));return
            if kind=='dead':return
            for key in keys:other(chosen+(key,))
        visit(state,graph);other(())
        self.assertTrue(point_solutions)
        self.assertEqual(point_solutions,independent_solutions)

    def test_compound_receptors_keep_every_base_cell(self):
        spec=case('compound',3,4,True);catalog=inventory(spec)
        model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        state=model.initial();graph=M.Graph(model,state)
        # Fix the closing boundary; it is a test context, not a supplied proof.
        key=(3,M.END,());graph.update(model,state,state.place(model.placement(key)))
        while graph.decision(state)[0]=='forced':
            forced=graph.decision(state)[2][0]
            graph.update(model,state,state.place(model.placement(forced)))
        kind,p,_=graph.decision(state)
        items,work=C.proposals(model,state,graph,p,self.library)
        self.assertTrue(items)
        templates={t['name']:t for t in self.library}
        for item in items:
            V.item(catalog['rules'],spec,templates,item,state.order)
            self.assertEqual(len(item['occupancy']),len(item['members']))
            self.assertTrue(all(v==12 for _,v in item['occupancy']))
        self.assertTrue(any(any(a[0] in ('and','imp') for a in t['bindings'].values()) for t in items))

    def test_failed_transactions_restore_every_semantic_field(self):
        spec=case('gapped',3,5,distractors=1);catalog=inventory(spec)
        model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        state=model.initial();graph=M.Graph(model,state)
        initial=state.copy();fingerprint=graph.fingerprint()
        kind,p,_=graph.decision(state)
        items,_=C.proposals(model,state,graph,p,self.library,limit=1000)
        rejections=[]
        for item in items:
            trace,child,cg=C.execute(model,state,graph,item)
            self.assertEqual(state,initial);self.assertEqual(graph.fingerprint(),fingerprint)
            if child is None:rejections.append(trace['status'])
        self.assertIn('rejected_scheduler',rejections)
        self.assertTrue(any(max(k[0] for k in t['members'])-min(k[0] for k in t['members'])+1>len(t['members']) for t in items))

    def test_unproposed_base_choices_remain_complete(self):
        spec=case('absent',3,4);spec['hypotheses'].pop(2);catalog=inventory(spec)
        model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        base=C.search(model)
        hint=C.search(M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses']),self.library,'fixed',proposal_limit=1)
        self.assertEqual(base['status'],'exhausted_finite_region')
        self.assertEqual(hint['status'],base['status'])
        V.result(catalog['rules'],spec,{t['name']:t for t in self.library},hint)

    def test_bad_aggregate_and_budget_roll_back(self):
        spec=case('budget',2,3);catalog=inventory(spec)
        model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        state=model.initial();graph=M.Graph(model,state)
        key=(2,M.END,());graph.update(model,state,state.place(model.placement(key)))
        p=graph.decision(state)[1];items,_=C.proposals(model,state,graph,p,self.library)
        item=items[0];bad=copy.deepcopy(item);bad['occupancy']=tuple((p,11) for p,v in bad['occupancy'])
        snapshot=state.copy();fingerprint=graph.fingerprint()
        with self.assertRaises(ValueError):C.execute(model,state,graph,bad)
        def cutoff():raise C.Budget()
        trace,child,cg=C.execute(model,state,graph,item,cutoff)
        self.assertEqual(trace['status'],'unknown_transaction_budget')
        self.assertIsNone(child);self.assertEqual(state,snapshot);self.assertEqual(graph.fingerprint(),fingerprint)


if __name__=='__main__':unittest.main()
