#!/usr/bin/env python3

from materials_gcts_iqc_overlap_consensus_benchmark import evaluate


result = evaluate(shuffled_runs=7)
assert result.train_crop_atoms > result.train_seed_atoms > 0
assert result.eval_crop_atoms > result.eval_seed_atoms > 0
assert result.train_eval_crop_domain_ids_disjoint
assert result.frozen_prototypes and result.frozen_ports
assert result.train_candidates and result.eval_candidates
assert result.identical_eval_candidates_all_arms
assert not result.eval_target_used_during_fit_calibration_or_candidate_enumeration
assert not result.oracle_family_phi_cell_used_by_learner
assert result.eval_consensus.proposals == result.eval_overlap_only.proposals
assert result.eval_consensus.proposals == result.eval_production_frequency.proposals
assert not result.causal_superiority_gate_passed
assert not result.integrated_as_default_marking

print("IQC overlap-consensus marking: all assertions passed")
