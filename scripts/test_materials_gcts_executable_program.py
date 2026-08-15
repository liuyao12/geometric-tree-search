import unittest

from materials_gcts_executable_program import (
    discover_executable_program, execute_program)
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import benchmark_systems


class ExecutableGrowthProgramTest(unittest.TestCase):
    def test_family_blind_entrypoint_selects_crystal_and_quasicrystal_rules(self):
        crystal = next(item for item in benchmark_systems()
                       if item.name == "NaCl-rocksalt")
        fibonacci = make_input(9)
        selected = tuple(discover_executable_program(seed)
                         for seed in (crystal, fibonacci))
        self.assertEqual(tuple(item.production_kind for item in selected),
                         ("translation_quotient", "substitution_product"))
        self.assertFalse(any(item.family_label_used for item in selected))
        self.assertEqual(len(execute_program(crystal, selected[0], 1)[0].positions),
                         1728)
        self.assertEqual(len(execute_program(fibonacci, selected[1], 1)[0].positions),
                         3375)


if __name__ == "__main__":
    unittest.main()
