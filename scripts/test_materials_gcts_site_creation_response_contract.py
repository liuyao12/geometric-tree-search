from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-creation-response.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_creation_shell_is_frozen_before_optional_projection():
    assert "freezeCreationGeometryForAtoms(freshAtomIdsInBatch);" in APP
    assert APP.index("freezeCreationGeometryForAtoms(freshAtomIdsInBatch);") < APP.index(
        "projectAcceptedBatchGeometry(freshAtomIdsInBatch, relaxationAuthorized)")
    assert "atom.creationGeometry" in APP
    assert "siteId: neighbor.id" in APP
    assert "vectorAngstrom" in APP


def test_response_uses_exact_neighbor_identity_and_affine_residual():
    assert "bestAffineNeighborhoodResidual" in MODULE
    assert "currentById.get(String(neighbor.siteId))" in MODULE
    assert "exactNeighborIdentityPairing: true" in MODULE
    for field in ("centerDisplacementAngstrom", "radialRmsAngstrom", "rootD2MinAngstrom",
                  "equivalentShearStrain", "localVolumeChangeFraction"):
        assert field in MODULE


def test_response_is_visible_and_claims_fail_closed():
    for identifier in ("siteCreationResponseState", "siteCreationResponseGrid", "siteCreationResponseBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert ".site-creation-response" in STYLE
    assert "targetUsed: false" in MODULE
    assert "physicalDynamicsIntegrated: false" in MODULE
    assert "energyInferred: false" in MODULE
    assert "forceInferred: false" in MODULE
    assert "it is not a force trajectory, energy relaxation, rate, mechanism, or physical elapsed time" in APP


def test_build_192_assets_and_narrative():
    assert 'buildId: "20260826-214"' in APP
    assert 'app.js?v=20260826-214' in HTML
    assert 'style.css?v=20260826-104' in HTML
    assert 'site-creation-response.js?v=20260826-1' in APP
    assert "Build 192" in README
    assert "Build 192" in DOCS
