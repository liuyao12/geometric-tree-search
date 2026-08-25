#!/usr/bin/env python3
"""Contract for observed multi-nucleus growth and geometric impingement."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()
POSES = (APP_DIR / "proper-pose-orbits.js").read_text()


def test_multi_nucleus_growth_uses_only_observed_occurrences() -> None:
    for element_id in ("growthNucleiSelect", "growthNucleiHint", "nucleiBadge", "nucleiBadgeLabel"):
        assert f'id="{element_id}"' in HTML
    for element_id in ("nucleusInterfaceInspector", "nucleusInterfaceState", "nucleusPairButtons", "nucleusPairDetail"):
        assert f'id="{element_id}"' in HTML
    for count in ("1", "2", "4"):
        assert f'value="{count}"' in HTML
    assert ".nuclei-badge" in CSS
    assert ".nucleus-interface-inspector" in CSS

    assert "function observedGrowthSeedIndices()" in APP
    assert "overlapGrammar.replaySeedIndex" in APP
    assert "minimumSeparation" in APP
    assert "occurrence.position.distanceTo" in APP
    assert "referenceSupports" in APP
    assert "every((referenceIndex) => !occupied.has(referenceIndex))" in APP
    assert "seedNucleus: true" in APP
    assert "nucleusId: nucleusIndex + 1" in APP
    assert "placedClusters.forEach(enqueueRulesFromPlacement)" in APP
    assert "function nucleusInterfaceForCandidate(candidate, evaluation)" in APP
    assert "function growthNucleusPairs()" in APP
    assert "symmetryReducedMisorientation" in APP
    assert "properSymmetryReducedMisorientationDegrees" in APP
    assert "properGaugePairsMinimized" in APP
    assert "improperRotationsQuotiented: false" in APP
    assert "function renderNucleusInterfaceInspector()" in APP
    assert "new THREE.LineDashedMaterial" in APP
    assert "atom.interfaceContact = true" in APP
    assert "crossNucleusMergeContacts++" in APP
    assert "interfaceRingMaterial" in APP

    for invariant in (
        "selection: nucleationSelectionAudit",
        'additionalNuclei: "atom-disjoint farthest-point traversal within one recurring fitted cluster type"',
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
    normalized_readme = " ".join(README.split())
    assert "proper symmetry-reduced misorientation" in normalized_readme
    assert "not a CSL grain-boundary assignment" in normalized_readme
    assert "export function symmetryReducedMisorientation(first, second" in POSES
    assert "coloredMetricClassKey(first, metricToleranceFraction)" in POSES
    assert "frameOrbitDistance(firstFrames, secondFrames)" in POSES
    assert "firstFrame.properCode === secondFrame.properCode" in POSES
    assert 'reason: "different colored metric classes"' in POSES
    assert "improperRotationsQuotiented: false" in POSES


if __name__ == "__main__":
    test_multi_nucleus_growth_uses_only_observed_occurrences()
    print("multi-nucleus geometric growth contract: passed")
