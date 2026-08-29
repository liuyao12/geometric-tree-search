#!/usr/bin/env python3
"""Static contract for Build 287's same-as-placed settling sensitivity."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, fragment


def test_same_as_placed_ladder_is_visible_and_interactive():
    for element_id in (
        "settlingSensitivityLab", "settlingSensitivityState",
        "settlingSensitivityArms", "settlingSensitivityDetail",
        "settlingSensitivityBoundary",
    ):
        require(f'id="{element_id}"', HTML)
        require(f'$("{element_id}")')
    require("function renderSettlingSensitivity")
    require("dataset.settlingSensitivityMode", APP)
    require(".settling-sensitivity-arms", CSS)


def test_counterfactuals_share_state_and_neighborhood_and_never_commit():
    require('const evaluated = ["gentle", "balanced", "strong"]')
    require("sameAsPlacedCheckpoint: true")
    require("sameFixedNeighborhood: true")
    require("candidateGeometryChanged: false")
    require("searchRerun: false")
    require("counterfactualsCommitted: false")
    require("targetUsed: false")
    require("physicalPotentialUsed: false")
    require("forceIntegrated: false")
    require("energyMinimized: false")
    require("physicalTimeModeled: false")
    require("STRUCTURAL_RELAXATION_MODES.strong.displacementFraction")
    require("maximumIterations: spec.iterations")
    require("arm.iterations}/${arm.maximumIterations} iter")


def test_preview_precedes_the_only_committed_projection_and_is_receipted():
    checkpoint = APP.index("const asPlaced = currentLeapOutcomeSnapshot")
    preview = APP.index("const settlingSensitivityPreview", checkpoint)
    selected = APP.index("const relaxation = projectAcceptedBatchGeometry", preview)
    finalized = APP.index("const settlingSensitivity = finalizeSettlingSensitivity", selected)
    receipt = APP.index("settlingSensitivity,", finalized)
    assert checkpoint < preview < selected < finalized < receipt
    assert APP.count("settlingSensitivity: leap.settlingSensitivity || null") == 2
    require("selectedExecutionMatchesPreview")


def test_material_fingerprint_is_virtual_downstream_and_coordinate_cache_is_fresh():
    require("function settlingMaterialFingerprint")
    require("compareSettlingMaterialFingerprints(materialBaseline, materialFingerprint)")
    require("materialSensitiveModes")
    require("materialChangedFields")
    require("settling sensitivity changed atom inventory or chemistry")
    require("atomCountInvariant: true")
    require("chemistryInvariant: true")
    require("coordinatesEmbedded: false")
    require("usedForAdmission: false")
    require("usedForRanking: false")
    require('`${pipelineStage}:${atoms.length}:${replayIndex}:${atomGeometryRevision}`')
    require("calculateLiveStructureForSource")


def test_claims_are_bounded_and_current_build_is_exposed():
    require("Build 290 · retained-leap settling robustness", README)
    require('buildId: "20260829-326"')
    require("not MD, energy, force integration, probability, kinetics, or time")


if __name__ == "__main__":
    test_same_as_placed_ladder_is_visible_and_interactive()
    test_counterfactuals_share_state_and_neighborhood_and_never_commit()
    test_preview_precedes_the_only_committed_projection_and_is_receipted()
    test_material_fingerprint_is_virtual_downstream_and_coordinate_cache_is_fresh()
    test_claims_are_bounded_and_current_build_is_exposed()
    print("settling sensitivity contract passed")
