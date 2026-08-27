from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_marking_winners_receive_bounded_multiscale_counterfactuals():
    assert "function markingWinnerMultiscaleConsequence(entry, maximumAnchorAtoms = 64)" in APP
    assert "function counterfactualOrderSnapshot(stats)" in APP
    assert "function counterfactualScatteringSnapshot(stats)" in APP
    assert "const beforeStats = calculateStructuralStats(anchors" in APP
    assert "const afterStats = calculateStructuralStats([...anchors, ...fresh]" in APP
    assert "localSymmetryTransition(counterfactualOrderSnapshot(beforeStats)" in APP
    assert "reciprocalSpaceTransition(counterfactualScatteringSnapshot(beforeStats)" in APP


def test_counterfactual_is_cached_invariant_and_never_drives_search():
    assert "const materialConsequenceCache = new Map();" in APP
    assert "if (!materialConsequenceCache.has(candidate.key))" in APP
    assert 'analysisWindowPolicy: "nearest 64 current atoms to emitted-site centroid plus every emitted site"' in APP
    assert "properRotationInvariant: true" in APP
    assert "atomPermutationInvariant: true" in APP
    assert "usedForRanking: false" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "executed: false" in APP
    assert "targetUsed," in APP


def test_multiscale_readout_is_visible_receipted_and_versioned():
    assert "S(q) peak prominence" in APP
    assert "multiscaleStructure: marking.materialConsequence.multiscaleStructure ?" in APP
    assert "pairDistanceEvaluations" in APP
    assert "q₆/|ψ₆|" in HTML
    assert 'buildId: "20260827-242"' in APP
    assert 'app.js?v=20260827-242' in HTML
    assert "Build 215" in README
    assert "Build 215" in DOC


if __name__ == "__main__":
    test_marking_winners_receive_bounded_multiscale_counterfactuals()
    test_counterfactual_is_cached_invariant_and_never_drives_search()
    test_multiscale_readout_is_visible_receipted_and_versioned()
    print("marking multiscale consequence contract passed")
