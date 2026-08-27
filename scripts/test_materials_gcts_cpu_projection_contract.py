from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_cpu_fallback_projects_the_live_scene_graph():
    start = APP.index("function fallbackViewportRenderer()")
    end = APP.index("function materialsViewportRenderer()", start)
    fallback = APP[start:end]

    assert 'aria-label", "CPU-projected materials geometry' in fallback
    assert "scene.traverseVisible" in fallback
    assert "object.isInstancedMesh" in fallback
    assert "object.isPoints" in fallback
    assert "object.isLine" in fallback
    assert "camera.matrixWorldInverse" in fallback
    assert "worldPoint.project(camera)" in fallback
    assert "CPU-PROJECTED GEOMETRY · DRAG TO ORBIT" in fallback
    assert "WebGL not required" in fallback
    assert "3D VIEW UNAVAILABLE" not in fallback


def test_projection_is_bounded_display_work_not_scientific_truncation():
    start = APP.index("function fallbackViewportRenderer()")
    end = APP.index("function materialsViewportRenderer()", start)
    fallback = APP[start:end]

    assert "let dotBudget = 3200" in fallback
    assert "let segmentBudget = 4200" in fallback
    assert "now - lastDraw < 34" in fallback
    assert "display fallback" in README
    assert "never\ntruncate the scientific state" in DOC


def test_build_211_release_identity_is_coherent():
    assert 'buildId: "20260827-258"' in APP
    assert 'app.js?v=20260827-258' in HTML
    assert "Build 209" in README
    assert "Build 209" in DOC


if __name__ == "__main__":
    test_cpu_fallback_projects_the_live_scene_graph()
    test_projection_is_bounded_display_work_not_scientific_truncation()
    test_build_211_release_identity_is_coherent()
    print("CPU projection contract: passed")
