#!/usr/bin/env python3
"""Contract for frozen-frontier geometric-physics weight interventions."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_policy_workbench_contract() -> None:
    assert 'buildId: "20260825-122"' in APP
    assert 'app.js?v=20260825-122' in HTML
    assert 'id="policyWorkbenchState"' in HTML
    assert 'id="policyWorkbenchReset"' in HTML
    assert "function buildPolicyWorkbench" in APP
    assert "function cyclePolicyWorkbenchTerm" in APP
    assert "function renderPolicyWorkbenchState" in APP
    assert "workbenchCandidates" in APP
    assert "workbenchMultipliers" in APP
    assert 'throw new Error("frozen-frontier workbench term vector does not reconcile with the active score")' in APP
    assert 'candidateSetChanged: false' in APP
    assert 'hardAdmissionChanged: false' in APP
    assert 'candidateGeometryChanged: false' in APP
    assert 'executed: false' in APP
    assert 'targetUsedToChooseMultipliers: false' in APP
    assert "counterfactual preview only · not executed" in APP
    assert ".policy-workbench-heading" in CSS
    assert "frozen-frontier hypothesis workbench" in README
    assert "never committed to growth" in README


if __name__ == "__main__":
    test_policy_workbench_contract()
    print("policy workbench contract passed")
