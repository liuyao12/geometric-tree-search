"""Source contract for the bounded, coordinate-free experiment notebook."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_experiment_notebook_compares_receipt_summaries_without_coordinates() -> None:
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")

    for element_id in ("saveNotebookButton", "clearNotebookButton", "notebookState", "notebookEntries", "notebookComparison"):
        assert f'id="{element_id}"' in html
    receipt_section = html[html.index('class="receipt-section"'):html.index('class="legend-section"')]
    assert 'type="text"' not in receipt_section

    assert 'const EXPERIMENT_NOTEBOOK_STORAGE = "gcts-experiment-notebook-v1"' in source
    assert "const MAX_EXPERIMENT_NOTEBOOK_ENTRIES = 8" in source
    assert "function experimentNotebookSummary(receipt)" in source
    assert "function persistExperimentNotebook()" in source
    assert "function restoreExperimentNotebook()" in source
    assert "function renderExperimentNotebook()" in source
    assert "async function saveCurrentExperimentNotebookEntry()" in source
    assert "entry.experimentStateSha256 === receipt.experimentStateSha256" in source
    assert "This exact experiment state is already saved" in source
    assert "if (selectedNotebookEntryIds.length >= 2) selectedNotebookEntryIds.shift()" in source
    assert "coordinatesEmbedded: false" in source
    assert "coordinate-free summary" in source

    for key in ("material", "input", "geometry", "cover", "marking", "search", "output", "decisions", "classification", "claim boundary"):
        assert f'["{key}"' in source or f'"{key}":' in source

    assert "if (!notebookClearArmed)" in source
    assert 'clearNotebookButton.textContent = "Confirm clear"' in source
    assert "localStorage.removeItem(EXPERIMENT_NOTEBOOK_STORAGE)" in source
    assert ".notebook-entries" in css
    assert ".notebook-comparison" in css
    assert "experiment notebook" in readme
    assert "never stores atom" in readme


if __name__ == "__main__":
    test_experiment_notebook_compares_receipt_summaries_without_coordinates()
    print("coordinate-free experiment notebook contract: passed")
