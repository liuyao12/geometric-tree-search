"""Static contract for proper-pose residual-force transport and bounded geometric seeding."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_residual_force_vectors_are_transportable_but_never_become_a_force_field() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    projection = (APP / "local-constraint-relaxation.js").read_text(encoding="utf-8")
    force_seed = (APP / "force-seed-geometry.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(
        encoding="utf-8")

    assert 'force: Object.freeze({ label: "residual-force direction seed"' in source
    assert "calculationForceLocalEvPerAngstrom" in source
    assert "new THREE.Vector3(...atom.calculationForceEvPerAngstrom).applyQuaternion(localFrameInverse)" in source
    assert "calculationForceWorldEvPerAngstrom" in source
    assert ".applyQuaternion(candidate.rotation)" in source
    assert "copyPlacedCalculationForce(atom, site)" in source
    assert "applyCommutingBatchForceConsensus(batch, freshAtomIdsInBatch)" in source
    assert "calculationForceSeedScaleEvPerAngstrom" in source
    assert "boundedForceSeedOffset(atom.calculationForceEvPerAngstrom, scale, cap)" in source
    assert "displacementCap * Math.min(1, norm / referenceScale) / norm" in force_seed
    assert "meanForceVectors" in source
    assert "calculationForceSeedAccepted" in source
    assert "calculationForceTransportAudit" in source
    assert 'properPoseTransport: "F_world = R_cluster F_local"' in source
    assert "transportedCalculationForceVectors" in source
    assert "drawClusterCardCalculationForces" in source
    assert "archivedResidualForceCopiedAsForceField: false" in source
    assert "forceFieldInferred: false" in source
    assert "forceIntegrated: false" in source
    assert "massOrTimeStepUsed: false" in source
    assert "initialSeedAccepted" in projection
    assert '<option value="force">Residual-force direction seed' in html
    assert 'buildId: "20260827-268"' in source
    assert 'app.js?v=20260827-268' in html
    assert "Build 252" in readme
    assert "Proper-pose residual-force seeds (Build 252)" in benchmark


if __name__ == "__main__":
    test_residual_force_vectors_are_transportable_but_never_become_a_force_field()
    print("residual-force transport and bounded-seed integration contract: passed")
