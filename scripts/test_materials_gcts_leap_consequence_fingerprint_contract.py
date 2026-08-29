#!/usr/bin/env python3
"""Contract for the leap-resolved material consequence fingerprint."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_consequence_fingerprint_is_interactive_and_multiscale():
    for element_id in (
        "leapConsequenceLab",
        "leapConsequenceState",
        "leapConsequenceFilters",
        "leapConsequenceComponents",
        "leapConsequenceMatrix",
        "leapConsequenceDetail",
        "leapConsequenceBoundary",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    for group in ("all", "local", "mesoscale", "chemistry", "reciprocal"):
        assert f'data-consequence-filter="{group}"' in HTML
    for component in ("total", "attachment", "settling"):
        assert f'data-consequence-component="{component}"' in HTML
    for metric_id in (
        "atoms", "composition", "feedstock", "coordination", "local-order",
        "centrosymmetry", "radius", "anisotropy", "interface", "reciprocal",
        "packing", "radial-composition", "void-clearance", "void-network", "void-throat", "void-steric",
    ):
        assert f'id: "{metric_id}"' in APP
    assert "function renderLeapConsequence" in APP
    assert "renderLeapConsequence(selected);" in APP
    assert ".leap-consequence-matrix" in CSS
    assert ".leap-consequence-components" in CSS
    assert ".consequence-track" in CSS


def test_composition_is_retained_as_state_not_action_score():
    assert "function structuralCompositionSnapshot" in APP
    assert "compositionDrift(species, compositionTarget)" in APP
    assert APP.count("composition: structuralCompositionSnapshot()") >= 6
    for field in (
        "totalVariationFromObservedTarget",
        "targetDerivedFromObservedConfiguration",
        "chemicalPotentialInferred: false",
        "phaseEquilibriumInferred: false",
        "physicalTimeIntegrated: false",
    ):
        assert field in APP


def test_claim_boundary_forbids_dynamical_overinterpretation():
    for phrase in (
        "independently scaled",
        "not MD, force integration, energy minimization, kinetics, or physical time",
        "not experimental diffraction intensity",
        "not chemical potential, phase equilibrium",
    ):
        assert phrase in APP
    assert "Each row compares two certified structural states" in HTML


def test_current_build_is_exposed():
    assert 'buildId: "20260828-321"' in APP
    assert 'app.js?v=20260828-321' in HTML
    assert 'style.css?v=20260828-321' in HTML


def test_as_placed_checkpoint_precedes_projection_and_is_retained():
    checkpoint = APP.index("const asPlaced = currentLeapOutcomeSnapshot")
    projection = APP.index("const relaxation = projectAcceptedBatchGeometry", checkpoint)
    receipt = APP.index("asPlaced,", projection)
    assert checkpoint < projection < receipt
    assert "resolveLeapConsequenceComparison" in APP
    assert "selectedLeapConsequenceComponent" in APP
    assert APP.count("asPlaced: leap.asPlaced || null") == 2
    assert 'offLatticeCheckpointSchema: ["before", "asPlaced", "after"]' in APP
    assert "decomposedOffLatticeEvents" in APP


def test_dimensionless_jump_vector_and_unknown_dynamics_are_receipted():
    for element_id in (
        "leapConsequenceVectorState", "leapConsequenceVector",
        "leapConsequenceUnknowns", "leapConsequenceBridge",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "buildDimensionlessLeapConsequence" in APP
    assert APP.count("consequenceFingerprint: leap.consequenceFingerprint || null") == 2
    assert "renderLeapConsequenceVector(consequenceFingerprint)" in APP
    for phrase in (
        "axes are never summed into an energy or favorability score",
        "Intermediate configurations, physical duration, and path likelihood are not represented",
    ):
        assert phrase in APP or phrase in (ROOT / "apps/iqc-growth-live/leap-structural-consequence.mjs").read_text()
    assert ".leap-consequence-vector-lab" in CSS


if __name__ == "__main__":
    test_consequence_fingerprint_is_interactive_and_multiscale()
    test_composition_is_retained_as_state_not_action_score()
    test_claim_boundary_forbids_dynamical_overinterpretation()
    test_current_build_is_exposed()
    test_as_placed_checkpoint_precedes_projection_and_is_retained()
    test_dimensionless_jump_vector_and_unknown_dynamics_are_receipted()
    print("leap consequence fingerprint contract passed")
