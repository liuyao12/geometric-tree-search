#!/usr/bin/env python3
"""Static integration contract for Build 279's frozen-frontier decisiveness history."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, f"missing decisiveness-history fragment: {fragment}"


def main() -> None:
    require("const POLICY_DECISIVENESS_STAGES = [")
    for stage in ("score", "leader", "order", "antichain", "atoms", "chemistry"):
        require(f'{{ id: "{stage}"')
    require("function buildPolicyDecisivenessHistory(snapshot, requestedTermId = null)")
    require("historySnapshot.decisivenessAudit")
    require("candidateSetDigest: audit?.candidateSetDigest || historySnapshot.candidateDigest")
    require("physicalTimeModeled: false")
    require("causalHierarchyInferred: false")
    require("function receiptPolicyDecisivenessHistory(history)")
    require("function renderPolicyDecisivenessHistory(snapshot, termId)")
    require("selectPolicyDecisivenessFrontier(record.historyIndex, history.termId)")
    require("selectedHypothesisDecisivenessHistory: includeIdentifiability")
    require('id="policyDecisivenessHistoryState"', HTML)
    require('id="policyDecisivenessHistory"', HTML)
    require("Columns are discrete frozen frontier updates, not physical time", HTML)
    require(".policy-decisiveness-history-grid button.changed", CSS)
    require("Build 279 · decisiveness through structural growth", README)
    require('application: { name: "Materials Growth Lab", buildId: "20260827-282" }')
    print("frozen-frontier decisiveness history contract passed")


if __name__ == "__main__":
    main()
