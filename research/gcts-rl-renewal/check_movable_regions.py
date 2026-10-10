"""Separate explicit region/domain, exhaustion and point-certificate verifier.

This imports the independent quantified inventory and syntax checker; it never
imports the producer's region model, reference factors or scheduler.
"""
import collections
import itertools
import hashlib

import check_quantified_receptors as A


freeze, need = A.freeze, A.need
END, PAD = -1, -2


def cell(j):
    return (2*j, 0)


def flow(j):
    return (2*j, -2)


def port(j, a):
    return [((2*j, 2+k), v) for k, v in enumerate(A.word(a))]+[((2*j, 1), 0)]


def initial(spec):
    d = freeze(spec)
    c = A.parser(d['theory'])
    bad = set().union(*(c.free(a) for a in d['hypotheses']))
    marks = dict((p, v) for j, a in enumerate(d['hypotheses'], -len(d['hypotheses']))
                 for p, v in port(j, a))
    marks.update(((-1000, j), int(x in bad)) for j, x in enumerate(d['variables']))
    marks.update({flow(0): 1, flow(d['bound']+1): 0})
    return marks


def tile(rules, spec, key, marking=()):
    d, key, marking = freeze(spec), freeze(key), freeze(marking)
    j, rid, refs = key
    need(type(j) is int and 0 <= j <= d['bound'], 'placement region')
    marks = {}

    def assign(p, v):
        need(p not in marks or marks[p] == v, 'single-valued placement')
        marks[p] = v

    if rid >= 0:
        need(type(rid) is int and rid < len(rules) and j < d['bound'], 'inference rule')
        r = rules[rid]
        need(len(refs) == len(r['inputs']) and all(type(i) is int and -len(d['hypotheses']) <= i < j for i in refs), 'reference bounds')
        for i, a in [(j, r['output'])]+list(zip(refs, r['inputs'])):
            for p, v in port(i, a):
                assign(p, v)
        for x in r['guards']:
            assign((-1000, d['variables'].index(x)), 0)
        assign(flow(j), 1)
        assign(flow(j+1), 1)
    elif rid == END:
        need(not refs and (j > 0 or d['hypotheses']), 'end input')
        for p, v in port(j-1, d['target']):
            assign(p, v)
        assign(flow(j), 1)
        assign(flow(j+1), 0)
    elif rid == PAD:
        need(not refs, 'padding references')
        assign(flow(j), 0)
        assign(flow(j+1), 0)
    else:
        raise ValueError('structural rule')
    for n, pair in enumerate(marking):
        for candidate, value in zip(pair, (0, 1)):
            if candidate == key:
                assign((-2000, n), value)
    return dict(key=key, occupancy=((cell(j), 12),), marks=tuple(sorted(marks.items())))


def state(rules, spec, chosen, marking=()):
    d = freeze(spec)
    chosen = freeze(chosen)
    marks = initial(d)
    filled = set()
    ports = {j: a for j, a in enumerate(d['hypotheses'], -len(d['hypotheses']))}
    for key in chosen:
        j, rid, refs = key
        need(j not in filled, 'capacity and multiplicity')
        t = tile(rules, d, key, marking)
        for p, v in t['marks']:
            need(p not in marks or marks[p] == v, 'global marking agreement')
            marks[p] = v
        if rid >= 0:
            r = rules[rid]
            ports.update([(j, r['output'])]+list(zip(refs, r['inputs'])))
        elif rid == END:
            ports[j-1] = d['target']
        filled.add(j)
    return filled, ports, marks


def domains(rules, spec, chosen=(), marking=()):
    """Explicit rule/reference products, independent of integer masks/counts."""
    d = freeze(spec)
    filled, known, marks = state(rules, d, chosen, marking)
    h = len(d['hypotheses'])
    ds = {}
    bad = {x for j, x in enumerate(d['variables']) if marks.get((-1000, j)) != 0}
    extra = collections.defaultdict(dict)
    for n, (a, b) in enumerate(freeze(marking)):
        extra[a][(-2000, n)] = 0
        extra[b][(-2000, n)] = 1

    def compatible(j, a, b):
        return ((flow(j) not in marks or marks[flow(j)] == a)
                and (flow(j+1) not in marks or marks[flow(j+1)] == b))

    def learned_legal(key):
        return all(p not in marks or marks[p] == v for p, v in extra.get(key, {}).items())

    for j in range(d['bound']+1):
        if j in filled:
            continue
        keys = []
        if compatible(j, 0, 0):
            keys.append((j, PAD, ()))
        if ((j > 0 or h) and compatible(j, 1, 0)
                and (j-1 not in known or known[j-1] == d['target'])):
            keys.append((j, END, ()))
        if j < d['bound'] and compatible(j, 1, 1):
            for rid, r in enumerate(rules):
                if bad.intersection(r['guards']) or (j in known and known[j] != r['output']):
                    continue
                choices = ([i for i in range(-h, j) if i not in known or known[i] == a]
                           for a in r['inputs'])
                for refs in itertools.product(*choices):
                    if any(refs[a] == refs[b] and r['inputs'][a] != r['inputs'][b]
                           for a in range(len(refs)) for b in range(a)):
                        continue
                    keys.append((j, rid, refs))
        ds[cell(j)] = [k for k in keys if learned_legal(k)]
    return ds


def decide(ds, generations=None):
    generations = generations or {}
    dead = sorted(p for p, keys in ds.items() if not keys)
    forced = sorted(p for p, keys in ds.items() if len(keys) == 1)
    if dead:
        return 'dead', dead[0], ()
    if forced:
        return 'forced', forced[0], ds[forced[0]]
    if not ds:
        return 'empty', None, ()
    p = min(ds, key=lambda p: (generations.get(p, 0), len(ds[p]), p))
    return 'branch', p, ds[p]


def tree(rules, spec, result=None, marking=(), seeds=(), node=None):
    totals = collections.Counter()
    leaf = None
    d = freeze(spec)
    seeds = freeze(seeds)
    if result is not None:
        node = result['search_tree']
        seeds = freeze(result['seeds'])
        if node is None:
            need(result['status'] == 'unknown_search_budget', 'nonterminal tree scope')
            return dict(status='unknown')

    def visit(t, chosen):
        nonlocal leaf
        ds = domains(rules, d, chosen, marking)
        kind, p, keys = decide(ds)
        totals['nodes'] += 1
        totals['peak_candidates'] = max(totals['peak_candidates'], sum(map(len, ds.values())))
        need((t['kind'], freeze(t['point'])) == (kind, p), 'global complete scheduler')
        if kind == 'dead':
            totals['dead'] += 1
            return False
        if kind == 'empty':
            leaf = chosen
            return True
        totals[kind] += 1
        ok = False
        seen = set()
        for child in t['children']:
            key = freeze(child['key'])
            need(not ok and key in keys and key not in seen, 'unique incident alternative')
            seen.add(key)
            totals['attempts'] += 1
            ok = visit(child['tree'], chosen+(key,))
            if not ok:
                totals['backtracks'] += 1
        need(ok or len(seen) == len(keys), 'every alternative before exhaustion')
        return ok

    ok = visit(node, seeds)
    if result is not None:
        need(ok == (result['status'] == 'finite_exact_proof_region'), 'terminal status')
        need(not ok or leaf == freeze(result['placements']), 'actual positive leaf')
        for k, v in totals.items():
            need(result['metrics'].get(k, 0) == v, 'tree metric '+k)
        h = len(d['hypotheses'])
        universe = sum(sum(1 for refs in itertools.product(range(-h, j), repeat=len(r['inputs']))
                           if all(refs[a] != refs[b] or r['inputs'][a] == r['inputs'][b]
                                  for a in range(len(refs)) for b in range(a)))
                       for j in range(d['bound']) for r in rules)
        universe += d['bound']+1+d['bound']+int(bool(h))
        need(result['candidate_universe'] == universe, 'universe cardinality')
    return dict(status='accepted_complete_tree', outcome=ok, nodes=totals['nodes'])


def certificate(rules, spec, result, tiles, marking=()):
    d = freeze(spec)
    keys, actual = freeze(result['placements']), freeze(tiles)
    need(len(keys) == d['bound']+1 and {k[0] for k in keys} == set(range(d['bound']+1)), 'all required capacity points')
    need(actual == tuple(tile(rules, d, k, marking) for k in keys), 'complete actual tile data')
    filled, ports, marks = state(rules, d, keys, marking)
    endpoints = [k[0] for k in keys if k[1] == END]
    need(len(endpoints) == 1, 'one end')
    n = endpoints[0]
    need(result['endpoint'] == n, 'decoded endpoint')
    for key in keys:
        j, rid, refs = key
        need((j < n and rid >= 0) or (j == n and rid == END)
             or (j > n and rid == PAD), 'flow-defined prefix/end/suffix')
    rows = {j: dict(kind=rules[rid]['kind'], formula=rules[rid]['output'],
                    refs=refs, parameters=rules[rid]['parameters'])
            for j, rid, refs in keys if rid >= 0}
    proof = [rows[j] for j in range(n)]
    need(freeze(result['proof']) == freeze(proof), 'displayed proof')
    if proof:
        logical = A.proof(proof, d['target'], d['hypotheses'], d['theory'])
    else:
        need(d['hypotheses'] and d['hypotheses'][-1] == d['target'], 'supplied target for zero-line proof')
        logical = dict(status='accepted', primitive_lines=0, commands=0)
    need(all(marks[flow(j)] == int(j <= n) for j in range(d['bound']+2)), 'entire flow word')
    need(all(g == 1 for g in result['tile_generations']), 'root-based successor generations')
    return dict(logical, endpoint=n, padding=d['bound']-n,
                occupied_points=len(filled), marking_points=len(marks))


def cluster(rules, spec, result, marking=()):
    n, d = result['endpoint'], freeze(spec)
    keys = [(n, END, ())]+[(j, PAD, ()) for j in range(n+1, d['bound']+1)]
    totals = collections.Counter()
    marks = {}
    for key in keys:
        t = tile(rules, d, key, marking)
        for p, v in t['occupancy']:
            totals[p] += v
        for p, v in t['marks']:
            need(p not in marks or marks[p] == v, 'cluster compatible union')
            marks[p] = v
    expected = dict(name='end-and-padding', endpoint=n, keys=keys,
                    occupancy=tuple(sorted(totals.items())), marks=tuple(sorted(marks.items())),
                    execution='inspectable aggregate only; base placements remain the searched inventory')
    need(freeze(result['closing_cluster']) == freeze(expected), 'exact aggregate expansion')
    need(all(v == 12 for v in totals.values()), 'capacity-preserving closure aggregate')
    return dict(cells=len(keys), status='accepted')


def context_hash(catalog, spec):
    d = freeze(spec)
    data = dict(catalog=freeze(catalog), target=d['target'], bound=d['bound'],
                hypotheses=d['hypotheses'], initial=sorted(initial(d).items()),
                transformations='identity', capacity=12)
    return hashlib.sha256(A.packed(data)).hexdigest()


def frames(rules, spec, result, marking=()):
    d = freeze(spec)
    chosen = []
    need(len(result['frames']) == len(result['placements']), 'whole actual factor path')
    for f, key in zip(freeze(result['frames']), freeze(result['placements'])):
        expected = domains(rules, d, chosen, marking)
        kind, p, keys = decide(expected)
        need((f['kind'], f['point'], f['key']) == (kind, p, key) and key in keys, 'path scheduler')
        need([a['point'] for a in f['domains']] == sorted(expected), 'all frontier factors')
        for a in f['domains']:
            j = a['point'][0]//2
            raw = list(a['structural'])
            for rid, masks, distinct in a['blocks']:
                need(0 <= rid < len(rules) and len(masks) == len(rules[rid]['inputs']), 'factor arity')
                need(distinct == (len(masks) == 2 and rules[rid]['inputs'][0] != rules[rid]['inputs'][1]), 'factor diagonal')
                need(all(type(v) is int and 0 <= v < 1 << (j+len(d['hypotheses'])) for v in masks), 'finite mask')
                choices = [[k for k in range(j+len(d['hypotheses'])) if mask & (1 << k)] for mask in masks]
                raw.extend((j, rid, tuple(k-len(d['hypotheses']) for k in refs))
                           for refs in itertools.product(*choices) if not distinct or refs[0] != refs[1])
            need(set(a['excluded']).issubset(raw), 'excluded actual instances')
            actual = [k for k in raw if k not in a['excluded']]
            need(actual == expected[a['point']] and len(actual) == a['count'], 'complete factor expansion')
        chosen.append(key)
    return dict(status='accepted_actual_factors', count=len(chosen))
