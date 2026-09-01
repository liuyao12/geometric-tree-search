"""Source-level regression for the browser ice-cluster gallery contract."""

from pathlib import Path


APP = Path(__file__).parents[1] / "apps" / "iqc-growth-live" / "app.js"
STYLE = Path(__file__).parents[1] / "apps" / "iqc-growth-live" / "style.css"


def test_ice_gallery_uses_molecular_and_center_free_polyhedral_views() -> None:
    source = APP.read_text(encoding="utf-8")
    style = STYLE.read_text(encoding="utf-8")

    assert 'from "./molecular-components.js?v=20260824-3"' in source
    assert 'molecularCover: "water"' not in source
    assert "function molecularComponentHypothesis(source)" in source
    assert "function discoveredWaterComponents(discovery)" in source
    assert "discoverFiniteMolecularComponents({" in source
    assert "function buildWaterClusterCover(source, molecularDiscovery)" in source
    assert "molecularDiscovery.components.forEach" in source
    assert "if (learnedCover?.molecular) return learnMolecularOverlapGrammar(source)" in source
    assert 'materialLabelUsed: discovery.materialLabelUsed' in source
    assert 'expectedFormulaUsed: discovery.expectedFormulaUsed' in source
    assert 'label: `${waterLabel} molecule`' in source
    assert 'label: "hydrogen-bond bridge"' in source
    assert 'label: "six-water ring void"' in source
    assert "customVectors: centeredPeriodicSupport(source, waterSupport)" in source
    assert "customVectors: centeredPeriodicSupport(source, bridgeSupport)" in source
    assert "customVectors: unwrappedRingSupport(source, waters" in source
    assert "ring: ring.slice(), ringWaterIndices: true" in source
    assert 'cluster.visualKind === "ring"' in source
    assert "[index, (index + 1) % sites.length, \"ring\"]" in source
    assert "function waterBridgePolyhedron(sites)" in source
    assert "function addSettledDiscoverySurfaces(placements, color, opacity)" in source
    assert "topology.faces.flatMap(triangulateDiscoveryFace)" in source
    assert "side: THREE.DoubleSide" in source
    assert "settle into translucent molecular faces, connection polyhedra, and gap boundaries" in source
    assert "function clusterGallerySites(cluster)" in source
    assert "displayTopology.faces.length" in source
    assert "displayTopology.edges.length" in source
    assert "if (bridge) return bridge" in source
    assert "A generic hull is the wrong representation here" in source
    assert "[0, 1, 2], [3, paired[1], paired[0]]" in source
    assert "if (learnedCover?.occurrenceBased || learnedCover?.molecular) return;" in source
    assert "without inventing radial spokes" in source
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
    assert 'molecular.water ? molecular.waterLabel || "H₂O" : "Finite molecules"' in source
    assert "button.dataset.clusterLedgerFilter" in source
    assert "top: Math.max(0, selected.offsetTop - 8), left: 0" in source
    assert "clusterGallery.scrollTop = 0" in source
    assert "clusterGallery.scrollLeft = 0" in source
    assert "data-cluster-family-filter" in source
    assert ".cluster-cover-ledger" in style
    assert "const rows = document.createDocumentFragment()" in source
    assert "rows.append(toolbar)" in source
    assert "grid-template-columns: minmax(0,1fr)" in style
    assert '["molecule", learnedCover.molecular.water ? `${learnedCover.molecular.waterLabel || "H₂O"} molecules` : "Molecules"]' in source
    assert '["bridge", "Bridge polyhedra"]' in source
    assert '["gap", "Gap boundaries"]' in source
    assert "no classes merged" in source
    assert "card.dataset.clusterFamily = clusterGalleryFamily(cluster)" in source
    assert "card.dataset.isometrySignature = cluster.classSignature" in source
    assert "supportSites" in source
    assert "clusterCoverRole(cluster)" in source
    assert "moleculeClasses: 1" in source
    assert "observedMetricConformers: molecularConformers.length" in source
    assert "galleryTypes.filter((type) => type.familyType === 1).length" in source
    assert "galleryTypes.filter((type) => type.familyType === 2).length" in source
    assert "if (learnedCover.galleryTypes) return learnedCover.galleryTypes" in source
    assert "markingPrototypeTypes().forEach((cluster, clusterIndex)" in source
    assert "return learnedCover?.occurrenceBased || learnedCover?.molecular ? learnedCover.types" in source
    assert "candidate species-resolved bonds and intermolecular connections are proposed, rejected, and replaced" in source
    assert "Each learned cover class now receives its own rotating 3D card" in source
    assert "metric conformers as pose subtypes beneath one topological atom-cover class" in source
    assert "cluster-gallery-inspector" in source
    assert "literal terminal · never promoted" in source
    assert "markingPrototypeTypes().forEach((_, cluster)" in source
    assert "sectionModel.sampleLabels" in source
    assert 'const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v5"' in source
    assert "marking.vocabularyKey === vocabularyKey" in source
    assert 'hierarchy: [1, 8, "pose domains"]' in source
    assert 'gate: "pass anchor · molecular growth open"' in source
    assert 'gate: "progress · cross-polytype blind transfer"' in source
    assert "16/16 and then 8/8 correct unseen oxygen anchors" in source
    assert "Bernal–Fowler ice rules" in source
    assert "stationary, and exponential ice growth therefore stay red" in source
    assert 'from "./ice-molecular-anchor-growth.js?v=20260901-454"' in source
    assert "function initializeIceAnchorSearch()" in source
    assert "executeIceMolecularAnchorGrowth(" in source
    assert "if (iceAnchorTrace) {\n    performIceAnchorEvent()" in source
    assert 'oracleMetric.textContent = "0"' in source
    assert 'mutually exclusive ${iceAnchorTrace.moleculeLabel} orientation hypotheses remain symbolic' in source
    assert "Clusters² is disabled because no stationary promoted ice production has been certified" in source
    assert 'species === "H" || species === "D"' in source
    assert 'waterLabel: isotope === "D" ? "D₂O" : "H₂O"' in source
    assert 'molecularFixture: "ice-viii-cod-1566658"' in source
    assert "generateIceViiiObservation" in source


if __name__ == "__main__":
    test_ice_gallery_uses_molecular_and_center_free_polyhedral_views()
    print("ice gallery molecular/polyhedral contract: passed")
