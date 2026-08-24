"""Contract for stage-local, receipt-recorded clustering tolerance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_tolerance_controls_all_metric_isometry_learners() -> None:
    html = (APP_DIR / "index.html").read_text()
    source = (APP_DIR / "app.js").read_text()

    assert 'id="clusterToleranceSelect"' in html
    assert "Strict · 1.0%" in html
    assert "Balanced · 2.5%" in html
    assert "Thermal/disordered · 5.0%" in html
    assert "function clusterMetricTolerance()" in source
    assert 'clusterToleranceMode === "strict" ? .01' in source
    assert 'clusterToleranceMode === "thermal" ? .05 : .025' in source
    assert source.count("descriptorToleranceA: referenceSpacingA * clusterMetricTolerance()") == 2
    assert "metricTolerance: clusterMetricTolerance()" in source
    assert 'clusterToleranceSelect.addEventListener("change"' in source
    assert "metricIsometryToleranceMode: clusterToleranceMode" in source
    assert "metricIsometryToleranceFractionOfNearestNeighbor: clusterMetricTolerance()" in source
    assert "metricIsometryToleranceAngstrom: receiptRound(referenceSpacingA * clusterMetricTolerance())" in source
    assert "metricToleranceMode: clusterToleranceMode" in source
    assert "metricToleranceFraction: clusterMetricTolerance()" in source
    assert '(marking.config.clusterToleranceMode || "balanced") === clusterToleranceMode' in source
    assert 'const tolerance = { strict: "ε1%", balanced: "ε2.5%", thermal: "ε5%" }' in source


if __name__ == "__main__":
    test_tolerance_controls_all_metric_isometry_learners()
    print("cluster metric-tolerance contract: passed")
