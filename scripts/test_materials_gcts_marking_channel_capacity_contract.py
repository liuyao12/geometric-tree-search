from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def function_body(name: str, next_name: str) -> str:
    start = APP.index(f"function {name}(")
    end = APP.index(f"function {next_name}(", start)
    return APP[start:end]


def test_selected_channel_count_is_the_actual_model_dimension():
    atomic = function_body("learnSectionModel", "learnMolecularSectionModel")
    molecular = function_body("learnMolecularSectionModel", "selectedMarking")

    assert "const axes = markingChannelAxes(config.channels);" in atomic
    assert "const axes = markingChannelAxes(config.channels);" in molecular
    assert "const axes = BALANCE_DIRECTIONS;" not in atomic
    assert "const axes = BALANCE_DIRECTIONS;" not in molecular
    assert "new Array(axes.length).fill(0)" in atomic
    assert "activeChannelsByPrototype" in atomic
    assert "activeChannelsByPrototype" in molecular


def test_scalar_and_multichannel_bases_are_intrinsic_and_bounded():
    axes = function_body("markingChannelAxes", "markingBasisFeatures")
    basis = function_body("markingBasisFeatures", "fallbackViewportRenderer")

    assert "clamp(Math.round(Number(channelCount) || 1), 1, 12)" in axes
    assert "if (count === 1) return [new THREE.Vector3()]" in axes
    assert "goldenAngle" in axes
    assert "return [radial]" in basis
    assert "direction.dot(axis)" in basis
    assert "laboratory axis" in axes


def test_pose_port_rank_masks_and_saved_audits_are_explicit():
    assert "Math.min(axes.length, recommendedChannelsForCluster(cluster))" in APP
    assert "markingChannelAllocationLabel" in APP
    assert "inactive coefficients remain exactly zero" in APP
    assert 'MARKING_LIBRARY_STORAGE = "gcts-marking-library-v4"' in APP
    assert "MARKING_VOCABULARY_SCHEMA = 4" in APP
    assert "channelBasis: sectionModel.axes.map" in APP
    assert "activeChannelsByPrototype: sectionModel.activeChannelsByPrototype.slice()" in APP


def test_build_210_release_identity_is_coherent():
    assert 'buildId: "20260827-228"' in APP
    assert 'app.js?v=20260827-228' in HTML
    assert "Build 210" in README
    assert "Build 210" in DOC


if __name__ == "__main__":
    test_selected_channel_count_is_the_actual_model_dimension()
    test_scalar_and_multichannel_bases_are_intrinsic_and_bounded()
    test_pose_port_rank_masks_and_saved_audits_are_explicit()
    test_build_210_release_identity_is_coherent()
    print("Marking channel-capacity contract: passed")
