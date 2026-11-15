"""Train on geometry-only cavities, freeze, and benchmark separate source runs."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from geometry import Geometry, GROUP, norm, normalize, transform
from solver import Cavity, Offers, Policy, mine, reward, solve, verify


LANES = ('gcts', 'primitive_rl', 'pairs_rl', 'hierarchy_random', 'hierarchy_largest', 'hierarchy_rl')
TRAINED = ('primitive_rl', 'pairs_rl', 'hierarchy_rl')
SETTINGS = {
    'gcts': ('lex', None), 'primitive_rl': ('rl', None), 'pairs_rl': ('rl', 1),
    'hierarchy_random': ('random', 3), 'hierarchy_largest': ('largest', 3), 'hierarchy_rl': ('rl', 3),
}


def load(directory, shape, split):
    for path in sorted(directory.glob(f'{shape}-*.json')):
        item = json.loads(path.read_text())
        if item['split'] == split:
            for case in item['cases']:
                yield (case['id'], case['source'], tuple(map(tuple, case['atoms'])),
                       tuple(map(tuple, case['boundary'])))


class Distinct:
    """Reject symmetry-equivalent cavities by exact comparison on moment collisions."""
    def __init__(self):
        self.index = defaultdict(list)

    @staticmethod
    def canonical(points):
        def relative(o):
            world = sorted(transform(o, x, y) for x, y in points)
            u, v = world[0]
            return tuple((x-u, y-v) for x, y in world)
        return min(relative(o) for o in range(len(GROUP)))

    def add(self, points):
        # Translation- and symmetry-invariant sum of squared pair distances.
        count = len(points)
        invariant = (count, count*sum(norm(x, y) for x, y in points) -
                     norm(sum(x for x, _ in points), sum(y for _, y in points)))
        collisions = self.index[invariant]
        if collisions:
            canonical = self.canonical(points)
            for old in collisions:
                if canonical == self.canonical(old):
                    return False
        collisions.append(points)
        return True


def groups(items):
    result = defaultdict(list)
    for item in items:
        result[item[1]].append(item)
    return result


def subset(items, cap, seed):
    rng = Random(seed)
    result = []
    for source_items in groups(items).values():
        # Sample across prespecified size tiers for each independent source.
        rng.shuffle(source_items)
        tiers = defaultdict(list)
        for item in source_items:
            tiers[int(item[0].rsplit('-', 1)[1]) % 4].append(item)
        result.extend(sorted((values[0] for values in tiers.values()), key=lambda t: t[0])[:cap])
    return result


def bootstrap_ratio(rows, lane, metric):
    by_seed = defaultdict(list)
    for row in rows:
        by_seed[row['source']].append(row)
    rng = Random(667)
    clusters = list(by_seed.values())
    ratios = []
    for _ in range(1000):
        sample = [row for cluster in rng.choices(clusters, k=len(clusters)) for row in cluster]
        a = sum(row['lanes'][lane][metric] for row in sample)
        b = sum(row['lanes']['gcts'][metric] for row in sample)
        ratios.append(a/b)
    return sorted(ratios)[25], sorted(ratios)[974]


def summarize(rows):
    totals = {}
    for lane in LANES:
        samples = [row['lanes'][lane] for row in rows]
        totals[lane] = dict(
            solved=sum(s['solved'] for s in samples),
            states=sum(s['stats']['states'] for s in samples),
            dead=sum(s['stats'].get('dead', 0) for s in samples),
            domainChecks=sum(s['stats'].get('domainChecks', 0) for s in samples),
            seconds=sum(s['seconds'] for s in samples),
            endToEnd=sum(s['endToEnd'] for s in samples),
            searchRatio95=bootstrap_ratio(rows, lane, 'seconds'),
            endToEndRatio95=bootstrap_ratio(rows, lane, 'endToEnd'),
            winningMacros=dict(Counter(len(ks) for s in samples for index, ks in s['choices'] if index)),
        )
    return totals


def experiment(directory, shape, output, repeats):
    started = perf_counter()
    g = Geometry(shape)
    distinct = Distinct()
    samples, episode_cavities = [], []
    duplicate_train = 0
    train_cases = list(load(directory, shape, 'train'))
    train_started = perf_counter()
    for cid, source, atoms, boundary in train_cases:
        if not distinct.add(atoms):
            duplicate_train += 1
            continue
        cavity = Cavity(g, atoms)
        base, _ = solve(cavity, 'lex')
        if base['solved']:
            verify(g, atoms, boundary, base['patch'])
            samples.append((source, base['patch']))
        episode_cavities.append((cid, source, atoms, boundary, cavity, base))
    bank = mine(g, samples)
    for item in bank:
        left, right = item['children']
        assert set(left).isdisjoint(right) and tuple(sorted((*left, *right))) == item['keys']
        if item['depth'] > 1:
            for child in item['children']:
                assert any(parent['depth'] == item['depth']-1 and parent['keys'] == normalize(child)
                           for parent in bank)
        g.verify(item['keys'])
    print(shape, len(episode_cavities), 'training cases. Bank sizes', Counter(i['depth'] for i in bank), flush=True)
    offer_banks = {depth: Offers(bank, depth) for depth in (1, 3)}
    policies = {lane: Policy() for lane in TRAINED}
    training = []
    rng = Random(42441)
    for epoch in range(2):
        rng.shuffle(episode_cavities)
        for cid, source, atoms, boundary, cavity, base in episode_cavities:
            for lane in TRAINED:
                _, depth = SETTINGS[lane]
                result, gradients = solve(cavity, 'rl', offers=offer_banks.get(depth),
                                          policy=policies[lane], train=True, seed=rng.randrange(2**32))
                if result['solved']:
                    verify(g, atoms, boundary, result['patch'])
                score = reward(result, base)
                policies[lane].update(gradients, score)
                training.append(dict(id=cid, source=source, epoch=epoch+1, lane=lane,
                                     reward=score, solved=result['solved'], stats=result['stats'],
                                     seconds=result['seconds'], updates=len(gradients)))
        print(shape, 'training epoch', epoch+1, flush=True)
    frozen = dict(bank=bank, weights={lane: policy.weights for lane, policy in policies.items()})
    frozen_bytes = json.dumps(frozen, sort_keys=True, separators=(',', ':')).encode()
    output.with_suffix('.policy.json').write_bytes(frozen_bytes)
    policy_hash = hashlib.sha256(frozen_bytes).hexdigest()
    train_seconds = perf_counter()-train_started

    # Extract held-out targets only after freezing. Recorded interiors are
    # omitted by load() and never passed to the learner or solver.
    test_cases = list(load(directory, shape, 'test'))
    assert {r[1] for r in train_cases}.isdisjoint(r[1] for r in test_cases)
    available = []
    duplicates_test = 0
    for case in test_cases:
        if distinct.add(case[2]):
            available.append(case)
        else:
            duplicates_test += 1
    selected = subset(available, 4, 1888)
    rows = []
    for cid, source, atoms, boundary in selected:
        compile_times, runs = [], defaultdict(list)
        for repeat in range(repeats):
            before = perf_counter()
            cavity = Cavity(g, atoms)
            compile_times.append(perf_counter()-before)
            order = list(LANES)
            rng.shuffle(order)
            for lane in order:
                mode, depth = SETTINGS[lane]
                result, _ = solve(cavity, mode, offers=offer_banks.get(depth), policy=policies.get(lane),
                                  seed=int(cid.replace('-', '')))
                runs[lane].append(result)
        lane_results = {}
        for lane, attempts in runs.items():
            result = attempts[0]
            assert all((a['patch'], a['stats']) == (result['patch'], result['stats']) for a in attempts)
            if result['solved']:
                verify(g, atoms, boundary, result['patch'])
            result['seconds'] = median(a['seconds'] for a in attempts)
            result['endToEnd'] = median(compile_times)+result['seconds']
            lane_results[lane] = result
        rows.append(dict(id=cid, source=source, tileCount=cavity.tile_count, boundary=boundary,
                         columns=len(cavity.domains), candidates=len(cavity.keys),
                         compileSeconds=median(compile_times), lanes=lane_results))
    assert json.dumps(frozen, sort_keys=True, separators=(',', ':')).encode() == frozen_bytes
    result = dict(shape=shape, trainingCases=len(episode_cavities), trainingLineages=len(groups(train_cases)),
                  trainingDuplicates=duplicate_train, bootstrapSolved=len(samples), training=training,
                  trainSeconds=train_seconds, heldoutLineages=len(groups(selected)),
                  availableTest=len(available), totalTest=len(test_cases), testDuplicates=duplicates_test,
                  rows=rows, summary=summarize(rows), policySha256=policy_hash,
                  repeats=repeats, seconds=perf_counter()-started)
    output.write_text(json.dumps(result, separators=(',', ':')))
    print(shape, json.dumps({k: v for k, v in result.items() if k not in ('rows','training')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('shape', choices=('hat', 'turtle'))
    parser.add_argument('output', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    options = parser.parse_args()
    experiment(options.directory, options.shape, options.output, options.repeats)
