#!/usr/bin/env python3

from materials_gcts_generic_overlap import (
    run_null_control,
    run_perturbed_suite,
    run_suite,
)


def main() -> None:
    results = run_suite()
    assert len(results) >= 6 * 5
    assert all(result.consistent for result in results)
    assert all(result.compact_grammar for result in results)
    assert all(result.true_assignment_admitted for result in results)
    assert all(result.overlap_accuracy == 1.0 for result in results)
    assert all(result.overlap_forced == result.hidden_atoms for result in results)
    assert sum(result.overlap_forced for result in results) >= sum(
        result.geometry_baseline_forced for result in results)
    assert sum(result.overlap_accuracy * result.hidden_atoms for result in results) > sum(
        result.geometry_map_accuracy * result.hidden_atoms for result in results)
    assert sum(result.overlap_accuracy * result.hidden_atoms for result in results) > sum(
        result.pairwise_markov_accuracy * result.hidden_atoms for result in results)
    assert all(result.hybrid_markov_accuracy == result.overlap_accuracy
               for result in results)
    null_results = run_null_control()
    assert all(not result.compact_grammar for result in null_results)
    assert min(result.learned_patterns for result in null_results) > max(
        result.learned_patterns for result in results)
    perturbed = run_perturbed_suite()
    assert all(result.compact_grammar for result in perturbed)
    assert all(result.consistent and result.true_assignment_admitted
               for result in perturbed)
    assert all(result.overlap_forced == result.hidden_atoms for result in perturbed)
    assert all(result.overlap_accuracy == 1.0 for result in perturbed)
    assert sum(result.overlap_accuracy * result.hidden_atoms
               for result in perturbed) > sum(
        result.hybrid_markov_accuracy * result.hidden_atoms
        for result in perturbed)
    print("generic overlap GCTS: all assertions passed")
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
