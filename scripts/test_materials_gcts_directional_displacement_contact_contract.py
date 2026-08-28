"""Static contract for reported Uij in the colored contact geometry."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_full_uij_enters_directional_contact_geometry_without_motion_claims() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    envelopes = (APP / "colored-distance-envelopes.js").read_text(encoding="utf-8")
    displacement = (APP / "displacement-envelope.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    assert "directionalPairDisplacementSigma" in displacement
    assert "nᵀ(U_i + U_j)n" in displacement
    assert "pairSigma" in envelopes
    assert "minimumOneSigmaContact" in envelopes
    assert "meanPositionExclusion" in envelopes
    assert "directionalSigmaUpper" in envelopes
    assert "directionalUncertaintyApplied" in envelopes
    assert "pairSigma: (first, second) => directionalPairDisplacementSigma" in source
    assert "one-sigma pair-direction contact envelopes" in source
    assert "directionalPairEnvelopeModel" in source
    assert "independentSiteCovarianceAssumed: true" in source
    assert "correlatedDisplacementModelUsed: false" in source
    assert "contactProbabilityClaimed: false" in source
    assert "full-Uij pair-direction support" in source
    assert 'buildId: "20260827-277"' in source
    assert 'app.js?v=20260827-277' in html
    assert "Build 247 carries reported Cartesian Uiso/Uij into the local contact geometry" in readme
    assert "not correlated thermal motion" in readme


if __name__ == "__main__":
    test_full_uij_enters_directional_contact_geometry_without_motion_claims()
    print("directional Uij contact-geometry integration contract: passed")
