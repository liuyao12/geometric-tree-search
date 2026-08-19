#!/usr/bin/env python3
"""Fast receipt-validation tests; the real target-opening test is separate."""

from materials_gcts_iqc_extended_fusion_development_benchmark import (
    _digest, validate_candidate_receipt)


def _fake_receipt():
    from materials_gcts_iqc_extended_development_preregistration import (
        DEVELOPMENT_CENTERS)
    from materials_gcts_iqc_extended_fusion_execution_preregistration import (
        FUSION_ARTIFACT_DIGEST, FUSION_MODEL_DIGEST, audit)
    action = [[0., 0., 0., "X"], [1., 0., 0., "Y"], [0., 1., 0., "Z"]]
    payload = {
        "format": "gcts-iqc-extended-fusion-candidates-v1",
        "execution_manifest_digest": audit().manifest_digest,
        "fusion_artifact_digest": FUSION_ARTIFACT_DIGEST,
        "fusion_model_digest": FUSION_MODEL_DIGEST,
        "seed_radius": 9., "target_radius": 14.562305898749054,
        "oracle_lift_bound": 44,
        "nuclei": [{
            "center": list(center), "seed_atoms": 1,
            "candidate_counts_by_depth": [1, 1, 1],
            "retained_counts_by_depth": [1, 1, 1],
            "terminal_count": 1, "candidate_digest": "0" * 64,
            "scalar_stable_index": 0, "fusion_stable_index": 0,
            "scalar_order": [0], "fusion_order": [0],
            "terminal_actions": [action],
        } for center in DEVELOPMENT_CENTERS],
        "target_open_count": 0, "target_used": False,
    }
    payload["receipt_digest"] = _digest(payload)
    return payload


def test_receipt_validation_is_target_free_and_fail_closed():
    payload = _fake_receipt()
    assert validate_candidate_receipt(payload) is payload
    payload["nuclei"][0]["fusion_order"] = []
    payload["receipt_digest"] = _digest(payload)
    try:
        validate_candidate_receipt(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete candidate order was accepted")


if __name__ == "__main__":
    test_receipt_validation_is_target_free_and_fail_closed()
    print("extended IQC frozen-fusion receipt tests passed")
