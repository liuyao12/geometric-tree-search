from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-force-geometry.mjs").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_validated_force_response_has_an_explicit_geometry_gate():
    for fragment in (
        'from "./external-force-geometry.mjs?v=20260830-346"',
        "externalPhysicsResponseRuntime",
        "externalPhysicsForceGeometryEnabled",
        "buildValidatedForceGeometryRuntime",
        "bindValidatedForceGeometry",
        "enableValidatedExternalForceGeometry",
        "Encode force vectors & relearn",
        'dataset.externalPhysicsForceGeometry',
        "bindExternalForceGeometryToReference(referenceAtoms)",
        "validated request-linked external-physics response",
    ):
        assert fragment in APP
    assert ".external-physics-force-actions" in STYLE


def test_force_geometry_contract_preserves_the_scientific_boundary():
    for fragment in (
        'audit?.quantityId !== "forces"',
        'audit.configurationRole !== "observation"',
        "audit.validationPassed !== true",
        "audit.targetCoordinatesEmbedded !== false",
        "F_world = R_cluster F_local",
        "candidateGeometryChanged: false",
        "candidateRankingChanged: false",
        "forceIntegrated: false",
        "usedAsPotential: false",
        "physicalTimeModeled: false",
        "targetUsed: false",
    ):
        assert fragment in MODULE
    for fragment in (
        "candidateGeometryChangedByBinding = false",
        "candidateRankingChangedByBinding = false",
        "forceSeedRequiresExplicitOptIn = true",
        "properPoseTransportHypothesis",
    ):
        assert fragment in APP


def test_build_340_is_documented_and_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260901-449' in document
        assert 'style.css?v=20260901-449' in document
        assert 'evidence-atlas.js?v=20260901-449' in document
    assert "Build 340 · encode validated force vectors as geometry" in README
    assert "Validated force-to-geometry deployment (Build 340)" in BENCHMARK
    assert "not an automatic force-field deployment" in README
    assert "Binding leaves support discovery, exact action poses" in BENCHMARK


def main() -> None:
    test_validated_force_response_has_an_explicit_geometry_gate()
    test_force_geometry_contract_preserves_the_scientific_boundary()
    test_build_340_is_documented_and_cache_busted()
    print("external force geometry portal contract: passed")


if __name__ == "__main__":
    main()
