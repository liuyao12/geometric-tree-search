from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def function_body(name: str, next_name: str) -> str:
    start = APP.index(f"function {name}(")
    end = APP.index(f"function {next_name}(", start)
    return APP[start:end]


def test_frontier_refits_identical_samples_at_real_capacities():
    row = function_body("markingCapacityFrontierRow", "finalizeMarkingCapacityFrontier")
    fit = function_body("learnMarkingCapacityFrontier", "scheduleMarkingCapacityFrontier")
    finalize = function_body("finalizeMarkingCapacityFrontier", "learnMarkingCapacityFrontier")
    assert "[1, 3, 6, 12, autoCapacity]" in fit
    assert "learnSectionModel(source, { ...baseConfig, channels: capacity" in row
    assert "finalPoint.trainLoss" in row
    assert "finalPoint.validationLoss" in row
    assert "activeParameters" in row
    assert "coefficientSlots" in row
    assert "shortfallTypes" in row
    assert "scheduleMarkingCapacityFrontier(referenceAtoms)" in APP
    assert "window.setTimeout(fitNext, 0)" in APP
    assert 'splitRule: "deterministic occurrence index modulo 5; index 0 held out"' in finalize
    assert "targetUsed: false" in finalize
    assert "physicalEnergy: false" in finalize


def test_recommendation_requires_rank_coverage_before_loss_tolerance():
    fit = function_body("finalizeMarkingCapacityFrontier", "learnMarkingCapacityFrontier")
    assert "rows.filter((row) => row.shortfallTypes === 0)" in fit
    assert "bestValidation * 1.05 + .002" in fit
    assert 'selectionRule: "smallest rank-complete capacity within 5% + 0.002' in fit
    assert "row.capacity === audit.recommendedCapacity" in APP
    assert "restartMarkingTraining({ rebuildCapacityFrontier: false })" in function_body(
        "renderMarkingCapacityFrontier", "markingCapacityAuditRecord"
    )


def test_frontier_is_visible_and_receipt_audited():
    assert 'id="markingCapacityFrontier"' in HTML
    assert 'id="markingCapacityDetail"' in HTML
    assert ".marking-capacity-audit" in CSS
    assert "capacityFrontier: markingCapacityAuditRecord()" in APP
    assert "capacityAudit: markingCapacityAuditRecord()" in APP
    assert "activeMarking.capacityAudit" in APP


def test_build_211_release_identity_is_coherent():
    assert 'buildId: "20260826-214"' in APP
    assert 'app.js?v=20260826-214' in HTML
    assert "Build 211" in README
    assert "Build 211" in DOC


if __name__ == "__main__":
    test_frontier_refits_identical_samples_at_real_capacities()
    test_recommendation_requires_rank_coverage_before_loss_tolerance()
    test_frontier_is_visible_and_receipt_audited()
    test_build_211_release_identity_is_coherent()
    print("Marking capacity-frontier contract: passed")
