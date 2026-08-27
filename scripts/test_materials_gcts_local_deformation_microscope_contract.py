#!/usr/bin/env python3
"""Contract for the Build 167 local affine-deformation microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MATH = (ROOT / "apps/iqc-growth-live/relaxation-local-environment.js").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_affine_solver_exposes_rank_guarded_rotation_invariants():
    for token in (
        "export function affineDeformationInvariants",
        "normalizedSourceMomentDeterminant",
        "fullRankSource: false",
        "rightCauchyGreen",
        "meanNormalGreenLagrangeStrain",
        "deviatoricGreenLagrangeMagnitude",
        "equivalentShearStrain",
        "localVolumeChangeFraction",
        "normalizedRootD2Min",
    ):
        assert token in MATH


def test_interactive_four_mode_microscope_is_wired_to_one_frozen_field():
    for token in (
        'id="relaxationLocalEnvironmentMetric"',
        'value="nonaffine"',
        'value="shear"',
        'value="dilation"',
        'value="neighbor"',
    ):
        assert token in HTML
    for token in (
        "relaxationLocalEnvironmentMetric.value",
        'metric === "shear"',
        'metric === "dilation"',
        'metric === "neighbor"',
        "percentile90EquivalentShearStrain",
        "percentile90AbsoluteLocalVolumeChangeFraction",
        "compressionColor",
    ):
        assert token in APP
    assert ".local-deformation-layer select" in STYLE


def test_receipt_hashes_maps_and_preserves_claim_boundary():
    for token in (
        "bestAffine: record.bestAffine.map",
        "affineInvariantDefinition",
        "rankDeficiencyPolicy",
        "affineResolvedCenters",
        "rankDeficientCenters",
        "orientationReversingCenters",
        "recordsEmbedded: false",
        "localBestAffineMapsEmbedded: false",
        'physicalTimeUsed: false',
        'usedForGrowth: false',
    ):
        assert token in APP
    for phrase in (
        "not stress, elastic energy, modulus",
        "Rank-deficient cages withhold 3D strain",
        "Falk–Langer best-affine F",
    ):
        assert phrase in APP


def test_portal_narrative_and_primary_provenance_are_visible():
    assert "10.1103/PhysRevE.57.7192" in APP
    assert "Build 167" in README
    assert "Build 167" in DOCS
    assert "Green–Lagrange" in ATLAS
    assert "Rank-deficient cages" in ATLAS


def test_current_build_is_cache_busted():
    assert 'buildId: "20260827-265"' in APP
    assert 'app.js?v=20260827-265' in HTML
    assert 'relaxation-local-environment.js?v=20260826-2' in APP
    assert 'evidence-atlas.js?v=20260827-23' in HTML


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("materials local deformation microscope contract: passed")
