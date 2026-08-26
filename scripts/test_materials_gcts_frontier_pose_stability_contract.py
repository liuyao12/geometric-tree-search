#!/usr/bin/env python3
"""Contract for bounded target-blind pose stability over frozen frontier candidates."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_frontier_pose_stability_contract() -> None:
    assert 'buildId: "20260825-135"' in APP
    assert 'app.js?v=20260825-135' in HTML
    assert 'id="policyPoseAuditLimit"' in HTML
    assert 'id="policyPoseAuditHint"' in HTML
    assert '<option value="0">Off · no perturbation trials</option>' in HTML
    assert '<option value="16" selected>16 candidates · responsive</option>' in HTML
    assert '<option value="64">64 candidates · full audit</option>' in HTML
    assert 'const MAXIMUM_FRONTIER_POSE_AUDITS = 64' in APP
    assert 'let frontierPoseAuditLimit = 16' in APP
    assert 'candidatePosePerturbationAudit(entry.candidate)' in APP
    assert 'displayed active candidate, then candidate key lexical order' in APP
    assert 'candidateSelectionTargetUsed: !reconstructionCertified' in APP
    assert 'boundedPoseAudit: frontierPoseAudits.get(entry.candidate.key) || null' in APP
    assert 'point.boundedPoseAudit.perturbationHardAcceptanceCount' in APP
    assert '=== point.boundedPoseAudit.perturbationTrials' in APP
    assert 'stabilityClass = !poseAudit ? "unaudited"' in APP
    assert 'perturbation-stable' in APP
    assert 'usedForAdmission: false, usedForRanking: false, targetUsed: false' in APP
    assert 'posteriorProbabilityInferred: false' in APP
    assert 'thermalEnsembleInferred: false' in APP
    assert '.policy-pareto-plot circle.stable' in CSS
    assert '.policy-pareto-plot circle.fragile' in CSS
    assert '.policy-pareto-plot circle.unaudited' in CSS
    assert 'pose-stability audit' in README
    assert 'never recomputes an old' in README
    assert 'not a posterior probability' in README


if __name__ == "__main__":
    test_frontier_pose_stability_contract()
    print("frontier pose stability contract passed")
