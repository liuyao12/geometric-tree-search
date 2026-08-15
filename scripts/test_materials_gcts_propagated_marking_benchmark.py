import unittest

import materials_gcts_propagated_marking as propagated
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_propagated_marking_benchmark import evaluate


class PropagatedMarkingBenchmarkTest(unittest.TestCase):
    def test_seed_marks_drive_two_exact_recursive_levels(self):
        result = evaluate()
        self.assertEqual(result.training_atoms, 507)
        self.assertEqual(result.final_atoms, 1689)
        self.assertEqual(result.exact_added_sites, 1182)
        self.assertEqual(tuple(level.exact_sites for level in result.levels),
                         (642, 540, 0, 0, 0, 0))
        self.assertEqual(result.marking_dimension, 3)
        self.assertEqual(result.port_arity, 2)
        self.assertFalse(result.coordinate_lift_used_at_inference)
        self.assertFalse(result.global_section_queried_at_inference)
        self.assertFalse(result.heldout_atoms_inserted)
        self.assertTrue(result.exact_colored_growth)
        self.assertFalse(result.exponential_growth)
        self.assertTrue(result.local_marking_gate_passed)

    def test_inference_does_not_lift_a_coordinate(self):
        seed, instruction = _compile_iqc_instruction()
        marking = propagated.fit_propagated_marking(instruction, seed)
        state = propagated.initial_marked_configuration(seed, marking)
        original = propagated.lift_point

        def forbidden(*_args, **_kwargs):
            raise AssertionError("coordinate lift leaked into inference")

        propagated.lift_point = forbidden
        try:
            wave = propagated.execute_propagated_wave(
                instruction, marking, state, level=1)
        finally:
            propagated.lift_point = original
        self.assertEqual(len(wave.emitted_sites), 582)


if __name__ == "__main__":
    unittest.main()
