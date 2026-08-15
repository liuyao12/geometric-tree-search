#!/usr/bin/env python3

from materials_gcts_iqc_multiwave_confirmatory_benchmark import evaluate


result = evaluate()
assert result.train_target_raw_id_intersection == 0
assert result.spatial_domains_disjoint
assert result.frozen_calibration_ratio == 15 / 21
assert result.maximum_waves == 5
assert result.maximum_accepted_per_wave == 40
assert result.consensus.accepted_per_wave == (3, 17, 4, 30, 5)
assert result.consensus.proposed_unique_atoms == 109
assert result.consensus.correct_unique_atoms == 109
assert result.consensus.wrong_unique_atoms == 0
assert result.consensus.precision == 1.0
assert not result.consensus.target_used_during_execution
assert result.exact_self_fed_continuation
assert not result.stationary_or_exponential_certificate
assert result.target_constructed_after_all_executions
assert result.family_phi_cell_target_unused_by_executor

print("IQC five-wave executed confirmation: all assertions passed")
