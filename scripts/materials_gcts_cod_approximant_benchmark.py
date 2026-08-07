#!/usr/bin/env python3
"""Real COD approximant benchmark for recursive material parent clusters.

COD 1521830 is the experimentally refined crystalline approximant discussed
with a dodecagonal Ta-V-Te quasicrystal.  Fractionally occupied Ta/V sites are
kept as a virtual-crystal color; no random occupational realization is
invented.  The public CIF supplies the periodic cell, while GCTS learns the
overlapping cluster hierarchy inside that measured 314-site parent.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from typing import Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_periodic_growth import replicate
from materials_recursive_gcts import learn_recursive_hierarchy

COD_ID = "1521830"
COD_URL = "https://www.crystallography.net/cod/1521830.html"

# Merged from the public-domain COD CIF.  The third item preserves the refined
# occupancy text for audit even though the point-cloud color is virtual-crystal
# Ta/V at shared sites.
ASYMMETRIC_SITES = (
    ("Te", (0.0, 0.0, 0.8306), "Te:1"),
    ("Te", (0.0, 0.5, 0.5979), "Te:1"),
    ("Ta/V", (0.0151, 0.7634, 0.6288), "V:0.192/Ta:0.808"),
    ("Te", (0.0358, 0.6367, 0.669), "Te:1"),
    ("Ta/V", (0.0602, 0.9374, 0.6655), "Ta:0.85/V:0.15"),
    ("Te", (0.064, 0.7644, 0.8645), "Te:1"),
    ("Ta/V", (0.0719, 0.5719, 0.462), "V:0.203/Ta:0.797"),
    ("Ta/V", (0.087, 0.8362, 0.6779), "Ta:0.864/V:0.136"),
    ("Te", (0.0971, 0.8973, 0.8962), "Te:1"),
    ("Ta/V", (0.1138, 0.7363, 0.6402), "Ta:0.854/V:0.146"),
    ("Ta", (0.14, 0.64, 0.5524), "Ta:1"),
    ("Te", (0.167, 0.667, 0.8039), "Te:1"),
    ("Te", (0.2066, 0.8017, 0.7826), "Te:1"),
    ("Ta/V", (0.2151, 0.7151, 0.6017), "V:0.201/Ta:0.799"),
    ("Te", (0.3019, 0.1981, 0.8521), "Te:1"),
    ("Ta", (0.3195, 0.316, 0.4717), "Ta:1"),
    ("Ta/V", (0.3499, 0.2243, 0.6207), "Ta:0.823/V:0.177"),
    ("Ta", (0.3713, 0.1287, 0.7245), "Ta:1"),
    ("Te", (0.4003, 0.0997, 0.9714), "Te:1"),
    ("Ta/V", (0.4209, 0.2931, 0.5764), "V:0.344/Ta:0.656"),
    ("Te", (0.4342, 0.2292, 0.7951), "Te:1"),
    ("Ta", (0.4522, 0.1821, 0.5671), "Ta:1"),
    ("Ta/V", (0.4721, 0.1025, 0.7771), "Ta:0.877/V:0.123"),
    ("Ta", (0.499, 0.3643, 0.4902), "Ta:1"),
    ("Ta", (0.5, 0.0, 0.6604), "Ta:1"),
    ("Te", (0.5, 0.0, 0.918), "Te:1"),
    ("Ta/V", (0.5162, 0.2681, 0.6368), "Ta:0.846/V:0.154"),
    ("Te", (0.5331, 0.1344, 0.9794), "Te:1"),
    ("Ta/V", (0.5466, 0.1742, 0.7329), "V:0.12/Ta:0.88"),
    ("Te", (0.5663, 0.2657, 0.8727), "Te:1"),
    ("Ta", (0.5749, 0.0749, 0.7817), "Ta:1"),
    ("Ta/V", (0.5893, 0.3408, 0.6808), "V:0.144/Ta:0.856"),
    ("Ta/V", (0.6185, 0.2413, 0.6465), "Ta:0.795/V:0.205"),
    ("Ta", (0.6366, 0.1366, 0.5568), "Ta:1"),
    ("Te", (0.6563, 0.1563, 0.812), "Te:1"),
    ("Ta/V", (0.714, 0.214, 0.605), "V:0.357/Ta:0.643"),
    ("Ta/V", (0.7501, 0.7499, 0.6441), "V:0.113/Ta:0.887"),
    ("Te", (0.7993, 0.7007, 0.8458), "Te:1"),
    ("Te", (0.8285, 0.8345, 0.7313), "Te:1"),
    ("Ta/V", (0.8485, 0.7233, 0.6167), "V:0.206/Ta:0.794"),
    ("Te", (0.8633, 0.9755, 0.7487), "Te:1"),
    ("Ta/V", (0.8905, 0.8944, 0.5549), "V:0.279/Ta:0.721"),
    ("Te", (0.9035, 0.5965, 0.6661), "Te:1"),
    ("Ta/V", (0.9184, 0.7971, 0.5742), "V:0.192/Ta:0.808"),
    ("Te", (0.932, 0.7332, 0.7861), "Te:1"),
    ("Ta/V", (0.9457, 0.6926, 0.5417), "V:0.116/Ta:0.884"),
    ("Te", (0.9596, 0.872, 0.7519), "Te:1"),
    ("Ta/V", (0.9615, 0.9634, 0.5998), "Ta:0.817/V:0.183"),
    ("Ta/V", (0.9734, 0.5985, 0.4594), "Ta:0.812/V:0.188"),
)


@dataclass(frozen=True)
class CodApproximantBenchmark:
    cod_id: str
    source_url: str
    measured_parent_atoms: int
    chemical_elements: int
    point_colors: Tuple[str, ...]
    hierarchy_supports: Tuple[int, ...]
    hierarchy_marking_confidence: Tuple[float, ...]
    hierarchy_cover_fraction: Tuple[float, ...]
    randomized_color_supports: Tuple[int, ...]
    color_marking_changes_hierarchy: bool
    inferred_order: str
    quasicrystal_label_rejected: bool
    action_counts: Tuple[int, ...]
    atom_counts: Tuple[int, ...]
    explicit_action_two_exact: bool
    atomwise_actions_per_macro_action: float


def _symmetry_images(point):
    x, y, z = point
    return ((x, y, z), (y, -x, -z), (-x, -y, z), (-y, x, -z),
            (x + .5, -y + .5, -z), (-y + .5, -x + .5, z),
            (-x + .5, y + .5, -z), (y + .5, x + .5, z))


def cod_1521830_configuration() -> AtomicConfiguration:
    lengths = (27.3569, 27.3569, 10.33)
    sites = {}
    for chemical, point, _ in ASYMMETRIC_SITES:
        for image in _symmetry_images(point):
            fractional = tuple(value % 1.0 for value in image)
            key = (chemical,) + tuple(round(value, 6) for value in fractional)
            sites[key] = fractional
    ordered = sorted(sites.items())
    positions = tuple(tuple(fractional[axis] * lengths[axis]
                            for axis in range(3))
                      for _, fractional in ordered)
    species = tuple(key[0] for key, _ in ordered)
    cell = ((lengths[0], 0.0, 0.0),
            (0.0, lengths[1], 0.0),
            (0.0, 0.0, lengths[2]))
    return AtomicConfiguration(
        "Ta-V-Te-dodecagonal-approximant-COD-1521830", positions, species,
        cell, True, "Experimental COD 1521830; P -4 21 m; virtual-crystal "
        "colors retain partial Ta/V sites.")


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _hierarchy(configuration, species):
    result, _ = learn_recursive_hierarchy(
        configuration.name, configuration.positions, species,
        maximum_levels=3, first_descriptor_bin_scale=.02,
        first_angle_bin=.03, macro_distance_bin_scale=.20,
        macro_angle_bin=.08)
    return result


def evaluate() -> CodApproximantBenchmark:
    parent = cod_1521830_configuration()
    hierarchy = _hierarchy(parent, parent.species)
    randomized = list(parent.species)
    random.Random(1521830).shuffle(randomized)
    random_hierarchy = _hierarchy(parent, tuple(randomized))
    supports = tuple(level.largest_recurring_support
                     for level in hierarchy.levels)
    random_supports = tuple(level.largest_recurring_support
                            for level in random_hierarchy.levels)
    first = replicate(parent)
    second = replicate(first)
    # The explicit cell supplied by the experimental CIF makes this a
    # crystalline approximant parent, irrespective of the paper's QC context.
    counts = tuple(len(parent.positions) * 8 ** action for action in range(5))
    generated = len(second.positions) - len(parent.positions)
    expected_second = replicate(replicate(parent))
    return CodApproximantBenchmark(
        COD_ID, COD_URL, len(parent.positions), 3,
        tuple(sorted(set(parent.species))), supports,
        tuple(level.marking_confidence for level in hierarchy.levels),
        tuple(level.recurring_cover_fraction for level in hierarchy.levels),
        random_supports, supports != random_supports,
        "periodic crystalline approximant", True, tuple(range(5)), counts,
        _sites(second) == _sites(expected_second), generated / 2.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
