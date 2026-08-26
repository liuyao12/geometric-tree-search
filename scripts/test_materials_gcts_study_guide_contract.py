#!/usr/bin/env python3
"""Static contract for the transparent materials-science study guide."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_guide_contract() -> None:
    assert 'buildId: "20260826-154"' in APP
    assert 'app.js?v=20260826-154' in HTML
    assert 'style.css?v=20260826-63' in HTML
    for element_id in ("studyGuideButton", "studyGuide", "studyGuideClose",
                       "studyRecipeList", "studyRecipeDetail"):
        assert f'id="{element_id}"' in HTML
    for recipe_id in ("bulk-order", "molecular-ice", "quasicrystal", "moire",
                      "epitaxy", "impingement", "pore-fill", "glass-control"):
        assert f'id: "{recipe_id}"' in APP
    assert "const MATERIALS_STUDY_RECIPES" in APP
    assert "function activeStudyRecipeAudit" in APP
    assert "function applyStudyRecipe" in APP
    assert "convenienceOnly: true" in APP
    assert "hiddenPhysicsAdded: false" in APP
    assert "candidateGeometryAuthorized: false" in APP
    assert "settingsStillMatch" in APP
    assert "no growth has run" in APP
    assert "const studyDesign = activeStudyRecipeAudit();" in APP
    assert "studyDesign: studyDesign ?" in APP
    assert "predictionAudit: activeStudyOutcomeAudit()" in APP
    assert ".study-guide-shell" in CSS
    assert ".study-recipe-manifest" in CSS
    assert ".study-recipe-boundary" in CSS
    assert "Build 142 adds a question-driven" in README
    assert "starts nothing automatically" in README
    assert "adds no hidden physics" in README


if __name__ == "__main__":
    test_study_guide_contract()
    print("materials study guide contract passed")
