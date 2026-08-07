#!/usr/bin/env python3

from materials_gcts_cod_approximant_benchmark import evaluate


def test_real_cod_approximant_has_recursive_internal_hierarchy() -> None:
    result = evaluate()
    assert result.cod_id == "1521830"
    assert result.measured_parent_atoms == 314
    assert result.chemical_elements == 3
    assert result.point_colors == ("Ta", "Ta/V", "Te")
    assert all(support > 0 for support in result.hierarchy_supports)
    assert result.hierarchy_supports[-1] >= 100
    assert min(result.hierarchy_cover_fraction) > 0.95
    assert result.color_marking_changes_hierarchy
    assert result.inferred_order == "periodic crystalline approximant"
    assert result.quasicrystal_label_rejected
    assert result.atom_counts == (314, 2512, 20096, 160768, 1286144)
    assert result.explicit_action_two_exact
    assert result.atomwise_actions_per_macro_action == 9891.0
