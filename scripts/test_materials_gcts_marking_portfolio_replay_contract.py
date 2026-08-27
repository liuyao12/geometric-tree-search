from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_saved_marking_replays_its_own_basis_and_mask():
    assert "markingAxesForBasis(channelBasis" in APP
    assert "marking.channelBasis, marking.activeChannelsByPrototype" in APP
    assert "channelBasis = sectionModel.axes" in APP
    assert "activeChannelsByPrototype = sectionModel.activeChannelsByPrototype" in APP
    assert "row.length === Number(marking.config.channels)" in APP
    assert "marking.channelBasis.every((axis)" in APP


def test_portfolio_audit_is_visible_and_receipted_without_geometry_or_target_use():
    assert 'id="markingPortfolioState"' in HTML
    assert 'id="markingPortfolioRows"' in HTML
    assert ".marking-portfolio-audit" in STYLE
    assert "function markingPortfolioReplayAudit()" in APP
    assert "sameCandidateGeometry: true" in APP
    assert "targetUsed: false" in APP
    assert "portfolioReplayAudit: markingPortfolioReplayAudit()" in APP
    assert "meanRankDisplacement" in APP


def test_build_212_release_labels_are_consistent():
    assert 'buildId: "20260826-216"' in APP
    assert 'app.js?v=20260826-216' in HTML
    assert "Build 212" in README
    assert "Build 212" in DOC


if __name__ == "__main__":
    test_saved_marking_replays_its_own_basis_and_mask()
    test_portfolio_audit_is_visible_and_receipted_without_geometry_or_target_use()
    test_build_212_release_labels_are_consistent()
    print("marking portfolio replay contract passed")
