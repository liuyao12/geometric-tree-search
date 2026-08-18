#!/usr/bin/env python3
"""Fast checks for the sealed harness; this test never opens the nucleus."""

from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    BRANCH_FEATURE_NAMES, EXPECTED_BRANCH_MODEL_DIGEST,
    EXPECTED_STATE_RUNTIME_DIGEST, _branch_features, _load_branch_model,
    _load_state_model)
from materials_gcts_recurrent_branch_value import recurrent_branch_value_digest


def test_frozen_models_and_branch_features_load_without_target():
    state, state_digest = _load_state_model()
    branch = _load_branch_model()
    assert state_digest == EXPECTED_STATE_RUNTIME_DIGEST
    assert len(state.state_probabilities) == 876
    assert len(state.token_marking.token_weights) == 148729
    assert not state.state_evidence
    assert recurrent_branch_value_digest(branch) == EXPECTED_BRANCH_MODEL_DIGEST
    assert branch.neighbors == 9
    features = _branch_features(
        (((0., 0., 0.), "X"), ((3., 0., 0.), "Y"),
         ((0., 4., 0.), "Z")), (.5, .25, .125), (2, 3, 4))
    assert len(features) == len(BRANCH_FEATURE_NAMES)
    assert features[1:] == (.125, .875, 9., 4., 3., 3., 4., 5.)


if __name__ == "__main__":
    test_frozen_models_and_branch_features_load_without_target()
    print("recurrent branch autonomous confirmation harness passed")
