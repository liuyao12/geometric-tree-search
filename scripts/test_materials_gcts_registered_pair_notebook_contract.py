#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_registered_pair_notebook_contract():
    assert 'buildId: "20260826-151"' in APP
    assert 'app.js?v=20260826-151' in HTML
    assert 'style.css?v=20260826-60' in HTML

    for field in ("question", "settings", "outcomes", "boundary", "autoExecuted"):
        assert field in APP[APP.index("registeredStudy:"):APP.index("physicalTimeModeled:", APP.index("registeredStudy:"))]

    assert "function notebookRegisteredPairAudit" in APP
    assert 'armSet.has("reference") && armSet.has("contrast")' in APP
    assert "intervention.changedFactors.length === 1" in APP
    assert "intervention.sameInput" in APP
    assert "settingsStillMatch === true" in APP
    assert "autoExecuted === false" in APP
    assert "notebook-registered-pair" in APP
    assert "notebook-registered-arms" in APP
    assert "notebook-registered-outcomes" in APP
    assert "registered.referenceLabel" in APP
    assert "registered.contrastLabel" in APP
    assert "registered.boundary" in APP
    assert "registered pair unavailable" in APP
    assert "registered pair not certified" in APP
    assert "const executionEvidence =" in APP
    assert "totalStructuralLeapEvents > 0" in APP
    assert 'status: responseComparable ? "registered" : valid ? "registered-unexecuted" : "invalid"' in APP
    assert "registered design · execute both arms" in APP
    assert "response-comparable" in APP
    assert "outcome attribution awaits at least one structural leap or audited fixed point" in APP

    factors = APP[APP.index("function notebookInterventionFactors"):APP.index("function experimentNotebookSummary")]
    marking_factor = factors[factors.index('marking: { label: "GCTS marking"'):factors.index('ranking: { label: "frontier ranking"')]
    protocol_factor = factors[factors.index('protocol: { label: "growth protocol"'):factors.index('relaxation: { label: "post-attachment')]
    assert "searchMode" not in marking_factor
    assert "experimentProtocol.settings" not in protocol_factor
    assert 'nucleation: { label: "growth nuclei"' in factors
    assert "search.multiNucleusGrowth?.requestedNuclei" in factors

    for selector in (".notebook-intervention-audit.registered-pair", ".notebook-registered-pair.registered",
                     ".notebook-intervention-audit.registered-pair.response-comparable",
                     ".notebook-registered-pair.registered-unexecuted",
                     ".notebook-registered-arms", ".notebook-registered-outcomes"):
        assert selector in CSS

    assert "Build 148 closes that registered comparison inside the saved-run notebook" in README
    assert "exactly one recorded intervention" in README
    assert "Legacy,\nedited, same-arm, different-input, multi-factor" in README
    assert "Browser regression checks confirm that all eight" in README
    assert "Build 149 separates a valid registered design from an executed response pair" in README


if __name__ == "__main__":
    test_registered_pair_notebook_contract()
    print("registered pair notebook contract passed")
