"""Regression for the interactive molecular-ice evidence atlas."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def test_ice_evidence_is_executed_linked_and_claim_bounded() -> None:
    atlas = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")
    artifact = json.loads((APP_DIR / "ice-molecular-port-artifact.json").read_text(encoding="utf-8"))

    assert artifact["schema"] == "gcts-ice-molecular-port-artifact-v1"
    assert artifact["provenance"] == {
        "fit": "ice-Ih positions+species only",
        "trainingAtoms": 201,
        "trainingMolecules": 67,
        "trainingConnections": 99,
        "poseTolerance": 0.04,
        "targetUsed": False,
    }
    assert len(artifact["ports"]) == 8

    # The atlas executes the frozen artifact. Expected audit counts may verify
    # parity in the executor, but they must not be read as the plotted result.
    assert 'import { executeIceMolecularAnchorGrowth }' in atlas
    assert '[caseId, executeIceMolecularAnchorGrowth(ICE_PORT_ARTIFACT, caseId)]' in atlas
    assert "acceptedPerWave" in atlas
    assert ".expectedAcceptedAnchors" not in atlas

    assert 'short: "H₂O ice"' in atlas
    assert '["Ih isometry classes", "1 + 3 + 33"]' in atlas
    assert '["Ic isometry classes", "1 + 2 + 39"]' in atlas
    assert '["Complete molecular cover", "Ih 216 / 216 · Ic 192 / 192"' in atlas
    assert '"O anchors green · proton poses red"' in atlas
    assert '"no promoted ice rule"' in atlas
    assert '"finite fixed point"' in atlas
    assert '"Proton-resolved ice growth"' in atlas

    assert '["Inspect Ice Ih cover", "iceIh", 1]' in atlas
    assert '["Inspect ordered Ice VIII cover", "iceVIII", 1]' in atlas
    assert '["Inspect disordered Ice VI ambiguity", "iceVI", 1]' in atlas
    assert '["Verify Ice VI growth is withheld", "iceVI", 4]' in atlas
    assert '["Sample Ice VI and inspect D₂O clusters", "iceVI", 1, "resolve-ice-vi"]' in atlas
    assert '["Replay Ice Ih anchor trace", "iceIh", 4]' in atlas
    assert '["Replay Ih → Ic transfer", "iceIc", 4]' in atlas
    assert 'scenarioSelect.dispatchEvent(new Event("change"' in atlas
    assert 'stageButton.click()' in atlas

    assert 'id="atlasSystemActions"' in html
    assert "One question, five very different structures" in html
    assert 'evidence-atlas.js?v=20260824-8' in html
    assert ".atlas-system-actions" in css
    assert ".system-tabs { display: grid; grid-template-columns: repeat(5,1fr)" in css


if __name__ == "__main__":
    test_ice_evidence_is_executed_linked_and_claim_bounded()
    print("ice evidence atlas contract: passed")
