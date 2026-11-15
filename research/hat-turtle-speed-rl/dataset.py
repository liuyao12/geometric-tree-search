"""Generate disjoint source trajectories and fixed-boundary cavity tasks."""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random
from time import perf_counter

from geometry import Geometry, NEIGHBORS, norm


def cavities(geometry, patch, seed, heldout):
    rng = Random(seed)
    footprints = {k: geometry.footprint(k) for k in patch}
    owners = {p: k for k, atoms in footprints.items() for p in atoms}
    adjacent = {k: set() for k in patch}
    for (x, y), tile in owners.items():
        a, b = x % 18, y % 18
        for u, v in NEIGHBORS[a, b]:
            other = owners.get((x-a+u, y-b+v))
            if tile != other:
                adjacent[tile].add(other)
    eligible = {k for k, ns in adjacent.items() if None not in ns}
    centers = sorted(eligible)
    rng.shuffle(centers)
    cases, seen = [], set()
    sizes = (12, 20, 32, 44) if heldout else (6, 10, 14, 20, 27)
    for i, center in enumerate(centers[:16]):
        _, x, y = center
        wanted = sizes[i % len(sizes)]
        selected, queue = {center}, adjacent[center] & eligible
        while queue and len(selected) < wanted:
            tile = min(queue, key=lambda k: (norm(k[1]-x, k[2]-y), k))
            selected.add(tile)
            queue = (queue | (adjacent[tile] & eligible)) - selected
        if len(selected) < max(4, wanted-4):
            continue
        cavity = frozenset(selected)
        if cavity in seen:
            continue
        seen.add(cavity)
        collar = set.union(*(adjacent[k] for k in selected)) - selected
        cases.append(dict(id=f'{seed}-{i:02}', source=seed, boundary=sorted(collar),
                          atoms=sorted(p for k in selected for p in footprints[k]),
                          witness=sorted(selected)))
    return cases


def generate(job):
    shape, seed, heldout, size, nodes = job
    g = Geometry(shape)
    rng = Random(seed ^ 5033)
    patch = g.grow(seed, size, nodes, (rng.randrange(-2, 3), rng.randrange(-2, 3)))
    assert not g.verify(patch['placements'])['markValues']
    cases = cavities(g, patch['placements'], seed, heldout)
    print(shape, 'heldout' if heldout else 'train', seed, len(patch['placements']),
          patch['nodes'], len(cases), flush=True)
    return dict(split='test' if heldout else 'train', patch=patch, cases=cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--train', type=int, default=20)
    parser.add_argument('--test', type=int, default=8)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--size', type=int, default=96)
    parser.add_argument('--nodes', type=int, default=2200)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    jobs = [(shape, base+i*9967, test, args.size, args.nodes)
            for test, base, count in ((False, 10241, args.train), (True, 902391, args.test))
            for i in range(count) for shape in ('hat', 'turtle')]
    started = perf_counter()
    with ProcessPoolExecutor(args.workers) as pool:
        for job, result in zip(jobs, pool.map(generate, jobs)):
            shape, seed, *_ = job
            (args.directory/f'{shape}-{seed}.json').write_text(json.dumps(result))
    print('Dataset wall seconds', round(perf_counter()-started, 3), flush=True)


if __name__ == '__main__':
    main()
