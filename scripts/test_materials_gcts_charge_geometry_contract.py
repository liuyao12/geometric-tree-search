#!/usr/bin/env python3
"""Contract for finite supplied-formal-charge neighborhood geometry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_charge_geometry_uses_only_complete_supplied_labels() -> None:
    for element_id in (
        "chargeGeometrySelect", "chargeGeometryReachSelect",
        "chargeGeometryWeightSelect", "chargeGeometryHint",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "opposite", "field-neutral", "combined"):
        assert f'value="{mode}"' in HTML
    for reach in ("1.5", "2.5", "4"):
        assert f'value="{reach}"' in HTML

    assert 'scenario === "competition" ? (species === "Na" ? 1 : -1) : null' in APP
    assert "let suppliedFormalChargeBySpecies = new Map()" in APP
    assert "values.every((value) => Number.isFinite(value)" in APP
    assert "function suppliedFormalChargeForToken(" in APP
    assert "function chargeGeometryForFreshSites(" in APP
    assert "Math.exp(-distance / cutoff)" in APP
    assert "q * neighborCharge < 0 ? 1" in APP
    assert "field.length() / fieldScale" in APP
    assert 'id: "charge-geometry"' in APP
    assert "activeChargeGeometryWeight() * evaluation.chargeGeometry.score" in APP
    assert "suppliedChargeGeometryRanking" in APP
    assert 'name: "charge geometry"' in APP
    assert "new THREE.SphereGeometry" in APP

    for invariant in (
        "suppliedFormalChargeOnly: true", "oxidationStatesInferred: false",
        "candidateSetChanged: false", "candidateGeometryChanged: false", "hardAdmissionChanged: false",
        "targetUsed: false", "electrostaticEnergyInferred: false",
        "electrostaticPotentialSolved: false", "dielectricConstantInferred: false",
        "debyeLengthInferred: false", "chargeTransferModeled: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "Supplied-charge neighborhood geometry" in README
    assert "never guesses oxidation states from element names" in normalized
    assert "not an electrostatics solver" in normalized
    assert "not a Debye length" in normalized


if __name__ == "__main__":
    test_charge_geometry_uses_only_complete_supplied_labels()
    print("materials GCTS supplied-charge geometry contract: passed")
