"""Static contract for proper-pose Uij transport into live growth admission."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_reported_covariance_rotates_with_clusters_and_reaches_hard_growth_gates() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    displacement = (APP / "displacement-envelope.js").read_text(encoding="utf-8")
    envelopes = (APP / "colored-distance-envelopes.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    assert "rotateDisplacementTensor" in displacement
    assert "R U R^T" in displacement
    assert "directionalContactExclusion" in displacement
    assert "When neither live site" in displacement
    assert "maximumMeanPositionExclusion" in envelopes
    assert "uAnisoLocalA2" in source
    assert "templateSiteFromReference" in source
    assert "rotateDisplacementTensor(site.uAnisoLocalA2, candidate.rotation.toArray())" in source
    assert "coloredPairDirectionalExclusion(first, second)" in source
    assert "coloredPairDirectionalExclusion(site, atom)" in source
    assert "copyPlacedDisplacementTensor(atom, site)" in source
    assert "U_world = R_cluster U_local R_cluster^T" in source
    assert "sweptPathDirectionalClearance: true" in source
    assert "postAttachmentDirectionalRecheck: true" in source
    assert 'buildId: "20260827-280"' in source
    assert 'app.js?v=20260827-280' in html
    assert "Build 248 rotates each reported displacement covariance" in readme
    assert "not correlated atomic motion" in readme


if __name__ == "__main__":
    test_reported_covariance_rotates_with_clusters_and_reaches_hard_growth_gates()
    print("transported directional contact integration contract: passed")
