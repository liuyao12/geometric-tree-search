"""Prospective ROOT-activated bounded real PointGraph/Controller fixture.

No scientific imports occur at module load. This deliberately uses a small
synthetic fixture inventory; it never loads Hilbert input or proves a theorem.
Every primitive action uses unchanged Executor.step. Catalog construction and
negative input mutation are explicit authored fixture operations. No RNG/update.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

VERSION = 'real-Controller-learned-overlay-fixture-v1'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def verify(pin, root):
    path = Path(pin['path'])
    path = path if path.is_absolute() else root / path
    raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('exact immutable pin changed: ' + pin['path'])
    return path


def load(pin, root, name):
    spec = importlib.util.spec_from_file_location(name, verify(pin, root))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FixtureGroupAuthority:
    """Fixture wrapper, not the production 171-body GroupAuthority.

    Original BodyAuthority recompiles the exact full body/primitive identity.
    Metadata augmentation gives the unchanged overlay its component fields.
    Every augmented record is rebuilt and compared in full at registration.
    """
    def __init__(self, graph, original, specs, life):
        self.original, self.life = original, life
        self.graph_text = original.graph_text
        self.spec_text = life.core.canonical(specs)
        self.epoch = life.core.digest(dict(schema='fixture-only-whole-record-wrapper-v1',
            original_epoch=original.epoch, specs=specs, graph=json.loads(self.graph_text)))

    def check_graph(self, graph):
        self.original.check_graph(graph)
        expected = self.life.core.digest(dict(schema='fixture-only-whole-record-wrapper-v1',
            original_epoch=self.original.epoch, specs=json.loads(self.spec_text),
            graph=json.loads(self.graph_text)))
        if expected != self.epoch:
            raise ValueError('stale fixture wrapper epoch')

    def expected(self, graph, index):
        self.check_graph(graph)
        core = self.life.core
        core.integer(index)
        spec = json.loads(self.spec_text)[index]
        original = self.original.expected(graph, spec['name'], spec['input_rows'],
                                           spec['member_rows'], spec['priority'])
        self.original.compile(graph, original)
        body = self.original.body(spec['name'])
        data = copy.deepcopy(original)
        data.update(body_authority_epoch=self.epoch,
            original_body_authority_epoch=self.original.epoch,
            fixture_wrapper_schema='fixture-only-whole-record-wrapper-v1',
            fixture_pool_index=index, fixture_original_record=original,
            components=[dict(name=spec['name'],
                ordered_receptor_ports=copy.deepcopy(original['ordered_receptor_ports']),
                ordered_input_bindings=[dict(kind='fixture_receptor', index=i)
                                        for i in range(len(spec['input_rows']))],
                conclusion_code=body['primitive_members'][-1]['formula_code'],
                conclusion_row=spec['member_rows'][-1])],
            component_member_occurrences=len(original['members']),
            distinct_member_count=len(original['members']), shared_member_count=0)
        data.pop('descriptor_id')
        data['descriptor_id'] = 'fixture-whole-family-' + core.digest(data)
        return data

    def compile(self, graph, descriptor):
        if not isinstance(descriptor, dict):
            raise ValueError('literal complete fixture descriptor required')
        expected = self.expected(graph, descriptor['fixture_pool_index'])
        if self.life.core.canonical(expected) != self.life.core.canonical(descriptor):
            raise ValueError('fixture whole descriptor differs from exact original body/identity/metadata')
        keys = self.life.exact_keys(expected['members'])
        return self.life.CompiledDescriptor(self.life.core.canonical(expected), keys,
            tuple(expected['full_member_ids']), tuple(tuple(v) for v in expected['aggregate_t']),
            tuple(tuple(v) for v in expected['aggregate_m']),
            expected['descriptor_id'], expected['fixed_priority'])


class Harness:
    def __init__(self, scenario, corpus, model_name, proposal_names, modules, source_bindings):
        self.scenario, self.events = scenario, []
        self.life, self.features, self.math, overlay = modules
        self.core = self.life.core
        model = corpus['models'][model_name]
        authority = copy.deepcopy(corpus['authority_body'])
        authority['epoch'] = self.core.digest(authority)
        self.model = dict(height=corpus['height'], formulas=copy.deepcopy(corpus['formulas']),
            recipe_data=copy.deepcopy(corpus['recipes']), context=copy.deepcopy(corpus['context']),
            authority=authority, fixed_marks=copy.deepcopy(model['fixed_marks']),
            roots=copy.deepcopy(model['roots']), seed_keys=copy.deepcopy(model['seed_keys']),
            fixture=True, source_bindings={p['path']: dict(sha256=p['sha256'], bytes=p['bytes'])
                                           for p in source_bindings})
        args = copy.deepcopy(self.model)
        args['seed_keys'] = self.life.exact_keys(args['seed_keys'])
        self.graph = self.core.PointGraph(**args)
        bodies, specs = [], []
        for name in proposal_names:
            p = corpus['proposal_specs'][name]
            keys = self.life.exact_keys(p['members'])
            body = self.life.primitive_body(self.graph, name, keys)
            bodies.append(body)
            specs.append(dict(name=name, input_rows=body['canonical_input_rows'],
                              member_rows=[k.row for k in keys], priority=p['priority']))
        self.bodies, self.specs, self.source_bindings = bodies, specs, source_bindings
        self.original = self.life.BodyAuthority.build(self.graph, source_bindings, bodies)
        self.authority = FixtureGroupAuthority(self.graph, self.original, specs, self.life)
        self.descriptors = [self.authority.expected(self.graph, i) for i in range(len(specs))]
        self.control = self.life.Controller(self.graph, self.authority, self.descriptors)
        if len(self.control.descriptors) != len(specs) or json.loads(self.control.root_rejected_text):
            raise ValueError('complete explicit fixture pool required, no partial activation')
        weights = {name: 0.0 for name in self.features.FEATURE_NAMES}
        if len(weights) != corpus['preserved_protocol']['feature_count']:
            raise ValueError('frozen31 features required')
        self.overlay = overlay.LearnedFamilyOverlay(self.control, self.core,
            self.features, self.math, weights, epsilon=0.1, temperature=1.0,
            maximum_descriptors=64)
        self.primitive = self.core.Executor(self.graph)
        self.record('initial_snapshot', {}, None, None, self.snapshot())

    def decision(self):
        d = self.graph.decision()
        return [d.kind, d.row, d.count, d.generation]

    def snapshot(self):
        return dict(overlay=self.overlay.semantic_state(),
            complete_domains=[[k.data() for k in self.graph.candidates(r)]
                              for r in range(self.graph.height)], decision=self.decision(),
            trail_lengths=dict(graph=len(self.graph.trail), controller=len(self.control.trail),
                               overlay=len(self.overlay.trail)),
            cumulative_metrics=dict(graph=copy.deepcopy(self.graph.metrics),
                                    controller=copy.deepcopy(self.control.metrics)),
            actual_overlay_weights=copy.deepcopy(self.overlay.weights),
            overlay_history=copy.deepcopy(self.overlay.history))

    def record(self, op, payload, before, result, after, error=None):
        value = dict(index=len(self.events), op=op, payload=copy.deepcopy(payload),
                     before=before, result=result, after=after)
        if error is not None: value['error'] = error
        self.events.append(value)
        return result

    def call(self, op, payload, action, *, rejects=False, contains=None):
        before = self.snapshot()
        try:
            result = action()
        except ValueError as exc:
            if not rejects or (contains is not None and contains not in str(exc)): raise
            self.record(op, payload, before, None, self.snapshot(),
                        dict(type='ValueError', message=str(exc)))
            return None
        if rejects: raise AssertionError('negative fixture unexpectedly accepted: ' + op)
        return self.record(op, payload, before, wire(result), self.snapshot())

    def prepare(self):
        holder = {}
        self.call('prepare', {'decision': self.decision()},
                  lambda: holder.setdefault('value', self.overlay.prepare(self.graph.decision())))
        return holder['value']

    def choose(self, prepared, name=None, draw=None, *, rejects=False, contains=None):
        if name is not None:
            ids = prepared['menu']['action_ids']
            identifier = 'NULL' if name == 'NULL' else next(
                d.identifier for d in self.control.descriptors
                if json.loads(d.text)['body_name'] == name)
            # Explicit fixture draw only. Zero weights -> exact uniform menu.
            draw = (ids.index(identifier) + 0.5) / len(ids)
        holder = {}
        self.call('choose', dict(prepared=wire(prepared), supplied_draw=draw,
                                explicit_fixture_action=name),
            lambda: holder.setdefault('value', self.overlay.choose_prepared(prepared, draw)),
            rejects=rejects, contains=contains)
        return holder.get('value')

    def step(self, key):
        self.call('primitive_apply', dict(key=key.data()), lambda: self.primitive.step(key))
        self.call('controller_resync', {}, lambda: self.control.resync())
        self.call('overlay_after_resync', {}, lambda: self.overlay.after_resync())

    def checkpoint(self):
        holder = {}
        self.call('checkpoint', {}, lambda: holder.setdefault('value', self.overlay.checkpoint()))
        return holder['value']

    def rollback(self, checkpoint):
        self.call('paired_rollback', dict(checkpoint=wire(checkpoint)),
                  lambda: self.overlay.rollback(checkpoint))

    def output(self):
        return dict(id=self.scenario, model=self.model,
            source_bindings=self.source_bindings, bodies=self.bodies, descriptor_specs=self.specs,
            original_authority=dict(graph_text=self.original.graph_text,
                source_text=self.original.source_text, bodies=list(self.original.bodies),
                epoch=self.original.epoch),
            wrapper_epoch=self.authority.epoch, descriptors=self.descriptors,
            events=self.events, terminal=self.snapshot(), producer_assertions_passed=True)


def wire(value):
    if hasattr(value, 'data'): return wire(value.data())
    if hasattr(value, 'kind'): return [value.kind, value.row, value.count, value.generation]
    if isinstance(value, dict): return {str(k): wire(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [wire(v) for v in value]
    return value


def run(corpus, modules, bindings):
    outputs = []
    def make(name, model='ordinary', proposals=('ready-Q',)):
        return Harness(name, corpus, model, proposals, modules, bindings)
    def finish(h):
        outputs.append(h.output())
    def check(value, message):
        if not value: raise AssertionError(message)

    h = make('null-full-fallback')
    p = h.prepare(); base = p['base']; keys, record = h.choose(p, 'NULL')
    check(keys == base and record['preferred_keys'] == [] and h.overlay.active_id is None,
          'NULL must suppress all fixed priorities while preserving complete original order')
    finish(h)

    h = make('nonnull-whole-preference')
    p = h.prepare(); keys, record = h.choose(p, 'ready-Q')
    check(keys[0] == h.core.Key(3, 1) and keys[0] != p['base'][0]
          and set(keys) == set(p['base']) and len(keys) == len(p['base']),
          'one whole proposal changes preference, never degrees or fallback')
    finish(h)

    h = make('registration-whole-mutations')
    mutations = []
    for field in ('members', 'full_member_ids', 'aggregate_m', 'components', 'body_authority_epoch'):
        bad = copy.deepcopy(h.descriptors[0])
        if field == 'members': bad[field][0][0] = 1
        elif field == 'full_member_ids': bad[field][0] = 'invalid-full-identity'
        elif field == 'aggregate_m': bad[field].append([1, 5, 0])
        elif field == 'components': bad[field][0]['conclusion_code'] = 0
        else: bad[field] = '0' * 64
        mutations.append((field, bad))
    for field, bad in mutations:
        def register():
            c = h.life.Controller(h.graph, h.authority, [bad])
            check(not c.descriptors and len(json.loads(c.root_rejected_text)) == 1,
                  'whole malformed record must be rejected, no member salvage')
            return dict(descriptor_ids=[d.identifier for d in c.descriptors],
                        rejected=json.loads(c.root_rejected_text), semantic_state=c.semantic_state())
        h.call('invalid_registration', dict(field=field, descriptor=bad), register)
    finish(h)

    h = make('global-distant-dead', 'dead_and_forced')
    check(h.decision() == ['dead', 4, 0, 0] and h.graph.domains[5].count == 1,
          'global distant dead must outrank forced and every proposal')
    h.call('prepare_rejected_global_dead', dict(decision=h.decision()),
           lambda: h.overlay.prepare(h.graph.decision()), rejects=True, contains='global graph decision')
    finish(h)

    h = make('global-forced-no-draw', 'forced')
    p = h.prepare(); keys, record = h.choose(p)
    check(h.decision() == ['forced', 5, 1, 0] and keys == p['base']
          and not p['needs_one_draw'] and record['policy'] is None,
          'global forced singleton must bypass policy and all draws')
    finish(h)

    h = make('forced-active-no-draw', 'pending_source', ('pending-then-future',))
    keys, _ = h.choose(h.prepare(), 'pending-then-future')
    active = h.overlay.active_id; h.step(keys[0])
    check(h.decision()[:3] == ['forced', 2, 1] and h.overlay.active_id == active,
          'pending future member preserves whole active hint under forced interruption')
    p = h.prepare(); keys, record = h.choose(p)
    check(not p['needs_one_draw'] and record['policy'] is None and keys == p['base'],
          'forced active continuation may consume no draw')
    h.step(keys[0]); check(h.overlay.active_id == active, 'forced step preserves waiting continuation')
    finish(h)

    h = make('earlier-generation', 'early_wide')
    check(h.decision() == ['branch', 1, 7, 0] and h.graph.domains[2].count == 3
          and h.graph.point_generation(2) == 2,
          'earlier broad generation must outrank later smaller degree')
    p = h.prepare(); h.choose(p, 'NULL'); finish(h)

    h = make('pending-source-not-fact', 'pending_source', ())
    h.step(h.core.Key(4, 3, (1, 2)))
    rows = h.call('available_facts', {}, lambda: dict(
        complete=h.features.available_rows(h.overlay._feature_graph(), h.overlay.recipes)['complete'],
        fact_potential=h.overlay.fact_potential()))
    check('3' not in rows['complete'] and rows['fact_potential'] == 0,
          'physically selected output with pending ordered sources is no available fact')
    h.step(h.core.Key(2, 2))
    h.step(h.core.Key(0, 1))
    rows = h.call('available_facts', {}, lambda: dict(
        complete=h.features.available_rows(h.overlay._feature_graph(), h.overlay.recipes)['complete'],
        fact_potential=h.overlay.fact_potential()))
    check(rows['complete']['3'] == 1 and rows['fact_potential'] == 2,
          'complete exact dependency closure unlocks output, excludes initial root code')
    finish(h)

    h = make('repeated-ports', proposals=('repeated-source',))
    record = h.descriptors[0]
    check(record['members'] == [[6, 3, [0, 0]]]
          and len(record['ordered_receptor_ports'][0]['readers']) == 2
          and [2, 3, -3] in record['aggregate_m'] and [3, 3, -3] in record['aggregate_m'],
          'both repeated primitive ports and distinct offset channels must survive')
    h.choose(h.prepare(), 'repeated-source'); finish(h)

    h = make('assigned-zero-remote-retirement', proposals=('remote-zero',))
    check([1, 1, 0] in h.descriptors[0]['aggregate_m'] and (1, 1) not in h.graph.marks,
          'assigned zero is a receptor value, missing remains unconstrained')
    h.choose(h.prepare(), 'remote-zero'); h.step(h.core.Key(3, 1))
    check(h.control.states[0].status == 'retired' and h.overlay.active_id is None
          and h.graph.marks[1, 1] == 1 and not h.graph.legal(h.core.Key(4, 4, (1, 2))),
          'distant assigned-zero conflict retires the whole proposal')
    h.call('controller_resync', {}, lambda: h.control.resync())
    check(h.control.states[0].status == 'retired', 'retirement absorbing within this branch')
    finish(h)

    h = make('waiting-persistence', proposals=('waiting-conditional',))
    h.choose(h.prepare(), 'waiting-conditional'); active = h.overlay.active_id
    check(h.control.states[0].status == 'waiting', 'future complete body starts waiting')
    h.step(h.core.Key(0, 1)); p = h.prepare(); keys, record = h.choose(p)
    check(keys == p['base'] and not p['needs_one_draw'] and h.overlay.active_id == active,
          'waiting uses complete base continuation without resampling')
    h.step(h.core.Key(0, 2)); p = h.prepare(); keys, record = h.choose(p)
    check(keys[0] == h.core.Key(2, 3) and record['policy'] is None,
          'same waiting whole hint becomes ready without resampling')
    h.step(keys[0]); keys, _ = h.choose(h.prepare()); check(keys[0] == h.core.Key(4, 4, (1, 3)),
          'included conditional output/source identity preserved')
    h.step(keys[0]); check(h.control.states[0].status == 'consumed' and h.overlay.active_id is None,
          'complete whole consumption ends preference')
    finish(h)

    h = make('paired-rollback'); outer = h.checkpoint(); root = h.overlay.semantic_state()
    keys, _ = h.choose(h.prepare(), 'ready-Q'); inner = h.checkpoint(); active = h.overlay.semantic_state()
    h.step(keys[0]); check(h.overlay.active_id is None, 'consumption ends active hint')
    history = len(h.overlay.history); h.rollback(inner)
    check(h.overlay.semantic_state() == active, 'paired rollback restores selected whole hint and revision')
    h.rollback(outer); check(h.overlay.semantic_state() == root and len(h.overlay.history) == history,
          'complete paired root rollback while cumulative choice history does not rewind')
    finish(h)

    h = make('unknown-no-exclusion'); initial = h.control.semantic_state()
    def unknown():
        executor = h.life.Executor(h.control)
        result = executor.solve(max_attempts=0, seconds=1.0)
        return dict(result=result, unchanged_executor_events=executor.events)
    r = h.call('zero_attempt_unknown', dict(max_attempts=0, seconds=1.0), unknown)
    check(r['result']['status'] == 'unknown_budget' and h.control.semantic_state() == initial
          and all(not values for values in h.graph.excluded),
          'actual unchanged zero-attempt solver UNKNOWN cannot exclude a parent candidate')
    finish(h)

    for name, field in [('stale-prepared-state','prepared_state_sha256'),
                        ('stale-prepared-pool','pool_epoch'), ('stale-prepared-weight','weight_sha256')]:
        h = make(name); p = h.prepare(); p[field] = '0' * 64
        h.choose(p, draw=0.5, rejects=True, contains='stale or changed prepared')
        finish(h)

    for name, mutate in [
        ('mutated-prepared-vector', lambda p: p['menu']['feature_vectors'][0].update(bias=0.25)),
        ('mutated-prepared-action', lambda p: p['menu']['action_ids'].__setitem__(0, 'altered-action')),
        ('mutated-draw-requirement', lambda p: p.update(needs_one_draw=False)),
        ('mutated-draw-bool-type', lambda p: p.update(needs_one_draw=1))]:
        h = make(name); p = h.prepare(); mutate(p)
        h.choose(p, draw=0.5, rejects=True, contains='prepared complete menu or draw requirement')
        finish(h)

    h = make('forced-extra-draw', 'forced'); p = h.prepare()
    h.choose(p, draw=0.5, rejects=True, contains='must consume no draw'); finish(h)
    h = make('continuation-extra-draw', proposals=('waiting-conditional',))
    h.choose(h.prepare(), 'waiting-conditional'); p = h.prepare()
    h.choose(p, draw=0.5, rejects=True, contains='must consume no draw'); finish(h)
    h = make('missing-new-selection-draw'); p = h.prepare()
    h.choose(p, rejects=True, contains='saved draw required'); finish(h)
    h = make('immutable-weight-mutation'); p = h.prepare()
    def alter(): h.overlay.weights['bias'] = 0.25
    h.call('explicit_negative_weight_mutation', dict(feature='bias', value=0.25), alter)
    h.choose(p, draw=0.5, rejects=True, contains='episode weights changed'); finish(h)

    if [r['id'] for r in outputs] != corpus['scenario_order']:
        raise AssertionError('every prospective fixture scenario in frozen order required')
    return dict(schema=VERSION, status='completed_producer_fixture_assertions_pending_independent_replay',
        scenarios=outputs, scope=corpus['scope'], uncovered=corpus['uncovered'],
        feature_count=31, actual_RNG_draws=0, training_updates=0, native_queries=0,
        actual_Hilbert_models=0, mathematical_proofs_accepted=0,
        independent_acceptance=False, unrestricted_cluster_synthesis=False)


def main():
    worker_begin = time.monotonic()
    root = Path(__file__).resolve().parents[2]
    plan_path = Path(sys.argv[1]).resolve()
    plan = json.loads(plan_path.read_text())
    activation_path = root / plan['activation_path']
    activation = json.loads(activation_path.read_text())
    if (activation.get('schema') != 'ROOT-real-Controller-overlay-fixture-activation-v1'
            or activation.get('authorized') is not True
            or activation.get('plan') != dict(path=str(plan_path.relative_to(root)),
                sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(), bytes=plan_path.stat().st_size)):
        raise ValueError('exact separate ROOT activation required')
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixture worker deadline')))
    signal.setitimer(signal.ITIMER_REAL, max(0.001,
        plan['limits']['child_seconds'] - (time.monotonic() - worker_begin)))
    for pin in plan['sources'] + plan['inputs'] + plan['preserved']:
        verify(pin, root)
    verify(plan['runtime']['binary'], root); verify(plan['runtime']['observer'], root)
    if Path(sys.executable).resolve() != Path(plan['runtime']['binary']['path']).resolve():
        raise ValueError('pinned actual Python runtime required')
    start = time.monotonic()
    roles = {p['role']: p for p in plan['inputs'] if 'role' in p}
    life = load(roles['unchanged_lifecycle'], root, 'real_overlay_fixture_lifecycle_v1')
    features = load(roles['frozen_features'], root, 'real_overlay_fixture_features_v1')
    math = load(roles['frozen_math'], root, 'real_overlay_fixture_math_v2')
    overlay = load(roles['overlay_successor'], root, 'real_overlay_fixture_overlay_v2')
    corpus = json.loads(verify(roles['fixture_corpus'], root).read_text())
    bindings = [{k:p[k] for k in ('path','sha256','bytes')} for p in plan['inputs']]
    result = run(corpus, (life, features, math, overlay), bindings)
    result.update(plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        worker_pid=os.getpid(), worker_compute_before_serialization_seconds=time.monotonic()-start,
        kernel_peak_before_final_result_serialization_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output = root / plan['outputs']['result']
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')
    signal.setitimer(signal.ITIMER_REAL, 0.0)


if __name__ == '__main__': main()
