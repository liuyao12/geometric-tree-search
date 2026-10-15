"""UNEXECUTED ordinary-word-only logical adapter, not an FD/cold authority.

A future authenticated clean caller must load unchanged checker1717 and this
exact Source into a fresh process, bind every actual module/class/native endpoint,
and supply its genuine full source_guard. No producer object/module enters that
checker process. This module neither loads Source nor authenticates file bytes.
Current selected-point verifier/protocol remains unchanged and rejects this wire.
"""
import hashlib
import json
import math
import resource
import sys
import time
import types

VERSION = 'Q-ordinary-first-ready-word-validation-adapter-Source-v1'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CHECKER_SHA256 = '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'

CHECKER_BYTES = 46514

DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'

BINDING = {
    'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
    'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
    'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039',
    'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe'}

RAW_INPUT_BINDINGS = {
    'declaration': {'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc', 'bytes': 2683},
    'preparation': {'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a', 'bytes': 38376960},
    'initial_state': {'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9', 'bytes': 8296118},
    'initial_oracle': {'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969', 'bytes': 8295473},
    'finite_ROOT_admission': {'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1', 'bytes': 8563},
    'finite_certificate': {'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87', 'bytes': 5789},
    'word_controls_ROOT': {'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1', 'bytes': 6796},
    'architecture_choice': {'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f', 'bytes': 6808}}

LIMITS = {'joint_seconds': 20, 'failure_only_seconds': 55, 'owned_seconds': 60,
          'aggregate_owned_bytes': 536870912, 'caller_seconds': 90,
          'caller_finish_reserve_seconds': 1}

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


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def value_digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def function_state(function):
    """Full identity/strong-reference metadata, including keyword entries."""
    need(type(function) is types.FunctionType, 'exact Python function endpoint')
    kw = function.__kwdefaults__
    return (function, function.__code__, function.__globals__, function.__defaults__,
        tuple((id(v), v) for v in function.__defaults__ or ()), kw,
        tuple((k, id(v), v) for k, v in sorted((kw or {}).items())),
        tuple((cell, cell.cell_contents) for cell in function.__closure__ or ()))


def validate_first_ready_candidate(*, candidate, fixed_authority,
        fixed_authority_sha256, checker_module, source_guard, joint_began_ns, joint_deadline_ns):
    """New ordinary origin; same unchanged independent six-rule word endpoint.

    Caller authenticates the exact authority buffer that it parsed. Only this
    logical call is concrete here; read-only FDs, raw Source cache/MRO/parser and
    final output/terminal/resource custody remain required cold-wrapper work.
    """
    need(sys.platform == 'darwin' and type(joint_began_ns) is int
         and type(joint_deadline_ns) is int and 0 <= joint_began_ns < joint_deadline_ns < (1 << 63)
         and joint_deadline_ns - joint_began_ns == 20000000000,
         'original inherited native joint20, no reset')
    need(type(fixed_authority_sha256) is str and len(fixed_authority_sha256) == 64
         and all(c in '0123456789abcdef' for c in fixed_authority_sha256), 'authenticated whole authority digest')
    need(type(fixed_authority) is dict and set(fixed_authority) ==
         {'schema', 'coordinator_invocation_id', 'declaration', 'binding', 'raw_input_bindings', 'source_bindings', 'limits'}
         and fixed_authority['schema'] == 'Q-ordinary-word-fixed-authority-v1', 'explicit ordinary-purpose authority')
    declaration = fixed_authority['declaration']
    need(fixed_authority['binding'] == BINDING and fixed_authority['raw_input_bindings'] == RAW_INPUT_BINDINGS
         and value_digest(declaration) == DECLARATION_VALUE_SHA256
         and declaration['ordered_Gamma'] == [] and type(declaration['height']) is int
         and declaration['height'] == 24, 'exact original full declaration/theory/empty Gamma/parameters/target/epochs')
    identifier = fixed_authority['coordinator_invocation_id']
    need(type(identifier) is str and 1 <= len(identifier) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in identifier),
         'bounded genuine coordinator invocation')
    need(type(fixed_authority['limits']) is dict and set(fixed_authority['limits']) == set(LIMITS)
         and all(type(v) is int for v in fixed_authority['limits'].values())
         and fixed_authority['limits'] == LIMITS, 'same literal limits, Boolean not integer')
    sources = fixed_authority['source_bindings']
    need(type(sources) is dict and set(sources) ==
         {'coordinator', 'ordinary_producer', 'ordinary_adapter', 'independent_checker'},
         'separate ordinary source ledger, no selected point-source assertion')
    for record in sources.values():
        need(type(record) is dict and set(record) == {'sha256', 'bytes'}
             and type(record['sha256']) is str and len(record['sha256']) == 64
             and all(c in '0123456789abcdef' for c in record['sha256'])
             and type(record['bytes']) is int and 0 < record['bytes'] <= 1048576,
             'whole immutable Source pins authenticated by future caller')
    need(sources['independent_checker'] == {'sha256': CHECKER_SHA256, 'bytes': CHECKER_BYTES},
         'unchanged independently authored checker1717')
    need(type(candidate) is dict and set(candidate) ==
         {'schema', 'coordinator_invocation_id', 'authority_sha256', 'binding', 'submission_index', 'commands', 'origin', 'termination'}
         and candidate['schema'] == 'Q-untrusted-ordinary-first-ready-word-v1'
         and candidate['coordinator_invocation_id'] == identifier
         and candidate['authority_sha256'] == fixed_authority_sha256 and candidate['binding'] == BINDING
         and type(candidate['submission_index']) is int and candidate['submission_index'] == 0,
         'sole ordinary first-ready candidate, no selected-origin substitution')
    need(len(canonical(candidate).encode('utf8')) <= 2 * 1048576, 'whole complete ordinary wire cap')
    commands, origin, termination = candidate['commands'], candidate['origin'], candidate['termination']
    need(type(commands) is list and 1 <= len(commands) <= 24, 'nonempty at-most24 primitive commands')
    need(type(origin) is dict and set(origin) ==
         {'kind', 'recipe_indices', 'formula_codes', 'discovery_ordinals', 'known_formula_count', 'completed_sweeps'}
         and origin['kind'] == 'ordinary_first_ready_forward_saturation', 'ordinary provenance only')
    for field, maximum in [('recipe_indices', 20000), ('formula_codes', 50000), ('discovery_ordinals', 50000)]:
        need(type(origin[field]) is list and len(origin[field]) == len(commands)
             and all(type(x) is int and 0 <= x < maximum for x in origin[field]), 'literal parallel ordinary provenance')
    need(type(origin['known_formula_count']) is int and len(commands) <= origin['known_formula_count'] <= 50000
         and type(origin['completed_sweeps']) is int and 1 <= origin['completed_sweeps'] <= 50001
         and len(set(origin['formula_codes'])) == len(commands)
         and all(a < b for a, b in zip(origin['discovery_ordinals'], origin['discovery_ordinals'][1:]))
         and all(x < origin['known_formula_count'] for x in origin['discovery_ordinals']),
         'bounded unique monotone discovery claims; no independent trace authority')
    need(type(termination) is dict and set(termination) ==
         {'producer_status', 'proof_accepted', 'full24_accepted', 'trajectory_accepted'}
         and termination['producer_status'] == 'CANDIDATE_NOT_VERIFIED'
         and all(termination[name] is False for name in ('proof_accepted', 'full24_accepted', 'trajectory_accepted')),
         'ordinary producer has no checked/point/trajectory authority')
    fields = {'axiom': {'name'}, 'assumption': {'index'}, 'instantiate': {'universal', 'term'},
        'eq_subst': {'variable', 'template', 'left', 'right'},
        'mp': {'antecedent', 'implication'}, 'generalize': {'variable', 'source'}}
    for row, command in enumerate(commands):
        need(type(command) is dict and command.get('rule') in fields
             and set(command) == {'rule', 'formula'} | fields[command['rule']], 'exact six primitive command fields')
        refs = [command['antecedent'], command['implication']] if command['rule'] == 'mp' else (
            [command['source']] if command['rule'] == 'generalize' else [])
        need(all(type(ref) is int and 0 <= ref < row for ref in refs), 'ordered strict-prior integer references')
        if command['rule'] == 'assumption':
            need(type(command['index']) is int and 0 <= command['index'] < len(declaration['ordered_Gamma']),
                 'original indexed context only; empty context has no assumptions')
    need(type(checker_module) is types.ModuleType
         and checker_module.VERSION == 'independent-complete-finite-Q-semantics-v1',
         'genuine separately loaded original checker module required')
    endpoint = checker_module.check_primitive_word
    need(type(endpoint) is types.FunctionType and endpoint.__globals__ is checker_module.__dict__,
         'actual original checker endpoint, not an inherited producer callable')
    # Initial captures occur before any injected callback. The cold caller must
    # additionally authenticate module/class/MRO/native/parser/source bytes.
    functions = (need, canonical, value_digest, function_state, project_local_float_deadline,
                 validate_first_ready_candidate, endpoint, source_guard)
    anchors = tuple(function_state(f) for f in functions)
    clock, clock_id, usage, usage_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC, resource.getrusage, resource.RUSAGE_SELF
    time_module, resource_module, math_module, types_module = time, resource, math, types
    native = (time.perf_counter, math.nextafter, math.isfinite, float.as_integer_ratio)
    original_guard, fault = source_guard, RuntimeError
    authority_value_sha, candidate_value_sha = value_digest(fixed_authority), value_digest(candidate)

    def boundary():
        # The two direct loops straddle the callback. No delegated function-state
        # validator is trusted after arbitrary callback return.
        for phase in (0, 1):
            for function, code, globals_dict, defaults, positional, kw, entries, cells in anchors:
                if (function.__code__ is not code or function.__globals__ is not globals_dict
                        or function.__defaults__ is not defaults or function.__kwdefaults__ is not kw
                        or len(function.__defaults__ or ()) != len(positional)
                        or any(value is not old for value, (_, old) in zip(function.__defaults__ or (), positional))
                        or set(function.__kwdefaults__ or {}) != {k for k, _, _ in entries}
                        or any(function.__kwdefaults__[k] is not value for k, _, value in entries)
                        or len(function.__closure__ or ()) != len(cells)
                        or any(a is not b or a.cell_contents is not value
                               for a, (b, value) in zip(function.__closure__ or (), cells))):
                    raise fault('original delegated function/code/default-entry/closure changed')
            if (time is not time_module or resource is not resource_module or math is not math_module
                    or types is not types_module or time.clock_gettime_ns is not clock
                    or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC is not clock_id
                    or resource.getrusage is not usage or resource.RUSAGE_SELF is not usage_id
                    or time.perf_counter is not native[0] or math.nextafter is not native[1]
                    or math.isfinite is not native[2] or float.as_integer_ratio is not native[3]
                    or checker_module.check_primitive_word is not endpoint
                    or tuple((need, canonical, value_digest, function_state, project_local_float_deadline,
                              validate_first_ready_candidate, endpoint, source_guard)) != functions):
                raise fault('original module/helper/native endpoint binding changed')
            now = clock(clock_id)
            if (now < joint_began_ns or now >= joint_deadline_ns
                    or usage(usage_id).ru_maxrss >= 524288000):
                raise fault('ordinary validation not complete inside original global20/500MiB')
            if phase == 0:
                try:
                    original_guard()
                except BaseException as failure:
                    raise fault('genuine cold source guard failed') from failure

    boundary_fn, boundary_code = boundary, boundary.__code__
    boundary_cells = tuple((cell, cell.cell_contents) for cell in boundary.__closure__ or ())
    # Each outer boundary delegation immediately checks its actual original
    # function/code/no-defaults/cells, not only a previously delegated guard.
    for stage in ('before_projection', 'after_projection', 'after_checker', 'final_output'):
        if (boundary is not boundary_fn or boundary_fn.__code__ is not boundary_code
                or boundary_fn.__defaults__ is not None or boundary_fn.__kwdefaults__ is not None
                or len(boundary_fn.__closure__ or ()) != len(boundary_cells)
                or any(a is not b or a.cell_contents is not value
                       for a, (b, value) in zip(boundary_fn.__closure__ or (), boundary_cells))):
            raise fault('actual invoking boundary changed')
        boundary_fn()
        if stage == 'before_projection':
            _, local_deadline = project_local_float_deadline(joint_deadline_ns)
        elif stage == 'after_projection':
            certificate, rejection = None, None
            try:
                certificate = endpoint(theory=declaration['theory'], parameters=declaration['parameters'],
                    original_Gamma=declaration['ordered_Gamma'], commands=commands, target=declaration['target'],
                    source_guard=boundary_fn, deadline=local_deadline, maximum_visits=5000000)
            except ValueError as failure:
                rejection = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
        elif stage == 'after_checker':
            need(value_digest(fixed_authority) == authority_value_sha and value_digest(candidate) == candidate_value_sha,
                 'entire decoded authority/candidate unchanged across checker')
            if certificate is not None:
                need(certificate['completed'] is True and certificate['original_Gamma_target_sequent_accepted'] is True
                     and certificate['essential_rows'] == list(range(len(commands))),
                     'whole dependency-complete exact original-target word')
            result = {'schema': 'Q-ordinary-first-ready-word-validation-v1', 'version': VERSION,
                'CLOCK_DOMAIN': CLOCK_DOMAIN, 'coordinator_invocation_id': identifier,
                'authority_sha256': fixed_authority_sha256, 'binding': dict(BINDING),
                'status': 'WORD_ACCEPTED' if certificate is not None else 'WORD_REJECTED',
                'word_logically_accepted': certificate is not None,
                'certificate': certificate, 'rejection': rejection,
                'selected_provenance_accepted': False, 'point_state_accepted': False,
                'full24_accepted': False, 'trajectory_accepted': False, 'native_accepted': False,
                'ROOT_primary_accepted': False, 'ROOT_resource_accepted': False,
                'finite_catalogue_membership_independently_checked': False}
            canonical(result)
    # The real FD output, exit/reap and terminal clock are future caller gates.
    return result
