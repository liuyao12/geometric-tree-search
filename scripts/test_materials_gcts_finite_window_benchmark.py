#!/usr/bin/env python3

from materials_gcts_finite_window_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.window_cases == 12
    assert result.all_programs_stable
    assert result.all_parameters_stable
    assert result.all_continuations_exact
    assert tuple(item.atom_range for item in result.families) == (
        (64, 512), (345, 919), (216, 1728), (470, 1130))
    print("finite-window recursive GCTS benchmark: passed")


if __name__ == "__main__":
    main()
