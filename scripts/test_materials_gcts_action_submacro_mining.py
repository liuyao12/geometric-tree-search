#!/usr/bin/env python3
"""Repeated and noncongruent controls for exact action submacros."""

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_action_submacro_mining import (
    ActionMacroCorpusEntry, mine_action_submacros)
from test_materials_gcts_action_macro_promotion import (
    _synthetic_three_wave_result)


def test_recurring_connected_submacros_have_disjoint_positive_mdl_proofs():
    program, batch = _synthetic_three_wave_result()
    actions = promote_batch_action_macros(program, batch)
    mined = mine_action_submacros(program, actions.macros)
    assert mined.submacro_types
    assert not mined.target_used
    assert all(len(item.occurrences) >= 2 and item.mdl_saving > 0 and
               item.maximum_occurrence_atom_overlap_fraction <= .1 and
               item.exact_induced_graph_verified and
               item.proper_se3_colored_union_verified and
               item.boundary_slots
               for item in mined.submacro_types)
    assert any(len(item.node_types) == 3 and
               {occurrence.wave for occurrence in item.occurrences} ==
               {1, 2, 3} for item in mined.submacro_types)
    for item in mined.submacro_types:
        node_sets = [set(occurrence.source_node_ids)
                     for occurrence in item.occurrences]
        assert all(not left.intersection(right)
                   for index, left in enumerate(node_sets)
                   for right in node_sets[index + 1:])


def test_noncongruent_third_wave_is_not_a_three_node_occurrence():
    program, batch = _synthetic_three_wave_result(noncongruent_third=True)
    actions = promote_batch_action_macros(program, batch)
    mined = mine_action_submacros(program, actions.macros)
    three_node = [item for item in mined.submacro_types
                  if len(item.node_types) == 3]
    assert three_node
    assert all(3 not in {occurrence.wave for occurrence in item.occurrences}
               for item in three_node)
    # The unchanged two-child face is still honestly reusable.
    assert any(len(item.node_types) == 2 and
               3 in {occurrence.wave for occurrence in item.occurrences}
               for item in mined.submacro_types)


def test_disjoint_patch_namespace_prevents_false_node_id_overlap():
    program, batch = _synthetic_three_wave_result()
    actions = promote_batch_action_macros(program, batch)
    reused = actions.macros[0]
    mined = mine_action_submacros(program, (
        ActionMacroCorpusEntry("patch-A", reused),
        ActionMacroCorpusEntry("patch-B", reused)))
    assert mined.source_patches == 2
    assert mined.submacro_types
    assert all({occurrence.patch_id for occurrence in item.occurrences} ==
               {"patch-A", "patch-B"}
               for item in mined.submacro_types)


if __name__ == "__main__":
    test_recurring_connected_submacros_have_disjoint_positive_mdl_proofs()
    test_noncongruent_third_wave_is_not_a_three_node_occurrence()
    test_disjoint_patch_namespace_prevents_false_node_id_overlap()
    print("recurring exact action submacro mining: passed")
