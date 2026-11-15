"""Run branch-order advice beside the exact, unchanged GCTS baseline."""

import argparse
import hashlib
import json
import multiprocessing as mp
from collections import Counter
from multiprocessing.connection import wait
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from experiment import Distinct, groups, load
from geometry import Geometry
from solver import Cavity, Policy, solve, verify


def worker(connection, peer, cavities, policy):
    peer.close()
    try:
        while True:
            index, budget, report_choice = connection.recv()
            def on_choice():
                connection.send(('choice', None))
            result, _ = solve(cavities[index], 'rl' if policy else 'lex',
                              policy=policy, budget=budget,
                              on_first_choice=on_choice if report_choice else None)
            connection.send(('result', result))
    except (EOFError, BrokenPipeError):
        return
    finally:
        connection.close()


class SearchWorkers:
    """Both workers inherit the read-only incidence matrices on POSIX."""

    def __init__(self, cavities, policy):
        context = mp.get_context('fork')
        self.lanes = {}
        for name, advisor in (('base', None), ('advised', policy)):
            parent, child = context.Pipe()
            process = context.Process(target=worker, args=(child, parent, cavities, advisor))
            try:
                process.start()
            except (OSError, RuntimeError):
                child.close()
                parent.close()
                if name == 'base':
                    raise
                continue
            child.close()
            self.lanes[name] = parent, process

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        # A caller may finish with an optional search still in flight.
        for connection, process in self.lanes.values():
            connection.close()
            if process.is_alive():
                process.terminate()
            process.join()

    def start(self, pending, lane, index, budget, *, report_choice=False):
        if lane not in self.lanes:
            return
        connection, _ = self.lanes[lane]
        try:
            connection.send((index, budget, report_choice))
        except (BrokenPipeError, EOFError, OSError):
            if lane == 'base':
                raise
            return
        pending[connection] = lane

    @staticmethod
    def receive(pending):
        connection = wait(tuple(pending))[0]
        lane = pending[connection]
        try:
            event, result = connection.recv()
        except (BrokenPipeError, EOFError, OSError):
            if lane == 'base':
                raise
            event, result = 'result', None
        if event == 'result':
            del pending[connection]
        return lane, event, result

    def first_verified(self, g, index, atoms, collar, budgets):
        started = perf_counter()
        pending = {}
        self.start(pending, 'base', index, budgets['base'], report_choice='advised' in budgets)
        results = {}
        while pending:
            lane, event, result = self.receive(pending)
            if event == 'choice':
                self.start(pending, 'advised', index, budgets['advised'])
                continue
            results[lane] = result
            if result is None or not result['solved']:
                continue
            try:
                verify(g, atoms, collar, result['patch'])
            except AssertionError:
                if lane == 'base':
                    raise
                continue
            return lane, result, perf_counter()-started, pending, results
        return None, None, perf_counter()-started, pending, results


def compare(g, sets, policy, repeats):
    cavities, compile_times = [], []
    for _, _, atoms, _ in sets:
        started = perf_counter()
        cavities.append(Cavity(g, atoms))
        compile_times.append(perf_counter()-started)
    rows = []
    with SearchWorkers(cavities, policy) as workers:
        for index, (cid, seed, atoms, collar) in enumerate(sets):
            base_times, protected_times, outcomes = [], [], []
            base_stats = None
            for repeat in range(repeats):
                jobs = ('solo', 'protected') if (index+repeat) % 2 else ('protected', 'solo')
                for job in jobs:
                    budgets = dict(base=3500, advised=3500) if job == 'protected' else dict(base=3500)
                    lane, winner, elapsed, pending, received = workers.first_verified(
                        g, index, atoms, collar, budgets)
                    # Drain only for measurements and to reuse the workers.
                    # The winning verified fill has already been returned.
                    while pending:
                        key, event, result = workers.receive(pending)
                        assert event == 'result'
                        received[key] = result
                    baseline = received['base']
                    key_stats = (baseline['patch'], baseline['stats'])
                    if base_stats is None:
                        base_stats = key_stats
                    assert key_stats == base_stats
                    if job == 'solo':
                        assert lane == 'base'
                        base_times.append(elapsed)
                    else:
                        assert winner is not None
                        protected_times.append(elapsed)
                        outcomes.append(lane)
                        advisor = received.get('advised')
                        if advisor is not None and advisor['solved']:
                            verify(g, atoms, collar, advisor['patch'])
            rows.append(dict(id=cid, source=seed, tiles=cavities[index].tile_count,
                             baselineStates=base_stats[1]['states'], advisorStarted=advisor is not None,
                             advisorStates=advisor['stats']['states'] if advisor else None,
                             advisorSolved=bool(advisor and advisor['solved']),
                             winnerRepeats=dict(Counter(outcomes)), baseSeconds=median(base_times),
                             raceSeconds=median(protected_times), compileSeconds=compile_times[index]))
        # Exhaust the advisor's budget on a case that exercised it.
        attempted = [i for i, row in enumerate(rows) if row['advisorStarted']]
        if attempted:
            index = attempted[0]
            cid, _, atoms, collar = sets[index]
            lane, _, _, pending, received = workers.first_verified(
                g, index, atoms, collar, dict(base=3500, advised=1))
            while pending:
                key, event, result = workers.receive(pending)
                assert event == 'result'
                received[key] = result
            assert lane == 'base' and not received['advised']['solved'], cid
    return rows


def run(directory, recorded, shape, repeats):
    primary = json.loads((recorded/f'gcts-cavities-1114-{shape}-results.json').read_text())
    followup = json.loads((recorded/f'gcts-cavities-1114-{shape}-forced.json').read_text())
    frozen_data = (recorded/f'{shape}-policy.json').read_bytes()
    assert hashlib.sha256(frozen_data).hexdigest() == primary['policySha256']
    policy = Policy()
    policy.weights.update(json.loads(frozen_data)['weights']['primitive_rl'])
    old = {row['id'] for study in (primary, followup) for row in study['rows']}
    distinct = Distinct()
    train = list(load(directory, shape, 'train'))
    test = list(load(directory, shape, 'test'))
    assert {item[1] for item in train}.isdisjoint(item[1] for item in test)
    for _, _, atoms, _ in train + [t for t in test if t[0] in old]:
        distinct.add(atoms)
    pool = [case for case in test if case[0] not in old and distinct.add(case[2])]
    geometry = Geometry(shape)
    rng = Random(734234)
    cases = []
    for source in groups(pool).values():
        rng.shuffle(source)
        for lo, hi in ((10, 22), (23, 34), (35, 44)):
            cases.extend([c for c in source if lo <= len(c[2])//len(geometry.atoms[0]) <= hi][:1])
    rows = compare(geometry, cases, policy, repeats)
    return dict(shape=shape, rows=rows, repeats=repeats, sources=len(groups(cases)),
                policySha256=primary['policySha256'],
                faultCheck='one-state advisor budget' if any(row['advisorStarted'] for row in rows) else None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cavities', type=Path)
    parser.add_argument('recorded', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    outcomes = []
    for name in ('hat', 'turtle'):
        study = run(args.cavities, args.recorded, name, args.repeats)
        outcomes.append(study)
        args.output.write_text(json.dumps(outcomes, indent=2)+'\n')
        print(name, len(study['rows']), 'verified cavities', flush=True)
