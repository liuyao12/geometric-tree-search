#!/usr/bin/env python3
"""Fast target-free contracts for Cd--Yb confirmatory protocol v2."""

from pathlib import Path

from materials_gcts_cdyb_confirmatory_preregistration_v2 import (
    ConfirmatoryMetrics, FROZEN_MODEL_DIGEST, FROZEN_SOURCE_FILE_HASHES,
    PROTOCOL_V1_DIGEST, PROTOCOL_V2, SOURCE_COMMIT, TRAIN_CORPUS_DIGEST,
    TRAIN_AUDIT_DIGEST,
    OneShotOrderGuard,
    audit_frozen_manifests, audit_frozen_source_files,
    evaluate_preregistered_gates,
    plus_one_lower_tail, plus_one_upper_tail, protocol_v2_digest)


def test_manifests_and_decisions_are_frozen_without_oracle_import():
    audit = audit_frozen_manifests()
    assert SOURCE_COMMIT == "51090f27da810177f3b68c1cb3ebd90b4b17efe4"
    assert len(PROTOCOL_V1_DIGEST) == len(TRAIN_CORPUS_DIGEST) == \
        len(FROZEN_MODEL_DIGEST) == len(TRAIN_AUDIT_DIGEST) == 64
    assert TRAIN_AUDIT_DIGEST == \
        "0796c2e60517fbf475ea383f1cc86b2f6cdd38efa2cad7f7c85b5818c3112c62"
    assert audit["corpus_manifest_digest_matches"]
    assert audit["actual_training_corpus_digest"] == TRAIN_CORPUS_DIGEST
    assert audit["model_digest_matches"]
    assert not audit["target_or_oracle_imported"]
    assert PROTOCOL_V2.expanded_shift_corpus_admitted
    assert PROTOCOL_V2.probability_threshold is None
    assert PROTOCOL_V2.top_budget_per_wave == 5
    assert PROTOCOL_V2.maximum_waves_per_level == 3
    assert PROTOCOL_V2.maximum_hierarchy_levels == 4
    assert PROTOCOL_V2.comparison_arms == (
        "marked: frozen continuous model", "unmarked: stable candidate key",
        "diagnostic: frozen macro-frequency baseline",
        "nulls: within-window shuffled-label refits")
    assert PROTOCOL_V2.later_wave_candidate_divergence_expected
    assert PROTOCOL_V2.shuffle_trials == 31
    assert PROTOCOL_V2.frozen_source_file_hashes == FROZEN_SOURCE_FILE_HASHES
    assert all(matches for _name, matches in audit_frozen_source_files(
        Path(__file__).parent))
    assert len(protocol_v2_digest()) == 64


def test_plus_one_null_and_gate_conjunction_are_exact():
    assert plus_one_upper_tail(2., (1.,) * 31) == 1 / 32
    assert plus_one_upper_tail(1., (1.,) * 31) == 1.
    assert plus_one_lower_tail(1., (2.,) * 31) == 1 / 32
    assert plus_one_lower_tail(2., (2.,) * 31) == 1.
    passing = ConfirmatoryMetrics(.8, .95, .5, 1/32, 1/32, 1/32,
                                  2., 3, .2)
    assert evaluate_preregistered_gates(passing) == (True, True)
    primary_only = ConfirmatoryMetrics(.8, .95, .5, 1/32, 1/32, 1/32,
                                       2., 2, .2)
    assert evaluate_preregistered_gates(primary_only) == (True, False)
    failed = ConfirmatoryMetrics(.79, 1., 1., 1/32, 1/32, 1/32, 3., 4, 1.)
    assert evaluate_preregistered_gates(failed) == (False, False)


def test_single_use_target_factory_order_is_mechanically_enforced():
    guard = OneShotOrderGuard()
    try:
        guard.open_target(lambda: "forbidden")
    except RuntimeError:
        pass
    else:
        raise AssertionError("target opened before artifacts froze")
    try:
        guard.record("model-frozen", FROZEN_MODEL_DIGEST)
    except RuntimeError:
        pass
    else:
        raise AssertionError("out-of-order freeze event was accepted")
    for event, digest in (
        ("protocol-verified", protocol_v2_digest()),
        ("training-artifacts-verified", TRAIN_CORPUS_DIGEST),
        ("model-frozen", FROZEN_MODEL_DIGEST),
        ("seed-opened", "seed"),
        ("first-wave-candidates-frozen", "candidates"),
        ("controls-frozen", "controls"),
        ("execution-frozen", "execution")):
        guard.record(event, digest)
    calls = []
    target = guard.open_target(lambda: calls.append(1) or "fake-target")
    assert target == "fake-target" and calls == [1]
    guard.record_score("execution")
    audit = guard.audit()
    assert audit["target_factory_calls"] == 1
    assert audit["execution_frozen_before_target"] and audit["scored_once"]
    for operation in (
        lambda: guard.open_target(lambda: "again"),
        lambda: guard.record("execution-frozen", "changed"),
        lambda: guard.record_score("execution")):
        try:
            operation()
        except RuntimeError:
            pass
        else:
            raise AssertionError("one-shot guard allowed a repeated action")


if __name__ == "__main__":
    test_manifests_and_decisions_are_frozen_without_oracle_import()
    test_plus_one_null_and_gate_conjunction_are_exact()
    test_single_use_target_factory_order_is_mechanically_enforced()
    print("CdYb confirmatory preregistration v2: passed")
