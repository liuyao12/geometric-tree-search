#!/usr/bin/env python3
"""Static contract for the responsive bounded experiment-notebook snapshot."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()


def _function_body(name: str, following: str) -> str:
    start = APP.index(f"async function {name}")
    end = APP.index(following, start)
    return APP[start:end]


def test_save_uses_bounded_snapshot_not_full_receipt():
    body = _function_body("saveCurrentExperimentNotebookEntry()", "async function withReceiptStatus")
    assert "buildExperimentNotebookSnapshot()" in body
    assert "buildExperimentReceipt()" not in body
    assert "bounded coordinate-free snapshot" in body


def test_snapshot_retains_lineage_frontier_and_claim_evidence():
    body = _function_body("buildExperimentNotebookSnapshot()", "function notebookInterventionFactors")
    required = (
        'schema: "gcts-materials-growth-notebook-snapshot-v1"',
        "structureSha256: await structureDigest(referenceAtoms, \"angstrom\")",
        "coverLineageAudit: await coverLineageReceiptEvidence()",
        "structuralLeapCertificates: leapHistoryReceipt",
        "...receiptGrowthClaims(scenarioSelect.value, benchmark, iceAnchorTrace)",
        "coordinatesEmbedded: false",
    )
    for phrase in required:
        assert phrase in body
    assert "candidateSetDigest: snapshot.candidateDigest" in APP
    assert "hardAdmittedCandidateSetDigest: markingAudit.hardAdmittedCandidateSetDigest" in APP


def test_snapshot_is_honest_about_deferred_heavy_evidence():
    assert 'fullReceiptBuilt: false' in APP
    assert '"deferred to explicit response-atlas analysis or full receipt export"' in APP
    assert "availableInFullReceiptExport: true" in APP
    assert "digestExcludesBuildTiming: true" in APP


def test_build_232_assets_are_paired():
    assert 'buildId: "20260827-279"' in APP
    assert 'app.js?v=20260827-279' in HTML
    assert 'style.css?v=20260827-279' in HTML


if __name__ == "__main__":
    test_save_uses_bounded_snapshot_not_full_receipt()
    test_snapshot_retains_lineage_frontier_and_claim_evidence()
    test_snapshot_is_honest_about_deferred_heavy_evidence()
    test_build_232_assets_are_paired()
    print("bounded notebook snapshot contract passed")
