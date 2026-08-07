#!/usr/bin/env python3
"""Learn a cluster hierarchy from an experimental icosahedral quasicrystal.

The input is the real-space P1 model distributed with the Sc-Zn structure
refinement of Yamada et al.  It is downloaded from Europe PMC and pinned by
SHA-256.  No cluster centres or higher-dimensional coordinates are read from
the paper: centres are proposed by recurrent antipodal shells of the minority
species, and an inflation marking is fitted to the resulting centre graph.

This is deliberately a benchmark, not yet a general quasicrystal generator.
It records what can be learned from the colored point cloud and keeps the
held-out continuation score visible.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

Point = Tuple[float, float, float]

SOURCE_URL = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4937780/"
    "supplementaryFiles"
)
SOURCE_DOI = "https://doi.org/10.1107/S2052252516007041"
EXPECTED_CIF_SHA256 = (
    "ae26312042ec1ff55e7fac5fb2e6bec58cbee1f6ca42e3e8f8018526449e08a6"
)


@dataclass(frozen=True)
class AtomicSite:
    position: Point
    species: Tuple[str, ...]
    occupancy: float


@dataclass(frozen=True)
class ShellCluster:
    center: Point
    shell_species: str
    shell_radius: float
    shell_atoms: int
    antipodal_votes: int


@dataclass(frozen=True)
class InflationFit:
    origin: Point
    scale: float
    training_matches: int
    training_eligible: int
    training_mean_error: float
    heldout_matches: int
    heldout_eligible: int
    heldout_mean_error: float


@dataclass(frozen=True)
class CenterHierarchyLevel:
    level: int
    radius: float
    recurring_types: int
    recurring_centers: int
    recurring_cover_fraction: float
    largest_support: int
    boundary_marking_confidence: float


@dataclass(frozen=True)
class AtomicSectionMarkingFit:
    descriptor_dimensions: int
    training_samples: int
    heldout_samples: int
    neighbors: int
    threshold: float
    training_loo_balanced_accuracy: float
    unmarked_heldout_matches: int
    unmarked_heldout_candidates: int
    marked_heldout_matches: int
    marked_heldout_candidates: int
    marked_heldout_precision: float
    marked_heldout_recall: float


@dataclass(frozen=True)
class ConjunctiveSectionMarkingFit:
    descriptor_dimensions: int
    training_samples: int
    heldout_samples: int
    histogram_neighbors: int
    histogram_threshold: float
    moment_neighbors: int
    moment_threshold: float
    training_loo_balanced_accuracy: float
    unmarked_heldout_matches: int
    unmarked_heldout_candidates: int
    marked_heldout_matches: int
    marked_heldout_candidates: int
    marked_heldout_precision: float
    marked_heldout_recall: float


@dataclass(frozen=True)
class ExperimentalScZnBenchmark:
    source_url: str
    source_doi: str
    cif_sha256: str
    raw_rows: int
    unique_sites: int
    virtual_colors: Tuple[str, ...]
    selected_shell_species: str
    learned_cluster_centers: int
    median_atoms_per_cluster: int
    learned_shell_radius_angstrom: float
    learned_link_lengths_angstrom: Tuple[float, ...]
    center_hierarchy_supports: Tuple[int, ...]
    center_hierarchy_cover_fraction: Tuple[float, ...]
    center_marking_confidence: Tuple[float, ...]
    learned_inflation_scale: float
    golden_ratio_error: float
    training_inflation_precision: float
    heldout_inflation_precision: float
    heldout_inflation_mean_error_angstrom: float
    marked_heldout_inflation_precision: float
    marked_heldout_inflation_recall: float
    marking_precision_gain: float
    single_section_heldout_precision: float
    pair_only_heldout_precision: float
    geometry_only_heldout_precision: float
    chemistry_precision_gain: float
    marking_descriptor_dimensions: int
    marking_training_samples: int
    marking_heldout_samples: int
    marking_training_loo_balanced_accuracy: float
    marked_heldout_candidates: int
    marking_rotation_invariant: bool
    flat_cluster_actions: int
    hierarchical_actions: int
    represented_atom_instances: int
    represented_cluster_action_compression: float
    honest_status: str


def _distance(a: Point, b: Point) -> float:
    return math.dist(a, b)


def download_cif() -> bytes:
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "geometric-tree-search-benchmark/1"})
    archive = urllib.request.urlopen(request, timeout=90).read()
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = [name for name in bundle.namelist() if name.lower().endswith(".cif")]
        if len(names) != 1:
            raise ValueError(f"expected one supplementary CIF, found {names}")
        cif = bundle.read(names[0])
    digest = hashlib.sha256(cif).hexdigest()
    if digest != EXPECTED_CIF_SHA256:
        raise ValueError(f"supplementary CIF checksum changed: {digest}")
    return cif


def parse_cif(cif: bytes) -> Tuple[List[AtomicSite], int]:
    """Parse and merge the simple atom loop in the supplied P1 model."""
    lines = cif.decode("utf-8", "replace").splitlines()
    raw: List[Tuple[str, Point, float]] = []
    cell_length = None
    for line in lines:
        fields = line.split()
        if fields and fields[0] == "_cell_length_a":
            cell_length = float(fields[1].split("(")[0])
            break
    if cell_length is None:
        raise ValueError("missing cell length")
    for start, line in enumerate(lines):
        if line.strip() != "_atom_site_type_symbol":
            continue
        for row in lines[start + 1:]:
            fields = row.split()
            if len(fields) < 6:
                break
            point = tuple(float(fields[index]) * cell_length
                          for index in (2, 3, 4))
            raw.append((fields[5], point, float(fields[1])))
        break
    if not raw:
        raise ValueError("missing atom-site loop")

    merged: Dict[Point, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for species, point, occupancy in raw:
        key = tuple(round(value, 5) for value in point)
        merged[key][species] += occupancy
    sites = [AtomicSite(point, tuple(sorted(colors)), sum(colors.values()))
             for point, colors in sorted(merged.items())]
    return sites, len(raw)


def _neighbor_cells(key: Tuple[int, int, int]):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield key[0] + dx, key[1] + dy, key[2] + dz


def infer_shell_clusters(
        sites: Sequence[AtomicSite], minimum_pair_distance: float = 6.0,
        maximum_pair_distance: float = 12.0, midpoint_bin: float = .35,
        shell_tolerance: float = .40, _refine: bool = True
        ) -> Tuple[str, List[ShellCluster]]:
    """Find recurrent centrosymmetric shells without atom-centre labels.

    Chemical elements are tried from rarest to most abundant.  A midpoint
    receiving six mutually consistent antipodal-pair votes and supporting
    twelve atoms on one sphere is a cluster-centre proposal.  The first color
    with recurrent proposals is selected; for this data that inference chooses
    Sc without being told its name.
    """
    elements = sorted({element for site in sites for element in site.species})
    by_element = {element: [site.position for site in sites
                            if element in site.species]
                  for element in elements}
    elements.sort(key=lambda element: len(by_element[element]))
    for element in elements:
        points = by_element[element]
        cell = maximum_pair_distance
        grid: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
        for index, point in enumerate(points):
            grid[tuple(math.floor(value / cell) for value in point)].append(index)
        votes: Dict[Tuple[int, int, int], List[Tuple[Point, float]]] = defaultdict(list)
        for key, indices in grid.items():
            for other_key in _neighbor_cells(key):
                for first in indices:
                    for second in grid.get(other_key, ()):
                        if second <= first:
                            continue
                        a, b = points[first], points[second]
                        separation = _distance(a, b)
                        if not minimum_pair_distance <= separation <= maximum_pair_distance:
                            continue
                        midpoint = tuple((a[axis] + b[axis]) / 2.0
                                         for axis in range(3))
                        bin_key = tuple(round(value / midpoint_bin)
                                        for value in midpoint)
                        votes[bin_key].append((midpoint, separation / 2.0))
        proposals: List[ShellCluster] = []
        for values in votes.values():
            if len(values) < 4:
                continue
            # One coarse midpoint bin can contain unrelated pairs at another
            # radius.  Select its densest radius-consistent vote section rather
            # than letting those pairs move the proposed centre.
            ordered = sorted(values, key=lambda value: value[1])
            consistent = max(
                (ordered[left:right]
                 for left in range(len(ordered))
                 for right in range(left + 1, len(ordered) + 1)
                 if ordered[right - 1][1] - ordered[left][1] <= .25),
                key=len)
            if len(consistent) < 4:
                continue
            center = tuple(sum(value[0][axis] for value in consistent) /
                           len(consistent)
                           for axis in range(3))
            radii = sorted(value[1] for value in consistent)
            radius = radii[len(radii) // 2]
            shell = [_distance(center, point) for point in points
                     if abs(_distance(center, point) - radius) <= shell_tolerance]
            if len(shell) != 12 or max(radii) - min(radii) > .25:
                continue
            proposals.append(ShellCluster(
                center, element, sum(shell) / len(shell), 12,
                len(consistent)))
        proposals.sort(key=lambda cluster:(-cluster.antipodal_votes,
                                            cluster.center))
        deduplicated: List[ShellCluster] = []
        for proposal in proposals:
            if all(_distance(proposal.center, previous.center) > .7
                   for previous in deduplicated):
                deduplicated.append(proposal)
        if deduplicated:
            if _refine and maximum_pair_distance - minimum_pair_distance > 2.0:
                learned_radius = sorted(cluster.shell_radius
                                        for cluster in deduplicated)[
                                            len(deduplicated) // 2]
                return infer_shell_clusters(
                    sites, 2.0 * learned_radius - .6,
                    2.0 * learned_radius + .6, midpoint_bin,
                    shell_tolerance, False)
            return element, deduplicated
    raise ValueError("no recurrent antipodal shell was found for any color")


def infer_link_lengths(centers: Sequence[Point], maximum: float = 16.0,
                       bin_width: float = .1) -> Tuple[float, ...]:
    histogram: Counter[float] = Counter()
    for index, first in enumerate(centers):
        for second in centers[index + 1:]:
            distance = _distance(first, second)
            if distance <= maximum:
                histogram[round(distance / bin_width) * bin_width] += 1
    peaks: List[float] = []
    for distance, _ in histogram.most_common():
        if all(abs(distance - previous) >= .5 for previous in peaks):
            peaks.append(distance)
        if len(peaks) == 2:
            break
    return tuple(sorted(round(value, 2) for value in peaks))


def learn_center_hierarchy(
        centers: Sequence[Point], link_lengths: Sequence[float], scale: float,
        levels: int = 3, distance_tolerance: float = .45,
        count_bin: int = 4) -> Tuple[CenterHierarchyLevel, ...]:
    """Learn bounded clusters-of-clusters and their outer markings.

    A type is an element of a finite radial section: counts on the learned
    connection shells and their inflated copies, quantized to tolerate the
    incomplete boundary of the finite experimental model.  Its marking is the
    next pair of shells, outside the represented cluster.  No atomic labels or
    cluster centres from the refinement are supplied to this stage.
    """
    distances = [[_distance(first, second) for second in centers]
                 for first in centers]
    learned: List[CenterHierarchyLevel] = []
    for level in range(1, levels + 1):
        internal_shells = [length * scale ** power
                           for power in range(level)
                           for length in link_lengths]
        boundary_shells = [length * scale ** level
                           for length in link_lengths]
        labels = []
        markings = []
        supports = []
        for index, row in enumerate(distances):
            values = [distance for other, distance in enumerate(row)
                      if other != index]
            labels.append(tuple(round(sum(abs(distance - radius) <=
                                          distance_tolerance
                                          for distance in values) / count_bin)
                                for radius in internal_shells))
            markings.append(tuple(round(sum(abs(distance - radius) <=
                                            distance_tolerance
                                            for distance in values) / count_bin)
                                  for radius in boundary_shells))
            supports.append(1 + sum(distance <= max(internal_shells) +
                                    distance_tolerance
                                    for distance in values))
        occurrences = Counter(labels)
        recurring = {label for label, count in occurrences.items()
                     if count >= 2}
        recurring_centers = sum(occurrences[label] for label in recurring)
        consistent = 0
        for label in recurring:
            boundary_counts = Counter(
                marking for candidate, marking in zip(labels, markings)
                if candidate == label)
            consistent += max(boundary_counts.values())
        relevant_supports = [support for support, label
                             in zip(supports, labels) if label in recurring]
        learned.append(CenterHierarchyLevel(
            level, max(internal_shells), len(recurring), recurring_centers,
            recurring_centers / len(centers),
            max(relevant_supports, default=0),
            consistent / recurring_centers if recurring_centers else 0.0))
    return tuple(learned)


def _nearest(point: Point, centers: Sequence[Point], grid, tolerance: float):
    key = tuple(math.floor(value / tolerance) for value in point)
    best = float("inf")
    for neighbor in _neighbor_cells(key):
        for index in grid.get(neighbor, ()):
            best = min(best, _distance(point, centers[index]))
    return best


def _spatial_index(points: Sequence[Point], cell: float):
    grid: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for index, point in enumerate(points):
        grid[tuple(math.floor(value / cell) for value in point)].append(index)
    return grid


def _candidate_rows(centers: Sequence[Point], inflation: InflationFit,
                    tolerance: float = .45):
    grid = _spatial_index(centers, tolerance)
    lower = tuple(min(point[axis] for point in centers) + 1.0
                  for axis in range(3))
    upper = tuple(max(point[axis] for point in centers) - 1.0
                  for axis in range(3))
    rows = []
    for index, point in enumerate(centers):
        if _distance(point, inflation.origin) <= 1e-9:
            # An inflation fixes its origin.  That tautological correspondence
            # is neither a growth placement nor a meaningful pair marking.
            continue
        target = tuple(inflation.origin[axis] + inflation.scale *
                       (point[axis] - inflation.origin[axis])
                       for axis in range(3))
        if not all(lower[axis] <= target[axis] <= upper[axis]
                   for axis in range(3)):
            continue
        split = sum(math.floor(value / 8.0) for value in point) & 1
        error = _nearest(target, centers, grid, tolerance)
        rows.append((index, split, int(error <= tolerance), error))
    return rows


def _atomic_section_descriptors(
        sites: Sequence[AtomicSite], centers: Sequence[Point], origin: Point,
        candidate_indices: Sequence[int], radius: float = 7.8,
        chemical: bool = True) -> Dict[int, Tuple[float, ...]]:
    """Bounded rotation-invariant sections around a proposed parent action.

    The pair axis from the inflation origin to the source cluster is intrinsic.
    Counts use three radial bands and four axial-cosine bands.  Consequently a
    rigid rotation of the complete point cloud leaves the descriptor unchanged.
    """
    points = [site.position for site in sites]
    grid = _spatial_index(points, radius)
    elements = sorted({element for site in sites for element in site.species})
    colors: Tuple[object, ...] = tuple(elements) if chemical else (None,)
    radial_bands = ((0.0, 3.5), (3.5, 5.5), (5.5, radius))
    descriptors = {}
    for candidate in candidate_indices:
        center = centers[candidate]
        axis = tuple(center[coordinate] - origin[coordinate]
                     for coordinate in range(3))
        pair_distance = math.sqrt(sum(value * value for value in axis))
        unit = tuple(value / pair_distance for value in axis)
        counts = [0] * (len(radial_bands) * len(colors) * 4)
        key = tuple(math.floor(value / radius) for value in center)
        neighbors = []
        for neighbor in _neighbor_cells(key):
            neighbors.extend(grid.get(neighbor, ()))
        for site_index in neighbors:
            site = sites[site_index]
            vector = tuple(site.position[coordinate] - center[coordinate]
                           for coordinate in range(3))
            distance = math.sqrt(sum(value * value for value in vector))
            if not 0.0 < distance <= radius:
                continue
            radial_bin = next((index for index, (low, high)
                               in enumerate(radial_bands)
                               if low < distance <= high), None)
            if radial_bin is None:
                continue
            cosine = sum(vector[coordinate] * unit[coordinate]
                         for coordinate in range(3)) / distance
            axial_bin = min(3, max(0, int((cosine + 1.0) * 2.0)))
            for color_index, color in enumerate(colors):
                if color is None or color in site.species:
                    offset = ((radial_bin * len(colors) + color_index) * 4 +
                              axial_bin)
                    counts[offset] += 1
        descriptors[candidate] = (pair_distance,) + tuple(counts)
    return descriptors


def _knn_score(training, descriptor, neighbors: int) -> float:
    dimensions = len(descriptor)
    means = [sum(row[0][axis] for row in training) / len(training)
             for axis in range(dimensions)]
    scales = [max(1e-6, (sum((row[0][axis] - means[axis]) ** 2
                             for row in training) / len(training)) ** .5)
              for axis in range(dimensions)]
    distances = sorted((sum(((known[axis] - descriptor[axis]) /
                             scales[axis]) ** 2
                            for axis in range(dimensions)), label)
                       for known, label in training)
    selected = distances[:neighbors]
    weights = [1.0 / (math.sqrt(distance) + 1e-6)
               for distance, _ in selected]
    return (sum(weight * label for weight, (_, label)
                in zip(weights, selected)) / sum(weights))


def _select_knn(training):
    positives = sum(label for _, label in training)
    negatives = len(training) - positives
    choices = []
    for neighbors in (1, 3, 5, 7):
        if neighbors > len(training) - 1:
            continue
        loo = []
        for omitted, (descriptor, label) in enumerate(training):
            subset = training[:omitted] + training[omitted + 1:]
            loo.append((_knn_score(subset, descriptor, neighbors), label))
        for threshold in (.35, .45, .50, .55, .65, .75, .85):
            true_positive = sum(score >= threshold and label
                                for score, label in loo)
            true_negative = sum(score < threshold and not label
                                for score, label in loo)
            balanced = .5 * (true_positive / positives +
                             true_negative / negatives)
            predicted = sum(score >= threshold for score, _ in loo)
            precision = (true_positive / predicted if predicted else 0.0)
            choices.append((balanced, precision, threshold, -neighbors,
                            neighbors, tuple(loo)))
    return max(choices)


def _legendre(order: int, value: float) -> float:
    previous, current = 1.0, value
    if order == 0:
        return previous
    if order == 1:
        return current
    for degree in range(2, order + 1):
        previous, current = current, (
            ((2 * degree - 1) * value * current -
             (degree - 1) * previous) / degree)
    return current


def _atomic_moment_descriptors(
        sites: Sequence[AtomicSite], centers: Sequence[Point], origin: Point,
        candidate_indices: Sequence[int], radius: float = 7.8,
        chemical: bool = False) -> Dict[int, Tuple[float, ...]]:
    """A second finite section using continuous even angular moments."""
    points = [site.position for site in sites]
    grid = _spatial_index(points, radius)
    elements = sorted({element for site in sites for element in site.species})
    colors: Tuple[object, ...] = tuple(elements) if chemical else (None,)
    radial_bands = ((0.0, 3.5), (3.5, 5.5), (5.5, radius))
    orders = (2, 4, 6, 8)
    descriptors = {}
    for candidate in candidate_indices:
        center = centers[candidate]
        axis = tuple(center[coordinate] - origin[coordinate]
                     for coordinate in range(3))
        pair_distance = math.sqrt(sum(value * value for value in axis))
        unit = tuple(value / pair_distance for value in axis)
        key = tuple(math.floor(value / radius) for value in center)
        neighbors = []
        for neighbor in _neighbor_cells(key):
            neighbors.extend(grid.get(neighbor, ()))
        features: List[float] = [pair_distance]
        for low, high in radial_bands:
            for color in colors:
                cosines = []
                for site_index in neighbors:
                    site = sites[site_index]
                    if color is not None and color not in site.species:
                        continue
                    vector = tuple(site.position[coordinate] - center[coordinate]
                                   for coordinate in range(3))
                    distance = math.sqrt(sum(value * value for value in vector))
                    if not low < distance <= high:
                        continue
                    cosines.append(sum(vector[coordinate] * unit[coordinate]
                                       for coordinate in range(3)) / distance)
                features.append(float(len(cosines)))
                features.extend(sum(_legendre(order, cosine)
                                    for cosine in cosines)
                                for order in orders)
        descriptors[candidate] = tuple(features)
    return descriptors


def fit_atomic_section_marking(
        sites: Sequence[AtomicSite], centers: Sequence[Point],
        inflation: InflationFit, chemical: bool = True,
        include_section: bool = True
        ) -> AtomicSectionMarkingFit:
    """Fit the GCTS acceptance section on split 0 and audit split 1 once."""
    rows = _candidate_rows(centers, inflation)
    candidate_indices = [row[0] for row in rows]
    if include_section:
        descriptors = _atomic_section_descriptors(
            sites, centers, inflation.origin, candidate_indices,
            chemical=chemical)
    else:
        descriptors = {
            index: (_distance(centers[index], inflation.origin),)
            for index in candidate_indices}
    training = [(descriptors[index], label)
                for index, split, label, _ in rows if split == 0]
    heldout = [(descriptors[index], label)
               for index, split, label, _ in rows if split == 1]
    balanced, _, threshold, _, neighbors, _ = _select_knn(training)
    heldout_scores = [(_knn_score(training, descriptor, neighbors), label)
                      for descriptor, label in heldout]
    marked_candidates = sum(score >= threshold
                            for score, _ in heldout_scores)
    marked_matches = sum(score >= threshold and label
                         for score, label in heldout_scores)
    heldout_positives = sum(label for _, label in heldout)
    precision = marked_matches / marked_candidates if marked_candidates else 0.0
    recall = marked_matches / heldout_positives if heldout_positives else 0.0
    return AtomicSectionMarkingFit(
        len(training[0][0]), len(training), len(heldout), neighbors, threshold,
        balanced, heldout_positives, len(heldout), marked_matches,
        marked_candidates, precision, recall)


def fit_conjunctive_section_marking(
        sites: Sequence[AtomicSite], centers: Sequence[Point],
        inflation: InflationFit) -> ConjunctiveSectionMarkingFit:
    """Require agreement of two independently cross-validated GCTS sections."""
    rows = _candidate_rows(centers, inflation)
    indices = [row[0] for row in rows]
    histogram = _atomic_section_descriptors(
        sites, centers, inflation.origin, indices, chemical=False)
    moments = _atomic_moment_descriptors(
        sites, centers, inflation.origin, indices, chemical=False)
    histogram_training = [(histogram[index], label)
                          for index, split, label, _ in rows if split == 0]
    moment_training = [(moments[index], label)
                       for index, split, label, _ in rows if split == 0]
    h_balanced, _, h_threshold, _, h_neighbors, h_loo = _select_knn(
        histogram_training)
    m_balanced, _, m_threshold, _, m_neighbors, m_loo = _select_knn(
        moment_training)
    labels = [label for _, label in histogram_training]
    conjunction = [h_score >= h_threshold and m_score >= m_threshold
                   for (h_score, _), (m_score, _) in zip(h_loo, m_loo)]
    positives = sum(labels)
    negatives = len(labels) - positives
    true_positive = sum(prediction and label
                        for prediction, label in zip(conjunction, labels))
    true_negative = sum(not prediction and not label
                        for prediction, label in zip(conjunction, labels))
    balanced = .5 * (true_positive / positives + true_negative / negatives)

    heldout = [(index, label) for index, split, label, _ in rows if split == 1]
    predictions = []
    for index, label in heldout:
        h_score = _knn_score(histogram_training, histogram[index], h_neighbors)
        m_score = _knn_score(moment_training, moments[index], m_neighbors)
        predictions.append((h_score >= h_threshold and
                            m_score >= m_threshold, label))
    candidates = sum(prediction for prediction, _ in predictions)
    matches = sum(prediction and label for prediction, label in predictions)
    heldout_positives = sum(label for _, label in heldout)
    return ConjunctiveSectionMarkingFit(
        len(histogram_training[0][0]) + len(moment_training[0][0]),
        len(histogram_training), len(heldout), h_neighbors, h_threshold,
        m_neighbors, m_threshold, balanced, heldout_positives, len(heldout),
        matches, candidates, matches / candidates if candidates else 0.0,
        matches / heldout_positives if heldout_positives else 0.0)


def _section_rotation_invariant(sites, centers, inflation) -> bool:
    rows = _candidate_rows(centers, inflation)
    indices = [row[0] for row in rows]
    original = _atomic_section_descriptors(
        sites, centers, inflation.origin, indices)
    original_moments = _atomic_moment_descriptors(
        sites, centers, inflation.origin, indices)

    def move(point):
        # A proper 90-degree rotation followed by a translation.
        return (-point[1] + 113.0, point[0] - 37.0, point[2] + 19.0)

    moved_sites = [AtomicSite(move(site.position), site.species, site.occupancy)
                   for site in sites]
    moved_centers = [move(point) for point in centers]
    moved = _atomic_section_descriptors(
        moved_sites, moved_centers, move(inflation.origin), indices)
    moved_moments = _atomic_moment_descriptors(
        moved_sites, moved_centers, move(inflation.origin), indices)
    return all(
        all(abs(left - right) <= 1e-9
            for left, right in zip(original[index], moved[index])) and
        all(abs(left - right) <= 1e-9
            for left, right in zip(original_moments[index],
                                    moved_moments[index]))
        for index in indices)


def fit_inflation(centers: Sequence[Point], tolerance: float = .45) -> InflationFit:
    """Fit scale+origin on one deterministic half and report the other half."""
    grid: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for index, point in enumerate(centers):
        grid[tuple(math.floor(value / tolerance) for value in point)].append(index)
    lower = tuple(min(point[axis] for point in centers) + 1.0 for axis in range(3))
    upper = tuple(max(point[axis] for point in centers) - 1.0 for axis in range(3))

    def membership(point: Point) -> int:
        # A spatial checkerboard avoids fitting and testing adjacent list rows.
        return sum(math.floor(value / 8.0) for value in point) & 1

    def score(origin: Point, scale: float, split: int):
        eligible = matches = 0
        errors: List[float] = []
        for point in centers:
            if membership(point) != split:
                continue
            if _distance(point, origin) <= 1e-9:
                continue
            target = tuple(origin[axis] + scale * (point[axis] - origin[axis])
                           for axis in range(3))
            if not all(lower[axis] <= target[axis] <= upper[axis]
                       for axis in range(3)):
                continue
            eligible += 1
            error = _nearest(target, centers, grid, tolerance)
            if error <= tolerance:
                matches += 1
                errors.append(error)
        mean = sum(errors) / len(errors) if errors else float("inf")
        return matches, eligible, mean

    candidates = []
    for origin in centers:
        for step in range(1400, 2001, 2):
            scale = step / 1000.0
            matches, eligible, error = score(origin, scale, 0)
            if eligible >= 12 and matches >= 4:
                candidates.append((matches / eligible, matches, -error,
                                   origin, scale, eligible, error))
    if not candidates:
        raise ValueError("no inflation candidate passed the support gate")
    _, matches, _, origin, scale, eligible, error = max(candidates)
    held_matches, held_eligible, held_error = score(origin, scale, 1)
    return InflationFit(origin, scale, matches, eligible, error,
                        held_matches, held_eligible, held_error)


def evaluate() -> ExperimentalScZnBenchmark:
    cif = download_cif()
    sites, raw_rows = parse_cif(cif)
    species, clusters = infer_shell_clusters(sites)
    # Boundary centres have incomplete atomic decorations.  The inflation fit
    # uses all learned centres but evaluates only targets inside their bounds.
    centers = [cluster.center for cluster in clusters]
    links = infer_link_lengths(centers)
    inflation = fit_inflation(centers)
    hierarchy = learn_center_hierarchy(centers, links, inflation.scale)
    marking = fit_atomic_section_marking(sites, centers, inflation)
    conjunctive_marking = fit_conjunctive_section_marking(
        sites, centers, inflation)
    geometry_marking = fit_atomic_section_marking(
        sites, centers, inflation, chemical=False)
    pair_marking = fit_atomic_section_marking(
        sites, centers, inflation, chemical=False, include_section=False)
    rotation_invariant = _section_rotation_invariant(sites, centers, inflation)
    atoms_per_cluster = sorted(sum(_distance(cluster.center, site.position) <= 7.8
                                   for site in sites)
                               for cluster in clusters)
    median_atoms = atoms_per_cluster[len(atoms_per_cluster) // 2]
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    train_precision = inflation.training_matches / inflation.training_eligible
    held_precision = (inflation.heldout_matches / inflation.heldout_eligible
                      if inflation.heldout_eligible else 0.0)
    # One learned inflation action represents every accepted centre placement;
    # decorating those centres separately is the flat cluster baseline.
    flat_actions = inflation.training_matches + inflation.heldout_matches
    hierarchical_actions = 1
    status = ("held-out marking improves inflation; multi-origin replication "
              "still required"
              if conjunctive_marking.marked_heldout_precision >= .5 else
              "cluster hierarchy detected; held-out growth not yet reliable")
    return ExperimentalScZnBenchmark(
        SOURCE_URL, SOURCE_DOI, hashlib.sha256(cif).hexdigest(), raw_rows,
        len(sites), tuple(sorted({"/".join(site.species) for site in sites})),
        species, len(clusters), median_atoms,
        round(sum(cluster.shell_radius for cluster in clusters) / len(clusters), 4),
        links, tuple(level.largest_support for level in hierarchy),
        tuple(level.recurring_cover_fraction for level in hierarchy),
        tuple(level.boundary_marking_confidence for level in hierarchy),
        inflation.scale, abs(inflation.scale - phi), train_precision,
        held_precision, inflation.heldout_mean_error,
        conjunctive_marking.marked_heldout_precision,
        conjunctive_marking.marked_heldout_recall,
        conjunctive_marking.marked_heldout_precision - held_precision,
        marking.marked_heldout_precision,
        pair_marking.marked_heldout_precision,
        geometry_marking.marked_heldout_precision,
        marking.marked_heldout_precision -
        geometry_marking.marked_heldout_precision,
        conjunctive_marking.descriptor_dimensions,
        conjunctive_marking.training_samples,
        conjunctive_marking.heldout_samples,
        conjunctive_marking.training_loo_balanced_accuracy,
        conjunctive_marking.marked_heldout_candidates,
        rotation_invariant,
        flat_actions,
        hierarchical_actions, flat_actions * median_atoms,
        float(flat_actions), status)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
