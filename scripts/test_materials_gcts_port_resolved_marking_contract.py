from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/cluster-marking-port-atlas.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_port_evidence_is_separate_from_representation_channels():
    assert "buildClusterMarkingPortAtlas" in APP
    assert "portObservations" in APP
    assert "supportOccurrenceFrame(source, occurrence.placement).invert()" in APP
    assert "channelAxes: axes.map((axis) => axis.toArray())" in APP
    assert "scalarDirectional" in ATLAS
    assert "atlas.sphericalFallbackUsed = false" in ATLAS


def test_renderer_uses_connection_lobes_without_spherical_fallback():
    start = APP.index("function drawClusterCardMarking(")
    end = APP.index("function drawClusterGallery(", start)
    renderer = APP[start:end]
    assert "atlas?.compatiblePorts" in renderer
    assert "atlas?.unsupportedSectors" in renderer
    assert "new THREE.Vector3(...record.direction)" in renderer
    assert "if (!compatible) context.setLineDash" in renderer
    assert "no directional port evidence · no spherical fallback" in renderer
    assert "context.arc(canvas.width / 2, canvas.height / 2, 54" not in renderer


def test_receipt_and_ui_preserve_the_claim_boundary():
    assert "portResolvedLevelSets" in APP
    assert "physicalPotential: sectionModel.portAtlas.physicalPotential" in APP
    assert "candidateGeometryChanged: sectionModel.portAtlas.candidateGeometryChanged" in APP
    assert "unsupported training sectors" in APP
    assert "no spherical fallback is invented" in HTML
    assert "Build 260 · port-resolved GCTS level sets" in README
    assert 'buildId: "20260827-271"' in APP
    assert "app.js?v=20260827-271" in HTML


if __name__ == "__main__":
    test_port_evidence_is_separate_from_representation_channels()
    test_renderer_uses_connection_lobes_without_spherical_fallback()
    test_receipt_and_ui_preserve_the_claim_boundary()
    print("Port-resolved GCTS marking contract: passed")
