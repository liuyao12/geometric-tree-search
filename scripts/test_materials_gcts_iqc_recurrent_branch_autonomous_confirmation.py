#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures/iqc_recurrent_branch_autonomous_confirmation.json"
SOURCE = ROOT / "materials_gcts_iqc_recurrent_branch_autonomous_confirmation.py"


def test_sealed_recurrent_branch_confirmation_is_preserved_honestly():
    report = json.loads(FIXTURE.read_text())
    assert report["preregistration_digest"] == \
        "6099d968bb0cef9cd73d3ea2dc17e117471b4daffd021f03e05e469ebf3b936e"
    assert report["confirmation_center"] == [40., -40., -80.]
    assert report["oracle_lift_bound"] == 44
    assert report["target_bound_plus_one_stable"]
    assert report["seed_atoms"] == 482
    assert report["target_atoms"] == 2033
    assert report["candidate_counts_by_depth"] == [4, 16, 16]
    assert report["retained_configurations_by_depth"] == [4, 4, 4]
    assert report["terminal_configurations"] == 4
    assert report["exact_terminal_configurations"] == 0
    assert report["correct_sites"] == 2
    assert report["false_sites"] == 1
    assert report["precision"] == 2 / 3
    assert report["candidate_digest"] == \
        "9ef36560339e20e6b384a6a85199e5e277b5213a3e9845ef81b07526fd1cda48"
    assert report["terminal_digest"] == \
        "bca0a6be8cf4230126f8a472fde50d14e34fb02811740e96a56d6388114e6d0a"
    assert report["trace_digest_before_target_open"] == \
        "0a30b5945c7fdcc81f4f71e3e6ccbdbdcd3bcd3b88936601afa27430290fcf80"
    assert report["target_open_count"] == 1
    assert report["target_materialized_after_execution"]
    assert not report["target_used_for_state_or_branch_fit"]
    assert not report["target_used_for_candidate_or_feature_generation"]
    assert not report["target_used_for_ranking_or_execution"]
    assert not report["exact_candidate_geometry_changed"]
    assert report["self_fed_depth"] == 3
    assert not report["autonomous_top1_gate_passed"]
    assert not report["stationary_or_exponential_certificate"]
    source = SOURCE.read_text()
    assert source.index("frozen = prepare_target_blind_execution()") < \
        source.index("target, target_stable = _open_target_once()")


if __name__ == "__main__":
    test_sealed_recurrent_branch_confirmation_is_preserved_honestly()
    print("recurrent branch autonomous confirmation regression passed")
