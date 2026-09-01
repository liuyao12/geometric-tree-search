#!/usr/bin/env python3
"""Source/artifact contract for the browser ice pose-marking audit."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PORTAL = ROOT / "apps" / "iqc-growth-live"


def test_portal_exposes_honest_disjoint_pose_marking_result() -> None:
    artifact = json.loads((PORTAL / "ice-orientation-marking-artifact.json").read_text())
    app = (PORTAL / "app.js").read_text()
    atlas = (PORTAL / "evidence-atlas.js").read_text()
    readme = (PORTAL / "README.md").read_text()
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text()

    assert artifact["schema"] == "gcts-ice-orientation-marking-audit-v1"
    assert artifact["candidateDigest"] == \
        "c9f23613b2b8a595495a470e024076d25b6e9ddea485c014099728fdcaa2c2f1"
    assert artifact["modelDigest"] == \
        "fafb81a25297a3ebd1cb0f0a49bab790ecf40d7cc88cec008728b2d2b8533416"
    assert artifact["heldout"] == {
        "candidateDomains": 65, "targetMatchedDomains": 51,
        "alternatives": 191, "exactSupplyDomains": 40,
    }
    assert artifact["arms"]["learned"]["exact"] == 9
    assert artifact["arms"]["unmarked"]["exact"] == 8
    assert artifact["arms"]["shuffled"] == {
        "count": 31, "medianExact": 9, "bestExact": 9, "empiricalP": .75,
    }
    assert artifact["gate"] == {
        "passed": False, "learnedBeatsUnmarked": True, "learnedBeatsShuffles": False,
    }
    protocol = artifact["protocol"]
    assert protocol["rawTrainHeldoutMoleculeOverlap"] == 0
    assert protocol["candidatesFrozenBeforeTarget"]
    assert not protocol["targetUsedForFitOrRanking"]
    assert not protocol["canonicalBranchMaterializedDuringGrowth"]
    forbidden = {"trainCenters", "heldoutCenters", "targetCoordinates"}
    assert forbidden.isdisjoint(artifact)
    assert forbidden.isdisjoint(protocol)

    assert 'ice-orientation-marking-artifact.json?v=20260901-427' in app
    assert 'iceOrientationMarkingTransferPassed' in app
    assert 'orientationMarkingTransfer: ICE_ORIENTATION_MARKING_AUDIT' in app
    assert 'held-out pose marking' in app
    assert 'Inspect pose-marking evidence' in app
    assert 'gcts:open-evidence-system' in app
    assert 'Disjoint pose-marking transfer' in atlas
    assert 'renderSystem(key)' in atlas
    assert 'Build 402 · disjoint proton-pose marking audit' in readme
    assert 'Disjoint proton-pose marking audit (Build 402)' in benchmark


if __name__ == "__main__":
    test_portal_exposes_honest_disjoint_pose_marking_result()
    print("ice orientation marking portal contract: passed")
