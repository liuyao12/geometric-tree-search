#!/usr/bin/env python3
"""Portal contract for the exploratory group-sealed Cd--Yb site selector."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BACKEND = (ROOT / "scripts/materials_gcts_cdyb_site_resolved_completion_section.py").read_text()
EXECUTION = (ROOT / "scripts/materials_gcts_cdyb_group_sealed_site_mask_execution.py").read_text()
SPATIAL = (ROOT / "scripts/materials_gcts_cdyb_obligation_spatial_transfer.py").read_text()
COVERAGE = (ROOT / "scripts/materials_gcts_cdyb_candidate_supply_coverage_audit.py").read_text()


def test_cdyb_site_section_portal_contract() -> None:
    assert "def _group_refit_zero_error_audit(rows):" in BACKEND
    assert "math.nextafter(max(negative_scores), 1.)" in BACKEND
    assert '"nextafter-maximum-fitted-negative-by-original-window"' in BACKEND
    assert "group_refit_rule_selected_after_current_corpus_was_seen" in BACKEND
    assert "group_refit_rule_exploratory_not_confirmatory=True" in BACKEND
    assert "future_confirmatory_target_opened=False" in BACKEND
    assert "group_refit_selector_passed" in BACKEND
    assert "value >= group_refit[\"correct\"]" in BACKEND
    assert "execute_partial_completion_site_masks" in EXECUTION
    assert "execute_partial_completion_sections" in EXECUTION
    assert "future_confirmatory_target_opened: bool" in EXECUTION
    assert "vocabulary is shared across the five training windows" in EXECUTION
    assert "minimum_marking_score=obligation_threshold" in SPATIAL
    assert "reserved_windows_previously_consumed_by_reencoding" in SPATIAL
    assert "not fresh confirmation" in SPATIAL
    assert "COVERAGE_OPTIONS = (1 / 3, 1 / 2)" in COVERAGE
    assert "primitive_fallback_has_exact_supply" in COVERAGE
    assert "selected.zero_wrong_action_gate" in COVERAGE
    assert "selected_zero < baseline_zero_reserves" in COVERAGE

    for statement in (
        "207 / 211 correct sites",
        "98.10% precision",
        "23.77% recall",
        "minimum fold precision is 95.92%",
        "best shuffled refit retains only 21 correct sites",
        "future untouched nucleus",
        "strict per-site arm commits 9 / 74 first-wave obligations (8 correct)",
        "commits 16 complete port-witnessed children",
        "emits 146 / 146 correct sites",
        "genuine child-driven later waves in two of five",
        "default Cd–Yb policy remains disabled",
        "executes 4 → 4 → 3 complete sections across three waves",
        "81 / 81 correct sites and 11 promoted parents",
        "zero retained macro-anchor types",
        "not fresh confirmation",
        "one wrong held-development action and ten wrong sites",
        "overlap zero retained macro-anchor types",
        "204 exact among 345 target-blind primitive candidates",
        "promotion/anchor coverage",
    ):
        assert statement in HTML
    assert '["site calibration", "207 / 211 nested"]' in ATLAS
    assert '["obligation closure", "16 parents · 146 / 146"]' in ATLAS
    assert '["spatial reserve", "81 / 81 · 11 parents"]' in ATLAS
    assert '["Site-resolved section", "207 / 211 · P 98.10%"' in ATLAS
    assert '["Group-sealed obligation execution", "146 / 146 sites · 16 parents"' in ATLAS
    assert '["Consumed spatial transfer", "81 / 81 sites · 11 parents"' in ATLAS
    assert '["Candidate-supply diagnosis", "0 anchor types · 204 / 345 exact primitive"' in ATLAS
    assert "future untouched confirmation remains sealed" in ATLAS
    assert 'closureFunnel: {' in ATLAS
    assert '["isolated-site arm", 9' in ATLAS
    assert '["development children", 16' in ATLAS
    assert '["development sites", 146' in ATLAS
    assert '["development parents", 16' in ATLAS
    assert '["reserved sites", 81' in ATLAS
    assert '["reserved parents", 11' in ATLAS
    assert 'id="systemClosureFunnel"' in HTML
    assert 'id="closureFunnelSteps"' in HTML
    assert 'button.dataset.closureStep' in ATLAS
    assert 'id="systemSupplyAudit"' in HTML
    assert 'id="supplyAuditTabs"' in HTML
    assert 'id="supplyAuditStages"' in HTML
    assert 'supplyAudit: {' in ATLAS
    assert 'reserve A · anchor-starved' in ATLAS
    assert 'reserve B · executable' in ATLAS
    assert 'primitive: { exact: 204, total: 345, sites: 292 }' in ATLAS
    assert 'button.dataset.supplyReserve' in ATLAS
    assert 'button.dataset.supplyStage' in ATLAS
    assert "Build 316 · candidate supply versus marking value" in README
    assert "32 exact occurrences spanning 17" in README
    assert "204 exact actions" in README
    assert "Build 315 · spatial transfer of whole-child value" in README
    assert "One reserve has no candidate supply" in README
    assert "81 / 81" in README
    assert "11 children" in README
    assert "16 complete port-witnessed children" in README
    assert "146 / 146 correct emitted" in README
    assert "outer recall is only 0.39%" in README
    assert "exploratory training-corpus result" in README
    assert "older fully nested margin *selection* remains red at 94.48%" in README
    assert 'buildId: "20260901-412"' in APP
    assert 'app.js?v=20260901-412' in HTML
    assert 'style.css?v=20260901-412' in HTML
    assert 'evidence-atlas.js?v=20260901-412' in HTML


if __name__ == "__main__":
    test_cdyb_site_section_portal_contract()
    print("CdYb group-sealed site-section portal contract: passed")
