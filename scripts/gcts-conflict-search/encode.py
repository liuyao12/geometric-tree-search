#!/usr/bin/env python3
"""Deterministic two-corona DIMACS generator. Python standard library only."""
import argparse
from itertools import combinations, product
from pathlib import Path

OFFSETS = tuple(product((-1, 0, 1), repeat=3))
# Orientation IDs are part of the published variable numbering.
SHAPES = tuple(
    tuple([(0, 0, 0)] + [tuple(d if k == a else 0 for k in range(3))
                         for a in axes for d in (-2, -1, 1, 2)])
    for axes in ((0, 1), (0, 2), (1, 2))
)


def cells(placement, shapes=SHAPES):
    orientation, anchor = placement
    return frozenset(tuple(a + b for a, b in zip(v, anchor))
                     for v in shapes[orientation])


def halo(points):
    return {tuple(a + b for a, b in zip(p, d))
            for p in points for d in OFFSETS}


def candidates(target, root, shapes=SHAPES):
    result = set()
    for q in target:
        for orientation, shape in enumerate(shapes):
            for voxel in shape:
                placement = (orientation, tuple(a - b for a, b in zip(q, voxel)))
                if placement not in result and cells(placement, shapes).isdisjoint(root):
                    result.add(placement)
    return result


def geometry(shapes=SHAPES):
    root = cells((0, (0, 0, 0)), shapes)
    near = halo(root) - root
    first = candidates(near, root, shapes)
    requirements = {s: halo(cells(s, shapes)) - root - cells(s, shapes) for s in first}
    target = near.union(*requirements.values())
    universe = sorted(candidates(target, root, shapes))
    ids = {s: i for i, s in enumerate(universe, 1)}
    by_voxel = {}
    for s in universe:
        for q in cells(s, shapes):
            by_voxel.setdefault(q, []).append(ids[s])
    overlaps = set()
    for incident in by_voxel.values():
        overlaps.update(combinations(incident, 2))
    return dict(root=root, near=near, first=first, requirements=requirements,
                target=target, universe=universe, ids=ids, by_voxel=by_voxel,
                overlaps=overlaps)


def clauses(g):
    for a, b in sorted(g['overlaps']):
        yield [-a, -b]
    for q in sorted(g['near']):
        yield g['by_voxel'][q]
    for s in sorted(g['first']):
        for q in sorted(g['requirements'][s]):
            yield [-g['ids'][s]] + g['by_voxel'][q]


def stats(g):
    return dict(variables=len(g['universe']), first_candidates=len(g['first']),
                root_required_cells=len(g['near']), overlap_pairs=len(g['overlaps']),
                clauses=len(g['overlaps']) + len(g['near']) +
                sum(map(len, g['requirements'].values())))


def write(g, cnf, placements):
    info = stats(g)
    with Path(cnf).open('w', encoding='ascii', newline='\n') as out:
        out.write('p cnf {variables} {clauses}\n'.format(**info))
        for clause in clauses(g):
            out.write(' '.join(map(str, clause)) + ' 0\n')
    with Path(placements).open('w', encoding='ascii', newline='\n') as out:
        for orientation, anchor in g['universe']:
            out.write(' '.join(map(str, (orientation,) + anchor)) + '\n')
    return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('build'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    print(write(geometry(), args.output / 'two-corona.cnf', args.output / 'placements.txt'))
