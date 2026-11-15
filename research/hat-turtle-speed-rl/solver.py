"""Point-incidence GCTS on a fixed cavity with optional learned cluster moves."""

from collections import Counter, defaultdict
from functools import lru_cache
from math import exp, log
from random import Random
from time import perf_counter

from geometry import NEIGHBORS, inverse, move, ref, transform
from model import point_data

popcount = getattr(int, 'bit_count', lambda n: bin(n).count('1'))


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


@lru_cache(maxsize=32)
def rasterize(vertices, orientation):
    loop = tuple((*p, -sum(p)) for p in (transform(orientation, *q[:2]) for q in vertices))
    return ref.atomize(tuple(p[:2] for p in loop)), tuple(point_data(loop).items())


def verify(g, atoms, boundary, patch):
    """Rerasterize polygons independently of every solver mask."""
    occupied = set()
    actual = set()
    angles = Counter()
    for keys, inside in ((boundary, False), (patch, True)):
        for o, x, y in keys:
            raster, values = rasterize(g.model.vertices, o)
            footprint = {(18*x+a, 18*y+b) for a, b in raster}
            assert occupied.isdisjoint(footprint)
            occupied.update(footprint)
            if inside:
                actual.update(footprint)
            for (a, b, _), v in values:
                angles[x+a, y+b] += v
    assert max(angles.values()) <= 12
    assert actual == set(atoms)
    for x, y in actual:
        a, b = x % 18, y % 18
        assert all((x-a+u, y-b+v) in occupied for u, v in NEIGHBORS[a, b])


class Cavity:
    def __init__(self, g, points):
        points = frozenset(points)
        self.tile_count = len(points)//len(g.atoms[0])
        points = tuple(sorted(points))
        point_index = {p: i for i, p in enumerate(points)}
        by_residue = defaultdict(list)
        for p in points:
            by_residue[p[0] % 18, p[1] % 18].append(p)
        rows = {}
        for o, offsets in enumerate(g.atoms):
            # One fixed atom suffices to enumerate every translation. Test
            # extremal atoms first so most boundary crossings fail quickly.
            ends = [min(offsets), max(offsets), min(offsets, key=lambda p: p[1]),
                    max(offsets, key=lambda p: p[1])]
            ordered = tuple(dict.fromkeys(ends+list(offsets)))
            a, b = ordered[0]
            for x, y in by_residue[a % 18, b % 18]:
                dx, dy = x-a, y-b
                indices = []
                for u, v in ordered:
                    i = point_index.get((dx+u, dy+v))
                    if i is None:
                        break
                    indices.append(i)
                else:
                    rows[o, dx//18, dy//18] = indices
        self.keys = tuple(sorted(rows))
        self.index = {k: i for i, k in enumerate(self.keys)}
        atom_domains = [0]*len(points)
        for row, key in enumerate(self.keys):
            flag = 1 << row
            for i in rows[key]:
                atom_domains[i] |= flag
        assert all(atom_domains), 'a cavity atom has no admissible tile'
        # Identical columns remain equivalent under any row deletion.
        self.domains = tuple(dict.fromkeys(atom_domains))
        self.row_columns = [0]*len(rows)
        self.conflicts = [0]*len(rows)
        for column, domain in enumerate(self.domains):
            for row in bits(domain):
                self.row_columns[row] |= 1 << column
                self.conflicts[row] |= domain
        self.initial_columns = (1 << len(self.domains))-1
        self.initial_rows = (1 << len(rows))-1


def mine(g, samples, limit=12):
    """Promote recurring disjoint unions of two retained, touching children."""
    bank = {}
    contexts = []
    for source, patch in samples:
        neighbors = {k: set() for k in patch}
        for i, a in enumerate(patch):
            for b in patch[i+1:]:
                if g.touches(a, b):
                    neighbors[a].add(b)
                    neighbors[b].add(a)
        contexts.append((source, [frozenset((k,)) for k in patch], neighbors))

    for depth in range(1, 4):
        support = defaultdict(set)
        children = {}
        next_contexts = []
        for source, parts, neighbors in contexts:
            instances = {}
            frontier = [(a, set().union(*(neighbors[k] for k in a))-a) for a in parts]
            for i, (a, near) in enumerate(frontier):
                for b in parts[i+1:]:
                    if not a.isdisjoint(b) or b.isdisjoint(near):
                        continue
                    union = a | b
                    if union in instances:
                        continue
                    frame = min((tuple(sorted(move(inverse(k), tile) for tile in union)), k) for k in union)
                    key, anchor = frame
                    support[key].add(source)
                    if key not in children:
                        inv = inverse(anchor)
                        children[key] = tuple(sorted(tuple(sorted(move(inv, tile) for tile in part))
                                                     for part in (a, b)))
                    instances[union] = key
            next_contexts.append((source, instances, neighbors))
        tops = sorted((k for k, sources in support.items() if len(sources) >= 2),
                      key=lambda k: (-len(support[k]), k))[:limit]
        for key in tops:
            bank[key] = dict(id=len(bank)+1, depth=depth, sources=len(support[key]),
                             children=children[key], keys=key)
        selected = set(tops)
        contexts = [(source, [instance for instance, pattern in instances.items() if pattern in selected], neighbors)
                    for source, instances, neighbors in next_contexts]
    return list(bank.values())


class Offers:
    def __init__(self, bank, max_depth=3):
        plans = defaultdict(set)
        self.templates = {}
        for item in bank:
            if item['depth'] > max_depth:
                continue
            index = item['id']
            self.templates[index] = item
            for anchor in item['keys']:
                relatives = [move(inverse(anchor), k) for k in item['keys'] if k != anchor]
                for o in range(12):
                    offsets = tuple(sorted(move((o, 0, 0), k) for k in relatives))
                    plans[o].add((index, offsets))
        self.plans = {o: sorted(p) for o, p in plans.items()}

    def match(self, cavity, row, counts):
        o, x, y = cavity.keys[row]
        matches = {}
        for index, relative in self.plans.get(o, ()):
            counts['templateChecks'] += 1
            members = [row]
            for j, a, b in relative:
                candidate = cavity.index.get((j, x+a, y+b))
                if candidate is None:
                    break
                members.append(candidate)
            else:
                row_mask, columns, conflicts = 0, 0, 0
                for member in members:
                    assert not (columns & cavity.row_columns[member])
                    columns |= cavity.row_columns[member]
                    conflicts |= cavity.conflicts[member]
                    row_mask |= 1 << member
                matches[row_mask] = (index, tuple(sorted(members)), row_mask, columns, conflicts)
        return tuple(matches.values())


class Policy:
    def __init__(self):
        self.weights = Counter()

    def features(self, option, degree, remaining, active, columns):
        template, rows, _, covered, conflicts = option
        scale = len(rows)/8
        return (('size', scale), ('macro', float(bool(template))), (f'option{template}', 1.0),
                ('size_at_forced', scale*(degree == 1)), ('size_early', scale*remaining),
                ('size_at_branch', scale*(degree > 1)),
                ('column_share', popcount(covered)/columns), ('row_share', popcount(conflicts & active)/popcount(active)))

    def rank(self, options, degree, remaining, active, columns, rng, train, counter):
        if len(options) <= 1:
            return options, None
        counter['scores'] += len(options)
        features = [self.features(option, degree, remaining, active, popcount(columns)) for option in options]
        scores = [sum(self.weights[n]*v for n, v in f) for f in features]
        if not train:
            return [options[i] for i in sorted(range(len(options)), key=lambda i: (-scores[i], i))], None
        top = max(scores)
        probs = [exp(x-top) for x in scores]
        total = sum(probs)
        chosen = rng.choices(range(len(options)), weights=probs, k=1)[0]
        gradient = Counter()
        for p, pairs in zip(probs, features):
            for name, value in pairs:
                gradient[name] -= p/total*value
        for name, value in features[chosen]:
            gradient[name] += value
        return [options[chosen], *options[:chosen], *options[chosen+1:]], gradient

    def update(self, gradients, reward):
        normalizer = max(1, len(gradients)) ** 0.5
        for gradient in gradients:
            for name, value in gradient.items():
                self.weights[name] = max(-8.0, min(8.0, self.weights[name]+0.18*reward*value/normalizer))


def solve(cavity, mode, *, offers=None, policy=None, train=False, seed=0, budget=3500):
    started = perf_counter()
    rng = Random(seed)
    counts = Counter()
    gradients = []
    matched = {}
    path = []
    best = []
    solution = None
    pairs = [(0, (row,), 1 << row, cavity.row_columns[row], cavity.conflicts[row])
             for row in range(len(cavity.keys))]

    def visit(columns, active, placed):
        nonlocal solution, best
        if counts['states'] >= budget:
            return
        counts['states'] += 1
        if not columns:
            solution = list(path)
            return
        branch = 0
        degree = float('inf')
        # All cavity atoms are fixed generation-zero obligations.
        for col in bits(columns):
            domain = cavity.domains[col] & active
            counts['domainChecks'] += 1
            if not domain:
                counts['dead'] += 1
                return
            if degree != 1:
                width = popcount(domain)
                if width < degree:
                    branch, degree = domain, width
        if placed > len(best):
            best = [row for _, members in path for row in members]
        options = [pairs[row] for row in bits(branch)]
        if offers:
            seen = set()
            for row in bits(branch):
                if row not in matched:
                    matched[row] = offers.match(cavity, row, counts)
                for proposal in matched[row]:
                    mask = proposal[2]
                    if mask not in seen and mask & active == mask:
                        seen.add(mask)
                        options.append(proposal)
        if mode == 'random':
            rng.shuffle(options)
        elif mode == 'largest':
            options.sort(key=lambda option: -len(option[1]))
        elif mode == 'rl':
            options, gradient = policy.rank(options, degree, 1-placed/cavity.tile_count,
                                            active, columns, rng, train, counts)
            if gradient:
                gradients.append(gradient)
        for template, rows, _, covered, conflicts in options:
            if counts['states'] >= budget:
                break
            assert covered & columns == covered
            path.append((template, rows))
            counts['attempts'] += 1
            counts['macroAttempts'] += bool(template)
            visit(columns ^ covered, active & ~conflicts, placed + len(rows))
            path.pop()
            if solution is not None:
                return

    visit(cavity.initial_columns, cavity.initial_rows, 0)
    seconds = perf_counter()-started
    if solution is not None:
        counts['firstPathMoves'] = len(solution)
    choices = [(template, [cavity.keys[row] for row in rows]) for template, rows in (solution or [])]
    patch = [key for _, members in choices for key in members]
    reward_work = counts['domainChecks'] + 4*counts['attempts'] + len(cavity.domains)
    result = dict(solved=solution is not None, stats=dict(counts), work=reward_work,
                  seconds=seconds, choices=choices, patch=patch, bestTiles=len(best))
    return result, gradients


def reward(result, baseline):
    """Combine completed coverage, candidate-incidence work and measured runtime."""
    if not result['solved']:
        return -3 + result['bestTiles']/max(1, len(baseline['patch']))
    relative_work = result['work']/baseline['work']
    relative_time = (result['seconds']+.0001)/(baseline['seconds']+.0001)
    return max(-2, min(2, -.68*log(relative_work)-.32*log(relative_time)))
