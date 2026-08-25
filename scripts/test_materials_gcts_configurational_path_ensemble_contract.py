#!/usr/bin/env python3
"""Contract for reproducible, non-thermodynamic branch-path exploration."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_configurational_path_ensemble_preserves_exact_frontier() -> None:
    for element_id in (
        "explorationScaleSelect",
        "explorationScaleHint",
        "resampleGrowthButton",
        "explorationBadge",
        "explorationBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML
    for scale in ("0", "0.05", "0.15", "0.35"):
        assert f'value="{scale}"' in HTML
    assert 'id="explorationScaleSelect"' in HTML
    assert '<input' not in HTML[HTML.index('id="explorationScaleSelect"') - 100:HTML.index('id="explorationScaleSelect"') + 500]
    assert ".exploration-badge" in CSS

    assert "function deterministicPathUniform(candidateKey)" in APP
    assert "function geometricExplorationOffset(candidate)" in APP
    assert "growthPathSeed}|${eventIndex}|${candidateKey}" in APP
    assert "-Math.log(-Math.log(uniform))" in APP
    assert "selectionScore: score + explorationOffset" in APP
    assert "second.selectionScore - first.selectionScore" in APP
    assert 'label: "combined greedy"' in APP
    assert "growthPathSeed += 1" in APP

    for invariant in (
        "candidateSetChanged: false",
        "hardAdmissionChanged: false",
        "exactCandidateGeometryChanged: false",
        "physicalTemperatureKelvin: null",
        "energyUnitsUsed: false",
        "boltzmannDistributionClaimed: false",
        "freeEnergyInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    assert "Reproducible configurational-path ensemble" in README
    assert "not Kelvin temperature" in README
    assert "Boltzmann weights" in README
    assert "Candidate positions" in README


if __name__ == "__main__":
    test_configurational_path_ensemble_preserves_exact_frontier()
    print("configurational path ensemble contract: passed")
