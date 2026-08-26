#!/usr/bin/env python3
"""Source contract for variable-cell-safe archived relaxation displacements."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_interactive_displacement_layer_and_readout_are_present():
    for token in (
        'id="relaxationDisplacementState"',
        'id="relaxationDisplacementToggle"',
        'id="relaxationDisplacementToggleLabel"',
    ):
        assert token in HTML
    for token in (
        "function relaxationDisplacementField()",
        "Selected → final non-affine displacement",
        "relaxationDisplacementToggle.checked",
        "nonAffineSegments",
        "affineSegments",
    ):
        assert token in APP
    assert ".relaxation-displacement-state" in STYLE


def test_periodic_affine_and_nonaffine_terms_are_kept_separate():
    for token in (
        "sourceFractional = sourceCartesian.clone().applyMatrix3(sourceContext.inverse)",
        "targetFractional = targetCartesian.clone().applyMatrix3(targetContext.inverse)",
        "fractionalChange.getComponent(axis) - Math.round(fractionalChange.getComponent(axis))",
        "nonAffine = fractionalChange.applyMatrix3(targetContext.matrix)",
        "affine = sourceFractional.clone().applyMatrix3(targetContext.matrix).sub(sourceCartesian)",
        'nonAffineRmsAngstrom: rms("nonAffine")',
        'affineRmsAngstrom: rms("affine")',
        "targetVolume / sourceVolume - 1",
    ):
        assert token in APP


def test_receipt_hashes_derived_vectors_without_embedding_them():
    for token in (
        "relaxationDisplacementRecords",
        "relaxationDisplacementSha256",
        "selectedToFinalDisplacement",
        "viewportLengthsNormalizedForVisibility: true",
        "vectorsEmbedded: false",
        "usedForClusterIdentification: false",
        "usedForMarkingLearning: false",
        "usedForGrowth: false",
    ):
        assert token in APP


def test_claim_boundary_does_not_turn_structure_differences_into_dynamics():
    for token in (
        "The displacement field is a difference between archived structures, not a physical path.",
        "Selected-to-final vectors compare two archived structures; they are not a trajectory.",
        "No velocity, integration step, optimizer clock, minimum-energy path, transition probability, or growth rate is inferred",
    ):
        assert token in APP


def test_build_114_is_cache_busted():
    assert 'buildId: "20260825-135"' in APP
    assert 'app.js?v=20260825-135' in HTML


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("materials relaxation displacement contract: passed")
