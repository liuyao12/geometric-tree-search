from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_live_marking_disagreement_can_be_registered_as_two_arms():
    for identifier in (
        "markingInterventionRegister",
        "markingInterventionBaseline",
        "markingInterventionAlternative",
        "markingInterventionClear",
    ):
        assert f'id="{identifier}"' in HTML
    assert "function registerMarkingComparisonExperiment(snapshot, audit, selected)" in APP
    assert "function configureMarkingComparisonArm(arm)" in APP
    assert "function renderMarkingComparisonExperiment(snapshot, audit = null, selected = null)" in APP
    assert ".marking-intervention" in STYLE


def test_registration_freezes_artifacts_frontier_and_non_marking_controls():
    assert "function frozenMarkingArtifactDigest(marking)" in APP
    assert "baselineDigest = frozenMarkingArtifactDigest(baseline)" in APP
    assert "alternativeDigest = frozenMarkingArtifactDigest(alternative)" in APP
    assert "sourceCandidateSetDigest: audit.candidateSetDigest" in APP
    assert "sourceHardAdmittedSetDigest: audit.hardAdmittedCandidateSetDigest" in APP
    assert "materialConsequenceDigest" in APP
    assert "growthSettingsJson: JSON.stringify(currentGrowthProtocolSettings())" in APP
    assert "registrationDigest = notebookStringHash" in APP


def test_arm_activation_fails_closed_resets_and_never_executes():
    assert "frozenMarkingArtifactDigest(entry) === record.artifactDigest" in APP
    assert "artifact is unavailable or changed; experiment failed closed" in APP
    assert "enterPipelineStage(0);" in APP
    assert "no growth executed" in APP
    assert "activeMarkingStillMatchesArm" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "targetUsedToRegister: false" in APP
    assert "autoExecuted: false" in APP


def test_intervention_is_receipted_and_release_is_consistent():
    assert "markingComparisonExperiment: markingComparisonReceipt()" in APP
    assert 'buildId: "20260827-232"' in APP
    assert 'app.js?v=20260827-232' in HTML
    assert "Build 216" in README
    assert "Build 216" in DOC


if __name__ == "__main__":
    test_live_marking_disagreement_can_be_registered_as_two_arms()
    test_registration_freezes_artifacts_frontier_and_non_marking_controls()
    test_arm_activation_fails_closed_resets_and_never_executes()
    test_intervention_is_receipted_and_release_is_consistent()
    print("marking intervention contract passed")
