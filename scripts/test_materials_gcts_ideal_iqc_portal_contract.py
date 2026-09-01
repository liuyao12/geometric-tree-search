#!/usr/bin/env python3
"""Portal contract for the exact ideal-IQC browser control."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP_DIR / "app.js").read_text()
    html = (APP_DIR / "index.html").read_text()
    alias = (ROOT / "iqc-growth-live" / "index.html").read_text()
    readme = (APP_DIR / "README.md").read_text()
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text()

    for needle in (
        'import { IDEAL_IQC_BROWSER_FIXTURE }',
        'idealModelFixture: "icosahedral-6d-r9"',
        'name: "Ideal 6D icosahedral model set"',
        'function makeIdealIqcReferenceConfiguration()',
        'family: "ideal-icosahedral-6d-model-set"',
        '? "algorithmic model set"',
        'material.fixtureProvenance?.fixtureClass === "algorithmic"',
        'publishedFixtureHeading.textContent = algorithmic',
        'publishedFixtureArticle.hidden = !provenance.articleDoi',
        'Exact mathematical control, not experimental material data.',
        'geometryFixture: material.fixtureProvenance ?',
        'publishedModel: material.fixtureProvenance && material.fixtureProvenance.fixtureClass !== "algorithmic"',
        'buildId: "20260901-436"',
    ):
        assert needle in source, needle

    for document in (html, alias):
        assert 'id="publishedFixtureHeading"' in document
        assert 'id="publishedFixtureNote"' in document
        assert 'Ideal 6D IQC model set · Al/Cu/Fe colors' in document
        assert 'app.js?v=20260901-436' in document

    for document in (readme, benchmark):
        assert "507" in document
        assert "cut-and-project" in document
        assert "experimental" in document

    print("ideal IQC portal contract: passed")


if __name__ == "__main__":
    main()
