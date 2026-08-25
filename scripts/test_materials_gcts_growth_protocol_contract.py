#!/usr/bin/env python3
"""Contract for explicit, receipt-visible materials-growth protocol bundles."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_growth_protocols_expand_into_existing_controls() -> None:
    for element_id in ("growthProtocolSelect", "growthProtocolHint", "growthProtocolSummary"):
        assert f'id="{element_id}"' in HTML
    for mode in ("custom", "bulk", "epitaxy", "misfit-film", "directional", "dendritic", "impingement", "pore-fill"):
        assert f'value="{mode}"' in HTML
    assert ".growth-protocol-summary" in CSS

    assert "const GROWTH_PROTOCOL_DEFAULTS = Object.freeze" in APP
    assert "const GROWTH_PROTOCOLS = Object.freeze" in APP
    assert "function applyGrowthProtocol(mode)" in APP
    assert "function currentGrowthProtocolSettings()" in APP
    assert "function growthProtocolManifest()" in APP
    assert "experimentProtocol: growthProtocolManifest()" in APP
    assert 'protocol: { label: "growth protocol"' in APP
    assert 'growthProtocolMode = "custom"' in APP
    assert "GROWTH_PROTOCOL_CONTROL_IDS.has(event.target.id)" in APP

    for setting in (
        "confinement", "geometryPreference", "compositionPreference", "solutePartitionMode", "surfacePreference",
        "growthDrivingMode", "growthDrivingWeight",
        "attachmentTopologyMode", "attachmentTopologyWeight",
        "frontMorphologyMode", "capillaryGeometryMode", "epitaxyTemplateMode", "externalDriveMode", "thermalFieldMode",
        "robustnessPreference", "microstructureCouplingMode", "loopClosurePreference",
        "arrivalPathMode", "geometricExplorationScale", "requestedGrowthNuclei",
        "growthScheduling", "hierarchyEnabled",
    ):
        assert setting in APP
    for invariant in (
        "convenienceOnly: true", "hiddenPhysicsAdded: false", "candidateGeometryAuthorized: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "Materials-growth experiment protocols" in README
    assert "convenience bundles, not new hidden backends" in normalized
    assert "fully expanded state" in normalized
    assert "No protocol adds atoms, candidates, material labels, rates, or target access" in normalized


if __name__ == "__main__":
    test_growth_protocols_expand_into_existing_controls()
    print("materials-growth experiment protocol contract: passed")
