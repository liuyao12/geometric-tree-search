#!/usr/bin/env python3
"""Contract for the bounded, non-thermodynamic bulk–surface growth score."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_bulk_surface_driving_is_visible_bounded_and_audited() -> None:
    for element_id in ("growthDrivingSelect", "growthDrivingWeightSelect", "growthDrivingHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "surface-limited", "balanced", "volume-driven"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function bulkSurfaceDrivingForCandidate(" in APP
    assert "referenceActionCapacity" in APP
    assert "interfaceIntegrity" in APP
    assert "growthDrivingBulkShare" in APP
    assert 'mode === "volume-driven" ? .78' in APP
    assert 'mode === "balanced" ? .50' in APP
    assert 'mode === "surface-limited" ? .22' in APP
    assert 'id: "bulk-surface-driving"' in APP
    assert "bulkSurfaceDrivingRanking" in APP
    assert 'name: "bulk–surface driving"' in APP
    assert "new THREE.IcosahedronGeometry" in APP
    assert "chemicalPotentialInferred: false" in APP
    assert "supersaturationInferred: false" in APP
    assert "surfaceFreeEnergyInferred: false" in APP
    assert "nucleationBarrierInferred: false" in APP
    assert "physicalTimeIntegrated: false" in APP

    for protocol_mode in ("balanced", "surface-limited", "volume-driven"):
        assert f'growthDrivingMode: "{protocol_mode}"' in APP
    normalized = " ".join(README.split())
    assert "Reduced bulk–surface growth driving" in README
    assert "dimensionless, target blind, and soft" in normalized
    assert "cannot create a pose" in normalized
    assert "not a chemical potential, supersaturation" in normalized


if __name__ == "__main__":
    test_bulk_surface_driving_is_visible_bounded_and_audited()
    print("materials GCTS bulk-surface driving contract: passed")
