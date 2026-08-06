#!/usr/bin/env python3

from materials_cover_value_benchmark import benchmark


def main() -> None:
    result = benchmark()
    assert result.training.cases == 6
    assert result.training.validation_cases == 3
    assert result.training.imitation_examples > 0
    assert result.training.descendant_outcomes > 0
    assert result.training.feasible_outcomes > 0
    assert result.training.improving_outcomes > 0
    assert len(result.held_out) == 6
    assert {row.family for row in result.held_out} == {
        "rotated_crystal", "non_lattice_motifs", "delayed_conflict"}
    assert all(row.optimum_cost > 0 for row in result.held_out)
    assert result.selection.selected_policy == "imitation"
    assert result.selection.imitation_validation_nodes < (
        result.selection.unguided_validation_nodes)
    assert result.selection.descendant_validation_nodes == (
        result.selection.imitation_validation_nodes)
    assert sum(row.imitation_nodes for row in result.held_out) <= sum(
        row.unguided_nodes for row in result.held_out)
    assert len(result.large_transfer) == 2
    assert all(row.atoms == 123 for row in result.large_transfer)
    assert result.large_transfer[0].node_budget == 50
    assert result.large_transfer[0].imitation_cost < (
        result.large_transfer[0].unguided_cost)
    assert all(not row.descendant_optimal for row in result.large_transfer)
    print("cover descendant-value benchmark: all assertions passed")
    print(result)


if __name__ == "__main__":
    main()
