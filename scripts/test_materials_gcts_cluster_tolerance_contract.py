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
    assert "function measuredPairUncertaintyAngstrom()" in source
    assert "function measuredPairUncertaintySource()" in source
    assert "function learnReferenceEnsemblePairUncertainty()" in source
    assert "function clusterMetricToleranceAngstrom()" in source
    assert "function effectiveClusterMetricTolerance()" in source
    assert 'clusterToleranceMode === "strict" ? .01' in source
    assert 'clusterToleranceMode === "thermal" ? .05 : .025' in source
    assert source.count("descriptorToleranceA: clusterMetricToleranceAngstrom()") == 2
    assert "metricTolerance: effectiveClusterMetricTolerance()" in source
    assert 'clusterToleranceSelect.addEventListener("change"' in source
    assert "metricIsometryToleranceMode: clusterToleranceMode" in source
    assert "nominalMetricIsometryToleranceFractionOfNearestNeighbor: clusterMetricTolerance()" in source
    assert "metricIsometryToleranceFractionOfNearestNeighbor: receiptRound(effectiveClusterMetricTolerance())" in source
    assert "metricIsometryToleranceAngstrom: receiptRound(clusterMetricToleranceAngstrom())" in source
    assert '"fixed-topology snapshot pair distances"' in source
    assert "pairDistanceOneSigmaFloorAngstrom: receiptRound(measuredPairUncertaintyAngstrom())" in source
    assert "upperPairDistanceSigmaAngstrom" in source
    assert "crossFramePairsConstructed: false" in source
    assert "metricToleranceMode: clusterToleranceMode" in source
    assert "metricToleranceFraction: effectiveClusterMetricTolerance()" in source
    assert '(marking.config.clusterToleranceMode || "balanced") === clusterToleranceMode' in source
    assert 'const nominalTolerance = { strict: 1, balanced: 2.5, thermal: 5 }' in source
    assert 'effectiveMetricToleranceFraction: effectiveClusterMetricTolerance()' in source


if __name__ == "__main__":
    test_tolerance_controls_all_metric_isometry_learners()
    print("cluster metric-tolerance contract: passed")
