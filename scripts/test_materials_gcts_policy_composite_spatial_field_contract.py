#!/usr/bin/env python3
"""Contract for exact composite candidate-field decomposition in the growth portal."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_composite_spatial_field_contract() -> None:
    assert 'buildId: "20260826-152"' in APP
    assert 'app.js?v=20260826-152' in HTML
    assert 'id="policySpatialDecomposition"' in HTML
    assert 'const POLICY_SPATIAL_COMPOSITE = "__composite__"' in APP
    assert 'snapshot.spatialTermId ||= POLICY_SPATIAL_COMPOSITE' in APP
    assert 'termContributions.reduce((sum, term) => sum + term.contribution, 0)' in APP
    assert 'mode: composite ? "exact signed composite" : "single signed term"' in APP
    assert 'compositeScoreDecompositionExact: composite' in APP
    assert 'function renderPolicySpatialDecomposition' in APP
    assert 'row.addEventListener("click", () => selectPolicySpatialTerm(snapshot, term.id))' in APP
    assert 'fieldMode: field.mode' in APP
    assert 'termContributions: point.termContributions.map' in APP
    assert 'candidateCoordinatesEmbedded: false' in APP
    assert 'candidateSetChanged: false' in APP
    assert 'hardAdmissionChanged: false' in APP
    assert 'executed: false' in APP
    assert '.policy-spatial-decomposition' in CSS
    assert 'the exact\nsigned sum of all currently active terms' in README
    assert 'not a force' in README


if __name__ == "__main__":
    test_policy_composite_spatial_field_contract()
    print("policy composite spatial field contract passed")
