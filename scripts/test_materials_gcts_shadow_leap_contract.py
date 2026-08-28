#!/usr/bin/env python3
"""Static integration contract for Build 277 shadow structural leaps."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(text: str, source: str = APP) -> None:
    assert text in source, f"missing shadow-leap contract fragment: {text}"


def main() -> None:
    require('function candidateFitsCommutingBatch(acceptedBatch, entry')
    require('candidateFitsCommutingBatch(accepted, entry, { recordWork: false })')
    require('candidateFitsCommutingBatch(acceptedBatch, entry)')
    require('function buildFrozenShadowLeapAudit(entries, candidateSetDigest)')
    require('sameBatchFeasibilityRules: true')
    require('candidateDigest: notebookStringHash([...candidateKeys].sort().join("|"))')
    require('candidateOrderDigest: notebookStringHash(candidateKeys.join("|"))')
    require('reorderedBatches: cases.filter((entry) => entry.orderChanged && !entry.structuralLeapChanged).length')
    require('baselineSelectionMatchesLiveBatch')
    require('throw new Error("frozen shadow-leap baseline diverged from the live commuting batch")')
    require('candidateSetChanged: false')
    require('hardAdmissionChanged: false')
    require('receiptCoordinatesEmbedded: false')
    require('downstreamFrontierEnumerated: false')
    require('physicalCausalEffectIdentified: false')
    require('energyOrRateInferred: false')
    require('shadowStructuralLeap: receiptFrozenShadowLeapAudit(snapshot.shadowLeapAudit)')
    require('id="policyShadowLeapPlot"', HTML)
    require('id="policyShadowLeapDetail"', HTML)
    require('Build 277 · leave-one-channel-out shadow structural leaps', README)
    require('application: { name: "Materials Growth Lab", buildId: "20260827-277" }')
    print("shadow structural-leap contract passed")


if __name__ == "__main__":
    main()
