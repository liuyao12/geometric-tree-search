#!/usr/bin/env python3
"""Published Cd--Yb nested-window transfer gate for the current GCTS engine.

The cut-and-project generator is an external oracle: it creates the sealed
windows, but none of its lattice coordinates, occupation domains, source-site
labels, or phase name is passed to the learner.  The initial adapter is
deliberately conservative.  It records what the current generic local-cover
and recursive-program discovery can infer, then emits no unsupported sites.
Consequently this benchmark is expected to remain red until a genuinely
generic irregular-cover/oriented-port learner transfers to both held-out
annuli.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_oracle import CdYbAtoms, SOURCE, generate_cdyb
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_nested_transfer_benchmark import (
    FittedProgram, GrowthTrace, NestedCropSplit, ProgramAudit,
    TransferThresholds, evaluate_nested_transfer)
from materials_gcts_recursive_connections import point_key
from materials_gcts_recursive_program import discover_recursive_program_candidates
from materials_pointset_clusters import learn_cluster_candidates


@dataclass(frozen=True)
class CurrentGenericProgram:
    """Compact record of the train-only hypotheses admitted by today's engine."""

    seed_sites: tuple[tuple[tuple[float, float, float], str], ...]
    local_cluster_types: int
    recurring_occurrences: int
    residual_singleton_types: tuple[str, ...]
    recursive_candidates: tuple[str, ...]


def _configuration(
    name: str, atoms: CdYbAtoms, origin: tuple[float, float, float],
    radius: float,
) -> AtomicConfiguration:
    selected = tuple(
        (point, species) for point, species in zip(atoms.positions, atoms.symbols)
        if math.dist(origin, point) <= radius + 1e-10)
    return AtomicConfiguration(
        name,
        tuple(point for point, _ in selected),
        tuple(species for _, species in selected),
        provenance=(
            f"fixed radial restriction of DOI {SOURCE['archive_doi']}; "
            "oracle construction withheld from learner"),
    )


def build_cdyb_split(
    *, max_index: int = 4, box_size: float = 60.0,
    origin: tuple[float, float, float] = (3.1, 5.7, 8.2),
    radii: tuple[float, float, float] = (14.0, 18.0, 21.0),
) -> NestedCropSplit:
    """Generate nonsymmetric nested crops (506/1,056/1,672 by default).

    The predeclared generic origin avoids turning the icosahedral fixed point's
    global rotation orbits into apparent independent motif repetitions.
    """
    atoms = generate_cdyb(max_index, (box_size,) * 3)
    crops = tuple(_configuration(label, atoms, origin, radius)
                  for label, radius in zip(
                      ("Cd5.7Yb-offcenter-seed",
                       "Cd5.7Yb-offcenter-validation",
                       "Cd5.7Yb-offcenter-test"), radii))
    outer_records = CdYbAtoms(
        crops[-1].species, crops[-1].positions,
        tuple("withheld" for _ in crops[-1].positions))
    return NestedCropSplit(
        crops[0], crops[1], crops[2], origin, radii,
        outer_records.canonical_sha256())


def fit_current_generic(seed: AtomicConfiguration) -> FittedProgram[CurrentGenericProgram]:
    """Fit only APIs that accept an unlabeled colored point configuration."""
    local = learn_cluster_candidates(
        seed.species, seed.positions, neighbor_count=12,
        descriptor_tolerance=1e-5, minimum_occurrences=2)
    covered = {atom for occurrence in local.occurrences
               for atom in occurrence.member_indices}
    residual_species = tuple(sorted({seed.species[index]
                                     for index in range(len(seed.positions))
                                     if index not in covered}))
    candidates = discover_recursive_program_candidates(seed)
    program = CurrentGenericProgram(
        tuple(sorted((point_key(point), species)
                     for point, species in zip(seed.positions, seed.species))),
        len(local.cluster_types), len(local.occurrences), residual_species,
        tuple(candidate.program.family for candidate in candidates))
    # Every missed site is retained as an explicit residual singleton.  This
    # makes cover accounting exact without pretending those literal terminals
    # are a useful recursive grammar.
    audit = ProgramAudit(
        len(seed.positions), len(seed.positions), len(local.cluster_types),
        len(residual_species), 0, 0, True, False, False)
    return FittedProgram(program, audit)


def grow_current_generic(
    program: CurrentGenericProgram, seed: AtomicConfiguration,
    origin: tuple[float, float, float], radius: float, marked: bool,
) -> GrowthTrace:
    """Refuse to hallucinate when the frozen vocabulary has no growth rule."""
    del origin, radius, marked
    seed_sites = frozenset((point_key(point), species)
                           for point, species in zip(seed.positions, seed.species))
    if seed_sites != frozenset(program.seed_sites):
        raise ValueError("growth seed differs from the fitted configuration")
    return GrowthTrace(seed_sites, 0, 0, 0, 0)


def serialize_current_generic(program: CurrentGenericProgram) -> bytes:
    return json.dumps(asdict(program), sort_keys=True,
                      separators=(",", ":")).encode()


def evaluate(
    *, max_index: int = 4, box_size: float = 60.0,
    origin: tuple[float, float, float] = (3.1, 5.7, 8.2),
    radii: tuple[float, float, float] = (14.0, 18.0, 21.0),
):
    split = build_cdyb_split(
        max_index=max_index, box_size=box_size, origin=origin, radii=radii)
    return evaluate_nested_transfer(
        split, fit_current_generic, grow_current_generic,
        serialize_current_generic, TransferThresholds(matching_tolerance=.15))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
