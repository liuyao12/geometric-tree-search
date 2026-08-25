#!/usr/bin/env python3
"""Contract for optional geometry-only microstructure-conditioned growth."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_microstructure_coupling_ranks_but_does_not_relabel_geometry() -> None:
    for element_id in (
        "microstructureCouplingSelect",
        "microstructureCouplingWeightSelect",
        "microstructureCouplingHint",
        "growthMechanismCanvas",
    ):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "gap-heal", "interface-follow", "anomaly-avoid", "occupancy-follow"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function microstructureCouplingForCandidate(candidate, evaluation)" in APP
    assert "function microstructureRoleMatches(role, mode = microstructureCouplingMode)" in APP
    assert "growthEventNeighborhood(candidate, evaluation)" in APP
    assert "+ activeMicrostructureCouplingWeight() * evaluation.microstructureCoupling.score" in APP
    assert 'id: "microstructure"' in APP
    assert "microstructureCouplingRanking:" in APP
    assert "usedForBranchRanking: activeMicrostructureCouplingWeight() > 0" in APP
    assert "branchRankingMode: microstructureCouplingMode" in APP

    for nonclaim in (
        "observedInputGeometryUsed: true",
        "heldoutTargetUsed: false",
        "defectLabelsUsed: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "formationEnergyInferred: false",
        "mobilityInferred: false",
    ):
        assert nonclaim in APP

    assert "microstructure-coupling experiment" in README.lower()
    assert "same exact frontier" in README
    assert "never become vacancy, dislocation, grain" in README
    assert "No formation energy" in README


if __name__ == "__main__":
    test_microstructure_coupling_ranks_but_does_not_relabel_geometry()
    print("microstructure coupling contract: passed")
