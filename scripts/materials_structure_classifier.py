#!/usr/bin/env python3
"""Transparent post-hoc order classification for colored 3-D point sets.

This module deliberately does not use generator metadata.  It distinguishes
translation-periodic, locally periodic, recurrent nonperiodic, and disordered
point sets using finite-sample diagnostics.  The categories are hypotheses,
not thermodynamic phase labels.  In particular, ``quasicrystal-candidate``
means "recurrent ordered structure without three convincing translations";
diffraction or a higher-dimensional model is still needed for confirmation.

An ordinary space group is reported only when a periodic cell is supplied and
spglib finds a label that is stable over a tolerance sweep.  This avoids the
common but misleading practice of assigning P1 to amorphous or quasiperiodic
finite crops.
"""

from __future__ import annotations

import collections
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

Vector = Tuple[float, float, float]
Cell = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class TranslationEvidence:
    vector: Vector
    match_fraction: float
    eligible_atoms: int
    matched_atoms: int
    localization: float


@dataclass(frozen=True)
class SpaceGroupEvidence:
    status: str
    number: Optional[int] = None
    symbol: Optional[str] = None
    stable_fraction: float = 0.0
    tolerance_labels: Tuple[Tuple[float, Optional[int], Optional[str]], ...] = ()
    note: str = ""


@dataclass(frozen=True)
class StructureEvaluation:
    category: str
    confidence: float
    atom_count: int
    species_count: int
    nearest_neighbor_scale: float
    boundary_core_radius: float
    boundary_core_atoms: int
    independent_translation_count: int
    translation_periodicity: float
    translation_closure: float
    local_environment_recurrence: float
    radial_shell_contrast: float
    localized_translation_count: int
    translations: Tuple[TranslationEvidence, ...]
    space_group: SpaceGroupEvidence
    reasons: Tuple[str, ...]
    caveats: Tuple[str, ...]

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(float(a - b) for a, b in zip(left, right))  # type: ignore[return-value]


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(float(a + b) for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(value: float, vector: Sequence[float]) -> Vector:
    return tuple(float(value * x) for x in vector)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _canonical(vector: Vector) -> Vector:
    for value in vector:
        if abs(value) > 1e-12:
            return vector if value > 0 else _scale(-1.0, vector)
    return vector


def _spatial_index(
    positions: Sequence[Vector], species: Sequence[str], bin_size: float,
) -> Dict[Tuple[str, int, int, int], list[int]]:
    result: Dict[Tuple[str, int, int, int], list[int]] = collections.defaultdict(list)
    for index, (point, chemical) in enumerate(zip(positions, species)):
        key = (chemical,) + tuple(math.floor(x / bin_size) for x in point)
        result[key].append(index)  # type: ignore[index]
    return result


def _has_match(
    target: Vector,
    chemical: str,
    positions: Sequence[Vector],
    index: Dict[Tuple[str, int, int, int], list[int]],
    tolerance: float,
) -> bool:
    cell = tuple(math.floor(value / tolerance) for value in target)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                key = (chemical, cell[0] + dx, cell[1] + dy, cell[2] + dz)
                for candidate in index.get(key, ()):
                    if _norm(_sub(positions[candidate], target)) <= tolerance:
                        return True
    return False


def _nearest_data(positions: Sequence[Vector]) -> Tuple[float, Tuple[Tuple[float, ...], ...]]:
    rows = []
    nearest = []
    for i, left in enumerate(positions):
        distances = sorted(_norm(_sub(left, right))
                           for j, right in enumerate(positions) if i != j)
        nearest.append(distances[0])
        rows.append(tuple(distances[:min(12, len(distances))]))
    return _percentile(nearest, 0.5), tuple(rows)


def _translation_candidates(
    positions: Sequence[Vector],
    species: Sequence[str],
    center: Vector,
    support_radius: float,
    scale: float,
    tolerance: float,
) -> Tuple[TranslationEvidence, ...]:
    # Vote for repeated species-preserving displacements.  Limiting the range
    # prevents a large number of weak long-baseline coincidences from hiding
    # primitive or short supercell translations.
    bins: Dict[Tuple[int, int, int], list[Vector]] = collections.defaultdict(list)
    maximum_length = 4.25 * scale
    quantization = max(tolerance * 1.35, 1e-12)
    for i, left in enumerate(positions):
        for j in range(i + 1, len(positions)):
            if species[i] != species[j]:
                continue
            vector = _canonical(_sub(positions[j], left))
            length = _norm(vector)
            if length < 1.35 * scale or length > maximum_length:
                continue
            key = tuple(round(value / quantization) for value in vector)
            bins[key].append(vector)  # type: ignore[index]
    minimum_votes = max(4, round(0.025 * len(positions)))
    voted = sorted((len(vectors), key, vectors)
                   for key, vectors in bins.items()
                   if len(vectors) >= minimum_votes)[-160:]
    spatial = _spatial_index(positions, species, tolerance)
    evidences = []
    minimum_eligible = max(10, round(0.12 * len(positions)))
    for _, _, vectors in reversed(voted):
        vector = tuple(sum(value[axis] for value in vectors) / len(vectors)
                       for axis in range(3))  # type: ignore[assignment]
        matched_indices = []
        eligible = 0
        for atom, (point, chemical) in enumerate(zip(positions, species)):
            # Test both directions.  An atom is eligible only where the target
            # remains in an interior ball, so missing crop-boundary atoms do
            # not count as broken translational symmetry.
            atom_matched = False
            atom_eligible = False
            for sign in (-1.0, 1.0):
                target = _add(point, _scale(sign, vector))
                if _norm(_sub(target, center)) <= support_radius:
                    atom_eligible = True
                    atom_matched |= _has_match(
                        target, chemical, positions, spatial, tolerance)
            if atom_eligible:
                eligible += 1
                if atom_matched:
                    matched_indices.append(atom)
        if eligible < minimum_eligible:
            continue
        fraction = len(matched_indices) / eligible
        if not matched_indices:
            localization = 0.0
        else:
            centroid = tuple(sum(positions[i][axis] for i in matched_indices) /
                             len(matched_indices) for axis in range(3))
            localization = min(1.0, _norm(_sub(centroid, center)) /
                               max(support_radius, 1e-12))
        evidences.append(TranslationEvidence(
            vector, fraction, eligible, len(matched_indices), localization))
    # Merge near-identical vectors produced by adjacent quantization cells.
    selected = []
    for evidence in sorted(evidences,
                           key=lambda item: (item.match_fraction,
                                             item.eligible_atoms), reverse=True):
        if any(_norm(_sub(evidence.vector, old.vector)) <= 1.8 * tolerance
               for old in selected):
            continue
        selected.append(evidence)
        if len(selected) == 24:
            break
    return tuple(selected)


def _independent_translations(
    candidates: Sequence[TranslationEvidence],
) -> Tuple[TranslationEvidence, ...]:
    if candidates:
        peak = max(item.match_fraction for item in candidates)
        near_peak = sorted(
            (item for item in candidates if item.match_fraction >= peak - 0.10),
            key=lambda item: (_norm(item.vector), -item.match_fraction))
        remainder = sorted(
            (item for item in candidates if item.match_fraction < peak - 0.10),
            key=lambda item: (-item.match_fraction, _norm(item.vector)))
        candidates = tuple(near_peak + remainder)
    chosen = []
    for candidate in candidates:
        vector = candidate.vector
        if not chosen:
            chosen.append(candidate)
        elif len(chosen) == 1:
            sine = _norm(_cross(chosen[0].vector, vector)) / (
                _norm(chosen[0].vector) * _norm(vector))
            if sine > 0.18:
                chosen.append(candidate)
        else:
            volume = abs(_dot(_cross(chosen[0].vector, chosen[1].vector), vector))
            normalized = volume / (_norm(chosen[0].vector) *
                                   _norm(chosen[1].vector) * _norm(vector))
            if normalized > 0.08:
                chosen.append(candidate)
        if len(chosen) == 3:
            break
    return tuple(chosen)


def _translation_closure(
    basis: Sequence[TranslationEvidence],
    positions: Sequence[Vector],
    species: Sequence[str],
    center: Vector,
    support_radius: float,
    tolerance: float,
) -> float:
    """Test whether apparent translations remain valid when composed.

    A frequent short displacement in a Fibonacci word can match most sites in
    a small crop even though applying it twice is not a symmetry.  A lattice
    translation, in contrast, composes with itself wherever both endpoints
    remain inside the observed support.  This is a stricter test than finding
    three geometrically independent high-vote displacement vectors.
    """
    if len(basis) != 3:
        return 0.0
    spatial = _spatial_index(positions, species, tolerance)
    minimum_eligible = max(8, round(0.06 * len(positions)))
    scores = []
    for evidence in basis:
        vector = _scale(2.0, evidence.vector)
        eligible = matched = 0
        for point, chemical in zip(positions, species):
            atom_eligible = False
            atom_matched = False
            for sign in (-1.0, 1.0):
                target = _add(point, _scale(sign, vector))
                if _norm(_sub(target, center)) <= support_radius:
                    atom_eligible = True
                    atom_matched |= _has_match(
                        target, chemical, positions, spatial, tolerance)
            if atom_eligible:
                eligible += 1
                matched += atom_matched
        if eligible >= minimum_eligible:
            scores.append(matched / eligible)
    # A very small crop may not contain a measurable doubled translation.  Do
    # not invent evidence against periodicity in that case, but expose that the
    # composition check was inconclusive via the neutral value.
    return min(scores) if scores else 0.5


def _local_recurrence(
    nearest_rows: Sequence[Sequence[float]],
    positions: Sequence[Vector],
    center: Vector,
    core_radius: float,
    scale: float,
) -> float:
    fingerprints = []
    width = 0.13 * scale
    for point, distances in zip(positions, nearest_rows):
        if _norm(_sub(point, center)) > core_radius:
            continue
        # A radial environment signature is rotation invariant.  Six shells
        # capture local recurrence without pretending to be a complete motif.
        fingerprints.append(tuple(round(value / width) for value in distances[:8]))
    counts = collections.Counter(fingerprints)
    if not fingerprints:
        return 0.0
    return sum(count for count in counts.values() if count >= 3) / len(fingerprints)


def _shell_contrast(positions: Sequence[Vector], scale: float) -> float:
    width = 0.14 * scale
    bins = [0] * 29
    for i, left in enumerate(positions):
        for right in positions[i + 1:]:
            distance = _norm(_sub(left, right))
            index = int(distance / width)
            if 0 < index < len(bins):
                bins[index] += 1
    # Divide by spherical-shell volume.  Coefficient of variation is a simple
    # finite-size proxy for sharp radial shells, bounded for stable reporting.
    normalized = [bins[i] / (i * i) for i in range(4, len(bins))]
    mean = sum(normalized) / len(normalized) if normalized else 0.0
    if mean == 0:
        return 0.0
    deviation = math.sqrt(sum((value - mean) ** 2 for value in normalized) /
                          len(normalized))
    return min(3.0, deviation / mean) / 3.0


def _inverse_cell(cell: Cell) -> Cell:
    a, b, c = cell
    determinant = _dot(a, _cross(b, c))
    if abs(determinant) < 1e-12:
        raise ValueError("cell vectors must be linearly independent")
    # Rows which dot Cartesian positions into fractional coordinates.
    return (_scale(1.0 / determinant, _cross(b, c)),
            _scale(1.0 / determinant, _cross(c, a)),
            _scale(1.0 / determinant, _cross(a, b)))


def _space_group(
    positions: Sequence[Vector],
    species: Sequence[str],
    cell: Optional[Cell],
    fractional_positions: Optional[Sequence[Vector]],
    tolerances: Sequence[float],
    allow_periodic_label: bool,
) -> SpaceGroupEvidence:
    if not allow_periodic_label:
        return SpaceGroupEvidence(
            "not-applicable", note="No ordinary space group is assigned to a "
            "nonperiodic or multi-domain classification.")
    if cell is None:
        return SpaceGroupEvidence(
            "cell-required", note="The finite crop is crystal-like, but a "
            "space-group label requires an explicit or independently fitted cell.")
    try:
        import spglib  # type: ignore
    except ImportError:
        return SpaceGroupEvidence(
            "spglib-unavailable", note="Install the optional spglib baseline "
            "dependency to obtain a species-preserving space-group label.")
    if fractional_positions is None:
        inverse = _inverse_cell(cell)
        fractional_positions = tuple(tuple(_dot(row, point) % 1.0
                                              for row in inverse)
                                     for point in positions)  # type: ignore[assignment]
    if len(fractional_positions) != len(positions):
        raise ValueError("fractional_positions must match positions")
    identifiers = {chemical: index + 1 for index, chemical in
                   enumerate(sorted(set(species)))}
    labels = []
    for tolerance in tolerances:
        dataset = spglib.get_symmetry_dataset(
            (cell, fractional_positions,
             [identifiers[chemical] for chemical in species]),
            symprec=tolerance)
        if dataset is None:
            labels.append((float(tolerance), None, None))
        else:
            labels.append((float(tolerance), int(dataset.number),
                           str(dataset.international)))
    valid = [(number, symbol) for _, number, symbol in labels if number is not None]
    if not valid:
        return SpaceGroupEvidence("unresolved", tolerance_labels=tuple(labels),
                                  note="spglib found no symmetry dataset.")
    (number, symbol), count = collections.Counter(valid).most_common(1)[0]
    stability = count / len(labels)
    status = "stable" if stability >= 0.6 and count >= 2 else "tolerance-sensitive"
    note = ("Species identities were preserved during symmetry matching."
            if status == "stable" else
            "The label changes across tolerances; do not treat it as definitive.")
    return SpaceGroupEvidence(status, number, symbol, stability,
                              tuple(labels), note)


def evaluate_structure(
    positions: Sequence[Sequence[float]],
    species: Sequence[str],
    *,
    cell: Optional[Sequence[Sequence[float]]] = None,
    fractional_positions: Optional[Sequence[Sequence[float]]] = None,
    boundary_core_fraction: float = 0.72,
    symmetry_tolerances: Sequence[float] = (1e-4, 3e-4, 1e-3, 3e-3, 1e-2),
) -> StructureEvaluation:
    """Classify a colored point set without using lattice metadata.

    The default radial core removes the most boundary-sensitive atoms from
    local-environment statistics.  Translation matching uses a larger support
    ball and excludes shifted targets outside it.
    """
    points: Tuple[Vector, ...] = tuple(tuple(map(float, point)) for point in positions)  # type: ignore[assignment]
    chemicals = tuple(str(value) for value in species)
    if len(points) != len(chemicals) or len(points) < 16:
        raise ValueError("at least 16 positions with matching species are required")
    if any(len(point) != 3 or not all(math.isfinite(x) for x in point)
           for point in points):
        raise ValueError("positions must contain finite 3-D coordinates")
    if not 0.5 <= boundary_core_fraction <= 0.9:
        raise ValueError("boundary_core_fraction must lie in [0.5, 0.9]")
    center = tuple(sum(point[axis] for point in points) / len(points)
                   for axis in range(3))  # type: ignore[assignment]
    radii = tuple(_norm(_sub(point, center)) for point in points)
    core_radius = _percentile(radii, boundary_core_fraction)
    support_radius = _percentile(radii, 0.90)
    scale, nearest_rows = _nearest_data(points)
    tolerance = max(0.12 * scale, 1e-8)
    translations = _translation_candidates(
        points, chemicals, center, support_radius, scale, tolerance)
    strong = tuple(item for item in translations if item.match_fraction >= 0.72)
    independent = _independent_translations(strong)
    periodicity = (min(item.match_fraction for item in independent)
                   if len(independent) == 3 else
                   (sum(item.match_fraction for item in independent) / 3.0
                    if independent else 0.0))
    closure = _translation_closure(
        independent, points, chemicals, center, support_radius, tolerance)
    recurrence = _local_recurrence(
        nearest_rows, points, center, core_radius, scale)
    contrast = _shell_contrast(points, scale)
    localized = tuple(item for item in translations
                      if 0.24 <= item.match_fraction < 0.72 and
                      item.localization >= 0.18)
    localized_independent = _independent_translations(localized)

    reasons = []
    if (len(independent) == 3 and periodicity >= 0.72 and
            closure >= 0.68):
        category = "crystal"
        confidence = min(0.99, 0.45 + 0.30 * periodicity + 0.24 * closure)
        reasons.append("three independent species-preserving translations "
                       "survive boundary-aware matching and composition")
    elif (len(independent) == 3 and closure < 0.68 and
          recurrence >= 0.50 and contrast >= 0.30):
        category = "quasicrystal-candidate"
        confidence = min(0.88, 0.38 + 0.28 * recurrence +
                         0.20 * contrast + 0.12 * (1.0 - closure))
        reasons.append("three frequent independent displacements occur, but "
                       "they fail the composition test required of a lattice")
    elif len(localized_independent) >= 2 and recurrence >= 0.45:
        category = "polycrystal-like"
        confidence = min(0.90, 0.45 + 0.25 * recurrence +
                         0.08 * len(localized_independent))
        reasons.append("recurrent local environments coexist with translations "
                       "supported only in spatially localized subsets")
    elif recurrence >= 0.50 and contrast >= 0.30:
        category = "quasicrystal-candidate"
        confidence = min(0.86, 0.35 + 0.32 * recurrence + 0.22 * contrast)
        reasons.append("local environments and radial shells recur without "
                       "three convincing global translations")
        if len(independent) == 3 and closure < 0.68:
            reasons.append("the apparent translations fail the doubled-vector "
                           "composition test expected of a lattice")
    else:
        category = "amorphous"
        confidence = min(0.90, 0.52 + 0.25 * (1.0 - recurrence) +
                         0.10 * (1.0 - contrast))
        reasons.append("no global translation basis or sufficiently strong "
                       "recurrent nonperiodic order was detected")
    reasons.append(f"local recurrence={recurrence:.3f}, shell contrast={contrast:.3f}, "
                   f"translation periodicity={periodicity:.3f}, "
                   f"translation closure={closure:.3f}")

    normalized_cell: Optional[Cell] = None
    if cell is not None:
        normalized_cell = tuple(tuple(map(float, row)) for row in cell)  # type: ignore[assignment]
        if len(normalized_cell) != 3 or any(len(row) != 3 for row in normalized_cell):
            raise ValueError("cell must be a 3 by 3 sequence")
    normalized_fractional = None if fractional_positions is None else tuple(
        tuple(map(float, point)) for point in fractional_positions)
    space_group = _space_group(
        points, chemicals, normalized_cell, normalized_fractional,
        symmetry_tolerances, category == "crystal")
    caveats = (
        "This is a finite-sample structural diagnostic, not a thermodynamic phase assignment.",
        "A quasicrystal-candidate requires diffraction, inflation, or superspace confirmation.",
        "Boundary handling assumes an approximately radial crop; strongly anisotropic crops need an explicit support mask.",
    )
    return StructureEvaluation(
        category, confidence, len(points), len(set(chemicals)), scale,
        core_radius, sum(radius <= core_radius for radius in radii),
        len(independent), periodicity, closure, recurrence, contrast,
        len(localized_independent), translations[:12], space_group,
        tuple(reasons), caveats)


__all__ = [
    "SpaceGroupEvidence", "StructureEvaluation", "TranslationEvidence",
    "evaluate_structure",
]
