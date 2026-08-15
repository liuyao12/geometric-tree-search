import unittest
import itertools

import materials_gcts_propagated_marking as propagated
from materials_gcts_geometry_vm import compile_metric_overlap_from_seed
from materials_gcts_geometry_vm_benchmark import _compile_iqc_instruction
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_propagated_marking_benchmark import evaluate


class PropagatedMarkingBenchmarkTest(unittest.TestCase):
    def test_overlap_compiler_derives_scale_and_shells_from_seed(self):
        seed, _ = oracle_patch(3, 9.0)
        instruction = compile_metric_overlap_from_seed(seed)
        self.assertEqual(instruction.opcode, "overlap_section")
        self.assertEqual(len(instruction.payload.atlas.accepted_ports), 73)
        self.assertEqual(len(instruction.payload.section.accepted_pairs), 271)
        self.assertEqual(instruction.payload.seed_minimum_votes, 11)
        self.assertFalse(instruction.family_label_used)

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

    def test_address_macro_does_not_lift_output_coordinates(self):
        seed, instruction = _compile_iqc_instruction()
        marking = propagated.fit_propagated_marking(instruction, seed)
        original = propagated.lift_point

        def forbidden(*_args, **_kwargs):
            raise AssertionError("coordinate lift leaked into macro emission")

        propagated.lift_point = forbidden
        try:
            sites = tuple(itertools.islice(
                propagated.emit_marked_macro_sites(
                    instruction, marking, 20.0), 100))
        finally:
            propagated.lift_point = original
        self.assertEqual(len(sites), 100)


if __name__ == "__main__":
    unittest.main()
