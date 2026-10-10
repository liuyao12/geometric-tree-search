"""Bounded movable proof boundaries and certified instance-specific markings.

The finite region has at most B inference cells plus one end cell. Binary flow
values force a prefix of inferences, exactly one end tile and a padding suffix.
All are full-capacity unit placements. No stopping or scope test bypasses the
point graph. Learned exclusions are finite point values, never pair callbacks.
"""
import collections
import hashlib
import itertools
import time

import quantified_receptors as Q
from turtle import State, Placement, CAPACITY
from serialized_kernel import canonical

END, PAD = -1, -2


def flow(j):
    return (2*j, -2)


def learning_point(j):
    return (-2000, j)


def freeze(value):
    if isinstance(value, (tuple, list)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, dict):
        return {k: freeze(v) for k, v in value.items()}
    return value


class Domain:
    """An exact union of a reference factor and two structural placements."""
    def __init__(self, base, structural, excluded=()):
        self.base = base
        self.structural = tuple(structural)
        self.excluded = frozenset(k for k in excluded
                                  if k in base or k in self.structural)
        self.count = len(base) + len(self.structural) - len(self.excluded)

    def __len__(self):
        return self.count

    def __iter__(self):
        # Padding first explores a shorter active region before extending it.
        for k in itertools.chain(self.structural, self.base):
            if k not in self.excluded:
                yield k

    def __contains__(self, key):
        return key not in self.excluded and (key in self.base or key in self.structural)

    def __getitem__(self, index):
        if index != 0:
            raise IndexError("only singleton extraction")
        return next(iter(self))


class Model(Q.Model):
    END = -1
    PAD = -2

    def __init__(self, catalog, target, bound, hypotheses=(), marking=()):
        super().__init__(catalog, target, bound+1, hypotheses)
        self.bound = bound
        self.marking = tuple(freeze(pair) for pair in marking)
        self.extra = collections.defaultdict(dict)
        self.dependencies = collections.defaultdict(set)
        for n, (a, b) in enumerate(self.marking):
            if a == b:
                raise ValueError("distinct learned pair")
            for key, value in ((a, 0), (b, 1)):
                # The positional system uses identity transformations only.
                self.extra[key][learning_point(n)] = value
                self.dependencies[learning_point(n)].add(key)

    def initial(self):
        s = State()
        s.roots = {Q.cell(j): 0 for j in range(self.length)}
        s.generations = s.roots.copy()
        s.allowed_points = frozenset(s.roots)
        for j, a in enumerate(self.hypotheses, -len(self.hypotheses)):
            s.marks.update(Q.port(j, a))
        s.marks.update((Q.scope(j), int(x in self.forbidden))
                       for j, x in enumerate(self.variables))
        s.marks[flow(0)] = 1
        s.marks[flow(self.length)] = 0
        return s

    def placement(self, key):
        key = freeze(key)
        if key in self.cache:
            return self.cache[key]
        j, rid, refs = key
        if not 0 <= j < self.length:
            raise ValueError("finite region")
        if rid >= 0:
            if j >= self.bound:
                raise ValueError("last slot must end or pad")
            c = super().placement(key)
            marks = dict(c.marks)
            marks.update({flow(j): 1, flow(j+1): 1})
        elif rid == self.END:
            if refs or (j == 0 and not self.hypotheses):
                raise ValueError("end requires an earlier formula")
            marks = dict(Q.port(j-1, self.target))
            marks.update({flow(j): 1, flow(j+1): 0})
        elif rid == self.PAD:
            if refs:
                raise ValueError("padding has no references")
            marks = {flow(j): 0, flow(j+1): 0}
        else:
            raise ValueError("structural kind")
        if rid < 0:
            self.metrics['materialized_placements'] += 1
        marks.update(self.extra.get(key, {}))
        c = Placement(key, ((Q.cell(j), CAPACITY),), tuple(sorted(marks.items())), ())
        self.cache[key] = c
        return c

    def cardinality(self):
        h = len(self.hypotheses)
        proof = sum((j+h)**len(r['inputs'])
                    - ((j+h) if len(r['inputs']) == 2
                       and r['inputs'][0] != r['inputs'][1] else 0)
                    for j in range(self.bound) for r in self.catalog['rules'])
        return proof + self.length + self.bound + int(bool(h))

    def context_hash(self):
        data = dict(catalog=self.catalog, target=self.target, bound=self.bound,
                    hypotheses=self.hypotheses, initial=self.initial().marks,
                    transformations='identity', capacity=CAPACITY)
        # JSON keys must be strings; exact sorted point/value pairs are used.
        data['initial'] = sorted(data['initial'].items())
        return hashlib.sha256(canonical(data)).hexdigest()


class Graph:
    def __init__(self, m, s):
        self.m = m
        self.order = tuple(s.order)
        self.ports = {j: a for j, a in enumerate(m.hypotheses, -len(m.hypotheses))}
        self.flows = {j: s.marks[flow(j)] for j in range(m.length+1)
                      if flow(j) in s.marks}
        if self.flows.get(0) != 1 or self.flows.get(m.length) != 0:
            raise ValueError("explicit exterior flow values")
        self.scopes = {x: s.marks.get(Q.scope(j)) for j, x in enumerate(m.variables)}
        if any(self.scopes[x] != int(x in m.forbidden) for x in m.variables):
            raise ValueError("fixed ambient scope")
        self.learned = {p: v for p, v in s.marks.items() if p[0] == -2000}
        self.domains = {p: self.calculate(p) for p in s.frontier()}

    def copy(self):
        g = object.__new__(Graph)
        g.m = self.m
        for name in ('ports', 'flows', 'scopes', 'learned', 'domains'):
            setattr(g, name, getattr(self, name).copy())
        g.order = self.order
        return g

    def compatible_flow(self, j, a, b):
        return ((j not in self.flows or self.flows[j] == a)
                and (j+1 not in self.flows or self.flows[j+1] == b))

    def calculate(self, point):
        j = point[0]//2
        m = self.m
        h = len(m.hypotheses)
        known = collections.defaultdict(int)
        bound = 0
        for i, a in self.ports.items():
            if -h <= i < j:
                known[a] |= 1 << (i+h)
                bound |= 1 << (i+h)
        free = ((1 << (j+h))-1) & ~bound
        blocks = []
        if j < m.bound and self.compatible_flow(j, 1, 1):
            a = self.ports.get(j)
            for rid in m.by_output.get(a, ()) if a is not None else range(len(m.catalog['rules'])):
                r = m.catalog['rules'][rid]
                if any(self.scopes[x] != 0 for x in r['guards']):
                    continue
                masks = tuple(free | known[v] for v in r['inputs'])
                distinct = len(masks) == 2 and r['inputs'][0] != r['inputs'][1]
                if all(masks) and (not distinct or Q.count(masks[0])*Q.count(masks[1]) > Q.count(masks[0]&masks[1])):
                    blocks.append((rid, masks, distinct))
        structural = []
        if self.compatible_flow(j, 0, 0):
            structural.append((j, m.PAD, ()))
        if ((j > 0 or h) and self.compatible_flow(j, 1, 0)
                and (j-1 not in self.ports or self.ports[j-1] == m.target)):
            structural.append((j, m.END, ()))
        excluded = set()
        # Evaluate sparse point assignments, not learned pair membership.
        for p, v in self.learned.items():
            for key in m.dependencies[p]:
                if key[0] == j and m.extra[key][p] != v:
                    excluded.add(key)
        m.metrics['domain_constructions'] += 1
        m.metrics['factor_records_constructed'] += len(blocks)
        m.metrics['learned_key_exclusions_tested'] += len(excluded)
        d = Domain(Q.Domain(j, h, blocks), structural, excluded)
        m.metrics['learned_candidate_domains_removed'] += len(d.excluded)
        return d

    def update(self, m, s, changed):
        if tuple(s.order[:-1]) != self.order:
            raise ValueError("one-placement transaction")
        key = s.order[-1]
        j, rid, refs = key
        if rid >= 0:
            r = m.catalog['rules'][rid]
            bindings = [(j, r['output'])] + list(zip(refs, r['inputs']))
        elif rid == m.END:
            bindings = [(j-1, m.target)]
        else:
            bindings = []
        new = []
        for i, a in bindings:
            if i in self.ports and self.ports[i] != a:
                raise ValueError("word conflict")
            if not all(s.marks.get(p) == v for p, v in Q.port(i, a)):
                raise ValueError("actual word assignment")
            if i not in self.ports:
                self.ports[i] = a
                new.append(i)
        touched = set()
        for p in changed:
            if p[1] == -2 and p[0] >= 0:
                i = p[0]//2
                self.flows[i] = s.marks[p]
                touched.update((i-1, i))
            if p[0] == -2000:
                self.learned[p] = s.marks[p]
                touched.update(k[0] for k in m.dependencies[p])
        if any(s.marks.get(Q.scope(m.vi[x])) != v for x, v in self.scopes.items()):
            raise ValueError("scope changed")
        self.order = tuple(s.order)
        frontier = s.frontier()
        for p in self.domains.keys()-frontier:
            del self.domains[p]
        for p in frontier:
            i = p[0]//2
            if i in touched or (new and i >= min(new)):
                self.domains[p] = self.calculate(p)

    def candidate_points(self, key):
        p = Q.cell(key[0])
        return {p} if p in self.domains and key in self.domains[p] else set()

    def decision(self, s):
        dead = sorted(p for p, d in self.domains.items() if not len(d))
        forced = sorted(p for p, d in self.domains.items() if len(d) == 1)
        if dead:
            return 'dead', dead[0], ()
        if forced:
            return 'forced', forced[0], self.domains[forced[0]]
        if not self.domains:
            return 'empty', None, ()
        p = min(self.domains, key=lambda p: (s.generations.get(p, s.roots.get(p, 0)), len(self.domains[p]), p))
        return 'branch', p, self.domains[p]

    def fingerprint(self):
        return (tuple(sorted(self.ports.items())), tuple(sorted(self.flows.items())),
                tuple(sorted(self.scopes.items())), tuple(sorted(self.learned.items())),
                self.order, tuple(sorted((p, d.base.blocks, d.structural,
                                         tuple(sorted(d.excluded)), len(d))
                                        for p, d in self.domains.items())))


def decode(m, keys):
    end = [k[0] for k in keys if k[1] == m.END]
    if len(end) != 1:
        raise ValueError("exactly one proof boundary")
    rows = {j: Q.row(m.catalog['rules'][rid], refs)
            for j, rid, refs in keys if rid >= 0}
    if set(rows) != set(range(end[0])):
        raise ValueError("contiguous proof prefix")
    return [rows[j] for j in range(end[0])], end[0]


def search(m, node_limit=30000, seconds=15, seeds=(), collect_pairs=False):
    start = time.perf_counter()
    s = m.initial()
    g = Graph(m, s)
    for key in freeze(seeds):
        c = m.placement(key)
        if not s.legal(c):
            raise ValueError("fixed test pair must be compatible")
        g.update(m, s, s.place(c))
    metrics = collections.Counter()
    found = None
    best = s
    negatives = []

    def visit(s, g):
        nonlocal found, best
        metrics['nodes'] += 1
        if metrics['nodes'] > node_limit or time.perf_counter()-start > seconds:
            raise Q.Limit()
        kind, p, keys = g.decision(s)
        metrics['peak_candidates'] = max(metrics['peak_candidates'], sum(len(d) for d in g.domains.values()))
        if len(s.order) > len(best.order):
            best = s
        if kind == 'dead':
            metrics['dead'] += 1
            return False, dict(kind=kind, point=p)
        if kind == 'empty':
            found = s
            return True, dict(kind=kind, point=p)
        metrics[kind] += 1
        t = dict(kind=kind, point=p, children=[])
        for key in keys:
            metrics['attempts'] += 1
            ss, gg = s.copy(), g.copy()
            gg.update(m, ss, ss.place(m.placement(key)))
            ok, child = visit(ss, gg)
            t['children'].append(dict(key=key, tree=child))
            if not ok and collect_pairs and len(ss.order) == 2:
                negatives.append(dict(pair=tuple(ss.order), tree=child))
            if ok:
                return True, t
            metrics['backtracks'] += 1
        return False, t

    tree = None
    try:
        ok, tree = visit(s, g)
        status = 'finite_exact_proof_region' if ok else 'exhausted_finite_region'
    except Q.Limit:
        status = 'unknown_search_budget'
    selected = found or best
    rows, endpoint = decode(m, selected.order) if found else (None, None)
    return dict(status=status, placements=selected.order, proof=rows, endpoint=endpoint,
                metrics=dict(metrics), graph_metrics=dict(m.metrics),
                seconds=time.perf_counter()-start, search_tree=tree,
                candidate_universe=m.cardinality(), tile_generations=selected.tile_generations,
                seeds=tuple(freeze(seeds)), negatives=negatives,
                limits=dict(nodes=node_limit, seconds=seconds))


def chronological(m, node_limit=30000, seconds=15):
    """Conventional forward DFS: stop at the target; no padding is searched."""
    start = time.perf_counter()
    metrics = collections.Counter()
    found = None
    h = len(m.hypotheses)

    def visit(keys, known, state):
        nonlocal found
        metrics['nodes'] += 1
        if metrics['nodes'] > node_limit or time.perf_counter()-start > seconds:
            raise Q.Limit()
        j = len(keys)
        if (j and known[j-1] == m.target) or (not j and h and m.hypotheses[-1] == m.target):
            complete = state.copy()
            for k in [(j, m.END, ())]+[(i, m.PAD, ()) for i in range(j+1, m.length)]:
                if not complete.legal(m.placement(k)):
                    return False
                complete.place(m.placement(k))
            found = keys
            return True
        if j == m.bound:
            return False
        for rid, r in enumerate(m.catalog['rules']):
            if any(x in m.forbidden for x in r['guards']):
                continue
            for refs in itertools.product(*([i for i, a in known.items() if a == v] for v in r['inputs'])):
                metrics['attempts'] += 1
                key = (j, rid, refs)
                c = m.placement(key)
                if not state.legal(c):
                    metrics['marking_rejections'] += 1
                    continue
                child = state.copy()
                child.place(c)
                if visit(keys+[key], known | {j: r['output']}, child):
                    return True
                metrics['backtracks'] += 1
        return False

    try:
        ok = visit([], {j: a for j, a in enumerate(m.hypotheses, -h)}, m.initial())
        status = 'found' if ok else 'exhausted_finite_region'
    except Q.Limit:
        status = 'unknown_search_budget'
    rows = [Q.row(m.catalog['rules'][rid], refs) for j, rid, refs in found] if found is not None else None
    return dict(status=status, proof=rows, metrics=dict(metrics),
                seconds=time.perf_counter()-start, endpoint=len(rows) if rows is not None else None)


def closing_cluster(m, endpoint):
    """Aggregate a witnessed end/padding suffix without executing a macro."""
    keys = [(endpoint, m.END, ())]+[(j, m.PAD, ()) for j in range(endpoint+1, m.length)]
    values, marks = collections.Counter(), {}
    for key in keys:
        c = m.placement(key)
        for p, v in c.occupancy:
            values[p] += v
            if values[p] > CAPACITY:
                raise ValueError("cluster internal capacity")
        for p, v in c.marks:
            if p in marks and marks[p] != v:
                raise ValueError("cluster internal marking")
            marks[p] = v
    return dict(name='end-and-padding', endpoint=endpoint, keys=keys,
                occupancy=tuple(sorted(values.items())), marks=tuple(sorted(marks.items())),
                execution='inspectable aggregate only; base placements remain the searched inventory')


def compile_region(proof, target, hypotheses, theory, deduce=False):
    if proof:
        return Q.compile_request(proof, target, hypotheses, theory, deduce)
    if not hypotheses or hypotheses[-1] != target:
        raise ValueError("empty derivation requires the last supplied hypothesis")
    # Copy the already supplied fact into the kernel's final-line position.
    # This is a deterministic certificate adapter, not a search derivation.
    lines, _ = Q.commands([], hypotheses)
    lines.append(dict(rule='tautology', formula=Q.L.Imp(target, target)))
    lines.append(dict(rule='mp', formula=target, antecedent=len(hypotheses)-1,
                      implication=len(hypotheses)))
    actual = target
    theory = dict(theory, axioms=dict(theory['axioms']))
    if deduce:
        lines = Q.discharge(lines, hypotheses)
        for h in reversed(hypotheses):
            actual = Q.L.Imp(h, actual)
    elif any(Q.L.free(a) for a in hypotheses):
        probe = Q.L.Imp(('bot',), ('bot',))
        request = dict(protocol=Q.PROTOCOL, theory=theory, target=probe,
                       blocks=[dict(name='discovered-sequent', premises=hypotheses,
                                    conclusion=target, proof=lines)],
                       proof=[dict(rule='tautology', formula=probe)])
        result = Q.check(canonical(request), max_work=None)
        if result['status'] != 'accepted':
            raise ValueError(result)
        return dict(request=request, host=result, scope='zero inference rows; checked sequent, root identity probe')
    else:
        for j, a in enumerate(hypotheses):
            name = 'premise-'+str(j)
            if name in theory['axioms']:
                raise ValueError("reserved premise name")
            theory['axioms'][name] = a
            lines[j] = dict(rule='axiom', formula=a, name=name)
    request = dict(protocol=Q.PROTOCOL, theory=theory, target=actual, blocks=[], proof=lines)
    result = Q.check(canonical(request), max_work=None,
                     expected_problem_sha256=Q.problem_hash(request))
    if result['status'] != 'accepted':
        raise ValueError(result)
    return dict(request=request, host=result,
                scope='fully discharged theorem' if deduce else 'zero inference rows; supplied fact copied')
