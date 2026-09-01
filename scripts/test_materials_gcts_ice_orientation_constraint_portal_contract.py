#!/usr/bin/env python3
"""Portal contract for the finite, target-blind ice-rule orientation audit."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = (ROOT / "apps/iqc-growth-live/ice-molecular-anchor-growth.js").read_text()
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_orientation_audit_is_geometric_target_blind_and_fail_honest():
    for token in (
        "function donorTowardAnchor(artifact, occurrence, neighborPoint)",
        "function orientationConstraintAudit(artifact, hypotheses, anchorSites)",
        "const DONOR_CONE_DEGREES = 35",
        "Math.cos(DONOR_CONE_DEGREES * Math.PI / 180)",
        "Number(donorTowardAnchor(artifact, leftPose.occurrence, right.point))",
        "+ Number(donorTowardAnchor(artifact, rightPose.occurrence, left.point)) === 1",
        'schema: "gcts-ice-orientation-constraint-audit-v1"',
        "globallySupportedHypotheses",
        "resolvedAnchors",
        "ambiguousAnchors",
        "const factorCount = (fixed = null) =>",
        "stateCountExact",
        "stateSpaceSha256",
        "poseMarginals",
        "canonicalBranchMaterialized: false",
        "targetUsed: false",
        "physicalPotentialUsed: false",
        "Boundary bonds outside the finite public domain remain open",
    ):
        assert token in EXECUTOR
    assert "seedOrientationAudit" in EXECUTOR
    assert "orientationAudit" in EXECUTOR


def test_live_stage_and_receipts_expose_the_constraint_result_without_materializing_a_branch():
    for token in (
        '"ice-rule edges"',
        '"H₂O pose domains"',
        "exactly one geometrically donated H (≤${audit.orientationAudit.donorConeDegrees}°) on every observed O–O edge",
        "globally supported hypotheses · finite boundary bonds remain open",
        "orientationConstraintAudit: iceOrientationAuditReceipt(wave.orientationAudit)",
        "seedOrientationConstraintAudit: iceOrientationAuditReceipt(iceAnchorTrace.seedOrientationAudit)",
        "finalOrientationConstraintAudit: iceOrientationAuditReceipt(iceAnchorTrace.orientationAudit)",
        "finiteIceRuleConstraintAuditPassed",
        "exactFeasibleAssignmentCount",
        "stateSpaceConstraintSha256",
    ):
        assert token in APP
    assert APP.count("finalOrientationConstraintAudit: iceOrientationAuditReceipt") == 2
    assert "Finite proton constraint audit" in ATLAS
    assert "Build 401 · finite proton-orientation constraint audit" in README


if __name__ == "__main__":
    test_orientation_audit_is_geometric_target_blind_and_fail_honest()
    test_live_stage_and_receipts_expose_the_constraint_result_without_materializing_a_branch()
    print("ice orientation constraint portal contract passed")
