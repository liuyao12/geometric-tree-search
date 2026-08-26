#!/usr/bin/env python3
"""Contract for the exact leave-one-geometric-channel-out frontier audit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_omission_attribution_contract() -> None:
    assert 'buildId: "20260825-140"' in APP
    assert 'app.js?v=20260825-140' in HTML
    for element_id in ("policyOmissionState", "policyOmissionList", "policyOmissionDetail"):
        assert f'id="{element_id}"' in HTML
    assert "function buildPolicyOmissionAudit" in APP
    assert "function buildPolicyOmissionPreview" in APP
    assert "function renderPolicyOmissionAudit" in APP
    assert "function previewPolicyOmission" in APP
    assert 'new Set(["grammar-priority", "known-window-gain", "exploration"])' in APP
    assert "candidatePoseDifference(baseline.candidate, winner.candidate)" in APP
    assert "sameChildPrototype" in APP
    assert "symmetryReducedMisorientation" in APP
    assert "properSymmetryGaugePairsMinimized" in APP
    assert "symmetry-reduced proper misorientation" in APP
    assert "coloredSiteIntersectionCount" in APP
    assert "emittedSiteJaccard" in APP
    assert "leaveOnePhysicsChannelOut" in APP
    assert 'candidateSetChanged: false' in APP
    assert 'hardAdmissionChanged: false' in APP
    assert 'candidateGeometryChanged: false' in APP
    assert 'causalEffectIdentified: false' in APP
    assert 'energyDecompositionInferred: false' in APP
    assert 'parameterFittingPerformed: false' in APP
    assert ".policy-omission-card" in CSS
    assert ".policy-omission-list button.changed" in CSS
    assert "Leave-one-physics-channel-out attribution" in README
    assert "not causal" in README


if __name__ == "__main__":
    test_policy_omission_attribution_contract()
    print("policy omission attribution contract passed")
