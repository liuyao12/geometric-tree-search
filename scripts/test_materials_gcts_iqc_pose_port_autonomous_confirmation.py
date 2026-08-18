#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures" / "iqc_pose_port_autonomous_confirmation.json"
SOURCE = ROOT / "materials_gcts_iqc_pose_port_autonomous_confirmation.py"


def test_sealed_pose_port_confirmation_is_honest_and_immutable():
    report = json.loads(FIXTURE.read_text())
    assert report["preregistration_digest"] == \
        "39ad50d65f18b30a3d7f8b85abd5349de3e56f3edbc412460596378b0a99bb24"
    assert report["model_matches_preregistration"]
    assert report["frozen_recurrent_states"] == 437
    assert report["oracle_lift_bound"] == 32
    assert report["target_bound_plus_one_stable"]
    assert report["confirmation_center"] == [-50., 50., -10.]
    assert report["seed_atoms"] == 490
    assert report["target_atoms"] == 2064
    assert report["candidate_counts_by_depth"] == [4, 16, 16]
    assert report["retained_configurations_by_depth"] == [4, 4, 4]
    assert report["emitted_sites"] == 3
    assert report["correct_sites"] == 1
    assert report["false_sites"] == 2
    assert report["precision"] == 1 / 3
    assert report["candidate_digest"] == \
        "028acae9f4c2105f506b06de0e2c8d6aa238bd8d6e7fb3932c8d682af148529e"
    assert report["trace_digest_before_target_open"] == \
        "d2a0290f5bf819a7234803b71ac38fcb539e8ace4409b8156e2c73aeb6f6e49d"
    assert report["target_open_count"] == 1
    assert report["target_materialized_after_execution"]
    assert not report["target_used_for_candidate_generation"]
    assert not report["target_used_for_model_fit"]
    assert not report["exact_candidate_geometry_changed"]
    assert report["self_fed_depth"] == 3
    assert not report["autonomous_top1_gate_passed"]
    assert not report["stationary_or_exponential_certificate"]
    source = SOURCE.read_text()
    assert source.index("= _execute(") < source.index(
        "target, target_stable = _open_target_once()")


if __name__ == "__main__":
    test_sealed_pose_port_confirmation_is_honest_and_immutable()
    print("IQC pose-port autonomous confirmation fixture passed")
