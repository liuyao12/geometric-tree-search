import unittest

from materials_gcts_common_executed_benchmark import evaluate


class CommonExecutedBenchmarkTest(unittest.TestCase):
    def test_three_family_blind_programs_execute_three_exact_actions(self):
        result = evaluate()
        self.assertEqual(tuple(case.atom_counts for case in result.cases), (
            (216, 1728, 13824, 110592),
            (507, 4923, 13847, 31521),
            (729, 3375, 13824, 59319)))
        self.assertEqual(result.explicit_atoms_scored, 252953)
        self.assertTrue(result.one_discovery_entrypoint)
        self.assertTrue(result.one_execution_entrypoint)
        self.assertTrue(result.all_three_actions_executed)
        self.assertTrue(result.all_exact)
        self.assertTrue(result.all_self_fed)
        self.assertTrue(result.exponential_style_all_cases)
        self.assertTrue(result.specialized_production_kinds_remain)
        self.assertTrue(result.cross_family_execution_gate_passed)
        self.assertFalse(result.single_generic_production_gate_passed)


if __name__ == "__main__":
    unittest.main()
