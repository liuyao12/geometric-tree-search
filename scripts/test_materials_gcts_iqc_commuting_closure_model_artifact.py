#!/usr/bin/env python3
"""Serialization contract for the frozen commuting-closure model."""

from copy import deepcopy

from materials_gcts_iqc_commuting_closure_model_artifact import (
    load_default_marking, marking_from_payload)


def test_default_scalar_model_is_inert_and_development_sealed() -> None:
    model, payload = load_default_marking()
    assert payload["development_gate_passed"] is True
    assert payload["development_examples"] == 224
    assert payload["development_positive_examples"] == 16
    assert len(payload["development_source_fixture_sha256"]) == 4
    assert model.scalar.representation.name == "incidence"
    assert len(model.scalar.representation.feature_indices) == 9
    assert model.scalar.value.neighbors == 1
    assert len(model.scalar.value.normalized_examples) == 224
    assert model.training_groups == 4
    assert not model.target_used


def test_artifact_mutation_fails_closed() -> None:
    _model, payload = load_default_marking()
    altered = deepcopy(payload)
    altered["development_gate_passed"] = False
    try:
        marking_from_payload(altered)
    except ValueError:
        pass
    else:
        raise AssertionError("mutated commuting artifact was accepted")


if __name__ == "__main__":
    test_default_scalar_model_is_inert_and_development_sealed()
    test_artifact_mutation_fails_closed()
    print("IQC commuting closure model artifact tests passed")
