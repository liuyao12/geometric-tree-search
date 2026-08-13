#!/usr/bin/env python3

from dataclasses import replace
import math

from materials_gcts_2d_generic_atlas import layered_hexagonal_configuration
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_recursive_program import (
    discover_recursive_program, symbolic_count as legacy_symbolic_count)
from materials_gcts_typed_productions import (
    TypedProduction, _validated_program, actions_to_at_least,
    induce_typed_transform_program, symbolic_atom_count)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


def main() -> None:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    fibonacci = make_input(9)
    for configuration, types, children in (
            (nacl, 1, (8,)),
            (fibonacci, 8, (1, 2, 4, 8)),
            (layered_hexagonal_configuration(
                "typed-planar", 18.0,
                ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N")),
                (0.0, math.pi / 6), global_rotation=True), 2, (4,))):
        typed = induce_typed_transform_program(configuration)
        assert typed.deterministic
        assert len(typed.type_names) == types
        assert set(len(item.children) for item in typed.productions) == set(children)
        assert all(child.section_mark for item in typed.productions
                   for child in item.children)
        assert not typed.family_label_used
        assert not typed.physical_potential_used
        legacy = discover_recursive_program(configuration)
        for action in range(7):
            assert symbolic_atom_count(typed, action) == legacy_symbolic_count(
                configuration, legacy, action)
        action, count = actions_to_at_least(typed)
        assert action <= 6 and count >= 1_000_000

    sample = amorphous_hard_core_point_set(atom_count=507)
    amorphous = AtomicConfiguration(
        sample.name, sample.positions, sample.species)
    assert not induce_typed_transform_program(amorphous).deterministic

    typed = induce_typed_transform_program(nacl)
    conflict = replace(typed.productions[0], evidence_occurrences=1)
    try:
        _validated_program(
            typed.type_names, dict(zip(typed.type_names, typed.atomic_weights)),
            (*typed.productions, conflict),
            __import__("collections").Counter(dict(zip(
                typed.type_names, typed.root_counts))), "test", "test")
    except ValueError as error:
        assert "conflicting" in str(error)
    else:
        raise AssertionError("conflicting productions must be rejected")
    print("shared typed transform productions: passed")


if __name__ == "__main__":
    main()
