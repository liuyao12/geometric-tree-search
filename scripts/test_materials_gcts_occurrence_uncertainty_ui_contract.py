#!/usr/bin/env python3
"""Static contract for Build 300's occurrence-blocked marking uncertainty UI."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/validation-uncertainty.mjs").read_text()


def require(source: str, needle: str) -> None:
    assert needle in source, f"missing contract text: {needle}"


def test_occurrence_uncertainty_ui_contract() -> None:
    require(MODULE, "export function validationOccurrenceJackknife(records)")
    require(MODULE, 'method: "delete-one-heldout-occurrence jackknife"')
    require(MODULE, "occurrenceBlocks: sampleIndices.length")
    require(MODULE, "sectorLabels: records.length")
    require(MODULE, "(replicates.length - 1) / replicates.length")
    require(MODULE, "not an independent-material population confidence interval")
    require(APP, 'from "./validation-uncertainty.mjs?v=20260828-320"')
    require(APP, "occurrenceJackknife: validationOccurrenceJackknife(selected)")
    require(APP, "occurrenceJackknife: validationOccurrenceJackknife(heldoutRecords)")
    require(APP, "occurrence JK95")
    require(APP, "correlated sector labels")
    require(APP, "uncertaintyClaim")
    require(STYLE, "repeat(5,minmax(0,1fr))")
    require(README, "Build 300 · occurrence-blocked validation uncertainty")
    require(APP, 'buildId: "20260829-334"')
    require(HTML, 'app.js?v=20260829-334')
    require(HTML, 'style.css?v=20260829-334')


if __name__ == "__main__":
    test_occurrence_uncertainty_ui_contract()
    print("occurrence-blocked validation uncertainty UI contract passed")
