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
    assert 'id="orientationalOrderMapButton"' in HTML
    for harmonic in (4, 6, 12):
        assert f'<option value="{harmonic}"' in HTML
    assert "export function localOrientationalOrder" in MODULE
    assert "legendrePolynomial(harmonic" in MODULE
    assert "Math.atan2(y, x) * harmonic" in MODULE
    assert "selectOrientationalOrderBin(index)" in APP
    assert "show matching local shells" in APP
    assert "currentOrientationalOrderField()" in APP
    assert "orientationalOrderHaloColor(value)" in APP
    assert "new THREE.IcosahedronGeometry(.25, 0)" in APP
    assert "unresolved surface centers intentionally receive no halo" in APP
    assert '<option value="localOrder">mean local q₆ / |ψ₆|</option>' in HTML
    assert "orientationalOrder: structuralOrientationalOrderSnapshot()" in APP
    assert 'localOrder: { label: "mean local q₆ / |ψ₆|"' in APP


def test_order_is_rotation_invariant_posthoc_evidence_not_growth_physics():
    assert "Steinhardt q" in APP
    assert "properRotationInvariant: true" in APP
    assert "usedAsGrowthInput: false" in APP
    assert "phaseProbabilityClaimed: false" in APP
    assert "freeEnergyClaimed: false" in APP
    assert "elementCoreColorsPreserved: true" in APP
    assert "coordinatesChanged: false" in APP
    assert "candidateGeometryChanged: false" in APP
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


def test_structural_leaps_freeze_local_symmetry_change_without_using_it_for_growth():
    assert 'value="localOrderShift">local-symmetry JS distance' in HTML
    assert "function localSymmetryTransition(before, after)" in APP
    assert "jensenShannonDistance(first.histogram, second.histogram)" in APP
    assert "frozen.localSymmetryTransition = localSymmetryTransition(" in APP
    assert "localSymmetryTransition: leap.localSymmetryTransition || null" in APP
    assert 'id: "local-symmetry"' in APP
    assert 'phaseTransitionClaimed: false' in APP
    assert 'latentHeatClaimed: false' in APP
    assert 'kineticsClaimed: false' in APP
    assert 'targetUsed: false' in APP
    assert 'usedAsGrowthInput: false' in APP
    assert "Local qℓ / |ψℓ| and unit-weight geometric S(q) changes are rotation-invariant structural fingerprints" in APP


def test_structural_leaps_compare_finite_observation_reciprocal_space():
    assert 'value="scatteringShift">reciprocal-space JS distance' in HTML
    assert "function structuralScatteringSnapshot()" in APP
    assert "function reciprocalSpaceTransition(before, after)" in APP
    assert "compareStructureFactors(before, after)" in APP
    assert "export function compareStructureFactors" in MODULE
    assert "scattering: structuralScatteringSnapshot()" in APP
    assert "frozen.reciprocalSpaceTransition = reciprocalSpaceTransition(" in APP
    assert "reciprocalSpaceTransition: leap.reciprocalSpaceTransition || null" in APP
    assert 'id: "reciprocal-space"' in APP
    assert 'experimentalIntensityClaimed: false' in APP
    assert 'correlationLengthClaimed: false' in APP
    assert "unit-weight geometric S(q) changes are rotation-invariant structural fingerprints" in APP
    assert "Build 138 pairs that local microscope with a reciprocal-space transition certificate" in README


if __name__ == "__main__":
    test_dimension_aware_orientational_order_is_exposed_interactively()
    test_structural_leaps_freeze_local_symmetry_change_without_using_it_for_growth()
    test_structural_leaps_compare_finite_observation_reciprocal_space()
    test_order_is_rotation_invariant_posthoc_evidence_not_growth_physics()
    test_order_provenance_is_serialized()
    print("orientational-order portal contract: passed")
