#!/usr/bin/env python3
"""Train-calibrated overlap-consensus marking on a frozen IQC frontier.

The grammar and threshold see only a training crop.  Candidate generation on
either seed uses train-frozen prototypes and ports. Evaluation-shell atoms are
accepted only by the post-hoc scorer.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import random
from typing import Hashable, Sequence

from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import (
    _add, _classify, _pose_key, _render, _site_key)
from materials_gcts_oriented_overlap_ports import (
    expand_port_orbit, matmul, matvec)

SiteKey = tuple[str, int, int, int]


@dataclass(frozen=True)
class FrozenFrontierCandidate:
    candidate_id: int
    port_id: int
    overlap_atoms: int
    production_frequency: int
    emitted_sites: tuple[SiteKey, ...]


@dataclass(frozen=True)
class FrozenFrontier:
    candidates: tuple[FrozenFrontierCandidate, ...]
    emitted_site_universe: tuple[SiteKey, ...]
    seed_occurrences: int
    candidate_digest_payload: tuple[tuple[int, int, tuple[SiteKey, ...]], ...]


@dataclass(frozen=True)
class RankedSiteScore:
    proposals: int
    correct: int
    wrong: int
    precision: float
    recall: float
    backtracks: int = 0


@dataclass(frozen=True)
class ActionBatchScore:
    placements: int
    proposals_checked: int
    incompatible_backtracks: int
    correct_placements: int
    action_precision: float
    unique_emitted_atoms: int
    unique_correct_atoms: int
    unique_wrong_atoms: int
    emitted_site_precision: float
    recall: float


def _point_from_key(key: SiteKey, tolerance: float = .03):
    return tuple(value * tolerance for value in key[1:])


def boundary_censored_candidates(frontier: FrozenFrontier, center, radius,
                                 *, tolerance: float = .03):
    return tuple(candidate for candidate in frontier.candidates
                 if all(math.dist(_point_from_key(site, tolerance), center)
                        <= radius + tolerance for site in
                        candidate.emitted_sites))


def normalized_action_scores(candidates, site_support):
    maximum = max(site_support.values(), default=1)
    return {candidate.candidate_id: min(
        (site_support[site] / maximum for site in candidate.emitted_sites),
        default=0.0) for candidate in candidates}


def _compatible(candidate, occupied, *, tolerance: float = .03,
                exclusion_distance: float = .10):
    for site in candidate.emitted_sites:
        species, *coordinate_key = site
        point = tuple(value * tolerance for value in coordinate_key)
        for known_species, known_point in occupied.values():
            distance = math.dist(point, known_point)
            if distance <= tolerance:
                if known_species != species:
                    return False
            elif distance < exclusion_distance:
                return False
    return True


def compatible_batch(candidates, rank_scores, *, minimum_score=None,
                     maximum_placements=None, exclusion_distance=.10):
    ordered = sorted(candidates, key=lambda candidate: (
        -rank_scores[candidate.candidate_id], -candidate.overlap_atoms,
        -candidate.production_frequency, candidate.candidate_id))
    occupied = {}
    accepted = []
    checked = backtracks = 0
    for candidate in ordered:
        if (minimum_score is not None and
                rank_scores[candidate.candidate_id] + 1e-12 < minimum_score):
            continue
        if maximum_placements is not None and len(accepted) >= maximum_placements:
            break
        checked += 1
        if not _compatible(candidate, occupied,
                           exclusion_distance=exclusion_distance):
            backtracks += 1
            continue
        accepted.append(candidate)
        for site in candidate.emitted_sites:
            occupied.setdefault(site[1:],
                                (site[0], _point_from_key(site)))
    return tuple(accepted), checked, backtracks


def score_action_batch(batch, checked, backtracks, correct_sites,
                       shell_atoms):
    valid = sum(all(site in correct_sites for site in candidate.emitted_sites)
                for candidate in batch)
    emitted = {site for candidate in batch for site in candidate.emitted_sites}
    correct = len(emitted.intersection(correct_sites))
    return ActionBatchScore(
        len(batch), checked, backtracks, valid,
        valid / max(1, len(batch)), len(emitted), correct,
        len(emitted) - correct, correct / max(1, len(emitted)),
        correct / max(1, shell_atoms))


def calibrate_action_threshold(candidates, site_support, correct_sites,
                               shell_atoms, *, precision_gate=.95,
                               exclusion_distance=.10):
    scores = normalized_action_scores(candidates, site_support)
    ratios = sorted(set(scores.values()), reverse=True)
    choices = []
    for ratio in ratios:
        batch, checked, backtracks = compatible_batch(
            candidates, scores, minimum_score=ratio,
            exclusion_distance=exclusion_distance)
        result = score_action_batch(
            batch, checked, backtracks, correct_sites, shell_atoms)
        if result.action_precision >= precision_gate:
            choices.append((result.unique_correct_atoms, ratio,
                            -result.placements, result))
    if not choices:
        return 1.0, ActionBatchScore(0, 0, 0, 0, 0., 0, 0, 0, 0., 0.), False
    _, ratio, _, result = max(choices, key=lambda item: item[:3])
    return ratio, result, True


def candidate_incidence_scores(candidates):
    consensus = Counter()
    overlap = defaultdict(int)
    frequency = defaultdict(int)
    for candidate in candidates:
        for site in candidate.emitted_sites:
            consensus[site] += 1
            overlap[site] = max(overlap[site], candidate.overlap_atoms)
            frequency[site] = max(frequency[site],
                                  candidate.production_frequency)
    return consensus, overlap, frequency


def candidate_subfrontier(frontier, candidates):
    candidates = tuple(candidates)
    universe = tuple(sorted({site for candidate in candidates
                             for site in candidate.emitted_sites}))
    payload = tuple((item.candidate_id, item.port_id, item.emitted_sites)
                    for item in candidates)
    return FrozenFrontier(candidates, universe,
                          frontier.seed_occurrences, payload)


def crop(species, positions, center, radius):
    ids = tuple(index for index, point in enumerate(positions)
                if math.dist(point, center) <= radius + 1e-10)
    return (tuple(species[index] for index in ids),
            tuple(positions[index] for index in ids), ids)


def frozen_frontier(program, seed_species, seed_positions,
                    *, tolerance: float = .03) -> FrozenFrontier:
    enumeration = enumerate_frozen_port_occurrences(
        program, seed_species, seed_positions, select_greedy_cover=True)
    prototypes = {item.type_id: item for item in program.prototypes}
    occupied = tuple(zip(seed_species, seed_positions))
    exclusion = max(tolerance, program.cover.minimum_distance * .45)
    by_parent = defaultdict(list)
    for port_id, port in enumerate(program.atlas.ports):
        by_parent[port.parent_type].append((port_id, port))
    candidates = {}
    for parent in enumeration.occurrences:
        parent_prototype = prototypes[parent.type_id]
        for port_id, port in by_parent[parent.type_id]:
            child_prototype = prototypes[port.child_type]
            for relative_rotation, relative_translation in expand_port_orbit(
                    parent_prototype, child_prototype, port, tolerance):
                rotation = matmul(parent.rotation, relative_rotation)
                translation = _add(parent.translation,
                                   matvec(parent.rotation,
                                          relative_translation))
                pose = _pose_key(port.child_type, rotation, translation,
                                 tolerance)
                rendered = _render(child_prototype, rotation, translation)
                overlap, emitted, invalid = _classify(
                    rendered, occupied, tolerance, exclusion)
                if invalid or len(overlap) < len(port.overlap) or not emitted:
                    continue
                emitted_keys = tuple(sorted({_site_key(site, tolerance)
                                             for site in emitted}))
                rank = (-len(overlap), -port.observations,
                        port_id, emitted_keys)
                if pose not in candidates or rank < candidates[pose][0]:
                    candidates[pose] = rank, port_id, len(overlap), port, emitted_keys
    result = tuple(FrozenFrontierCandidate(
        index, value[1], value[2], value[3].observations, value[4])
                   for index, (_, value) in enumerate(sorted(
                       candidates.items(), key=lambda item: item[0])))
    universe = tuple(sorted({site for item in result
                             for site in item.emitted_sites}))
    payload = tuple((item.candidate_id, item.port_id, item.emitted_sites)
                    for item in result)
    return FrozenFrontier(result, universe, len(enumeration.occurrences), payload)


def incidence_scores(frontier: FrozenFrontier):
    consensus = Counter()
    overlap = defaultdict(int)
    frequency = defaultdict(int)
    for candidate in frontier.candidates:
        for site in candidate.emitted_sites:
            consensus[site] += 1
            overlap[site] = max(overlap[site], candidate.overlap_atoms)
            frequency[site] = max(frequency[site],
                                  candidate.production_frequency)
    return consensus, overlap, frequency


def choose_consensus_threshold(frontier: FrozenFrontier,
                               correct_sites: set[SiteKey]):
    consensus, _, _ = incidence_scores(frontier)
    choices = []
    for threshold in sorted(set(consensus.values())):
        proposed = {site for site, count in consensus.items()
                    if count >= threshold}
        correct = len(proposed.intersection(correct_sites))
        precision = correct / max(1, len(proposed))
        if precision >= .99:
            # Required lexicographic gate, then the simpler/higher threshold.
            choices.append((correct, threshold, -len(proposed)))
    if not choices:
        return max(consensus.values(), default=1), False
    correct, threshold, _ = max(choices)
    return threshold, True


def score_selected(selected: Sequence[SiteKey], correct_sites: set[SiteKey],
                   shell_atoms: int) -> RankedSiteScore:
    selected = tuple(selected)
    correct = len(set(selected).intersection(correct_sites))
    return RankedSiteScore(
        len(selected), correct, len(selected) - correct,
        correct / max(1, len(selected)), correct / max(1, shell_atoms), 0)


def threshold_selection(scores, threshold):
    return tuple(sorted(site for site, count in scores.items()
                        if count >= threshold))


def top_k_selection(scores, count):
    return tuple(site for site, _ in sorted(
        scores.items(), key=lambda item: (-item[1], item[0]))[:count])


def shuffled_incidence_consensus(frontier: FrozenFrontier, *, seed: int):
    """Preserve candidate IDs/degrees but destroy candidate-to-site support."""
    rng = random.Random(seed)
    universe = frontier.emitted_site_universe
    counts = Counter()
    for candidate in frontier.candidates:
        degree = min(len(candidate.emitted_sites), len(universe))
        for site in rng.sample(universe, degree):
            counts[site] += 1
    return counts


def shuffled_candidate_incidence(frontier: FrozenFrontier, *, seed: int):
    """Return degree-preserving synthetic incidence and its site support."""
    rng = random.Random(seed)
    universe = frontier.emitted_site_universe
    incidence = {}
    counts = Counter()
    for candidate in frontier.candidates:
        degree = min(len(candidate.emitted_sites), len(universe))
        sites = tuple(rng.sample(universe, degree))
        incidence[candidate.candidate_id] = sites
        counts.update(sites)
    return incidence, counts
