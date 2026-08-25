#!/usr/bin/env python3
"""Contract for swept-clearance geometric arrival-path ordering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_arrival_path_is_soft_geometry_not_dynamics() -> None:
    for element_id in (
        "arrivalPathSelect",
        "arrivalPathWeightSelect",
        "arrivalPathHint",
        "arrivalPathBadge",
        "arrivalPathBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "parent-outward", "radial-outward", "declared-drive", "free-volume"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML
    assert ".arrival-path-badge" in CSS

    assert "function geometricArrivalPathForCandidate(candidate, fresh)" in APP
    assert "const sampleCount = arrivalPathMode === \"none\" ? 0 : 9" in APP
    assert "const sweepDistance = 2 * referenceSpacing" in APP
    assert "const detourRadius = .72 * referenceSpacing" in APP
    assert "transverseU.clone().negate()" in APP
    assert "transverseV.clone().negate()" in APP
    assert "second.minimumClearance - first.minimumClearance" in APP
    assert "selectedRouteTortuosity" in APP
    assert "arrivalPathRouteEvaluations" in APP
    assert "blockedSamplesReferToSelectedRouteOnly: true" in APP
    assert 'routeSelectionObjective: "maximize the minimum species-specific hard-core clearance' in APP
    assert 'arrivalPathMode: "free-volume"' in APP
    assert "point.distanceTo(atom.p) - coloredPairExclusion(site.species, atom.species)" in APP
    assert "+ activeArrivalPathWeight() * evaluation.arrivalPath.score" in APP
    assert 'id: "arrival-path"' in APP
    assert "geometricArrivalPathRanking:" in APP
    assert "declaredDirectionAvailable:" in APP
    assert "candidate.arrivalAxis && candidate.arrivalSweepDistance > 0" in APP

    for invariant in (
        "emittedSitesOnly: true",
        "intermediateBoundaryEnforced: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "barrierOrRateInferred: false",
        "diffusionEquationSolved: false",
        "minimumEnergyPathClaimed: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    assert "geometric arrival-path" in README.lower()
    assert "exact final candidate" in README
    assert "not a minimum-energy path" in README
    assert "free-volume routing" in README
    assert "four symmetric transverse" in README
    assert "elapsed physical" in README


if __name__ == "__main__":
    test_arrival_path_is_soft_geometry_not_dynamics()
    print("geometric arrival-path contract: passed")
