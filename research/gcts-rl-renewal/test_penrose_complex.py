import copy
import unittest
import cyclotomic as ring
import penrose_complex as p
import audit_penrose_complex as audit


class ComplexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = p.corner_catalog()
        cls.stars = p.enumerate_stars(cls.catalog)

    def test_complete_independent_cyclic_partition_catalog(self):
        self.assertEqual(len(self.catalog), 40)
        self.assertEqual(sum(len(c["aliases"]) for c in self.catalog), 80)
        self.assertEqual({tuple(s["corners"]) for s in self.stars}, audit.cyclic_partition_sets(self.catalog))
        self.assertEqual(len(self.stars), 708)
        self.assertEqual({s["faces"] for s in self.stars}, set(range(3, 11)))

    def test_root_capacity_seams_incomplete_and_tampered_indices(self):
        star = self.stars[80]
        self.assertEqual(p.star_certificate(star["corners"], self.catalog), star)
        for seam in star["seams"]:
            self.assertEqual(len(seam["faces"]), 2)
            self.assertEqual(p.norm2(seam["endpoint"]), ring.ONE)
        for bad in (star["corners"][:-1], star["corners"]+[star["corners"][0]], [True], [40], []):
            with self.assertRaises(ValueError):
                p.star_certificate(bad, self.catalog)

    def test_exact_metric_bounds_and_degenerate_triangle(self):
        result = p.template_audit()
        self.assertEqual(result["barycentric_triangles_checked"], 160)
        self.assertEqual(result["unit_edges_checked"], 80)
        self.assertEqual(result["graph_distance_lipschitz_bound"], 12)
        self.assertEqual(p.cross2(ring.ONE, ring.ONE), ring.ZERO)
        changed = copy.deepcopy(p.VERTICES)
        changed["thick"] = tuple(p.scale(v, 2) for v in changed["thick"])
        original = p.VERTICES
        try:
            p.VERTICES = changed
            with self.assertRaises(ValueError):
                p.template_audit()
        finally:
            p.VERTICES = original

    def test_complete_star_does_not_complete_the_finite_patch(self):
        keys = [self.catalog[i]["key"] for i in self.stars[80]["corners"]]
        full, incomplete = p.complete_vertices(keys)
        self.assertIn(ring.ZERO, full)
        self.assertGreater(incomplete, 0)
        with self.assertRaises(ValueError):
            p.complete_vertices(keys+[keys[0]])

    def test_connectedness_counterexample_uses_distinct_vertex_cosets(self):
        control = p.periodic_controls(self.catalog)
        shift = control["second_layer_shift"]
        self.assertTrue(shift[2] or shift[3])
        full, _ = p.complete_vertices(control["root_placements"]+control["shifted_root_placements"])
        self.assertIn(ring.ZERO, full)
        self.assertIn(shift, full)
        self.assertTrue(control["vertex_cosets_disjoint"])

    def test_orientation_and_integer_translation_are_declared(self):
        for key in (("thick", False, ring.ZERO), ("thin", 10, ring.ZERO),
                    ("thick", 0, (True, 0, 0, 0)), ("thick", 0, (0, 0, 0))):
            with self.assertRaises(ValueError):
                p.placement(key)

    def test_artifact_omitted_star_and_forged_edge_partner_reject(self):
        report = {"prototype_vertices": audit.normalized(p.VERTICES), "corners": audit.normalized(self.catalog),
                  "stars": audit.normalized(self.stars), "template_bounds": p.template_audit(),
                  "comparison_controls": audit.normalized(p.periodic_controls(self.catalog))}
        omitted = copy.deepcopy(report)
        omitted["stars"].pop()
        with self.assertRaises(ValueError):
            audit.check_catalog_and_stars(omitted)
        forged = copy.deepcopy(report)
        forged["stars"][0]["seams"][0]["endpoint"] = list(ring.ZERO)
        with self.assertRaises(ValueError):
            audit.check_catalog_and_stars(forged)


if __name__ == "__main__":
    unittest.main()
