#!/usr/bin/env python3

from materials_gcts_macro_derivation_benchmark import evaluate


def test_real_promoted_overlap_ports_remain_an_honest_red_growth_gate():
    result = evaluate()
    assert result.all_targets_sealed
    assert result.all_overlap_certificates_valid
    assert not result.any_real_growth_gate_passed
    assert tuple(case.system for case in result.cases) == (
        "NaCl-rocksalt", "Icosahedral-6D-model-set",
        "Cd5.7Yb-offcenter-seed")
    for case in result.cases:
        assert case.frozen_macro_productions > 0
        assert case.attempted_candidates > 0
        assert case.accepted_steps == 0
        assert case.level_emitted_nodes == (0,)
        assert case.proposed_novel_atoms == 0
        assert case.symbolic_count == case.explicit_count
        assert case.independent_count_verified
        assert not case.stationary_contract_available


if __name__ == "__main__":
    test_real_promoted_overlap_ports_remain_an_honest_red_growth_gate()
    print("real self-fed macro execution gate: honest red")
