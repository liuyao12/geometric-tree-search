"""Automatically derived, redundant distant proof-prefix capacity markings.

This is certified constraint synthesis over the declared finite rule grammar,
not an empirical classifier or an unrestricted first-order completeness claim.
"""
import collections
import hashlib
import time

import movable_proof_regions as M
import quantified_receptors as Q
from serialized_kernel import canonical
from turtle import Placement


def point(j):
    return (-3000, j)


def synthesis(model):
    """Greatest fixed point, checked by induction on actual proof prefixes."""
    began = time.perf_counter()
    rules = model.catalog['rules']
    formulas = set(model.hypotheses) | {model.target}
    for rule in rules:
        formulas.update(rule['inputs'])
        formulas.add(rule['output'])
    formulas = sorted(formulas, key=canonical)
    ids = {formula: i for i, formula in enumerate(formulas)}
    given = {ids[a] for a in model.hypotheses}
    eligible = [i for i, rule in enumerate(rules)
                if not model.forbidden.intersection(rule['guards'])]
    arms = collections.defaultdict(list)
    for i in eligible:
        rule = rules[i]
        arms[ids[rule['output']]].append([ids[a] for a in rule['inputs']])
    universe = set(range(len(formulas))) - given
    current = [set() if i in given else universe.copy() for i in range(len(formulas))]
    rounds = [[sorted(row) for row in current]]
    while True:
        after = []
        for i in range(len(formulas)):
            if i in given:
                after.append(set())
                continue
            alternatives = [set().union(*(current[j] for j in inputs))
                            for inputs in arms[i]]
            common = set.intersection(*alternatives) if alternatives else universe
            after.append({i} | common)
        if after == current:
            break
        if any(not b <= a for a, b in zip(current, after)):
            raise ValueError('descending greatest fixed point')
        current = after
        rounds.append([sorted(row) for row in current])
    context = dict(rules=rules, target=model.target, hypotheses=model.hypotheses,
                   bound=model.bound, forbidden=sorted(model.forbidden),
                   transformations='identity', capacity=12)
    return dict(version='dependency-budget-certificate-001',
                context_sha256=hashlib.sha256(canonical(context)).hexdigest(),
                formulas=formulas, given=sorted(given), eligible_rules=eligible,
                rounds=rounds, required=[len(row) for row in current],
                target=ids[model.target], seconds=time.perf_counter()-began,
                scope='Necessary distinct original inference outputs before each formula, excluding supplied hypotheses, for every valid proof in this finite rule grammar and fixed ambient scope.')


class Model(M.Model):
    def __init__(self, catalog, target, bound, hypotheses=(), certificate=None):
        super().__init__(catalog, target, bound, hypotheses)
        self.certificate = certificate
        if certificate is not None:
            context = dict(rules=self.catalog['rules'], target=self.target,
                           hypotheses=self.hypotheses, bound=self.bound,
                           forbidden=sorted(self.forbidden), transformations='identity', capacity=12)
            if certificate['context_sha256'] != hashlib.sha256(canonical(context)).hexdigest():
                raise ValueError('budget certificate context')
            fs = [M.freeze(a) for a in certificate['formulas']]
            ids = {a: i for i, a in enumerate(fs)}
            rows = [set(row) for row in certificate['rounds'][-1]]
            given = {ids[a] for a in self.hypotheses}
            if len(ids) != len(fs) or len(rows) != len(fs) or certificate['required'] != [len(row) for row in rows]:
                raise ValueError('complete budget table')
            universe = set(range(len(fs))) - given
            if any(not row <= universe for row in rows) or any(rows[i] for i in given):
                raise ValueError('only non-hypothesis necessities')
            for rule in self.catalog['rules']:
                if self.forbidden.intersection(rule['guards']):
                    continue
                output = ids[rule['output']]
                permitted = {output} | set().union(*(rows[ids[a]] for a in rule['inputs']))
                if not rows[output] <= permitted:
                    raise ValueError('unsound necessary-formula certificate')
        self.requirements = ({M.freeze(a): n for a, n in
                              zip(certificate['formulas'], certificate['required'])}
                             if certificate is not None else {})

    def initial(self):
        state = super().initial()
        if self.certificate is not None:
            state.marks.update((point(j), 0) for j in range(self.length))
        return state

    def assignments(self, key):
        if self.certificate is None:
            return ()
        j, rid, refs = M.freeze(key)
        if rid >= 0:
            rule = self.catalog['rules'][rid]
            bindings = [(j, rule['output'])] + list(zip(refs, rule['inputs']))
        elif rid == self.END:
            bindings = [(j-1, self.target)]
        else:
            bindings = []
        values = {}
        for i, formula in bindings:
            if i >= 0:
                value = int(self.requirements[formula] > i+1)
                if point(i) in values and values[point(i)] != value:
                    raise ValueError('single-valued budget marking')
                values[point(i)] = value
        return tuple(sorted(values.items()))

    def placement(self, key):
        key = M.freeze(key)
        if key in self.cache:
            return self.cache[key]
        original = super().placement(key)
        values = dict(original.marks)
        values.update(self.assignments(key))
        decorated = Placement(key, original.occupancy, tuple(sorted(values.items())), ())
        self.cache[key] = decorated
        return decorated

    def mask(self, formula, j):
        h = len(self.hypotheses)
        first = min(j, max(0, self.requirements[formula]-1))
        positives = ((1 << j)-1) & ~((1 << first)-1)
        return ((1 << h)-1) | (positives << h)


class Graph(M.Graph):
    def __init__(self, model, state):
        self.check_root(model, state)
        super().__init__(model, state)

    @staticmethod
    def check_root(model, state):
        if model.certificate is not None and any(state.marks.get(point(j)) != 0
                                                for j in range(model.length)):
            raise ValueError('fixed distant budget root values')

    def update(self, model, state, changed):
        self.check_root(model, state)
        super().update(model, state, changed)

    def copy(self):
        graph = object.__new__(type(self))
        graph.m = self.m
        for name in ('ports', 'flows', 'scopes', 'learned', 'domains'):
            setattr(graph, name, getattr(self, name).copy())
        graph.order = self.order
        return graph

    def calculate(self, p):
        raw = super().calculate(p)
        m, j = self.m, p[0]//2
        if m.certificate is None:
            return raw
        blocks = []
        for rid, masks, distinct in raw.base.blocks:
            rule = m.catalog['rules'][rid]
            if m.requirements[rule['output']] > j+1:
                continue
            narrowed = tuple(mask & m.mask(a, j)
                             for mask, a in zip(masks, rule['inputs']))
            if all(narrowed) and (not distinct or
                    Q.count(narrowed[0])*Q.count(narrowed[1]) >
                    Q.count(narrowed[0] & narrowed[1])):
                blocks.append((rid, narrowed, distinct))
        structural = tuple(k for k in raw.structural
                           if k[1] != m.END or k[0] == 0 or
                           m.requirements[m.target] <= k[0])
        domain = M.Domain(Q.Domain(j, len(m.hypotheses), blocks),
                          structural, raw.excluded)
        m.metrics['budget_domain_candidates_before'] += len(raw)
        m.metrics['budget_domain_candidates_after'] += len(domain)
        m.metrics['budget_candidates_removed'] += len(raw)-len(domain)
        return domain
