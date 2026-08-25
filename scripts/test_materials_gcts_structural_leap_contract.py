"""Source contract for the live structural leap certificate."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def test_structural_leaps_separate_geometry_from_dynamics() -> None:
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    style = (APP_DIR / "style.css").read_text(encoding="utf-8")
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")

    for element_id in (
        "leapCertificateSection", "leapCertificateState", "leapHistory",
        "leapFlow", "leapClaimBoundary",
    ):
        assert f'id="{element_id}"' in html
    assert "function renderStructuralLeap(leap = null)" in source
    assert "function recordStructuralLeap(leap)" in source
    assert "targetUsed: false" in source
    assert "physicalTimeModeled: false" in source
    assert "dynamicsIntegrated: false" in source
    assert "structuralLeapCertificates: leapHistory.map" in source
    assert "pairwise-commuting whole-cluster actions" in source
    assert "valid in every placement order" in source
    assert "No force trajectory, relaxation path, transition probability" in source
    assert "finite structural fixed point" in source
    assert "shared oxygen-anchor leap" in source
    assert "tunnelling, diffusion, relaxation, probability" in source
    assert ".leap-history" in style
    assert ".leap-flow" in style
    assert ".leap-claim-boundary" in style
    assert "molecular-dynamics time step" in readme
    assert "frontier exhaustion is reported as a finite structural fixed" in readme


if __name__ == "__main__":
    test_structural_leaps_separate_geometry_from_dynamics()
    print("structural leap certificate contract: passed")
