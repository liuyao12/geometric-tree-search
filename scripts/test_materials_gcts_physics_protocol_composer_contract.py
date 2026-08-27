#!/usr/bin/env python3
"""Portal contract for the target-free pre-growth physics protocol composer."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP / "app.js").read_text()
    module = (APP / "physics-compression-map.js").read_text()
    html = (APP / "index.html").read_text()
    root_html = (ROOT / "iqc-growth-live" / "index.html").read_text()
    css = (APP / "style.css").read_text()

    for needle in (
        'id="growthPhysicsProtocolComposer"',
        'id="growthPhysicsProtocolState"',
        'id="growthPhysicsProtocolCoverage"',
        'id="growthPhysicsProtocolSelection"',
        'data-physics-protocol-preset="executing"',
        'data-physics-protocol-preset="actionable"',
        'data-physics-protocol-preset="clear"',
        "freeze before the first candidate frontier",
        'app.js?v=20260827-265',
    ):
        assert needle in html, needle

    for needle in (
        "export function buildPhysicsInvestigationProtocol",
        'selectionMadeBeforeCandidateEnumeration: true',
        'candidateSetInspected: false',
        'coordinatesEmbedded: false',
        'targetUsed: false',
        'physicalTimeModeled: false',
        'state === "ready"',
        'Unready or evidence-only layers remain explicit',
    ):
        assert needle in module, needle

    for needle in (
        "buildPhysicsInvestigationProtocol, buildPhysicsLineagePath",
        'from "./physics-compression-map.js?v=20260827-5"',
        "function physicsProtocolForRecords(records)",
        "function updatePhysicsProtocolSelection(recordIds)",
        "function renderPhysicsProtocolComposer(manifest)",
        "investigationProtocol: physicsProtocolForRecords(records)",
        'schema: 2, records, counts',
        'physicsPreflightManifest: { ...physicsPreflightManifest',
        'frozenBeforeFirstStructuralAction: Boolean(frozenPhysicsPreflightManifest)',
        'if (leapEventCount > 0) return;',
        'no control changed.',
        'buildId: "20260827-265"',
    ):
        assert needle in source, needle

    for needle in (
        ".physics-protocol-composer",
        ".physics-protocol-presets",
        ".physics-protocol-coverage",
        ".physics-protocol-selection",
        ".protocol-selected",
    ):
        assert needle in css, needle

    assert '<base href="../apps/iqc-growth-live/">' in root_html
    assert 'id="growthPhysicsProtocolComposer"' in root_html
    assert 'app.js?v=20260827-265' in root_html
    print("physics protocol composer portal contract: passed")


if __name__ == "__main__":
    main()
