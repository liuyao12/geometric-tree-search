#!/usr/bin/env python3

from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_iqc_leakage_safe_dataset import split_iqc_train_guard_test
from materials_gcts_iqc_leakage_safe_dataset_benchmark import evaluate


raw, _ = oracle_patch(4, 12.0)
split = split_iqc_train_guard_test(raw.species, raw.positions)
assert set(split.train.global_ids).isdisjoint(split.guard.global_ids)
assert set(split.train.global_ids).isdisjoint(split.heldout.global_ids)
assert set(split.guard.global_ids).isdisjoint(split.heldout.global_ids)
assert set(split.fit.global_ids) == set(split.train.global_ids).union(
    split.guard.global_ids)
assert not split.heldout_payload_exposed_to_learner
assert not split.oracle_family_phi_cell_fields_in_fit_payload

audit = evaluate()
assert audit.train_atoms and audit.guard_atoms and audit.heldout_atoms
assert audit.exact_domain_id_disjointness
assert audit.frozen_support_types > 0
assert 0 <= audit.heldout_unknown_fraction <= 1
assert (audit.heldout_known_atoms + audit.heldout_unknown_atoms ==
        audit.heldout_atoms)
assert audit.admitted_macro_types > 0
assert audit.dense_train_macro_occurrences > 0
assert audit.frozen_vocabulary_transfer_without_refit
assert not audit.heldout_atoms_used_by_fit_or_dense_matching
assert not audit.oracle_lifts_family_phi_cell_used_by_learner

print("IQC leakage-safe dataset adapter: all assertions passed")
