#!/usr/bin/env python3

from materials_gcts_selection_robustness import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.all_programs_retained
    assert result.all_clean_precision_above_99_percent
    assert result.all_clean_recall_above_99_percent
    assert all(not case.seed_replay_exact for case in result.retained_cases)
    assert result.iqc_vacancy_proposals == 1
    assert result.iqc_vacancy_selected_program == "internal_section_inflation"
    assert result.iqc_vacancy_clean_precision == 1.0
    assert result.iqc_vacancy_clean_recall == 1.0
    assert result.bounded_vacancy_fit
    assert result.defect_crystal_selected_program == "translation_quotient"
    assert not result.defect_crystal_seed_replay_exact
    assert result.amorphous_false_positives == 0
    print("recursive selection robustness: passed")


if __name__ == "__main__":
    main()
