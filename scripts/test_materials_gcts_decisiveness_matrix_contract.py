#!/usr/bin/env python3
"""Static integration contract for Build 278's hypothesis decisiveness matrix."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, f"missing decisiveness fragment: {fragment}"


def main() -> None:
    require("function buildPolicyDecisivenessAudit(snapshot")
    require('const shadowByTerm = new Map((shadowAudit?.cases || []).map((entry) => [entry.termId, entry]))')
    require('baselineOmittedRank')
    require('differentialScoreField: contributionRange > 1e-12')
    require('antichainChanged: Boolean(shadow?.structuralLeapChanged)')
    require('atomsChanged')
    require('chemistryChanged')
    require('baselineWeightsFrozenAtFrontierCapture: true')
    require('causalHierarchyInferred: false')
    require('lastPolicyComparison.decisivenessAudit = buildPolicyDecisivenessAudit(lastPolicyComparison)')
    require('hypothesisDecisiveness: receiptPolicyDecisivenessAudit(snapshot.decisivenessAudit)')
    require('id="policyDecisivenessMatrix"', HTML)
    require('id="policyDecisivenessDetail"', HTML)
    require('Build 278 · hypothesis decisiveness matrix', README)
    require('application: { name: "Materials Growth Lab", buildId: "20260827-280" }')
    print("hypothesis decisiveness matrix contract passed")


if __name__ == "__main__":
    main()
