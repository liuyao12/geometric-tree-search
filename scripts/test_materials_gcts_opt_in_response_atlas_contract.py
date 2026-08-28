#!/usr/bin/env python3
"""Static contract for opt-in, state-keyed creation-response analysis."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
WORKER = (ROOT / "apps/iqc-growth-live/creation-response-worker.js").read_text()


def test_response_atlas_is_an_explicit_notebook_action():
    assert 'id="computeNotebookResponseButton"' in HTML
    assert 'id="notebookResponseAnalysisStatus"' in HTML
    assert 'computeNotebookResponseButton.addEventListener("click", computeNotebookResponseAnalysis)' in APP
    assert 'computeNotebookResponseButton.textContent = "Computing response atlas…"' in APP


def test_heavy_models_run_off_the_rendering_thread():
    assert 'new Worker(new URL("./creation-response-worker.js?v=20260827-1"' in APP
    assert "runInWorker: true" in APP
    assert "running off the rendering thread" in APP
    for phrase in (
        "buildCreationResponseAssociation(records)",
        "blockedCreationResponseValidation(records, outcomeId",
        "blockedCreationResponseSurrogate(records, outcomeId",
        "creationResponseHorizonSweep(records, outcomeId",
        'self.postMessage({ type: "result"',
    ):
        assert phrase in WORKER


def test_cache_is_keyed_to_exact_growth_state_and_invalidated():
    required = (
        "async function creationResponseStateSha256()",
        'explicitSitesSha256: await structureDigest(atoms, "scene")',
        "placementLedger,",
        "leapEventCount,",
        "structuralRelaxationAccepted,",
        "async function stateMatchedCreationResponseEvidence",
        "currentStateSha256 === cachedCreationResponseStateSha256",
        'invalidateCreationResponseEvidenceCache("new specimen or reset state")',
        'invalidateCreationResponseEvidenceCache("a new structural leap changed the response state")',
    )
    for phrase in required:
        assert phrase in APP


def test_bounded_snapshot_reuses_only_matching_evidence():
    required = (
        "const creationResponseState = searchVisible ? await creationResponseStateSha256() : null",
        "await stateMatchedCreationResponseEvidence(creationResponseState)",
        "creationResponseEvidence: cachedCreationResponse",
        "creationResponseCacheMatched: Boolean(cachedCreationResponse)",
        '"attached from state-matched opt-in analysis"',
        '"deferred to explicit response-atlas analysis or full receipt export"',
    )
    for phrase in required:
        assert phrase in APP


def test_response_evidence_keeps_scientific_boundaries():
    body = APP[APP.index("async function creationResponseReceiptEvidence"):
        APP.index("const POPULATION_RESPONSE_LABELS")]
    for phrase in (
        "atomLevelPseudoreplicationAvoided: true",
        "blockedByCompleteStructuralLeap: true",
        "randomSplitUsed: false",
        "targetUsed: false",
        "causalEffectInferred: false",
        "physicalTimeModeled: false",
    ):
        assert phrase in body


def test_build_232_assets_are_paired():
    assert 'buildId: "20260827-272"' in APP
    assert 'app.js?v=20260827-272' in HTML
    assert 'style.css?v=20260827-272' in HTML


if __name__ == "__main__":
    test_response_atlas_is_an_explicit_notebook_action()
    test_heavy_models_run_off_the_rendering_thread()
    test_cache_is_keyed_to_exact_growth_state_and_invalidated()
    test_bounded_snapshot_reuses_only_matching_evidence()
    test_response_evidence_keeps_scientific_boundaries()
    test_build_232_assets_are_paired()
    print("opt-in response atlas contract passed")
