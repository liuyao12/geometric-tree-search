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
        ('from "../../assets/a2-layered-size8-candidates.js?v=20260827-2"', "generated candidate import"),
        ('short: "A₂ size 8"', "A2 system"),
        ('["layer-essential census", "4,940"]', "exact census"),
        ('["Claim boundary", "4 unresolved"', "classification boundary"),
        ('curveNote: "4,940 → 411 → 6 → 4 · zero solver unknowns"', "curve semantics"),
        ('function renderA2Candidate(', "candidate interaction"),
        ('function a2CandidateSvg(', "cell-support drawing"),
        ('Larger domains and more general grammars keep the classification <b>unresolved</b>', "per-candidate boundary"),
        ('Exact A₂ layer-essential screening', "claim ledger progress entry"),
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
    require(root_html, "Four size-eight candidates remain exact through seven copies",
            "root-level current A2 classification")
    require(root_html, './evidence-atlas.js?v=20260827-24', "root-level atlas cache version")

    asset_text = (ROOT / "assets" / "a2-layered-size8-candidates.js").read_text()
    payload = asset_text.split("Object.freeze(", 1)[1].rsplit(");", 1)[0]
    candidates = json.loads(payload)
    assert [candidate["id"] for candidate in candidates] == [
        "a2lp_8_02131", "a2lp_8_02151", "a2lp_8_03411", "a2lp_8_04836"
    ]
    assert [candidate["screening"]["corona_root_patch_copies"] for candidate in candidates] == [24, 29, 30, 27]
    assert [candidate["screening"]["corona2_gcts_sound_clauses"] for candidate in candidates] == [16, 72, 72, 62]
    assert [candidate["screening"]["periodic_seven_copy_exact_multicover_nodes"]
            for candidate in candidates] == [29338463, 74819710, 74782180, 29328075]
    assert [candidate["screening"]["periodic_seven_copy_mitm_fallbacks"]
            for candidate in candidates] == [0, 32, 32, 0]
    for candidate in candidates:
        screen = candidate["screening"]
        assert len(candidate["cells"]) == 8
        assert candidate["morphology"]["layer_essential"] is True
        assert screen["source_pool_size"] == 4940
        assert screen["periodic_one_copy_certificates"] == 4529
        assert screen["periodic_two_copy_certificates_after_one_copy_screen"] == 405
        assert screen["periodic_four_copy_certificates_after_three_copy_screen"] == 2
        assert screen["periodic_exact_through"] == 7
        assert screen["periodic_hnf_bases_exhausted_by_copies"]["7"] == 1995
        assert screen["periodic_seven_copy_exact_multicover_nodes"] > 0
        assert screen["periodic_seven_copy_complete"] is True
        assert screen["periodic_solver_unknowns"] == 0
        assert screen["corona_completed_verified"] is True
        assert screen["corona2_gcts_outer_exhausted"] is False
        assert screen["direct_scalar_substitution_scales_exhausted"] == list(range(2, 9))
        assert screen["direct_layer_scale_pairs_exhausted"] == 49
        assert screen["two_copy_metatile_substitution_scales_exhausted"] == [2, 3]
        assert screen["three_copy_metatile_substitution_scales_exhausted"] == [2, 3]

    print("A2 evidence atlas contract: passed")


if __name__ == "__main__":
    main()
