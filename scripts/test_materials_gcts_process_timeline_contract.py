#!/usr/bin/env python3
"""Static contract for the reversible cluster/GCTS process microscope."""

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
    ):
        assert f'id="{element_id}"' in HTML
    assert 'id="processTimelineInput" type="range"' in HTML
    assert 'type="text"' not in HTML[HTML.index('id="processTimeline"'):HTML.index('id="processTimeline"') + 1600]

    assert 'function processTimelineRecord()' in APP
    assert 'stage: "cluster-identification"' in APP
    assert 'stage: "gcts-learning"' in APP
    assert 'reversible: true' in APP
    assert 'traceFrozen: true' in APP
    assert 'targetUsed: false' in APP
    assert 'function scrubProcessTimeline(value)' in APP
    assert 'setPlaying(false);' in APP[APP.index('function scrubProcessTimeline(value)'):]
    assert 'clusterDiscoveryProgress = progress' in APP
    assert 'trainingProgress = progress' in APP
    assert 'processTimelineInput.addEventListener("input"' in APP
    assert 'reversibleProcessTimeline: processTimelineRecord()' in APP

    assert '.process-timeline' in CSS
    assert '--process-progress' in CSS
    assert 'Play resumes from the selected decision step' in README
    assert 'resume training from that sample count' in README


if __name__ == "__main__":
    test_reversible_process_timeline_contract()
    print("process timeline contract: ok")
