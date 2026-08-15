#!/usr/bin/env python3

from materials_gcts_iqc_action_submacro_recurrence_audit import evaluate


result = evaluate()

assert result.patches == 5
assert result.exact_input_actions == 141
assert result.candidate_occurrences == 19547
assert result.exact_semantic_classes == 18931
assert result.recurrent_classes == 344
assert len(result.admitted_types) == 344
assert result.admitted_by_node_count == ((2, 20), (3, 53),
                                         (4, 111), (5, 160))
assert result.promotable_types == 344
assert result.maximum_independent_patch_support == 2
assert result.types_with_three_independent_patches == 0
assert result.maximum_admitted_occurrence_atom_overlap_fraction <= .1
assert all(item.independent_patch_support >= 2 and item.mdl_saving > 0
           for item in result.admitted_types)
assert all(item.promotable and len(item.occurrences) >= 2
           for item in result.admitted_types)
assert all(len({occurrence.patch_id for occurrence in item.occurrences}) ==
           len(item.occurrences) for item in result.admitted_types)
assert not result.heldout_used
assert not result.family_phi_cell_used
assert not result.raw_type_or_production_id_used_as_semantics
assert result.train_labels_used_only_for_trace_construction
assert result.semantic_extension_available

print("clean IQC recurring action-submacro audit: all assertions passed")
