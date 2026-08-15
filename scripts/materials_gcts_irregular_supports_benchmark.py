#!/usr/bin/env python3
"""Cross-family benchmark for the cell-free irregular-support learner."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_supports import (
    enumerate_frozen_vocabulary, fit_frozen_vocabulary)
from materials_gcts_periodic_growth import replicate


@dataclass(frozen=True)
class IrregularSupportCase:
    system: str
    atoms: int
    species: int
    repeated_types: int
    merged_types: int
    repeated_occurrences: int
    largest_support: int
    repeated_coverage: float
    gap_types: int
    complete_cover: bool
    frozen_target_atoms: int
    frozen_occurrences: int
    frozen_core_coverage: float
    frozen_heldout_coverage: float


@dataclass(frozen=True)
class IrregularSupportBenchmark:
    cases: tuple[IrregularSupportCase, ...]


def _site(label, point):
    return label, tuple(round(value, 8) for value in point)


def _case(configuration: AtomicConfiguration,
          target: AtomicConfiguration) -> IrregularSupportCase:
    vocabulary, cover = fit_frozen_vocabulary(
        configuration.species, configuration.positions)
    repeated = tuple(item for item in cover.support_types if item.kind == "repeated")
    frozen = enumerate_frozen_vocabulary(
        vocabulary, target.species, target.positions)
    training_sites = {_site(label, point) for label, point in zip(
        configuration.species, configuration.positions)}
    core = tuple(index for index, (label, point) in enumerate(zip(
        target.species, target.positions)) if _site(label, point) in training_sites)
    core_set = set(core)
    heldout = tuple(index for index in range(len(target.positions))
                    if index not in core_set)
    return IrregularSupportCase(
        configuration.name, len(configuration.positions),
        len(set(configuration.species)), cover.repeated_type_count,
        sum(item.hierarchy_level > 0 for item in repeated),
        cover.repeated_occurrence_count,
        max((item.support_size for item in repeated), default=0),
        cover.repeated_coverage, cover.gap_type_count, cover.complete,
        len(target.positions), sum(len(group) for group in frozen.occurrences_by_type),
        frozen.coverage_of(core), frozen.coverage_of(heldout))


def evaluate() -> IrregularSupportBenchmark:
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    # Remove all supplied periodic metadata before learning.
    nacl_cloud = AtomicConfiguration(
        nacl.name, nacl.positions, nacl.species, provenance=nacl.provenance)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb_split = build_cdyb_split()
    configurations = (
        (nacl_cloud, replicate(nacl)),
        (iqc, iqc_target),
        (cdyb_split.training, cdyb_split.validation),
    )
    return IrregularSupportBenchmark(tuple(_case(training, target)
                                           for training, target in configurations))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
