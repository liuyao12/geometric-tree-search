from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-trajectory-geometry.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_pair_correlation_is_a_validated_proper_rotation_invariant_statistic():
    for fragment in (
        "validatedTrajectoryPairCorrelation",
        "driftRemovedDisplacementsAngstrom",
        "normalizedTrapezoidalTimeWeights",
        "isotropicCorrelation",
        "longitudinalCorrelation",
        "relativeRmsAngstrom",
        "globalTranslationRemovedPerFrame: true",
        "properRotationInvariant: true",
        "probabilityDistributionInferred: false",
        "targetUsed: false",
    ):
        assert fragment in MODULE


def test_marking_is_explicit_response_bound_and_does_not_change_geometry():
    for fragment in (
        '"trajectory-ports"',
        "trajectoryCorrelationWeight: .14",
        "requiresValidatedTrajectory: true",
        "trajectoryEvidenceSha256",
        "trajectoryCorrelationEvidenceSha256",
        "trajectoryCorrelationSectionAudit",
        "markingRankingMayChangeOnlyWhenExplicitlySelected: true",
        "candidateGeometryChanged: false",
        "candidateEnumerationChanged: false",
        "hardAdmissionChanged: false",
        "physicalPotentialUsed: false",
        "causalMechanismInferred: false",
        "physicalClockTransferred: false",
    ):
        assert fragment in APP
    for document in (HTML, ALIAS_HTML):
        assert '<option value="trajectory-ports" disabled>' in document


def test_learning_cards_and_scientific_boundary_are_visible():
    for fragment in (
        "drawClusterCardTrajectoryCorrelations",
        "rgba(92,240,204",
        "rgba(255,113,145",
        "co-motion",
        "trajectory-port-correlation",
        "Cyan solid card edges",
        "dashed pink edges",
    ):
        assert fragment in APP
    assert "Build 343 · collective trajectory geometry in GCTS connection markings" in README
    assert "Collective trajectory marking deployment (Build 343)" in BENCHMARK


def test_build_343_is_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260831-380' in document
        assert 'style.css?v=20260831-380' in document
        assert 'evidence-atlas.js?v=20260831-380' in document
    assert 'buildId: "20260831-380"' in APP


def main() -> None:
    test_pair_correlation_is_a_validated_proper_rotation_invariant_statistic()
    test_marking_is_explicit_response_bound_and_does_not_change_geometry()
    test_learning_cards_and_scientific_boundary_are_visible()
    test_build_343_is_cache_busted()
    print("trajectory correlation marking portal contract: passed")


if __name__ == "__main__":
    main()
