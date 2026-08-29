from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
SCHEDULE = (ROOT / "apps/iqc-growth-live/cluster-discovery-schedule.js").read_text()


def test_cluster_process_uses_evidence_order_not_hash_timing():
    assert "evidenceOrderedClusterDiscoverySchedule" in APP
    assert "evidenceOrderedPlacementSchedule" in SCHEDULE
    assert "hashSchedulingUsed: false" in SCHEDULE
    assert "discoveryHash" not in APP
    assert "maximum uncovered support gain" in SCHEDULE
    assert "after both endpoints acquire selected-cover evidence" in SCHEDULE


def test_every_connection_decision_has_a_scientific_reason_class():
    for reason in (
        "recurring-support-edge",
        "complete-cover-edge",
        "unsupported-colored-pair",
        "outside-colored-envelope",
        "redundant-support-chord",
        "no-recurring-support",
    ):
        assert reason in APP
    assert "orderingAudit: { ...clusterDiscoveryTrace.orderingAudit }" in APP
    assert "rather than molecular dynamics" in APP
    assert "wall-clock optimizer trace" in APP


def test_stage_separation_remains_explicit():
    assert 'aria-label="Stage process and structural-history timeline"' in HTML
    assert 'aria-label="One rotating three-dimensional marking scene per learned cluster type"' in HTML
    assert 'pipelineStage === 1 ? "full configuration · tentative → rejected → settled supports"' in APP
    assert 'pipelineStage === 3\n    ? "one evolving marking scene per cluster' in APP


def test_build_306_cache_and_narrative_contract():
    assert 'buildId: "20260829-330"' in APP
    assert "app.js?v=20260829-330" in HTML
    assert "style.css?v=20260829-330" in HTML
    assert "Build 259 · evidence-ordered cluster discovery" in README
    assert "Build 306 · settled cluster surfaces in the discovery scene" in README
    assert "function addSettledDiscoverySurfaces(placements, color, opacity)" in APP
    assert "hypotheses remain muted lines" in README
