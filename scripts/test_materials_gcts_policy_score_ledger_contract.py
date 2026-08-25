#!/usr/bin/env python3
"""Source contract for the exact, signed material-growth score ledger."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_score_ledger_contract() -> None:
    assert 'buildId: "20260825-118"' in APP
    assert 'app.js?v=20260825-118' in HTML
    assert 'id="policyScoreLedger"' in HTML
    assert 'id="policyScoreLedgerState"' in HTML
    assert ".policy-score-term" in CSS
    assert ".policy-score-bar i.positive" in CSS
    assert ".policy-score-bar i.negative" in CSS
    assert "function activeCandidateScoreTerms" in APP
    assert "function policyScoreTerms" in APP
    assert "function renderPolicyScoreLedger" in APP
    assert "scoreTermTotal" in APP
    assert "scoreDecompositionExact" in APP
    assert "everyScoreDecompositionExact" in APP
    assert 'throw new Error("growth-policy score ledger does not reconcile with the ranking score")' in APP
    for term in (
        "grammar-priority", "known-window-gain", "geometric-strain", "composition",
        "formal-charge", "surface", "attachment", "habit", "coherency", "front",
        "capillary", "epitaxy", "drive", "thermal", "loop", "arrival", "exposure",
        "exploration",
    ):
        assert f'scoreTerm("{term}"' in APP
    assert "Not supersaturation or thermodynamic driving force." in APP
    assert "not commensurate\nphysical energies" in README
    assert "same frozen candidate set" in README


if __name__ == "__main__":
    test_score_ledger_contract()
    print("policy score ledger contract passed")
