#!/usr/bin/env python3
"""Static/data contract for the dual A2 exact-geometry explorer."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "iqc-growth-live"
HTML = (APP / "index.html").read_text()
JS = (APP / "evidence-atlas.js").read_text()
CSS = (APP / "style.css").read_text()
README = (APP / "README.md").read_text()
ASSET = (ROOT / "assets" / "a2-sliced-size7-candidates.js").read_text()


def _asset_records():
    return json.loads(ASSET[ASSET.index("["):ASSET.rindex("]") + 1])


def test_generated_sliced_catalog_has_the_published_finite_audit():
    records = _asset_records()
    assert len(records) == 8
    assert all(len(item["alcoves"]) == 7 for item in records)
    assert all(item["screening"]["periodic_solver_unknowns"] == 0
               for item in records)
    assert all(item["screening"]["corona_completed_radius"] == 2
               and item["screening"]["corona_completed_verified"]
               for item in records)
    assert min(item["screening"]["radius_two_patch_copies"]
               for item in records) == 190
    assert max(item["screening"]["radius_two_patch_copies"]
               for item in records) == 252
    assert sum(item["screening"]["radius_three_failure_clauses"]
               for item in records) == 759
    assert sum(item["screening"]["radius_three_first_corona_clauses"]
               for item in records) == 731
    assert {item["screening"]["radius_three_status"]
            for item in records} == {"unresolved"}
    bounded = [item for item in records if
               item["screening"]["three_copy_metatile_scale3_reflected_status"] ==
               "no_three_copy_metatile_scalar3_substitution"]
    assert len(bounded) == 8
    assert sum(item["screening"]["three_copy_metatile_scale3_reflected_parent_types"]
               for item in bounded) == 12825
    assert len(records) - len(bounded) == 0
    bounded_scale4 = [item for item in records if
                      item["screening"]["three_copy_metatile_scale4_reflected_status"] ==
                      "no_three_copy_metatile_scalar4_substitution"]
    assert len(bounded_scale4) == 8
    assert sum(item["screening"]["three_copy_metatile_scale4_reflected_parent_types"]
               for item in bounded_scale4) == 12825
    bounded_four_copy = [item for item in records if
                         item["screening"]["four_copy_metatile_scale2_reflected_status"] ==
                         "no_four_copy_metatile_scalar2_substitution"]
    assert [item["id"] for item in bounded_four_copy] == ["a2sa_7_00120"]
    assert bounded_four_copy[0]["screening"]["four_copy_metatile_scale2_reflected_parent_types"] == 65110
    candidate_139 = next(item for item in records
                         if item["id"] == "a2sa_7_00139")
    screening = candidate_139["screening"]
    assert screening["three_copy_metatile_substitution_scales_exhausted"] == [2, 3, 4]
    assert screening["three_copy_metatile_scale3_reflected_parent_types"] == 1268
    assert screening["three_copy_metatile_scale3_reflected_status"] == \
        "no_three_copy_metatile_scalar3_substitution"


def test_portal_switches_catalogs_without_changing_claim_semantics():
    for token in (
            'data-a2-catalog="layered"', 'data-a2-catalog="sliced"',
            'id="a2ExplorerTitle"', 'id="a2ExplorerSummary"'):
        assert token in HTML
    for token in (
            "A2_SLICED_SIZE7_CANDIDATES", "const A2_CATALOGS",
            'activeA2Catalog = "layered"', "candidate.alcoves",
            "radius_three_failure_clauses", "radius_three_first_corona_clauses",
            "radius_three_stopped_by", "three_copy_metatile_scale3_reflected_parent_types",
            "A2_SLICED_SCALE3_OBSTRUCTIONS", "A2_SLICED_SCALE3_PARENT_COUNT",
            "A2_SLICED_SCALE4_OBSTRUCTIONS", "A2_SLICED_SCALE4_PARENT_COUNT",
            "A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS",
            "A2_SLICED_FOUR_COPY_SCALE2_PARENT_COUNT",
            "four_copy_metatile_scale2_reflected_parent_types",
            "candidate.screening.three_copy_metatile_scale3_reflected_status",
            "convexHull"):
        assert token in JS
    assert ".a2-catalog-tabs" in CSS
    assert "Build 317 · two exact A₂ geometry frontiers" in README
    assert "Build 318 · every live physics channel reaches the execution atlas" in README
    assert "does not thereby prove" not in JS  # no hidden upgrade of status
    assert "The candidate remains <b>unresolved</b>" in JS


if __name__ == "__main__":
    test_generated_sliced_catalog_has_the_published_finite_audit()
    test_portal_switches_catalogs_without_changing_claim_semantics()
    print("A2 dual-catalog portal contract: passed")
