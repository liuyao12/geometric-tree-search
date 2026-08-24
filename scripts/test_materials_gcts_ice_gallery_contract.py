"""Source-level regression for the browser ice-cluster gallery contract."""

from pathlib import Path


APP = Path(__file__).parents[1] / "apps" / "iqc-growth-live" / "app.js"
STYLE = Path(__file__).parents[1] / "apps" / "iqc-growth-live" / "style.css"


def test_ice_gallery_uses_molecular_and_center_free_polyhedral_views() -> None:
    source = APP.read_text(encoding="utf-8")
    style = STYLE.read_text(encoding="utf-8")

    assert 'from "./molecular-components.js?v=20260824-2"' in source
    assert 'molecularCover: "water"' not in source
    assert "function molecularComponentHypothesis(source)" in source
    assert "function discoveredWaterComponents(discovery)" in source
    assert "discoverFiniteMolecularComponents({" in source
    assert "function buildWaterClusterCover(source, molecularDiscovery)" in source
    assert "molecularDiscovery.components.forEach" in source
    assert "if (learnedCover?.molecular) return learnMolecularOverlapGrammar(source)" in source
    assert 'materialLabelUsed: discovery.materialLabelUsed' in source
    assert 'expectedFormulaUsed: discovery.expectedFormulaUsed' in source
    assert 'label: "H₂O molecule"' in source
    assert 'label: "hydrogen-bond bridge"' in source
    assert 'label: "six-water ring void"' in source
    assert "customVectors: centeredPeriodicSupport(source, waterSupport)" in source
    assert "customVectors: centeredPeriodicSupport(source, bridgeSupport)" in source
    assert "customVectors: unwrappedRingSupport(source, waters" in source
    assert 'cluster.visualKind === "ring"' in source
    assert "[index, (index + 1) % sites.length, \"ring\"]" in source
    assert "function waterBridgePolyhedron(sites)" in source
    assert "if (bridge) return bridge" in source
    assert "A generic hull is the wrong representation here" in source
    assert "[0, 1, 2], [3, paired[1], paired[0]]" in source
    assert "if (learnedCover?.occurrenceBased || learnedCover?.molecular) return;" in source
    assert "would turn molecular or irregular supports back into radial spokes" in source
    assert "function learnMolecularSectionModel(source, config)" in source
    assert 'sampleKind: learnedCover.molecular ? "molecular cover occurrence" : "irregular support occurrence"' in source
    assert "function observedPortRules(cluster)" in source
    assert "overlapGrammar.reconstructionByOccurrence.forEach" in source
    assert "function coloredPeriodicSupportSignature(source, support)" in source
    assert "function molecularIsometryGallery(source, families, familyTypes)" in source
    assert "function buildMolecularGalleryToolbar(types)" in source
    assert "function buildMolecularCoverLedger(types)" in source
    assert 'eyebrow: "atomic cover"' in source
    assert 'eyebrow: "connection cover"' in source
    assert 'eyebrow: "void-boundary cover"' in source
    assert 'molecular.water ? "H₂O" : "Finite molecules"' in source
    assert "button.dataset.clusterLedgerFilter" in source
    assert "data-cluster-family-filter" in source
    assert ".cluster-cover-ledger" in style
    assert '["molecule", learnedCover.molecular.water ? "H₂O molecules" : "Molecules"]' in source
    assert '["bridge", "Bridge polyhedra"]' in source
    assert '["gap", "Gap boundaries"]' in source
    assert "no classes merged" in source
    assert "card.dataset.clusterFamily = clusterGalleryFamily(cluster)" in source
    assert "card.dataset.isometrySignature = cluster.classSignature" in source
    assert "supportSites" in source
    assert "clusterCoverRole(cluster)" in source
    assert "galleryTypes.filter((type) => type.familyType === 0).length" in source
    assert "galleryTypes.filter((type) => type.familyType === 1).length" in source
    assert "galleryTypes.filter((type) => type.familyType === 2).length" in source
    assert "if (learnedCover.galleryTypes) return learnedCover.galleryTypes" in source
    assert "markingPrototypeTypes().forEach((cluster, clusterIndex)" in source
    assert "return learnedCover?.occurrenceBased || learnedCover?.molecular ? learnedCover.types" in source
    assert "colored metric-isometry classes as independent rotating scenes" in source
    assert "cluster-gallery-inspector" in source
    assert "literal terminal · never promoted" in source
    assert "markingPrototypeTypes().forEach((_, cluster)" in source
    assert "sectionModel.sampleLabels" in source
    assert 'const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v3"' in source
    assert "marking.vocabularyKey === vocabularyKey" in source
    assert 'hierarchy: [1, 8, "pose domains"]' in source
    assert 'gate: "pass anchor · molecular growth open"' in source
    assert 'gate: "progress · cross-polytype blind transfer"' in source
    assert "16/16 and then 8/8 correct unseen oxygen anchors" in source
    assert "Bernal–Fowler ice rules" in source
    assert "stationary, and exponential ice growth stay red" in source
    assert 'from "./ice-molecular-anchor-growth.js"' in source
    assert "function initializeIceAnchorSearch()" in source
    assert "executeIceMolecularAnchorGrowth(" in source
    assert "if (iceAnchorTrace) {\n    performIceAnchorEvent()" in source
    assert 'oracleMetric.textContent = "0"' in source
    assert "mutually exclusive H₂O orientation hypotheses remain symbolic" in source
    assert "Clusters² is disabled because no stationary promoted ice production has been certified" in source


if __name__ == "__main__":
    test_ice_gallery_uses_molecular_and_center_free_polyhedral_views()
    print("ice gallery molecular/polyhedral contract: passed")
