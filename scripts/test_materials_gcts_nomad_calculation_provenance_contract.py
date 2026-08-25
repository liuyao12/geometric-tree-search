"""Source contract for public calculation provenance and force geometry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_nomad_calculation_vectors_remain_diagnostic_geometry() -> None:
    database = (APP / "structure-database.js").read_text(encoding="utf-8")
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    assert 'const JOULE_PER_ELECTRON_VOLT = 1.602176634e-19' in database
    assert 'const NEWTON_PER_ELECTRON_VOLT_PER_ANGSTROM = 1.602176634e-9' in database
    assert '"calculation[-1]": { energy: "*", forces: "*", system_ref: "*", method_ref: "*" }' in database
    assert "calculationForceEvPerAngstrom" in database
    assert "forceRmsElectronVoltPerAngstrom" in database
    assert 'forcesUsedForGrowth: false' in database
    assert 'absoluteEnergyComparedAcrossEntries: false' in database

    assert 'id="forceToggle"' in html
    assert 'id="forceToggleLabel"' in html
    assert 'function activeCalculationProvenance()' in source
    assert 'forceToggle.disabled = !(calculation?.forceCoverage > 0)' in source
    assert 'new THREE.Vector3(...atom.calculationForceEvPerAngstrom)' in source
    assert 'id: "calculation-forces"' in source
    assert 'role: calculation?.forceCoverage > 0 ? "external calculation diagnostic"' in source
    assert 'id: "calculation", short: "calculation"' in source
    assert 'const externalCalculation = activeCalculationProvenance()' in source
    assert 'externalCalculation: externalCalculation ? {' in source
    assert 'forceVectorsSha256: calculationForceSha256' in source
    assert 'perSiteVectorsEmbedded: false' in source
    for exclusion in (
        "usedForClusterIdentification: false",
        "usedForMarkingLearning: false",
        "usedForCandidateGeneration: false",
        "usedForAdmission: false",
        "usedForBranchRanking: false",
        "usedForRelaxation: false",
        "usedForClassification: false",
    ):
        assert exclusion in source

    assert "Public calculation provenance and residual-force geometry" in readme
    assert "Absolute total energies are not compared across entries" in normalized_readme
    assert "Forces do not change clustering, marking, candidate geometry" in normalized_readme


if __name__ == "__main__":
    test_nomad_calculation_vectors_remain_diagnostic_geometry()
    print("NOMAD calculation-provenance contract: passed")
