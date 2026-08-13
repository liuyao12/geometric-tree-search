#!/usr/bin/env python3

import math

from materials_gcts_2d_generic_atlas import _score, layered_hexagonal_configuration
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_recursive_program import (
    actions_to_at_least, discover_recursive_program, explicit_apply,
    symbolic_count)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


def main() -> None:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    iqc, _ = oracle_patch(3, 9.0)
    fibonacci = make_input(9)
    planar = layered_hexagonal_configuration(
        "generic-program-30deg-hBN", 18.0,
        ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N")),
        (0.0, math.pi / 6), global_rotation=True)
    amorphous_sample = amorphous_hard_core_point_set(atom_count=507)
    amorphous = AtomicConfiguration(
        amorphous_sample.name, amorphous_sample.positions,
        amorphous_sample.species)

    cases = ((nacl, "translation_quotient"),
             (iqc, "internal_section_inflation"),
             (fibonacci, "substitution_product"),
             (planar, "planar_pose_address"))
    for configuration, family in cases:
        program = discover_recursive_program(configuration)
        assert program.family == family
        assert program.deterministic
        assert not program.family_label_used
        assert not program.heldout_atoms_used
        assert not program.physical_potential_used
        first = symbolic_count(configuration, program, 1)
        second = symbolic_count(configuration, program, 2)
        assert first > len(configuration.positions)
        assert second > first
        actions, count = actions_to_at_least(configuration, program)
        assert actions <= 6
        assert count >= 1_000_000

    planar_program = discover_recursive_program(planar)
    for actions in (1, 2):
        predicted = explicit_apply(planar, planar_program, actions)
        expected = layered_hexagonal_configuration(
            f"generic-program-heldout-{actions}",
            planar_program.observation_radius * 2 ** actions,
            ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N")),
            (0.0, math.pi / 6), global_rotation=True)
        assert _score(predicted, expected) == (1.0, 1.0, 1.0)

    rejected = discover_recursive_program(amorphous)
    assert rejected.family == "none"
    assert not rejected.deterministic
    print("family-blind recursive program interface: passed")


if __name__ == "__main__":
    main()
