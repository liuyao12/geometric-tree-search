from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-trajectory-geometry.mjs").read_text()
REQUEST = (ROOT / "apps/iqc-growth-live/external-physics-request.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_trajectory_response_has_an_explicit_local_section_gate():
    for fragment in (
        'from "./external-trajectory-geometry.mjs?v=20260830-346"',
        "externalPhysicsRequestRuntime",
        "externalPhysicsTrajectoryGeometryEnabled",
        "buildValidatedTrajectoryGeometryRuntime",
        "bindValidatedTrajectoryGeometry",
        "enableValidatedExternalTrajectoryGeometry",
        "Encode trajectory sections & relearn",
        "dataset.externalPhysicsTrajectoryGeometry",
        "bindExternalTrajectoryGeometryToReference(referenceAtoms)",
        "validated request-linked external-physics trajectory",
    ):
        assert fragment in APP


def test_trajectory_geometry_is_ordered_drift_removed_and_target_free():
    for fragment in (
        'audit?.quantityId !== "trajectory"',
        'audit.configurationRole !== "observation"',
        "audit.validationPassed !== true",
        "audit.targetCoordinatesEmbedded !== false",
        "trajectory reference frame does not match the exact ordered observation",
        "globalTranslationRemovedPerFrame: true",
        "globalRotationRemovedPerFrame: false",
        "delta_r_world = R_cluster delta_r_local",
        "candidateGeometryChanged: false",
        "candidateRankingChanged: false",
        "trajectoryIntegrated: false",
        "usedAsPhysicalClock: false",
        "targetUsed: false",
        "normalizedTrapezoidalWeights",
        "covarianceCartesianAngstromSquared",
        "time-weighted drift-removed empirical trajectory covariance",
        "covarianceProbabilityDistributionInferred: false",
        "covarianceThermalEquilibriumAssumed: false",
        "covariancePhononModelAssumed: false",
        "C_world = R_cluster C_local R_cluster^T",
    ):
        assert fragment in MODULE
    assert "frame zero must reproduce the selected configuration within 1e-7 angstrom" in REQUEST


def test_transport_and_receipt_boundaries_are_visible():
    for fragment in (
        "observedDisplacementSeedRequiresExplicitOptIn = true",
        "gctsSearchStepsUsedAsPhysicalTime = false",
        "trajectoryIntegratedByGcts: false",
        "suppliedTimestampsUsedAsGctsClock: false",
        "externalTrajectoryPathLengthAngstrom",
        "externalTrajectoryMaximumExcursionAngstrom",
        "trajectory section",
        "externalTrajectoryCovarianceMode",
        "externalTrajectoryCovarianceModeSelect",
        "atomDisplayedDisplacementTensorAngstrom2",
        'externalTrajectoryCovarianceMode === "directional-clearance"',
        "trajectoryCovarianceLiveDirectionalAdmission",
        "candidateRankingChangedByCovarianceMode = false",
        "resetExternalTrajectoryCovarianceMode",
        "delete atom.trajectoryCovarianceCartesianA2",
    ):
        assert fragment in APP
    for fragment in (
        'id="externalTrajectoryCovarianceControl"',
        'id="externalTrajectoryCovarianceMode"',
        '<option value="display">display only</option>',
        '<option value="directional-clearance">1σ directional clearance</option>',
    ):
        assert fragment in HTML
    assert "Build 342 · empirical anisotropic trajectory covariance" in README
    assert "Trajectory covariance deployment (Build 342)" in BENCHMARK


def test_build_342_is_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260901-411' in document
        assert 'style.css?v=20260901-411' in document
        assert 'evidence-atlas.js?v=20260901-411' in document
    assert 'buildId: "20260901-411"' in APP


def main() -> None:
    test_trajectory_response_has_an_explicit_local_section_gate()
    test_trajectory_geometry_is_ordered_drift_removed_and_target_free()
    test_transport_and_receipt_boundaries_are_visible()
    test_build_342_is_cache_busted()
    print("external trajectory geometry portal contract: passed")


if __name__ == "__main__":
    main()
