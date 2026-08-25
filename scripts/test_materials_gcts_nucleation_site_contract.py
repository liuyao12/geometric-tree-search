#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_observed_nucleation_site_geometry_contract():
    app = (ROOT / "apps/iqc-growth-live/app.js").read_text()
    html = (ROOT / "apps/iqc-growth-live/index.html").read_text()
    readme = (ROOT / "apps/iqc-growth-live/README.md").read_text()

    assert 'id="nucleationSiteSelect"' in html
    for element_id in ("nucleationLandscapeInspector", "nucleationLandscapeState",
                       "nucleationLandscapeSummary", "nucleationLandscapeCandidates"):
        assert f'id="{element_id}"' in html
    for mode in ("replay", "interior", "surface", "gap", "interface", "dispersed"):
        assert f'value="{mode}"' in html
    assert 'app.js?v=20260825-108' in html

    assert "function observedGrowthSeedIndices()" in app
    assert "function renderNucleationLandscapeInspector()" in app
    assert "nucleationSiteLandscape = ranked.map" in app
    assert "const nucleationGroup = new THREE.Group()" in app
    assert "new THREE.IcosahedronGeometry(.38, 1)" in app
    assert "nucleationCandidateMaterial" in app
    assert "nucleationSelectedMaterial" in app
    assert "growthEnvironmentSignedMargin" in app
    assert "role.gapBoundary || role.literalTerminal" in app
    assert "role.poseInterface" in app
    assert "selectedOccurrencesWereFitted: true" in app
    assert "properObservedPosesPreserved: true" in app
    assert "candidateGeometryChanged: false" in app
    assert "heldoutTargetUsed: false" in app
    assert "nucleationBarrierInferred: false" in app
    assert "criticalNucleusSizeInferred: false" in app
    assert "requested local role absent; replay anchor retained" in app
    assert "atom-disjoint farthest-point traversal" in app
    assert "coordinatesEmbeddedInReceipt: false" in app

    assert "Observed nucleation site" in readme
    assert "not a nucleation barrier, rate, critical nucleus size" in readme
    assert "amber wire halos" in readme


if __name__ == "__main__":
    test_observed_nucleation_site_geometry_contract()
    print("nucleation-site contract passed")
