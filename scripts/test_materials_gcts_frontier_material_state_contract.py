#!/usr/bin/env python3
"""Static integration contract for Build 280's linked frontier material-state passports."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ROOT_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, f"missing frontier-state fragment: {fragment}"


def main() -> None:
    require("const POLICY_MATERIAL_STATE_OBSERVABLES = [")
    for observable in (
        "coordinationDeficit", "underpackedFraction", "compositionDrift", "localOrder6",
        "centrosymmetry", "scatteringProminence", "chargeDipole", "bondValenceMismatch",
    ):
        require(f'id: "{observable}"')
    require("function compactFrontierMaterialState(state)")
    require("observablesEvaluatedBeforeCandidateScoring: true")
    require("coordinatesEmbedded: false")
    require("usedForAdmission: false")
    require("usedForRanking: false")
    require("energyInferred: false")
    require("physicalTimeModeled: false")
    require("function capturePolicyComparison(entries, frontierStructuralState = null)")
    require("frontierMaterialState: compactFrontierMaterialState(frontierStructuralState)")
    require("const batch = await commutingFrontierBatch(before)")
    require("materialState: historySnapshot.frontierMaterialState || null")
    require("function renderPolicyMaterialStateHistory(snapshot, termId)")
    require("Display normalization is row-local and never enters ranking")
    require('id="policyMaterialStateHistoryState"', HTML)
    require('id="policyMaterialStateHistory"', HTML)
    require('id="policyMaterialStateDetail"', HTML)
    require('id="policyMaterialStateHistory"', ROOT_HTML)
    require(".policy-material-state-history-grid", CSS)
    require("Build 280 · linked frontier material-state passports", README)
    require('application: { name: "Materials Growth Lab", buildId: "20260827-281" }')
    print("linked frontier material-state passport contract passed")


if __name__ == "__main__":
    main()
