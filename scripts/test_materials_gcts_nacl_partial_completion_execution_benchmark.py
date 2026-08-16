#!/usr/bin/env python3

from materials_gcts_nacl_partial_completion_execution_benchmark import evaluate


def test_nacl_whole_macro_batch_is_exact_but_not_action_compressed():
    result = evaluate()
    assert result.atoms == 216 and result.seed_atoms == 32
    assert result.seed_occurrences == 192
    assert result.candidate_counts == (144, 0)
    assert result.accepted_whole_macros == (12, 0)
    assert result.emitted_atoms == result.correct_atoms == 24
    assert result.wrong_atoms == 0
    assert result.primitive_child_actions == result.whole_macro_actions == 12
    assert result.symbolic_action_compression == 1.
    assert result.exact_certificates
    assert result.candidate_digests_frozen_before_scorer
    assert not result.target_used_for_execution
    assert result.gate_passed


if __name__ == "__main__":
    test_nacl_whole_macro_batch_is_exact_but_not_action_compressed()
    print("NaCl partial completion execution benchmark: passed")
