#!/usr/bin/env python3
"""Contract for declared reduced thermal geometry without invented thermodynamics."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_reduced_thermal_field_is_spatial_geometry_not_heat_dynamics() -> None:
    for element_id in ("thermalFieldSelect", "thermalFieldWeightSelect", "thermalFieldHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "z-plus-cold", "z-minus-cold", "radial-cold", "radial-hot", "band"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function thermalFieldOriginVector()" in APP
    assert "function reducedThermalFieldForCandidate(candidate, { recordWork = true } = {})" in APP
    assert 'originPolicy: "centroid of observed depth-zero seed cluster poses"' in APP
    assert "const transitionRadius = 4 * referenceSpacing" in APP
    assert "const width = 2 * referenceSpacing" in APP
    assert "score = Math.tanh(reducedCoordinate)" in APP
    assert "score = 2 * Math.exp(-.5 * reducedCoordinate ** 2) - 1" in APP
    assert "+ activeThermalFieldWeight() * evaluation.thermalField.score" in APP
    assert 'id: "thermal-field"' in APP
    assert "reducedThermalFieldRanking:" in APP
    assert "new THREE.IcosahedronGeometry(4 * referenceSpacing, 2)" in APP

    for invariant in (
        "scalarFieldDeclaredByUser: thermalFieldMode !== \"none\"",
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "temperatureKelvin: null",
        "temperatureGradientInferred: false",
        "heatEquationSolved: false",
        "conductivityInferred: false",
        "latentHeatModeled: false",
        "thermalDiffusionIntegrated: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "## Reduced thermal-field geometry" in README
    assert "different from the external-drive vector" in normalized
    assert "same candidate digest" in normalized
    assert "No temperature is fitted or reported in Kelvin" in normalized
    assert "does not solve a heat equation" in normalized


if __name__ == "__main__":
    test_reduced_thermal_field_is_spatial_geometry_not_heat_dynamics()
    print("reduced thermal-field contract: passed")
