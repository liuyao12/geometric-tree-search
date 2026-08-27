from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_horizon_is_visible_selectable_and_frozen_at_registration():
    assert 'id="markingInterventionHorizon"' in HTML
    assert 'value="1"' in HTML and 'value="4" selected' in HTML and 'value="8"' in HTML
    assert '$("markingInterventionHorizon")' in APP
    assert "comparisonHorizonLeaps: Number(markingInterventionHorizon.value)" in APP
    assert "markingInterventionHorizon.disabled = Boolean(experiment)" in APP
    assert ".marking-intervention select" in STYLE


def test_growth_pauses_and_further_steps_fail_closed_at_horizon():
    assert "function enforceMarkingComparisonHorizon(render = false)" in APP
    assert "leapEventCount < markingComparisonExperiment.comparisonHorizonLeaps" in APP
    assert "enforceMarkingComparisonHorizon();" in APP
    assert "if (enforceMarkingComparisonHorizon(true)) return;" in APP
    assert "setPlaying(false);" in APP
    assert "pipelineAuto = false;" in APP


def test_receipt_and_notebook_require_matched_horizon_or_two_fixed_points():
    assert "executedStructuralLeaps: leapEventCount" in APP
    assert "comparisonHorizonReached" in APP
    assert "comparisonHorizonExceeded" in APP
    assert "terminalFixedPointObserved" in APP
    assert "matchedExecutionHorizon" in APP
    assert "matchedTerminalFixedPoints" in APP
    assert "responseComparable = valid && baselineExecuted && alternativeExecuted" in APP
    assert "Both runs must stop at H" in APP


def test_build_218_narrative_and_assets_are_current():
    assert "Build 218" in README
    assert "Build 218" in DOC
    assert 'buildId: "20260827-226"' in APP
    assert 'app.js?v=20260827-226' in HTML


if __name__ == "__main__":
    test_horizon_is_visible_selectable_and_frozen_at_registration()
    test_growth_pauses_and_further_steps_fail_closed_at_horizon()
    test_receipt_and_notebook_require_matched_horizon_or_two_fixed_points()
    test_build_218_narrative_and_assets_are_current()
    print("marking matched-horizon contract passed")
