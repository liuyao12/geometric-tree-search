"""SOURCE ONLY untrusted complete-model point producer, compact telemetry.

Original PointGraph and canonical scheduler/recipes are unchanged. Fingerprints
stream every semantic state field plus full trail prefix at rollback boundaries;
no repeated full-state JSON or retained domain snapshot. All provenance/hash/
rollback/phase claims remain untrusted; fresh original checker owns mathematics.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import types
VERSION = 'Q-full-original-model-untrusted-compact-candidate-Source-v4'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'

LIMITS = {'joint_seconds': 20, 'failure_seconds': 55, 'worker_bytes': 524288000,
          'owned_seconds': 60, 'owned_bytes': 536870912, 'caller_seconds': 90,
          'max_attempts': 128, 'max_events': 2000, 'max_candidates': 1}

CURRENT = {'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
    'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
    'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039',
    'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe'}

RULES = {'axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize'}

class Unfinished(TimeoutError):
    """Never means mathematical rejection or exhausted-child justification."""

def need(value, message):
    if not value:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

class Budget:
    """Untrusted integer-native guidance; enclosing parent owns acceptance."""
    def __init__(self, began_ns, deadline_ns):
        need(type(began_ns) is int and type(deadline_ns) is int
             and 0 <= began_ns < deadline_ns < (1 << 63)
             and deadline_ns - began_ns == 20000000000,
             'original coordinator integer joint20, no reset or mixed float clock')
        self.began_ns, self.deadline_ns = began_ns, deadline_ns
        self.clock, self.clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
        self.usage, self.usage_id = resource.getrusage, resource.RUSAGE_SELF
        need(type(self.clock) is types.BuiltinFunctionType and type(self.clock_id) is int,
             'native global clock callable and exact integer clock ID')
        self.counts = {'budget_checks':0, 'fingerprints':0, 'fingerprint_bytes':0,
                       'fingerprint_block_ticks':0, 'event_files':0, 'event_bytes':0,
                       'event_writes':0, 'return_validations':0}
        self.phases = {'construction_begin_ns':None, 'construction_end_ns':None,
                       'search_begin_ns':None, 'search_end_ns':None,
                       'fingerprint_elapsed_ns':0, 'event_serialization_elapsed_ns':0}
        self.check()

    def now(self):
        if (time.clock_gettime_ns is not self.clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != self.clock_id
                or resource.getrusage is not self.usage or resource.RUSAGE_SELF != self.usage_id):
            raise Unfinished('original native clock/resource endpoint changed')
        stamp = self.clock(self.clock_id)
        if type(stamp) is not int or stamp < self.began_ns:
            raise Unfinished('global integer clock domain changed')
        return stamp

    def check(self, *, cleanup=False):
        self.counts['budget_checks'] += 1
        stamp = self.now()
        if (stamp - self.began_ns >= 55000000000
                or self.usage(self.usage_id).ru_maxrss >= 524288000):
            raise Unfinished('producer failure55/500 reserve exceeded')
        if not cleanup and stamp >= self.deadline_ns:
            raise Unfinished('joint20 unfinished; no producer acceptance')
        return stamp

def chunks(value):
    # Full sorted-key canonical traversal, no sampled fields or domain factors.
    if type(value) is dict:
        yield '{'
        for index, name in enumerate(sorted(value)):
            need(type(name) is str, 'literal JSON object key')
            if index:
                yield ','
            yield canonical(name) + ':'
            yield from chunks(value[name])
        yield '}'
    elif type(value) in (list, tuple):
        yield '['
        for index, child in enumerate(value):
            if index:
                yield ','
            yield from chunks(child)
        yield ']'
    else:
        yield canonical(value)

def complete_digest(value, budget, *, cleanup=False):
    budget.check(cleanup=cleanup)
    digest, since_check = hashlib.sha256(), 0
    for text in chunks(value):
        raw = text.encode('utf8')
        digest.update(raw)
        since_check += len(raw)
        if since_check >= 65536:
            budget.check(cleanup=cleanup)
            since_check = 0
    budget.check(cleanup=cleanup)
    return digest.hexdigest()

class FingerprintWriter:
    """Injective typed length-delimited encoding, streamed directly into SHA256.

    No semantic_state(), whole-domain copy/string, or per-depth domain snapshot.
    Collection type/count and scalar type/length are explicit. SHA equality is
    collision-resistance-based producer evidence, not mathematical authority.
    """
    def __init__(self, budget, cleanup):
        self.budget, self.cleanup = budget, cleanup
        self.digest, self.bytes, self.since_tick = hashlib.sha256(), 0, 0

    def write(self, raw):
        need(type(raw) is bytes, 'immutable fingerprint byte block')
        for start in range(0, len(raw), 65536):
            part = raw[start:start + 65536]
            self.digest.update(part)
            self.bytes += len(part)
            self.since_tick += len(part)
            if self.since_tick >= 65536:
                self.budget.check(cleanup=self.cleanup)
                self.budget.counts['fingerprint_block_ticks'] += 1
                self.since_tick = 0

    def begin(self, tag, count):
        need(type(tag) is bytes and tag in (b'L',b'T',b'D',b'K')
             and type(count) is int and count >= 0, 'typed collection header')
        self.write(tag + str(count).encode('ascii') + b':')

    def value(self, value):
        if value is None:
            self.write(b'N')
        elif type(value) is bool:
            self.write(b'B1' if value else b'B0')
        elif type(value) is int:
            raw = str(value).encode('ascii')
            self.write(b'I' + str(len(raw)).encode('ascii') + b':' + raw)
        elif type(value) is str:
            raw = value.encode('utf8')
            self.write(b'S' + str(len(raw)).encode('ascii') + b':' + raw)
        elif type(value) in (list,tuple):
            self.begin(b'L' if type(value) is list else b'T', len(value))
            for item in value:
                self.value(item)
        else:
            raise ValueError('unsupported fingerprint scalar/container type')

    def key(self, key):
        need(type(key.recipe) is int and type(key.row) is int and type(key.refs) is tuple,
             'literal original key value')
        self.begin(b'K',3)
        self.value(key.recipe); self.value(key.row); self.value(key.refs)


def state_fingerprint(graph, budget, *, cleanup=False):
    """All original semantic fields plus full checkpoint/trail-prefix custody.

    Dictionary/set iteration is canonical; native existing factor order and
    ordered/repeated ports are preserved. Metrics are cumulative and excluded,
    exactly as in original semantic_state(). Only fixed-size digest metadata is
    retained by each recursion frame. No snapshot is an independent certificate.
    """
    started = budget.check(cleanup=cleanup)
    writer = FingerprintWriter(budget,cleanup)
    writer.write(b'Q-POINT-STATE-FINGERPRINT-v1:')
    writer.begin(b'D',11)
    writer.value('totals'); writer.value(graph.totals)
    writer.value('marks'); writer.begin(b'L',len(graph.marks))
    for point in sorted(graph.marks):
        writer.value((point[0],point[1],graph.marks[point],graph.mark_refs[point]))
    writer.value('mark_refs'); writer.begin(b'L',len(graph.mark_refs))
    for point in sorted(graph.mark_refs):
        writer.value((point[0],point[1],graph.mark_refs[point]))
    writer.value('order'); writer.begin(b'L',len(graph.order))
    for key in graph.order: writer.key(key)
    writer.value('selected_generations'); writer.begin(b'L',len(graph.selected))
    for key in sorted(graph.selected):
        writer.begin(b'T',2); writer.key(key); writer.value(graph.selected[key])
    writer.value('roots'); writer.value(graph.roots)
    writer.value('excluded'); writer.begin(b'L',len(graph.excluded))
    for excluded in graph.excluded:
        writer.begin(b'L',len(excluded))
        for key in sorted(excluded): writer.key(key)
    writer.value('domains'); writer.begin(b'L',len(graph.domains))
    for domain in graph.domains:
        writer.begin(b'D',4)
        writer.value('factors'); writer.begin(b'L',len(domain.factors))
        for factor in domain.factors:
            writer.value((factor.recipe,factor.left,factor.right,factor.different,factor.count))
        writer.value('base_count'); writer.value(domain.base_count)
        writer.value('excluded_legal'); writer.begin(b'L',len(domain.excluded_legal))
        for key in domain.excluded_legal: writer.key(key)
        writer.value('count'); writer.value(domain.count)
    writer.value('model_epoch'); writer.value(graph.model_epoch)
    checkpoint = graph.checkpoint()
    need(type(checkpoint) is int and checkpoint == len(graph.trail), 'exact complete trail prefix')
    writer.value('checkpoint'); writer.value(checkpoint)
    writer.value('trail_prefix'); writer.begin(b'L',len(graph.trail))
    for entry in graph.trail:
        need(type(entry) is tuple and entry[0] in ('place','exclude'), 'original trail record')
        writer.begin(b'T',len(entry)); writer.value(entry[0]); writer.key(entry[1])
        if entry[0] == 'place':
            need(len(entry)==4, 'complete placement trail entry')
            writer.value(entry[2]); writer.value(entry[3])
        else:
            need(len(entry)==2, 'complete parent-local exclusion entry')
    finished = budget.check(cleanup=cleanup)
    budget.counts['fingerprints'] += 1
    budget.counts['fingerprint_bytes'] += writer.bytes
    budget.phases['fingerprint_elapsed_ns'] += finished-started
    return {'schema':'Q-complete-producer-state-fingerprint-v1',
            'sha256':writer.digest.hexdigest(),'bytes':writer.bytes,'checkpoint':checkpoint}

class CompactEvents:
    """Exclusive bounded complete event files; no full-domain trace authority."""
    def __init__(self, directory, budget):
        self.directory, self.budget = Path(directory), budget
        need(self.directory.is_absolute() and self.directory == self.directory.resolve()
             and not self.directory.exists(), 'exclusive canonical producer event directory')
        self.pins, self.partial = [], []
        budget.check(); self.directory.mkdir(); budget.check()

    def append(self, value, *, cleanup=False):
        started = self.budget.check(cleanup=cleanup)
        if len(self.pins) >= 2000:
            raise Unfinished('complete event ceiling; no missing-event acceptance')
        path = self.directory / ('event-%06d.json' % len(self.pins))
        self.partial.append(str(path))
        raw = canonical(value).encode('utf8') + b'\n'
        need(len(raw)<=65536,'whole compact event bound; never truncate')
        digest, count = hashlib.sha256(),0
        with path.open('xb') as stream:
            for start in range(0,len(raw),65536):
                self.budget.check(cleanup=cleanup)
                block=raw[start:start+65536]
                need(stream.write(block)==len(block),'whole compact event write')
                digest.update(block);count+=len(block)
                self.budget.counts['event_writes'] += 1
        finished=self.budget.check(cleanup=cleanup)
        record={'path':str(path),'sha256':digest.hexdigest(),'bytes':count}
        self.pins.append(record);self.partial.remove(str(path))
        self.budget.counts['event_files'] += 1
        self.budget.counts['event_bytes'] += count
        self.budget.phases['event_serialization_elapsed_ns'] += finished-started
        return record

def decision_data(decision):
    return {'kind': decision.kind, 'row': decision.row, 'count': decision.count, 'generation': decision.generation}

def collect_first_ancestry(graph, catalogue, target_code, budget):
    """Complete selected strict-prior expansion only; not a semantic checker."""
    by_row = {key.row: key for key in graph.order}
    need(len(by_row) == len(graph.order), 'one selected occurrence per physical row')
    for row in sorted(by_row):
        budget.check()
        root = by_row[row]
        if graph._recipe_key(root).output != target_code:
            continue
        essential, pending, unresolved = set(), [row], False
        while pending:
            budget.check()
            current = pending.pop()
            if current in essential:
                continue
            key = by_row.get(current)
            if key is None:
                unresolved = True
                break
            recipe = graph._recipe_key(key)
            need(len(key.refs) == len(recipe.inputs), 'whole ordered primitive interface')
            for ref, required_code in zip(key.refs, recipe.inputs):
                need(type(ref) is int and 0 <= ref < key.row, 'strict-prior physical source')
                source = by_row.get(ref)
                if source is None:
                    unresolved = True
                    break
                need(graph._recipe_key(source).output == required_code, 'exact selected ordered formula code')
                pending.append(ref)
            if unresolved:
                break
            essential.add(current)
        if unresolved:
            continue
        keys = [by_row[r] for r in sorted(essential)]
        mapping = {key.row: local for local, key in enumerate(keys)}
        commands = []
        for local, key in enumerate(keys):
            budget.check()
            record = catalogue['recipes'][key.recipe]
            command = copy.deepcopy(record['primitive_witness'])
            need(command['rule'] in RULES and record['id'] == graph.recipes[key.recipe].identifier,
                 'original raw recipe expansion, no lemma/library')
            refs = [mapping[ref] for ref in key.refs]
            need(all(type(ref) is int and 0 <= ref < local for ref in refs), 'rebased ordered prior rows')
            if command['rule'] == 'mp':
                need(len(refs) == 2, 'actual two-port MP')
                command.update(antecedent=refs[0], implication=refs[1])
            elif command['rule'] == 'generalize':
                need(len(refs) == 1, 'actual unary generalize')
                command.update(source=refs[0])
            else:
                need(not refs, 'original zero-port primitive')
            commands.append(command)
        need(1 <= len(commands) == len(keys) <= 24, 'complete finite target ancestry word')
        budget.check()
        return commands, [key.data() for key in keys]
    budget.check()
    return None

def run_untrusted_candidate_search(*, point_module, catalogue, declaration,
        original_source_bindings, binding, coordinator_invocation_id, authority_sha256,
        event_directory, joint_began_ns, joint_deadline_ns):
    """Fresh complete PointGraph, canonical full fallback, first submission only.

    Caller/authenticated FD loading are separate unimplemented integration gates.
    Returned data cannot assert proof, selected provenance, point or resource
    acceptance. Fresh verifier has no dependence on this module's own predicates.
    """
    budget = Budget(joint_began_ns, joint_deadline_ns)
    need(type(binding) is dict and binding == CURRENT, 'fixed original epoch digest binding')
    need(type(coordinator_invocation_id) is str and 1 <= len(coordinator_invocation_id) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in coordinator_invocation_id)
         and type(authority_sha256) is str and len(authority_sha256) == 64
         and all(c in '0123456789abcdef' for c in authority_sha256), 'coordinator opaque invocation and authority digest')
    need(catalogue['declaration'] == declaration and declaration['ordered_Gamma'] == []
         and catalogue['height'] == declaration['height'] == 24, 'whole original declared empty-Gamma24 model')
    boundary = catalogue['boundary']
    budget.phases['construction_begin_ns'] = budget.check()
    graph = point_module.PointGraph(height=catalogue['height'], formulas=catalogue['formula_codes'],
        recipe_data=catalogue['recipes'], context=catalogue['context'], authority=catalogue['authority'],
        fixed_marks=boundary['fixed_marks'], roots=boundary['roots'], seed_keys=(), fixture=False,
        source_bindings=original_source_bindings)
    budget.check()
    need(graph.model_epoch == CURRENT['model_epoch'] and graph.authority_epoch == CURRENT['primitive_authority_epoch']
         and graph.registry_sha == CURRENT['formula_registry_sha256'] and graph.initial_selected == (),
         'entire original graph model, no Source/model epoch replacement')
    # Original constructor has traversed the complete registry and inventory;
    # no target shortlist, alternative compiler or historical proof input.
    need(graph.formulas == catalogue['formula_codes'] and len(graph.recipes) == len(catalogue['recipes']),
         'whole original registry/recipes retained')
    target_code = next(index for index, formula in enumerate(graph.formulas) if formula == declaration['target'])
    budget.phases['construction_end_ns'] = budget.check()
    events = CompactEvents(event_directory, budget)
    counters = dict(attempts=0, placements=0, forced=0, branch_decisions=0, backtracks=0,
        exclusions=0, nodes=0, rollbacks=0, events=0, ancestry_scans=0)
    outcome = {'candidate': None, 'restoration_failed': False, 'trace_complete': True}
    entry = graph.checkpoint()
    error = None

    def emit(kind, *, node=None, parent=None, depth=0, decision=None, key=None,
             status=None, fingerprint=False, cleanup=False):
        budget.check(cleanup=cleanup)
        state = state_fingerprint(graph,budget,cleanup=cleanup) if fingerprint else None
        ordinal = counters['events']
        record = {'schema':'Q-untrusted-producer-compact-event-v2','event':ordinal,
            'observed_native_ns':budget.check(cleanup=cleanup),
            'budget_counts_before_event_serialization':dict(budget.counts),
            'budget_phase_intervals_before_event_serialization':dict(budget.phases),
            'kind':kind,'node':node,'parent':parent,'depth':depth,'decision':decision,
            'key':None if key is None else key.data(),'producer_status':status,
            'counters':dict(counters),'graph_metrics':dict(graph.metrics),
            'checkpoint':graph.checkpoint(),'state_fingerprint':state,
            'producer_claim_only':True,'full_domain_snapshot':False,
            'independent_trajectory_replay_accepted':False}
        raw = events.append(record,cleanup=cleanup)
        counters['events'] += 1
        return {'event':ordinal,'state_fingerprint':state,'file':raw}

    def place(key, decision, node, parent, depth):
        budget.check()
        if counters['attempts'] >= 128:
            raise Unfinished('all-base placement attempt ceiling128')
        current = graph.decision()
        need(decision_data(current) == decision and current.kind in ('forced', 'branch')
             and key.row == current.row and graph.legal(key), 'original complete reference scheduler/legal base move')
        if current.kind == 'forced':
            iterator = iter(graph.candidates(current.row))
            need(next(iterator, None) == key and next(iterator, None) is None, 'whole singleton EOF')
        counters['attempts'] += 1
        graph._apply_legal(key)
        counters['placements'] += 1
        if current.kind == 'forced':
            counters['forced'] += 1
        budget.check()
        emit('forced_place' if current.kind == 'forced' else 'branch_place',
             node=node, parent=parent, depth=depth, decision=decision, key=key)

    def walk(parent, depth):
        budget.check()
        need(depth <= graph.height, 'finite board recursion')
        node = counters['nodes']
        counters['nodes'] += 1
        checkpoint = graph.checkpoint()
        before = emit('node_enter', node=node, parent=parent, depth=depth, fingerprint=True)
        local_status = 'UNKNOWN'
        try:
            while True:
                budget.check()
                decision = decision_data(graph.decision())
                event = emit('decision', node=node, parent=parent, depth=depth, decision=decision)
                if decision['kind'] == 'dead':
                    local_status = 'EXHAUSTED_PRODUCER_SUBTREE'
                    return local_status
                counters['ancestry_scans'] += 1
                candidate = collect_first_ancestry(graph, catalogue, target_code, budget)
                if candidate is not None:
                    commands, physical_keys = candidate
                    outcome['candidate'] = {'schema': 'Q-untrusted-first-candidate-word-v1',
                        'coordinator_invocation_id': coordinator_invocation_id,
                        'authority_sha256': authority_sha256, 'binding': copy.deepcopy(binding),
                        'submission_index': 0, 'commands': commands,
                        'origin': {'kind': 'producer_claimed_selected_original_target_ancestry',
                            'source_event_index': event['event'], 'physical_keys': physical_keys},
                        'termination': {'producer_status': 'CANDIDATE_NOT_VERIFIED',
                            'root_rollback_claimed': False, 'proof_accepted': False,
                            'full24_accepted': False, 'trajectory_accepted': False}}
                    local_status = 'CANDIDATE_NOT_VERIFIED'
                    return local_status
                if decision['kind'] == 'complete':
                    # Point completeness is only a producer claim and does not
                    # create a proof/full24 certificate or independent rejection.
                    local_status = 'UNKNOWN_COMPLETE_BOARD_WITHOUT_CANDIDATE'
                    return local_status
                iterator = iter(graph.candidates(decision['row']))
                key = next(iterator, None)
                need(key is not None, 'positive domain has original canonical first candidate')
                if decision['kind'] == 'forced':
                    place(key, decision, node, parent, depth)
                    continue
                need(decision['kind'] == 'branch', 'earliest-generation branch only')
                counters['branch_decisions'] += 1
                parent_checkpoint = graph.checkpoint()
                parent_state = emit('branch_checkpoint', node=node, parent=parent, depth=depth, fingerprint=True)
                place(key, decision, node, parent, depth)
                child_status = walk(node, depth + 1)
                graph.rollback(parent_checkpoint)
                counters['rollbacks'] += 1
                restored = emit('child_rollback', node=node, parent=parent, depth=depth, status=child_status, fingerprint=True)
                need(restored['state_fingerprint'] == parent_state['state_fingerprint'], 'whole exact parent rollback claim')
                if child_status != 'EXHAUSTED_PRODUCER_SUBTREE':
                    local_status = child_status
                    return local_status
                counters['backtracks'] += 1
                graph.exclude_failed_child(key)
                counters['exclusions'] += 1
                emit('producer_exhausted_child_local_exclusion', node=node, parent=parent, depth=depth, key=key)
        finally:
            cleanup = budget.now() >= joint_deadline_ns
            try:
                budget.check(cleanup=cleanup)
                graph.rollback(checkpoint)
                counters['rollbacks'] += 1
                restored = emit('node_unwind', node=node, parent=parent, depth=depth, status=local_status, fingerprint=True, cleanup=cleanup)
                need(restored['state_fingerprint'] == before['state_fingerprint'], 'whole exact node rollback claim')
            except BaseException:
                outcome['restoration_failed'] = True
                outcome['trace_complete'] = False
                raise

    budget.phases['search_begin_ns'] = budget.check()
    initial = emit('run_entry',fingerprint=True)
    try:
        status = walk(None, 0)
        budget.check()
    except BaseException as failure:
        status = 'UNKNOWN'
        outcome['candidate'] = None
        error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    finally:
        cleanup = budget.now() >= joint_deadline_ns
        try:
            budget.check(cleanup=cleanup)
            graph.rollback(entry)
            counters['rollbacks'] += 1
            restored = emit('run_restored', status=status, fingerprint=True, cleanup=cleanup)
            need(restored['state_fingerprint'] == initial['state_fingerprint'], 'whole original run rollback claim')
        except BaseException as failure:
            status = 'UNKNOWN'
            outcome['candidate'] = None
            outcome['restoration_failed'] = True
            outcome['trace_complete'] = False
            error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    budget.phases['search_end_ns'] = budget.check(cleanup=status=='UNKNOWN')
    result = {'schema': 'Q-full-original-model-untrusted-producer-return-v1', 'version': VERSION,
        'producer_status': status, 'candidate': outcome['candidate'], 'error': error,
        'event_files': list(events.pins), 'partial_event_files': list(events.partial),
        'compact_event_sequence_complete_claimed': outcome['trace_complete'],
        'trace_complete_claimed': False, 'full_domain_trace_recorded':False,
        'independent_trajectory_replay_accepted':False,
        'root_rollback_claimed': not outcome['restoration_failed'],
        'counters': dict(counters), 'graph_metrics': dict(graph.metrics),
        'binding': copy.deepcopy(binding), 'candidate_policy': 'first_complete_ancestry_only_max1_no_restart',
        'proof_accepted': False, 'selected_provenance_accepted': False,
        'point_state_accepted': False, 'full24_accepted': False, 'trajectory_accepted': False,
        'mathematical_authority': False, 'ROOT_resource_accepted': False,
        'CLOCK_DOMAIN':CLOCK_DOMAIN,'joint_began_ns':joint_began_ns,'joint_deadline_ns':joint_deadline_ns,
        'phase_counts_observed_before_return_validation':dict(budget.counts),
        'phase_intervals_native_ns':dict(budget.phases),
        'phase_scope':'Construction/search are enclosing intervals; fingerprint/event times nested, never add twice. Outer intake/parse/output/checker/exit remain separate charged costs.',
        'library_used': False, 'rank_used': False, 'RL_used': False, 'native_accepted': False}
    try:
        if result['candidate'] is not None:
            need(status == 'CANDIDATE_NOT_VERIFIED' and not outcome['restoration_failed'], 'only fully unwound candidate can escape')
            result['candidate']['termination']['root_rollback_claimed'] = True
            candidate_bytes = 0
            for text in chunks(result['candidate']):
                candidate_bytes += len(text.encode('utf8'))
                need(candidate_bytes <= 2 * 1048576, 'whole bounded candidate JSON wire')
                budget.check()
            need(type(result['candidate']['origin']['source_event_index']) is int
                 and 0 <= result['candidate']['origin']['source_event_index'] <= 2000,
                 'bounded finite producer source event ordinal')
        budget.counts['return_validations'] += 1
        complete_digest(result, budget, cleanup=status == 'UNKNOWN')
        budget.check(cleanup=status == 'UNKNOWN')
    except BaseException as failure:
        result['producer_status'], result['candidate'] = 'UNKNOWN', None
        result['error'] = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    return result
