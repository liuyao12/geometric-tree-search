"""Source-level regression for the browser ice-cluster gallery contract."""

from pathlib import Path


APP = Path(__file__).parents[1] / "apps" / "iqc-growth-live" / "app.js"


def test_ice_gallery_uses_molecular_and_center_free_polyhedral_views() -> None:
    source = APP.read_text(encoding="utf-8")

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
    assert "if (learnedCover?.molecular) return;" in source
    assert "would redraw those objects as radial first-shell spokes" in source
    assert "function learnMolecularSectionModel(source, config)" in source
    assert 'sampleKind: "molecular cover occurrence"' in source
    assert "function observedPortRules(cluster)" in source
    assert "overlapGrammar.reconstructionByOccurrence.forEach" in source
    assert "if (learnedCover?.molecular) {\n    clusterGalleryTypes().forEach" in source
    assert "markingPrototypeTypes().forEach((_, cluster)" in source
    assert "sectionModel.sampleLabels" in source
    assert 'const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v2"' in source
    assert "marking.vocabularyKey === vocabularyKey" in source
    assert 'hierarchy: [1, 8, "pose domains"]' in source
    assert 'gate: "pass anchor · molecular growth open"' in source
    assert 'gate: "progress · cross-polytype blind transfer"' in source
    assert "16/16 and then 8/8 correct unseen oxygen anchors" in source
    assert "Bernal–Fowler ice rules" in source
    assert "stationary, and exponential ice growth stay red" in source


if __name__ == "__main__":
    test_ice_gallery_uses_molecular_and_center_free_polyhedral_views()
    print("ice gallery molecular/polyhedral contract: passed")
