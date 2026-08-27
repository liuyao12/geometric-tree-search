#!/usr/bin/env python3
"""Static contract for the saved marking-to-cover-family comparison."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()


def test_notebook_retains_coordinate_free_lineage_provenance():
    required = (
        "function notebookCoverLineageSummary(receipt)",
        "acceptedGenericPlacementSha256: audit.acceptedGenericPlacementSha256 || null",
        "transitionGroups,",
        "markingGroups:",
        "coordinatesEmbedded: false",
        "coverLineage: notebookCoverLineageSummary(receipt)",
    )
    for phrase in required:
        assert phrase in APP


def test_pair_comparison_is_fail_closed_for_causal_attribution():
    required = (
        "function notebookMarkingLineageComparison(first, second)",
        "registered?.responseComparable === true",
        "Identical input, non-marking controls, first hard-admitted frontier, and registered horizon",
        "Without the registered matched-frontier/horizon gate",
        "target-free provenance",
        "physicalMechanismInferred: audit.physicalMechanismInferred",
    )
    for phrase in required:
        assert phrase in APP


def test_notebook_renders_marking_to_family_pathways():
    required_app = (
        "function renderNotebookMarkingLineageRun(entry, record, runLabel)",
        "marking  →  compatible cover-family attachments  →  emitted sites",
        "function renderNotebookMarkingLineageComparison(first, second)",
        "notebookComparison.append(renderNotebookMarkingLineageComparison(selected[0], selected[1]))",
    )
    for phrase in required_app:
        assert phrase in APP
    for selector in (
        ".notebook-lineage-comparison",
        ".notebook-lineage-runs",
        ".notebook-lineage-marking",
        ".notebook-lineage-transitions",
        ".notebook-lineage-summary",
    ):
        assert selector in CSS
    assert 'id="notebookComparison"' in HTML


def test_build_230_assets_are_paired():
    assert 'buildId: "20260827-243"' in APP
    assert 'app.js?v=20260827-243' in HTML
    assert 'style.css?v=20260827-243' in HTML


if __name__ == "__main__":
    test_notebook_retains_coordinate_free_lineage_provenance()
    test_pair_comparison_is_fail_closed_for_causal_attribution()
    test_notebook_renders_marking_to_family_pathways()
    test_build_230_assets_are_paired()
    print("marking-lineage notebook contract passed")
