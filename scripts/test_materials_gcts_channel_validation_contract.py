#!/usr/bin/env python3
"""Static contract for Build 297's held-out channel-sign audit."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, needle: str) -> None:
    assert needle in source, f"missing contract text: {needle}"


def test_channel_validation_contract() -> None:
    require(APP, "function sectionChannelValidationRecord(prototype)")
    require(APP, "function renderClusterChannelValidation(panel, prototype)")
    require(APP, 'split: sampleIndex % 5 === 0 ? "holdout" : "fit"')
    require(APP, "observedCompatible: target > 0")
    require(APP, "predictedCompatible: prediction > 0")
    require(APP, 'cells = { tp: [], fp: [], fn: [], tn: [] }')
    require(APP, 'class="cluster-channel-validation"')
    require(APP, "heldoutUpdatesCoefficients: false")
    require(APP, "growthTargetUsed: false")
    require(APP, "heldoutSignAudit: channelValidation ?")
    require(APP, 'buildId: "20260829-326"')
    require(HTML, 'app.js?v=20260829-326')
    require(HTML, 'style.css?v=20260829-326')
    require(STYLE, ".cluster-channel-validation-matrix")
    require(STYLE, ".cluster-channel-validation-detail")
    require(README, "Build 297 · held-out connection-sign audit")
    require(README, "declared zero coefficient threshold")
    require(README, "coefficient. The receipt stores the confusion counts")


if __name__ == "__main__":
    test_channel_validation_contract()
    print("channel validation contract passed")
