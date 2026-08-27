#!/usr/bin/env python3
"""Static/data contract for the interactive A2 exact-corona evidence view."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle}"


def main() -> None:
    atlas = (APP / "evidence-atlas.js").read_text()
    html = (APP / "index.html").read_text()
    root_html = (ROOT / "iqc-growth-live" / "index.html").read_text()
    css = (APP / "style.css").read_text()

    for needle, label in (
        ('from "../../assets/a2-layered-size7-candidates.js?v=20260827-4"', "generated candidate import"),
        ('short: "A₂ corona"', "A2 system"),
        ('["historical family blockers", "1,113"]', "exact blocker total"),
        ('["Claim boundary", "7 unresolved · 1 periodic"', "updated classification boundary"),
        ('curveNote: "exact counts · not a growth curve"', "curve semantics"),
        ('function renderA2Candidate(', "candidate interaction"),
        ('function a2CandidateSvg(', "cell-support drawing"),
        ('outer-corona remainder keeps the classification <b>unresolved</b>', "per-candidate boundary"),
        ('Exact A₂ obstruction learning', "claim ledger progress entry"),
        ('A₂ global classification', "claim ledger open entry"),
    ):
        require(atlas, needle, label)

    for needle, label in (
        ('id="a2CoronaExplorer"', "explorer region"),
        ('id="a2CandidateTabs"', "candidate selector"),
        ('id="a2BlockerBars"', "blocker comparison"),
        ('What it does not mean', "visible claim boundary"),
        ('id="atlasCurveEyebrow"', "dynamic curve semantics"),
    ):
        require(html, needle, label)

    require(css, ".a2-corona-explorer", "explorer styling")
    require(css, ".a2-candidate-shape", "candidate support styling")
    require(css, ".a2-blocker-bars", "comparison styling")
    require(root_html, '<base href="../apps/iqc-growth-live/">', "root-level asset base")
    require(root_html, "Seven unresolved candidates after one eight-copy periodic witness",
            "root-level current A2 classification")
    require(root_html, './evidence-atlas.js?v=20260827-22', "root-level atlas cache version")

    expected = {
        "a2lp_7_00128": (130, 7),
        "a2lp_7_00211": (136, 4),
        "a2lp_7_00232": (156, 12),
        "a2lp_7_00235": (131, 9),
        "a2lp_7_00694": (139, 7),
        "a2lp_7_00755": (142, 3),
        "a2lp_7_00777": (140, 6),
        "a2lp_7_00809": (139, 8),
    }
    records = {}
    for candidate_id, (expected_count, expected_core_size) in expected.items():
        path = ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-strengthened.ndjson"
        record = json.loads(path.read_text())
        assert record["corona2_core_classification"] == "unresolved"
        assert record["corona2_core_cegar"]["outer_exhausted"] is False
        assert record["corona2_core_cegar"]["rounds"] == 32
        count = len(record["corona2_core_cegar"]["clauses"])
        assert count == expected_count
        core = json.loads((
            ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-mincore.ndjson"
        ).read_text())
        assert core["classification"] == "sound_radius2_placement_obstruction"
        assert core["minimal"] is False
        assert core["final_replay"]["result"] == "unsat"
        assert len(core["reduced_outer_placement_indices"]) == expected_core_size
        records[candidate_id] = count
    assert sum(records.values()) == 1113

    print("A2 evidence atlas contract: passed")


if __name__ == "__main__":
    main()
