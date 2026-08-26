#!/usr/bin/env python3
"""Contract for recipe-aware, claim-bounded prediction audits."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_outcome_contract() -> None:
    assert 'buildId: "20260825-145"' in APP
    assert 'app.js?v=20260825-145' in HTML
    assert 'style.css?v=20260825-54' in HTML
    for element_id in (
        "studyOutcome", "studyOutcomeTitle", "studyOutcomeStatus",
        "studyOutcomeTiles", "studyOutcomeInterpretation",
    ):
        assert f'id="{element_id}"' in HTML

    assert "function activeStudyOutcomeAudit" in APP
    assert "function renderStudyOutcome" in APP
    audit = APP[APP.index("function activeStudyOutcomeAudit"):APP.index("function renderStudyOutcome")]
    for evidence_layer in ("representation", "marking", "live", "benchmark"):
        assert evidence_layer in audit
    for separation in (
        "liveResponseUsedToCertifyBenchmark: false",
        "benchmarkUsedToSelectLiveActions: false",
        "targetCoordinatesUsedForOutcome: false",
        "physicalPotentialUsed: false",
        "physicalTimeInferred: false",
        "stationaryClaimFromFiniteResponse: false",
    ):
        assert separation in audit
    assert 'recipe.id === "bulk-order"' in audit
    assert 'recipe.id === "glass-control"' in audit
    assert "Finite aperiodic structural response observed" in audit
    assert "generic stationary or exponential quasicrystal production remains open" in audit
    assert "Failing closed is the result" in audit
    assert "renderStudyOutcome(growthCertificate)" in APP
    assert "predictionAudit: activeStudyOutcomeAudit()" in APP
    assert ".study-outcome-tiles" in CSS
    assert "Build 145 closes the guided study's scientific loop" in README
    assert "continuation separately" in README and "from stationarity" in README


if __name__ == "__main__":
    test_study_outcome_contract()
    print("materials study outcome contract passed")
