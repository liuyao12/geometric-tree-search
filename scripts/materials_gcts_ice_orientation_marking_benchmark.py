#!/usr/bin/env python3
"""Frozen local GCTS marking for mutually exclusive H2O pose domains.

Five spatially disjoint ice-Ih nuclei supply training labels.  The molecular
port grammar, bounded descriptor tables, and 31 within-domain shuffled controls
are frozen before three other target crops are opened.  The benchmark asks a
narrow but important question: after geometry has produced an ice-rule-
compatible orientation domain, can already-observed local geometry identify
the particular proton decoration in a disjoint ordered specimen?
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

from materials_gcts_ice_cover import IceConfiguration, ice_ih
from materials_gcts_molecular_gap_clusters import unwrapped_cluster_sites
from materials_gcts_molecular_port_growth import (
    FrozenMolecularPortGrammar,
    MolecularAnchorGrowthTrace,
    MolecularOrientationAlternative,
    MolecularOrientationDomain,
    execute_molecular_anchor_growth,
    fit_molecular_port_grammar,
    recognize_seed_molecules,
    score_sites,
)
from materials_gcts_oriented_overlap_ports import matvec

Vector = tuple[float, float, float]
Site = tuple[str, Vector]
Feature = tuple[int, ...]

REPEATS = (8, 8, 5)
SEED_RADIUS = 3.5
TARGET_RADIUS = 7.0
GRAMMAR_RADIUS = 8.0
GRAMMAR_FRACTION = (.22, .22, .50)
PATCH_FRACTIONS: tuple[Vector, ...] = tuple(
    (x, y, z) for z in (.25, .75) for y in (.25, .75) for x in (.25, .75))
TRAIN_PATCHES = tuple(range(5))
HELDOUT_PATCHES = tuple(range(5, 8))
MINIMUM_BACKOFF_SUPPORT = 2
SHUFFLES = 31


@dataclass(frozen=True)
class OrientationSample:
    patch: int
    domain_id: str
    pose_key: str
    feature: Feature
    label: bool


@dataclass(frozen=True)
class FrozenOrientationMarking:
    fine: tuple[tuple[Feature, int, int], ...]
    coarse: tuple[tuple[Feature, int, int], ...]
    minimal: tuple[tuple[Feature, int, int], ...]
    global_positive: int
    global_total: int
    minimum_support: int
    target_used: bool = False


@dataclass(frozen=True)
class FrozenDomainCandidate:
    patch: int
    domain_id: str
    anchor: Vector
    alternatives: tuple[tuple[str, Feature], ...]


@dataclass(frozen=True)
class PatchTrace:
    patch: int
    center: Vector
    seed_molecules: int
    target_molecules: int
    trace: MolecularAnchorGrowthTrace
    candidates: tuple[FrozenDomainCandidate, ...]
    candidate_digest: str


@dataclass(frozen=True)
class SelectionScore:
    supplied_domains: int
    exact_anchor_domains: int
    selected_domains: int
    exact_selected: int
    wrong_selected: int
    precision: float
    pose_precision_given_exact_anchor: float
    recall: float
    unseen_fine: int
    unseen_all_backoffs: int


@dataclass(frozen=True)
class IceOrientationMarkingResult:
    source_atoms: int
    frozen_ports: int
    train_patches: int
    heldout_patches: int
    minimum_patch_center_separation: float
    required_patch_separation: float
    raw_train_heldout_molecule_overlap: int
    training_domains: int
    training_alternatives: int
    training_positive_alternatives: int
    heldout_candidate_domains: int
    heldout_target_matched_domains: int
    heldout_alternatives: int
    heldout_exact_supply_domains: int
    candidate_digest: str
    model_digest: str
    learned: SelectionScore
    unmarked: SelectionScore
    shuffled_exact_median: int
    shuffled_exact_best: int
    empirical_p: float
    learned_beats_unmarked: bool
    learned_beats_shuffles: bool
    orientation_marking_gate_passed: bool
    candidates_frozen_before_target: bool
    target_open_count: int
    target_used_for_fit_or_ranking: bool
    proper_motion_invariant_features: bool
    canonical_branch_materialized_during_growth: bool
    claim_boundary: str


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _center(cell: tuple[Vector, Vector, Vector], fraction: Vector) -> Vector:
    return tuple(sum(fraction[index] * cell[index][axis] for index in range(3))
                 for axis in range(3))  # type: ignore[return-value]


def _crop(configuration: IceConfiguration, center: Vector, radius: float) -> tuple[
        tuple[int, ...], tuple[str, ...], tuple[Vector, ...], tuple[Site, ...]]:
    oxygen_count = len(configuration.positions) // 3
    molecule_ids, sites = [], []
    for oxygen in range(oxygen_count):
        if math.dist(configuration.positions[oxygen], center) > radius:
            continue
        molecule_ids.append(oxygen)
        members = (oxygen, oxygen_count + 2 * oxygen, oxygen_count + 2 * oxygen + 1)
        sites.extend(unwrapped_cluster_sites(
            configuration.species, configuration.positions, members,
            cell=configuration.cell))
    return (tuple(molecule_ids), tuple(species for species, _ in sites),
            tuple(point for _, point in sites), tuple(sites))


def _render(grammar: FrozenMolecularPortGrammar,
            alternative: MolecularOrientationAlternative) -> tuple[Site, ...]:
    return tuple((species, _add(matvec(alternative.rotation, point), alternative.translation))
                 for species, point in grammar.prototype.sites)


def _neighbor_graph(grammar: FrozenMolecularPortGrammar,
                    domains: Sequence[MolecularOrientationDomain]) -> tuple[tuple[int, ...], ...]:
    neighbors = [list() for _ in domains]
    for first, left in enumerate(domains):
        for second in range(first + 1, len(domains)):
            right = domains[second]
            separation = math.dist(left.anchor_site[1], right.anchor_site[1])
            if abs(separation - grammar.anchor_connection_distance) <= grammar.anchor_connection_tolerance:
                neighbors[first].append(second)
                neighbors[second].append(first)
    return tuple(tuple(items) for items in neighbors)


def _donates(grammar: FrozenMolecularPortGrammar,
             alternative: MolecularOrientationAlternative, neighbor: Vector) -> int:
    sites = _render(grammar, alternative)
    oxygen = next(point for species, point in sites if species == "O")
    axis = tuple(neighbor[index] - oxygen[index] for index in range(3))
    axis_length = math.sqrt(sum(value * value for value in axis))
    for species, point in sites:
        if species != "H":
            continue
        vector = tuple(point[index] - oxygen[index] for index in range(3))
        length = math.sqrt(sum(value * value for value in vector))
        if length and axis_length and sum(vector[index] * axis[index] for index in range(3)) \
                / (length * axis_length) >= .94:
            return 1
    return 0


def _graph_depths(domains: Sequence[MolecularOrientationDomain],
                  neighbors: Sequence[Sequence[int]]) -> tuple[int, ...]:
    depths = [-1] * len(domains)
    frontier = [index for index, domain in enumerate(domains) if domain.seed]
    for index in frontier:
        depths[index] = 0
    while frontier:
        index = frontier.pop(0)
        for other in neighbors[index]:
            if depths[other] >= 0:
                continue
            depths[other] = depths[index] + 1
            frontier.append(other)
    return tuple(max(0, depth) for depth in depths)


def _features(grammar: FrozenMolecularPortGrammar,
              trace: MolecularAnchorGrowthTrace) -> dict[tuple[str, str], Feature]:
    domains = trace.orientation_domains
    neighbors = _neighbor_graph(grammar, domains)
    depths = _graph_depths(domains, neighbors)
    output: dict[tuple[str, str], Feature] = {}
    for index, domain in enumerate(domains):
        neighbor_domains = [domains[other] for other in neighbors[index]]
        seed_neighbors = sum(other.seed for other in neighbor_domains)
        neighbor_alternatives = sum(len(other.alternatives) for other in neighbor_domains)
        for alternative in domain.alternatives:
            donated = tuple(_donates(grammar, alternative, other.anchor_site[1])
                            for other in neighbor_domains)
            compatible = 0
            for donated_value, other in zip(donated, neighbor_domains):
                compatible += sum(donated_value + _donates(
                    grammar, other_alternative, domain.anchor_site[1]) == 1
                    for other_alternative in other.alternatives)
            output[(domain.anchor_key, alternative.pose_key)] = (
                len(domain.alternatives), len(neighbor_domains), seed_neighbors,
                sum(donated), sum(value for value, other in zip(donated, neighbor_domains)
                                  if other.seed), compatible, neighbor_alternatives,
                depths[index], sum(len(other.alternatives) == 1 for other in neighbor_domains),
            )
    return output


def _candidate_trace(grammar: FrozenMolecularPortGrammar, configuration: IceConfiguration,
                     patch: int, center: Vector) -> PatchTrace:
    _, seed_species, seed_positions, _ = _crop(configuration, center, SEED_RADIUS)
    _, seed_occurrences, _ = recognize_seed_molecules(grammar, seed_species, seed_positions)
    trace = execute_molecular_anchor_growth(
        grammar, seed_occurrences, boundary_center=center,
        boundary_radius=TARGET_RADIUS, maximum_waves=3,
        maximum_hypotheses_per_anchor=8,
        require_parent_domain_unanimity=True,
        enforce_learned_connection_occupancy=False)
    features = _features(grammar, trace)
    candidates = tuple(FrozenDomainCandidate(
        patch=patch, domain_id=domain.anchor_key, anchor=domain.anchor_site[1],
        alternatives=tuple((alternative.pose_key,
                            features[(domain.anchor_key, alternative.pose_key)])
                           for alternative in domain.alternatives))
        for domain in trace.orientation_domains if not domain.seed)
    payload = [(candidate.patch, candidate.domain_id, candidate.anchor,
                candidate.alternatives) for candidate in candidates]
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    target_ids, _, _, _ = _crop(configuration, center, TARGET_RADIUS)
    return PatchTrace(patch, center, len(seed_occurrences), len(target_ids),
                      trace, candidates, digest)


def _target_molecules(configuration: IceConfiguration, center: Vector) -> tuple[
        tuple[int, Vector, tuple[Site, ...]], ...]:
    ids, _, _, _ = _crop(configuration, center, TARGET_RADIUS)
    oxygen_count = len(configuration.positions) // 3
    return tuple((oxygen, configuration.positions[oxygen], tuple(unwrapped_cluster_sites(
        configuration.species, configuration.positions,
        (oxygen, oxygen_count + 2 * oxygen, oxygen_count + 2 * oxygen + 1),
        cell=configuration.cell))) for oxygen in ids)


def _labels(grammar: FrozenMolecularPortGrammar, trace: PatchTrace,
            target: Sequence[tuple[int, Vector, tuple[Site, ...]]]) -> tuple[OrientationSample, ...]:
    alternatives = {domain.anchor_key: {item.pose_key: item for item in domain.alternatives}
                    for domain in trace.trace.orientation_domains}
    samples = []
    for candidate in trace.candidates:
        matches = [molecule for molecule in target
                   if math.dist(candidate.anchor, molecule[1]) <= .06]
        if len(matches) != 1:
            continue
        target_h = tuple(site for site in matches[0][2] if site[0] == "H")
        for pose_key, feature in candidate.alternatives:
            predicted_h = tuple(site for site in _render(
                grammar, alternatives[candidate.domain_id][pose_key]) if site[0] == "H")
            correct, wrong, missing = score_sites(predicted_h, target_h, tolerance=.06)
            samples.append(OrientationSample(
                trace.patch, candidate.domain_id, pose_key, feature,
                correct == 2 and wrong == 0 and missing == 0))
    return tuple(samples)


def _count_table(samples: Iterable[OrientationSample], key) -> tuple[tuple[Feature, int, int], ...]:
    counts: dict[Feature, list[int]] = {}
    for sample in samples:
        record = counts.setdefault(key(sample.feature), [0, 0])
        record[0] += int(sample.label)
        record[1] += 1
    return tuple((feature, positive, total)
                 for feature, (positive, total) in sorted(counts.items()))


def _fine(feature: Feature) -> Feature:
    return feature


def _coarse(feature: Feature) -> Feature:
    domain, degree, seed_neighbors, donated, donated_seed, compatible, alternatives, depth, fixed = feature
    fraction_bin = round(4 * compatible / max(1, alternatives))
    return degree, seed_neighbors, donated, donated_seed, fraction_bin, depth, fixed


def _minimal(feature: Feature) -> Feature:
    _, degree, seed_neighbors, donated, _, _, _, depth, _ = feature
    return degree, seed_neighbors, donated, depth


def fit_marking(samples: Sequence[OrientationSample]) -> FrozenOrientationMarking:
    return FrozenOrientationMarking(
        fine=_count_table(samples, _fine), coarse=_count_table(samples, _coarse),
        minimal=_count_table(samples, _minimal),
        global_positive=sum(sample.label for sample in samples),
        global_total=len(samples), minimum_support=MINIMUM_BACKOFF_SUPPORT)


def _table(items: Sequence[tuple[Feature, int, int]]) -> Mapping[Feature, tuple[int, int]]:
    return {feature: (positive, total) for feature, positive, total in items}


def marking_score(model: FrozenOrientationMarking, feature: Feature) -> tuple[int, float]:
    for level, (items, key) in enumerate(((model.fine, _fine), (model.coarse, _coarse),
                                          (model.minimal, _minimal))):
        counts = _table(items).get(key(feature))
        if counts and counts[1] >= model.minimum_support:
            return level, (counts[0] + 1) / (counts[1] + 2)
    return 3, (model.global_positive + 1) / (model.global_total + 2)


def _score(model: FrozenOrientationMarking, candidates: Sequence[FrozenDomainCandidate],
           labels: Mapping[tuple[int, str, str], bool], *, unmarked: bool = False) -> SelectionScore:
    supplied = exact_anchor_domains = selected = exact = wrong = unseen_fine = unseen_all = 0
    fine_table = _table(model.fine)
    for domain in candidates:
        supplied_here = any(labels.get((domain.patch, domain.domain_id, pose), False)
                            for pose, _ in domain.alternatives)
        exact_anchor_domains += int(any((domain.patch, domain.domain_id, pose) in labels
                                        for pose, _ in domain.alternatives))
        supplied += int(supplied_here)
        if not domain.alternatives:
            continue
        ranked = sorted(domain.alternatives, key=lambda item: (
            (3, 0.0) if unmarked else marking_score(model, item[1]), item[0]))
        if not unmarked:
            ranked = sorted(domain.alternatives, key=lambda item: (
                marking_score(model, item[1])[0], -marking_score(model, item[1])[1], item[0]))
        pose_key, feature = ranked[0]
        level, _ = marking_score(model, feature)
        unseen_fine += int(_fine(feature) not in fine_table)
        unseen_all += int(level == 3)
        selected += 1
        is_exact = labels.get((domain.patch, domain.domain_id, pose_key), False)
        exact += int(is_exact)
        wrong += int(not is_exact)
    return SelectionScore(supplied, exact_anchor_domains, selected, exact, wrong,
                          exact / max(1, selected), exact / max(1, exact_anchor_domains),
                          exact / max(1, supplied),
                          unseen_fine, unseen_all)


def _shuffle(samples: Sequence[OrientationSample], seed: int) -> tuple[OrientationSample, ...]:
    rng = random.Random(seed)
    groups: dict[tuple[int, str], list[OrientationSample]] = {}
    for sample in samples:
        groups.setdefault((sample.patch, sample.domain_id), []).append(sample)
    shuffled = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda sample: sample.pose_key)
        labels = [sample.label for sample in group]
        rng.shuffle(labels)
        shuffled.extend(OrientationSample(sample.patch, sample.domain_id,
                                          sample.pose_key, sample.feature, label)
                        for sample, label in zip(group, labels))
    return tuple(shuffled)


def _model_digest(model: FrozenOrientationMarking) -> str:
    return hashlib.sha256(json.dumps(asdict(model), sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def evaluate() -> IceOrientationMarkingResult:
    configuration = ice_ih(REPEATS)
    centers = tuple(_center(configuration.cell, fraction) for fraction in PATCH_FRACTIONS)
    grammar_center = _center(configuration.cell, GRAMMAR_FRACTION)
    minimum_separation = min(math.dist(first, second) for index, first in enumerate(centers)
                             for second in centers[index + 1:])
    train_ids, train_species, train_positions, _ = _crop(
        configuration, grammar_center, GRAMMAR_RADIUS)
    grammar = fit_molecular_port_grammar(train_species, train_positions,
                                         pose_tolerance=.04,
                                         minimum_port_observations=2)
    traces = tuple(_candidate_trace(grammar, configuration, patch, center)
                   for patch, center in enumerate(centers))

    # Training targets are authorized labels. Heldout outer crops remain closed
    # until the real and all shuffled markings plus candidate digests are frozen.
    training_samples = tuple(sample for patch in TRAIN_PATCHES
                             for sample in _labels(grammar, traces[patch],
                                                   _target_molecules(configuration, centers[patch])))
    model = fit_marking(training_samples)
    shuffled_models = tuple(fit_marking(_shuffle(training_samples, 0x1CE000 + index))
                            for index in range(SHUFFLES))
    heldout_candidates = tuple(candidate for patch in HELDOUT_PATCHES
                               for candidate in traces[patch].candidates)
    candidate_digest = hashlib.sha256(json.dumps(
        [(trace.patch, trace.candidate_digest) for trace in traces if trace.patch in HELDOUT_PATCHES],
        separators=(",", ":")).encode()).hexdigest()
    frozen_model_digest = _model_digest(model)

    target_open_count = 0
    heldout_samples = []
    for patch in HELDOUT_PATCHES:
        target_open_count += 1
        heldout_samples.extend(_labels(
            grammar, traces[patch], _target_molecules(configuration, centers[patch])))
    label_map = {(sample.patch, sample.domain_id, sample.pose_key): sample.label
                 for sample in heldout_samples}
    learned = _score(model, heldout_candidates, label_map)
    unmarked = _score(model, heldout_candidates, label_map, unmarked=True)
    shuffled = tuple(_score(item, heldout_candidates, label_map)
                     for item in shuffled_models)
    shuffled_exact = sorted(score.exact_selected for score in shuffled)
    p_value = (1 + sum(value >= learned.exact_selected for value in shuffled_exact)) / (SHUFFLES + 1)
    train_molecule_ids = set(train_ids) | set().union(*(
        set(_crop(configuration, centers[patch], TARGET_RADIUS)[0]) for patch in TRAIN_PATCHES))
    heldout_molecule_ids = set().union(*(
        set(_crop(configuration, centers[patch], TARGET_RADIUS)[0]) for patch in HELDOUT_PATCHES))
    training_domains = len({(sample.patch, sample.domain_id) for sample in training_samples})
    heldout_domains = len({(sample.patch, sample.domain_id) for sample in heldout_samples})
    gate = (learned.precision >= .95 and learned.recall >= .90
            and learned.exact_selected > unmarked.exact_selected and p_value <= .05)
    return IceOrientationMarkingResult(
        source_atoms=len(configuration.positions), frozen_ports=len(grammar.ports),
        train_patches=len(TRAIN_PATCHES), heldout_patches=len(HELDOUT_PATCHES),
        minimum_patch_center_separation=minimum_separation,
        required_patch_separation=GRAMMAR_RADIUS + TARGET_RADIUS,
        raw_train_heldout_molecule_overlap=len(train_molecule_ids & heldout_molecule_ids),
        training_domains=training_domains, training_alternatives=len(training_samples),
        training_positive_alternatives=sum(sample.label for sample in training_samples),
        heldout_candidate_domains=len(heldout_candidates),
        heldout_target_matched_domains=heldout_domains,
        heldout_alternatives=len(heldout_samples),
        heldout_exact_supply_domains=learned.supplied_domains,
        candidate_digest=candidate_digest, model_digest=frozen_model_digest,
        learned=learned, unmarked=unmarked,
        shuffled_exact_median=shuffled_exact[len(shuffled_exact) // 2],
        shuffled_exact_best=max(shuffled_exact, default=0), empirical_p=p_value,
        learned_beats_unmarked=learned.exact_selected > unmarked.exact_selected,
        learned_beats_shuffles=learned.exact_selected > max(shuffled_exact, default=-1)
        and p_value <= .05,
        orientation_marking_gate_passed=gate,
        candidates_frozen_before_target=True, target_open_count=target_open_count,
        target_used_for_fit_or_ranking=False, proper_motion_invariant_features=True,
        canonical_branch_materialized_during_growth=False,
        claim_boundary="A finite local marking ranks already-generated mutually exclusive H2O poses. Heldout proton sites score the frozen order only after all candidate/model digests exist. Passing would identify one ordered finite decoration, not energy, entropy, proton disorder, tunnelling, kinetics, stationarity, or physical time.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
