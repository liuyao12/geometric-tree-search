"""Source-level contract for the four-stage geometry/marking/search controls."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text(encoding="utf-8")
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text(encoding="utf-8")


def test_clustering_exposes_geometry_pose_and_derived_channel_rank() -> None:
    for identifier in (
        "geometryModeSelect", "translationSupport", "rotationSupport",
        "channelRankSupport", "poseAtlas",
    ):
        assert f'id="{identifier}"' in HTML
    assert "function resolvedGeometryMode()" in APP
    assert "function learnOrientationAtlas()" in APP
    assert "function clusterPosePortRank(cluster)" in APP
    assert "function automaticMarkingChannels()" in APP
    assert "poseAtlasEntryStatus(entry)" in APP


def test_marking_configuration_and_library_are_executable_controls() -> None:
    for identifier in (
        "markingChannelsSelect", "markingReachSelect",
        "markingRepresentationSelect", "saveMarkingButton",
        "markingLibrarySelect", "markingSearchModeSelect",
        "trainVariantButton",
    ):
        assert f'id="{identifier}"' in HTML
    assert "function restartMarkingTraining()" in APP
    assert "function freezeCurrentMarking()" in APP
    assert "function markingVocabularyKey()" in APP
    assert 'const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v2"' in APP
    assert "Library entries are enabled only when the colored cluster, pose, and port vocabulary matches exactly" in HTML


def test_growth_can_disable_promotion_without_changing_candidate_geometry() -> None:
    assert 'id="primitiveGrowthButton"' in HTML
    assert 'id="hierarchicalGrowthButton"' in HTML
    assert "hierarchyEnabled = false" in APP
    assert "hierarchyEnabled = true" in APP
    assert "const continuationRules = hierarchyEnabled || placement.depth === 0" in APP
    assert "same exact candidate geometry" in HTML


def test_growth_exposes_serial_and_commuting_tree_schedules() -> None:
    assert 'id="growthSchedulingSelect"' in HTML
    assert '<option value="commuting" selected>Commuting frontier · simultaneous antichain</option>' in HTML
    assert '<option value="serial">Serial best-first · one branch decision</option>' in HTML
    assert 'growthScheduling === "serial"' in APP
    assert 'candidateGeometryChangedByScheduling: false' in APP
    assert 'maximal pairwise-compatible antichain; every accepted placement is valid in every permutation' in APP


def test_growth_exposes_candidate_identical_geometric_strain_ablation() -> None:
    assert 'id="geometryPreferenceSelect"' in HTML
    assert 'id="strainWeightSelect"' in HTML
    assert '<option value="none">Off · marking/action ordering only</option>' in HTML
    assert "function activeGeometricStrainWeight()" in APP
    assert 'geometryPreference === "strain" ? geometricStrainWeight : 0' in APP
    assert "- activeGeometricStrainWeight() * evaluation.geometricStrain.total" in APP
    assert "target-blind soft ordering of the unchanged exact candidate set" in APP
    assert 'id="compositionPreferenceSelect"' in HTML
    assert "function activeCompositionBalanceWeight()" in APP
    assert "- activeCompositionBalanceWeight() * evaluation.compositionBalance.scaledDelta" in APP


if __name__ == "__main__":
    test_clustering_exposes_geometry_pose_and_derived_channel_rank()
    test_marking_configuration_and_library_are_executable_controls()
    test_growth_can_disable_promotion_without_changing_candidate_geometry()
    test_growth_exposes_serial_and_commuting_tree_schedules()
    test_growth_exposes_candidate_identical_geometric_strain_ablation()
    print("stage option contract: passed")
