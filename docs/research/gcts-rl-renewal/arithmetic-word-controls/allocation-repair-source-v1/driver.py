"""UNEXECUTED baseline Q observer/driver proposal; no project imports.

The cold caller must authenticate the complete admitted original catalogue,
declaration and initial witnesses, and load unchanged graph/checker bytes. It
must seal this module, injected modules and every constructed effective endpoint.
This file neither constructs admission nor supplies a proof route. The old
point-control Executor is never called. Complete event snapshots go to an owned
exclusive stream, not an in-memory array of thousands of full domain relations.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
from pathlib import Path
import resource
import time
import types

VERSION = 'Q-baseline-first-actual-selected-proof-Source-v3'
MARKING = 'injective-formula-ordered-primitive-offset-Q-v1'
RULES = {'axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize'}
LIMITS = {'inner_seconds': 20, 'worker_seconds': 55, 'worker_bytes': 524288000,
          'owned_seconds': 60, 'owned_bytes': 536870912, 'caller_seconds': 90,
          'max_attempts': 128, 'max_events': 2000, 'maximum_visits': 5000000}
CURRENT = {
    'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
    'finite_admission_sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1',
    'finite_certificate_sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87',
    'word_controls_sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1',
    'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
    'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039',
    'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe'}


class Unresolved(TimeoutError):
    """Incomplete work is UNKNOWN, never an exhausted-child justification."""


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def function_state(function):
    need(type(function) is types.FunctionType, 'exact injected Python function')
    return (function, function.__code__, id(function.__defaults__),
            tuple(id(v) for v in function.__defaults__ or ()), id(function.__kwdefaults__),
            tuple((k, id(v)) for k, v in sorted((function.__kwdefaults__ or {}).items())),
            tuple((id(c), id(c.cell_contents)) for c in function.__closure__ or ()))


def blockable(value):
    stack = [value]
    visits = characters = 0
    while stack:
        child = stack.pop()
        visits += 1
        if visits > 512:
            return False
        if type(child) is str:
            characters += len(child)
            if characters > 32768:
                return False
        elif type(child) is int:
            if child.bit_length() > 4096:
                return False
        elif child is None or type(child) in (bool, float):
            pass
        elif type(child) is dict:
            if len(child) > 512:
                return False
            for name, item in child.items():
                if type(name) is not str:
                    return False
                stack.extend((name, item))
                if len(stack) > 512:
                    return False
        elif type(child) in (list, tuple):
            if len(child) > 512:
                return False
            stack.extend(child)
            if len(stack) > 512:
                return False
        else:
            return False
    return True


def chunks(value):
    if blockable(value):
        yield canonical(value)
    elif type(value) is dict:
        yield '{'
        for index, name in enumerate(sorted(value)):
            need(type(name) is str, 'literal JSON key')
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


def invoke(function, anchor, *args, **kwargs):
    # The cold caller also guards this helper's own code before/after entry.
    need(function_state(function) == anchor, 'effective callback code/default/closure changed')
    result = function(*args, **kwargs)
    need(function_state(function) == anchor, 'effective callback changed while invoked')
    return result


class Runtime:
    """One absolute20s plus unchanged whole-worker reserve, never a new clock.

    cleanup=True suppresses only the exhausted inner clock for rollback/failure
    evidence. It cannot be passed to a logical/point check, candidate expansion
    or successful endpoint. A late successful return is downgraded to UNKNOWN.
    Every cleanup cost is still owned55/500 and enclosing60/512/90.
    """
    __slots__ = ('began', 'deadline', 'guard', 'guard_anchor', 'clock', 'usage',
                 'state_function', 'state_code', 'reject', 'reject_code')

    def __init__(self, *, began, deadline, source_guard):
        need(type(began) in (int, float) and type(deadline) in (int, float)
             and math.isfinite(began) and math.isfinite(deadline)
             and deadline == began + LIMITS['inner_seconds'], 'one original absolute20s')
        self.began, self.deadline = began, deadline
        self.state_function, self.state_code = function_state, function_state.__code__
        self.reject, self.reject_code = need, need.__code__
        self.guard, self.guard_anchor = source_guard, function_state(source_guard)
        self.clock, self.usage = time.perf_counter, resource.getrusage
        self.check()

    def check(self, *, cleanup=False):
        if function_state is not self.state_function or function_state.__code__ is not self.state_code:
            raise ValueError('original function-state predicate changed')
        if need is not self.reject or need.__code__ is not self.reject_code:
            raise ValueError('original rejecting endpoint changed')
        if time.perf_counter is not self.clock or resource.getrusage is not self.usage:
            raise ValueError('original clock/resource endpoint changed')
        if self.state_function(self.guard) != self.guard_anchor:
            raise ValueError('original cold guard code/default/closure changed')
        if self.clock() - self.began >= LIMITS['worker_seconds'] or self.usage(resource.RUSAGE_SELF).ru_maxrss >= LIMITS['worker_bytes']:
            raise Unresolved('whole worker55/500 reserve exceeded')
        if not cleanup and self.clock() >= self.deadline:
            raise Unresolved('original shared20s unfinished')
        self.guard()
        # Reject changed original endpoints before postguard delegation.
        if function_state is not self.state_function or function_state.__code__ is not self.state_code:
            raise ValueError('original function-state predicate changed during cold guard')
        if need is not self.reject or need.__code__ is not self.reject_code:
            raise ValueError('original rejecting endpoint changed during cold guard')
        if time.perf_counter is not self.clock or resource.getrusage is not self.usage:
            raise ValueError('original clock/resource endpoint changed during cold guard')
        if self.state_function(self.guard) != self.guard_anchor:
            raise ValueError('cold guard changed during delegation')
        if self.clock() - self.began >= LIMITS['worker_seconds'] or self.usage(resource.RUSAGE_SELF).ru_maxrss >= LIMITS['worker_bytes']:
            raise Unresolved('whole worker reserve exceeded after delegation')
        if not cleanup and self.clock() >= self.deadline:
            raise Unresolved('shared20s exceeded after delegated guard')


def complete_digest(value, runtime, *, cleanup=False):
    runtime.check(cleanup=cleanup)
    h = hashlib.sha256()
    since_boundary = 0
    for chunk in chunks(value):
        raw = chunk.encode('utf8')
        h.update(raw)
        since_boundary += len(raw)
        if since_boundary >= 65536:
            runtime.check(cleanup=cleanup)
            since_boundary = 0
    runtime.check(cleanup=cleanup)
    return h.hexdigest()


class OwnedEvents:
    """Exclusive all-field event files plus an in-memory raw-pin ledger only.

    No field/domain is sampled or omitted. A partial file stays checkable but
    never becomes a completed event pin. Event overflow is UNKNOWN; rollback
    still runs, but omitted cleanup evidence cannot make the trace accepted.
    """
    __slots__ = ('directory', 'runtime', 'pins', 'partial', 'serialization', 'complete')

    def __init__(self, directory, runtime):
        directory = Path(directory)
        need(directory.is_absolute() and directory == directory.resolve()
             and not directory.exists(), 'fresh owned absolute event directory')
        self.directory, self.runtime = directory, runtime
        self.pins, self.partial, self.serialization = [], [], []
        self.complete = True
        runtime.check()
        directory.mkdir()
        runtime.check()

    def append(self, event, *, cleanup=False):
        self.runtime.check(cleanup=cleanup)
        if len(self.pins) >= LIMITS['max_events']:
            self.complete = False
            raise Unresolved('complete event ceiling reached; no omitted-event acceptance')
        path = self.directory / ('event-%06d.json' % len(self.pins))
        self.partial.append(str(path))
        began = self.runtime.clock()
        h = hashlib.sha256()
        count = maximum = since_boundary = 0
        with path.open('xb') as stream:
            for chunk in chunks(event):
                raw = chunk.encode('utf8')
                need(len(raw) <= 4 * 1048576, 'bounded full-event serialization chunk')
                need(stream.write(raw) == len(raw), 'whole event write')
                h.update(raw)
                count += len(raw)
                maximum = max(maximum, len(raw))
                since_boundary += len(raw)
                if since_boundary >= 65536:
                    self.runtime.check(cleanup=cleanup)
                    since_boundary = 0
        self.runtime.check(cleanup=cleanup)
        record = {'path': str(path), 'sha256': h.hexdigest(), 'bytes': count}
        # Full EOF/hash check remains inside this original clock/reserve.
        verify = hashlib.sha256()
        size = 0
        with path.open('rb') as stream:
            for raw in iter(lambda: stream.read(65536), b''):
                self.runtime.check(cleanup=cleanup)
                verify.update(raw)
                size += len(raw)
        need(size == count and verify.hexdigest() == record['sha256'], 'complete saved event byte/SHA/EOF')
        self.runtime.check(cleanup=cleanup)
        self.pins.append(record)
        self.partial.remove(str(path))
        self.serialization.append({'event': len(self.pins) - 1, 'file': record,
            'inclusive_seconds': self.runtime.clock() - began, 'maximum_chunk_bytes': maximum,
            'cleanup_only': cleanup})
        return record


class FirstSelectedProofObserver:
    """Selected-dependency observer, not a proposer or a target-shortlist policy.

    The complete catalogue is authenticated/admitted before this constructor.
    Deriving every primitive interface is allocation-only lookup, not a second
    grammar compiler. New selected word semantics and all24 current domains are
    checked only at a dependency-complete candidate endpoint, inside the same20s.
    """
    __slots__ = ('graph', 'catalogue', 'declaration', 'checker', 'runtime', 'binding',
                 'primitives', 'target_code', 'point_boundary', 'counts')

    def __init__(self, *, graph, catalogue, declaration, checker_module, runtime, context_binding, allocation_guard=None):
        runtime.check()
        need(type(context_binding) is dict and set(context_binding) == {'schema', 'finite_admission',
            'finite_certificate', 'word_controls', 'declaration', 'preparation', 'initial_state_witness',
            'initial_oracle_witness', 'model_epoch', 'primitive_authority_epoch', 'formula_registry_sha256'},
            'exact prospective original-context binding, no new q or admission')
        need(context_binding['schema'] == 'Q-first-selected-proof-original-context-binding-v1'
             and context_binding['finite_admission']['sha256'] == CURRENT['finite_admission_sha256']
             and context_binding['finite_certificate']['sha256'] == CURRENT['finite_certificate_sha256']
             and context_binding['word_controls']['sha256'] == CURRENT['word_controls_sha256']
             and context_binding['declaration']['sha256'] == CURRENT['declaration_sha256'],
             'genuine previously admitted finite raw inputs; cold caller authenticates entire closure')
        need(graph.fixture is False and graph.height == catalogue['height'] == declaration['height'] == 24
             and catalogue['declaration'] == declaration and declaration['ordered_Gamma'] == []
             and catalogue['context'] == graph.context
             and graph.initial_selected == () and graph.initial_marks
             == {(x, y): value for x, y, value in catalogue['boundary']['fixed_marks']},
             'entire original24 empty-Gamma/seedless/fixed-boundary profile')
        need(graph.order == [] and graph.selected == {} and graph.totals == [0] * 24
             and graph.trail == [] and all(not excluded for excluded in graph.excluded)
             and graph.roots == tuple(catalogue['boundary']['roots']),
             'fresh actual graph, no warm prefix or inherited exclusions')
        for name, actual in [('model_epoch', graph.model_epoch), ('primitive_authority_epoch', graph.authority_epoch),
                             ('formula_registry_sha256', graph.registry_sha)]:
            need(context_binding[name] == CURRENT[name] == actual, 'exact original model/authority/registry epoch')
        self.graph, self.catalogue, self.declaration = graph, catalogue, declaration
        self.checker, self.runtime, self.binding = checker_module, runtime, copy.deepcopy(context_binding)
        codes = {canonical(formula): index for index, formula in enumerate(catalogue['formula_codes'])}
        need(len(codes) == len(catalogue['formula_codes'])
             and graph.formulas == catalogue['formula_codes'], 'whole exact injective formula code registry')
        self.target_code = codes[canonical(declaration['target'])]
        primitives = []
        need(len(graph.recipes) == len(catalogue['recipes']), 'entire admitted primitive inventory, not a shortlist')
        if allocation_guard is None:
            for index, record in enumerate(catalogue['recipes']):
                runtime.check()
                witness, premises = record['primitive_witness'], record['ordered_premise_formulas']
                need(witness['rule'] in RULES and record['id'] == graph.recipes[index].identifier,
                     'all original licensed recipe identities')
                primitive = (codes[canonical(witness['formula'])], tuple(codes[canonical(p)] for p in premises))
                need(primitive == (graph.recipes[index].output, graph.recipes[index].inputs)
                     and graph.recipes[index].witness == witness and graph.recipes[index].formulas == premises,
                     'complete graph-to-admitted raw witness/interface correspondence')
                need(record['identity_preimage']['primitive_authority_epoch'] == graph.authority_epoch
                     and record['identity_preimage']['formula_registry_sha256'] == graph.registry_sha,
                     'whole fixed admitted recipe preimage scopes; full hash custody belongs to cold caller')
                primitives.append(primitive)
        else:
            # This exact cold-caller callback is confined to this initializer.
            # Full raw/module/object authority checks still delimit each fixed32
            # batch. No cheap callback is retained or used by observation/search.
            state_fn, reject_fn, invoke_fn = function_state, need, invoke
            state_code, reject_code, invoke_code = state_fn.__code__, reject_fn.__code__, invoke_fn.__code__
            clock, usage, usage_kind = time.perf_counter, resource.getrusage, resource.RUSAGE_SELF
            function_type, method_type = types.FunctionType, types.MethodType
            canonical_fn = canonical
            full_guard = runtime.guard
            runtime_type = type(runtime)
            check_fn = runtime.check.__func__
            began, deadline = runtime.began, runtime.deadline
            need(type(allocation_guard) is function_type and allocation_guard is not full_guard
                 and allocation_guard.__globals__ is full_guard.__globals__
                 and allocation_guard.__module__ == full_guard.__module__
                 and allocation_guard.__code__.co_filename == full_guard.__code__.co_filename,
                 'exact initializer-only callback from the original authenticated cold namespace')
            signature_anchors = tuple((fn, state_fn(fn)) for fn in
                (state_fn, reject_fn, invoke_fn, canonical_fn, check_fn, full_guard, allocation_guard))
            canonical_anchor = state_fn(canonical_fn)
            callback_anchor = state_fn(allocation_guard)
            need(runtime_type is Runtime and runtime.state_function is state_fn
                 and runtime.state_code is state_code and runtime.reject is reject_fn
                 and runtime.reject_code is reject_code and runtime.clock is clock and runtime.usage is usage
                 and deadline == began + 20, 'unchanged actual Runtime and original absolute clock')
            runtime.check()

            def allocation_validate(index, recipe):
                # Every delegated encoding/property read has an immediate slice
                # before and after it. The factory separately authenticates its
                # original module/raw buffers, Recipe endpoints and ctor frame.
                for after_delegation in (False, True):
                    if function_state is not state_fn or state_fn.__code__ is not state_code:
                        raise ValueError('initializer original function-state endpoint changed')
                    if need is not reject_fn or reject_fn.__code__ is not reject_code:
                        raise ValueError('initializer original rejecting endpoint changed')
                    if invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code:
                        raise ValueError('initializer original invocation endpoint changed')
                    if time.perf_counter is not clock or resource.getrusage is not usage or resource.RUSAGE_SELF != usage_kind:
                        raise ValueError('initializer original clock/resource endpoint changed')
                    if types.FunctionType is not function_type or types.MethodType is not method_type:
                        raise ValueError('initializer original callable types changed')
                    if canonical is not canonical_fn or Runtime is not runtime_type:
                        raise ValueError('initializer original encoding/runtime endpoint changed')
                    for fn, signature in signature_anchors:
                        if state_fn(fn) != signature:
                            raise ValueError('initializer callback/helper code/default/closure changed')
                    effective_check = runtime.check
                    if (type(runtime) is not runtime_type or type(effective_check) is not method_type
                            or effective_check.__self__ is not runtime or effective_check.__func__ is not check_fn
                            or runtime.began != began or runtime.deadline != deadline
                            or runtime.guard is not full_guard or runtime.state_function is not state_fn
                            or runtime.state_code is not state_code or runtime.reject is not reject_fn
                            or runtime.reject_code is not reject_code or runtime.clock is not clock or runtime.usage is not usage):
                        raise ValueError('initializer effective Runtime or fixed authority changed')
                    if clock() - began >= 55 or usage(usage_kind).ru_maxrss >= 524288000:
                        raise Unresolved('original worker55/500 reserve exceeded during allocation')
                    if clock() >= deadline:
                        raise Unresolved('original shared20s unfinished during allocation')
                    if not after_delegation:
                        invoke_fn(allocation_guard, callback_anchor, index=index, recipe=recipe)

            allocation_validate_anchor = state_fn(allocation_validate)
            for index, record in enumerate(catalogue['recipes']):
                if index % 32 == 0:
                    runtime.check()
                recipe = graph.recipes[index]
                # These direct pregates precede every delegation to the private
                # validator; invoke also checks that validator before/after use.
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed before record')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                witness, premises = record['primitive_witness'], record['ordered_premise_formulas']
                need(witness['rule'] in RULES and record['id'] == recipe.identifier,
                     'all original licensed recipe identities')
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed before output encoding')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                output_text = invoke_fn(canonical_fn, canonical_anchor, witness['formula'])
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed after output encoding')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                ordered_input_codes = []
                for premise in premises:
                    if (function_state is not state_fn or state_fn.__code__ is not state_code
                            or need is not reject_fn or reject_fn.__code__ is not reject_code
                            or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                        raise ValueError('initializer own validator endpoints changed before premise encoding')
                    invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                    premise_text = invoke_fn(canonical_fn, canonical_anchor, premise)
                    if (function_state is not state_fn or state_fn.__code__ is not state_code
                            or need is not reject_fn or reject_fn.__code__ is not reject_code
                            or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                        raise ValueError('initializer own validator endpoints changed after premise encoding')
                    invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                    ordered_input_codes.append(codes[premise_text])
                primitive = (codes[output_text], tuple(ordered_input_codes))
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed before witness getter')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                decoded_witness = recipe.witness
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed after witness getter')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed before premises getter')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                decoded_premises = recipe.formulas
                if (function_state is not state_fn or state_fn.__code__ is not state_code
                        or need is not reject_fn or reject_fn.__code__ is not reject_code
                        or invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code):
                    raise ValueError('initializer own validator endpoints changed after premises getter')
                invoke_fn(allocation_validate, allocation_validate_anchor, index, recipe)
                need(primitive == (recipe.output, recipe.inputs)
                     and decoded_witness == witness and decoded_premises == premises,
                     'complete graph-to-admitted raw witness/interface correspondence')
                need(record['identity_preimage']['primitive_authority_epoch'] == graph.authority_epoch
                     and record['identity_preimage']['formula_registry_sha256'] == graph.registry_sha,
                     'whole fixed admitted recipe preimage scopes; full hash custody belongs to cold caller')
                primitives.append(primitive)
            # The remainder, including an empty inventory, must have a final
            # full authority check. No partially allocated prefix can escape.
            runtime.check()
        self.primitives = tuple(primitives)
        self.point_boundary = checker_module.Boundary(runtime.guard, runtime.deadline, LIMITS['maximum_visits'])
        self.counts = {'observations': 0, 'selected_target_roots': 0, 'pending_roots': 0,
                       'independent_words': 0, 'independent_point_states': 0, 'full_boards': 0}
        runtime.check()

    def _ancestry(self, root, by_row):
        essential, pending = set(), [root.row]
        while pending:
            self.runtime.check()
            row = pending.pop()
            if row in essential:
                continue
            key = by_row.get(row)
            if key is None:
                return None
            recipe = self.graph._recipe_key(key)
            for ref, code in zip(key.refs, recipe.inputs):
                self.runtime.check()
                source = by_row.get(ref)
                if source is None:
                    return None
                need(type(ref) is int and ref < row
                     and self.graph._recipe_key(source).output == code,
                     'selected strict-prior source has exact ordered required formula')
                pending.append(ref)
            essential.add(row)
        return [by_row[row] for row in sorted(essential)]

    def _commands(self, keys):
        mapping = {key.row: local for local, key in enumerate(keys)}
        need(len(mapping) == len(keys), 'one selected physical constituent per proof row')
        commands, physical = [], []
        for local, key in enumerate(keys):
            self.runtime.check()
            record = self.catalogue['recipes'][key.recipe]
            command = copy.deepcopy(record['primitive_witness'])
            if command['rule'] == 'mp':
                need(len(key.refs) == 2, 'two genuinely ordered MP inputs')
                command.update(antecedent=mapping[key.refs[0]], implication=mapping[key.refs[1]])
            elif command['rule'] == 'generalize':
                need(len(key.refs) == 1, 'true unary generalize, no dummy second port')
                command.update(source=mapping[key.refs[0]])
            else:
                need(not key.refs, 'zero-port primitive has no supplied inference premises')
            refs = [mapping[ref] for ref in key.refs]
            need(all(type(ref) is int and 0 <= ref < local for ref in refs), 'exact strict-prior rebased word')
            commands.append(command)
            t, m = self.graph.point_data(key)
            physical.append({'physical_row': key.row, 'local_row': local, 'key': key.data(),
                'recipe_id': record['id'], 'identity_preimage': record['identity_preimage'],
                'ordered_physical_prior_rows': list(key.refs), 'ordered_local_prior_rows': refs,
                'primitive_command': command, 't': t, 'm': m})
        return commands, physical

    def observe(self, *, decision, source_event):
        self.runtime.check()
        self.counts['observations'] += 1
        by_row = {key.row: key for key in self.graph.order}
        need(len(by_row) == len(self.graph.order), 'actual selected rows unique')
        target_roots = [by_row[row] for row in sorted(by_row)
                        if self.graph._recipe_key(by_row[row]).output == self.target_code]
        self.counts['selected_target_roots'] += len(target_roots)
        for root in target_roots:
            self.runtime.check()
            keys = self._ancestry(root, by_row)
            if keys is None:
                self.counts['pending_roots'] += 1
                continue
            commands, physical = self._commands(keys)
            state = self.graph.semantic_state()
            state_sha = complete_digest(state, self.runtime)
            need(state_sha == source_event['state_sha256'], 'proof is bound to whole actual decision snapshot')
            point = self.checker.check_point_state(state=state, catalogue=self.catalogue,
                primitives=self.primitives, epoch=self.graph.model_epoch, b=self.point_boundary)
            self.counts['independent_point_states'] += 1
            need(point['point_decision'] == decision and point['exact_saved_point_union_accepted'] is True,
                 'all24 domains/global decision/current fixed marking/refcount union independently checked')
            logical = self.checker.check_primitive_word(theory=self.declaration['theory'],
                parameters=self.declaration['parameters'], original_Gamma=self.declaration['ordered_Gamma'],
                commands=commands, target=self.declaration['target'], source_guard=self.runtime.guard,
                deadline=self.runtime.deadline, maximum_visits=LIMITS['maximum_visits'])
            self.counts['independent_words'] += 1
            need(logical['completed'] is True and logical['original_Gamma_target_sequent_accepted'] is True
                 and logical['essential_rows'] == list(range(len(commands))), 'only complete actual target ancestry')
            board = None
            if decision['kind'] == 'complete':
                all_keys = [by_row[row] for row in range(self.graph.height)]
                all_commands, all_physical = self._commands(all_keys)
                all_logical = self.checker.check_primitive_word(theory=self.declaration['theory'],
                    parameters=self.declaration['parameters'], original_Gamma=self.declaration['ordered_Gamma'],
                    commands=all_commands, target=self.declaration['target'], source_guard=self.runtime.guard,
                    deadline=self.runtime.deadline, maximum_visits=LIMITS['maximum_visits'])
                self.counts['independent_words'] += 1
                need(state['totals'] == [1] * self.graph.height and all_logical['completed'] is True,
                     'full24 independent point relation and all24 literal commands; no padding')
                board = {'schema': 'Q-current-full24-point-and-word-observable-v1', 'full24_accepted': True,
                    'point_check': point, 'whole24_word_check': all_logical, 'physical_rows': all_physical}
                self.counts['full_boards'] += 1
            certificate = {'schema': 'Q-first-actual-selected-original-Gamma-target-certificate-v1',
                'origin_kind': 'actual_selected', 'completed': True, 'original_Gamma_target_sequent_accepted': True,
                'current_state_point_union_accepted': True, 'full24_accepted': False,
                'physical_rows': physical, 'commands': commands, 'independent_word_check': logical,
                'independent_current_point_check': point, 'source_state': state, 'source_state_sha256': state_sha,
                'source_event': source_event, 'original_context_binding': self.binding,
                'actual_target_physical_row': root.row, 'selected_ancestry_physical_rows': [key.row for key in keys],
                'original_Gamma': self.declaration['ordered_Gamma'], 'closed_target': self.declaration['target'],
                'parameters': self.declaration['parameters'], 'theory': self.declaration['theory'],
                'native_accepted': False, 'full_trajectory_accepted': False, 'induction_accepted': False,
                'full_PA_accepted': False, 'ROOT_resource_accepted': False, 'RL_used': False}
            # Full traversal and final deadline precede the escaping primary.
            complete_digest(certificate, self.runtime)
            if board is not None:
                complete_digest(board, self.runtime)
            self.runtime.check()
            return certificate, board
        self.runtime.check()
        return None, None


def run_first_checked_Q(*, graph, observer, runtime, events):
    """Canonical all-base DFS, global scheduler after every state change.

    Only a returned EXHAUSTED child causes exclusion in its exact restored
    parent. FOUND/UNKNOWN/guard/clock/event/resource failures never do. Deliberate
    success still unwinds every ancestor transaction before an accepted return.
    Metric counters are cumulative work and intentionally do not roll back.
    """
    runtime.check()
    need(type(observer) is FirstSelectedProofObserver and observer.graph is graph
         and observer.runtime is runtime and type(events) is OwnedEvents and events.runtime is runtime,
         'exact cold-owned constructed endpoints; caller seals their effective methods/MRO')
    entry = graph.checkpoint()
    counters = {'attempts': 0, 'placements': 0, 'forced': 0, 'branch_decisions': 0,
                'backtracks': 0, 'exclusions': 0, 'nodes': 0, 'events': 0,
                'rollbacks': 0, 'observer_calls': 0}
    # These four declared outcomes change during normal recursion. Keep
    # the captured container identity stable; callback anchors still bind
    # every function/code/default and closure-cell/content identity.
    outcome_state = {'first_proof': None, 'full_board': None,
                     'restoration_failed': False, 'trace_complete': True}
    error = None
    local_anchors = {}

    def emit(kind, *, node, parent, depth, decision=None, key=None, outcome=None, cleanup=False):
        runtime.check(cleanup=cleanup)
        state = graph.semantic_state()
        state_sha = complete_digest(state, runtime, cleanup=cleanup)
        counters['events'] += 1
        event = {'schema': 'Q-full-point-state-search-event-v1', 'event': counters['events'] - 1,
            'kind': kind, 'node': node, 'parent': parent, 'depth': depth, 'decision': decision,
            'key': None if key is None else key.data(), 'outcome': outcome,
            'counters': dict(counters), 'graph_metrics': dict(graph.metrics),
            'state': state, 'state_sha256': state_sha, 'checkpoint': graph.checkpoint()}
        raw_pin = events.append(event, cleanup=cleanup)
        return {'event': event['event'], 'kind': kind, 'node': node, 'file': raw_pin, 'state_sha256': state_sha}

    def decision_data(value):
        return {'kind': value.kind, 'row': value.row, 'count': value.count, 'generation': value.generation}

    def place(key, decision, *, node, parent, depth):
        runtime.check()
        if counters['attempts'] >= LIMITS['max_attempts']:
            raise Unresolved('placement-attempt ceiling; no exhausted-child exclusion')
        current = graph.decision()
        need(invoke(decision_data, local_anchors['decision_data'], current) == decision and current.kind in ('forced', 'branch')
             and key.row == current.row and graph.legal(key), 'reference scheduler chose this legal base candidate')
        if current.kind == 'forced':
            candidates = iter(graph.candidates(current.row))
            only = next(candidates, None)
            need(only == key and next(candidates, None) is None, 'whole singleton candidate EOF')
        counters['attempts'] += 1
        graph._apply_legal(key)
        counters['placements'] += 1
        if current.kind == 'forced':
            counters['forced'] += 1
        runtime.check()
        invoke(emit, local_anchors['emit'], 'forced_place' if current.kind == 'forced' else 'branch_place',
             node=node, parent=parent, depth=depth, decision=decision, key=key)

    def walk(parent, depth):
        runtime.check()
        need(depth <= graph.height, 'finite occupancy bounds actual recursion depth')
        node = counters['nodes']
        counters['nodes'] += 1
        checkpoint = graph.checkpoint()
        witness = invoke(emit, local_anchors['emit'], 'node_enter', node=node, parent=parent, depth=depth)
        outcome = 'UNKNOWN'
        try:
            while True:
                runtime.check()
                decision = invoke(decision_data, local_anchors['decision_data'], graph.decision())
                source_event = invoke(emit, local_anchors['emit'], 'decision', node=node, parent=parent, depth=depth, decision=decision)
                # Known global dead is never hidden by a target mark/prefix.
                if decision['kind'] == 'dead':
                    outcome = 'EXHAUSTED'
                    invoke(emit, local_anchors['emit'], 'dead', node=node, parent=parent, depth=depth, decision=decision, outcome=outcome)
                    return outcome
                counters['observer_calls'] += 1
                candidate, board = observer.observe(decision=decision, source_event=source_event)
                runtime.check()
                if candidate is not None:
                    outcome_state['first_proof'], outcome_state['full_board'] = candidate, board
                    outcome = 'FOUND'
                    invoke(emit, local_anchors['emit'], 'deliberate_checked_proof_stop', node=node, parent=parent, depth=depth,
                         decision=decision, outcome=outcome)
                    return outcome
                if decision['kind'] == 'complete':
                    raise ValueError('complete board must decode independently checked original target before return')
                iterator = iter(graph.candidates(decision['row']))
                key = next(iterator, None)
                runtime.check()
                need(key is not None, 'positive complete domain has its canonical first candidate')
                if decision['kind'] == 'forced':
                    invoke(place, local_anchors['place'], key, decision, node=node, parent=parent, depth=depth)
                    continue
                need(decision['kind'] == 'branch', 'only earliest-generation branch remains')
                counters['branch_decisions'] += 1
                parent_checkpoint = graph.checkpoint()
                parent_witness = invoke(emit, local_anchors['emit'], 'branch_checkpoint', node=node, parent=parent, depth=depth,
                                      decision=decision, key=key)
                invoke(place, local_anchors['place'], key, decision, node=node, parent=parent, depth=depth)
                child_outcome = invoke(walk, local_anchors['walk'], node, depth + 1)
                runtime.check()
                # Child returned after its own rollback but preserves this
                # branch placement; restore exactly before exclusion/return.
                graph.rollback(parent_checkpoint)
                counters['rollbacks'] += 1
                restored = invoke(emit, local_anchors['emit'], 'child_rollback', node=node, parent=parent, depth=depth,
                                decision=decision, key=key, outcome=child_outcome)
                need(restored['state_sha256'] == parent_witness['state_sha256'], 'complete parent rollback equality')
                if child_outcome != 'EXHAUSTED':
                    outcome = child_outcome
                    return outcome
                counters['backtracks'] += 1
                graph.exclude_failed_child(key)
                counters['exclusions'] += 1
                invoke(emit, local_anchors['emit'], 'justified_parent_local_exclusion', node=node, parent=parent, depth=depth,
                     key=key, outcome='EXHAUSTED_CHILD_ONLY')
                # Return to complete global dead/forced/generation checks, not
                # a stale preferred iterator or minimum-count-only choice.
        finally:
            cleanup = runtime.clock() >= runtime.deadline
            try:
                runtime.check(cleanup=cleanup)
                graph.rollback(checkpoint)
                counters['rollbacks'] += 1
                restored = invoke(emit, local_anchors['emit'], 'node_unwind', node=node, parent=parent, depth=depth,
                                outcome=outcome, cleanup=cleanup)
                need(restored['state_sha256'] == witness['state_sha256'], 'complete node-entry rollback equality')
            except BaseException:
                outcome_state['restoration_failed'] = True
                outcome_state['trace_complete'] = False
                raise

    local_anchors.update({name: function_state(function) for name, function in
                         [('emit', emit), ('decision_data', decision_data), ('place', place), ('walk', walk)]})
    entry_witness = invoke(emit, local_anchors['emit'], 'run_entry', node=None, parent=None, depth=0)
    try:
        status = invoke(walk, local_anchors['walk'], None, 0)
        runtime.check()
    except BaseException as failure:
        status = 'UNKNOWN'
        error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
        outcome_state['first_proof'] = outcome_state['full_board'] = None
    finally:
        cleanup = runtime.clock() >= runtime.deadline
        try:
            runtime.check(cleanup=cleanup)
            graph.rollback(entry)
            counters['rollbacks'] += 1
            final = invoke(emit, local_anchors['emit'], 'run_restored', node=None, parent=None, depth=0, outcome=status, cleanup=cleanup)
            need(final['state_sha256'] == entry_witness['state_sha256'], 'complete run-entry restoration')
        except BaseException as failure:
            outcome_state['restoration_failed'] = True
            outcome_state['trace_complete'] = False
            status = 'UNKNOWN'
            outcome_state['first_proof'] = outcome_state['full_board'] = None
            error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    result = {'schema': 'Q-first-selected-proof-baseline-return-v1', 'version': VERSION,
        'status': 'first_checked_actual_selected_original_Gamma_target_proof' if status == 'FOUND' else (
            'exhausted_complete_finite_board_subtree_only' if status == 'EXHAUSTED' else 'UNKNOWN'),
        'first_checked_proof': outcome_state['first_proof'], 'full24_observable': outcome_state['full_board'],
        'selected_target_proof_accepted': status == 'FOUND', 'full24_accepted': outcome_state['full_board'] is not None,
        'event_files': list(events.pins), 'partial_event_files': list(events.partial),
        'serialization_records': list(events.serialization), 'complete_event_trace': outcome_state['trace_complete'] and events.complete,
        'complete_entry_rollback': not outcome_state['restoration_failed'], 'counters': dict(counters),
        'graph_metrics': dict(graph.metrics), 'observer_counters': dict(observer.counts), 'error': error,
        'original_model_epoch': graph.model_epoch, 'original_context_binding': observer.binding,
        'native_accepted': False, 'full_trajectory_accepted': False, 'induction_accepted': False,
        'full_PA_accepted': False, 'ROOT_resource_accepted': False, 'RL_used': False,
        'proposed_proofs': 0, 'library_used': False, 'rank_used': False,
        'cost_scope': 'All setup/search/checking/full successful event/proof traversal and rollback must fit original20s. Failure-only restoration/metadata may use remaining55/500 worker reserve, charged inside60/512 owner; no new search/checker work or reset.'}
    try:
        complete_digest(result, runtime, cleanup=status == 'UNKNOWN')
        runtime.check(cleanup=status == 'UNKNOWN')
    except BaseException as failure:
        result['status'] = 'UNKNOWN'
        result['first_checked_proof'] = None
        result['full24_observable'] = None
        result['selected_target_proof_accepted'] = result['full24_accepted'] = False
        result['error'] = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
        # Cold worker must perform the remaining guard/output/receipt clock;
        # this returned value cannot issue a successful external stage latch.
    return result
