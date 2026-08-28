"""Static contract for rendering the same transported Uij used by growth."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_transported_covariance_reaches_candidate_cluster_and_committed_glyphs() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(
        encoding="utf-8")

    assert "symmetricTensorEigenSystem" in source
    assert "copyPlacedDisplacementTensor(atom, site)" in source
    assert "atom.thermalSigmaAxesA = eigen.sigmaAxesA.slice()" in source
    assert "atom.thermalAxesCartesian = eigen.axes.map" in source
    assert "candidateDisplacementSites" in source
    assert "candidateDisplacementMaterial" in source
    assert "transportedCandidateCovariance" in source
    assert "drawClusterCardDisplacementEllipses" in source
    assert "clusterGalleryProjectsRotatedTwoSigmaEllipses: true" in source
    assert "placedEllipsoidGlyphSites" in source
    assert "currentCandidateEllipsoidGlyphSites" in source
    assert 'id="displacementToggle"' in html
    assert 'id="displacementToggleLabel"' in html
    assert 'buildId: "20260827-271"' in source
    assert 'app.js?v=20260827-271' in html
    assert "Build 249 closes the visual half of that covariance lineage" in readme
    assert "Transported displacement ellipsoids (Build 249)" in benchmark
    assert "not atomic surfaces" in readme


if __name__ == "__main__":
    test_transported_covariance_reaches_candidate_cluster_and_committed_glyphs()
    print("transported displacement glyph integration contract: passed")
