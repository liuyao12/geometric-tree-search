"""Contract for the live, claim-bounded material-growth certificate."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_growth_certificate_separates_replay_continuation_and_recurrence() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    for element_id in (
        "growthCertificateSection",
        "growthCertificateState",
        "certificateReplay",
        "certificateContinuation",
        "certificateHierarchy",
        "certificateBoundary",
        "growthCertificateNote",
    ):
        assert f'id="{element_id}"' in html

    assert "function liveGrowthCertificate()" in source
    assert "function updateGrowthCertificate()" in source
    assert "updateGrowthCertificate();" in source
    assert "liveCertificate: liveGrowthCertificate()" in source
    assert 'targetCalls: 0' in source
    assert 'targetCoordinatesUsed: false' in source
    assert 'physicalPotentialUsed: false' in source
    assert 'geometrically certified but not labeled physically correct' in source
    assert 'Mutually exclusive ${iceAnchorTrace.moleculeLabel} orientations stay symbolic' in source
    assert 'this viewport trace is not itself a physical-time trajectory' in source
    assert "exact replay of the supplied window" in readme
    assert "outside-window structural output" in readme
    assert "The same structured certificate is embedded in experiment" in readme


if __name__ == "__main__":
    test_growth_certificate_separates_replay_continuation_and_recurrence()
    print("live growth certificate contract: passed")
