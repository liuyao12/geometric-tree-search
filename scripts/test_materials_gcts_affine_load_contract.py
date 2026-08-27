#!/usr/bin/env python3
"""Contract for prescribed affine loading as a geometric metric."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_affine_load_deforms_only_the_soft_metric() -> None:
    for element_id in (
        "affineLoadSelect",
        "affineLoadMagnitudeSelect",
        "affineLoadHint",
        "affineLoadBadge",
        "affineLoadGlyph",
        "affineLoadBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML

    for mode in ("none", "hydro-compress", "hydro-tension", "z-tension", "xy-shear",
                 "archive-stress", "archive-stress-reverse"):
        assert f'value="{mode}"' in HTML
    for magnitude in ("0.01", "0.02", "0.04"):
        assert f'value="{magnitude}"' in HTML

    assert "function affineLoadModeLabel(mode = affineLoadMode)" in APP
    assert "function affineLoadTensor()" in APP
    assert "function applyAffineLoad(vector)" in APP
    assert "function affineLoadedGeometricStrainForFreshSites" in APP
    assert "function effectiveGeometricStrain(evaluation)" in APP
    assert "applyAffineLoad(projected[second].p.clone().sub(projected[first].p))" in APP
    assert "- activeGeometricStrainWeight() * effectiveGeometricStrain(evaluation).total" in APP
    assert 'id: "affine-load"' in APP
    assert "entry.baseScore - .16 * entry.evaluation.geometricStrain.total" in APP
    assert "entry.baseScore - .16 * effectiveGeometricStrain(entry.evaluation).total" in APP

    assert "deformationGradient:" in APP
    assert "candidateCoordinatesChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "modulusOrStressInferred: false" in APP
    assert "prescribedStrainMagnitude" in APP
    assert "unloadedAcceptedMean" in APP
    assert "unloadedRejectedMean" in APP

    assert "prescribed affine loading" in README.lower()
    assert "Exact atom coordinates" in README
    assert "counterfactual policy table" in README
    assert "not stress, pressure, modulus" in README


if __name__ == "__main__":
    test_affine_load_deforms_only_the_soft_metric()
    print("prescribed affine loading contract: passed")
