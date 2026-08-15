import unittest

from materials_gcts_cluster_promotion_benchmark import evaluate


class ClusterPromotionBenchmarkTest(unittest.TestCase):
    def test_self_generated_parent_promotes_and_amplifies(self):
        result = evaluate()
        self.assertEqual(result.training_atoms, 507)
        self.assertEqual(result.self_generated_parent_atoms, 1689)
        self.assertEqual(result.final_atoms, 31521)
        self.assertEqual(result.base_cluster_types, 30)
        self.assertEqual(result.promoted_cluster_types, 30)
        self.assertGreater(result.support_growth_factor, 3.0)
        self.assertEqual(result.maximum_promoted_cluster_support, 225)
        self.assertEqual(result.promoted_ports, 789)
        self.assertEqual(result.promoted_port_pairs, 13111)
        self.assertEqual(result.promoted_wave_sites, 3234)
        self.assertEqual(result.exact_promoted_wave_sites, 3234)
        self.assertGreater(result.promoted_wave_to_parent_ratio, 1.9)
        self.assertEqual(result.promoted_level_sites, (3234, 8924, 17674))
        self.assertEqual(result.exact_promoted_level_sites,
                         result.promoted_level_sites)
        self.assertGreater(min(result.promoted_level_growth_factors), 1.9)
        self.assertGreater(result.geometric_mean_level_growth, 2.3)
        self.assertFalse(result.heldout_atoms_used_for_promotion)
        self.assertFalse(result.global_section_queried_at_inference)
        self.assertTrue(result.larger_support_clusters_promoted)
        self.assertTrue(result.amplified_exact_growth)
        self.assertTrue(result.exponential_growth)
        self.assertTrue(result.promotion_gate_passed)


if __name__ == "__main__":
    unittest.main()
