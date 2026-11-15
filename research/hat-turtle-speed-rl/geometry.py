"""Exact unmarked geometry and frontier search for generating source patches."""

from collections import defaultdict
from functools import lru_cache
from random import Random
from time import perf_counter

from model import Model, ref

ROOT = (0, 0, 0)
GROUP = ref.SYMMETRIES
INVERSE = tuple(GROUP.index((g[0], tuple(g[1].index(j) for j in range(3)))) for g in GROUP)
COMPOSE = tuple(tuple(GROUP.index(ref.compose(g, h)) for h in GROUP) for g in GROUP)


def transform(o, x, y):
    z = (x, y, -x-y)
    s, p = GROUP[o]
    return s*z[p[0]], s*z[p[1]]


def move(a, b):
    """Apply frame a to placement b (translations in unscaled lattice units)."""
    o, x, y = a
    p, u, v = b
    u, v = transform(o, u, v)
    return COMPOSE[o][p], x+u, y+v


def inverse(a):
    o, x, y = a
    p = INVERSE[o]
    x, y = transform(p, -x, -y)
    return p, x, y


def normalize(keys):
    return min(tuple(sorted(move(inverse(a), b) for b in keys)) for a in keys)


def norm(x, y):
    return x*x + x*y + y*y


def atom_neighbors():
    edges = defaultdict(list)
    for dx in (-18, 0, 18):
        for dy in (-18, 0, 18):
            for (a, b), triangle in ref.TEMPLATES.items():
                corners = tuple((3*x+dx, 3*y+dy) for x, y in triangle)
                for j in range(3):
                    edge = tuple(sorted((corners[j], corners[(j+1) % 3])))
                    edges[edge].append((a+dx, b+dy))
    adjacent = defaultdict(set)
    for pair in edges.values():
        if len(pair) == 2:
            a, b = pair
            adjacent[a].add(b)
            adjacent[b].add(a)
    return {a: tuple(sorted(adjacent[a])) for a in ref.TEMPLATES}


NEIGHBORS = atom_neighbors()
assert all(len(near) == 3 for near in NEIGHBORS.values())


class Geometry:
    def __init__(self, name):
        self.model = Model(name)
        self.name = name
        angles, atoms = [], []
        for orientation in self.model.orientations:
            angles.append(tuple((x//18, y//18, v) for (x, y, _), v in orientation
                                if x % 18 == 0 and y % 18 == 0))
            atoms.append(tuple((x, y) for (x, y, _), _ in orientation if x % 18 or y % 18))
        self.angles, self.atoms = tuple(angles), tuple(atoms)
        by_residue = defaultdict(list)
        for o, entries in enumerate(self.atoms):
            for x, y in entries:
                by_residue[x % 18, y % 18].append((o, x, y))
        self.by_residue = dict(by_residue)
        self.align = tuple((o, -x, -y, v) for o, entries in enumerate(self.angles)
                           for x, y, v in entries)
        conflicts = set()
        for x, y in self.atoms[0]:
            for o, u, v in self.by_residue[x % 18, y % 18]:
                conflicts.add((o, (x-u)//18, (y-v)//18))
        self.conflicts = tuple(tuple(sorted(move((o, 0, 0), k) for k in conflicts))
                               for o in range(len(GROUP)))
        self.footprint = lru_cache(maxsize=24000)(self.footprint)
        self.contact = {}
        own_boundary = {(x, y) for x, y, v in self.angles[0] if v < 12}
        for o, a, b, _ in self.align:
            for x, y in own_boundary:
                key = o, x+a, y+b
                if key not in conflicts:
                    self.contact[key] = self.contact.get(key, 0)+1

    def footprint(self, key):
        o, x, y = key
        return tuple((18*x+a, 18*y+b) for a, b in self.atoms[o])

    def touches(self, a, b):
        return self.contact.get(move(inverse(a), b), 0) > 0

    def verify(self, keys):
        return self.model.verify([(o, (18*x, 18*y, -18*(x+y))) for o, x, y in keys])

    def grow(self, seed, size, budget, offset=(0, 0)):
        """Global dead/forced checks, then earliest generation and degree."""
        rng = Random(seed)
        totals, generations, blocked = {}, {}, {}
        order, best = [], []
        cx, cy = offset
        # Vary the early region and branch order across independently seeded trajectories.
        core = {(x, y) for x in range(cx-5, cx+6) for y in range(cy-5, cy+6)
                if norm(x-cx, y-cy) <= 16}
        obligation = {p: 0 for p in core}
        nodes = 0
        started = perf_counter()

        @lru_cache(maxsize=4000)
        def options(p):
            x, y = p
            return tuple((o, x+a, y+b, v) for o, a, b, v in self.align)

        def push(k):
            o, x, y = k
            entries = [((x+a, y+b), v) for a, b, v in self.angles[o]]
            generation = 1 + min((generations[p] for p, _ in entries if p in generations), default=-1)
            frame = [(p, totals.get(p, 0), generations.get(p, 0)) for p, _ in entries]
            for p, v in entries:
                totals[p] = totals.get(p, 0)+v
                generations[p] = min(generations.get(p, generation), generation, obligation.get(p, generation))
            prohibitions = [(j, x+a, y+b) for j, a, b in self.conflicts[o]]
            for b in prohibitions:
                blocked[b] = blocked.get(b, 0)+1
            order.append(k)
            return frame, prohibitions

        def pop(frame, prohibitions):
            order.pop()
            for p, total, generation in frame:
                if total:
                    totals[p], generations[p] = total, generation
                else:
                    del totals[p], generations[p]
            for k in prohibitions:
                if blocked[k] == 1:
                    del blocked[k]
                else:
                    blocked[k] -= 1

        def visit():
            nonlocal best, nodes
            nodes += 1
            legality = {}
            choice, rank = (), None
            for p in totals.keys() | core:
                total = totals.get(p, 0)
                if total == 12:
                    continue
                choices = []
                for o, x, y, value in options(p):
                    if total+value > 12:
                        continue
                    k = o, x, y
                    if k in blocked:
                        continue
                    if k not in legality:
                        legality[k] = all(totals.get((x+a, y+b), 0)+v <= 12 for a, b, v in self.angles[o])
                    if legality[k]:
                        choices.append(k)
                if not choices:
                    return False
                priority = (0, p) if len(choices) == 1 else (1, generations.get(p, 0), len(choices), p)
                if rank is None or priority < rank:
                    rank, choice = priority, choices
            if len(order) > len(best):
                best = list(order)
            if len(order) >= size:
                return True
            rng.shuffle(choice)
            for k in choice:
                if nodes >= budget:
                    break
                frame = push(k)
                if visit():
                    return True
                pop(*frame)
            return False

        push(ROOT)
        visit()
        return dict(seed=seed, offset=offset, placements=best, nodes=nodes, seconds=perf_counter()-started)
