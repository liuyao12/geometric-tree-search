#!/usr/bin/env python3
"""Static contract for the representative-first molecular GCTS gallery."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_representative_overview_is_default_and_complete_library_remains_available():
    for token in (
        'let molecularGalleryFilter = "representative"',
        '["representative", "Family overview"]',
        '["all", "All cover classes"]',
        'const representativeIndices = new Set()',
        '["molecule", "bridge", "gap", "residual"]',
        'representativeIndices.has(Number(card.dataset.clusterIndex))',
        'one representative per cover family',
        'full isometry library on demand',
    ):
        assert token in APP


def test_representative_filter_is_display_only_and_receipt_visible():
    for token in (
        'molecularGalleryFilter = family',
        'molecularCoverFocus = ["molecule", "bridge", "gap", "residual"].includes(family)',
        'galleryFilterAtReceipt: molecularGalleryFilter',
        'representativeGalleryChangesLearningOrRanking: false',
        'displayFocusUsedForRanking: false',
        'const retainedMolecularGalleryFilter = Number(index) === 0 ? "representative" : molecularGalleryFilter',
        'molecularGalleryFilter = retainedMolecularGalleryFilter',
    ):
        assert token in APP
    assert 'data-cluster-family-filter="representative"' in CSS
    assert "Build 399 · molecular-family GCTS overview" in README


if __name__ == "__main__":
    test_representative_overview_is_default_and_complete_library_remains_available()
    test_representative_filter_is_display_only_and_receipt_visible()
    print("molecular gallery overview contract passed")
