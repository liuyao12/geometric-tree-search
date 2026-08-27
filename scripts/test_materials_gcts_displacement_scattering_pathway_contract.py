from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CORE = (ROOT / "apps/iqc-growth-live/structure-observables.js").read_text()


def test_reported_displacement_scattering_pathway_contract():
    assert 'id="scatteringDisplacementSelect"' in HTML
    assert 'reported Ueq damping' in HTML
    assert 'displacementDampedWeightedPowderStructureFactor' in CORE
    assert 'Math.exp(-.5 * waveNumber * waveNumber * term.meanSquareSum)' in CORE
    assert 'meanSquareDisplacements' in APP
    assert 'scatteringDisplacementMode === "reported"' in APP
    assert 'missingDisplacementTensorsUseZeroAttenuation: true' in APP
    assert 'diffuseRedistributionIncluded: false' in APP
    assert 'usedAsGrowthInput: false' in APP
