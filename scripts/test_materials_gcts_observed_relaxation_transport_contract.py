"""Static contract for proper-pose transport of archived relaxation vectors."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_observed_non_affine_vectors_seed_only_bounded_fail_closed_projection() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    projection = (APP / "local-constraint-relaxation.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(
        encoding="utf-8")

    assert 'observed: Object.freeze({ label: "observed-vector seed"' in source
    assert "observedRelaxationLocalScene" in source
    assert ".applyQuaternion(localFrameInverse)" in source
    assert "observedRelaxationWorldScene" in source
    assert ".applyQuaternion(candidate.rotation)" in source
    assert "copyPlacedObservedRelaxation(atom, site)" in source
    assert "const initialOffsets = observedOffsets || forceOffsets" in source
    assert "initialOffsets," in source
    assert "observedRelaxationSeedAccepted" in source
    assert "observedRelaxationTransportAudit" in source
    assert "transportedObservedRelaxationVectors" in source
    assert "drawClusterCardObservedRelaxation" in source
    assert "worseningSeedIgnored: true" in source
    assert "archivedDisplacementCopiedAsForce: false" in source
    assert "initialOffsets = null" in projection
    assert "seedImprovedObjective" in projection
    assert "magnitude > displacementCap" in projection
    assert '<option value="observed">Observed non-affine vector seed' in html
    assert 'buildId: "20260827-252"' in source
    assert 'app.js?v=20260827-252' in html
    assert "Build 251 adds the first archive-observed shortcut" in readme
    assert "Proper-pose observed relaxation seeds (Build 251)" in benchmark


if __name__ == "__main__":
    test_observed_non_affine_vectors_seed_only_bounded_fail_closed_projection()
    print("observed relaxation-vector transport integration contract: passed")
