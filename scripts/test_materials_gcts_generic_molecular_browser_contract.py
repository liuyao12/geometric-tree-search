from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_non_water_molecular_fixture_uses_generic_discovery():
    assert '<option value="dryIce">Dry ice · cubic CO₂-I</option>' in HTML
    assert 'molecularFixture: "dry-ice-pa3"' in APP
    assert "function makeDryIceReferenceConfiguration()" in APP
    assert "discoverMolecularConnectionTopology" in APP
    assert "function buildGenericMolecularClusterCover" in APP
    assert 'molecularCover: "water"' not in APP


def test_molecule_connection_void_roles_are_explicit_and_label_free():
    components = (ROOT / "apps/iqc-growth-live/molecular-components.js").read_text()
    assert 'family: "molecule"' in APP
    assert 'family: "bridge"' in APP
    assert 'family: "gap"' in APP
    assert "expectedRingSizeUsed: topology.expectedRingSizeUsed" in APP
    assert "materialLabelUsed: false" in components
    assert "close the atom cover; connection and void clusters" in APP
    assert "autonomous dry-ice continuation remains an" in README
    assert 'action: "94 replay decisions"' in APP
    assert 'speed: "324 / 324 · fixed point"' in APP
    assert "exact target-aware known-window replay" in APP
    assert "94 deterministic tree decisions" in README


def test_water_renderer_stays_a_specialized_view_after_generic_discovery():
    assert "const waterCover = buildWaterClusterCover(source, waterDiscovery);" in APP
    assert "decorateIceViOxygenVoidBoundaries(source, waterCover)" in APP
    assert "learnedCover.molecular?.water\n    && (currentMaterial().icePolytype || scenarioSelect.value === \"iceVI\")" in APP
    assert 'visualKind: molecule ? "molecule" : connection ? "bridge" : "ring"' in APP


if __name__ == "__main__":
    test_non_water_molecular_fixture_uses_generic_discovery()
    test_molecule_connection_void_roles_are_explicit_and_label_free()
    test_water_renderer_stays_a_specialized_view_after_generic_discovery()
    print("generic molecular browser contract: passed")
