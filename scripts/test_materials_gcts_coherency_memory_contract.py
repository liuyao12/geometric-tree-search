#!/usr/bin/env python3
"""Contract for finite-range accepted-history coherency memory."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_coherency_memory_is_finite_target_blind_and_history_dependent() -> None:
    for element_id in (
        "coherencyMemorySelect", "coherencyReachSelect",
        "coherencyMemoryWeightSelect", "coherencyMemoryHint",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "continue", "relieve", "isolate"):
        assert f'value="{mode}"' in HTML
    for reach in ("1", "2", "3"):
        assert f'value="{reach}"' in HTML

    assert "function coherencyMemoryForCandidate(" in APP
    assert "for (let hop = 0; hop < coherencyMemoryReach" in APP
    assert "weight: 1 / (1 + hop)" in APP
    assert "placedClusters.find((entry) => entry.id === id)?.coherencyMemory" in APP
    assert "placement.coherencyMemory" not in APP  # stored in the placement constructor, not mutated later
    assert "coherencyMemory: { mismatch: evaluation.coherencyMemory.candidateMismatch" in APP
    for metric in (
        "candidateMismatch", "inheritedMismatch", "mismatchGradient",
        "orientationAgreement", "hotspot",
    ):
        assert metric in APP

    assert 'id: "coherency-memory"' in APP
    assert "activeCoherencyMemoryWeight() * evaluation.coherencyMemory.score" in APP
    assert "coherencyMemoryRanking" in APP
    assert 'name: "coherency memory"' in APP
    assert "new THREE.OctahedronGeometry" in APP
    for invariant in (
        "acceptedHistoryOnly: true", "actionGeometryChanged: false",
        "candidateSetChanged: false", "hardAdmissionChanged: false", "targetUsed: false",
        "stressInferred: false", "elasticEnergyInferred: false", "modulusInferred: false",
        "forceBalanceSolved: false", "relaxationIntegrated: false", "dislocationModeled: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP

    normalized = " ".join(README.split())
    assert "Finite-range coherency memory" in README
    assert "Only committed placements enter the memory" in normalized
    assert "not long-range elasticity" in normalized
    assert "cannot authorize a pose" in normalized


if __name__ == "__main__":
    test_coherency_memory_is_finite_target_blind_and_history_dependent()
    print("materials GCTS coherency-memory contract: passed")
