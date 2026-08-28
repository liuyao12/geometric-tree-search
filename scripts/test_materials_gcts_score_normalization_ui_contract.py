from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_score_normalization_ui_contract():
    assert 'from "./score-normalization.mjs?v=20260828-301"' in APP
    assert 'buildId: "20260828-301"' in APP
    assert 'app.js?v=20260828-301' in HTML
    assert 'style.css?v=20260828-301' in HTML
    for token in ("policyNormalizationState", "policyNormalizationSelect", "policyNormalizationDetail"):
        assert token in APP and token in HTML
    assert "function renderPolicyNormalizationLedger(policy)" in APP
    assert "normalization: term.normalization" in APP
    assert ".policy-normalization-card" in CSS
    assert "## Build 301 · dimensional reduction ledger" in README


if __name__ == "__main__":
    test_score_normalization_ui_contract()
    print("score normalization UI contract passed")
