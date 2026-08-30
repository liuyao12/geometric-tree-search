#!/usr/bin/env python3
"""Contract for the exact-IQC fitted-nucleus growth recommendation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text()
INDEX = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text()
ROOT_INDEX = (ROOT / "iqc-growth-live" / "index.html").read_text()
README = (ROOT / "apps" / "iqc-growth-live" / "README.md").read_text()
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text()


def test_fixture_specific_recommendation() -> None:
    assert 'recommendedGrowthSeedProtocol: "local-frontier"' in APP
    assert 'function recommendedGrowthSeedProtocol(material = currentMaterial())' in APP
    assert 'growthSeedProtocol = recommendedGrowthSeedProtocol();' in APP
    assert 'let growthSeedProtocol = "observed-window";' in APP
    assert 'geometricExplorationScale: 0, growthSeedProtocol: "observed-window"' in APP


def test_both_seed_protocols_remain_user_selectable() -> None:
    for document in (INDEX, ROOT_INDEX):
        assert 'value="observed-window" selected' in document
        assert 'value="local-frontier"' in document
        assert 'value="reconstruct"' in document
    assert 'growthSeedProtocolSelect.addEventListener("change"' in APP


def test_target_free_claim_boundary_remains_explicit() -> None:
    for needle in (
        'targetFreeContinuationAuthorized: growthSeedProtocol === "local-frontier"',
        'Remaining observed sites are neither snapped to nor scored',
        'targetUsed: false, futureSitesUsed: false',
        'knownWindowReplayRequested: growthSeedProtocol === "reconstruct"',
        'materialRecommendedMode: recommendedGrowthSeedProtocol()',
        'selectedModeMatchesMaterialRecommendation: growthSeedProtocol === recommendedGrowthSeedProtocol()',
    ):
        assert needle in APP


def test_build_and_measured_browser_audit_are_documented() -> None:
    assert 'buildId: "20260829-335"' in APP
    for document in (INDEX, ROOT_INDEX):
        assert 'app.js?v=20260829-335' in document
    for document in (README, DOCS):
        assert "Build 335" in document
        assert "12" in document and "57" in document
        assert "causal depth 1" in document
        assert "501" in document and "depth 10" in document
        assert "zero beyond" in document


if __name__ == "__main__":
    test_fixture_specific_recommendation()
    test_both_seed_protocols_remain_user_selectable()
    test_target_free_claim_boundary_remains_explicit()
    test_build_and_measured_browser_audit_are_documented()
    print("ideal IQC executable-growth contract: passed")
