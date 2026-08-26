#!/usr/bin/env python3
"""Contract for persistent, non-executing investigation guidance."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_study_compass_contract() -> None:
    assert 'buildId: "20260826-156"' in APP
    assert 'app.js?v=20260826-156' in HTML
    assert 'style.css?v=20260826-64' in HTML
    for element_id in (
        "studyCompass", "studyCompassKind", "studyCompassQuestion",
        "studyCompassIntegrity", "studyCompassShare", "studyCompassGuideButton", "studyCompassProgress",
        "studyCompassObjective", "studyCompassPrediction", "studyCompassInspect",
        "studyCompassBoundary", "studyCompassState", "studyCompassNext",
    ):
        assert f'id="{element_id}"' in HTML
    assert "const STUDY_STAGE_SEQUENCE" in APP
    assert "const STUDY_STAGE_GUIDANCE" in APP
    assert "function renderStudyCompass" in APP
    assert "recipe controls still match" not in APP.lower() or "settingsStillMatch" in APP
    assert "No phase, cluster, unit-cell, energy, or dynamical label" in APP
    assert "cannot invent a placement" in APP
    assert "Leap-frogged structural continuation has no physical clock" in APP
    assert "renderStudyCompass();" in APP
    assert 'dataset.nextStage = "receipt"' in APP
    assert 'scrollIntoView({ behavior: "smooth", block: "start" })' in APP
    assert "setPlaying(true)" not in APP[APP.index("function renderStudyCompass"):APP.index("function syncStageOptions")]
    assert ".study-compass-body" in CSS
    assert ".study-compass-boundary" in CSS
    assert "Build 143 keeps that study design visible" in README
    assert "navigate but never press Play" in README
    assert "mismatches in the receipt" in README



if __name__ == "__main__":
    test_study_compass_contract()
    print("materials study compass contract passed")
