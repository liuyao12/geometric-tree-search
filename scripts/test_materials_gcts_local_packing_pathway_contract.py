#!/usr/bin/env python3
"""Contract for the finite local packing-density pathway."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/local-packing-density.js").read_text()


def test_pathway_is_visible_and_leap_linked():
    for element_id in (
        "packingPathwayState", "packingPathwayMetrics",
        "packingDistributionPlot", "packingPathwayPlot",
        "packingPathwayReadout", "packingPathwayBoundary",
        "packingRadialState", "packingRadialChannels",
        "packingRadialPlot", "packingRadialReadout",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function structuralPackingSnapshot" in APP
    assert "function structuralPackingSeries" in APP
    assert "function renderPackingPathway" in APP
    assert "function renderPackingRadialProfile" in APP
    assert "packing: structuralPackingSnapshot()" in APP
    assert 'id: "packing", group: "local"' in APP
    assert 'id: "radial-composition", group: "chemistry"' in APP
    assert "renderPackingPathway();" in APP
    assert ".packing-pathway" in CSS
    assert ".packing-pathway svg rect.before" in CSS
    assert ".radial-material-profile" in CSS


def test_measure_is_finite_invariant_and_not_a_bulk_claim():
    for phrase in (
        "localPackingDensityAudit", "neighborRank: 6",
        "128 radial quantiles with complete equal-radius ties retained",
        "translationInvariant: true", "properRotationInvariant: true",
        "atomPermutationInvariant: true", "periodicImagesUsed: false",
        "massDensityInferred: false", "porosityInferred: false",
        "equilibriumSegregationInferred: false", "surfaceEnergyInferred: false",
        "thermodynamicVolumeInferred: false", "pressureInferred: false",
        "freeEnergyInferred: false", "physicalTimeIntegrated: false",
    ):
        assert phrase in APP
    for phrase in (
        "export function localPackingDensityAudit",
        "medianRelativeDensity", "coreMedianRelativeDensity",
        "surfaceMedianRelativeDensity", "medianRelativeLocalVolume",
        "radialProfile", "referenceRadialProfile", "speciesVocabulary",
        "surfaceExcess", "dominantSurfaceExcessSpecies",
        "targetUsed: false", "usedAsGrowthInput: false",
    ):
        assert phrase in MODULE
    assert "not mass density, porosity, thermodynamic free volume" in HTML


def test_build_242_is_exposed():
    assert 'buildId: "20260827-259"' in APP
    assert 'app.js?v=20260827-259' in HTML
    assert 'style.css?v=20260827-259' in HTML
    assert 'local-packing-density.js?v=20260827-2' in APP


if __name__ == "__main__":
    test_pathway_is_visible_and_leap_linked()
    test_measure_is_finite_invariant_and_not_a_bulk_claim()
    test_build_242_is_exposed()
    print("local packing pathway contract passed")
