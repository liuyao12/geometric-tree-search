"""Semantic checks for context sharing, structural hypotheses and fair roots."""
import json,unittest
from turtle import Model,State,Graph,rooted,growth_search,exhaustive_domains,verify_patch,SYMMETRIES
from spatial import canonical,moved
from spatial_context import ContextProposer
import boundary_grammar,coverage,diverse_motifs,logic,replay_proofs

class Progress(unittest.TestCase):
    def test_shared_cluster_identities_are_counted_once(self):
        model=Model();donor=growth_search(model,91000,4,100,3)
        self.assertEqual(donor["status"],"consistent_finite_patch")
        keys=donor["placements"];state=State()
        for key in keys[:2]:state.place(model.placement(key),seed=not state.order)
        graph=Graph(model,state);domain=graph.decision(state)[2]
        library=[{"expansion":canonical(keys),"count":1}]
        before=(state.totals.copy(),state.marks.copy(),state.selected.copy(),state.order.copy(),graph.fingerprint())
        actions=ContextProposer(library,128)(model,state,graph,domain,library,2)
        self.assertTrue(any(len(seq)==2 for seq in actions))
        self.assertTrue({(k,) for k in domain}<=set(actions))
        for seq in actions:
            child,g=state.copy(),graph.copy()
            for k in seq:
                self.assertNotIn(k,state.selected);self.assertIn(k,g.decision(child)[2])
                g.update(model,child,child.place(model.placement(k)))
            self.assertTrue(verify_patch(model,child.order))
        self.assertEqual((state.totals,state.marks,state.selected,state.order,graph.fingerprint()),before)
        self.assertGreater(model.metrics["spatial_shared_context_tiles"],0)

    def test_zero_proposal_budget_retains_all_base_moves(self):
        model=Model();state=rooted(model);graph=Graph(model,state);keys=graph.decision(state)[2]
        library=[{"expansion":canonical(state.order+[keys[0]])}]
        actions=ContextProposer(library,0)(model,state,graph,keys,library,4)
        self.assertEqual(set(actions),{(k,) for k in keys})

    def test_boundary_hypotheses_preserve_symmetry_but_drop_length(self):
        model=Model();keys=[(0,(0,0,0))]
        original=boundary_grammar.descriptors(model,keys)
        self.assertTrue(original["manifold_boundary"])
        for g in SYMMETRIES:
            self.assertEqual(boundary_grammar.descriptors(model,moved(keys,g,(7,-2,-5))),original)
        small=(((0,0,0),(2,-2,0),(0,2,-2)),)
        large=(tuple(tuple(2*x for x in p) for p in small[0]),)
        self.assertEqual(boundary_grammar.words(small),boundary_grammar.words(large))
        self.assertNotEqual(boundary_grammar.words(small,True),boundary_grammar.words(large,True))

    def test_diversity_category_is_group_invariant(self):
        keys=[(0,(0,0,0)),(1,(3,-2,-1)),(4,(1,2,-3))]
        for g in SYMMETRIES:self.assertEqual(diverse_motifs.category(keys),diverse_motifs.category(moved(keys,g)))

    def test_core_activation_rolls_back_and_matches_all_domains(self):
        model=Model();parent=rooted(model);graph=Graph(model,parent)
        before=(parent.roots.copy(),parent.generations.copy(),graph.fingerprint())
        child,g=parent.copy(),graph.copy();coverage.activate(model,child,g,coverage.hexagon(2))
        self.assertEqual(g.domains,exhaustive_domains(model,child))
        self.assertTrue(all(child.roots[p]==0 and child.generations[p]==0 for p in coverage.hexagon(2)))
        self.assertEqual((parent.roots,parent.generations,graph.fingerprint()),before)

    def test_nested_core_checkpoint_and_budget(self):
        model=Model();r=coverage.search(model,(0,1,2),seed=92000,node_limit=1000,seconds=5)
        self.assertEqual(r["status"],"consistent_finite_patch_with_core_coverage")
        for a,b in zip(r["checkpoints"],r["checkpoints"][1:]):
            self.assertEqual(b["placements"][:len(a["placements"])],a["placements"])
        for c in r["checkpoints"]:self.assertTrue(verify_patch(model,c["placements"],coverage.hexagon(c["radius"])))
        self.assertEqual(coverage.search(Model(),(0,1),node_limit=0)["status"],"unknown_budget")

    def test_serialized_proof_cannot_supply_a_new_axiom(self):
        data=json.loads(json.dumps(logic.demo()));self.assertTrue(replay_proofs.check_logic(data))
        forged={"proof":[{"rule":"axiom","name":"new_axiom","formula":data["target"]}],"target":data["target"]}
        self.assertFalse(replay_proofs.check_logic(forged))

if __name__=="__main__":unittest.main()
