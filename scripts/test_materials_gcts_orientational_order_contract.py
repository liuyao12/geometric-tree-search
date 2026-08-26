from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
MODULE = (APP_DIR / "structure-observables.js").read_text()
README = (APP_DIR / "README.md").read_text()


def test_dimension_aware_orientational_order_is_exposed_interactively():
    assert '<option value="order">local order · qℓ / ψℓ</option>' in HTML
    assert 'id="orientationalOrderSelect"' in HTML
    for harmonic in (4, 6, 12):
        assert f'<option value="{harmonic}"' in HTML
    assert "export function localOrientationalOrder" in MODULE
    assert "legendrePolynomial(harmonic" in MODULE
    assert "Math.atan2(y, x) * harmonic" in MODULE
    assert "selectOrientationalOrderBin(index)" in APP
    assert "show matching local shells" in APP
    assert '<option value="localOrder">mean local q₆ / |ψ₆|</option>' in HTML
    assert "orientationalOrder: structuralOrientationalOrderSnapshot()" in APP
    assert 'localOrder: { label: "mean local q₆ / |ψ₆|"' in APP


def test_order_is_rotation_invariant_posthoc_evidence_not_growth_physics():
    assert "Steinhardt q" in APP
    assert "properRotationInvariant: true" in APP
    assert "usedAsGrowthInput: false" in APP
    assert "phaseProbabilityClaimed: false" in APP
    assert "freeEnergyClaimed: false" in APP
    assert "structural fingerprints—not phase" in README


def test_order_provenance_is_serialized():
    assert "localOrientationalOrder:" in APP
    assert "neighborCutoffInNearestNeighborUnits: COORDINATION_CUTOFF" in APP
    assert "harmonic: orientationalOrderHarmonic" in APP
    assert "highOrderFractionAtLeastPointSeven" in APP
    assert "minimumNeighborsForResolvedValue" in APP
    assert "unresolvedCenters" in APP
    assert "spuriously perfect" in README
    assert 'structuralObservable: { label: "posthoc structural observable", role: "analysis only"' in APP


if __name__ == "__main__":
    test_dimension_aware_orientational_order_is_exposed_interactively()
    test_order_is_rotation_invariant_posthoc_evidence_not_growth_physics()
    test_order_provenance_is_serialized()
    print("orientational-order portal contract: passed")
