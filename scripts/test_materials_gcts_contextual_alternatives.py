#!/usr/bin/env python3

from materials_gcts_contextual_alternatives import evaluate


def test_existing_halo_does_not_fake_contextual_production_selection() -> None:
    result = evaluate()
    for case in (result.crystal, result.quasicrystal):
        assert case.heldout_occurrences >= 200
        assert case.known_context_fraction == 1.0
        assert case.oracle_seen_alternative_fraction > .99
        assert case.finite_vocabulary
        assert case.marked_context_accuracy == case.single_modal_accuracy
        assert case.original_halo_accuracy == case.single_modal_accuracy
        assert not case.benchmark_passed
    assert not result.both_markings_causal
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_existing_halo_does_not_fake_contextual_production_selection()
    print("context-marked production alternatives: honest red gate passed")
