import copy
import unittest
import cyclotomic as ring
import penrose_complex as c
import penrose_sectors as p
import penrose_star_search as s


class FullStarSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = c.corner_catalog()
        cls.stars = c.enumerate_stars(cls.catalog)
        cls.orbits, cls.lookup = s.orbit_catalog(cls.catalog, cls.stars)
        cls.keys = [cls.catalog[i]["key"] for i in cls.orbits[0][0]]
        cls.sample = s.search(p.Model(), cls.keys, 93000)

    def test_complete_rotation_orbits_and_all_aliases(self):
        self.assertEqual(len(self.orbits), 75)
        self.assertEqual(sum(len(m) for _, m in self.orbits), 708)
        self.assertEqual({member for _, members in self.orbits for member in members},
                         {tuple(star["corners"]) for star in self.stars})

    def test_positive_completion_target_generations_and_changed_prefix(self):
        self.assertEqual(self.sample["status"], "positive")
        state, witnesses = s.check_positive(self.keys, self.sample)
        self.assertTrue(witnesses)
        self.assertEqual(state.tile_generations[:len(self.keys)], [0]*len(self.keys))
        self.assertTrue(all(g == 1 for g in state.tile_generations[len(self.keys):]))
        bad = copy.deepcopy(self.sample)
        bad["placements"] = bad["placements"][1:]
        with self.assertRaises(ValueError):
            s.check_positive(self.keys, bad)

    def test_rotation_transfer_requires_every_exposed_witness(self):
        state, witnesses = s.check_positive(self.keys, self.sample)
        sample = {**self.sample, "frontier_witnesses": witnesses}
        for rotation in range(10):
            target = tuple(sorted(self.lookup[(self.catalog[i]["start"]+rotation) % 10,
                                              self.catalog[i]["width"]] for i in self.orbits[0][0]))
            self.assertEqual(s.transformed_positive(sample, rotation, target, self.catalog)[0], len(state.order))
        bad = copy.deepcopy(sample)
        bad["frontier_witnesses"].pop()
        with self.assertRaises(ValueError):
            s.transformed_positive(bad, 0, self.orbits[0][0], self.catalog)

    def test_budget_is_unknown_and_fabricated_negative_rejects(self):
        limited = s.search(p.Model(), self.keys, 93000, node_limit=0)
        self.assertEqual(limited["status"], "unresolved")
        self.assertIsNone(limited["proof"])
        self.assertFalse(s.check_negative(self.keys, {"dead": (ring.ZERO, 0)})[0])

    def test_multi_seed_zero_domains_incremental_graph_and_rollback(self):
        model = p.Model()
        state = s.initial_state(model, self.keys)
        graph = p.Graph(model, state)
        self.assertEqual(graph.domains, p.exhaustive_domains(model, state))
        self.assertTrue(all(g == 0 for g in state.generations.values()))
        self.assertEqual(state.active, {slot for key in self.keys for slot in model.placement(key).active})
        original_state = copy.deepcopy(state.__dict__)
        original_domains = copy.deepcopy(graph.domains)
        original_edges = copy.deepcopy(graph.edges)
        _, _, choices = graph.decision(state, {v for v, _ in state.active})
        child, cg = state.copy(), graph.copy()
        cg.update(child, child.place(model.placement(choices[0])))
        self.assertEqual(cg.domains, p.exhaustive_domains(model, child))
        self.assertEqual(state.__dict__, original_state)
        self.assertEqual(graph.domains, original_domains)
        self.assertEqual(graph.edges, original_edges)

    def test_explicit_marked_control_failure_uses_independent_domains(self):
        # Restrictive control only. The discovery runner always uses Model().
        markings = {kind: {(v, sector): 40*i+10*j+sector
                           for j, v in enumerate(p.VERTICES[kind]) for sector in range(10)}
                    for i, kind in enumerate(p.KINDS)}
        model = p.Model(markings)
        keys = [("thick", 0, ring.ZERO)]
        sample = s.search(model, keys, 94000)
        self.assertEqual(sample["status"], "negative")
        self.assertEqual(s.check_negative(keys, sample["proof"], p.Model(markings)), (True, 1))
        self.assertFalse(s.check_negative(keys, sample["proof"])[0])


if __name__ == "__main__":
    unittest.main()
