"""Certified two-row failures encoded as ordinary distant marking values.

The teacher is an original, undecorated prefix with two fixed formula words.
A negative forbids their conjunction, not either formula on its own. There is
no clause scanner or lookahead in the marked search. Scope: finite proof strips.
"""
import collections, copy, time
from certificate_boundary_search import canonical, digest
from semantic_receptor_points import Model
from semantic_inventory_search import search
from native_receptor_points import assignment
from prefix_failure_markings import context, catalog as unary_catalog, prefix_spec, prefix_lift
from turtle import Placement


class Teacher(Model):
    def __init__(self, parent, row):
        left, right = row['slots']
        spec = prefix_spec(parent.spec, right + 1, row['formulas'][1])
        spec['id'] = parent.spec['id'] + '-pair-' + str(row['id'])
        spec['scope'] = 'Original prefix with two fixed output words, whole-parent vocabulary and inventory.'
        super().__init__(spec, parent.compiled, parent.inventory)
        self.boundary = dict(assignment(left, 'formula', row['formulas'][0]))

    def initial(self):
        state = super().initial()
        for p, value in self.boundary.items():
            if p in state.marks and state.marks[p] != value:
                raise ValueError('two distinct fixed output words overlap')
            state.marks[p] = value
        return state

    def record(self):
        return dict(super().record(), initial_marks=sorted(self.initial().marks.items()))


def catalog(parent, row_pairs):
    pairs = sorted(set(tuple(p) for p in row_pairs))
    if len(pairs) != len(row_pairs) or any(not 0 <= a < b < parent.spec['length'] for a, b in pairs):
        raise ValueError('declare distinct ordered row pairs in this rectangle')
    groups = collections.defaultdict(list)
    for row in unary_catalog(parent):
        groups[row['slot']].append(row)
    out = []
    for left, right in pairs:
        for a in groups[left]:
            for b in groups[right]:
                out.append(dict(id=len(out), slots=[left, right],
                    formulas=[copy.deepcopy(a['formula']), copy.deepcopy(b['formula'])],
                    command_keys=[a['command_keys'], b['command_keys']]))
    return out


def learn(parent, row_pairs, attempts=400, seconds=.5, check=None):
    began = time.perf_counter()
    rows = catalog(parent, row_pairs)
    probes = []
    counts = collections.Counter()
    for row in rows:
        teacher = Teacher(parent, row)
        lift = prefix_lift(parent, teacher, row['formulas'][1])
        out = search(teacher, 'base', attempts=attempts, seconds=seconds)
        label = {'finite_marked_proof_region': 'positive',
                 'exhausted_finite_marked_region': 'negative',
                 'unknown_search_budget': 'unknown'}[out['status']]
        counts[label] += 1
        probe = dict(**row, spec=teacher.spec, model=teacher.record(), lift=lift,
                     search=out, label=label)
        if check is not None:
            probe['independent_check'] = check(parent, probe)
        probes.append(probe)
    return dict(version='conditional-failure-learning-001', context=context(parent),
        context_sha256=digest(context(parent)), row_pairs=sorted(map(list, row_pairs)),
        catalog=rows, probes=probes, counts=dict(counts),
        limits=dict(attempts=attempts, seconds=seconds), seconds=time.perf_counter()-began,
        scope='Complete Cartesian formula catalogs at the declared row pairs, not all row pairs. Original logical markings only in teachers. Exhausted causal prefixes justify grammar-scoped redundant conjunction exclusions; unknowns supply none. No Turtle corona or unrestricted logical unprovability claim.')


def points(probe_id):
    # Original marks have x congruent to 0, 1 or 2 modulo 4. Notebook 64's
    # unary ports have x congruent to 3 and y near 100000. These private ports
    # use a separate namespace for each conjunction and its single-tile case.
    return (3, 200000 + 2*probe_id), (3, 200001 + 2*probe_id)


class MarkedModel(Model):
    def __init__(self, base, learning, certificate):
        if certificate.get('status') != 'passed' or certificate['learning_sha256'] != digest(learning):
            raise ValueError('conditional layer needs an independently checked transcript')
        if context(base) != learning['context'] or certificate['context_sha256'] != digest(context(base)):
            raise ValueError('conditional marking belongs to a different grammar context')
        self.__dict__ = base.__dict__.copy()
        self.cache = base.cache.copy()
        self.dependencies = collections.defaultdict(set, {p:set(ks) for p,ks in base.dependencies.items()})
        self.metrics = collections.Counter()
        self.exterior = {}
        self.failures = []
        original = {k:dict(c.marks) for k,c in base.cache.items()}
        for probe in learning['probes']:
            if probe['label'] != 'negative':
                continue
            if probe['search']['status'] != 'exhausted_finite_marked_region':
                raise ValueError('unfinished conditional teacher cannot exclude')
            words = [assignment(slot, 'formula', f) for slot,f in zip(probe['slots'],probe['formulas'])]
            groups = [{k for k,values in original.items() if all(values.get(p)==v for p,v in word)}
                      for word in words]
            both = groups[0] & groups[1]
            pair, single = points(probe['id'])
            if both:
                self.exterior[single] = 0
            assigned = []
            for k in sorted(groups[0] | groups[1]):
                c = self.cache[k]
                point, value = (single,1) if k in both else (pair,0 if k in groups[0] else 1)
                if any(p==point for p,v in c.occupancy+c.marks):
                    raise ValueError('conditional port collision')
                self.cache[k] = Placement(c.key,c.occupancy,tuple(sorted(c.marks+((point,value),))),c.vertices)
                self.dependencies[point].add(k)
                assigned.append(dict(key=k,point=point,value=value))
            self.failures.append(dict(probe=probe['id'],slots=probe['slots'],formulas=probe['formulas'],
                pair_point=pair,single_point=single,left_keys=sorted(groups[0]-both),
                right_keys=sorted(groups[1]-both),joint_keys=sorted(both),assignments=assigned))
        self.learning_pin = digest(learning)
        self.certificate = certificate
        if set(self.cache)!=set(base.cache) or self.align_cache!=base.align_cache:
            raise ValueError('conditional layer changed the candidate universe')

    def initial(self):
        state = super().initial()
        state.marks.update(self.exterior)
        return state

    def record(self):
        return dict(super().record(),initial_marks=sorted(self.initial().marks.items()),
            conditional_overlay=dict(learning_sha256=self.learning_pin,
                context_sha256=digest(context(self)),certificate=self.certificate,
                exterior=sorted(self.exterior.items()),failures=self.failures),
            scope='Original t-data, roots, complete candidate identities and alignments. Opposing exact values encode each certified two-word conjunction; a candidate writing both gets a separately fixed exclusion port. All rejection uses the ordinary point graph.')


class CombinedModel(Model):
    def __init__(self,base,unary,pair):
        self.__dict__=base.__dict__.copy()
        self.cache=base.cache.copy()
        self.dependencies=collections.defaultdict(set)
        self.metrics=collections.Counter()
        self.exterior={}
        for layer in (unary,pair):
            if set(layer.cache)!=set(base.cache) or layer.align_cache!=base.align_cache:
                raise ValueError('combined layer changes original candidates')
            for p,v in layer.exterior.items():
                if p in self.exterior and self.exterior[p]!=v:raise ValueError('combined fixed-value collision')
                self.exterior[p]=v
        for k,c in base.cache.items():
            values=dict(c.marks)
            for layer in (unary,pair):
                if layer.cache[k].occupancy!=c.occupancy:raise ValueError('combined occupancy change')
                for p,v in layer.cache[k].marks:
                    if p in values and values[p]!=v:raise ValueError('combined tile-value collision')
                    values[p]=v
            tile=Placement(c.key,c.occupancy,tuple(sorted(values.items())),c.vertices)
            self.cache[k]=tile
            for p,v in tile.occupancy+tile.marks:self.dependencies[p].add(k)
        self.combination=dict(unary_certificate=unary.certificate,pair_certificate=pair.certificate,
                              unary_record_sha256=digest(unary.record()),pair_record_sha256=digest(pair.record()))

    def initial(self):
        state=super().initial();state.marks.update(self.exterior);return state

    def record(self):
        return dict(super().record(),initial_marks=sorted(self.initial().marks.items()),
                    combined_overlay=dict(**self.combination,exterior=sorted(self.exterior.items())),
                    scope='Compatible union of independently certified unary and conditional point layers; all base placements and ordinary search decisions retained.')
