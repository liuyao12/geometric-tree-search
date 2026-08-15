#!/usr/bin/env python3

from materials_gcts_iqc_action_consensus_benchmark import evaluate


result = evaluate(shuffled_runs=7)
assert result.train_candidates_after_censor <= result.train_candidates_before_censor
assert result.eval_candidates_after_censor <= result.eval_candidates_before_censor
assert result.calibration_gate_available
assert result.identical_candidate_actions_all_arms
assert not result.eval_outer_atoms_used_during_fit_calibration_or_enumeration
assert result.eval_consensus_95.placements == result.eval_overlap_only_matched.placements
assert result.eval_consensus_95.placements == result.eval_frequency_matched.placements
assert result.eval_consensus_99.emitted_site_precision >= .99
assert not result.integrated_as_default_marking

print("IQC action-level overlap consensus: all assertions passed")
