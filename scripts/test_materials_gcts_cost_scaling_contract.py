#!/usr/bin/env python3
"""Contract for the live GCTS-versus-MD algorithmic-work laboratory."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_cost_lab_separates_measured_work_representation_and_md_assumptions() -> None:
    for element_id in (
        "costScalingSection",
        "costScalingState",
        "mdHorizonSelect",
        "mdScalingSelect",
        "costLiveWork",
        "costPipelineWork",
        "costScalingTable",
        "costScalingBoundary",
    ):
        assert f'id="{element_id}"' in HTML

    assert 'type="text"' not in HTML[HTML.index('id="costScalingSection"'):HTML.index('id="auditedBenchmark"')]
    assert 'const COST_SCALING_FACTORS = [10, 1000, 100000];' in APP
    assert "function computationalCostAudit()" in APP
    assert "function measuredPipelineWorkLedger()" in APP
    assert "function renderComputationalCost()" in APP
    assert "symbolicRecursiveScalingClaimed" in APP
    assert 'symbolicActionBasis: amplification ? "certified recursive benchmark representation" : "not certified for this material"' in APP
    assert "explicitGctsMaterializationWrites: targetSites" in APP
    assert "mdForceEvaluationsPerformed: 0" in APP
    assert 'explicitMaterializationComplexity: "O(N)"' in APP
    assert "wallTimeCompared: false" in APP
    assert "speedupClaimed: false" in APP
    assert "mdReplacementClaimed: false" in APP
    assert "renderComputationalCost();" in APP
    assert "computationalWork: computationalCostAudit()" in APP
    assert "measuredPipelineWork: measuredPipelineWorkLedger()" in APP
    assert "operationClassesAreNotAdditive: true" in APP
    assert "countersAreDeterministicBrowserOperations: true" in APP
    for stage in ("sample configuration", "cluster identification", "GCTS marking fit",
                  "covering tree search", "explicit materialization"):
        assert stage in APP

    assert ".cost-scaling-section" in CSS
    assert ".cost-scaling-table" in CSS
    assert ".cost-pipeline-work" in CSS
    assert "computational work laboratory" in README
    assert "not a measured MD speedup" in README
    assert "Build 208" in README


if __name__ == "__main__":
    test_cost_lab_separates_measured_work_representation_and_md_assumptions()
    print("cost scaling contract: passed")
