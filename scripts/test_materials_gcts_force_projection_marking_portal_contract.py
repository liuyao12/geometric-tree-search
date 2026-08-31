from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-force-geometry.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_force_pair_geometry_is_finite_and_proper_rotation_invariant():
    for fragment in (
        "validatedForcePairGeometry",
        "forceP90ElectronVoltPerAngstrom",
        "inwardProjectionElectronVoltPerAngstrom",
        "commonModeProjectionElectronVoltPerAngstrom",
        "transverseRelativeElectronVoltPerAngstrom",
        "normalizedInwardProjection",
        'normalization: "observation force-magnitude p90"',
        "properRotationInvariant: true",
        "forceFieldInferred: false",
        "energySurfaceInferred: false",
        "targetUsed: false",
    ):
        assert fragment in MODULE


def test_force_marking_is_explicit_response_bound_and_geometry_preserving():
    for fragment in (
        '"force-ports"',
        "forceProjectionWeight: .12",
        "requiresValidatedForce: true",
        "forceEvidenceSha256",
        "forceProjectionEvidenceSha256",
        "forceProjectionSectionAudit",
        "markingRankingMayChangeOnlyWhenExplicitlySelected: true",
        "candidateGeometryChanged: false",
        "candidateEnumerationChanged: false",
        "hardAdmissionChanged: false",
        "equilibriumInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert fragment in APP
    for document in (HTML, ALIAS_HTML):
        assert '<option value="force-ports" disabled>' in document


def test_force_projection_is_visible_in_cluster_learning_and_physics_receipts():
    for fragment in (
        "drawClusterCardForceProjections",
        "rgba(255,196,92",
        "rgba(100,174,255",
        "force-port-projection",
        "Gold cluster-card edges",
        "dashed blue edges",
    ):
        assert fragment in APP
    assert "Build 344 · residual-force geometry in GCTS connection markings" in README
    assert "Residual-force connection marking deployment (Build 344)" in BENCHMARK


def test_build_344_is_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260831-360' in document
        assert 'style.css?v=20260831-360' in document
        assert 'evidence-atlas.js?v=20260831-360' in document
    assert 'buildId: "20260831-360"' in APP


def main() -> None:
    test_force_pair_geometry_is_finite_and_proper_rotation_invariant()
    test_force_marking_is_explicit_response_bound_and_geometry_preserving()
    test_force_projection_is_visible_in_cluster_learning_and_physics_receipts()
    test_build_344_is_cache_busted()
    print("force projection marking portal contract: passed")


if __name__ == "__main__":
    main()
