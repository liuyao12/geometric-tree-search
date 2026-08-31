#!/usr/bin/env python3
"""Contract for the specialized molecular-anchor Stage-4 launch certificate."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_specialized_ice_launch_does_not_fall_through_to_generic_seed_failure():
    start = APP.index("function growthLaunchReadinessAudit()")
    end = APP.index("function renderGrowthLaunchReadiness()", start)
    audit = APP[start:end]
    assert "if (iceAnchorTrace)" in audit
    assert audit.index("if (iceAnchorTrace)") < audit.index('let state = "ready"')
    for token in (
        'state: fixedPointReached ? "specialized-fixed" : "specialized-ready"',
        "iceAnchorTrace.seedAnchors",
        "iceAnchorTrace.portCount",
        "iceAnchorTrace.exactBackendCountParity",
        "nextWave?.candidateAnchors || 0",
        "emittedAnchors",
        "fixedPointReached",
        "targetUsed: false",
        "physicalPotentialUsed: false",
    ):
        assert token in audit


def test_launch_certificate_is_visible_receipt_evidence_with_honest_boundaries():
    for token in (
        'audit.specializedMolecularAnchor ? "Frozen disjoint seed"',
        'audit.specializedMolecularAnchor ? "Inspect molecular cover"',
        'audit.specializedMolecularAnchor ? "Generic marking not active"',
        "launchReadiness: growthLaunchReadinessAudit()",
        "full molecular placement, stationarity, and physical stopping time remain open",
        "Target calls: 0; no potential or physical time is inferred",
    ):
        assert token in APP
    assert APP.count("launchReadiness: growthLaunchReadinessAudit()") == 2
    assert ".growth-launch-readiness.specialized-ready" in CSS
    assert ".growth-launch-readiness.specialized-fixed" in CSS
    assert "Build 400 · molecular growth launch certificate" in README


if __name__ == "__main__":
    test_specialized_ice_launch_does_not_fall_through_to_generic_seed_failure()
    test_launch_certificate_is_visible_receipt_evidence_with_honest_boundaries()
    print("ice growth launch readiness contract passed")
