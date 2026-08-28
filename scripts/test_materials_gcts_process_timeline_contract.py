#!/usr/bin/env python3
"""Static contract for reversible learning and read-only growth microscopes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_reversible_process_timeline_contract() -> None:
    for element_id in (
        "processTimeline",
        "processTimelineEyebrow",
        "processTimelineTitle",
        "processTimelineState",
        "processTimelineInput",
        "processTimelineNote",
        "processEvidenceLedger",
        "processEvidenceDetail",
    ):
        assert f'id="{element_id}"' in HTML
    assert 'id="processTimelineInput" type="range"' in HTML
    assert 'type="text"' not in HTML[HTML.index('id="processTimeline"'):HTML.index('id="processTimeline"') + 1600]

    assert 'function processTimelineRecord()' in APP
    assert 'stage: "cluster-identification"' in APP
    assert 'stage: "gcts-learning"' in APP
    assert 'stage: "material-growth"' in APP
    assert 'reversible: true' in APP
    assert 'traceFrozen: true' in APP
    assert 'targetUsed: false' in APP
    assert 'function scrubProcessTimeline(value)' in APP
    assert 'function processTimelineEvidenceRecord()' in APP
    assert 'function renderProcessEvidence()' in APP
    assert 'evidence-ordered audit replay of selected recurring supports and explicit gaps' in APP
    assert 'deterministic sample-indexed section fit' in APP
    assert 'accepted / removed' in APP
    assert 'coefficient step' in APP
    assert 'Step order now follows explicit cover gain' in APP
    assert 'read-only audit of retained certified structural states' in APP
    assert 'evidenceReplayOnly: true' in APP
    assert 'liveGeometryMutated: false' in APP
    assert 'They are not forces, energies, potentials' in APP
    assert 'setPlaying(false);' in APP[APP.index('function scrubProcessTimeline(value)'):]
    assert 'clusterDiscoveryProgress = progress' in APP
    assert 'trainingProgress = progress' in APP
    assert 'processTimelineInput.addEventListener("input"' in APP
    assert 'reversibleProcessTimeline: processTimelineRecord()' in APP

    assert '.process-timeline' in CSS
    assert '.process-evidence-ledger' in CSS
    assert '--process-progress' in CSS
    assert 'Play resumes from the selected decision step' in README
    assert 'resume training from that sample count' in README


if __name__ == "__main__":
    test_reversible_process_timeline_contract()
    print("process timeline contract: ok")
