from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
NORMALIZATION = (ROOT / "apps/iqc-growth-live/score-normalization.mjs").read_text()
PHYSICS = (ROOT / "apps/iqc-growth-live/physics-compression-map.js").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-action-barrier.mjs").read_text()


def test_exact_frozen_frontier_handoff_is_visible_and_interactive():
    for control_id in (
        "actionBarrierFreeze", "actionBarrierDownload", "actionBarrierResponse",
        "actionBarrierWeight", "actionBarrierResume", "actionBarrierCancel",
        "actionBarrierCheckpointState", "actionBarrierSummary",
    ):
        assert f'id="{control_id}"' in HTML
    assert "External action barriers" in HTML
    assert "cannot create a pose" in HTML
    assert ".action-barrier-checkpoint" in CSS
    for event in (
        "freezeExternalActionBarrierFrontier", "downloadExternalActionBarrierRequest",
        "validateExternalActionBarrierFile", "refreshExternalActionBarrierScores",
        "releaseExternalActionBarrierCheckpoint",
    ):
        assert event in APP


def test_response_is_bound_to_the_complete_unchanged_action_batch():
    for phrase in (
        "candidateBatchSha256", "initialStructureSha256", "candidateDigestSha256",
        "candidate IDs must be unique", "exactly ${expected.candidates.length} candidate records",
        "duplicate barrier record", "omitted one or more frozen candidates",
        "candidateSetChanged !== false", "hardAdmissionChanged !== false",
    ):
        assert phrase in MODULE
    assert "candidateSetTargetUsed === true" in MODULE
    assert "targetCoordinatesEmbedded: false" in MODULE
    assert "geometricScoresUsedAsEnergyLabels: false" in MODULE
    assert "searchStepsUsedAsPhysicalTime: false" in MODULE


def test_barrier_is_one_bounded_soft_ledger_term_not_geometry_or_clock():
    assert 'scoreTerm("action-barrier"' in APP
    assert '"action-barrier": spec(' in NORMALIZATION
    assert '"action-barrier": "action-barrier-ranking"' in NORMALIZATION
    assert '"action-barrier-ranking"' in PHYSICS
    assert "externalActionBarrierWeight > 0" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "usedAsPotential: false" in APP
    assert "physicalTimeInferred: false" in APP
    assert "temperature and prefactor evidence" in APP


def test_checkpoint_is_consumed_only_at_the_existing_commit_boundary():
    assert "checkpointPausedBeforeCommit: true" in APP
    assert "validate or release the frozen action-barrier checkpoint before committing" in APP
    assert "actionBarrierCheckpoint: actionBarrierReceipt" in APP
    assert "externalActionBarrierCheckpoint = null" in APP
    assert 'status: "consumed"' in APP
    assert "candidateSetFrozenBeforeEvaluation: true" in APP


if __name__ == "__main__":
    test_exact_frozen_frontier_handoff_is_visible_and_interactive()
    test_response_is_bound_to_the_complete_unchanged_action_batch()
    test_barrier_is_one_bounded_soft_ledger_term_not_geometry_or_clock()
    test_checkpoint_is_consumed_only_at_the_existing_commit_boundary()
    print("external action barrier portal contract: passed")
