#!/usr/bin/env python3
"""Deterministic, offline oracle for the published icosahedral Cd5.7Yb model.

This is a standard-library port of M. Feuerbacher's vectorized notebook V1.5.
It retains the published six-dimensional cut-and-project parameters, occupation
domains, truncations, and physical-space shifts.  ``Zn`` in the source model is
an explicit placeholder for an empty cluster centre, not a constituent of
Cd5.7Yb, and is therefore omitted unless ``include_empty_centres`` is true.

Provenance
----------
Article: https://doi.org/10.1107/S2053273326006601
Archive: https://doi.org/10.5281/zenodo.21470195 (CC BY 4.0)
Archived file: iCdYb_basic_V1_5.ipynb
SHA-256: b0de87a489e23b6ceed43c64728b132e20ba5aef971aee210f065ce9774cc222

The port intentionally has no network or third-party runtime dependency so a
real-material transfer benchmark can use an immutable oracle in offline tests.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from typing import Iterable, Sequence

Vector = tuple[float, float, float]

SOURCE = {
    "model": "icosahedral Cd5.7Yb",
    "archive_title": "Calculation of physical-space structure of icosahedral CdYb",
    "creator": "Michael Feuerbacher",
    "creator_orcid": "0000-0003-2882-4960",
    "publication_date": "2026-07-21",
    "implementation": "iCdYb_basic_V1_5.ipynb",
    "version": "1.5",
    "article_doi": "10.1107/S2053273326006601",
    "archive_doi": "10.5281/zenodo.21470195",
    "license": "CC-BY-4.0",
    "archive_md5": "d93885209a8721b33b85f5768913e042",
    "archive_sha256": "b0de87a489e23b6ceed43c64728b132e20ba5aef971aee210f065ce9774cc222",
}

TAU = (1.0 + math.sqrt(5.0)) / 2.0
R = 1.0 / math.sqrt(2.0 * (2.0 + TAU))
A0 = 5.689 * math.sqrt(2.0)
SHIFT_SCALE = A0 / TAU**5

PROJ_PAR = (
    (1.0, TAU, 0.0, -1.0, TAU, 0.0),
    (TAU, 0.0, 1.0, TAU, 0.0, -1.0),
    (0.0, 1.0, TAU, 0.0, -1.0, TAU),
)
PROJ_PERP = (
    (-TAU, 1.0, 0.0, TAU, 1.0, 0.0),
    (1.0, 0.0, -TAU, 1.0, 0.0, TAU),
    (0.0, -TAU, 1.0, 0.0, TAU, 1.0),
)


def _scaled(rows: Sequence[Sequence[float]], scale: float) -> tuple[Vector, ...]:
    return tuple(tuple(scale * x for x in row) for row in rows)  # type: ignore[return-value]


PERP5 = _scaled((
    (-TAU, 1, 0), (1, 0, -TAU), (0, -TAU, 1),
    (TAU, 1, 0), (1, 0, TAU), (0, TAU, 1),
    (TAU, -1, 0), (-1, 0, TAU), (0, TAU, -1),
    (-TAU, -1, 0), (-1, 0, -TAU), (0, -TAU, -1),
), 1.0 / math.sqrt(2.0 + TAU))

PERP3 = _scaled((
    (-1, 0, 2-TAU), (-1+TAU, 1-TAU, 1-TAU), (0, 2-TAU, 1),
    (1-TAU, 1-TAU, 1-TAU), (1, 0, 2-TAU), (-1+TAU, -1+TAU, 1-TAU),
    (0, -2+TAU, 1), (1-TAU, -1+TAU, 1-TAU), (-2+TAU, 1, 0),
    (2-TAU, 1, 0), (1, 0, -2+TAU), (1-TAU, -1+TAU, -1+TAU),
    (0, -2+TAU, -1), (-1+TAU, -1+TAU, -1+TAU), (-1, 0, -2+TAU),
    (1-TAU, 1-TAU, -1+TAU), (0, 2-TAU, -1), (-1+TAU, 1-TAU, -1+TAU),
    (2-TAU, -1, 0), (-2+TAU, -1, 0),
), 1.0 / math.sqrt(6.0 - 3.0 * TAU))

PAR3 = _scaled((
    (-TAU, 0, 1+2*TAU), (-1-TAU, 1+TAU, 1+TAU), (0, 1+2*TAU, TAU),
    (1+TAU, 1+TAU, 1+TAU), (TAU, 0, 1+2*TAU), (-1-TAU, -1-TAU, 1+TAU),
    (0, -1-2*TAU, TAU), (1+TAU, -1-TAU, 1+TAU), (-1-2*TAU, TAU, 0),
    (1+2*TAU, TAU, 0), (TAU, 0, -1-2*TAU), (1+TAU, -1-TAU, -1-TAU),
    (0, -1-2*TAU, -TAU), (-1-TAU, -1-TAU, -1-TAU), (-TAU, 0, -1-2*TAU),
    (1+TAU, 1+TAU, -1-TAU), (0, 1+2*TAU, -TAU), (-1-TAU, 1+TAU, -1-TAU),
    (1+2*TAU, -TAU, 0), (-1-2*TAU, -TAU, 0),
), 1.0 / math.sqrt(6.0 + 9.0 * TAU))

_PERP2_HALF = (
    (0, 0, 2), (2, 0, 0), (0, 2, 0), (-1, -TAU, 1-TAU),
    (-1, TAU, 1-TAU), (1, TAU, 1-TAU), (1, -TAU, 1-TAU),
    (TAU, 1-TAU, 1), (TAU, -1+TAU, 1), (-TAU, -1+TAU, 1),
    (-TAU, 1-TAU, 1), (-1+TAU, 1, -TAU), (-1+TAU, -1, -TAU),
    (1-TAU, -1, -TAU), (1-TAU, 1, -TAU),
)
PERP2 = _scaled(_PERP2_HALF + tuple(tuple(-x for x in row) for row in _PERP2_HALF), 0.5)

_PAR2_HALF = (
    (0, 0, 2*TAU), (2*TAU, 0, 0), (0, 2*TAU, 0),
    (-TAU, 1, 1+TAU), (-TAU, -1, 1+TAU), (TAU, -1, 1+TAU),
    (TAU, 1, 1+TAU), (-1, 1+TAU, TAU), (-1, -1-TAU, TAU),
    (1, -1-TAU, TAU), (1, 1+TAU, TAU), (-1-TAU, TAU, 1),
    (-1-TAU, -TAU, 1), (1+TAU, -TAU, 1), (1+TAU, TAU, 1),
)
PAR2 = _scaled(_PAR2_HALF + tuple(tuple(-x for x in row) for row in _PAR2_HALF), 1.0 / (2.0 * TAU))


@dataclass(frozen=True)
class Site:
    name: str
    offset: tuple[float, float, float, float, float, float]
    radii: tuple[float, ...]
    axis: Vector | None = None


SITES = (
    Site("V", (0, 0, 0, 0, 0, 0), (0.1*A0, 0.879*A0, 1.143*A0)),
    Site("B", (.5, .5, .5, .5, .5, -.5), (.335*A0, .94*A0, 1.49*A0)),
    Site("E1", (.5, 0, 0, 0, 0, 0), (1.29*.492*A0, .492*A0), (-TAU, 1, 0)),
    Site("E2", (0, .5, 0, 0, 0, 0), (1.29*.492*A0, .492*A0), (1, 0, -TAU)),
    Site("E3", (0, 0, .5, 0, 0, 0), (1.29*.492*A0, .492*A0), (0, -TAU, 1)),
    Site("E4", (0, 0, 0, .5, 0, 0), (1.29*.492*A0, .492*A0), (TAU, 1, 0)),
    Site("E5", (0, 0, 0, 0, .5, 0), (1.29*.492*A0, .492*A0), (1, 0, TAU)),
    Site("E6", (0, 0, 0, 0, 0, .5), (1.29*.492*A0, .492*A0), (0, TAU, 1)),
)


@dataclass(frozen=True)
class CdYbAtoms:
    symbols: tuple[str, ...]
    positions: tuple[Vector, ...]
    source_sites: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.positions)

    def canonical_sha256(self, decimals: int = 10) -> str:
        records = sorted((s, *(round(x, decimals) for x in p))
                         for s, p in zip(self.symbols, self.positions))
        payload = json.dumps(records, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode()).hexdigest()


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x*y for x, y in zip(a, b))


def _add(a: Vector, b: Vector, scale: float = 1.0) -> Vector:
    return tuple(x + scale*y for x, y in zip(a, b))  # type: ignore[return-value]


def _project(point: Sequence[float], matrix: Sequence[Sequence[float]]) -> Vector:
    return tuple(A0 * R * _dot(row, point) for row in matrix)  # type: ignore[return-value]


def _norm2(point: Sequence[float]) -> float:
    return _dot(point, point)


def _first_translated_cut(point: Vector, radius: float,
                          directions: Sequence[Vector], distance: float) -> int | None:
    for index, direction in enumerate(directions):
        shifted = _add(point, direction, distance)
        if _norm2(shifted) < radius*radius:
            return index
    return None


def _ellipsoid_basis(direction: Vector) -> tuple[Vector, Vector, Vector]:
    if direction[0] == 0:
        y = (1.0, 0.0, 0.0)
    elif direction[1] == 0:
        y = (0.0, 1.0, 0.0)
    elif direction[2] == 0:
        y = (0.0, 0.0, 1.0)
    else:
        raise ValueError("ellipsoid direction needs a zero component")
    scale = 1.0 / math.sqrt(TAU + 2.0)
    x = tuple(scale*v for v in direction)
    z = (scale*(direction[1]*y[2] - direction[2]*y[1]),
         scale*(direction[2]*y[0] - direction[0]*y[2]),
         scale*(direction[0]*y[1] - direction[1]*y[0]))
    return x, y, z  # type: ignore[return-value]


def _inside_ellipsoid(point: Vector, radii: tuple[float, ...], axis: Vector) -> bool:
    a, b = radii
    x, y, z = _ellipsoid_basis(axis)
    return (_dot(point, x)**2 / b**2 +
            (_dot(point, y)**2 + _dot(point, z)**2) / a**2) < 1.0


def _lattice(max_index: int) -> Iterable[tuple[int, ...]]:
    values = range(-max_index, max_index + 1)
    return itertools.product(values, repeat=6)


def generate_cdyb(max_index: int = 3, box: Sequence[float] = (50.0, 50.0, 50.0),
                  include_empty_centres: bool = False) -> CdYbAtoms:
    """Generate a centred rectangular crop of the published Cd5.7Yb model."""
    if max_index < 0 or len(box) != 3 or any(value <= 0 for value in box):
        raise ValueError("max_index must be nonnegative and box must have three positive sides")
    half = tuple(value/2.0 for value in box)
    projected_nodes = tuple((_project(node, PROJ_PAR), _project(node, PROJ_PERP))
                            for node in _lattice(max_index))
    symbols: list[str] = []
    positions: list[Vector] = []
    source_sites: list[str] = []

    def append(symbol: str, point: Vector, site: str) -> None:
        if symbol != "Zn" or include_empty_centres:
            symbols.append(symbol); positions.append(point); source_sites.append(site)

    for site in SITES:
        par_offset = _project(site.offset, PROJ_PAR)
        perp_offset = _project(site.offset, PROJ_PERP)
        candidates = []
        for node_par, node_perp in projected_nodes:
            par = _add(node_par, par_offset)
            if all(-limit <= value <= limit for value, limit in zip(par, half)):
                candidates.append((par, _add(node_perp, perp_offset)))
        if site.name.startswith("E"):
            assert site.axis is not None
            for par, perp in candidates:
                if _inside_ellipsoid(perp, site.radii, site.axis):
                    append("Cd", par, site.name)
            continue
        r1, r2, r3 = site.radii
        for par, perp in candidates:
            d2 = _norm2(perp)
            if site.name == "V":
                if d2 < r1*r1:
                    append("Zn", par, "V")
                elif d2 < r2*r2:
                    append("Cd", par, "V")
                elif d2 < r3*r3:
                    index = _first_translated_cut(perp, r3-r2, PERP3, r3)
                    append("Cd", _add(par, PAR3[index], SHIFT_SCALE) if index is not None else par, "V")
            elif site.name == "B":
                if d2 < r1*r1:
                    cut = _first_translated_cut(perp, r1, PERP5, r2-r1)
                    append("Yb" if cut is not None else "Zn", par, "B")
                elif d2 < r2*r2:
                    append("Yb", par, "B")
                elif d2 < r3*r3:
                    if _first_translated_cut(perp, r3-r2, PERP5, r3) is not None:
                        continue
                    index = None
                    for radius, factor in (((r3-r2)/2.0, 1.0), ((r3-r2)/4.0, .75)):
                        current = _first_translated_cut(perp, radius, PERP2, r3*factor)
                        if current is not None:
                            index = current
                    append("Cd", _add(par, PAR2[index], SHIFT_SCALE) if index is not None else par, "B")
    return CdYbAtoms(tuple(symbols), tuple(positions), tuple(source_sites))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=float, default=50.0)
    parser.add_argument("--max-index", type=int, default=3)
    parser.add_argument("--include-empty-centres", action="store_true")
    args = parser.parse_args()
    atoms = generate_cdyb(args.max_index, (args.size,)*3, args.include_empty_centres)
    counts = {symbol: atoms.symbols.count(symbol) for symbol in sorted(set(atoms.symbols))}
    print(json.dumps({"atoms": atoms.count, "species": counts,
                      "canonical_sha256": atoms.canonical_sha256(),
                      "source": SOURCE}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
