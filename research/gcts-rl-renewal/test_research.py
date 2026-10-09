"""Conformance tests of semantic obligations, not just implementation snapshots."""
import unittest
from turtle import *
from cyclotomic import audit
from wang import demo
from inflation import probe
import logic
import spatial
import wang
from itertools import combinations,product

class Conformance(unittest.TestCase):
    def test_reference_point_data(self):
        self.assertEqual(len(BASE),28)
        self.assertEqual(sum(BASE.values()),240)
        self.assertTrue(all(sum(p)==0 for p in BASE))
        self.assertEqual([BASE[p] for p in VERTICES],list(ANGLES))
    def test_incremental_graph_matches_independent_enumeration(self):
        model = Model()
        state = rooted(model)
        graph = Graph(model,state)
        rng = random.Random(71)
        for _ in range(8):
            self.assertEqual(graph.domains,exhaustive_domains(model,state))
            self.assertEqual(graph.edges,{c:{p for p,cs in graph.domains.items() if c in cs}
                                         for c in graph.edges})
            kind,p,keys = graph.decision(state)
            if kind in ("dead","empty"): break
            key = rng.choice(keys)
            graph.update(model,state,state.place(model.placement(key)))
    def test_order(self):
        state = State(generations={(0,0,0):0,(1,0,-1):1,(2,0,-2):2})
        graph = object.__new__(Graph)
        graph.domains = {(0,0,0):{1,2,3},(1,0,-1):{4,5},(2,0,-2):set()}
        self.assertEqual(graph.decision(state)[0],"dead")
        graph.domains[2,0,-2] = {6}
        self.assertEqual(graph.decision(state)[:2],("forced",(2,0,-2)))
        graph.domains[2,0,-2] = {6,7}
        self.assertEqual(graph.decision(state)[:2],("branch",(0,0,0)))
    def test_rollback_and_shared_fractional_candidates(self):
        model = Model()
        parent = rooted(model)
        graph = Graph(model,parent)
        fp = graph.fingerprint()
        totals = parent.totals.copy()
        self.assertTrue(any(len(ps)>1 for ps in graph.edges.values()))
        for key in graph.decision(parent)[2][:4]:
            child,g = parent.copy(),graph.copy()
            g.update(model,child,child.place(model.placement(key)))
            self.assertEqual(g.domains,exhaustive_domains(model,child))
        self.assertEqual(graph.fingerprint(),fp)
        self.assertEqual(parent.totals,totals)
    def test_zero_obligation_and_mark_only_dependencies(self):
        model = Model({(20,-20,0):0,(21,-20,-1):1})
        state = rooted(model)
        state.roots[0,10,-10] = 0
        state.generations[0,10,-10] = 0
        graph = Graph(model,state)
        self.assertIn((0,10,-10),graph.domains)
        self.assertEqual(graph.domains,exhaustive_domains(model,state))
        # Explicit zero is assigned, so a remote disagreement must delete every
        # incident edge of a candidate even if this point is not in the frontier.
        key = next(iter(graph.edges))
        c = model.placement(key)
        p,v = c.marks[0]
        state.marks[p] = v+1
        graph.update(model,state,{p})
        self.assertNotIn(key,graph.edges)
        self.assertEqual(graph.domains,exhaustive_domains(model,state))
    def test_symmetry_action(self):
        for g in SYMMETRIES:
            for p in BASE: self.assertEqual(inverse(transform(p,g),g),p)
        base = {(tuple(p),v) for p,v in BASE.items()}
        model = Model()
        for g in SYMMETRIES:
            for o,h in enumerate(SYMMETRIES):
                composite = {(transform(transform(p,h),g),v) for p,v in BASE.items()}
                self.assertTrue(any(composite==set(entries) for entries in model.orientations))
    def test_negative_certificate_and_tamper(self):
        model = Model()
        sample = one_corona(model,pair_catalog(model)[0])
        self.assertEqual(sample["status"],"negative")
        self.assertTrue(check_failure_certificate(model,sample["second"],sample["certificate"])[0])
        self.assertFalse(check_failure_certificate(model,sample["second"],{"dead":(100,0,-100)})[0])
    def test_budget_is_unknown(self):
        result = one_corona(Model(),(0,(-6,3,3)),node_limit=0)
        self.assertEqual(result["status"],"unresolved")
    def test_ring(self): self.assertTrue(audit()["phi_identity_verified"])
    def test_wang_certificate(self):
        result = demo()
        self.assertTrue(result["verified"])
        self.assertTrue(result["tampered_certificate_rejected"])
    def test_finite_boundary_control(self):
        result = probe(1)
        self.assertEqual(result["status"],"finite_exact_self_inflation")
        self.assertEqual(len(result["placements"]),1)
    def test_sequence_fallback_and_transaction(self):
        model = Model()
        state = rooted(model)
        graph = Graph(model,state)
        keys = graph.decision(state)[2]
        before = (state.totals.copy(),graph.fingerprint())
        actions = sequence_actions(model,state,graph,keys,[],10)
        self.assertEqual({seq[0] for seq in actions},set(keys))
        self.assertEqual((state.totals,graph.fingerprint()),before)

    def test_spatial_interface_symmetry_and_duplicate_rejection(self):
        model=Model({(3,-2,-1):0})
        state=rooted(model); key=Graph(model,state).decision(state)[2][0]
        keys=state.order+[key]
        self.assertTrue(verify_patch(model,keys))
        sig=spatial.canonical(keys)
        for g in SYMMETRIES:
            self.assertEqual(spatial.canonical(spatial.moved(keys,g,(9,-2,-7))),sig)
        self.assertEqual(spatial.interface(model,keys)["units"],480)
        with self.assertRaises(ValueError): spatial.interface(model,keys+[key])

    def test_connected_subsets_against_independent_enumeration(self):
        graph={0:{1},1:{0,2,3},2:{1,3},3:{1,2}}
        expected=set()
        for n in (2,3,4):
            for ids in combinations(graph,n):
                seen={ids[0]}; pending=[ids[0]]
                while pending:
                    for j in graph[pending.pop()]&set(ids)-seen: seen.add(j); pending.append(j)
                if seen==set(ids): expected.add(frozenset(ids))
        self.assertEqual(set(spatial.connected_sets(graph,4)),expected)

    def test_spatial_proposals_preserve_complete_domains_and_transaction(self):
        model=Model(); state=rooted(model); graph=Graph(model,state)
        keys=graph.decision(state)[2]
        library=[{"expansion":spatial.canonical(state.order+[keys[0]])}]
        before=(state.totals.copy(),state.marks.copy(),state.order.copy(),graph.fingerprint())
        actions=spatial.Proposer(library)(model,state,graph,keys,library,5)
        self.assertTrue({(k,) for k in keys}<=set(actions))
        for seq in actions:
            trial,g=state.copy(),graph.copy()
            for k in seq:
                self.assertIn(k,g.decision(trial)[2])
                g.update(model,trial,trial.place(model.placement(k)))
        self.assertEqual((state.totals,state.marks,state.order,graph.fingerprint()),before)

    def test_logic_capture_avoiding_substitution(self):
        x,y=logic.V("x"),logic.V("y")
        a=logic.All("y",logic.Eq(x,y))
        result=logic.substitute(a,"x",y)
        self.assertEqual(logic.free(result),{"y"})
        self.assertNotEqual(result[1],"y")
        self.assertEqual(logic.substitute(logic.All("x",a),"x",y),logic.All("x",a))

    def test_logic_side_conditions_and_arithmetic_certificate(self):
        r=logic.demo(); self.assertTrue(r["verified"]); self.assertTrue(r["tampered_proof_rejected"])
        k=logic.Kernel({"zero":0},{},{})
        x=logic.V("x"); z=logic.F("zero"); p=logic.Eq(x,z); q=logic.Eq(z,z)
        a=logic.Imp(logic.All("x",logic.Imp(p,q)),logic.Imp(p,logic.All("x",q)))
        self.assertFalse(k.check([{"rule":"distribute","formula":a,"variable":"x","antecedent":p,"consequent":q}],a))
        with self.assertRaises(ValueError): logic.Kernel({"zero":0},{},{"unsound_open_assumption":p})
        self.assertFalse(k.check([{"rule":"mp","formula":q,"antecedent":0,"implication":0}],q))
        self.assertTrue(k.check([{"rule":"tautology","formula":logic.Imp(p,p)}],logic.Imp(p,p)))

    def test_wang_local_rules_against_operational_tm(self):
        c=wang.addition_machine()
        for state in c.states:
            for symbol in c.alphabet:
                if state!=c.halt and (state,symbol) not in c.transitions: continue
                for left,right in product(c.alphabet,repeat=2):
                    row=("B",left,wang.head(state,symbol),right,"B")
                    after=wang.direct_step(c,row)
                    local=tuple(c.rule(row[i-1] if i else "B",row[i],row[i+1] if i+1<len(row) else "B") for i in range(len(row)))
                    self.assertEqual(local,after)

    def test_wang_unknown_certificate_and_finite_failure(self):
        r=wang.certificate_demo()
        self.assertEqual(r["certificate"],"11")
        self.assertTrue(r["arithmetic_verified_independently"])
        self.assertTrue(r["tampered_input_rejected"])
        c=wang.addition_machine()
        bad=wang.search_certificate_rectangle(c,wang.addition_pattern(1,1,1),32)
        self.assertEqual(bad["status"],"exhausted_finite_rectangle")
        capped=wang.search_certificate_rectangle(c,wang.addition_pattern(1,1,2),32,node_limit=0)
        self.assertEqual(capped["status"],"unknown_budget")

if __name__=="__main__": unittest.main()
