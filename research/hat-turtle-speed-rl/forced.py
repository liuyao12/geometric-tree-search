"""Follow-up: commit learned clusters only as certified forced sequences."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from experiment import Distinct, bootstrap_ratio, groups, load
from geometry import Geometry
from solver import Cavity, Offers, Policy, bits, popcount, solve, verify


def guarded_search(cavity, offers, policy, budget=3500):
    started = perf_counter()
    stats = Counter()
    path, matched = [], {}
    solved = None

    def certify(rows, active):
        remaining = list(rows)
        forced_order = []
        while remaining:
            for i, row in enumerate(remaining):
                row_bit = 1 << row
                for column in bits(cavity.row_columns[row]):
                    stats['certificateChecks'] += 1
                    if cavity.domains[column] & active == row_bit:
                        break
                else:
                    continue
                forced_order.append(remaining.pop(i))
                active &= ~cavity.conflicts[row]
                break
            else:
                return None
        return forced_order

    def visit(columns, active, placed):
        nonlocal solved
        if stats['states'] >= budget:
            return
        stats['states'] += 1
        if not columns:
            solved = list(path)
            return
        branch, width = 0, float('inf')
        for column in bits(columns):
            domain = cavity.domains[column] & active
            stats['domainChecks'] += 1
            if not domain:
                stats['dead'] += 1
                return
            if width != 1:
                count = popcount(domain)
                if count < width:
                    branch, width = domain, count
        if width == 1:
            anchor = branch.bit_length()-1
            if anchor not in matched:
                matched[anchor] = offers.match(cavity, anchor, stats)
            valid = [p for p in matched[anchor] if p[2] & active == p[2]]
            if policy is None:
                valid.sort(key=lambda p: -len(p[1]))
            else:
                valid, _ = policy.rank(valid, width, 1-placed/cavity.tile_count,
                                       active, columns, None, False, stats)
            for template, rows, _, covered, conflicts in valid:
                forced = certify([r for r in rows if r != anchor], active & ~cavity.conflicts[anchor])
                if forced is None:
                    continue
                # The scheduled singleton and all certified members must
                # occur in every solution of this residual exact cover.
                path.append((template, (anchor, *forced)))
                stats['certifiedMacros'] += 1
                visit(columns ^ covered, active & ~conflicts, placed+len(rows))
                path.pop()
                return
        for row in bits(branch):
            if stats['states'] >= budget:
                break
            path.append((0, (row,)))
            visit(columns ^ cavity.row_columns[row], active & ~cavity.conflicts[row], placed+1)
            path.pop()
            if solved is not None:
                return

    visit(cavity.initial_columns, cavity.initial_rows, 0)
    moves = [(i, [cavity.keys[r] for r in rows]) for i, rows in (solved or [])]
    return dict(solved=solved is not None, seconds=perf_counter()-started, stats=dict(stats),
                choices=moves, patch=[tile for _, members in moves for tile in members])


def followup(directory, initial, output):
    source = json.loads(initial.read_text())
    shape = source['shape']
    g = Geometry(shape)
    frozen_bytes = initial.with_suffix('.policy.json').read_bytes()
    assert hashlib.sha256(frozen_bytes).hexdigest() == source['policySha256']
    frozen = json.loads(frozen_bytes)
    offers, policy = Offers(frozen['bank']), Policy()
    policy.weights.update(frozen['weights']['hierarchy_rl'])
    distinct = Distinct()
    for _, _, atoms, _ in load(directory, shape, 'train'):
        distinct.add(atoms)
    previously_measured = {row['id'] for row in source['rows']}
    cases = list(load(directory, shape, 'test'))
    for cid, _, atoms, _ in cases:
        if cid in previously_measured:
            distinct.add(atoms)
    pool = [case for case in cases if case[0] not in previously_measured and distinct.add(case[2])]
    rng = Random(583351)
    selected = []
    for candidates in groups(pool).values():
        rng.shuffle(candidates)
        for low, high in ((18, 30), (31, 44)):
            matches = [case for case in candidates if low <= len(case[2])//len(g.atoms[0]) <= high]
            selected.extend(matches[:1])
    rows = []
    modes = ('gcts', 'guarded_largest', 'guarded_rl')
    for cid, seed, atoms, boundary in selected:
        runs, compile_times = defaultdict(list), []
        for _ in range(3):
            started = perf_counter()
            cavity = Cavity(g, atoms)
            compile_times.append(perf_counter()-started)
            order = list(modes)
            rng.shuffle(order)
            for lane in order:
                if lane == 'gcts':
                    result, _ = solve(cavity, 'lex')
                else:
                    result = guarded_search(cavity, offers, policy if lane == 'guarded_rl' else None)
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
        rows.append(dict(id=cid, source=seed, tiles=cavity.tile_count, lanes=lane_results))
    summary = {}
    for lane in modes:
        outcomes = [row['lanes'][lane] for row in rows]
        summary[lane] = dict(
            solved=sum(r['solved'] for r in outcomes), states=sum(r['stats']['states'] for r in outcomes),
            seconds=sum(r['seconds'] for r in outcomes), endToEnd=sum(r['endToEnd'] for r in outcomes),
            searchRatio95=bootstrap_ratio(rows, lane, 'seconds'),
            endToEndRatio95=bootstrap_ratio(rows, lane, 'endToEnd'),
            certifiedMoves=dict(Counter(len(keys) for r in outcomes for i, keys in r['choices'] if i)))
    result = dict(shape=shape, rows=rows, summary=summary, lineages=len(groups(selected)),
                  reusedPolicySha256=source['policySha256'], posthoc=True)
    output.write_text(json.dumps(result, separators=(',', ':')))
    print(shape, len(rows), json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('initial', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    followup(args.directory, args.initial, args.output)
