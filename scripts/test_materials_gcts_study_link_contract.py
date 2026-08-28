#!/usr/bin/env python3
"""Contract for versioned, curated-only recipe reconstruction links."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_link_contract() -> None:
    assert 'buildId: "20260828-311"' in APP
    assert 'app.js?v=20260828-311' in HTML
    assert 'style.css?v=20260828-311' in HTML
    assert 'id="studyCompassShare"' in HTML
    assert "function shareableStudyUrl" in APP
    assert "function copyShareableInvestigationUrl" in APP
    share = APP[APP.index("function shareableStudyUrl"):APP.index("function shareableCustomExperimentUrl")]
    assert 'scenarioSelect.value === "imported"' in share
    assert 'url.searchParams.set("studyVersion", "1")' in share
    assert 'url.searchParams.set("study", audit.id)' in share
    assert 'url.searchParams.set("stage", String(pipelineStage))' in share
    assert "coordinates" not in share
    assert "coefficients" not in share
    launch_start = APP.index("function applyLaunchParameters")
    launch = APP[launch_start:APP.index("restoreMarkingLibrary();", launch_start)]
    assert 'requestedStudyVersion === "1"' in launch
    assert "MATERIALS_STUDY_RECIPES.find" in launch
    assert "STUDY_STAGE_SEQUENCE.some" in launch
    assert "applyGrowthProtocol(requestedRecipe.protocol, { sync: false })" in launch
    assert "coordinatesEmbedded: false" in launch
    assert "learnedWeightsEmbedded: false" in launch
    assert "growthHistoryEmbedded: false" in launch
    assert "setPlaying(true)" not in launch
    assert "unsupported recipe schema" in launch
    assert "unknown recipe" in launch
    assert "if (studyLaunchAudit) return 0" in launch
    assert "function markingMatchesDraft" in APP
    assert "compatibleMarkings().filter(markingMatchesDraft)" in APP
    assert "Build 310 · reconstructable custom investigations" in README
    assert "contains no atomic coordinates" in README
    assert "fail closed at known positions" in README


if __name__ == "__main__":
    test_study_link_contract()
    print("materials study link contract passed")
