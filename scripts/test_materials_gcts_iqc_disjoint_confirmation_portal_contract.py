#!/usr/bin/env python3
"""Portal contract for the sealed spatially disjoint IQC confirmation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text()
HTML = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text()
ALIAS = (ROOT / "iqc-growth-live" / "index.html").read_text()
README = (ROOT / "apps" / "iqc-growth-live" / "README.md").read_text()
DOC = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text()
ARTIFACT = (ROOT / "apps" / "iqc-growth-live" /
            "iqc-disjoint-confirmation-artifact.js").read_text()


def main() -> None:
    for needle in (
        "IQC_DISJOINT_CONFIRMATION_ARTIFACT",
        "initializeIqcDisjointConfirmationSearch",
        "performIqcDisjointConfirmationEvent",
        'mode: "sealed disjoint IQC continuation confirmation"',
        "targetCallsDuringBrowserExecution: 0",
        "autonomousContinuationCertified",
        "stationaryOrExponentialClaimed",
        'buildId: "20260831-359"',
    ):
        assert needle in APP, needle
    for document in (HTML, ALIAS):
        assert 'value="sealed-iqc-confirmation"' in document
        assert 'app.js?v=20260831-359' in document
    for needle in (
        "seedAtomCount: 473",
        "terminalCount: 128",
        "exactTerminalCountPosthoc: 90",
        "selectedTerminalIndex: 101",
        "selectedTerminalSiteCount: 3",
        "targetDomainDisjoint: true",
        "candidatesFrozenBeforeTarget: true",
        "targetUsedForFitCandidateOrRanking: false",
        "fusionFirstExactRank: 16",
        "sixActionAutonomousGatePassed: false",
        "stationaryOrExponentialClaimed: false",
    ):
        assert needle in ARTIFACT, needle
    for document in (README, DOC):
        assert "Build 336" in document
        assert "473-site" in document
        assert "90 exact" in document
        assert "ranks 13" in document or "ranks are\n13/16" in document
        assert "stationary" in document
        assert "exponential" in document
    print("sealed disjoint IQC portal contract: passed")


if __name__ == "__main__":
    main()
