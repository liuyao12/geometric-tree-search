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
    assert 'markingHeading.textContent = pipelineStage === 0 ? "colored distance envelopes"' in source
    assert 'role: "hard geometric exclusion learned from supplied positions; not a pair potential"' in source
    assert 'role: "causal upper saturation limits; incomplete frontier shells may remain below the bound"' in source
    assert "physicalPotentialUsed: false" in source
    assert "one universal collision radius" in readme
    assert "This is chemistry-as-geometry, not a pair potential" in readme
    assert 'app.js?v=20260824-12' in html


if __name__ == "__main__":
    test_growth_uses_train_derived_colored_distance_envelopes()
    print("colored geometric exclusion integration contract: passed")
