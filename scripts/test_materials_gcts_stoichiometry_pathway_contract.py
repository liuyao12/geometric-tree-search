#!/usr/bin/env python3
"""Contract for the species-resolved structural stoichiometry pathway."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
FEEDSTOCK = (ROOT / "apps/iqc-growth-live/feedstock-reservoir.js").read_text()


def test_pathway_is_species_resolved_and_leap_linked():
    for element_id in (
        "stoichiometryPathwayState", "stoichiometryPathwaySpecies",
        "stoichiometryPathwayTimeline", "stoichiometryPathwayPlot",
        "stoichiometryPathwayReadout", "stoichiometryPathwayBoundary",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function structuralStoichiometrySeries" in APP
    assert "function renderStoichiometryPathway" in APP
    assert "renderStoichiometryPathway();" in APP
    assert "selectedLeapIndex = state.leapIndex" in APP
    assert "selectedLeapIndex = point.state.leapIndex" in APP
    assert ".stoichiometry-pathway-timeline" in CSS
    assert ".stoichiometry-stack" in CSS


def test_arbitrary_species_counts_and_reservoirs_remain_explicit():
    for phrase in (
        "states.flatMap((state) => state.composition?.symbols || [])",
        "state.composition?.fractions?.[symbol]",
        "composition.counts?.[selectedStoichiometrySpecies]",
        "composition.targetFractions?.[selectedStoichiometrySpecies]",
        "selectedState?.feedstock?.species?.find", "exactIntegerSiteCounts: true",
        "speciesVocabulary:",
    ):
        assert phrase in APP
    assert "if (audit.open) return { reservoir: { ...reservoir, consumed," in FEEDSTOCK
    assert 'feedstock-reservoir.js?v=20260827-2' in APP


def test_pathway_cannot_be_misread_as_thermodynamics_or_kinetics():
    for phrase in (
        "suppliedCompositionUsedAsReferenceOnly: true",
        "chemicalPotentialInferred: false", "phaseEquilibriumInferred: false",
        "diffusionIntegrated: false", "physicalTimeIntegrated: false",
        "not chemical potential, activity, phase equilibrium, segregation energy, diffusion, flux, rate, or physical time",
    ):
        assert phrase in APP
    assert "not chemical potential, phase equilibrium, diffusion, flux, or physical time" in HTML


def test_build_237_is_exposed():
    assert 'buildId: "20260827-237"' in APP
    assert 'app.js?v=20260827-237' in HTML
    assert 'style.css?v=20260827-237' in HTML


if __name__ == "__main__":
    test_pathway_is_species_resolved_and_leap_linked()
    test_arbitrary_species_counts_and_reservoirs_remain_explicit()
    test_pathway_cannot_be_misread_as_thermodynamics_or_kinetics()
    test_build_237_is_exposed()
    print("stoichiometry pathway contract passed")
