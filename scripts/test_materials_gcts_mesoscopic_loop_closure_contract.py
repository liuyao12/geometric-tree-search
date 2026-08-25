#!/usr/bin/env python3
"""Contract for multi-parent geometric loop-closure ordering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_loop_closure_is_independent_target_blind_soft_consensus() -> None:
    for element_id in (
        "loopClosurePreferenceSelect",
        "loopClosureWeightSelect",
        "loopClosureHint",
        "loopClosureBadge",
        "loopClosureBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML
    assert 'value="consensus"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML
    assert ".loop-closure-badge" in CSS

    assert "function mesoscopicLoopClosureForCandidate(candidate)" in APP
    assert "function coloredSiteSetResidual(first, second)" in APP
    assert "overlapGrammar.byFrom.get(placement.type)" in APP
    assert "placement.rotation.clone().multiply(rule.rotation).normalize()" in APP
    assert "path.parentId !== candidate.parentId" in APP
    assert "independentCompatiblePaths" in APP
    assert "independentConflictingPaths" in APP
    assert "+ activeLoopClosureWeight() * evaluation.loopClosure.score" in APP
    assert 'id: "loop-closure"' in APP
    assert "mesoscopicLoopClosureRanking:" in APP

    for invariant in (
        "generatingParentExcludedFromConsensus: true",
        "frozenConnectionRulesOnly: true",
        "completeColoredSiteSetsCompared: true",
        "rawQuaternionUsedForCompatibility: false",
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "heldoutTargetUsed: false",
        "elasticEnergyInferred: false",
        "modulusOrStressInferred: false",
    ):
        assert invariant in APP

    assert "mesoscopic loop-closure" in README.lower()
    assert "one tree edge cannot certify itself" in README
    assert "unchanged exact frontier" in README
    assert "not elastic energy" in README


if __name__ == "__main__":
    test_loop_closure_is_independent_target_blind_soft_consensus()
    print("mesoscopic loop-closure contract: passed")
