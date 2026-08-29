#!/usr/bin/env python3
"""Static contract for the published Cd–Yb interactive evidence ladder."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_cdyb_evidence_ladder_contract():
    assert 'transfer: "published Cd–Yb · sealed finite continuation"' in APP
    assert "waves: [3, 18, 9, 35, 7]" in APP
    assert 'exact: "177 / 179 emitted coordinates match"' in APP
    assert 'safe: "held-out active types 53→20→8→2' in APP
    assert 'rejected: "independent seed: 0 complete L1 macros · only 6 / 82 partial completions exact"' in APP
    assert 'similarity: "zero common exact three-scale production keys · stationary/exponential red"' in APP

    assert '["Complete train cover", "2,385 / 2,385 atoms"' in ATLAS
    assert '["Frozen held-out hierarchy", "53/92→20/26→8/8→2/2"' in ATLAS
    assert '["Seed-only hierarchy", "276 primitive · 0 complete L1"' in ATLAS
    assert '["Partial promoted frontier", "82 candidates · 6 exact"' in ATLAS
    assert '["Preregistered confirmation", "7 waves · 247 / 2,217 shell atoms"' in ATLAS
    assert '["Site-resolved section", "207 / 211 · P 98.10%"' in ATLAS
    assert '["Stationary audit", "0 three-scale keys"' in ATLAS
    assert '["Inspect per-cluster GCTS sections", "cdyb", 3]' in ATLAS
    assert '["Run the live finite frontier", "cdyb", 4]' in ATLAS

    assert "generic frozen connection evidence" in HTML
    assert 'evidence-atlas.js?v=20260829-328' in HTML
    assert 'app.js?v=20260829-328' in HTML
    assert 'style.css?v=20260829-328' in HTML
    assert 'buildId: "20260829-328"' in APP
    assert "Build 308 · published Cd–Yb evidence ladder" in README


if __name__ == "__main__":
    test_cdyb_evidence_ladder_contract()
    print("Cd–Yb evidence ladder contract: passed")
