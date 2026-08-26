#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_registered_response_contract():
    assert 'id="studyComparisonResponse"' in HTML
    assert 'aria-label="Registered outcome response"' in HTML
    assert "function notebookRegisteredOutcomeObservations" in APP
    assert "function renderStudyComparisonResponse" in APP
    assert 'direction.textContent = "reference − contrast"' in APP
    assert "referenceRecord.value - contrastRecord.value" in APP
    assert "not certified" in APP
    assert "no proxy is invented" in APP
    assert "renderStudyComparisonResponse(recipeId, comparison)" in APP

    for outcome in (
        "continuation sites", "exact oxygen anchors", "held-out mismatch",
        "registry score", "effective nuclei", "boundary rejections", "RDF tail",
    ):
        assert f'"{outcome}"' in APP

    assert "publicBoundaryPrunes++" in APP
    assert "publicBoundaryPrunes," in APP
    assert "validationMismatch: receiptRound(currentTrainingPoint().validationLoss)" in APP
    for selector in (
        ".study-comparison-response", ".study-comparison-response-grid",
        ".study-comparison-response-grid article.unavailable",
    ):
        assert selector in CSS
    assert "Build 151 turns a ready response pair" in README
    assert "portal never substitutes a convenient proxy" in README


if __name__ == "__main__":
    test_registered_response_contract()
    print("registered response contract passed")
