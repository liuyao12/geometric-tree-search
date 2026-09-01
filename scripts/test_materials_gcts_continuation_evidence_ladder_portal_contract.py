#!/usr/bin/env python3
"""Portal contract for the live continuation-evidence claim ladder."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text()
HTML = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text()
ALIAS = (ROOT / "iqc-growth-live" / "index.html").read_text()
STYLE = (ROOT / "apps" / "iqc-growth-live" / "style.css").read_text()


def main() -> None:
    for document in (HTML, ALIAS):
        assert 'id="continuationEvidenceLadder"' in document
        assert 'id="continuationEvidenceSteps"' in document
        assert 'id="continuationEvidenceBoundary"' in document
        assert 'app.js?v=20260901-425' in document

    for needle in (
        "function continuationEvidenceSnapshot",
        "function renderContinuationEvidenceLadder",
        'schema: "gcts-continuation-evidence-ladder-v1"',
        'title: "Complete geometric representation"',
        'title: "Finite target-free continuation"',
        'title: "Spatially disjoint exterior confirmation"',
        'title: "Stationary / exponential recurrence"',
        'value: "reconstruct"',
        'value: "local-frontier"',
        'value: "sealed-iqc-confirmation"',
        'targetCoordinatesUsed: false',
        'physicalPotentialUsed: false',
        'physicalTimeIntegrated: false',
        'explicitMaterializationComplexity: "O(N)"',
        "continuationEvidenceLadder: continuationEvidenceSnapshot()",
        'buildId: "20260901-425"',
    ):
        assert needle in APP, needle

    for needle in (
        ".continuation-evidence-ladder",
        ".continuation-evidence-steps article.pass",
        ".continuation-evidence-steps article.progress",
    ):
        assert needle in STYLE, needle

    print("continuation evidence ladder portal contract: passed")


if __name__ == "__main__":
    main()
