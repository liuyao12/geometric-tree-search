#!/usr/bin/env python3
"""Contract for declared, target-blind support-plane registry ordering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_epitaxy_registry_is_declared_soft_geometry() -> None:
    for element_id in (
        "epitaxyTemplateSelect", "epitaxyWeightSelect", "epitaxyTemplateHint",
        "epitaxyBadge", "epitaxyBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in (
        "none", "square-coherent", "square-mismatch", "hex-coherent",
        "hex-mismatch", "hex-30",
    ):
        assert f'value="{mode}"' in HTML
    assert ".epitaxy-badge" in CSS

    assert "function epitaxyTemplateSpec(" in APP
    assert "function epitaxyLatticeCoordinate(" in APP
    assert "function epitaxyRegistryForFreshSites(" in APP
    assert 'confinementSelect.value === "substrate"' in APP
    assert "referenceSpacing * (1 + spec.mismatch)" in APP
    assert "2 * y / (Math.sqrt(3) * spacing)" in APP
    assert "Math.exp(-8 * (coordinate.nearestDistance / coordinate.spacing) ** 2)" in APP
    assert "Math.exp(-2 * height / reach)" in APP
    assert "+ activeEpitaxyWeight() * evaluation.epitaxyRegistry.score" in APP
    assert "epitaxialRegistryRanking:" in APP
    assert "new THREE.PointsMaterial({ color: 0xffb15c" in APP

    for invariant in (
        "substrateAtomsPresent: false",
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "adhesionEnergyInferred: false",
        "interfaceEnergyInferred: false",
        "epitaxialRelaxationModeled: false",
        "dislocationNetworkInferred: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "Declared epitaxial registry" in README
    assert "unchanged exact frontier" in normalized
    assert "not an atomistic substrate" in normalized
    assert "not adhesion" in normalized


if __name__ == "__main__":
    test_epitaxy_registry_is_declared_soft_geometry()
    print("declared epitaxial registry contract: passed")
