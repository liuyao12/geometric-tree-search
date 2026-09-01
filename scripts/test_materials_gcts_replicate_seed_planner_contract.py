#!/usr/bin/env python3
"""Portal contract for preparing a distinct target-free registered nucleus."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP / "app.js").read_text()
    outcome = (APP / "physics-protocol-outcome.js").read_text()
    styles = (APP / "style.css").read_text()
    html = (APP / "index.html").read_text()

    for needle in (
        'export const REPLICATE_SEED_MODE_IDS = Object.freeze([',
        'seedSelectionMode: baselineSeedSelectionMode === ablationSeedSelectionMode',
        'const seedRecords = comparable.map((session) => ({',
        'const recommendedSeedMode = seedModes.find((mode) => !mode.used)?.id || null;',
        'seedRecords, seedModes, recommendedSeedMode,',
        'more distinct target-free seed',
    ):
        assert needle in outcome, needle

    for needle in (
        'function prepareNextPhysicsProtocolReplicate(audit, campaign)',
        'function localFrontierSeedPreview(mode, rank, nuclei, poseVariant)',
        'function localFrontierPreviewCatalogue({ usedDigests = new Set()',
        'function initializeFirstExecutableFittedSeed({ usedDigests = new Set()',
        'function growthLaunchReadinessAudit()',
        'function renderGrowthLaunchReadiness()',
        'candidateGeometryInspected: false',
        'const preview = localFrontierSeedPreview(mode, rank, nuclei, poseVariant);',
        'growthSeedProtocol = "local-frontier";',
        'for (const nuclei of [1, 2, 4])',
        'for (const rank of [0, 1, 2, 3, 4, 5, 6, 7])',
        'for (const poseVariant of [0, 1, 2, 3, 4, 5])',
        'usedDigests.has(preview.digest) || seenDigests.has(preview.digest)',
        'replay.digestMatched && replay.liveFrontier > 0',
        'collision-or-closed-frontier',
        'The current experiment was restored',
        'physicsProtocolSelectedIds = new Set(experiment.baselineSelectedRecordIds);',
        'physicsProtocolAblatedRecordId = experiment.ablatedRecordId;',
        'physicsProtocolPairSessionId = newPhysicsProtocolPairSessionId();',
        'applyPhysicsProtocolArm(intervention, "baseline", physicsProtocolPairSessionId);',
        'Prepared unused executable target-free nucleus',
        'distinct-seed registered pairs',
        'target-free nucleus plan',
        'Same supplied specimen and intervention · scans fitted occurrence, 1/2/4 nuclei, and proper pose controls for an unused executable digest.',
    ):
        assert needle in source, needle

    assert 'independent registered pairs' not in source
    assert 'id="nucleationRankSelect"' in html
    assert 'id="nucleationPoseSelect"' in html
    assert 'id="growthLaunchReadiness"' in html
    assert 'id="growthLaunchFindSeed"' in html
    assert 'id="growthLaunchInspectClusters"' in html
    assert 'id="growthLaunchRetrainMarking"' in html
    assert 'Proper rotation E · 137° about [1 −3 2]' in html
    assert 'Rank 8 · alternate fitted occurrence' in html
    assert 'nucleationCandidateRank' in source
    assert 'requestedCandidateRank' in source and 'resolvedCandidateRank' in source
    assert '.notebook-physics-seed-planner' in styles
    assert '.growth-launch-readiness' in styles
    assert 'buildId: "20260901-411"' in source
    print("replicate seed planner contract: passed")


if __name__ == "__main__":
    main()
