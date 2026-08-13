#!/usr/bin/env python3

from materials_gcts_common_recursive_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert len(result.cases) == 4
    assert {case.learned_family for case in result.cases} == {
        "translation_quotient", "internal_section_inflation",
        "substitution_product", "planar_pose_address"}
    for case in result.cases:
        assert case.explicit_verified_actions == 2
        assert case.exact_position_species_each_action
        assert case.first_million_action <= 6
        assert case.first_million_atoms >= 1_000_000
        assert case.minimum_growth_factor > 3.0
        assert case.action_compression > 10_000
        assert case.symbolic_node_definitions <= 7
        assert case.marking_causal
        assert not case.family_label_used
        assert not case.heldout_atoms_used_for_learning
        assert not case.physical_potential_used
        assert case.explicit_output_is_linear
    assert result.amorphous_deterministic_rule_rejected
    assert result.shared_program_interface
    assert result.family_specific_backends_remain
    assert result.all_exact_two_level_certificates
    assert result.all_reach_million_in_at_most_six_actions
    assert result.all_minimum_growth_factors_above_three
    assert result.all_action_compressions_above_ten_thousand
    assert result.all_markings_causal
    assert result.benchmark_passed
    print("common recursive crystal/quasicrystal benchmark: passed")
    print(result)


if __name__ == "__main__":
    main()
