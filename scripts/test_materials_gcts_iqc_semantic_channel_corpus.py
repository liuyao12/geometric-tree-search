#!/usr/bin/env python3

from materials_gcts_iqc_semantic_channel_corpus import evaluate


def test_categorical_semantic_channels_fail_heldout_transfer():
    report = evaluate()
    assert report.training_nuclei == 5
    assert report.heldout_nuclei == 1
    assert report.training_channel_types == 20
    assert report.training_exact_channel_types == 4
    assert report.training_mixed_channel_types == 0
    assert report.heldout_exact_actions == 1
    assert report.heldout_channel_coverage == 0
    assert report.heldout_port_channel_coverage == 0
    assert report.heldout_coarse_channel_coverage == 0
    assert report.heldout_chemistry_channel_coverage == .25
    assert report.heldout_exact_actions_with_train_exact_channel == 0
    assert report.heldout_exact_actions_with_train_exact_port_channel == 0
    assert report.heldout_exact_actions_with_train_exact_coarse_channel == 0
    assert report.heldout_exact_actions_with_train_exact_chemistry_channel == 0
    assert not report.semantic_channel_transfers
    assert not report.target_used_for_channel_construction


if __name__ == "__main__":
    test_categorical_semantic_channels_fail_heldout_transfer()
    print("IQC semantic-channel corpus tests: passed")
