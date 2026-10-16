"""UNEXECUTED clean-process primitive-word verifier and non-executable protocol.

Only the coordinator supplies authenticated authority and checker-source bytes.
Producer data never selects a path, module, callable, theory, target or checker.
No producer code, graph, catalogue, self-check or claimed selected/rollback flag
is mathematical authority. Source review and new owned controls remain pending.

CLI positional arguments (trusted coordinator only):
authority_fd authority_sha256 authority_bytes candidate_fd candidate_sha256
candidate_bytes checker_source_fd result_fd joint_began_ns joint_deadline_ns

The response is two JSON lines followed by EOF: a complete body and a hash/size
completion record. A response is NOT a ROOT admission. The coordinator must
additionally require exit zero, both full authenticated lines/EOF, its own
observed completion before the original joint deadline, and all owned/caller
predicates. Even a fully written late mathematical certificate is unaccepted.
"""
import builtins
import hashlib
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import select
import sys
import time
import types

VERSION = 'Q-clean-original-target-word-verifier-Source-v4-global-clock'
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
AUTHORITY_MAX_BYTES = 1024 * 1024
CANDIDATE_MAX_BYTES = 2 * 1024 * 1024
RESPONSE_MAX_BYTES = 4 * 1024 * 1024
RULE_FIELDS = {'axiom': {'name'}, 'assumption': {'index'},
    'instantiate': {'universal', 'term'},
    'eq_subst': {'variable', 'template', 'left', 'right'},
    'mp': {'antecedent', 'implication'}, 'generalize': {'variable', 'source'}}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def literal_integer(value, low=0, high=(1 << 63) - 1):
    require(type(value) is int and low <= value <= high, 'literal bounded integer; no Boolean/coercion')
    return value


def hex_digest(value):
    require(type(value) is str and len(value) == 64
            and all(c in '0123456789abcdef' for c in value), 'exact lower-case SHA256')
    return value


def identifier(value):
    require(type(value) is str and 0 < len(value.encode('utf8')) <= 128
            and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in value),
            'bounded coordinator identifier')
    return value


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf8')


def value_digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def function_state(fn):
    require(type(fn) is types.FunctionType, 'exact Python function')
    return (fn, fn.__code__, id(fn.__defaults__),
            tuple(id(v) for v in fn.__defaults__ or ()), id(fn.__kwdefaults__),
            tuple((k, id(v)) for k, v in sorted((fn.__kwdefaults__ or {}).items())),
            tuple((id(cell), id(cell.cell_contents)) for cell in fn.__closure__ or ()))


def immutable_value(value, seen=None):
    """Seal module constants, not legitimate per-call semantic caches."""
    if seen is None:
        seen = set()
    if type(value) in (str, int, float, bool, bytes, type(None)):
        return (type(value), value)
    if type(value) not in (dict, list, tuple, set, frozenset):
        return None
    require(id(value) not in seen, 'acyclic declared constant data')
    seen.add(id(value))
    if type(value) is dict:
        result = ('dict', tuple((immutable_value(k, seen), immutable_value(v, seen))
                                for k, v in sorted(value.items(), key=lambda p: repr(p[0]))))
    elif type(value) in (set, frozenset):
        result = (type(value), tuple(sorted((immutable_value(v, seen) for v in value), key=repr)))
    else:
        result = (type(value), tuple(immutable_value(v, seen) for v in value))
    seen.remove(id(value))
    return result


def class_state(cls):
    items = []
    for base in cls.__mro__:
        bindings = tuple(sorted(vars(base).items()))
        functions = []
        for name, member in bindings:
            if isinstance(member, (staticmethod, classmethod)):
                member = member.__func__
            if type(member) is types.FunctionType:
                functions.append((name, function_state(member)))
            elif type(member) is property:
                functions.append((name, tuple(function_state(fn) if fn is not None else None
                                              for fn in (member.fget, member.fset, member.fdel))))
        items.append((base, bindings, tuple(functions)))
    return (cls, cls.__mro__, tuple(items))


def module_state(module):
    bindings = tuple(sorted(vars(module).items()))
    functions, classes, data = [], [], []
    for name, value in bindings:
        if type(value) is types.FunctionType and value.__module__ == module.__name__:
            functions.append((name, function_state(value)))
        elif isinstance(value, type) and value.__module__ == module.__name__:
            classes.append((name, class_state(value)))
        elif name != '__builtins__':
            sealed = immutable_value(value)
            if sealed is not None:
                data.append((name, sealed))
    return (module, bindings, tuple(functions), tuple(classes), tuple(data))


def endpoint_state(obj):
    """Actual cached decoder, including instance shadows and native scanner."""
    attrs = tuple(sorted(vars(obj).items()))
    methods = []
    for name in ('decode', 'raw_decode', 'scan_once'):
        value = getattr(obj, name)
        if type(value) is types.MethodType:
            methods.append((name, value.__self__, function_state(value.__func__)))
        elif type(value) is types.FunctionType:
            methods.append((name, function_state(value)))
        else:
            methods.append((name, type(value), value))
    return (obj, type(obj), class_state(type(obj)), attrs, tuple(methods))


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


class CodeSeal:
    """Fresh pinned address space only; no imported producer endpoint.

    Captures full module namespace names/identities and Python defaults/cells,
    actual cached JSON decoder/scanner endpoints and builtin name resolution.
    It does not claim asynchronous hostile-VM/OS integrity.
    """
    def __init__(self, modules, decoder, deadline_ns):
        self.modules = tuple(modules)
        self.deadline_ns = deadline_ns
        self.clock = time.clock_gettime_ns
        self.clock_id = time.CLOCK_MONOTONIC
        self.local_clock = time.perf_counter
        require(type(self.clock_id) is int and type(self.clock) is types.BuiltinFunctionType
                and type(self.local_clock) is types.BuiltinFunctionType, 'original native global/local clocks')
        self.validators = tuple((fn, function_state(fn)) for fn in
            (require, literal_integer, function_state, immutable_value, class_state,
             module_state, endpoint_state, project_local_float_deadline))
        self.validator_codes = tuple((fn, fn.__code__) for fn, _ in self.validators)
        self.check_method = CodeSeal.check
        self.check_code = CodeSeal.check.__code__
        self.decoder = decoder
        self.modules_at_capture = tuple(module_state(m) for m in self.modules)
        self.builtins_at_capture = tuple(sorted(vars(builtins).items()))
        self.decoder_at_capture = endpoint_state(decoder)
        self.default_decoder = json._default_decoder
        self.default_decoder_at_capture = endpoint_state(json._default_decoder)

    def check(self):
        # These direct comparisons precede the original captured validators.
        if CodeSeal.check is not self.check_method or CodeSeal.check.__code__ is not self.check_code:
            raise ValueError('clean seal method changed')
        if (time.clock_gettime_ns is not self.clock or time.CLOCK_MONOTONIC is not self.clock_id
                or type(self.clock_id) is not int or time.perf_counter is not self.local_clock):
            raise ValueError('original clean-process clock changed')
        if any(fn.__code__ is not code for fn, code in self.validator_codes):
            raise ValueError('original clean validator code changed')
        if tuple((globals().get(fn.__name__), fn.__code__) for fn, _ in self.validators) != self.validator_codes:
            raise ValueError('original clean validator binding changed')
        state = self.validators[2][0]
        if any(state(fn) != anchor for fn, anchor in self.validators):
            raise ValueError('clean validator defaults/closure changed')
        if self.clock(self.clock_id) >= self.deadline_ns:
            raise TimeoutError('original joint20 deadline')
        if tuple(sorted(vars(builtins).items())) != self.builtins_at_capture:
            raise ValueError('builtin resolution changed')
        if tuple(module_state(m) for m in self.modules) != self.modules_at_capture:
            raise ValueError('clean module/code/default/constant namespace changed')
        if endpoint_state(self.decoder) != self.decoder_at_capture:
            raise ValueError('actual strict decoder/scanner changed')
        if json._default_decoder is not self.default_decoder or endpoint_state(json._default_decoder) != self.default_decoder_at_capture:
            raise ValueError('actual cached default decoder/scanner changed')
        if self.clock(self.clock_id) >= self.deadline_ns:
            raise TimeoutError('joint20 exceeded after clean guard')


def no_constant(value):
    raise ValueError('non-finite JSON numeric token prohibited')


def no_float(value):
    raise ValueError('floating JSON token prohibited; integers are literal')


def parse_integer(text):
    require(len(text) <= 20, 'bounded integer token')
    value = int(text)
    require(-(1 << 63) <= value < (1 << 63), 'signed64 JSON integer')
    return value


def unique_pairs(pairs):
    value = {}
    for key, member in pairs:
        require(key not in value, 'duplicate JSON object key')
        value[key] = member
    return value


def inspect_json_tree(value, depth=0, visits=None):
    if visits is None:
        visits = [0]
    visits[0] += 1
    require(depth <= 64 and visits[0] <= 500000, 'complete bounded wire tree; no prefix')
    if type(value) is dict:
        require(all(type(k) is str for k in value), 'literal JSON member names')
        for key, member in value.items():
            require(len(key.encode('utf8')) <= 128, 'bounded wire member name')
            inspect_json_tree(member, depth + 1, visits)
    elif type(value) is list:
        for member in value:
            inspect_json_tree(member, depth + 1, visits)
    elif type(value) is str:
        require(len(value.encode('utf8')) <= 4096, 'bounded wire string')
    else:
        require(type(value) in (int, bool, type(None)), 'JSON integers/Booleans/null only')


def decode_complete(raw, decoder, guard):
    boundary_state, boundary_state_code = function_state, function_state.__code__
    guard_live = guard
    guard_live_anchor = boundary_state(guard)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    text = raw.decode('utf8', errors='strict')
    # Only JSON whitespace (not Unicode strip/isspace) may precede/follow.
    start = 0
    while start < len(text) and text[start] in ' \t\r\n':
        start += 1
    value, end = decoder.raw_decode(text, start)
    require(all(character in ' \t\r\n' for character in text[end:]),
            'whole single JSON document; only exact JSON whitespace then EOF')
    inspect_json_tree(value)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    return value


def read_fd(fd, expected_bytes, expected_sha256, cap, guard):
    boundary_state, boundary_state_code = function_state, function_state.__code__
    guard_live = guard
    guard_live_anchor = boundary_state(guard)
    literal_integer(fd, 3, 1 << 20); literal_integer(expected_bytes, 0, cap); hex_digest(expected_sha256)
    chunks, size = [], 0
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    while True:
        if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
            raise ValueError('original immediate boundary validator changed')
        if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
            raise ValueError('live boundary identity/code changed at own caller')
        if boundary_state(guard) != guard_live_anchor:
            raise ValueError('live boundary defaults/closure changed at own caller')
        guard_live()
        if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
            raise ValueError('original immediate boundary validator changed')
        if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
            raise ValueError('live boundary identity/code changed at own caller')
        if boundary_state(guard) != guard_live_anchor:
            raise ValueError('live boundary defaults/closure changed at own caller')
        ready, _, _ = select.select([fd], [], [], 0.02)
        if not ready:
            continue
        chunk = os.read(fd, min(65536, cap - size + 1))
        if not chunk:
            break
        size += len(chunk)
        require(size <= cap and size <= expected_bytes, 'complete FD length bound, never truncate')
        chunks.append(chunk)
    raw = b''.join(chunks)
    require(size == expected_bytes and hashlib.sha256(raw).hexdigest() == expected_sha256,
            'same authenticated complete FD buffer SHA/length/EOF')
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    return raw


def source_pin(record):
    require(type(record) is dict and set(record) == {'sha256', 'bytes'}, 'wire pin has no path authority')
    hex_digest(record['sha256']); literal_integer(record['bytes'], 0, 64 * 1024 * 1024)


def validate_authority(value):
    fields = {'schema', 'coordinator_invocation_id', 'declaration', 'binding',
              'raw_input_bindings', 'source_bindings', 'limits'}
    require(type(value) is dict and set(value) == fields
            and value['schema'] == 'Q-clean-verifier-fixed-authority-v1', 'exact fixed-authority schema')
    identifier(value['coordinator_invocation_id'])
    require(value['binding'] == BINDING and value['raw_input_bindings'] == RAW_INPUT_BINDINGS,
            'unchanged original raw inputs/model/authority/registry')
    require(type(value['limits']) is dict and set(value['limits']) == set(LIMITS)
            and all(type(value['limits'][key]) is int and 0 <= value['limits'][key] < (1 << 63)
                    for key in LIMITS) and value['limits'] == LIMITS,
            'literal integer original joint/owned/caller limits; no Boolean')
    declaration = value['declaration']
    require(type(declaration) is dict and set(declaration) ==
        {'schema', 'theory', 'ordered_Gamma', 'target', 'parameters', 'height', 'grammar', 'limits'},
        'entire original declaration')
    require(value_digest(declaration) == DECLARATION_VALUE_SHA256
            and type(declaration['height']) is int and declaration['height'] == 24,
            'exact original theory/full occurrence-ordered Gamma/parameters/closed target/finite grammar')
    require(type(value['source_bindings']) is dict and set(value['source_bindings']) ==
            {'coordinator', 'producer', 'verifier', 'independent_checker', 'point_graph'},
            'separate current source-role ledger')
    for record in value['source_bindings'].values():
        source_pin(record)
    require(value['source_bindings']['independent_checker'] ==
            {'sha256': CHECKER_SHA256, 'bytes': CHECKER_BYTES}, 'unchanged independently authored checker')
    require(value['source_bindings']['point_graph'] ==
            {'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567', 'bytes': 28531},
            'unchanged complete original point graph; raw provenance only here')


def validate_candidate(value, authority, authority_sha256):
    fields = {'schema', 'coordinator_invocation_id', 'authority_sha256', 'binding',
              'submission_index', 'commands', 'origin', 'termination'}
    require(type(value) is dict and set(value) == fields
            and value['schema'] == 'Q-untrusted-first-candidate-word-v1', 'exact candidate schema; no path/checked authority')
    require(value['coordinator_invocation_id'] == authority['coordinator_invocation_id']
            and value['authority_sha256'] == authority_sha256 and value['binding'] == authority['binding'],
            'candidate matches authenticated coordinator context, not an alternate target')
    require(type(value['submission_index']) is int and value['submission_index'] == 0,
            'one first submission; no restart/favorable subset')
    commands = value['commands']
    require(type(commands) is list and 1 <= len(commands) <= 24, 'complete original-board ancestry word')
    origin = value['origin']
    require(type(origin) is dict and set(origin) == {'kind', 'source_event_index', 'physical_keys'}
            and origin['kind'] == 'producer_claimed_selected_original_target_ancestry',
            'source-claimed provenance only')
    literal_integer(origin['source_event_index'], 0, 2000)
    keys = origin['physical_keys']
    require(type(keys) is list and len(keys) == len(commands), 'every expanded command has one claimed physical key')
    physical_rows = []
    for word_row, (command, key) in enumerate(zip(commands, keys)):
        require(type(command) is dict and command.get('rule') in RULE_FIELDS, 'literal primitive command')
        rule = command['rule']
        require(set(command) == {'rule', 'formula'} | RULE_FIELDS[rule], 'exact primitive fields')
        require(type(key) is list and len(key) == 3 and type(key[2]) is list, 'literal recipe/row/ordered-port key')
        literal_integer(key[0], 0, 19999); row = literal_integer(key[1], 0, 23)
        require(not physical_rows or row > physical_rows[-1], 'unique ascending claimed physical rows')
        refs = []
        if rule == 'mp':
            refs = [literal_integer(command['antecedent'], 0, word_row - 1),
                    literal_integer(command['implication'], 0, word_row - 1)]
        elif rule == 'generalize':
            refs = [literal_integer(command['source'], 0, word_row - 1)]
        elif rule == 'assumption':
            literal_integer(command['index'], 0, len(authority['declaration']['ordered_Gamma']) - 1)
        require(all(type(ref) is int and 0 <= ref < row for ref in key[2]), 'strict-prior integer physical ports')
        require(key[2] == [physical_rows[ref] for ref in refs], 'exact ordered word-to-physical-port correspondence')
        physical_rows.append(row)
    termination = value['termination']
    require(type(termination) is dict and set(termination) ==
        {'producer_status', 'root_rollback_claimed', 'proof_accepted', 'full24_accepted', 'trajectory_accepted'},
        'exact untrusted producer termination')
    require(termination['producer_status'] == 'CANDIDATE_NOT_VERIFIED'
            and termination['root_rollback_claimed'] is True
            and all(termination[name] is False for name in
                    ('proof_accepted', 'full24_accepted', 'trajectory_accepted')),
            'producer cannot issue proof/board/trajectory authority')


def load_checker(raw):
    require(len(raw) == CHECKER_BYTES and hashlib.sha256(raw).hexdigest() == CHECKER_SHA256,
            'hard-bound exact checker buffer')
    module = types.ModuleType('Q_clean_pinned_independent_checker')
    module.__file__ = '<coordinator-authenticated-independent-Q-semantics>'
    code = compile(raw, module.__file__, 'exec')
    exec(code, module.__dict__)
    require(module.VERSION == 'independent-complete-finite-Q-semantics-v1'
            and type(module.check_primitive_word) is types.FunctionType,
            'exact pinned independent word endpoint')
    return module


def write_response(fd, body, guard):
    boundary_state, boundary_state_code = function_state, function_state.__code__
    guard_live = guard
    guard_live_anchor = boundary_state(guard)
    body_bytes = canonical_bytes(body) + b'\n'
    require(len(body_bytes) <= RESPONSE_MAX_BYTES, 'whole response bound; no prefix certificate')
    completion = {'schema': 'Q-clean-verifier-response-completion-v1',
                  'body_sha256': hashlib.sha256(body_bytes).hexdigest(),
                  'body_bytes': len(body_bytes), 'exit_zero_and_coordinator_deadline_required': True}
    raw = body_bytes + canonical_bytes(completion) + b'\n'
    offset = 0
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    while offset < len(raw):
        if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
            raise ValueError('original immediate boundary validator changed')
        if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
            raise ValueError('live boundary identity/code changed at own caller')
        if boundary_state(guard) != guard_live_anchor:
            raise ValueError('live boundary defaults/closure changed at own caller')
        guard_live()
        if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
            raise ValueError('original immediate boundary validator changed')
        if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
            raise ValueError('live boundary identity/code changed at own caller')
        if boundary_state(guard) != guard_live_anchor:
            raise ValueError('live boundary defaults/closure changed at own caller')
        _, ready, _ = select.select([], [fd], [], 0.02)
        if ready:
            count = os.write(fd, raw[offset:offset + 4096])
            require(type(count) is int and count > 0, 'complete response write')
            offset += count
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    guard_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if guard is not guard_live or guard.__code__ is not guard_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(guard) != guard_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')  # A late complete wire does not earn exit zero.


def main(argv):
    require(len(argv) == 10, 'exact trusted coordinator verifier CLI10')
    authority_fd, authority_sha, authority_size, candidate_fd, candidate_sha, candidate_size, source_fd, result_fd, began_ns, deadline_ns = argv
    require(all(type(text) is str and text.isascii() and text.isdecimal()
                and (text == '0' or not text.startswith('0')) for text in
                (authority_fd, authority_size, candidate_fd, candidate_size, source_fd, result_fd, began_ns, deadline_ns)),
            'canonical decimal coordinator CLI integers')
    authority_fd, authority_size, candidate_fd, candidate_size, source_fd, result_fd, began_ns, deadline_ns = [
        int(text) for text in (authority_fd, authority_size, candidate_fd, candidate_size, source_fd, result_fd, began_ns, deadline_ns)]
    for value in (authority_fd, candidate_fd, source_fd, result_fd):
        literal_integer(value, 3, 1 << 20)
    require(len({authority_fd, candidate_fd, source_fd, result_fd}) == 4, 'distinct owned channels')
    global_clock, clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
    require(type(clock_id) is int and type(global_clock) is types.BuiltinFunctionType,
            'original native global clock and exact integer clock ID')
    now_ns = global_clock(clock_id)
    require(time.clock_gettime_ns is global_clock and time.CLOCK_MONOTONIC is clock_id
            and type(now_ns) is int and 0 <= began_ns < deadline_ns < (1 << 63)
            and deadline_ns - began_ns == 20000000000 and began_ns <= now_ns < deadline_ns,
            'same original global CLOCK_MONOTONIC joint20; no reset or mixed perf epoch')
    hex_digest(authority_sha); hex_digest(candidate_sha)
    decoder = json.JSONDecoder(object_pairs_hook=unique_pairs, parse_int=parse_integer,
                               parse_float=no_float, parse_constant=no_constant, strict=True)
    modules = (sys.modules[__name__], json, json.decoder, json.encoder, json.scanner,
               hashlib, itertools, math, os, select, sys, time, types)
    seal = CodeSeal(modules, decoder, deadline_ns)
    guard_method, guard_code = seal.check, CodeSeal.check.__code__
    def source_guard():
        if guard_method.__self__ is not seal or guard_method.__func__ is not CodeSeal.check or CodeSeal.check.__code__ is not guard_code:
            raise ValueError('effective clean guard changed before delegation')
        guard_method()
    guard_anchor = function_state(source_guard)
    def boundary():
        if source_guard is not guard_anchor[0] or source_guard.__code__ is not guard_anchor[1]:
            raise ValueError('clean delegated guard identity/code changed')
        if function_state(source_guard) != guard_anchor:
            raise ValueError('clean delegated guard defaults/closure changed')
        source_guard()
    boundary_state, boundary_state_code = function_state, function_state.__code__
    boundary_live = boundary
    boundary_live_anchor = boundary_state(boundary)
    authority_raw = read_fd(authority_fd, authority_size, authority_sha, AUTHORITY_MAX_BYTES, boundary)
    authority = decode_complete(authority_raw, decoder, boundary)
    validate_authority(authority)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    # Self bytes come from the fixed own launch path, never a candidate path.
    own_raw = Path(__file__).read_bytes()
    require(authority['source_bindings']['verifier'] ==
            {'sha256': hashlib.sha256(own_raw).hexdigest(), 'bytes': len(own_raw)}, 'coordinator-authenticated own source bytes')
    candidate_raw = read_fd(candidate_fd, candidate_size, candidate_sha, CANDIDATE_MAX_BYTES, boundary)
    candidate = decode_complete(candidate_raw, decoder, boundary)
    validate_candidate(candidate, authority, authority_sha)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    checker_raw = read_fd(source_fd, CHECKER_BYTES, CHECKER_SHA256, CHECKER_BYTES, boundary)
    checker = load_checker(checker_raw)
    # Owned load transition seals the new module before any mathematical call.
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    seal = CodeSeal(modules + (checker,), decoder, deadline_ns)
    guard_method, guard_code = seal.check, CodeSeal.check.__code__
    guard_anchor = function_state(source_guard)
    # Exact owned new-checker transition only: code/default identity was
    # checked above; the known source_guard seal/anchor closure cells now
    # bind the new exact pinned module before any mathematical invocation.
    boundary_live_anchor = boundary_state(boundary)
    fixed_value_sha, candidate_value_sha = value_digest(authority), value_digest(candidate)
    endpoint = checker.check_primitive_word
    endpoint_anchor = function_state(endpoint)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    # Project before the logical-rejection try: projection failure is UNKNOWN,
    # never an expected mathematical ValueError rejection. No shared float epoch.
    _, local_deadline = project_local_float_deadline(deadline_ns)
    certificate, rejection = None, None
    try:
        require(checker.check_primitive_word is endpoint and function_state(endpoint) == endpoint_anchor,
                'exact original independent checker endpoint')
        certificate = endpoint(theory=authority['declaration']['theory'],
            parameters=authority['declaration']['parameters'],
            original_Gamma=authority['declaration']['ordered_Gamma'], commands=candidate['commands'],
            target=authority['declaration']['target'], source_guard=boundary,
            deadline=local_deadline, maximum_visits=5000000)
        require(certificate['completed'] is True
                and certificate['original_Gamma_target_sequent_accepted'] is True
                and certificate['essential_rows'] == list(range(len(candidate['commands']))),
                'complete dependency ancestry, no favorable subset or unchecked suffix')
    except ValueError as error:
        rejection = {'exception_type': type(error).__name__, 'message': str(error)}
        certificate = None
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    require(checker.check_primitive_word is endpoint and function_state(endpoint) == endpoint_anchor
            and value_digest(authority) == fixed_value_sha and value_digest(candidate) == candidate_value_sha,
            'original checker/input values preserved after complete verification')
    body = {'schema': 'Q-clean-verifier-response-body-v1', 'version': VERSION,
        'coordinator_invocation_id': authority['coordinator_invocation_id'],
        'authority_raw_sha256': authority_sha, 'candidate_raw_sha256': candidate_sha,
        'authority_value_sha256': fixed_value_sha, 'candidate_value_sha256': candidate_value_sha,
        'binding': authority['binding'], 'source_bindings': authority['source_bindings'],
        'submission_index': 0, 'submissions_checked': 1,
        'status': 'WORD_VERIFIED_PENDING_COORDINATOR' if certificate is not None else 'WORD_REJECTED',
        'independent_word_certificate': certificate, 'rejection': rejection,
        'producer_origin_claim': candidate['origin'], 'producer_termination_claim': candidate['termination'],
        'actual_selected_accepted': False, 'point_snapshot_accepted': False, 'full24_accepted': False,
        'full_trajectory_accepted': False, 'native_accepted': False, 'RL_accepted': False,
        'induction_accepted': False, 'full_PA_accepted': False, 'ROOT_primary_accepted': False,
        'ROOT_resource_accepted': False, 'joint_began_ns': began_ns, 'joint_deadline_ns': deadline_ns}
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    write_response(result_fd, body, boundary)
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    boundary_live()
    if function_state is not boundary_state or function_state.__code__ is not boundary_state_code:
        raise ValueError('original immediate boundary validator changed')
    if boundary is not boundary_live or boundary.__code__ is not boundary_live_anchor[1]:
        raise ValueError('live boundary identity/code changed at own caller')
    if boundary_state(boundary) != boundary_live_anchor:
        raise ValueError('live boundary defaults/closure changed at own caller')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        # No receipt/certificate is emitted on incomplete input/check/deadline.
        # Any previously written response is invalid unless coordinator sees
        # exit zero, full completion/EOF and its own timely observation.
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(2)
