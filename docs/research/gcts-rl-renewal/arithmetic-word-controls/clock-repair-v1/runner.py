"""UNEXECUTED neutral controls callable. No Q theorem word is authored here.

The exact twenty unrelated words can use the original independent checker API.
Hard-target protocol, actual point/scheduler and process/full-data surfaces need
separately Source-reviewed cold adapters. Missing adapters produce explicit
not_exercised rows, never a whole-architecture pass. This is not a cold worker,
coordinator admission, mathematical authority or a compiled Wang board.
"""
import copy
import hashlib
import json
import math
import resource
import time
import types

VERSION = 'Q-split-neutral-controls-callable-v3-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
FIXTURE_SHA256 = '1420cd2c0a56d09e629ca65fe4b7f690570ccb283b1998762c10de1190180575'
FIXTURE_BYTES = 62584
CHECKER_RECORD = {'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3', 'bytes': 46514}
EXPECTED_COUNTS = (20, 16, 8, 8)
GROUPS = ('kernel_words', 'protocol_cases', 'point_and_scheduler_NONLOGICAL_cases', 'owned_role_and_deadline_cases')
SUCCESS_NS = 20000000000
FAILURE_NS = 55000000000
WORKER_GUIDANCE_BYTES = 524288000
VISIT_CEILING = 5000000


class Unresolved(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def function_state(function):
    require(type(function) is types.FunctionType, 'declared exact Python function endpoint')
    return (function, function.__code__, function.__defaults__, function.__kwdefaults__,
            tuple((cell, cell.cell_contents) for cell in function.__closure__ or ()))


def same_function(function, state):
    # Identity comparisons, including closure contents, do not invoke data equality.
    return (function is state[0] and function.__code__ is state[1]
            and function.__defaults__ is state[2] and function.__kwdefaults__ is state[3]
            and len(function.__closure__ or ()) == len(state[4])
            and all(cell is old and cell.cell_contents is value
                    for cell, (old, value) in zip(function.__closure__ or (), state[4])))


def project_local_float_deadline(global_deadline_ns, *, producer_pair=False,
        _global_clock=time.clock_gettime_ns, _clock_id=time.CLOCK_MONOTONIC,
        _local_clock=time.perf_counter, _nextafter=math.nextafter,
        _finite=math.isfinite, _ratio=float.as_integer_ratio,
        _negative_infinity=-math.inf):
    """Legacy local guidance only; global pre/post/output/terminal gates rule.

    Sample local perf BEFORE global; lower the sample and the rational deadline.
    The exact numeric bound at that sample makes no future rate/suspend claim.
    No callback, new clock epoch, renewal, producer acceptance or shared float.
    """
    if (type(global_deadline_ns) is not int or not 0 <= global_deadline_ns < (1 << 63)
            or type(producer_pair) is not bool or type(_clock_id) is not int
            or time.clock_gettime_ns is not _global_clock or time.CLOCK_MONOTONIC is not _clock_id
            or time.perf_counter is not _local_clock or math.nextafter is not _nextafter
            or math.isfinite is not _finite or float.as_integer_ratio is not _ratio
            or type(_global_clock) is not types.BuiltinFunctionType
            or type(_local_clock) is not types.BuiltinFunctionType):
        raise ValueError('original native projection endpoints/domain changed')
    local_before = _local_clock()
    global_after = _global_clock(_clock_id)
    if (time.clock_gettime_ns is not _global_clock or time.CLOCK_MONOTONIC is not _clock_id
            or time.perf_counter is not _local_clock or math.nextafter is not _nextafter
            or math.isfinite is not _finite or float.as_integer_ratio is not _ratio):
        raise ValueError('projection native endpoints changed during sampling')
    if (type(local_before) is not float or not _finite(local_before)
            or type(global_after) is not int or not 0 <= global_after < (1 << 63)):
        raise TimeoutError('unrepresentable local/global projection sample; UNKNOWN')
    remaining_ns = global_deadline_ns - global_after
    if not 0 < remaining_ns <= 20000000000:
        raise TimeoutError('expired or foreign original joint20 projection; UNKNOWN')
    local_lower = _nextafter(local_before, _negative_infinity)
    if not _finite(local_lower):
        raise TimeoutError('no finite downward local sample; UNKNOWN')
    numerator, denominator = _ratio(local_lower)
    bound_numerator = numerator * 1000000000 + remaining_ns * denominator
    bound_denominator = denominator * 1000000000
    # Integer division produces one rounded float; verify its exact ratio and
    # move downward once if needed. Failure is UNKNOWN, never a larger deadline.
    local_deadline = bound_numerator / bound_denominator
    if not _finite(local_deadline):
        raise TimeoutError('no finite local deadline; UNKNOWN')
    deadline_numerator, deadline_denominator = _ratio(local_deadline)
    if deadline_numerator * bound_denominator > bound_numerator * deadline_denominator:
        local_deadline = _nextafter(local_deadline, _negative_infinity)
    local_began = None
    if producer_pair:
        # Original producer2 requires this exact float expression. The synthetic
        # local origin is not the global begin and carries no resource authority.
        local_began = local_deadline - 20.0
        local_deadline = local_began + 20.0
        if not _finite(local_began) or not _finite(local_deadline):
            raise TimeoutError('no finite producer local pair; UNKNOWN')
        deadline_numerator, deadline_denominator = _ratio(local_deadline)
        if deadline_numerator * bound_denominator > bound_numerator * deadline_denominator:
            local_began = _nextafter(local_began, _negative_infinity)
            local_deadline = local_began + 20.0
    if not _finite(local_deadline) or (producer_pair and not _finite(local_began)):
        raise TimeoutError('unrepresentable downward local pair; UNKNOWN')
    deadline_numerator, deadline_denominator = _ratio(local_deadline)
    if (deadline_numerator * bound_denominator > bound_numerator * deadline_denominator
            or local_deadline <= local_before
            or (producer_pair and local_deadline != local_began + 20.0)):
        raise TimeoutError('exact local float bound/pair unavailable; UNKNOWN')
    if (time.clock_gettime_ns is not _global_clock or time.CLOCK_MONOTONIC is not _clock_id
            or time.perf_counter is not _local_clock or math.nextafter is not _nextafter
            or math.isfinite is not _finite or float.as_integer_ratio is not _ratio):
        raise ValueError('projection endpoints changed before final global gate')
    final_global = _global_clock(_clock_id)
    if (time.clock_gettime_ns is not _global_clock or time.CLOCK_MONOTONIC is not _clock_id
            or time.perf_counter is not _local_clock or math.nextafter is not _nextafter
            or math.isfinite is not _finite or float.as_integer_ratio is not _ratio):
        raise ValueError('projection endpoints changed at final global gate')
    if (type(final_global) is not int or final_global < global_after
            or final_global >= global_deadline_ns):
        raise TimeoutError('projection not complete in original global joint20; UNKNOWN')
    return local_began, local_deadline


class Boundary:
    """Anchors ordinary synchronous callable mutations; no async/hostile VM claim.

    Cold caller must first raw-compile exact Sources and seal full original module
    globals/class/MRO/effective objects/builtins. This local gate complements that
    caller; a function's filename or a claimed digest is never sufficient custody.
    """
    __slots__ = ('_guard', '_guard_state', '_clock', '_clock_id', '_local_clock', '_usage', '_native_type',
                 '_function_state', '_same_function', '_own_states', '_check_function', '_check_state',
                 '_began_ns', '_deadline_ns', '_sealed')

    def __init__(self, source_guard, joint_began_ns, joint_deadline_ns):
        require(type(joint_began_ns) is int and type(joint_deadline_ns) is int
                and 0 <= joint_began_ns < joint_deadline_ns <= (1 << 63) - 1
                and joint_deadline_ns - joint_began_ns == SUCCESS_NS, 'original exact native joint20 interval')
        object.__setattr__(self, '_guard', source_guard)
        object.__setattr__(self, '_guard_state', function_state(source_guard))
        object.__setattr__(self, '_clock', time.clock_gettime_ns)
        object.__setattr__(self, '_clock_id', time.CLOCK_MONOTONIC)
        object.__setattr__(self, '_local_clock', time.perf_counter)
        require(type(self._clock_id) is int and type(self._clock) is types.BuiltinFunctionType
                and type(self._local_clock) is types.BuiltinFunctionType, 'original native global/local clocks')
        object.__setattr__(self, '_usage', resource.getrusage)
        object.__setattr__(self, '_native_type', type)
        object.__setattr__(self, '_function_state', function_state)
        object.__setattr__(self, '_same_function', same_function)
        owned = (require, canonical, digest, function_state, same_function, project_local_float_deadline, decode_fixtures,
                 kernel_record, protocol_request, evaluate_adapter, run_split_neutral_controls,
                 Boundary.__init__, Boundary.__setattr__, Boundary.check, Boundary.invoke)
        object.__setattr__(self, '_own_states', tuple((function, function_state(function)) for function in owned))
        object.__setattr__(self, '_check_function', Boundary.check)
        object.__setattr__(self, '_check_state', function_state(Boundary.check))
        object.__setattr__(self, '_began_ns', joint_began_ns)
        object.__setattr__(self, '_deadline_ns', joint_deadline_ns)
        object.__setattr__(self, '_sealed', True)
        if Boundary.check is not self._check_function or Boundary.check.__code__ is not self._check_state[1]:
            raise ValueError('original constructor final Boundary endpoint changed')
        self._check_function(self)

    def __setattr__(self, name, value):
        raise AttributeError('neutral controls Boundary is sealed')

    def check(self, *, cleanup=False):
        # Direct original helper/code checks BEFORE any helper/callback authority.
        if (function_state is not self._function_state or same_function is not self._same_function
                or Boundary.check is not self._check_function
                or type is not self._native_type or time.clock_gettime_ns is not self._clock
                or time.CLOCK_MONOTONIC is not self._clock_id or type(self._clock_id) is not int
                or time.perf_counter is not self._local_clock
                or resource.getrusage is not self._usage):
            raise ValueError('original local validators/native endpoints changed')
        for function, state in self._own_states:
            if function.__code__ is not state[1] or function.__defaults__ is not state[2] or function.__kwdefaults__ is not state[3]:
                raise ValueError('original own function/code/default endpoint changed')
        if not self._same_function(self._guard, self._guard_state):
            raise ValueError('actual delegated Source guard changed')
        now = self._clock(self._clock_id)
        if type(now) is not int or now < self._began_ns:
            raise Unresolved('foreign/future global CLOCK_MONOTONIC epoch')
        if now - self._began_ns >= FAILURE_NS or self._usage(resource.RUSAGE_SELF).ru_maxrss >= WORKER_GUIDANCE_BYTES:
            raise Unresolved('original failure55/500 guidance exceeded')
        if not cleanup and now >= self._deadline_ns:
            raise Unresolved('original joint20 expired')
        guard = self._guard
        guard()
        # Repeat direct identities before returning to any caller after delegation.
        if (function_state is not self._function_state or same_function is not self._same_function
                or Boundary.check is not self._check_function or type is not self._native_type
                or time.clock_gettime_ns is not self._clock
                or time.CLOCK_MONOTONIC is not self._clock_id or type(self._clock_id) is not int
                or time.perf_counter is not self._local_clock or resource.getrusage is not self._usage):
            raise ValueError('original local validators/native endpoints changed after Source guard')
        for function, state in self._own_states:
            if function.__code__ is not state[1] or function.__defaults__ is not state[2] or function.__kwdefaults__ is not state[3]:
                raise ValueError('own endpoint changed after Source guard')
        if not self._same_function(self._guard, self._guard_state):
            raise ValueError('actual Source guard changed during delegation')
        now = self._clock(self._clock_id)
        if type(now) is not int or now < self._began_ns:
            raise Unresolved('foreign/future global CLOCK_MONOTONIC epoch')
        if now - self._began_ns >= FAILURE_NS or self._usage(resource.RUSAGE_SELF).ru_maxrss >= WORKER_GUIDANCE_BYTES:
            raise Unresolved('complete guarded boundary exceeded failure limits')
        if not cleanup and now >= self._deadline_ns:
            raise Unresolved('complete guarded boundary exceeded joint20')

    def invoke(self, endpoint, endpoint_state, *, keyword_arguments, counters):
        if (Boundary.check is not self._check_function or Boundary.check.__code__ is not self._check_state[1]
                or Boundary.check.__defaults__ is not self._check_state[2] or Boundary.check.__kwdefaults__ is not self._check_state[3]):
            raise ValueError('original invoke precheck endpoint changed')
        self._check_function(self)
        if not self._same_function(endpoint, endpoint_state):
            raise ValueError('actual delegated endpoint state changed before call')
        require(type(counters) is dict and set(counters) == {'started', 'returned', 'exceptions', 'expected_logical_rejections'}, 'literal own API census')
        error, result = None, None
        counters['started'] += 1
        try:
            result = endpoint(**keyword_arguments)
        except BaseException as failure:
            counters['exceptions'] += 1
            error = failure
        else:
            counters['returned'] += 1
        if (Boundary.check is not self._check_function or Boundary.check.__code__ is not self._check_state[1]
                or Boundary.check.__defaults__ is not self._check_state[2] or Boundary.check.__kwdefaults__ is not self._check_state[3]):
            raise ValueError('original invoke postcheck endpoint changed')
        self._check_function(self)
        if not self._same_function(endpoint, endpoint_state):
            raise ValueError('actual delegated endpoint changed before result observation')
        # Only a ValueError from inside the intact delegated endpoint is exposed
        # as a possible expected rejection; own boundary failures never become it.
        if error is not None and not isinstance(error, ValueError):
            raise error
        return {'returned': error is None, 'result': result, 'endpoint_ValueError': error}


def decode_fixtures(raw):
    require(type(raw) is bytes and len(raw) == FIXTURE_BYTES
            and hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, 'entire frozen52-case fixture bytes, no subset')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate frozen fixture key')
            result[key] = value
        return result
    def reject(token):
        raise ValueError('nonfinite fixture token: ' + token)
    value = json.loads(raw.decode('utf8'), object_pairs_hook=unique, parse_constant=reject)
    require(value['schema'] == 'Q-split-architecture-neutral-control-fixtures-design-v1'
            and value['case_count'] == 52 and value['actual_results'] is None
            and value['actual_calls'] == 0 and value['authored_original_Q_proof_routes'] == 0,
            'exact original authored neutral fixture declaration')
    require(tuple(len(value[name]) for name in GROUPS) == EXPECTED_COUNTS, 'complete20/16/8/8 arrays')
    ids = [case['id'] for name in GROUPS for case in value[name]]
    require(len(set(ids)) == 52, 'all distinct complete fixture IDs')
    return value


def kernel_record(case, certificate):
    wire = case['complete_wire']
    require(type(certificate) is dict and certificate['schema'] == 'independent-Q-primitive-word-certificate-v1'
            and certificate['completed'] is True and certificate['original_Gamma_target_sequent_accepted'] is True,
            'complete primitive word certificate, never attempted ports')
    require(canonical(certificate['original_ordered_Gamma']) == canonical(wire['original_Gamma'])
            and canonical(certificate['parameters']) == canonical(wire['parameters'])
            and canonical(certificate['target']) == canonical(wire['target'])
            and certificate['theory_sha256'] == digest(wire['theory'])
            and certificate['commands_sha256'] == digest(wire['commands']), 'exact unrelated full context/word/target')
    require(len(certificate['rows']) == len(wire['commands']), 'complete checked rows')
    expected = case['expected']
    require(certificate['consumed_original_occurrence_indices'] == expected['consumed_original_occurrence_indices']
            and [row['ordered_prior_rows'] for row in certificate['rows']] == expected['ordered_prior_rows'],
            'original occurrence consumption distinct from preserved Gamma and ordered ports')
    for row, entry in enumerate(certificate['rows']):
        require(type(entry['row']) is int and entry['row'] == row
                and entry['rule'] == wire['commands'][row]['rule']
                and all(type(reference) is int and 0 <= reference < row for reference in entry['ordered_prior_rows']),
                'complete exact strict-prior row receipt')
    for field in ('native_accepted', 'full24_accepted', 'current_state_point_union_accepted', 'full_trajectory_accepted',
                  'induction_accepted', 'full_PA_accepted', 'universal_compiler_accepted', 'ROOT_resource_accepted'):
        require(certificate[field] is False, 'unearned inherited authority flag remains false')
    return certificate


def protocol_request(case, baseline, authority_raw, invocation_id):
    """Literal bytes only. Adapter must run genuine fixed-target CLI and own EOF.

    This caller-owned authority is not taken from fixtures or a candidate. The
    only baseline command is the intentionally undeclared CONTROL_UNDECLARED.
    Authority perturbations here exist only in isolated rejection controls.
    """
    require(type(authority_raw) is bytes and len(authority_raw) <= 1048576, 'small complete coordinator-owned authority')
    require(type(invocation_id) is str and 1 <= len(invocation_id) <= 128
            and all(char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for char in invocation_id),
            'Root-owned ASCII opaque invocation')
    candidate = copy.deepcopy(baseline)
    candidate['coordinator_invocation_id'] = invocation_id
    candidate['authority_sha256'] = hashlib.sha256(authority_raw).hexdigest()
    prefix = case['id'].split('-')[0]
    intervention = case.get('intervention')
    authority_edit = None
    if prefix in ('W07', 'W09', 'W12'):
        path = intervention['path']
        parent = candidate
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = intervention['value']
    elif prefix == 'W11':
        candidate.update(intervention['extra_fields'])
    elif prefix in ('W10', 'W13'):
        authority_edit = copy.deepcopy(intervention)
    raw = canonical(candidate).encode('utf8')
    if prefix == 'W02':
        raw = b'{"schema":"Q-untrusted-first-candidate-word-v1",' + raw[1:]
    elif prefix == 'W03':
        raw = raw[:-1]
    elif prefix in ('W04', 'W05', 'W06'):
        raw += intervention['suffix_utf8'].encode('utf8')
    elif prefix == 'W08':
        require(raw.count(b'"submission_index":0') == 1, 'exact literal zero token replacement')
        raw = raw.replace(b'"submission_index":0', b'"submission_index":0.0', 1)
    actual_sha = hashlib.sha256(raw).hexdigest()
    expected_sha = intervention['value'] if prefix == 'W14' else actual_sha
    return {'case_id': case['id'], 'candidate_raw': raw, 'candidate_sha256': expected_sha,
            'candidate_bytes': len(raw), 'unperturbed_authority_raw': authority_raw,
            'authority_edit_control_only': authority_edit,
            'transport_intervention_control_only': copy.deepcopy(intervention) if prefix in ('W15', 'W16') else None,
            'authority_is_Root_owned': True, 'expected_Q_primary_acceptance': False}


def evaluate_adapter(case, surface, response):
    """Interpret an explicit reviewed adapter receipt, not arbitrary truthy output."""
    require(type(response) is dict and response['schema'] == 'Q-split-neutral-surface-observation-v1'
            and response['case_id'] == case['id'] and response['surface'] == surface,
            'exact current complete adapter observation')
    require(type(response['completed']) is bool and type(response['observed_predicate']) is bool
            and response['expected_source'] == 'frozen-neutral-fixture'
            and type(response['evidence']) is dict and response['evidence'], 'literal expected oracle and saved complete evidence')
    for field in ('original_Q_theorem_accepted', 'selected_accepted', 'point_union_accepted', 'full24_accepted',
                  'trajectory_accepted', 'ROOT_resource_accepted', 'RL_accepted'):
        require(response[field] is False, 'mechanics receipt has no mathematical/resource authority')
    # Positive protocol baseline is a rejected word; transport acceptance cannot be
    # mistaken for original-target acceptance. The adapter must retain full bytes,
    # actual child result and EOF/terminal observations, not only a pass Boolean.
    if surface == 'hard-target-protocol':
        require(response['evidence'].get('primary_acceptance') is False, 'no supplied original Q proof')
        if case['id'].startswith(('W01-', 'W05-')):
            require(response['evidence'].get('verifier_status') == 'WORD_REJECTED', 'typed baseline exact word rejection')
    return response['completed'] and response['observed_predicate'], response


def run_split_neutral_controls(*, complete_fixtures_raw, checker_module, checker_source_raw,
                              source_guard, joint_began_ns, joint_deadline_ns,
                              adapter_bindings=None, authority_raw=None, invocation_id=None):
    """Run the full declared inventory; retain pending surfaces rather than trim.

    adapter_bindings is a trusted cold-caller object, NEVER candidate JSON. Each
    supplied entry must have exactly endpoint, authenticated_source_raw,
    reviewed_source_record, genuine_typed_review. Current V1 ships no adapters.
    Future independent reviews must own the full surface receipt interpretation;
    claimed pins/filename alone do not authenticate a passed callable.
    """
    boundary = Boundary(source_guard, joint_began_ns, joint_deadline_ns)
    boundary_check = Boundary.check
    boundary_check_state = function_state(boundary_check)
    invoke_fn, invoke_state = Boundary.invoke, function_state(Boundary.invoke)
    def guard():
        if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                or boundary_check.__defaults__ is not boundary_check_state[2]
                or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
            raise ValueError('actual nested checker guard endpoint changed')
        boundary_check(boundary)
        if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                or boundary_check.__defaults__ is not boundary_check_state[2]
                or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
            raise ValueError('checker guard endpoint changed during call')
    guard_state = function_state(guard)
    require(type(checker_source_raw) is bytes and len(checker_source_raw) == CHECKER_RECORD['bytes']
            and hashlib.sha256(checker_source_raw).hexdigest() == CHECKER_RECORD['sha256'], 'whole exact independent checker raw Source')
    # Full cold-loader code/class/effective-instance verification is delegated to
    # the already anchored original Source guard. No digest attribute is authority.
    require(type(checker_module) is types.ModuleType, 'actual cold-loaded independent checker module')
    endpoint = checker_module.check_primitive_word
    endpoint_state = function_state(endpoint)
    checker_unresolved = checker_module.Unresolved
    fixtures = decode_fixtures(complete_fixtures_raw)
    bindings = {} if adapter_bindings is None else adapter_bindings
    require(type(bindings) is dict and set(bindings) <= {'hard-target-protocol', 'NONLOGICAL-point-scheduler', 'owned-model-role-deadline'}, 'only declared prospective surfaces')
    prepared = {}
    for surface, binding in bindings.items():
        require(type(binding) is dict and set(binding) == {'endpoint', 'authenticated_source_raw', 'reviewed_source_record', 'genuine_typed_review'}, 'complete trusted cold adapter binding')
        raw, record, review = binding['authenticated_source_raw'], binding['reviewed_source_record'], binding['genuine_typed_review']
        require(type(raw) is bytes and type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}
                and type(record['bytes']) is int and len(raw) == record['bytes']
                and hashlib.sha256(raw).hexdigest() == record['sha256'], 'same-buffer adapter source custody')
        require(type(review) is dict and review['source'] == record and review['source_only'] is True
                and review['source_review_passed'] is True
                and review['scope'] == 'Q-split-neutral-' + surface + '-adapter-Source'
                and type(review['source_contract']) is dict and set(review['source_contract']) == {'path', 'sha256', 'bytes'}
                and type(review['scientific_calls']) is int
                and review['scientific_calls'] == 0 and review['author_identity'] != review['reviewer_identity'], 'genuine current distinct-author adapter review')
        prepared[surface] = (binding['endpoint'], function_state(binding['endpoint']), record)
    records, calls = [], {'started': 0, 'returned': 0, 'exceptions': 0, 'expected_logical_rejections': 0}
    unfinished = None
    for group in GROUPS:
        for case in fixtures[group]:
            surface = {'kernel_words': 'unrelated-primitive-word-API', 'protocol_cases': 'hard-target-protocol',
                       'point_and_scheduler_NONLOGICAL_cases': 'NONLOGICAL-point-scheduler',
                       'owned_role_and_deadline_cases': 'owned-model-role-deadline'}[group]
            row = {'id': case['id'], 'surface': surface, 'input_sha256': digest(case), 'expected': copy.deepcopy(case['expected']),
                   'actual_status': 'not_exercised', 'started': False, 'returned': False, 'exception': None,
                   'complete_output': None, 'elapsed_ns': None, 'exercised_scope': [], 'deferred_scope': []}
            # W16 cannot pass under this same original joint20: an actual late
            # terminal/EOF must fail its immediate postboundary. Do not delegate
            # it to an adapter or fabricate a toy/reset clock/successful record.
            if group == 'protocol_cases' and case['id'] == 'W16-late-exit-or-held-EOF':
                row['deferred_scope'] = [
                    'separate future actual expected-UNKNOWN late-gate run required',
                    'original joint20/failure55/owned60/aggregate512/caller90+1; no clock reset',
                    'late full bytes/EOF/terminal evidence is not successful suite completion or admission']
                records.append(row)
                continue
            if unfinished is not None:
                row['actual_status'] = 'UNKNOWN_unfinished'
                row['deferred_scope'] = ['prior Source/deadline/control failure; inventory not truncated']
                records.append(row)
                continue
            if group != 'kernel_words' and surface not in prepared:
                row['deferred_scope'] = ['genuine current cold surface adapter absent; Source specification only']
                records.append(row)
                continue
            began = boundary._clock(boundary._clock_id)
            previous_starts, previous_returns = calls['started'], calls['returned']
            try:
                if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                        or boundary_check.__defaults__ is not boundary_check_state[2]
                        or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
                    raise ValueError('actual outer boundary endpoint changed')
                boundary_check(boundary)
                if not same_function(guard, guard_state):
                    raise ValueError('actual passed checker guard changed before delegation')
                if group == 'kernel_words':
                    wire = copy.deepcopy(case['complete_wire'])
                    _, local_deadline = project_local_float_deadline(joint_deadline_ns)
                    if (Boundary.invoke is not invoke_fn or invoke_fn.__code__ is not invoke_state[1]
                            or invoke_fn.__defaults__ is not invoke_state[2] or invoke_fn.__kwdefaults__ is not invoke_state[3]):
                        raise ValueError('actual kernel invocation shim changed before delegation')
                    invocation = invoke_fn(boundary, endpoint, endpoint_state, keyword_arguments=dict(wire,
                        source_guard=guard, deadline=local_deadline, maximum_visits=VISIT_CEILING), counters=calls)
                    if (Boundary.invoke is not invoke_fn or invoke_fn.__code__ is not invoke_state[1]
                            or invoke_fn.__defaults__ is not invoke_state[2] or invoke_fn.__kwdefaults__ is not invoke_state[3]):
                        raise ValueError('actual kernel invocation shim changed during delegation')
                    if not invocation['returned']:
                        error = invocation['endpoint_ValueError']
                        row['exception'] = {'type': type(error).__name__, 'message': str(error)[:2048]}
                        if case['expected']['status'] != 'reject':
                            row['actual_status'] = 'fail'
                        else:
                            row['actual_status'] = 'pass_expected_reject'
                            calls['expected_logical_rejections'] += 1
                    else:
                        certificate = invocation['result']
                        row['returned'] = True
                        row['complete_output'] = certificate
                        if case['expected']['status'] != 'accept':
                            row['actual_status'] = 'fail'
                        else:
                            kernel_record(case, certificate)
                            row['actual_status'] = 'pass_expected_accept'
                    row['exercised_scope'] = ['authored unrelated logical word only; exact original context and strict-prior ports']
                else:
                    adapter, adapter_state, record = prepared[surface]
                    request = protocol_request(case, fixtures['protocol_rejection_baseline'], authority_raw, invocation_id) if group == 'protocol_cases' else copy.deepcopy(case)
                    if (Boundary.invoke is not invoke_fn or invoke_fn.__code__ is not invoke_state[1]
                            or invoke_fn.__defaults__ is not invoke_state[2] or invoke_fn.__kwdefaults__ is not invoke_state[3]):
                        raise ValueError('actual adapter invocation shim changed before delegation')
                    invocation = invoke_fn(boundary, adapter, adapter_state, keyword_arguments={'request': request,
                        'literal_expected': copy.deepcopy(case['expected']), 'joint_began_ns': joint_began_ns,
                        'joint_deadline_ns': joint_deadline_ns, 'source_guard': guard}, counters=calls)
                    if (Boundary.invoke is not invoke_fn or invoke_fn.__code__ is not invoke_state[1]
                            or invoke_fn.__defaults__ is not invoke_state[2] or invoke_fn.__kwdefaults__ is not invoke_state[3]):
                        raise ValueError('actual adapter invocation shim changed during delegation')
                    if not invocation['returned']:
                        raise invocation['endpoint_ValueError']
                    response = invocation['result']
                    row['returned'] = True
                    passed, observation = evaluate_adapter(case, surface, response)
                    row['complete_output'] = observation
                    row['adapter_source'] = record
                    row['actual_status'] = 'pass_expected_reject' if passed and group == 'protocol_cases' else ('pass_expected_accept' if passed else 'fail')
                    row['exercised_scope'] = ['only exact reviewed surface adapter/current full evidence']
                if not same_function(guard, guard_state):
                    raise ValueError('actual passed guard changed during endpoint')
                if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                        or boundary_check.__defaults__ is not boundary_check_state[2]
                        or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
                    raise ValueError('actual outer boundary endpoint changed')
                boundary_check(boundary)
                row['elapsed_ns'] = boundary._clock(boundary._clock_id) - began
                if row['actual_status'] == 'fail':
                    unfinished = 'literal expected predicate did not match observed complete record'
            except (Unresolved, TimeoutError) as error:
                unfinished = type(error).__name__ + ': ' + str(error)
                row['actual_status'] = 'UNKNOWN_unfinished'
                row['exception'] = {'type': type(error).__name__, 'message': str(error)[:2048]}
                row['complete_output'] = None
                row['elapsed_ns'] = boundary._clock(boundary._clock_id) - began
            except Exception as error:
                unfinished = type(error).__name__ + ': ' + str(error)
                row['actual_status'] = 'UNKNOWN_unfinished' if type(error) is checker_unresolved else 'fail'
                row['exception'] = {'type': type(error).__name__, 'message': str(error)[:2048]}
                row['complete_output'] = None
                row['elapsed_ns'] = boundary._clock(boundary._clock_id) - began
            row['started'] = calls['started'] > previous_starts
            row['returned'] = calls['returned'] > previous_returns
            records.append(row)
    result = {'schema': 'Q-split-neutral-controls-callable-result-v1', 'version': VERSION,
              'complete_declared_case_records': len(records) == 52, 'case_count': len(records),
              'fixture_sha256': FIXTURE_SHA256, 'checker_source': CHECKER_RECORD, 'results': records,
              'call_counters': calls, 'joint_began_ns': joint_began_ns, 'joint_deadline_ns': joint_deadline_ns,
              'all_cases_exercised': all(row['started'] for row in records),
              'all_exercised_checks_passed': unfinished is None and all(row['actual_status'].startswith('pass_') or row['actual_status'] == 'not_exercised' for row in records),
              'unfinished': unfinished, 'full_architecture_qualified': False,
              'original_Q_theorem_accepted': False, 'selected_accepted': False, 'point_union_accepted': False,
              'full24_accepted': False, 'trajectory_accepted': False, 'ROOT_resource_accepted': False,
              'induction_accepted': False, 'full_PA_accepted': False, 'native_accepted': False, 'RL_accepted': False,
              'scope': 'authored neutral controls only; no theorem discovery or scientific advantage'}
    # Entire final metadata/canonicalization is charged. Late completion cannot
    # retain a positive aggregate, even if an earlier individual observation exists.
    canonical(result)
    if unfinished is None:
        try:
            if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                    or boundary_check.__defaults__ is not boundary_check_state[2]
                    or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
                raise ValueError('actual final boundary endpoint changed')
            boundary_check(boundary)
        except Exception as error:
            result['all_exercised_checks_passed'] = False
            result['unfinished'] = type(error).__name__ + ': ' + str(error)
    result['completed_before_joint_deadline'] = result['unfinished'] is None
    canonical(result)
    if result['unfinished'] is None:
        if (Boundary.check is not boundary_check or boundary_check.__code__ is not boundary_check_state[1]
                or boundary_check.__defaults__ is not boundary_check_state[2]
                or boundary_check.__kwdefaults__ is not boundary_check_state[3]):
            raise ValueError('actual completed-record boundary endpoint changed')
        boundary_check(boundary)
    return result
