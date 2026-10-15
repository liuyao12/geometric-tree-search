"""UNEXECUTED full-model candidate producer, explicitly outside proof authority.

No producer checker, Source live-custody validator or no-op guard is used. The
owned coordinator authenticates original data/buffers, loads this and unchanged
PointGraph in the producer process, and accepts mathematics only in its separate
fresh verifier. This module exposes a callable, not a qualified cold CLI/owner.
All snapshots, rollback equality and provenance below remain producer claims.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import resource
import time

VERSION = 'Q-full-original-model-untrusted-first-candidate-Source-v2'
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
    """Native producer accounting only; coordinator independently enforces all costs.

    There is no semantic/source_guard argument and no hidden live-guard waiver.
    Failure-only cleanup may use55; it cannot create/send a candidate after20.
    """
    def __init__(self, began, deadline):
        need(type(began) in (int, float) and type(deadline) in (int, float)
             and math.isfinite(began) and math.isfinite(deadline)
             and deadline == began + 20, 'original coordinator joint20, no reset')
        self.began, self.deadline = began, deadline
        self.check()

    def check(self, *, cleanup=False):
        now = time.perf_counter()
        if now - self.began >= 55 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 524288000:
            raise Unfinished('producer failure reserve55/500 exceeded')
        if not cleanup and now >= self.deadline:
            raise Unfinished('joint20 unfinished; no producer acceptance')


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


class FullEvents:
    """Untrusted complete event files, no mathematical/custody acceptance latch."""
    def __init__(self, directory, budget):
        self.directory, self.budget = Path(directory), budget
        need(self.directory.is_absolute() and self.directory == self.directory.resolve()
             and not self.directory.exists(), 'exclusive canonical producer event directory')
        self.pins, self.partial = [], []
        budget.check()
        self.directory.mkdir()
        budget.check()

    def append(self, value, *, cleanup=False):
        self.budget.check(cleanup=cleanup)
        if len(self.pins) >= 2000:
            raise Unfinished('complete event ceiling; no missing-event acceptance')
        path = self.directory / ('event-%06d.json' % len(self.pins))
        self.partial.append(str(path))
        digest, count, since_check = hashlib.sha256(), 0, 0
        with path.open('xb') as stream:
            for text in chunks(value):
                raw = text.encode('utf8')
                need(len(raw) <= 4 * 1048576 and stream.write(raw) == len(raw), 'bounded whole event write')
                digest.update(raw)
                count += len(raw)
                since_check += len(raw)
                if since_check >= 65536:
                    self.budget.check(cleanup=cleanup)
                    since_check = 0
        self.budget.check(cleanup=cleanup)
        record = {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': count}
        self.pins.append(record)
        self.partial.remove(str(path))
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
        event_directory, shared_began, deadline):
    """Fresh complete PointGraph, canonical full fallback, first submission only.

    Caller/authenticated FD loading are separate unimplemented integration gates.
    Returned data cannot assert proof, selected provenance, point or resource
    acceptance. Fresh verifier has no dependence on this module's own predicates.
    """
    budget = Budget(shared_began, deadline)
    need(type(binding) is dict and binding == CURRENT, 'fixed original epoch digest binding')
    need(type(coordinator_invocation_id) is str and 1 <= len(coordinator_invocation_id) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in coordinator_invocation_id)
         and type(authority_sha256) is str and len(authority_sha256) == 64
         and all(c in '0123456789abcdef' for c in authority_sha256), 'coordinator opaque invocation and authority digest')
    need(catalogue['declaration'] == declaration and declaration['ordered_Gamma'] == []
         and catalogue['height'] == declaration['height'] == 24, 'whole original declared empty-Gamma24 model')
    boundary = catalogue['boundary']
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
    events = FullEvents(event_directory, budget)
    counters = dict(attempts=0, placements=0, forced=0, branch_decisions=0, backtracks=0,
        exclusions=0, nodes=0, rollbacks=0, events=0, ancestry_scans=0)
    outcome = {'candidate': None, 'restoration_failed': False, 'trace_complete': True}
    entry = graph.checkpoint()
    error = None

    def emit(kind, *, node=None, parent=None, depth=0, decision=None, key=None, status=None, cleanup=False):
        budget.check(cleanup=cleanup)
        state = graph.semantic_state()
        state_sha = complete_digest(state, budget, cleanup=cleanup)
        ordinal = counters['events']
        counters['events'] += 1
        record = {'schema': 'Q-untrusted-producer-full-state-event-v1', 'event': ordinal,
            'kind': kind, 'node': node, 'parent': parent, 'depth': depth, 'decision': decision,
            'key': None if key is None else key.data(), 'producer_status': status,
            'counters': dict(counters), 'graph_metrics': dict(graph.metrics),
            'checkpoint': graph.checkpoint(), 'state': state, 'state_sha256': state_sha,
            'producer_claim_only': True}
        raw = events.append(record, cleanup=cleanup)
        return {'event': ordinal, 'state_sha256': state_sha, 'file': raw}

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
        before = emit('node_enter', node=node, parent=parent, depth=depth)
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
                parent_state = emit('branch_checkpoint', node=node, parent=parent, depth=depth)
                place(key, decision, node, parent, depth)
                child_status = walk(node, depth + 1)
                graph.rollback(parent_checkpoint)
                counters['rollbacks'] += 1
                restored = emit('child_rollback', node=node, parent=parent, depth=depth, status=child_status)
                need(restored['state_sha256'] == parent_state['state_sha256'], 'whole exact parent rollback claim')
                if child_status != 'EXHAUSTED_PRODUCER_SUBTREE':
                    local_status = child_status
                    return local_status
                counters['backtracks'] += 1
                graph.exclude_failed_child(key)
                counters['exclusions'] += 1
                emit('producer_exhausted_child_local_exclusion', node=node, parent=parent, depth=depth, key=key)
        finally:
            cleanup = time.perf_counter() >= deadline
            try:
                budget.check(cleanup=cleanup)
                graph.rollback(checkpoint)
                counters['rollbacks'] += 1
                restored = emit('node_unwind', node=node, parent=parent, depth=depth, status=local_status, cleanup=cleanup)
                need(restored['state_sha256'] == before['state_sha256'], 'whole exact node rollback claim')
            except BaseException:
                outcome['restoration_failed'] = True
                outcome['trace_complete'] = False
                raise

    initial = emit('run_entry')
    try:
        status = walk(None, 0)
        budget.check()
    except BaseException as failure:
        status = 'UNKNOWN'
        outcome['candidate'] = None
        error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    finally:
        cleanup = time.perf_counter() >= deadline
        try:
            budget.check(cleanup=cleanup)
            graph.rollback(entry)
            counters['rollbacks'] += 1
            restored = emit('run_restored', status=status, cleanup=cleanup)
            need(restored['state_sha256'] == initial['state_sha256'], 'whole original run rollback claim')
        except BaseException as failure:
            status = 'UNKNOWN'
            outcome['candidate'] = None
            outcome['restoration_failed'] = True
            outcome['trace_complete'] = False
            error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    result = {'schema': 'Q-full-original-model-untrusted-producer-return-v1', 'version': VERSION,
        'producer_status': status, 'candidate': outcome['candidate'], 'error': error,
        'event_files': list(events.pins), 'partial_event_files': list(events.partial),
        'trace_complete_claimed': outcome['trace_complete'],
        'root_rollback_claimed': not outcome['restoration_failed'],
        'counters': dict(counters), 'graph_metrics': dict(graph.metrics),
        'binding': copy.deepcopy(binding), 'candidate_policy': 'first_complete_ancestry_only_max1_no_restart',
        'proof_accepted': False, 'selected_provenance_accepted': False,
        'point_state_accepted': False, 'full24_accepted': False, 'trajectory_accepted': False,
        'mathematical_authority': False, 'ROOT_resource_accepted': False,
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
        complete_digest(result, budget, cleanup=status == 'UNKNOWN')
        budget.check(cleanup=status == 'UNKNOWN')
    except BaseException as failure:
        result['producer_status'], result['candidate'] = 'UNKNOWN', None
        result['error'] = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    return result
