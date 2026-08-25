#!/usr/bin/env python3
"""Contract for species-resolved geometric partition hypotheses."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_solute_partition_couples_observed_species_to_frozen_spatial_fields() -> None:
    for element_id in (
        "soluteSpeciesSelect", "soluteSpeciesHint", "solutePartitionSelect",
        "solutePartitionWeightSelect", "solutePartitionHint",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "cold-enrich", "hot-enrich", "surface-enrich", "bulk-enrich"):
        assert f'value="{mode}"' in HTML
    assert '<input' not in HTML[HTML.index('id="soluteSpeciesSelect"') - 100:HTML.index('id="soluteSpeciesSelect"') + 500]

    assert "function soluteSpeciesVocabulary()" in APP
    assert "function renderSoluteSpeciesOptions()" in APP
    assert "function solutePartitionForFreshSites(fresh, thermalField, capillaryGeometry" in APP
    assert "emittedFraction - referenceFraction" in APP
    assert 'fieldSource = thermalField?.enabled ? "declared reduced thermal field"' in APP
    assert 'fieldSource = "open solid-angle fraction"' in APP
    assert 'fieldSource = "occupied solid-angle fraction"' in APP
    assert "const score = solutePartitionMode !== \"none\" && available ? enrichmentContrast * spatialScore : 0" in APP
    assert "+ activeSolutePartitionWeight() * evaluation.solutePartition.score" in APP
    assert 'id: "solute-partition"' in APP
    assert "solutePartitionRanking:" in APP
    assert "elementRecord(candidate.solutePartition.species).color" in APP

    for invariant in (
        "speciesChosenFromObservedConfiguration: true",
        "candidateSetChanged: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "chemicalPotentialInferred: false",
        "partitionCoefficientInferred: false",
        "phaseDiagramUsed: false",
        "interfacialEnergyInferred: false",
        "diffusionIntegrated: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "## Species-resolved partition geometry" in README
    assert "no text field or hidden material label" in normalized
    assert "global composition-reservoir control remains separate" in normalized
    assert "No chemical potential, equilibrium partition coefficient" in normalized


if __name__ == "__main__":
    test_solute_partition_couples_observed_species_to_frozen_spatial_fields()
    print("species-resolved solute-partition contract: passed")
