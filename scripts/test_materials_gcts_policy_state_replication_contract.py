from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
INDEX = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/policy-state-replication.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_saved_run_is_the_replication_unit():
    assert 'analysisUnit: "one resolved coordinate-free contrast per unique saved-run receipt"' in MODULE
    assert "frontierRowsPooledAcrossRuns: false" in MODULE
    assert "unique.has(record.receiptSha256)" in MODULE
    assert 'minimumRuns = 3' in MODULE


def test_replication_claims_fail_closed():
    assert 'record.targetUsed !== false' in MODULE
    assert '!row?.resolved' in MODULE
    assert '"repeat-run-consistent"' in MODULE
    assert '"cross-input-consistent"' in MODULE
    assert 'pValueComputed: false' in MODULE
    assert 'causalEffectInferred: false' in MODULE
    assert 'statisticalIndependenceAssumed: false' in MODULE


def test_notebook_serializes_compact_state_contrast():
    assert "policyStateConditioning:" in APP
    assert 'frontierSamplesEmbedded: false' in APP
    assert 'analysisUnit: "one within-run retained-frontier contrast"' in APP
    assert "rows: audit.rows.map" in APP
    assert "stateConditioningUpgradeNeeded" in APP


def test_notebook_exposes_interactive_replication_card():
    for element_id in [
        "notebookStateReplication",
        "notebookStateReplicationContrast",
        "notebookStateReplicationObservable",
        "notebookStateReplicationRuns",
        "notebookStateReplicationSummary",
    ]:
        assert f'id="{element_id}"' in INDEX
        assert f'$("{element_id}")' in APP
    assert "runBlockedStateReplication(records" in APP
    assert "renderNotebookStateReplication(experimentNotebookEntries)" in APP
    assert ".notebook-state-replication.cross-input-consistent" in STYLE
    assert "No p-value, causal effect, specimen independence" in INDEX


def test_build_282_is_stamped_and_documented():
    assert 'buildId: "20260827-282"' in APP
    assert 'app.js?v=20260827-282' in INDEX
    assert "Build 282 · run-blocked material-state replication" in README
    assert "Run-blocked material-state replication (Build 282)" in DOCS
