"""Static integration contract for species-pair geometric exclusions."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_growth_uses_train_derived_colored_distance_envelopes() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    assert "learnColoredDistanceEnvelopes" in source
    assert "coloredPairExclusion(firstSpecies, secondSpecies)" in source
    assert "coloredPairExclusion(first.species, second.species)" in source
    assert "coloredPairExclusion(site.species, atom.species)" in source
    assert "coloredDistanceEnvelopes?.maximumExclusion" in source
    assert "learnColoredCoordinationEnvelopes" in source
    assert "coordinationOverflowsForFreshSites" in source
    assert "trial.flatMap((trialEntry) => trialEntry.evaluation.fresh)" in source
    assert "colored coordination capacities exceeded" in source
    assert "learnColoredAngularEnvelopes" in source
    assert "angularViolationsForFreshSites" in source
    assert "colored angular envelopes violated" in source
    assert "coloredGeometricStrain" in source
    assert "DEFAULT_GEOMETRIC_STRAIN_WEIGHT" in source
    assert "activeGeometricStrainWeight" in source
    assert "target-blind soft ordering of the unchanged exact candidate set" in source
    assert "uniqueFreshSites(trial.flatMap((trialEntry) => trialEntry.evaluation.fresh))" in source
    assert "function constraintProjectionForFreshSites(rawFreshSites, { recordWork = true } = {})" in source
    assert "nearbyAtoms(site.p, reach)" in source
    assert "nearbyAtoms(center.p, reach)" in source
    assert "coordinationOverflowsForFreshSites(fresh, constraintProjection)" in source
    assert "angularViolationsForFreshSites(fresh, constraintProjection)" in source
    assert "geometricStrainForFreshSites(fresh, constraintProjection)" in source
    assert "exact finite-reach neighborhood evaluation via the live spatial index" in source
    assert 'markingHeading.textContent = pipelineStage === 0 ? "colored geometric envelopes"' in source
    assert 'role: "hard geometric exclusion learned from supplied positions; not a pair potential"' in source
    assert 'role: "causal upper saturation limits; incomplete frontier shells may remain below the bound"' in source
    assert 'role: "causal three-body admissibility bands over already present contact neighbors; not an angular potential"' in source
    assert "physicalPotentialUsed: false" in source
    assert "one universal collision radius" in readme
    assert "This is chemistry-as-geometry, not a pair potential" in readme
    assert 'app.js?v=20260825-128' in html


if __name__ == "__main__":
    test_growth_uses_train_derived_colored_distance_envelopes()
    print("colored geometric exclusion integration contract: passed")
