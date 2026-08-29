#!/usr/bin/env python3
"""Static contract for Build 299's validation-to-frontier evidence bridge."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, needle: str) -> None:
    assert needle in source, f"missing contract text: {needle}"


def test_validation_frontier_bridge_contract() -> None:
    require(APP, "function buildMarkingFrontierCounterfactual(admissible, candidateSetDigest)")
    require(APP, "validationAvailableMarkings")
    require(APP, 'evidenceBridgeRole: "held-out connection-sign validation beside target-free live-frontier consequence"')
    require(APP, "validationUsedForCandidateGeneration: false")
    require(APP, "validationUsedForHardAdmission: false")
    require(APP, "validationUsedForRanking: false")
    require(APP, "validationUsedForAutomaticMarkingSelection: false")
    require(APP, 'evidenceBridge.className = "marking-evidence-bridge"')
    require(APP, 'validationLabel.textContent = "withheld connection sectors"')
    require(APP, 'frontierLabel.textContent = "same frozen live frontier"')
    require(APP, "marking.validation ? {")
    require(HTML, "Held-out connection-sector quality and the resulting live-frontier winner")
    require(STYLE, ".marking-evidence-bridge")
    require(README, "Build 299 · validation-to-frontier evidence bridge")
    require(README, "validation is not")
    require(APP, 'buildId: "20260829-324"')
    require(HTML, 'app.js?v=20260829-324')
    require(HTML, 'style.css?v=20260829-324')


if __name__ == "__main__":
    test_validation_frontier_bridge_contract()
    print("validation-to-frontier evidence bridge contract passed")
