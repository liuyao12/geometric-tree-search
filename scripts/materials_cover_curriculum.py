#!/usr/bin/env python3
"""Deterministic lattice-free curricula for learned cover policies.

Geometry is used only while constructing some benchmark cases.  Every public
case contains an :class:`OverlapCoverProblem` plus non-geometric provenance;
coordinates, rotations, unit cells, and lattice indices are deliberately not
retained.  A branch policy therefore sees exactly the same abstract covering
state that it will see inside GCTS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from materials_overlap_cover import Occurrence, OverlapCoverProblem
from materials_pointset_benchmarks import (
    crystalline_control,
    overlapping_motif_point_set,
)
from materials_pointset_clusters import learn_cluster_candidates


FAMILIES = (
    "rotated_crystal",
    "non_lattice_motifs",
    "delayed_conflict",
)


@dataclass(frozen=True)
class CoverFamilyMetadata:
    """Safe provenance kept beside a curriculum problem.

    ``parameters`` contains only integer complexity controls.  In particular,
    it never contains coordinates, a rotation, species, lattice sites, or
    planted occurrence supports.
    """

    case_id: str
    family: str
    split: str
    seed: int
    source_object_count: int
    candidate_count: int
    parameters: Tuple[Tuple[str, int], ...]
    policy_features: Tuple[str, ...] = (
        "cover_supports",
        "occurrence_costs",
        "pair_constraints",
        "marked_frontier_state",
    )


@dataclass(frozen=True)
class CoverCurriculumCase:
    problem: OverlapCoverProblem
    metadata: CoverFamilyMetadata


@dataclass(frozen=True)
class CoverCurriculum:
    train: Tuple[CoverCurriculumCase, ...]
    test: Tuple[CoverCurriculumCase, ...]

    @property
    def all_cases(self) -> Tuple[CoverCurriculumCase, ...]:
        return self.train + self.test


def _metadata(
    problem: OverlapCoverProblem,
    *,
    family: str,
    split: str,
    seed: int,
    ordinal: int,
    parameters: Mapping[str, int],
) -> CoverFamilyMetadata:
    return CoverFamilyMetadata(
        case_id=f"{split}-{family}-{ordinal:03d}-{seed}",
        family=family,
        split=split,
        seed=seed,
        source_object_count=len(problem.universe),
        candidate_count=len(problem.occurrences),
        parameters=tuple(sorted(parameters.items())),
    )


def _rotated_crystal_case(seed: int) -> OverlapCoverProblem:
    """Learn candidates from a randomly oriented finite crystal crop."""

    # shell_radius=2 has 33 sites: large enough to contain overlapping shells,
    # but small enough for an exact teacher to certify in a few dozen nodes.
    sample = crystalline_control(shell_radius=2, seed=seed)
    neighbor_count = 4 + seed % 3
    learned = learn_cluster_candidates(
        sample.species,
        sample.positions,
        neighbor_count=neighbor_count,
        descriptor_tolerance=1e-5,
    )
    occurrences = []
    for cluster_type in learned.cluster_types:
        for local_index, occurrence in enumerate(cluster_type.occurrences):
            occurrences.append(Occurrence(
                ("learned", cluster_type.type_id, local_index),
                occurrence.member_indices,
            ))
    # The sample (and all privileged generator metadata) dies here.  Only the
    # abstract incidence problem crosses the curriculum boundary.
    return OverlapCoverProblem(range(learned.point_count), tuple(occurrences))


def _non_lattice_motif_case(seed: int) -> OverlapCoverProblem:
    """Derive an overlapping cover from a random corner-sharing motif network."""

    motif_count = 4 + seed % 3
    sample = overlapping_motif_point_set(
        occurrence_count=motif_count,
        seed=seed,
    )
    occurrences = []
    for index, motif in enumerate(sample.motif_occurrences):
        support = motif.atom_indices
        occurrences.append(Occurrence(("motif", index), support, 1.0))
        # Two overlapping fragments make the choice nontrivial without leaking
        # a geometric descriptor.  Together they reproduce the full support at
        # a modestly higher cost than the reusable full motif.
        occurrences.append(Occurrence(
            ("fragment-a", index),
            (support[0], support[1], support[2]),
            0.62,
        ))
        occurrences.append(Occurrence(
            ("fragment-b", index),
            (support[0], support[3], support[4]),
            0.62,
        ))
    return OverlapCoverProblem(range(len(sample.positions)), tuple(occurrences))


def _delayed_conflict_case(seed: int) -> OverlapCoverProblem:
    """A tempting large placement fails only at the end of a tail.

    Greedy first selects ``tempting``.  It can then cover successive tail
    objects before discovering that the sole final placement conflicts with
    the initial choice.  Exact GCTS instead uses the two overlapping core
    placements and completes the tail.
    """

    core_size = 6 + 2 * (seed % 2)
    tail_size = 4 + seed % 3
    core = tuple(("core", index) for index in range(core_size))
    tail = tuple(("tail", index) for index in range(tail_size))
    gate = ("gate", 0)
    occurrences = [Occurrence("tempting", core)]
    midpoint = core_size // 2
    occurrences.extend((
        Occurrence("core-left", core[:midpoint] + (core[midpoint],)),
        Occurrence("core-right", (core[midpoint],) + core[midpoint + 1:]),
    ))
    # Consecutive placements overlap, so this is a cover rather than a
    # partition even away from the deliberately overlapping core split.
    for index in range(tail_size - 1):
        occurrences.append(Occurrence(
            ("tail-link", index), (tail[index], tail[index + 1])))
    # ``gate`` is private to the terminal placement.  The tempting branch can
    # make apparent progress through the entire visible tail before it becomes
    # impossible to cover this final object.
    occurrences.append(Occurrence("terminal", (tail[-1], gate)))
    return OverlapCoverProblem(
        core + tail + (gate,),
        tuple(occurrences),
        conflict_pairs=(("tempting", "terminal"),),
    )


def _make_case(
    family: str, split: str, seed: int, ordinal: int
) -> CoverCurriculumCase:
    if family == "rotated_crystal":
        problem = _rotated_crystal_case(seed)
        parameters = {"neighbor_count": 4 + seed % 3, "shell_radius": 2}
    elif family == "non_lattice_motifs":
        problem = _non_lattice_motif_case(seed)
        parameters = {"motif_count": 4 + seed % 3}
    elif family == "delayed_conflict":
        problem = _delayed_conflict_case(seed)
        parameters = {
            "core_size": 6 + 2 * (seed % 2),
            "tail_size": 4 + seed % 3,
        }
    else:
        raise ValueError(f"unknown curriculum family: {family!r}")
    return CoverCurriculumCase(
        problem,
        _metadata(
            problem,
            family=family,
            split=split,
            seed=seed,
            ordinal=ordinal,
            parameters=parameters,
        ),
    )


def build_cover_curriculum(
    *,
    base_seed: int = 20260805,
    train_per_family: int = 3,
    test_per_family: int = 2,
) -> CoverCurriculum:
    """Build disjoint deterministic train/test families.

    Split membership is arithmetic rather than random-library dependent.  Test
    seeds occupy a separate range, making accidental train/test duplication
    straightforward to audit.
    """

    if train_per_family < 1 or test_per_family < 1:
        raise ValueError("each split must contain at least one case per family")
    train = []
    test = []
    for family_index, family in enumerate(FAMILIES):
        family_seed = base_seed + 10_000 * family_index
        train.extend(
            _make_case(family, "train", family_seed + index, index)
            for index in range(train_per_family)
        )
        test.extend(
            _make_case(family, "test", family_seed + 5_000 + index, index)
            for index in range(test_per_family)
        )
    return CoverCurriculum(tuple(train), tuple(test))


__all__ = (
    "FAMILIES",
    "CoverCurriculum",
    "CoverCurriculumCase",
    "CoverFamilyMetadata",
    "build_cover_curriculum",
)
