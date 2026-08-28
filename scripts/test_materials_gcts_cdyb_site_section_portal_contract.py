#!/usr/bin/env python3
"""Portal contract for the exploratory group-sealed Cd--Yb site selector."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BACKEND = (ROOT / "scripts/materials_gcts_cdyb_site_resolved_completion_section.py").read_text()


def test_cdyb_site_section_portal_contract() -> None:
    assert "def _group_refit_zero_error_audit(rows):" in BACKEND
    assert "math.nextafter(max(negative_scores), 1.)" in BACKEND
    assert '"nextafter-maximum-fitted-negative-by-original-window"' in BACKEND
    assert "group_refit_rule_selected_after_current_corpus_was_seen" in BACKEND
    assert "group_refit_rule_exploratory_not_confirmatory=True" in BACKEND
    assert "future_confirmatory_target_opened=False" in BACKEND
    assert "group_refit_selector_passed" in BACKEND
    assert "value >= group_refit[\"correct\"]" in BACKEND

    for statement in (
        "207 / 211 correct sites",
        "98.10% precision",
        "23.77% recall",
        "minimum fold precision is 95.92%",
        "best shuffled refit retains only 21 correct sites",
        "future untouched nucleus",
        "Cd–Yb deployment remains disabled",
        "no new evaluation target has been opened",
    ):
        assert statement in HTML
    assert '["site calibration", "207 / 211 nested"]' in ATLAS
    assert '["Site-resolved section", "207 / 211 · P 98.10%"' in ATLAS
    assert "future untouched confirmation remains sealed" in ATLAS
    assert "Build 311 · group-sealed Cd–Yb site calibration" in README
    assert "exploratory training-corpus result" in README
    assert "older fully nested margin *selection* remains red at 94.48%" in README
    assert 'buildId: "20260828-311"' in APP
    assert 'app.js?v=20260828-311' in HTML
    assert 'style.css?v=20260828-311' in HTML
    assert 'evidence-atlas.js?v=20260828-311' in HTML


if __name__ == "__main__":
    test_cdyb_site_section_portal_contract()
    print("CdYb group-sealed site-section portal contract: passed")
