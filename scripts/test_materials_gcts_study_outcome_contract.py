#!/usr/bin/env python3
"""Contract for recipe-aware, claim-bounded prediction audits."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_outcome_contract() -> None:
    assert 'buildId: "20260826-154"' in APP
    assert 'app.js?v=20260826-154' in HTML
    assert 'style.css?v=20260826-63' in HTML
    for element_id in (
        "studyOutcome", "studyOutcomeTitle", "studyOutcomeStatus",
        "studyOutcomeTiles", "studyOutcomeInterpretation",
    ):
        assert f'id="{element_id}"' in HTML

    assert "function activeStudyOutcomeAudit" in APP
    assert "function recipeStructuralResponse" in APP
    assert "function renderStudyOutcome" in APP
    audit = APP[APP.index("function activeStudyOutcomeAudit"):APP.index("function renderStudyOutcome")]
    for evidence_layer in ("representation", "marking", "microscope", "live", "benchmark"):
        assert evidence_layer in audit
    microscope = APP[APP.index("function recipeStructuralResponse"):APP.index("function activeStudyOutcomeAudit")]
    assert 'selected === "order"' in microscope
    assert 'selected === "sq"' in microscope
    assert "rdfTailSummary" in microscope
    assert "phaseThresholdApplied: false" in microscope
    assert "usedAsGrowthInput: false" in microscope
    assert "unit weights; no form factors" in microscope
    assert "not crystallinity probability" in microscope
    assert "approaches one only at long range" in microscope
    assert "responseSites <= 0" in microscope
    assert "growth nucleus is not treated as an outcome" in microscope
    assert "Unresolved surface or sparse centers are excluded" in microscope
    assert 'recipe.id === "molecular-ice"' in microscope
    assert 'referenceAtoms.filter((atom) => atom.species === "O")' in microscope
    assert 'scope: oxygenAnchorScope ? "oxygen-anchor sublattice"' in microscope
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
    assert "Build 146 adds the recipe's actual" in README
    assert "No phase threshold is applied" in README
    assert "oxygen-anchor sublattice" in README
    assert "refuses" in README and "growth nucleus" in README
    assert "continuation separately" in README and "from stationarity" in README


if __name__ == "__main__":
    test_study_outcome_contract()
    print("materials study outcome contract passed")
