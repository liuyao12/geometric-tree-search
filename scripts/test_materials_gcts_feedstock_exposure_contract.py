#!/usr/bin/env python3
"""Contract for target-blind finite-ray feedstock exposure and shadowing."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_feedstock_exposure_is_soft_declared_geometry() -> None:
    for element_id in ("feedExposureSelect", "feedExposureWeightSelect", "feedExposureHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "top", "oblique", "dual", "hemisphere"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function feedExposureDirections(mode = feedExposureMode)" in APP
    assert "function feedstockExposureForFreshSites(fresh, { recordWork = true } = {})" in APP
    assert "const sampleCount = directions.length ? 6 : 0" in APP
    assert "const reach = 3 * referenceSpacing" in APP
    assert "point.distanceTo(atom.p) - coloredPairExclusion(site.species, atom.species)" in APP
    assert "score: directions.length ? 2 * visibilityFraction - 1 : 0" in APP
    assert "+ activeFeedExposureWeight() * evaluation.feedExposure.score" in APP
    assert 'id: "feed-exposure"' in APP
    assert "feedstockExposureRanking:" in APP
    assert "candidate.feedExposure.directionSummaries.forEach" in APP

    for invariant in (
        "sourceDirectionsDeclaredByUser: directions.length > 0",
        "emittedSitesOnly: true",
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "targetUsed: false",
        "fluxMagnitudeInferred: false",
        "diffusionFieldSolved: false",
        "stickingCoefficientInferred: false",
        "depositionRateInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "feedstock-exposure" in README
    assert "finite declared source-direction set" in normalized
    assert "deliberately distinct from the arrival-path probe" in normalized
    assert "not a concentration or flux magnitude" in normalized
    assert "No diffusion" in README


if __name__ == "__main__":
    test_feedstock_exposure_is_soft_declared_geometry()
    print("feedstock-exposure contract: passed")
