from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
MODULE = (APP_DIR / "local-constraint-relaxation.js").read_text()
README = (APP_DIR / "README.md").read_text()


def test_post_attachment_projection_is_user_controlled_and_bounded():
    assert 'id="structuralRelaxationSelect"' in HTML
    for mode in ("off", "gentle", "balanced", "strong", "interface-shell",
                 "model-force-interface", "model-force-layered-interface"):
        assert f'value="{mode}"' in HTML
    assert "const STRUCTURAL_RELAXATION_MODES" in APP
    assert "displacementFraction: .025" in APP
    assert "displacementFraction: .05" in APP
    assert "displacementFraction: .08" in APP
    assert "export function relaxLocalContactGeometry" in MODULE
    assert "maximumIterations <= 64" in MODULE
    assert "site.displacementCap" in MODULE
    assert "movable-site displacement cap" in MODULE
    assert "Interface shell · emitted 5% + substrate 1.5%" in HTML
    assert "Finite −∇U interface shell · 5% + 1.5%" in HTML
    assert "Finite −∇U two-shell response · 5% + 1.5% + 0.5%" in HTML


def test_projection_moves_fresh_or_strictly_bounded_interface_sites_and_fails_closed():
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
    assert "connectedInterfaceResponseDomain" in APP
    assert "substrateFractions: Object.freeze([.015])" in APP
    assert "substrateFractions: Object.freeze([.015, .005])" in APP
    assert "auditAnchoredInterfaceShells" in APP
    assert 'modelForceSeed: true, interfaceShell: true' in APP
    assert "interface shell lacks a fixed connected anchor" in APP
    assert "substrate displacement exceeds the frozen site-identity tolerance" in APP
    assert "discreteClusterSiteIdentityRetained" in APP
    assert "exactClusterGeometryRetained: !spec.interfaceShell" in APP
    assert "exactClusterTopologyRetained: true" in APP
    assert "clusterMembershipRecomputed: false" in APP
    assert "properPortTopologyRetained: true" in APP
    assert "continuumElasticityClaimed: false" in APP
    assert "mechanicalEquilibriumClaimed: false" in APP
    assert "modelForceResidualRedistributionPassed" in APP
    assert "modelForceGroupResiduals" in APP
    assert "modelForceResultantRedistributionPassed" in APP
    assert "modelForceGroupResultantsAvailable" in APP


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
    assert "Build 434 · the first substrate shell can accommodate an attachment" in README
    assert "Build 436 · anchored two-shell interface response" in README
    assert "Any failure atomically restores the exact template coordinates" in README


if __name__ == "__main__":
    test_post_attachment_projection_is_user_controlled_and_bounded()
    test_projection_moves_fresh_or_strictly_bounded_interface_sites_and_fails_closed()
    test_projection_is_auditable_without_physical_overclaim()
    print("post-attachment constraint-relaxation contract: passed")
