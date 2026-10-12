"""SOURCE ONLY literal unit-point reconstruction for the small real-engine gate.

The declared synthetic fixture language is not Hilbert or PA. No production
imports or factor-based legality helpers. Complete domains come from explicit
ordered reference products; assigned zero and distant marks are ordinary values.
This file is not an owned dispatcher and has never been imported by its author.
"""
import copy
import hashlib
import itertools
import json

MARKING = 'injective-formula-ordered-mp-offset-v1'


def need(condition, label):
    if not condition:
        raise ValueError(label)


def integer(value):
    need(type(value) is int, 'literal integer, not bool')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def key(value):
    need(type(value) in (list, tuple) and len(value) == 3 and type(value[2]) in (list, tuple),
         'complete ordered primitive key')
    return integer(value[0]), integer(value[1]), tuple(integer(v) for v in value[2])


def key_data(value):
    return [value[0], value[1], list(value[2])]


class LiteralFixtureGraph:
    def __init__(self, definition):
        self.definition = copy.deepcopy(definition)
        need(definition['fixture'] is True, 'explicit synthetic point-only gate')
        self.height = integer(definition['height'])
        need(0 < self.height <= 16, 'predeclared small fixture domain; no silent real-model truncation')
        self.formulas = copy.deepcopy(definition['formulas'])
        self.registry_sha = digest(self.formulas)
        codes = {canonical(f): i for i, f in enumerate(self.formulas)}
        need(len(codes) == len(self.formulas), 'injective formula-value registry')
        self.context, self.authority = copy.deepcopy(definition['context']), copy.deepcopy(definition['authority'])
        self.context_id = digest(self.context)
        self.authority_epoch = self.authority['epoch']
        need(self.authority['activated'] is False and self.authority['native_accepted'] is False and
             self.authority_epoch == digest({k: v for k, v in self.authority.items() if k != 'epoch'}),
             'exact inactive authority')
        self.source_bindings = copy.deepcopy(definition.get('source_bindings') or {})
        self.recipes = []
        identifiers = set()
        for record in definition['recipe_data']:
            witness, premises = record['primitive_witness'], record['ordered_premise_formulas']
            need(record['id'] not in identifiers, 'distinct source recipe identities')
            identifiers.add(record['id'])
            need(len(premises) in (0, 2), 'exact frozen zero/two ordered port grammar')
            rule = witness['rule']
            if premises:
                need(rule == 'opaque_pair' or (rule == 'mp' and
                     premises[1] == ['imp', premises[0], witness['formula']]), 'literal fixture pair/MP interface')
            else:
                need(rule in ('axiom', 'instantiate', 'eq_subst', 'assumption', 'fixture_zero'),
                     'declared synthetic zero-port license')
            if rule == 'assumption':
                occurrence = integer(witness['index'])
                gamma = self.context['ordered_local_premises']
                need(0 <= occurrence < len(gamma) and gamma[occurrence] == witness['formula'],
                     'exact occurrence-index assumption')
            self.recipes.append(dict(id=record['id'], witness=copy.deepcopy(witness),
                premises=copy.deepcopy(premises), output=codes[canonical(witness['formula'])],
                inputs=[codes[canonical(f)] for f in premises]))
        self.roots = list(definition['roots'] if definition.get('roots') is not None else [0] * self.height)
        need(len(self.roots) == self.height and all(type(v) is int and v >= 0 for v in self.roots),
             'every required point explicitly activated with its generation')
        self.fixed = {}
        for x, y, value in definition['fixed_marks']:
            integer(x); integer(y); integer(value)
            need((x, y) not in self.fixed or self.fixed[x, y] == value, 'fixed marking agreement')
            self.fixed[x, y] = value
        self.initial_selected = [key(k) for k in definition.get('seed_keys', [])]
        self.epoch = digest(dict(height=self.height, context=self.context, registry=self.registry_sha,
            authority=self.authority_epoch, recipes=[r['id'] for r in self.recipes],
            fixed_marks=[[x, y, v] for (x, y), v in sorted(self.fixed.items())], roots=self.roots,
            seed_keys=[key_data(k) for k in self.initial_selected], marking_version=MARKING,
            fixture=True, source_bindings=self.source_bindings))
        self.totals, self.marks = [0] * self.height, dict(self.fixed)
        self.refs = dict.fromkeys(self.fixed, 1)
        self.selected, self.order = {}, []
        self.excluded = [set() for _ in range(self.height)]
        self.trail = []
        self.metrics = dict(domain_refreshes=self.height, placements=0, forced=0, branches=0,
            backtracks=0, attempts=0, lazy_id_constructions=0, proposal_validations=0, proposal_rejections=0)
        for k in self.initial_selected:
            need(self.recipes[k[0]]['witness']['rule'] == 'assumption', 'seeds are exact recipient assumptions')
            self.apply(k, generation=0)
        self.trail = []

    def points(self, raw):
        i, row, sources = key(raw)
        need(0 <= i < len(self.recipes) and 0 <= row < self.height, 'primitive inventory/alignment')
        recipe = self.recipes[i]
        need(len(sources) == len(recipe['inputs']) and all(0 <= r < row for r in sources),
             'ordered strict-prior sources')
        marking = {(1, row): recipe['output']}
        for port, (source, code) in enumerate(zip(sources, recipe['inputs'])):
            need((1, source) not in marking or marking[1, source] == code, 'internal mark union agreement')
            marking[1, source] = code
            marking[2 + port, row] = source - row
        return [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(marking.items())]

    def legal(self, raw, include_excluded=False):
        try:
            k = key(raw)
            _, marking = self.points(k)
            return (self.totals[k[1]] == 0 and (include_excluded or k not in self.excluded[k[1]]) and
                    all((x, y) not in self.marks or self.marks[x, y] == value for x, y, value in marking))
        except (ValueError, IndexError, TypeError):
            return False

    def candidates(self, row, include_excluded=False):
        integer(row); need(0 <= row < self.height, 'complete required row')
        return [(i, row, sources) for i, recipe in enumerate(self.recipes)
                for sources in itertools.product(range(row), repeat=len(recipe['inputs']))
                if self.legal((i, row, sources), include_excluded)]

    def generation(self, row):
        return min([self.roots[row]] + [g for k, g in self.selected.items() if k[1] == row])

    def decision(self):
        frontier = [r for r in range(self.height) if not self.totals[r]]
        degrees = {r: len(self.candidates(r)) for r in frontier}
        for kind, degree in (('dead', 0), ('forced', 1)):
            selected = [r for r in frontier if degrees[r] == degree]
            if selected:
                row = min(selected)
                return [kind, row, degree, self.generation(row)]
        if not frontier:
            return ['complete', None, 0, None]
        row = min(frontier, key=lambda r: (self.generation(r), degrees[r], r))
        return ['branch', row, degrees[row], self.generation(row)]

    def saved(self):
        return copy.deepcopy((self.totals, self.marks, self.refs, self.selected, self.order, self.excluded))

    def apply(self, raw, generation=None):
        k = key(raw)
        need(self.legal(k) and k not in self.selected, 'literal complete-domain legal distinct placement')
        prior = self.saved()
        _, marking = self.points(k)
        affected = {k[1]}
        gen = self.generation(k[1]) + 1 if generation is None else integer(generation)
        self.totals[k[1]] = 1
        self.order.append(k); self.selected[k] = gen
        for x, y, value in marking:
            if (x, y) not in self.marks:
                if x == 1 and 0 <= y < self.height:
                    affected.update(range(y, self.height))
                elif x in (0, 2, 3) and 0 <= y < self.height:
                    affected.add(y)
            self.marks[x, y] = value
            self.refs[x, y] = self.refs.get((x, y), 0) + 1
        self.trail.append((prior, affected))
        self.metrics['domain_refreshes'] += len(affected)
        self.metrics['placements'] += 1

    def rollback(self, checkpoint):
        integer(checkpoint)
        need(0 <= checkpoint <= len(self.trail), 'exact graph checkpoint')
        affected = set()
        while len(self.trail) > checkpoint:
            prior, rows = self.trail.pop()
            self.totals, self.marks, self.refs, self.selected, self.order, self.excluded = prior
            affected.update(rows)
        self.metrics['domain_refreshes'] += len(affected)

    def semantic(self):
        domains = []
        for row in range(self.height):
            raw = self.candidates(row, include_excluded=True)
            factors = []
            for i, recipe in enumerate(self.recipes):
                matching = [k for k in raw if k[0] == i]
                if not matching:
                    continue
                if not recipe['inputs']:
                    factors.append([i, 0, 0, False, 1])
                else:
                    # Ports are enumerated separately for serial-format equality;
                    # legal count comes from the literal full-key stream above.
                    options = [[source for source in range(row)
                        if ((1, source) not in self.marks or self.marks[1, source] == code) and
                        ((2 + port, row) not in self.marks or self.marks[2 + port, row] == source - row)]
                        for port, code in enumerate(recipe['inputs'])]
                    factors.append([i, sum(1 << r for r in options[0]), sum(1 << r for r in options[1]),
                                    recipe['inputs'][0] != recipe['inputs'][1], len(matching)])
            removed = sorted(k for k in self.excluded[row] if self.legal(k, include_excluded=True))
            domains.append(dict(factors=factors, base_count=len(raw), excluded_legal=[key_data(k) for k in removed],
                                count=len(self.candidates(row))))
        return dict(totals=list(self.totals), marks=[[x, y, v, self.refs[x, y]] for (x, y), v in sorted(self.marks.items())],
            order=[key_data(k) for k in self.order], selected_generations=[[key_data(k), g] for k, g in sorted(self.selected.items())],
            roots=list(self.roots), excluded=[[key_data(k) for k in sorted(values)] for values in self.excluded],
            domains=domains, model_epoch=self.epoch)

    def decorate(self, raw):
        k = key(raw); recipe = self.recipes[k[0]]
        t, m = self.points(k)
        command = copy.deepcopy(recipe['witness'])
        if recipe['inputs']:
            if command['rule'] == 'mp':
                command.update(antecedent=k[2][0], implication=k[2][1])
            else:
                command['ordered_refs'] = list(k[2])
        prototype = dict(recipe_id=recipe['id'], primitive_witness=recipe['witness'],
            ordered_premise_formulas=recipe['premises'], relative_ordered_input_offsets=[r - k[1] for r in k[2]],
            orientation='identity', t=[[x, y - k[1], v] for x, y, v in t], m=[[x, y - k[1], v] for x, y, v in m],
            marking_version=MARKING, formula_registry_sha256=self.registry_sha, authority_epoch=self.authority_epoch)
        preimage = dict(prototype_id='primitive-prototype-' + digest(prototype), prototype_preimage=prototype,
            transform=[0, k[1]], context_id=self.context_id, ordered_input_rows=list(k[2]), primitive_command=command,
            t=t, m=m, authority_epoch=self.authority_epoch, formula_registry_sha256=self.registry_sha)
        return dict(id='aggregate-primitive-' + digest(preimage), identity_preimage=preimage,
                    key=key_data(k), command=command, t=t, m=m)
