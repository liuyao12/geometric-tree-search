from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_every_marking_scores_one_identical_frozen_frontier():
    assert "function buildMarkingFrontierCounterfactual(admissible, candidateSetDigest)" in APP
    assert "const markings = compatibleMarkings();" in APP
    assert "marking.channelBasis, marking.activeChannelsByPrototype" in APP
    assert "hardAdmittedCandidateSetDigest: frozenFrontierDigest(admissible)" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "targetUsed: false" in APP
    assert "executed: false" in APP


def test_frontier_marking_inspector_previews_without_execution():
    assert 'id="markingFrontierState"' in HTML
    assert 'id="markingFrontierRows"' in HTML
    assert 'id="markingFrontierDetail"' in HTML
    assert ".marking-frontier-counterfactual" in STYLE
    assert "function renderMarkingFrontierAudit(snapshot)" in APP
    assert "function previewMarkingFrontierWinner(row, snapshot)" in APP
    assert "best saved mark per action" in APP
    assert "preview only" in APP


def test_counterfactual_is_receipted_and_release_is_consistent():
    assert "markingFrontierCounterfactual: (() =>" in APP
    assert "scoreDigest: marking.scoreDigest" in APP
    assert 'buildId: "20260826-213"' in APP
    assert 'app.js?v=20260826-213' in HTML
    assert "Build 213" in README
    assert "Build 213" in DOC


if __name__ == "__main__":
    test_every_marking_scores_one_identical_frozen_frontier()
    test_frontier_marking_inspector_previews_without_execution()
    test_counterfactual_is_receipted_and_release_is_consistent()
    print("marking frontier counterfactual contract passed")
