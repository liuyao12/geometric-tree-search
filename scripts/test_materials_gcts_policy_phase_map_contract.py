#!/usr/bin/env python3
"""Contract for the two-hypothesis frozen-frontier attachment-action map."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_phase_map_contract() -> None:
    assert 'buildId: "20260825-149"' in APP
    assert 'app.js?v=20260825-149' in HTML
    assert 'id="policyPhaseX"' in HTML
    assert 'id="policyPhaseY"' in HTML
    assert 'id="policyPhaseMap"' in HTML
    assert 'id="policyPhaseMapState"' in HTML
    assert "const POLICY_PHASE_LEVELS = [0, .5, 1, 1.5, 2]" in APP
    assert "function defaultPolicyPhaseAxes" in APP
    assert "function buildPolicyPhaseMap" in APP
    assert "function applyPolicyPhaseCell" in APP
    assert "function renderPolicyPhaseMap" in APP
    assert "two largest frozen-frontier contribution ranges excluding target-aware known-window replay; lexical tie break" in APP
    assert '.filter((term) => term.id !== "known-window-gain")' in APP
    assert "targetUsedToChooseAxes: false" in APP
    assert "selectedAxesIncludeReferenceGuidedTerm" in APP
    assert "rankingTargetUsed" in APP
    assert "candidateSetChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "executed: false" in APP
    assert "decisionPhaseMap" in APP
    assert "runnerUpMargin" in APP
    assert ".policy-phase-map" in CSS
    assert "growth decision phase map" in README
    assert "not an equilibrium phase diagram" in README


if __name__ == "__main__":
    test_policy_phase_map_contract()
    print("policy phase map contract passed")
