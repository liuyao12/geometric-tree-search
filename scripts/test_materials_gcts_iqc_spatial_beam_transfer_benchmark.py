#!/usr/bin/env python3
import math

from materials_gcts_frontier_attachment_benchmark import (
    IterativeGrowthWave, RegenerativeGrowthTrace,
    score_regenerative_growth)


def test_posthoc_scorer_keeps_execution_sealed_and_species_aware():
    raw = (
        IterativeGrowthWave(1, 2, -1, -1, 2, math.nan, math.nan, .9, 10),
        IterativeGrowthWave(2, 1, -1, -1, 3, math.nan, math.nan, .8, 12),
    )
    traces = (
        RegenerativeGrowthTrace(1, ((1., 0., 0.), (2., 0., 0.)),
                                ("A", "B")),
        RegenerativeGrowthTrace(2, ((3., 0., 0.),), ("A",)),
    )
    scored = score_regenerative_growth(
        raw, traces, ((0., 0., 0.),),
        ((0., 0., 0.), (1., 0., 0.), (2., 0., 0.), (3., 0., 0.)),
        ("A", "A", "A", "A"))
    assert [(row.true_sites, row.false_sites) for row in scored] == [
        (1, 1), (1, 0)]
    assert scored[-1].cumulative_precision == 2 / 3
    assert scored[-1].cumulative_novel_coverage == 2 / 3


if __name__ == "__main__":
    test_posthoc_scorer_keeps_execution_sealed_and_species_aware()
    print("spatial IQC beam transfer tests: passed")
