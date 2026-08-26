#!/usr/bin/env python3
"""Portal contract for the live finite nucleus-interface geometry passport."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/interface-geometry.js").read_text()


def test_interface_geometry_contract() -> None:
    assert 'buildId: "20260826-164"' in APP
    assert 'app.js?v=20260826-164' in HTML
    assert 'from "./interface-geometry.js?v=20260825-1"' in APP
    assert "export function interfaceGeometryAudit" in MODULE
    assert "export function interfaceAccommodationScore" in MODULE
    assert 'value="interface-accommodate"' in HTML
    assert '"interface-accommodate": "cross-lineage registry accommodation"' in APP
    assert "function interfaceAccommodationForCandidate" in APP
    assert "interfaceAccommodation = interfaceAccommodationForCandidate" in APP
    assert 'microstructureCouplingMode === "interface-accommodate" ? rawSignal' in APP
    assert 'id="nucleusInterfaceProfile"' in HTML
    assert '$("nucleusInterfaceProfile")' in APP
    assert ".nucleus-interface-profile" in CSS
    for label in (
        "registry topology",
        "axial contact thickness",
        "tangential spread",
        "interface exposure",
        "finite registered contact zone",
    ):
        assert label in APP
    for field in (
        "axialThicknessRmsAngstrom",
        "tangentialRadiusRmsAngstrom",
        "axialSharedSiteHistogram",
        "sharedSiteChemistry",
        "physicalAreaInferred: false",
        "interfacialEnergyInferred: false",
        "interfaceMobilityInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert field in APP or field in MODULE
    assert "Build 128" in README
    assert "does not change\ncandidate enumeration, ranking, or admission" in README
    assert "Build 129" in README
    assert "newly registered support\n(40%)" in README
    assert "candidateSetChanged: false" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "targetUsed: false" in APP
    assert "grainBoundaryEnergyInferred: false" in APP


if __name__ == "__main__":
    test_interface_geometry_contract()
    print("interface geometry portal contract passed")
