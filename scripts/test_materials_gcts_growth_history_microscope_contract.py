#!/usr/bin/env python3
"""Portal contract for the read-only Stage 4 structural-history microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text()
HTML = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text()
ALIAS = (ROOT / "iqc-growth-live" / "index.html").read_text()


def main() -> None:
    for document in (HTML, ALIAS):
        assert 'id="processTimelineStart"' in document
        assert 'id="processTimelineEnd"' in document
        assert 'id="processTimelineInput"' in document
        assert 'id="leapHistory"' in document
    for needle in (
        'stage: "material-growth"',
        'title: "Certified structural states"',
        'eyebrow: "structural-history microscope · no physical clock"',
        "evidenceReplayOnly: true",
        "liveGeometryMutated: false",
        'mode: "read-only audit of retained certified structural states"',
        "selectedLeapIndex = progress - 1",
        "renderStructuralLeap(selectedLeapIndex < 0 ? null : leapHistory[selectedLeapIndex])",
        'seedButton.textContent = `seed · ${leapHistory[0].before.atoms}`',
        "const seedState = leapHistory[0]?.before",
        "frontier not sampled",
        "The slider selects retained coordinate-free certificates",
        "reversibleProcessTimeline: processTimelineRecord()",
    ):
        assert needle in APP, needle
    stage_branch = APP[APP.index('if (pipelineStage === 4 && leapHistory.length) {'):
                       APP.index("return null;", APP.index('if (pipelineStage === 4 && leapHistory.length) {'))]
    assert "atoms =" not in stage_branch
    assert "placedClusters =" not in stage_branch
    assert "performOffLatticeEvent" not in stage_branch
    print("read-only material-growth history microscope contract: passed")


if __name__ == "__main__":
    main()
