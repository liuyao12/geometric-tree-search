#!/usr/bin/env python3
"""Static contract for the field-wise settling response matrix."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/settling-material-sensitivity.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_matrix_is_visible_interactive_and_current():
    for element_id in ("settlingResponseState", "settlingResponseMatrix", "settlingResponseDetail"):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function renderSettlingResponseMatrix" in APP
    assert "dataset.settlingResponseField" in APP
    assert 'settlingResponseMatrix.addEventListener("click"' in APP
    assert 'event.target.closest("button[data-settling-response-field]")' in APP
    assert ".settling-response-matrix" in CSS
    assert "Build 290 · retained-leap settling robustness" in README
    assert 'buildId: "20260828-300"' in APP


def test_rows_preserve_units_and_failed_arms_remain_rollbacks():
    assert 'unit: "angstrom"' in MODULE
    assert 'unit: "category"' in MODULE
    assert "within-field maximum absolute delta only; no cross-unit scalar" in MODULE
    assert 'return "rollback"' in APP
    assert "Categorical cells report a resolved class change only" in APP
    assert "No values from other units enter the scale" in APP


def test_matrix_is_downstream_and_cannot_modify_growth():
    assert "buildSettlingMaterialResponseMatrix(arms)" in APP
    for boundary in (
        "coordinatesEmbedded: false", "targetUsed: false", "usedForAdmission: false",
        "usedForRanking: false", "physicalPotentialUsed: false",
        "energyInferred: false", "physicalTimeModeled: false",
    ):
        assert boundary in MODULE


if __name__ == "__main__":
    test_matrix_is_visible_interactive_and_current()
    test_rows_preserve_units_and_failed_arms_remain_rollbacks()
    test_matrix_is_downstream_and_cannot_modify_growth()
    print("settling response matrix contract passed")
