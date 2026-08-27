from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CORE = (ROOT / "apps/iqc-growth-live/structure-observables.js").read_text()


def test_reported_displacement_scattering_pathway_contract():
    assert 'id="scatteringDisplacementSelect"' in HTML
    assert 'reported Ueq damping' in HTML
    assert 'reported full Uij damping' in HTML
    assert 'id="loadAnisotropicFixtureButton"' in HTML
    assert 'displacementDampedWeightedPowderStructureFactor' in CORE
    assert 'anisotropicDisplacementDampedWeightedPowderStructureFactor' in CORE
    assert '96-direction Fibonacci sphere' in CORE
    assert '96-direction circle' in CORE
    assert 'Math.exp(-.5 * waveNumber * waveNumber * term.meanSquareSum)' in CORE
    assert 'meanSquareDisplacements' in APP
    assert 'displacementTensors' in APP
    assert 'meanSquareTensor' in APP
    assert 'full reported Cartesian Uiso/Uij projected into the intrinsic space' in APP
    assert 'quadratureDirections: displayedSq.quadratureDirections || null' in APP
    assert 'fetch("./fixtures/tav-disordered.cif")' in APP
    assert 'scatteringDisplacementMode = "reported-anisotropic"' in APP
    assert 'scatteringDisplacementMode === "reported"' in APP
    assert 'missingDisplacementTensorsUseZeroAttenuation: true' in APP
    assert 'diffuseRedistributionIncluded: false' in APP
    assert 'usedAsGrowthInput: false' in APP
