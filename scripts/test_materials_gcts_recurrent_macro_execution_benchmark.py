#!/usr/bin/env python3
"""Slow sealed NaCl/IQC recurrent-macro execution regression."""

import inspect

from materials_gcts_recurrent_macro_execution_benchmark import evaluate
from materials_gcts_recurrent_macro_executor import (
    execute_recurrent_macro_program)


def test_target_blind_recurrent_macro_execution_control_and_iqc_gate():
    assert "target" not in inspect.signature(
        execute_recurrent_macro_program).parameters
    result = evaluate()
    assert result.executor_target_argument_absent
    assert result.all_candidates_from_frozen_ports
    assert result.all_acceptances_self_fed

    nacl = result.nacl
    assert nacl.green_control
    assert nacl.proposed_novel_atoms == nacl.correct_novel_atoms == 64
    assert nacl.wrong_novel_atoms == 0 and nacl.precision == 1.0
    assert nacl.exact_certificates
    assert not nacl.target_used_for_proposals_or_ranking
    assert not nacl.spatially_disjoint_train_and_evaluation
    assert not nacl.rejection_trace_complete  # Aggregate counts retained.

    iqc = result.iqc_disjoint
    assert iqc.train_atoms == 4405 and iqc.training_patches == 5
    assert iqc.raw_macro_types == 322
    assert iqc.recurrent_macro_types == 141
    assert iqc.seed_atoms == 226 and iqc.seed_macro_occurrences == 2
    assert iqc.target_atoms == 873
    assert iqc.eligible_candidates_by_wave == (44, 18, 0)
    assert iqc.waves == (16, 8, 0)
    assert iqc.emitted_atoms_by_wave == (92, 56, 0)
    assert iqc.proposed_novel_atoms == 148
    assert iqc.correct_novel_atoms == 136
    assert iqc.wrong_novel_atoms == 12
    assert iqc.precision == 136 / 148
    assert iqc.recall_outside_seed == 136 / (873 - 226)
    assert iqc.exact_certificates and iqc.rejection_trace_complete
    assert iqc.spatially_disjoint_train_and_evaluation
    assert not iqc.target_used_for_proposals_or_ranking
    assert not iqc.green_control

    extended = result.iqc_extended_non_disjoint
    assert extended.target_atoms == 7862
    assert extended.eligible_candidates_by_wave == (44, 46, 114)
    assert extended.waves == (16, 24, 22)
    assert extended.emitted_atoms_by_wave == (92, 182, 142)
    assert extended.proposed_novel_atoms == 416
    assert extended.correct_novel_atoms == 374
    assert extended.precision == 374 / 416
    assert not extended.spatially_disjoint_train_and_evaluation
    assert not extended.target_used_for_proposals_or_ranking
    assert (extended.candidate_digests_by_wave[0] ==
            iqc.candidate_digests_by_wave[0])


if __name__ == "__main__":
    test_target_blind_recurrent_macro_execution_control_and_iqc_gate()
    print("sealed recurrent-macro execution benchmark: passed")
