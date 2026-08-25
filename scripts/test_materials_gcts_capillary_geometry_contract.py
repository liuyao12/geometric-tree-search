#!/usr/bin/env python3
"""Contract for discrete solid-angle interface geometry and its claim boundary."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_capillary_geometry_is_target_blind_soft_interface_ordering() -> None:
    for element_id in ("capillaryGeometrySelect", "capillaryGeometryWeightSelect", "capillaryGeometryHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "pocket", "planar", "exposed"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function capillaryQuadratureDirections()" in APP
    assert "const count = 32" in APP
    assert "function capillaryGeometryForFreshSites(fresh, { recordWork = true } = {})" in APP
    assert "const reach = 2.2 * referenceSpacing" in APP
    assert "Math.cos(38 * Math.PI / 180)" in APP
    assert "neighbor.dot(direction) >= capCosine" in APP
    assert "const pocketScore = 2 * meanOccupiedSolidAngleFraction - 1" in APP
    assert "const planarScore = 1 - 4 * Math.abs(meanOccupiedSolidAngleFraction - .5)" in APP
    assert "const exposedScore = 1 - 2 * meanOccupiedSolidAngleFraction" in APP
    assert "+ activeCapillaryGeometryWeight() * evaluation.capillaryGeometry.score" in APP
    assert 'id: "capillary-geometry"' in APP
    assert "discreteCapillaryGeometryRanking:" in APP
    assert "candidate.capillaryGeometry.directionSummaries.forEach" in APP

    for invariant in (
        "equalAreaSphereQuadrature: true",
        "emittedSitesIncludedAsNeighbors: true",
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "meanCurvatureInferred: false",
        "surfaceEnergyInferred: false",
        "capillaryPressureInferred: false",
        "equilibriumShapeInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "## Discrete capillary geometry" in README
    assert "32 deterministic equal-area directions" in normalized
    assert "existing or co-emitted neighbour" in normalized
    assert "same already-enumerated whole-cluster actions" in normalized
    assert "not differential mean curvature" in normalized


if __name__ == "__main__":
    test_capillary_geometry_is_target_blind_soft_interface_ordering()
    print("discrete capillary-geometry contract: passed")
