#!/usr/bin/env python3
"""Static integration contract for Build 281's state-conditioned decisiveness lens."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ROOT_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/policy-state-association.mjs").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, f"missing state-association fragment: {fragment}"


def main() -> None:
    require('finiteStateContrast } from "./policy-state-association.mjs?v=20260827-1"')
    require("function buildPolicyStateConditionedDecisiveness(snapshot")
    require("const minimumPerGroup = 3")
    require("finiteStateContrast(samples, { minimumPerGroup })")
    require("statisticalIndependenceAssumed: false")
    require("pValueComputed: false")
    require("causalEffectInferred: false")
    require("energyLandscapeInferred: false")
    require("physicalTimeModeled: false")
    require("function receiptPolicyStateConditionedDecisiveness(audit)")
    require("function renderPolicyStateAssociation(snapshot, termId)")
    require("selectedStateConditionedDecisiveness: includeIdentifiability")
    require("export function finiteStateContrast", MODULE)
    require("minimumPerGroup must be a positive integer", MODULE)
    require('id="policyStateAssociationState"', HTML)
    require('id="policyStateOutcome"', HTML)
    require('id="policyStateAssociationRows"', HTML)
    require('id="policyStateAssociationDetail"', HTML)
    require('id="policyStateAssociationRows"', ROOT_HTML)
    require(".policy-state-association", CSS)
    require("Build 281 · state-conditioned channel decisiveness", README)
    require('application: { name: "Materials Growth Lab", buildId: "20260827-281" }')
    print("state-conditioned channel decisiveness contract passed")


if __name__ == "__main__":
    main()
