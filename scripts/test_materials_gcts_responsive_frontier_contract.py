#!/usr/bin/env python3
"""Portal contract for target-free, event-loop-yielding frontier evaluation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text()
HTML = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text()
ALIAS = (ROOT / "iqc-growth-live" / "index.html").read_text()
CSS = (ROOT / "apps" / "iqc-growth-live" / "style.css").read_text()


def main() -> None:
    for document in (HTML, ALIAS):
        assert 'id="growthEvaluationProgress"' in document
        assert 'id="growthEvaluationMeter"' in document
        assert "Target-free candidates are evaluated in bounded browser slices." in document
    for needle in (
        "function scoreFrontierCandidate(candidate, audit)",
        "async function selectCommutingFrontierBatch(evaluated, generation)",
        "async function commutingFrontierBatch()",
        "await new Promise((resolve) => requestAnimationFrame(resolve))",
        "candidateSetFrozenBeforeEvaluation: true",
        "candidateSetTargetUsed: false",
        "eventLoopYields: growthFrontierWork.yields",
        "maximumSliceMilliseconds",
        "frontierEvaluation: growthFrontierWorkReceipt()",
        "if (generation !== growthSearchGeneration) return null",
        "stepButton.disabled = pipelineStage === 4 && (Boolean(material.growthWithheld) || growthFrontierWork.busy)",
        "Pause queued · the current immutable structural leap will finish atomically",
        "pauseRequested: pauseAfterCurrentGrowthLeap",
    ):
        assert needle in APP, needle
    assert "physicalTimeInferred: false" in APP
    assert ".growth-evaluation-progress" in CSS
    assert "max slice" in APP
    print("responsive target-free frontier portal contract: passed")


if __name__ == "__main__":
    main()
