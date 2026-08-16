#!/usr/bin/env python3

from materials_gcts_cdyb_confirmatory_benchmark_v2 import evaluate


def test_one_shot_cdyb_confirmation_v2():
    result = evaluate()
    assert len(result.pretarget_abort_erratum_digest) == 64
    assert result.protocol_digest == \
        "3d4dfca24c7526baff14a2258c715e4caf0631af1c28af8ab41860b8e593c3f6"
    assert result.source_files_verified
    assert result.train_artifacts_verified
    assert result.regenerated_training_corpus_digest == \
        "d4ddc8ae825f0e8919a2fd107633b32931dceca44bade4b6f6e2370fec675542"
    assert result.regenerated_model_digest == \
        "da3aef6b32bbf69ce4013d846e1535a1d90521db446404c10c5dd3fcedf67dbe"
    assert result.first_wave_candidates_identical_all_arms
    assert result.null_trials == 31
    assert result.target_factory_calls == 1
    assert result.all_order_events_passed
    assert not result.target_used_before_open
    assert not result.refit_or_retuning_after_target


if __name__ == "__main__":
    test_one_shot_cdyb_confirmation_v2()
    print("CdYb confirmation v2: passed")
