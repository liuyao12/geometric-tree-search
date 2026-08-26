#!/usr/bin/env python3
"""Contract for registered, non-executing study comparison arms."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_registered_study_comparison_contract() -> None:
    assert 'buildId: "20260826-153"' in APP
    assert 'app.js?v=20260826-153' in HTML
    assert 'style.css?v=20260826-62' in HTML
    for element_id in (
        "studyComparison", "studyComparisonQuestion", "studyComparisonFactor",
        "studyComparisonArms", "studyComparisonOutcomes", "studyComparisonBoundary",
    ):
        assert f'id="{element_id}"' in HTML
    assert "const MATERIALS_STUDY_COMPARISONS" in APP
    comparisons = APP[APP.index("const MATERIALS_STUDY_COMPARISONS"):APP.index("const GROWTH_PROTOCOL_CONTROL_IDS")]
    for recipe_id in (
        '"bulk-order"', '"molecular-ice"', "quasicrystal", "moire",
        "epitaxy", "impingement", '"pore-fill"', '"glass-control"',
    ):
        assert recipe_id in comparisons
    for factor in (
        "clusters² promotion", "connection marking", "marking chirality",
        "substrate registry", "nucleus count", "hard confinement",
    ):
        assert factor in comparisons
    assert comparisons.count('id: "reference"') == 8
    assert comparisons.count('id: "contrast"') == 8
    assert "Only the declared template spacing changes" in comparisons
    assert "Only the hard public boundary changes" in comparisons

    apply_start = APP.index("function applyStudyComparisonArm")
    apply_end = APP.index("const STUDY_STAGE_SEQUENCE", apply_start)
    apply_source = APP[apply_start:apply_end]
    assert "applyStudyRecipe(recipeId)" in apply_source
    assert 'activeStudyArmId = arm.id' in apply_source
    assert "applyStudyArmSettings(arm)" in apply_source
    assert "enterPipelineStage(0)" in apply_source
    assert "nothing executed" in apply_source
    assert "setPlaying(true)" not in apply_source
    assert "performEvent" not in apply_source

    audit_start = APP.index("function activeStudyRecipeAudit")
    audit_end = APP.index("function renderStudyGuide", audit_start)
    audit_source = APP[audit_start:audit_end]
    assert "registeredComparison" in audit_source
    assert "activeArmId" in audit_source
    assert "autoExecuted: false" in audit_source
    assert "comparisonHierarchy" in audit_source
    assert "comparisonPolicy" in audit_source
    assert "comparisonEpitaxyTemplate" in audit_source
    assert "comparisonNuclei" in audit_source
    assert "comparisonBoundary" in audit_source
    assert "registeredStudy: receipt.studyDesign?.id" in APP
    assert "registeredComparison?.activeArmId" in APP
    assert "registeredComparison?.activeArmLabel" in APP
    assert "autoExecuted: false" in APP

    share_start = APP.index("function shareableStudyUrl")
    share_end = APP.index("async function copyShareableStudyUrl", share_start)
    assert 'activeStudyArmId !== "reference"' in APP[share_start:share_end]
    assert ".study-comparison-arms" in CSS
    assert ".study-comparison > em" in CSS
    assert "registered comparison" in HTML
    assert "Build 147 adds a persistent" in README
    assert "always returns to the identical known positions" in README
    assert "Compact share links remain reference-only" in README


if __name__ == "__main__":
    test_registered_study_comparison_contract()
    print("materials study comparison contract passed")
