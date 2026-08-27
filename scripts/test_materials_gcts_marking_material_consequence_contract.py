from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_every_marking_winner_has_a_coordinate_free_material_consequence():
    assert "function markingWinnerMaterialConsequence(entry)" in APP
    assert "const materialConsequence = markingWinnerMaterialConsequence(entry);" in APP
    assert "materialConsequence: materialConsequenceFor(winner?.candidate)" in APP
    assert "sharedSites: evaluation.merged.length" in APP
    assert "emittedSites: evaluation.fresh.length" in APP
    assert "localMismatch: finite(effectiveGeometricStrain(evaluation).total)" in APP
    assert "constraintMargin: finite(evaluation.constraintRobustness.score)" in APP
    assert "favorableChannel" in APP
    assert "burdenChannel" in APP
    assert "consequence.digest = notebookStringHash" in APP


def test_consequence_is_previewed_and_target_use_is_separate_from_marking_score():
    assert "marking-consequence-grid" in APP
    assert ".marking-consequence-grid" in STYLE
    assert "targetUsedForMarkingScores: false" in APP
    assert "materialConsequenceTargetUsed: !reconstructionCertified" in APP
    assert "targetUsedForMaterialConsequence: !reconstructionCertified" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "executed: false" in APP
    assert "no candidate is created, removed, or executed" in HTML


def test_consequence_is_receipted_and_release_is_consistent():
    assert "materialConsequence: marking.materialConsequence ?" in APP
    assert "materialConsequenceDigest: audit.portfolio.materialConsequence?.digest" in APP
    assert 'buildId: "20260827-229"' in APP
    assert 'app.js?v=20260827-229' in HTML
    assert "Build 214" in README
    assert "Build 214" in DOC


if __name__ == "__main__":
    test_every_marking_winner_has_a_coordinate_free_material_consequence()
    test_consequence_is_previewed_and_target_use_is_separate_from_marking_score()
    test_consequence_is_receipted_and_release_is_consistent()
    print("marking material consequence contract passed")
