#!/usr/bin/env python3
"""Static contract for Build 290's retained-leap settling robustness map."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/settling-material-sensitivity.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_history_map_is_visible_and_selects_the_exact_leap():
    for element_id in (
        "settlingResponseHistoryState", "settlingResponseHistory",
        "settlingResponseHistoryBoundary",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function renderSettlingResponseHistory" in APP
    assert 'settlingResponseHistory.addEventListener("click"' in APP
    assert "selectedLeapIndex = retainedIndex" in APP
    assert "renderStructuralLeap(leapHistory[retainedIndex])" in APP
    assert ".settling-response-history" in CSS


def test_history_never_mixes_units_or_relabels_sequence_as_time():
    for fragment in (
        "within one material field across retained leaps and certified arms only; no cross-unit scalar",
        "discrete retained GCTS search order; not independent specimens or physical time",
        "retainedWindowOnly: true", "targetUsed: false", "usedForAdmission: false",
        "usedForRanking: false", "energyInferred: false", "kineticsInferred: false",
        "physicalTimeModeled: false",
    ):
        assert fragment in MODULE
    assert "Search order is not independent sampling, physical time, kinetics, or a trajectory" in APP


def test_history_is_receipted_and_current_build_is_exposed():
    assert APP.count("settlingRobustness: buildSettlingMaterialResponseHistory(leapHistory)") == 2
    assert "Build 290 · retained-leap settling robustness" in README
    assert 'buildId: "20260828-298"' in APP
    assert 'app.js?v=20260828-298' in HTML


if __name__ == "__main__":
    test_history_map_is_visible_and_selects_the_exact_leap()
    test_history_never_mixes_units_or_relabels_sequence_as_time()
    test_history_is_receipted_and_current_build_is_exposed()
    print("settling response history contract passed")
