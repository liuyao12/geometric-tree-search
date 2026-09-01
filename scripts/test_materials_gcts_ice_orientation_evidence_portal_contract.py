#!/usr/bin/env python3
"""Portal contract for the fail-closed ice orientation-physics bridge."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
PORTAL = ROOT / "apps" / "iqc-growth-live"


def test_global_orientation_evidence_is_interactive_and_receipt_visible() -> None:
    app = (PORTAL / "app.js").read_text()
    html = (PORTAL / "index.html").read_text()
    module = (PORTAL / "ice-orientation-evidence.mjs").read_text()
    atlas = (PORTAL / "evidence-atlas.js").read_text()
    readme = (PORTAL / "README.md").read_text()
    methods = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()

    assert 'gcts-ice-global-orientation-free-energy-request-v1' in module
    assert 'gcts-ice-global-orientation-free-energy-response-v1' in module
    assert 'independentLocalPoseEnergiesInsufficient: true' in module
    assert 'response.modelScope !== "global-configurational"' in module
    assert 'best.upperEv < record.lowerEv' in module
    assert 'uniqueIntervalWinner && stateSpaceComplete' in module
    assert 'violates frozen ice-rule constraint' in module
    assert 'candidateGeometryChanged: false' in module
    assert 'targetUsed: false' in module

    for token in (
        'id="iceOrientationEvidenceBridge"',
        'Proton-orientation evidence bridge',
        'id="iceOrientationTemperature"',
        'id="iceOrientationEvidenceDownload"',
        'id="iceOrientationEvidenceResponse"',
        'id="iceOrientationStateSpacePlot"',
        'id="iceOrientationStateSpaceDetail"',
        'id="iceBoundarySensitivityBars"',
        'id="iceBoundarySensitivityDetail"',
        'id="icePeriodicBoundaryPlot"',
        'id="icePeriodicBoundaryControls"',
        'id="icePeriodicBoundaryDetail"',
        'id="icePeriodicFluxState"',
        'id="icePeriodicFluxBars"',
        'id="icePeriodicFluxDetail"',
        'Periodic proton-flux sectors',
        'id="icePeriodicEntropyState"',
        'id="icePeriodicEntropyMetrics"',
        'id="icePeriodicEntropyFluxShare"',
        'id="icePeriodicEntropyWithinShare"',
        'id="icePeriodicEntropyDetail"',
        'State-space information accounting',
        'Boundary-sensitivity audit',
        'Local pose energies are insufficient',
    ):
        assert token in html
    assert 'from "./ice-orientation-evidence.mjs?v=20260901-439"' in app
    assert 'function renderIceOrientationEvidenceBridge()' in app
    assert 'function renderIceOrientationStateSpace(audit)' in app
    assert 'function renderIceBoundarySensitivity(audit)' in app
    assert 'function renderIcePeriodicBoundaryComparison(openBoundaryAudit)' in app
    assert 'function renderIcePeriodicFluxSectors(audit)' in app
    assert 'function renderIcePeriodicEntropyAccounting(audit)' in app
    assert 'let lastIceBoundarySensitivityRenderKey = ""' in app
    assert 'if (renderKey === lastIceBoundarySensitivityRenderKey) return' in app
    assert 'lastIceBoundarySensitivityRenderKey = renderKey' in app
    assert 'buildPeriodicIceIhBoundarySeries' in app
    assert 'https://doi.org/10.1021/ja01315a102' in app
    assert '"geometric assignments"' in app
    assert 'log Ω' in app
    assert 'function iceOrientationPhysicsReceipt()' in app
    assert 'orientationPhysicsEvidence: iceOrientationPhysicsReceipt()' in app
    assert app.count('orientationPhysicsEvidence: iceOrientationPhysicsReceipt()') == 2
    assert 'iceProtonFreeEnergyAssignmentResolved' in app
    assert 'candidateGeometryFrozenBeforeRequest: true' in module
    assert 'Orientation-physics handoff' in atlas
    assert 'Build 403 · proton-orientation physics handoff' in readme
    assert 'Build 409 · stable evidence-laboratory interactions' in readme
    assert 'Proton-orientation physics handoff (Build 403)' in methods


if __name__ == "__main__":
    test_global_orientation_evidence_is_interactive_and_receipt_visible()
    print("ice orientation evidence portal contract: passed")
