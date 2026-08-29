#!/usr/bin/env python3
"""Static contract for the live molecule → connection → void cover ribbon."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_molecular_cover_ribbon_contract():
    for token in (
        'id="molecularCoverRibbon"',
        'id="molecularCoverTitle"',
        'id="molecularCoverState"',
        'id="molecularCoverFlow"',
        'id="molecularCoverBoundary"',
    ):
        assert token in HTML
    for token in (
        "function renderMolecularCoverRibbon()",
        "learnedCover?.molecular",
        "clusterDiscoveryState()",
        'countFamily("molecule")',
        'countFamily("bridge")',
        'countFamily("gap")',
        'let molecularCoverFocus = "all"',
        'edge.families?.has(molecularCoverFocus)',
        'article.setAttribute("aria-pressed"',
        'molecularCoverFocus = record.focus',
        "buildClusterOverlay();",
        "const inheritedFamily = learnedCover.molecular",
        "if (learnedCover.molecular) molecularCoverFocus = family",
        'const retainedMolecularCoverFocus = Number(index) === 0 ? "all" : molecularCoverFocus',
        "molecularCoverFocus = retainedMolecularCoverFocus",
        "inheritedFilter.click()",
        "cover focus",
        "function prototypeCoverFamily(type)",
        "function coverLineageForRule(rule)",
        "displayFocusUsedForRanking: false",
        "coverLineage: coverLineageForRule(rule)",
        "coverLineage: coverLineageForRule(candidate.rule)",
        'name: "cover lineage"',
        "specialized frozen primitive molecular port",
        "never ranked",
        "function coverLineageReceiptEvidence()",
        "acceptedGenericPlacementSha256",
        "function renderGrowthLineageMap()",
        "growthCoverLineageGroups()",
        "current cover focus is display-only",
        "function markingProvenanceForCandidate(candidate)",
        "function specializedIceMarkingProvenance()",
        "markingProvenance: markingProvenanceForCandidate(candidate)",
        '"frozen marking"',
        '"capacity / reach"',
        '"section score"',
        "const sampleFamilies = sampleLabels.map(prototypeCoverFamily)",
        "const familyLossesFor",
        "familyLosses: familyLossesFor(initial)",
        "familyLosses: familyLossesFor(coefficients)",
        "focused occurrences",
        "unchanged global fit",
        "molecular.moleculeClasses",
        "molecular.connectionClasses",
        "molecular.voidClasses",
        "No radial atom-centred shell is substituted",
        "renderMolecularCoverRibbon();",
    ):
        assert token in APP
    assert APP.index("updateProcessTimeline();") < APP.index("renderMolecularCoverRibbon();", APP.index("function updateUI()"))
    assert ".molecular-cover-ribbon" in CSS
    assert ".molecular-cover-flow button.connection" in CSS
    assert ".molecular-cover-flow button.void" in CSS
    assert ".molecular-cover-flow button.coverage" in CSS
    assert ".molecular-cover-flow button.active" in CSS
    assert ".growth-lineage-map" in CSS
    assert 'id="growthLineageMap"' in HTML
    assert 'buildId: "20260828-315"' in APP
    assert 'app.js?v=20260828-315' in HTML


if __name__ == "__main__":
    test_molecular_cover_ribbon_contract()
    print("molecular cover ribbon contract passed")
