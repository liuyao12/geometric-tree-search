#!/usr/bin/env python3

from materials_gcts_model_selection_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.competing_hypothesis_case_present
    assert result.amorphous_proposals == 0
    assert not result.phase_label_used
    fibonacci = result.cases[2]
    assert fibonacci.proposed_programs == (
        "substitution_product", "translation_quotient")
    assert fibonacci.proposal_scores[0] < fibonacci.proposal_scores[1]
    assert fibonacci.winning_margin is not None
    assert fibonacci.winning_margin > .7
    print("recursive model-selection benchmark: passed")


if __name__ == "__main__":
    main()
