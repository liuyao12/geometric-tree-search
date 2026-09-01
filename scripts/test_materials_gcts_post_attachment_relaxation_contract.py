from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
MODULE = (APP_DIR / "local-constraint-relaxation.js").read_text()
README = (APP_DIR / "README.md").read_text()


def test_post_attachment_projection_is_user_controlled_and_bounded():
    assert 'id="structuralRelaxationSelect"' in HTML
    for mode in ("off", "gentle", "balanced", "strong"):
        assert f'value="{mode}"' in HTML
    assert "const STRUCTURAL_RELAXATION_MODES" in APP
    assert "displacementFraction: .025" in APP
    assert "displacementFraction: .05" in APP
    assert "displacementFraction: .08" in APP
    assert "export function relaxLocalContactGeometry" in MODULE
    assert "maximumIterations <= 64" in MODULE


def test_projection_moves_only_new_post_replay_sites_and_fails_closed():
    assert "const relaxationAuthorized = targetFreeGrowthAuthorized()" in APP
    assert "freshAtomIds: []" in APP
    assert "freshAtomIdsInBatch.push(...placement.freshAtomIds)" in APP
    assert "projectAcceptedBatchGeometry(freshAtomIdsInBatch, relaxationAuthorized)" in APP
    assert "after.strain.total < before.strain.total - 1e-9" in APP
    assert "contactAngleStrainDecreased: strainDecreased" in APP
    assert "coordination capacity would be exceeded" in APP
    assert "angular envelope would be violated" in APP
    assert "public boundary would be crossed" in APP
    assert "colored hard exclusion would be violated" in APP
    assert "rebuildSpatialIndex();" in APP
    assert "exactClusterTopologyRetained: true" in APP
    assert "properPortTopologyRetained: true" in APP


def test_projection_is_auditable_without_physical_overclaim():
    assert "postAttachmentConstraintProjection:" in APP
    assert "relaxation: leap.relaxation || null" in APP
    assert 'value="relaxationDisplacement"' in HTML
    assert "post-attachment maximum displacement · Å" in APP
    for nonclaim in (
        "targetUsed: false",
        "physicalPotentialUsed: false",
        "forceIntegrated: false",
        "elapsedPhysicalTimeModeled: false",
    ):
        assert nonclaim in APP
    assert "Build 134" in README
    assert "Any failure atomically restores the exact template coordinates" in README


if __name__ == "__main__":
    test_post_attachment_projection_is_user_controlled_and_bounded()
    test_projection_moves_only_new_post_replay_sites_and_fails_closed()
    test_projection_is_auditable_without_physical_overclaim()
    print("post-attachment constraint-relaxation contract: passed")
