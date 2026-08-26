#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_arm_progress_contract():
    assert 'buildId: "20260826-164"' in APP
    assert 'app.js?v=20260826-164' in HTML
    assert 'style.css?v=20260826-71' in HTML
    assert 'id="studyComparisonProgress"' in HTML
    assert 'aria-label="Saved and executed arm progress"' in HTML

    assert "function studyArmNotebookEvidence" in APP
    assert "entry.scenarioId === scenarioSelect.value" in APP
    assert "entry.registeredStudy?.settingsStillMatch === true" in APP
    assert "entry.executionEvidence?.executed === true" in APP
    assert "function renderStudyComparisonProgress" in APP
    for label in ("complete both arms", "design saved · execute both", "response pair ready",
                  "saved design", "executed response", "prior growth is never reused"):
        assert label in APP
    assert "renderStudyComparisonProgress(outcome.recipeId, comparison)" in APP
    assert APP.count("renderStudyOutcome();") >= 3

    for selector in (".study-comparison-progress", ".study-comparison-progress.design-saved > b",
                     ".study-comparison-progress.ready > b"):
        assert selector in CSS

    assert "Build 150 brings that execution audit back into the active study card" in README
    assert "Saving or clearing the local notebook updates this" in README


if __name__ == "__main__":
    test_study_arm_progress_contract()
    print("study arm progress contract passed")
