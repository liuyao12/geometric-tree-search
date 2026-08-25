#!/usr/bin/env python3
"""Contract for observed multi-nucleus growth and geometric impingement."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_multi_nucleus_growth_uses_only_observed_occurrences() -> None:
    for element_id in ("growthNucleiSelect", "growthNucleiHint", "nucleiBadge", "nucleiBadgeLabel"):
        assert f'id="{element_id}"' in HTML
    for count in ("1", "2", "4"):
        assert f'value="{count}"' in HTML
    assert ".nuclei-badge" in CSS

    assert "function observedGrowthSeedIndices()" in APP
    assert "overlapGrammar.replaySeedIndex" in APP
    assert "minimumSeparation" in APP
    assert "occurrence.position.distanceTo" in APP
    assert "seedNucleus: true" in APP
    assert "nucleusId: nucleusIndex + 1" in APP
    assert "placedClusters.forEach(enqueueRulesFromPlacement)" in APP
    assert "function nucleusInterfaceForCandidate(candidate, evaluation)" in APP
    assert "atom.interfaceContact = true" in APP
    assert "crossNucleusMergeContacts++" in APP
    assert "interfaceRingMaterial" in APP

    for invariant in (
        'selection: "deterministic farthest-point traversal of observed cluster occurrence centers"',
        'orientations: "observed proper-SE(3) occurrence poses; no artificial grain rotation"',
        "exactSpeciesAndCollisionGatesPreserved: true",
        "targetUsedToSelectSeeds: false",
        "nucleationRateInferred: false",
        "grainIdentityInferred: false",
        "interfacialEnergyInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    assert "Multiple observed nuclei and geometric impingement" in README
    assert "farthest-point traversal" in README
    assert "not a grain-boundary classification" in README


if __name__ == "__main__":
    test_multi_nucleus_growth_uses_only_observed_occurrences()
    print("multi-nucleus geometric growth contract: passed")
