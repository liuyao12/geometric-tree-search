#!/usr/bin/env python3
"""Contract for the exact candidate-space geometric Pareto explorer."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_pareto_frontier_contract() -> None:
    assert 'buildId: "20260825-121"' in APP
    assert 'app.js?v=20260825-121' in HTML
    for element_id in (
        "policyParetoState", "policyParetoX", "policyParetoY",
        "policyParetoPlot", "policyParetoDetail",
    ):
        assert f'id="{element_id}"' in HTML
    assert 'function buildPolicyParetoMap' in APP
    assert 'function buildPolicyParetoPreview' in APP
    assert 'function renderPolicyParetoMap' in APP
    assert 'function previewPolicyParetoCandidate' in APP
    assert 'other.xContribution >= point.xContribution - dominanceEpsilon' in APP
    assert 'other.yContribution >= point.yContribution - dominanceEpsilon' in APP
    assert 'point.dominatedBy = dominators.length' in APP
    assert 'point.nondominated = dominators.length === 0' in APP
    assert 'candidateTradeoffMap' in APP
    assert 'candidateSetChanged: false' in APP
    assert 'hardAdmissionChanged: false' in APP
    assert 'candidateGeometryChanged: false' in APP
    assert 'coordinatesEmbedded: false' in APP
    assert 'executed: false' in APP
    assert '.policy-pareto-plot circle.nondominated' in CSS
    assert '.policy-pareto-plot .frontier' in CSS
    assert 'Candidate-space geometric Pareto frontier' in README
    assert 'not a free-energy' in README


if __name__ == "__main__":
    test_policy_pareto_frontier_contract()
    print("policy Pareto frontier contract passed")
