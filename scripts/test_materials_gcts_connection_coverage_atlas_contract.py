#!/usr/bin/env python3
"""Portal contract for the per-cluster frozen connection coverage atlas."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP / "app.js").read_text()
    html = (APP / "index.html").read_text()
    alias = (ROOT / "iqc-growth-live" / "index.html").read_text()
    styles = (APP / "style.css").read_text()

    for document in (html, alias):
        for element_id in (
            "connectionCoverageAtlas",
            "connectionCoverageState",
            "connectionCoverageSummary",
            "connectionCoverageEvidence",
            "connectionCoverageTypes",
            "connectionCoverageDetail",
        ):
            assert f'id="{element_id}"' in document, element_id
        assert "residual-mediated topology are reported separately" in document

    for needle in (
        "function clusterConnectionCoverageRecords()",
        "function renderConnectionCoverageAtlas()",
        "function terminalBridgePoseAudit(source, occurrences, edges)",
        "terminalBridgeDirectedPoseObservations",
        "recurrentTerminalBridgePoseClasses",
        "composedTerminalEmissionCertified: false",
        "composedTerminalTransferCertified: false",
        "composedTerminalGrowthRules: 0",
        "const outgoing = overlapGrammar?.byFrom?.get(type) || [];",
        "const incoming = rules.filter((rule) => rule.to === type);",
        "reconstructionEdges, resolvedLobes:",
        'status = cluster.residual ? "terminal"',
        'record.outgoingRules > 0',
        "connectionEvidenceNarrative(evidence",
        'dataset.evidenceVerdict = molecular ? "molecular-anchor"',
        'molecular anchor path · ${promotable.length} cover types audited',
        '"terminal bridges"',
        "recurrent proper poses · not ports",
        '"excluded from growth supply"',
        "target-aware audit only · never growth supply",
        "updateClusterGalleryInspector(record.galleryIndex);",
        "renderConnectionCoverageAtlas();",
        'buildId: "20260829-333"',
    ):
        assert needle in source, needle

    for needle in (
        ".connection-coverage-atlas",
        ".connection-coverage-types button.stranded",
        ".connection-coverage-types button.bidirectional",
        ".connection-coverage-summary",
        ".connection-evidence-flow",
    ):
        assert needle in styles, needle

    print("connection coverage atlas contract: passed")


if __name__ == "__main__":
    main()
