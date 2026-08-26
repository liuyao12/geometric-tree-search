#!/usr/bin/env python3
"""Contract for the candidate-resolved spatial geometric-driving overlay."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_spatial_field_contract() -> None:
    assert 'buildId: "20260826-159"' in APP
    assert 'app.js?v=20260826-159' in HTML
    assert 'id="policySpatialFieldState"' in HTML
    assert 'id="policySpatialTerm"' in HTML
    assert 'id="policySpatialToggle"' in HTML
    assert 'id="policySpatialExtremes"' in HTML
    assert "function buildPolicySpatialField" in APP
    assert "function buildPolicySpatialPreview" in APP
    assert "function renderPolicySpatialField" in APP
    assert "function activePolicySpatialField" in APP
    assert "normalizedContribution" in APP
    assert "continuousFieldInferred: false" in APP
    assert "candidateSetChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "candidateCoordinatesEmbedded: false" in APP
    assert "spatialDrivingField" in APP
    assert "staticSpatialField" in APP
    assert ".policy-spatial-field-card" in CSS
    assert "Candidate-resolved geometric driving field" in README
    assert "not a force" in README


if __name__ == "__main__":
    test_policy_spatial_field_contract()
    print("policy spatial field contract passed")
