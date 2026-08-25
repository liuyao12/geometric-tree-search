#!/usr/bin/env python3
"""Contract for target-blind mesoscopic growth-front morphology ordering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_front_morphology_is_soft_local_geometry() -> None:
    for element_id in (
        "frontMorphologySelect", "frontMorphologyWeightSelect", "frontMorphologyHint",
        "frontMorphologyBadge", "frontMorphologyBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "smooth", "facet", "tip"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML
    assert ".front-morphology-badge" in CSS

    assert "function frontMorphologyForCandidate(candidate" in APP
    assert "parent-to-candidate normal" in APP
    assert "const reach = 2.4 * referenceSpacing" in APP
    assert "sectors.add(Math.floor(angle / (2 * Math.PI) * 8) % 8)" in APP
    assert "const planeCoherence = Math.exp(-2 * depthStd)" in APP
    assert "const smoothScore = 2 * angularCoverage - 1" in APP
    assert "const tipScore = 1 - 2 * angularCoverage" in APP
    assert "const facetScore = 2 * backingFraction * planeCoherence - 1" in APP
    assert "occupiedSectors: [...sectors].sort" in APP
    assert "candidate.frontMorphology.occupiedSectors.forEach" in APP
    assert "parent proper-SE(3) tangent frame + parent-to-candidate normal" in APP
    assert "+ activeFrontMorphologyWeight() * evaluation.frontMorphology.score" in APP
    assert "mesoscopicFrontMorphologyRanking:" in APP

    for invariant in (
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "meanCurvatureInferred: false",
        "surfaceEnergyInferred: false",
        "capillaryPressureInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "Mesoscopic front morphology" in README
    assert "same exact candidate set" in normalized
    assert "not capillary thermodynamics" in normalized
    assert "not mean curvature" in normalized


if __name__ == "__main__":
    test_front_morphology_is_soft_local_geometry()
    print("mesoscopic front morphology contract: passed")
