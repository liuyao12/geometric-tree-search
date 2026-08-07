#!/usr/bin/env python3

from materials_gcts_explicit_recursive_benchmark import evaluate


def test_learned_rules_materialize_two_recursive_parent_levels() -> None:
    result = evaluate()
    assert result.passed == result.total == 3
    assert result.crystal.atom_counts == (216, 1728, 13824)
    assert result.quasicrystal.atom_counts == (507, 1969, 8603)
    assert result.substitution_quasicrystal.atom_counts == (729, 3375, 13824)
    assert result.crystal.exact_each_action
    assert result.quasicrystal.exact_each_action
    assert result.substitution_quasicrystal.exact_each_action
    assert min(result.crystal.action_compression,
               result.quasicrystal.action_compression,
               result.substitution_quasicrystal.action_compression) > 4000
