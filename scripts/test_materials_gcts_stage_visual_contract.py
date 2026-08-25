"""Source regression for distinct clustering and GCTS-learning visual stages."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live" / "app.js"
STYLE = ROOT / "apps" / "iqc-growth-live" / "style.css"
HTML = ROOT / "apps" / "iqc-growth-live" / "index.html"


def test_clustering_is_full_scene_and_marking_uses_per_cluster_scenes() -> None:
    source = APP.read_text(encoding="utf-8")
    style = STYLE.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")

    # Cluster identification is an explicit, target-blind graph-discovery trace.
    assert "function buildClusterDiscoveryTrace()" in source
    assert "function clusterDiscoveryState(progress = clusterDiscoveryProgress)" in source
    assert "function buildClusterDiscoveryOverlay()" in source
    assert "tentative: [], rejected: [], settled: []" in source
    assert "targetUsed: false" in source
    assert "if (pipelineStage === 1) {\n    if (clusterDiscoveryProgress" in source
    assert "if (pipelineStage === 1 || pipelineStage === 3)" in source
    assert '"full configuration · tentative → rejected → settled supports"' in source
    assert "pipelineStage !== 1" in source  # generic proximity bonds do not obscure discovery edges
    assert "Locally inconsistent or non-recurrent edges flash red before removal" in source
    assert 'legendHeading.textContent = "Clustering decisions"' in source

    # The isolated scenes belong to GCTS training, not cluster identification.
    assert "clusterGallery.hidden = pipelineStage !== 3" in source
    assert 'viewport.classList.toggle("cluster-gallery-mode", pipelineStage === 3)' in source
    assert "if (pipelineStage !== 3 || clusterGallery.hidden) return" in source
    assert "function drawClusterCardMarking(" in source
    assert "function updateClusterGalleryTrainingReadouts()" in source
    assert "updateClusterGalleryTrainingReadouts();" in source
    assert "random local connection contours morph" in source
    assert ".cluster-training-readout" in style
    assert "One rotating three-dimensional marking scene per learned cluster type" in html


if __name__ == "__main__":
    test_clustering_is_full_scene_and_marking_uses_per_cluster_scenes()
    print("stage visual contract: passed")
