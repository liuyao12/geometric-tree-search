"""Authored whole-hint lifecycle over the unchanged complete primitive graph.

Descriptors are ordering advice, never native-admitted interfaces or atomic tiles.
The actual 229/217/24 loader has a separate, unexecuted full-language gate.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CORE_PATH = ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py'
CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'
if hashlib.sha256(CORE_PATH.read_bytes()).hexdigest() != CORE_SHA:
    raise ValueError('frozen primitive core changed')
_spec = importlib.util.spec_from_file_location('hilbert_lifecycle_frozen_primitive_core_v2', CORE_PATH)
core = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = core
_spec.loader.exec_module(core)
VERSION = 'whole-cluster-lifecycle-v1'


def exact_keys(data):
    result = []
    for value in data:
        if not isinstance(value, list) or len(value) != 3 or not isinstance(value[2], list):
            raise ValueError('literal full key triple required')
        result.append(core.Key(core.integer(value[0]), core.integer(value[1]),
                               tuple(core.integer(r) for r in value[2])))
    return tuple(result)


def graph_binding(g):
    # Untracked public metadata mutation is detected before hint continuation;
    # a new rule/version requires a separate accepted-prefix replay protocol.
    authority_body = {k: v for k, v in g.authority.items() if k != 'epoch'}
    if (core.digest(g.formulas) != g.registry_sha or core.digest(g.context) != g.context_id
            or core.digest(authority_body) != g.authority_epoch
            or g.authority.get('epoch') != g.authority_epoch
            or g.authority.get('activated') is not False or g.authority.get('native_accepted') is not False):
        raise ValueError('untracked model/context/registry/authority metadata mutation')
    palette = [{'id': r.identifier, 'witness': r.witness, 'premises': r.formulas,
                'output': r.output, 'inputs': list(r.inputs)} for r in g.recipes]
    return {'model_epoch': g.model_epoch, 'context_id': g.context_id,
            'formula_registry_sha256': g.registry_sha, 'authority_epoch': g.authority_epoch,
            'primitive_palette_sha256': core.digest(palette),
            'boundary_sha256': core.digest({'height': g.height, 'roots': g.roots,
                                           'fixed_marks': [[*p, v] for p, v in sorted(g.initial_marks.items())],
                                           'initial_selected': [k.data() for k in g.initial_selected]}),
            'source_bindings_sha256': core.digest(g.source_bindings),
            'marking_version': core.MARKING_VERSION, 'orientation': 'identity',
            'core_sha256': CORE_SHA, 'native_accepted': False, 'engine_authority_activated': False}


def _union(g, members):
    """Exact distinct constituent union; repeated *ports* are never removed."""
    t, m = {}, {}
    for key in members:
        points, marks = g.point_data(key)
        for x, y, value in points:
            p = (x, y); t[p] = t.get(p, 0) + value
            if t[p] > 1:
                raise ValueError('distinct members overfill their aggregate')
        for x, y, value in marks:
            p = (x, y)
            if p in m and m[p] != value:
                raise ValueError('inconsistent aggregate marking function')
            m[p] = value
    return tuple((*p, v) for p, v in sorted(t.items())), tuple((*p, v) for p, v in sorted(m.items()))


def primitive_body(g, name, keys):
    """Root-authored arbitrary primitive proposal, not a closed lemma certificate.

    This does not impose a known tiling strategy. The complete graph supplies
    all base placements independently of whether any such body was registered.
    """
    keys = tuple(keys)
    if not keys or len(set(keys)) != len(keys):
        raise ValueError('body has nonempty distinct ordered member occurrences')
    if any(a.row >= b.row for a, b in zip(keys, keys[1:])):
        raise ValueError('source body member order must be strictly prior')
    _union(g, keys)
    rows = {k.row for k in keys}
    input_rows = sorted({r for k in keys for r in k.refs if r not in rows})
    input_values = {}
    members = []
    for k in keys:
        recipe = g._recipe_key(k)
        for r, code in zip(k.refs, recipe.inputs):
            if r in input_rows:
                if r in input_values and input_values[r] != code:
                    raise ValueError('external receptor has conflicting formulas')
                input_values[r] = code
        members.append({'row': k.row, 'recipe_id': recipe.identifier,
                        'formula_code': recipe.output, 'ordered_inputs': list(k.refs)})
    body = {'kind': 'authored_primitive_proposal_not_closed_lemma', 'name': name,
            'canonical_input_rows': input_rows, 'premise_codes': [input_values[r] for r in input_rows],
            'primitive_members': members, 'dependency_bindings': [], 'native_accepted': False}
    body['ordered_receptor_ports'] = receptor_ports(body, g)
    body['source_body_sha256'] = core.digest(body)
    body['mapped_body_sha256'] = body['source_body_sha256']
    return body


def receptor_ports(body, g):
    ports = []
    for index, (row, code) in enumerate(zip(body['canonical_input_rows'], body['premise_codes'])):
        readers = []
        for member in body['primitive_members']:
            recipe = g.recipes[g.recipe_index[member['recipe_id']]]
            for port, (source, expected) in enumerate(zip(member['ordered_inputs'], recipe.inputs)):
                if source == row:
                    if code != expected:
                        raise ValueError('receptor formula differs from literal primitive port')
                    readers.append({'reader_row': member['row'], 'primitive_input_port': port,
                                    'formula_code': code})
        ports.append({'high_level_port': index, 'input_row': row, 'formula_code': code,
                      'new_occupancy': 0, 'readers': readers})
    return ports


@dataclass(frozen=True)
class BodyAuthority:
    """Immutable exact-byte source relation registry; no native activation."""
    graph_text: str
    source_text: str
    bodies: tuple[tuple[str, str], ...]
    epoch: str

    @classmethod
    def build(cls, g, source_bindings, bodies):
        if not source_bindings or not isinstance(source_bindings, list):
            raise ValueError('explicit exact source/certificate/audit bindings required')
        for p in source_bindings:
            if set(p) != {'path', 'sha256', 'bytes'} or not isinstance(p['path'], str):
                raise ValueError('complete literal source pin required')
            if core.integer(p['bytes']) < 0 or len(p['sha256']) != 64:
                raise ValueError('invalid source binding')
        if len({p['path'] for p in source_bindings}) != len(source_bindings):
            raise ValueError('duplicate source pin')
        records, names = [], set()
        for body in bodies:
            b = copy.deepcopy(body)
            if not isinstance(b['name'], str) or not b['name'] or b['name'] in names or b.get('native_accepted') is not False:
                raise ValueError('duplicate body or false native admission claim')
            names.add(b['name'])
            if b['kind'] not in ('authored_primitive_proposal_not_closed_lemma',
                                  'finite_source_body_structurally_certified_not_native_accepted'):
                raise ValueError('unknown body authority relation')
            for field in ('source_body_sha256', 'mapped_body_sha256'):
                if not isinstance(b[field], str) or len(b[field]) != 64:
                    raise ValueError('missing source/mapped body binding')
            input_rows = b['canonical_input_rows']
            if len(input_rows) != len(b['premise_codes']) or len(set(input_rows)) != len(input_rows):
                raise ValueError('canonical premise aliases retain ordered multiplicity')
            mapping = {core.integer(r): core.integer(c) for r, c in zip(input_rows, b['premise_codes'])}
            if any(r < 0 or not 0 <= c < len(g.formulas) for r,c in mapping.items()):
                raise ValueError('canonical receptor row/code outside finite symbolic grammar')
            prior = -1
            for member in b['primitive_members']:
                row = core.integer(member['row'])
                if row <= prior or row in mapping:
                    raise ValueError('strict source member order and distinct input aliases required')
                prior = row
                recipe = g.recipes[g.recipe_index[member['recipe_id']]]
                if core.integer(member['formula_code']) != recipe.output or len(member['ordered_inputs']) != len(recipe.inputs):
                    raise ValueError('body witness differs from exact primitive palette')
                for ref, code in zip(member['ordered_inputs'], recipe.inputs):
                    core.integer(ref)
                    if ref >= row or mapping.get(ref) != code:
                        raise ValueError('body reference missing/prior dependency or wrong formula')
                mapping[row] = recipe.output
            if not b['primitive_members']:
                raise ValueError('nontrivial source body required')
            if b['ordered_receptor_ports'] != receptor_ports(b, g):
                raise ValueError('ordered receptor/read-port projection mismatch')
            if not isinstance(b['dependency_bindings'], list):
                raise ValueError('explicit full earlier dependency bindings required')
            # Dependency bodies are byte-bound in the trusted registry, never caller supplied.
            for dep in b['dependency_bindings']:
                if set(dep) != {'name', 'body_sha256'} or dep['name'] not in names - {b['name']}:
                    raise ValueError('missing or not strict-prior body dependency')
                found = dict(records)[dep['name']]
                if dep['body_sha256'] != core.digest(json.loads(found)):
                    raise ValueError('dependency body binding differs')
            records.append((b['name'], core.canonical(b)))
        graph_text, source_text = core.canonical(graph_binding(g)), core.canonical(source_bindings)
        epoch = core.digest({'graph': json.loads(graph_text), 'sources': json.loads(source_text),
                             'bodies': [[n, core.digest(json.loads(t))] for n, t in records], 'version': VERSION})
        return cls(graph_text, source_text, tuple(records), epoch)

    def body(self, name):
        try:
            return json.loads(dict(self.bodies)[name])
        except KeyError as exc:
            raise ValueError('unknown frozen source body') from exc

    def check_graph(self, g):
        if core.canonical(graph_binding(g)) != self.graph_text:
            raise ValueError('stale model/context/registry/authority relation')
        epoch = core.digest({'graph': json.loads(self.graph_text), 'sources': json.loads(self.source_text),
                             'bodies': [[n, core.digest(json.loads(t))] for n, t in self.bodies], 'version': VERSION})
        if epoch != self.epoch:
            raise ValueError('mutated body authority')

    def expected(self, g, name, input_rows, member_rows, priority):
        self.check_graph(g)
        b = self.body(name)
        core.integer(priority)
        if priority < 0 or len(input_rows) != len(b['canonical_input_rows']) or len(member_rows) != len(b['primitive_members']):
            raise ValueError('complete ordered binding and nonnegative fixed priority required')
        all_rows = tuple(input_rows) + tuple(member_rows)
        if any(type(r) is not int or not 0 <= r < g.height for r in all_rows):
            raise ValueError('binding outside declared finite boundary')
        if any(a >= c for a, c in zip(member_rows, member_rows[1:])):
            raise ValueError('body order cannot be permuted')
        mapping = dict(zip(b['canonical_input_rows'], input_rows))
        mapping.update((m['row'], r) for m, r in zip(b['primitive_members'], member_rows))
        keys = tuple(core.Key(g.recipe_index[m['recipe_id']], r, tuple(mapping[s] for s in m['ordered_inputs']))
                     for m, r in zip(b['primitive_members'], member_rows))
        if len(set(keys)) != len(keys):
            raise ValueError('one body occurrence may not silently erase another')
        t, m = _union(g, keys)
        decorated = [g.decorate(k) for k in keys]
        bound_ports = []
        for port, row, code in zip(b['ordered_receptor_ports'], input_rows, b['premise_codes']):
            bound_ports.append({'high_level_port': port['high_level_port'], 'input_row': row,
                                'formula_code': code, 'new_occupancy': 0,
                                'readers': [{'reader_row': mapping[r['reader_row']],
                                             'primitive_input_port': r['primitive_input_port'],
                                             'formula_code': code,
                                             'offset_value': row - mapping[r['reader_row']]}
                                            for r in port['readers']]})
        # Input aliases constrain marks only: they never install a global hypothesis/seed.
        receptor_m = {}
        for row, code in zip(input_rows, b['premise_codes']):
            point = (1, row)
            if point in receptor_m and receptor_m[point] != code:
                raise ValueError('noninjective receptor map conflicts')
            receptor_m[point] = code
        merged = {(x, y): v for x, y, v in m}
        for point, code in receptor_m.items():
            if point in merged and merged[point] != code:
                raise ValueError('receptor alias conflicts with primitive aggregate')
            merged[point] = code
        data = {'version': VERSION, 'relation': b['kind'], 'graph_binding': json.loads(self.graph_text),
                'source_bindings': json.loads(self.source_text), 'body_authority_epoch': self.epoch,
                'body_name': name, 'body_sha256': core.digest(b),
                'source_body_sha256': b['source_body_sha256'], 'mapped_body_sha256': b['mapped_body_sha256'],
                'dependency_bindings': b['dependency_bindings'], 'ordered_input_rows': list(input_rows),
                'ordered_member_rows': list(member_rows), 'ordered_receptor_ports': bound_ports,
                'fixed_priority': priority, 'members': [k.data() for k in keys],
                'full_member_ids': [v['id'] for v in decorated],
                'full_identity_preimages': [v['identity_preimage'] for v in decorated],
                'aggregate_t': [list(v) for v in t],
                'aggregate_m': [[*p, v] for p, v in sorted(merged.items())],
                'native_accepted': False, 'native_authority_activated': False}
        data['descriptor_id'] = 'whole-cluster-' + core.digest(data)
        return data

    def compile(self, g, descriptor):
        if not isinstance(descriptor, dict):
            raise ValueError('literal descriptor object required')
        expected = self.expected(g, descriptor['body_name'], descriptor['ordered_input_rows'],
                                 descriptor['ordered_member_rows'], descriptor['fixed_priority'])
        if core.canonical(expected) != core.canonical(descriptor):
            raise ValueError('whole descriptor differs from frozen body/identity/authority')
        keys = exact_keys(expected['members'])
        return CompiledDescriptor(core.canonical(expected), keys,
                                  tuple(expected['full_member_ids']),
                                  tuple(tuple(v) for v in expected['aggregate_t']),
                                  tuple(tuple(v) for v in expected['aggregate_m']),
                                  expected['descriptor_id'], expected['fixed_priority'])


@dataclass(frozen=True)
class CompiledDescriptor:
    text: str
    members: tuple
    identities: tuple[str, ...]
    aggregate_t: tuple
    aggregate_m: tuple
    identifier: str
    priority: int


@dataclass(frozen=True)
class HintState:
    status: str
    reason: str | None
    eligible: tuple
    decision: tuple
    revision: int

    def data(self):
        return {'status': self.status, 'reason': self.reason,
                'eligible': [k.data() for k in self.eligible],
                'decision': list(self.decision), 'revision': self.revision}


class Controller:
    """Root-fixed registry. Whole revalidation never mutates graph legality."""
    def __init__(self, graph, authority, descriptors=()):
        self.graph, self.authority = graph, authority
        authority.check_graph(graph)
        compiled, rejected, ids = [], [], set()
        for index, proposal in enumerate(descriptors):
            try:
                item = authority.compile(graph, proposal)
                if item.identifier in ids:
                    raise ValueError('duplicate root descriptor identity')
                ids.add(item.identifier); compiled.append((index, item))
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                rejected.append({'registration': index, 'reason': type(exc).__name__ + ': ' + str(exc),
                                 'payload_sha256': core.digest(proposal)})
        self.descriptors = tuple(v for _, v in sorted(compiled, key=lambda p: (p[1].priority, p[0])))
        self.root_rejected_text = core.canonical(rejected)
        self.states = [HintState('waiting', None, (), ('unresolved', None, 0, None), 0)
                       for _ in self.descriptors]
        self.revision, self.trail = 0, []
        self.metrics = {'whole_scans': 0, 'members_checked': 0, 'mark_checks': 0,
                        'status_updates': 0, 'whole_retirements': 0, 'resynchronizations': 0,
                        'validation_seconds': 0.0, 'ordering_seconds': 0.0,
                        'rollback_seconds': 0.0, 'ordering_calls': 0, 'root_rejections': len(rejected)}
        self.resync()
        self.trail.clear()  # Root state is not a branch transaction.

    def _view(self, descriptor, decision, revision, *, charge=True):
        g = self.graph
        if charge: self.metrics['whole_scans'] += 1
        try:
            self.authority.check_graph(g)
            binding_ok = (core.canonical(graph_binding(g)) == self.authority.graph_text
                          and json.loads(descriptor.text)['body_authority_epoch'] == self.authority.epoch)
        except ValueError:
            binding_ok = False
        if not binding_ok:
            reason = 'stale_frozen_authority'
            return HintState('retired', reason, (), decision, revision)
        additional = {}
        pending = []
        for key, identifier in zip(descriptor.members, descriptor.identities):
            if charge: self.metrics['members_checked'] += 1
            # Full IDs are deterministic in the frozen graph. No formula-only sharing.
            if key in g.selected:
                if g.decorate(key)['id'] != identifier:
                    return HintState('retired', 'selected_identity_mismatch', (), decision, revision)
                continue
            if not g.legal(key):
                return HintState('retired', 'pending_member_illegal', (), decision, revision)
            pending.append(key)
            for x, y, value in g.point_data(key)[0]:
                point = (x, y); additional[point] = additional.get(point, 0) + value
                if g.totals[y] + additional[point] > 1:
                    return HintState('retired', 'pending_aggregate_overcapacity', (), decision, revision)
        for x, y, value in descriptor.aggregate_m:
            if charge: self.metrics['mark_checks'] += 1
            if (x, y) in g.marks and g.marks[x, y] != value:
                return HintState('retired', 'aggregate_remote_mark_conflict', (), decision, revision)
        if not pending:
            return HintState('consumed', None, (), decision, revision)
        eligible = tuple(k for k in pending if decision[0] == 'branch' and k.row == decision[1])
        return HintState('ready' if eligible else 'waiting', None, eligible, decision, revision)

    def resync(self, decision=None):
        start = time.perf_counter()
        decision = decision or self.graph.decision()
        d = (decision.kind, decision.row, decision.count, decision.generation)
        self.trail.append(('revision', self.revision)); self.revision += 1
        for index, descriptor in enumerate(self.descriptors):
            old = self.states[index]
            # Branch retirement is absorbing until paired rollback restores it.
            view = (HintState('retired', old.reason, (), d, self.revision) if old.status == 'retired'
                    else self._view(descriptor, d, self.revision))
            if view != old:
                self.trail.append(('state', index, old)); self.states[index] = view
                self.metrics['status_updates'] += 1
                if old.status != 'retired' and view.status == 'retired':
                    self.metrics['whole_retirements'] += 1
        self.metrics['resynchronizations'] += 1
        self.metrics['validation_seconds'] += time.perf_counter() - start
        return decision

    def ordered(self, decision):
        """Ready exact keys followed by *every* remaining base candidate.

        Timing excludes the caller's work while the iterator is suspended.
        """
        start = time.perf_counter()
        if decision != self.graph.decision() or decision.kind not in ('branch', 'forced'):
            raise ValueError('ordering requires current global graph decision')
        self.resync(decision)
        preferred = (() if decision.kind == 'forced' else
                     tuple(k for state in self.states if state.status == 'ready' for k in state.eligible))
        seen = set()
        self.metrics['ordering_calls'] += 1
        self.metrics['ordering_seconds'] += time.perf_counter() - start
        for key in preferred:
            start = time.perf_counter()
            new = key not in seen
            if new: seen.add(key)
            self.metrics['ordering_seconds'] += time.perf_counter() - start
            if new: yield key
        iterator = iter(self.graph.candidates(decision.row))
        while True:
            start = time.perf_counter()
            try: key = next(iterator)
            except StopIteration:
                self.metrics['ordering_seconds'] += time.perf_counter() - start
                break
            new = key not in seen
            if new: seen.add(key)
            self.metrics['ordering_seconds'] += time.perf_counter() - start
            if new: yield key

    def checkpoint(self):
        return (self.graph.checkpoint(), len(self.trail), self.revision,
                core.digest([v.identifier for v in self.descriptors]), core.digest(self.semantic_state()))

    def rollback(self, checkpoint):
        start = time.perf_counter()
        graph_cp, hint_cp, revision, registry, snapshot_sha = checkpoint
        if registry != core.digest([v.identifier for v in self.descriptors]):
            raise ValueError('root-fixed descriptor registry changed')
        core.integer(hint_cp)
        if not 0 <= hint_cp <= len(self.trail):
            raise ValueError('invalid hint trail checkpoint')
        self.graph.rollback(graph_cp)
        while len(self.trail) > hint_cp:
            entry = self.trail.pop()
            if entry[0] == 'revision': self.revision = entry[1]
            else: self.states[entry[1]] = entry[2]
        if self.revision != revision:
            raise AssertionError('hint revision rollback mismatch')
        if core.digest(self.semantic_state()) != snapshot_sha:
            raise AssertionError('paired graph/hint semantic snapshot rollback mismatch')
        self.metrics['rollback_seconds'] += time.perf_counter() - start

    def semantic_state(self):
        return {'graph': self.graph.semantic_state(), 'hint_states': [s.data() for s in self.states],
                'hint_revision': self.revision, 'descriptor_ids': [v.identifier for v in self.descriptors],
                'root_rejected': json.loads(self.root_rejected_text), 'authority_epoch': self.authority.epoch}


class Executor:
    """Primitive-only execution with whole hints and justified parent exclusions."""
    def __init__(self, controller):
        self.control = controller; self.graph = controller.graph
        self.primitive = core.Executor(self.graph)
        self.events = []  # Cumulative conformance trace; never a proposal or degree input.

    def event(self, kind, **data):
        self.events.append({'kind': kind, **data, 'state': self.control.semantic_state()})

    def step(self, key):
        self.primitive.step(key)  # dead/forced/earliest decision enforced first
        self.control.resync()   # forced and branch effects retire whole hints
        self.event('primitive_step', key=key.data())

    def checkpoint(self):
        return self.control.checkpoint()

    def rollback(self, checkpoint):
        self.control.rollback(checkpoint)
        self.event('paired_rollback', checkpoint=list(checkpoint))

    def solve(self, *, max_attempts, seconds):
        core.integer(max_attempts)
        if (max_attempts < 0 or not isinstance(seconds, (int, float)) or isinstance(seconds, bool)
                or not math.isfinite(seconds) or seconds < 0):
            raise ValueError('nonnegative bounded budget required')
        deadline = time.perf_counter() + seconds
        attempts = self.graph.metrics['attempts']
        initial = self.checkpoint()
        self.event('solve_begin', max_attempts=max_attempts, seconds=seconds)

        def walk():
            checkpoint = self.checkpoint()
            while True:
                decision = self.graph.decision()
                self.event('global_decision', decision=[decision.kind, decision.row, decision.count, decision.generation])
                if decision.kind == 'dead':
                    self.event('proved_dead_child')
                    self.rollback(checkpoint)
                    return 'exhausted_finite_marked_subtree'
                if decision.kind == 'complete':
                    self.control.resync(decision)
                    return 'finite_exact_point_tiling'
                if self.graph.metrics['attempts'] - attempts >= max_attempts or time.perf_counter() >= deadline:
                    self.event('budget_unknown_no_exclusion')
                    self.rollback(checkpoint)
                    return 'unknown_budget'
                # Exhaust the iterator only on demand; degrees are graph facts, not hints.
                candidate = next(self.control.ordered(decision))
                if decision.kind == 'forced':
                    self.step(candidate); continue
                parent = self.checkpoint()
                self.step(candidate)
                status = walk()
                if status == 'finite_exact_point_tiling': return status
                self.rollback(parent)
                if status == 'unknown_budget':
                    self.rollback(checkpoint)
                    return status
                if status != 'exhausted_finite_marked_subtree':
                    raise AssertionError('only a fully exhausted child may create exclusion')
                self.graph.metrics['backtracks'] += 1
                self.graph.exclude_failed_child(candidate)
                self.control.resync()
                self.event('parent_local_exhausted_child_exclusion', key=candidate.data(),
                           child_status=status)
        status = walk()
        if status != 'finite_exact_point_tiling': self.rollback(initial)
        return {'status': status, 'attempts': self.graph.metrics['attempts'] - attempts,
                'certificate': self.graph.point_certificate() if status == 'finite_exact_point_tiling' else None,
                'new_RL_training': False, 'native_queries': 0, 'atomic_macro_moves': 0}


def frozen_family_authority(graph, plan):
    """Actual model helper; NOT called by the synthetic phase.

    Exact compact projection + source/static audit closure is trusted only for
    the earlier finite checked relation. Compiler/native correspondence is open.
    The authored24 example field is discarded and never supplies proposals.
    """
    roles = {}
    for p in plan['inputs']:
        path = ROOT / p['path']
        if core.pin(path) != {k: p[k] for k in ('sha256', 'bytes')}:
            raise ValueError('frozen source/audit/input changed')
        roles[p['role']] = path
    reader = core.read_json(roles['complete_family_template_projection'])
    reader.pop('example', None)
    if reader['formula_codes'] != graph.formulas or reader['authority_epoch'] != graph.authority_epoch:
        raise ValueError('template projection uses different registry/authority')
    audit = core.read_json(roles['primitive_logical_audit'])
    if audit['status'] != 'passed_independent_finite_static_symbolic_and_aggregate_audit':
        raise ValueError('finite source expansion audit not accepted')
    if reader['independent_audit_pin'] != {k: next(p for p in plan['inputs'] if p['role'] == 'primitive_logical_audit')[k]
                                         for k in ('path', 'sha256', 'bytes')}:
        raise ValueError('template projection not bound to exact accepted audit')
    bodies = []
    for d in reader['definitions']:
        b = {'kind': 'finite_source_body_structurally_certified_not_native_accepted', 'name': d['name'],
             'canonical_input_rows': d['canonical_input_rows'], 'premise_codes': d['premise_codes'],
             'primitive_members': [{k: m[k] for k in ('row', 'recipe_id', 'formula_code', 'ordered_inputs')}
                                   for m in d['primitive_members']],
             'source_body_sha256': d['source_body_sha256'], 'mapped_body_sha256': d['mapped_body_sha256'],
             'dependency_bindings': [], 'native_accepted': False,
             'earlier_expansion_closure': 'all recursive source dependencies in pinned full expansion and its independent audit',
             'full_frozen_definition_sha256': core.digest(d)}
        b['ordered_receptor_ports'] = receptor_ports(b, graph)
        bodies.append(b)
    if len(bodies) != 171:
        raise ValueError('all 171 source bodies required')
    # Complete raw closure includes source/native receipt and earlier body evidence.
    pins = [{k: p[k] for k in ('path', 'sha256', 'bytes')} for p in plan['inputs']]
    return BodyAuthority.build(graph, pins, bodies)
