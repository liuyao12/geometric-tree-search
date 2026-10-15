"""UNEXECUTED W01-W15 genuine fresh-verifier controls adapter Source.

The trusted cold caller authenticates and seals the fixed modules, runtime,
readonly Source/input buffers and genuine coordinator Owner BEFORE this factory.
No coordinator.main/validate_plan, producer, graph or Q preparation parser is
called. Every candidate is exactly an authored CONTROL_UNDECLARED/bottom control.
W15 preserves the real complete response and rejects a labeled body-only view.
W16 is deferred in neutral runnerV2; this adapter cannot admit the full52.
Ordinary synchronous process/source custody is assumed, not hostile-VM security.
"""
import copy
import hashlib
import os
from pathlib import Path
import sys
import time
import types

VERSION = 'Q-clean-verifier-protocol-controls-adapter-Source-v4'
SOURCE_RECORDS = {'coordinator': {'bytes': 53864,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-coordinator-source-20261014/Q_split_owned_coordinator_v5.py',
                 'sha256': '1a769203da1050d2ede508edf3f2d40a4620be31d873e75eb4eb84245425785f'},
 'independent_checker': {'bytes': 46514,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py',
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-candidate-producer-source-20261014/Q_untrusted_candidate_search_v2.py',
              'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'verifier': {'bytes': 42086,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clean-verifier-protocol-source-20261014/Q_clean_word_verifier_v3.py',
              'sha256': 'a5cfbe5c72ab617d1c98b1939c4d24aefc0e1c701e36b5fc141dc48bd1ea329b'}}
RUNTIME = {'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
RAW_INPUT_BINDINGS = {'architecture_choice': {'bytes': 6808,
                         'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f'},
 'declaration': {'bytes': 2683,
                 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
 'finite_ROOT_admission': {'bytes': 8563,
                           'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1'},
 'finite_certificate': {'bytes': 5789,
                        'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87'},
 'initial_oracle': {'bytes': 8295473,
                    'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'},
 'initial_state': {'bytes': 8296118,
                   'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'},
 'preparation': {'bytes': 38376960,
                 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'},
 'word_controls_ROOT': {'bytes': 6796,
                        'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1'}}
BINDING = {'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
 'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe',
 'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
 'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039'}
LIMITS = {'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}
DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'
CASE_PROJECTION = {'W01-whole-typed-rejection-baseline': {'expected': 'transport/schema accepted; WORD_REJECTED with '
                                                    'no primary acceptance',
                                        'id': 'W01-whole-typed-rejection-baseline',
                                        'input': 'one complete candidate as below',
                                        'intervention': None},
 'W02-duplicate-top-key': {'expected': 'protocol rejection before word call',
                           'id': 'W02-duplicate-top-key',
                           'input': 'literal duplicate schema key in same object',
                           'intervention': {'raw_suffix_or_edit': 'duplicate object field, retain '
                                                                  'whole bytes; no ordinary-dict '
                                                                  'normalization'}},
 'W03-truncated-EOF': {'expected': 'incomplete input; no certificate',
                       'id': 'W03-truncated-EOF',
                       'input': 'drop final closing brace and close pipe',
                       'intervention': {'raw_edit': 'remove last object-closing byte'}},
 'W04-second-document': {'expected': 'whole EOF rejection',
                         'id': 'W04-second-document',
                         'input': 'valid candidate followed by {}',
                         'intervention': {'suffix_utf8': '{}'}},
 'W05-JSON-whitespace': {'expected': 'same WORD_REJECTED; transport completes',
                         'id': 'W05-JSON-whitespace',
                         'input': 'same invalid-word candidate then JSON whitespace',
                         'intervention': {'suffix_utf8': ' \t\r\n'}},
 'W06-nonJSON-whitespace': {'expected': 'protocol rejection',
                            'id': 'W06-nonJSON-whitespace',
                            'input': 'same candidate then NBSP',
                            'intervention': {'suffix_utf8': '\xa0'}},
 'W07-Boolean-physical-row': {'expected': 'strict integer rejection',
                              'id': 'W07-Boolean-physical-row',
                              'input': 'origin.physical_keys[0][1]=false',
                              'intervention': {'path': ['origin', 'physical_keys', 0, 1],
                                               'value': False}},
 'W08-float-submission': {'expected': 'numeric token rejection',
                          'id': 'W08-float-submission',
                          'input': 'submission_index=0.0 literal token',
                          'intervention': {'path': ['submission_index'], 'raw_token': '0.0'}},
 'W09-stale-epoch': {'expected': 'binding rejection',
                     'id': 'W09-stale-epoch',
                     'input': 'replace model epoch only',
                     'intervention': {'path': ['binding', 'model_epoch'],
                                      'value': '1111111111111111111111111111111111111111111111111111111111111111'}},
 'W10-authority-wrong-Gamma': {'expected': 'fixed original declaration digest rejection',
                               'id': 'W10-authority-wrong-Gamma',
                               'input': 'coordinator test authority declares one extra original '
                                        'hypothesis',
                               'intervention': {'authority_path': ['declaration', 'ordered_Gamma'],
                                                'value': [['pred', 'A', []]]}},
 'W11-forged-checked-or-path': {'expected': 'exact-field rejection without any file import',
                                'id': 'W11-forged-checked-or-path',
                                'input': 'candidate includes checked/source_path authority fields',
                                'intervention': {'extra_fields': {'checked': True,
                                                                  'source_path': 'NONEXECUTABLE_CONTROL_SENTINEL'}}},
 'W12-second-submission': {'expected': 'one-first-submission rejection; no restart',
                           'id': 'W12-second-submission',
                           'input': 'submission_index=1',
                           'intervention': {'path': ['submission_index'], 'value': 1}},
 'W13-authority-Boolean-reserve': {'expected': 'strict authority-integer rejection',
                                   'id': 'W13-authority-Boolean-reserve',
                                   'input': 'trusted test authority '
                                            'limits.caller_finish_reserve_seconds=true',
                                   'intervention': {'authority_path': ['limits',
                                                                       'caller_finish_reserve_seconds'],
                                                    'value': True}},
 'W14-pin-mismatch': {'expected': 'byte authentication rejection before parse',
                      'id': 'W14-pin-mismatch',
                      'input': 'complete candidate bytes but expected SHA differs',
                      'intervention': {'channel': 'candidate_sha256',
                                       'value': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'}},
 'W15-response-incomplete': {'expected': 'coordinator no acceptance',
                             'id': 'W15-response-incomplete',
                             'input': 'only full body line, no completion+EOF',
                             'intervention': {'response_lines': 1}},
 'W16-late-exit-or-held-EOF': {'expected': 'coordinator UNKNOWN no prefix rescue',
                               'id': 'W16-late-exit-or-held-EOF',
                               'input': 'response bytes complete before deadline, terminal/EOF '
                                        'observed afterjoint20',
                               'intervention': {'deadline_relation': 'terminal_observed_ns >= '
                                                                     'joint_deadline_ns'}}}
BASELINE_CANDIDATE = {'authority_sha256': '0000000000000000000000000000000000000000000000000000000000000000',
 'binding': {'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
             'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe',
             'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
             'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039'},
 'commands': [{'formula': ['bot'], 'name': 'CONTROL_UNDECLARED', 'rule': 'axiom'}],
 'coordinator_invocation_id': 'CONTROL_PROTOCOL_ONLY',
 'origin': {'kind': 'producer_claimed_selected_original_target_ancestry',
            'physical_keys': [[0, 0, []]],
            'source_event_index': 0},
 'schema': 'Q-untrusted-first-candidate-word-v1',
 'submission_index': 0,
 'termination': {'full24_accepted': False,
                 'producer_status': 'CANDIDATE_NOT_VERIFIED',
                 'proof_accepted': False,
                 'root_rollback_claimed': True,
                 'trajectory_accepted': False}}


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _function_state(fn):
    _need(type(fn) is types.FunctionType, 'exact Python function')
    return (fn, fn.__code__, id(fn.__defaults__),
            tuple(id(v) for v in fn.__defaults__ or ()), id(fn.__kwdefaults__),
            tuple((k, id(v)) for k, v in sorted((fn.__kwdefaults__ or {}).items())),
            tuple((id(cell), id(cell.cell_contents)) for cell in fn.__closure__ or ()))


def _effective_state(fn):
    if type(fn) is types.MethodType:
        return ('method', fn.__self__, _function_state(fn.__func__))
    if type(fn) is types.FunctionType:
        return ('function', _function_state(fn))
    return ('native', type(fn), fn, getattr(fn, '__self__', None))


def _class_state(cls):
    result = []
    for base in cls.__mro__:
        members = tuple(sorted(vars(base).items()))
        functions = []
        for name, member in members:
            if isinstance(member, (staticmethod, classmethod)):
                member = member.__func__
            if type(member) is types.FunctionType:
                functions.append((name, _function_state(member)))
            elif type(member) is property:
                functions.append((name, tuple(_function_state(fn) if fn is not None else None
                                      for fn in (member.fget, member.fset, member.fdel))))
        result.append((base, members, tuple(functions)))
    return (cls, cls.__mro__, tuple(result))


def _module_state(module):
    members = tuple(sorted(vars(module).items()))
    functions = tuple((name, _function_state(value)) for name, value in members
                      if type(value) is types.FunctionType)
    classes = tuple((name, _class_state(value)) for name, value in members
                    if type(value) is type and value.__module__ == module.__name__)
    return (module, members, functions, classes)


def _pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def _wire_pin(record):
    _need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'trusted full Source pin')
    _need(type(record['bytes']) is int and record['bytes'] >= 0, 'literal Source size')
    return {'sha256': record['sha256'], 'bytes': record['bytes']}


def make_protocol_surface_adapter(*, coordinator_module, coordinator_source_raw,
        verifier_source_raw, checker_source_raw, fixed_authority_raw, declaration_raw,
        source_records, runtime_record, owned_output_directory, owner, source_guard,
        joint_began_ns, joint_deadline_ns, observations_sink=None):
    """Called only by a separately reviewed, cold owned controls launcher.

    Factory inputs are authenticated coordinator buffers/objects, never fixture
    or producer authority. Original data values are sealed separately from the
    legitimate evolving Owner children/samples and per-case adapter counters.
    Optional observations_sink is an initially empty trusted actual list,
    committed once with exactly the returned W01 observation; never a callback.
    The caller owns cancellation, signals, enclosing60/caller90+1 and final
    raw receipt/ledger closure. This factory never grants those qualifications.
    """
    state_fn, state_code = _function_state, _function_state.__code__
    effective_fn, effective_code = _effective_state, _effective_state.__code__
    module_fn, module_code = _module_state, _module_state.__code__
    class_fn, class_code = _class_state, _class_state.__code__
    need_fn, need_code = _need, _need.__code__
    clock = time.perf_counter_ns
    # These five original top-level helpers have no defaults/cells. Capture
    # real metadata once; never trust a changed helper to test itself.
    validator_anchors = tuple((name, fn, fn.__code__, fn.__defaults__,
        fn.__kwdefaults__, fn.__closure__) for name, fn in (
            ('_function_state', state_fn), ('_effective_state', effective_fn),
            ('_module_state', module_fn), ('_class_state', class_fn), ('_need', need_fn)))
    if observations_sink is not None and (type(observations_sink) is not list or observations_sink):
        raise ValueError('trusted initially empty actual W01 observation list only')
    sink = observations_sink
    root_guard = source_guard
    root_guard_anchor = state_fn(root_guard)
    if type(joint_began_ns) is not int or type(joint_deadline_ns) is not int:
        raise ValueError('literal original native clock integers')
    if joint_deadline_ns - joint_began_ns != 20000000000:
        raise ValueError('original20 deadline; no reset')
    if type(coordinator_module) is not types.ModuleType or type(owner) is not coordinator_module.Owner:
        raise ValueError('exact cold genuine coordinator module/Owner')
    if owner.began_ns != joint_began_ns or owner.deadline_ns != joint_deadline_ns:
        raise ValueError('genuine Owner original clock')
    if source_records != SOURCE_RECORDS or runtime_record != RUNTIME:
        raise ValueError('exact current five Source records and original runtime')
    for raw, name in ((coordinator_source_raw, 'coordinator'), (verifier_source_raw, 'verifier'),
                      (checker_source_raw, 'independent_checker')):
        if type(raw) is not bytes or _pin(raw) != _wire_pin(SOURCE_RECORDS[name]):
            raise ValueError('same complete fixed Source buffer')
    if type(fixed_authority_raw) is not bytes or len(fixed_authority_raw) > 1048576:
        raise ValueError('complete small coordinator authority buffer')
    if type(declaration_raw) is not bytes or _pin(declaration_raw) != RAW_INPUT_BINDINGS['declaration']:
        raise ValueError('unchanged complete original declaration buffer')
    own_module = sys.modules[__name__]
    own_state = module_fn(own_module)
    coordinator_state = module_fn(coordinator_module)
    owner_class = type(owner)
    owner_class_state = class_fn(owner_class)
    owner_methods = {name: effective_fn(getattr(owner, name)) for name in
                     ('check', 'launch', 'reap', 'sample', 'cleanup', 'table', 'active')}
    owner_containers = {name: getattr(owner, name) for name in
                        ('children', 'launch_attempts', 'observer_intervals', 'samples',
                         'known', 'cleanup_errors', 'leftovers')}
    helpers = {name: (getattr(coordinator_module, name), effective_fn(getattr(coordinator_module, name)))
               for name in ('decode', 'canonical', 'pin_bytes', 'digest', 'read_small',
                            'write_exclusive', 'regular_fd', 'two_lines', 'raw_peak')}
    custody = {'runner_guard': None, 'runner_guard_anchor': None,
               'busy': False, 'next_prefix': 1, 'failed': False,
               'sink_observation': None, 'sink_bytes': None}
    raw_custody = (coordinator_source_raw, verifier_source_raw, checker_source_raw,
                   fixed_authority_raw, declaration_raw)
    raw_pins = tuple(_pin(raw) for raw in raw_custody)
    source_value = coordinator_module.canonical(source_records)
    runtime_value = coordinator_module.canonical(runtime_record)
    constant_value = coordinator_module.canonical([SOURCE_RECORDS, RUNTIME, RAW_INPUT_BINDINGS,
        BINDING, LIMITS, DECLARATION_VALUE_SHA256, CASE_PROJECTION, BASELINE_CANDIDATE])
    owned_root = Path(owned_output_directory)
    if not owned_root.is_absolute() or owned_root != owned_root.resolve() or owned_root.exists():
        raise ValueError('fresh canonical owned adapter directory')
    if owner.children or owner.samples:
        raise ValueError('factory requires fresh genuine verifier-only Owner')

    def check():
        # Direct own validator and actual clock checks precede delegation.
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if time.perf_counter_ns is not clock or clock() >= joint_deadline_ns:
            raise TimeoutError('original shared20 controls deadline')
        if (state_fn(root_guard) != root_guard_anchor
                or root_guard is not root_guard_anchor[0] or root_guard.__code__ is not root_guard_anchor[1]):
            raise ValueError('original Root guard identity/code/default/cell authority changed')
        if module_fn(own_module) != own_state or module_fn(coordinator_module) != coordinator_state:
            raise ValueError('original own/coordinator namespace/class/code/default authority changed')
        if type(owner) is not owner_class or class_fn(owner_class) != owner_class_state:
            raise ValueError('original Owner class/MRO/property endpoints changed')
        for name, endpoint in owner_methods.items():
            if name in owner.__dict__ or effective_fn(getattr(owner, name)) != endpoint:
                raise ValueError('effective Owner method instance shadow or code change')
        if (owner.began_ns != joint_began_ns or owner.deadline_ns != joint_deadline_ns
                or owner.failure_ns != joint_began_ns + 55000000000
                or owner.owned_ns != joint_began_ns + 60000000000):
            raise ValueError('original Owner clock authority changed')
        for name, container in owner_containers.items():
            if getattr(owner, name) is not container:
                raise ValueError('legitimate Owner container identity changed')
        if observations_sink is not sink or (sink is not None and type(sink) is not list):
            raise ValueError('original trusted observation list identity changed')
        if sink is not None:
            expected = custody['sink_observation']
            if expected is None:
                if len(sink) != 0:
                    raise ValueError('W01 list may change only through sole actual receipt commit')
            elif (len(sink) != 1 or sink[0] is not expected
                    or coordinator_module.canonical(expected) != custody['sink_bytes']):
                raise ValueError('committed actual W01 receipt identity/value changed')
        for name, (endpoint, anchor) in helpers.items():
            if getattr(coordinator_module, name) is not endpoint or effective_fn(endpoint) != anchor:
                raise ValueError('original coordinator helper endpoint changed')
        if tuple(_pin(raw) for raw in raw_custody) != raw_pins:
            raise ValueError('fixed authenticated raw buffers changed')
        if (coordinator_module.canonical(source_records) != source_value
                or coordinator_module.canonical(runtime_record) != runtime_value
                or coordinator_module.canonical([SOURCE_RECORDS, RUNTIME, RAW_INPUT_BINDINGS,
                    BINDING, LIMITS, DECLARATION_VALUE_SHA256, CASE_PROJECTION, BASELINE_CANDIDATE]) != constant_value):
            raise ValueError('fixed Source/runtime/fixture/epoch values changed')
        root_guard()
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if state_fn(root_guard) != root_guard_anchor:
            raise ValueError('Root guard authority changed during delegation')
        runner_guard = custody['runner_guard']
        if runner_guard is not None:
            if state_fn(runner_guard) != custody['runner_guard_anchor']:
                raise ValueError('original runner callback identity/code/default/cells changed')
            runner_guard()
            for name, original, code, defaults, kwdefaults, closure in validator_anchors:
                if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                        or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                        or original.__closure__ is not closure):
                    raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
            if state_fn(runner_guard) != custody['runner_guard_anchor']:
                raise ValueError('runner callback changed during delegation')
        if time.perf_counter_ns is not clock or clock() >= joint_deadline_ns:
            raise TimeoutError('original20 after complete guards')
        owner.check()
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if effective_fn(owner.check) != owner_methods['check']:
            raise ValueError('effective owned deadline changed during call')
    check_anchor = state_fn(check)

    def call(fn, *args, **kwargs):
        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                or check is not check_anchor[0] or check.__code__ is not check_anchor[1]
                or state_fn(check) != check_anchor):
            raise ValueError('immediate live adapter check authority changed')
        check()
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if (check is not check_anchor[0] or check.__code__ is not check_anchor[1]
                or state_fn(check) != check_anchor):
            raise ValueError('live check changed during its delegated callbacks')
        anchor = effective_fn(fn)
        error = None
        try:
            value = fn(*args, **kwargs)
        except BaseException as caught:
            error = caught
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                or check is not check_anchor[0] or check.__code__ is not check_anchor[1]
                or state_fn(check) != check_anchor or effective_fn(fn) != anchor):
            raise ValueError('delegated adapter endpoint or guard authority changed')
        check()
        for name, original, code, defaults, kwdefaults, closure in validator_anchors:
            if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                    or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                    or original.__closure__ is not closure):
                raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
        if (check is not check_anchor[0] or check.__code__ is not check_anchor[1]
                or state_fn(check) != check_anchor):
            raise ValueError('live postcheck changed during delegated callbacks')
        if error is not None:
            raise error
        return value
    call_anchor = state_fn(call)
    call_fn = call

    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    authority = call_fn(coordinator_module.decode, fixed_authority_raw, 1048576)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    declaration = call_fn(coordinator_module.decode, declaration_raw, 1048576)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    _need(type(authority) is dict and set(authority) == {'schema', 'coordinator_invocation_id',
          'declaration', 'binding', 'raw_input_bindings', 'source_bindings', 'limits'}
          and authority['schema'] == 'Q-clean-verifier-fixed-authority-v1', 'entire fixed authority')
    _need(authority['declaration'] == declaration and coordinator_module.digest(declaration) ==
          DECLARATION_VALUE_SHA256, 'exact original declaration value, Gamma occurrences and target')
    _need(authority['binding'] == BINDING and authority['raw_input_bindings'] == RAW_INPUT_BINDINGS,
          'all original model/authority/registry/raw epochs')
    _need(type(authority['limits']) is dict and set(authority['limits']) == set(LIMITS)
          and all(type(authority['limits'][key]) is int for key in LIMITS)
          and authority['limits'] == LIMITS, 'original literal integer20/55/60/512/90+1 limits')
    _need(authority['source_bindings'] == {name: _wire_pin(record) for name, record in SOURCE_RECORDS.items()},
          'exact coordinator/verifier/checker/producer/point Source ledger')
    nonce = authority['coordinator_invocation_id']
    _need(type(nonce) is str and 1 <= len(nonce) <= 128 and
          all(char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for char in nonce),
          'Root-owned fixed opaque invocation')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(owned_root.mkdir, mode=0o700)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    source_dir = owned_root / 'fixed-source'
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(source_dir.mkdir, mode=0o700)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    verifier_path, checker_path = source_dir / 'verifier.py', source_dir / 'checker.py'
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(coordinator_module.write_exclusive, verifier_path, verifier_source_raw)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(coordinator_module.write_exclusive, checker_path, checker_source_raw)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(os.chmod, verifier_path, 0o400)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(os.chmod, checker_path, 0o400)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    runtime_raw = call_fn(coordinator_module.read_small, runtime_record['path'], 1048576, _wire_pin(runtime_record))
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    # Root seals actual stdlib native/file/parser endpoints too. One complete
    # runtime read authenticates the configured executable; OS replacement
    # after this boundary is outside the declared ordinary synchronous scope.
    runtime_pin = _pin(runtime_raw)
    authority_value_raw = coordinator_module.canonical(authority)

    def surface_adapter(*, request, literal_expected, joint_began_ns,
                        joint_deadline_ns, source_guard):
        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('actual immediate delegation shim changed')
        if (joint_began_ns != owner.began_ns or type(joint_began_ns) is not int
                or type(joint_deadline_ns) is not int or joint_deadline_ns != owner.deadline_ns):
            raise ValueError('same original shared native clock required')
        if custody['runner_guard'] is None:
            # Exact once-only trusted caller endpoint registration; no input
            # wire can provide this object. Never re-anchor changed authority.
            custody['runner_guard'] = source_guard
            custody['runner_guard_anchor'] = state_fn(source_guard)
        elif source_guard is not custody['runner_guard'] or state_fn(source_guard) != custody['runner_guard_anchor']:
            raise ValueError('same once-bound genuine runner callback required')
        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original immediate call shim identity/code/default/cells changed')
        ignored = call_fn(owner.check)
        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original immediate call shim identity/code/default/cells changed')
        _need(not custody['busy'] and not custody['failed'], 'no recursive/failure retry/favorable subset')
        _need(type(request) is dict and set(request) == {'case_id', 'candidate_raw', 'candidate_sha256',
             'candidate_bytes', 'unperturbed_authority_raw', 'authority_edit_control_only',
             'transport_intervention_control_only', 'authority_is_Root_owned', 'expected_Q_primary_acceptance'},
             'exact frozen protocol request; no paths/callables/checked authority')
        case_id = request['case_id']
        _need(type(case_id) is str and case_id in CASE_PROJECTION, 'frozen retained protocol case')
        case = CASE_PROJECTION[case_id]
        prefix = case_id[:3]
        _need(prefix != 'W16', 'W16 is deferred BEFORE adapter dispatch; separate expected-UNKNOWN design')
        _need(prefix == 'W%02d' % custody['next_prefix'], 'single complete frozenW01-W15 sequence, never restart')
        _need(literal_expected == case['expected'] and request['unperturbed_authority_raw'] == fixed_authority_raw
              and request['authority_is_Root_owned'] is True and request['expected_Q_primary_acceptance'] is False,
              'exact fixture expectation and unchanged authenticated authority buffer')
        custody['busy'] = True
        child = None
        open_fds = []
        began = clock()
        sample_start = len(owner.samples)
        case_dir = owned_root / prefix
        evidence = {'primary_acceptance': False, 'authority_is_fixed_Root_buffer': True,
                    'Q_payload_parses': 0, 'target_searches': 0, 'case_id': case_id,
                    'control_fixture': 'CONTROL_UNDECLARED axiom/bottom only',
                    'same_original_joint_began_ns': joint_began_ns,
                    'same_original_joint_deadline_ns': joint_deadline_ns}
        try:
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            candidate = call_fn(copy.deepcopy, BASELINE_CANDIDATE)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            candidate['coordinator_invocation_id'] = nonce
            candidate['authority_sha256'] = _pin(fixed_authority_raw)['sha256']
            intervention = case.get('intervention')
            authority_edit = intervention if prefix in ('W10', 'W13') else None
            transport_edit = intervention if prefix == 'W15' else None
            if prefix in ('W07', 'W09', 'W12'):
                parent = candidate
                for key in intervention['path'][:-1]:
                    parent = parent[key]
                parent[intervention['path'][-1]] = intervention['value']
            elif prefix == 'W11':
                candidate.update(intervention['extra_fields'])
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            raw = call_fn(coordinator_module.canonical, candidate)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if prefix == 'W02':
                raw = b'{"schema":"Q-untrusted-first-candidate-word-v1",' + raw[1:]
            elif prefix == 'W03':
                raw = raw[:-1]
            elif prefix in ('W04', 'W05', 'W06'):
                raw += intervention['suffix_utf8'].encode('utf8')
            elif prefix == 'W08':
                _need(raw.count(b'"submission_index":0') == 1, 'whole exact zero token replacement')
                raw = raw.replace(b'"submission_index":0', b'"submission_index":0.0', 1)
            expected_sha = intervention['value'] if prefix == 'W14' else _pin(raw)['sha256']
            _need(type(request['candidate_raw']) is bytes and request['candidate_raw'] == raw
                  and type(request['candidate_bytes']) is int and request['candidate_bytes'] == len(raw)
                  and request['candidate_sha256'] == expected_sha
                  and request['authority_edit_control_only'] == authority_edit
                  and request['transport_intervention_control_only'] == transport_edit,
                  'entire same literal fixture request; no target proof or favorable wire substitution')
            sent_authority = fixed_authority_raw
            if authority_edit is not None:
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                edited_authority = call_fn(copy.deepcopy, authority)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                parent = edited_authority
                for key in authority_edit['authority_path'][:-1]:
                    parent = parent[key]
                parent[authority_edit['authority_path'][-1]] = authority_edit['value']
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                sent_authority = call_fn(coordinator_module.canonical, edited_authority)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(case_dir.mkdir, mode=0o700)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            authority_path, candidate_path = case_dir / 'authority.json', case_dir / 'candidate.json'
            result_path = case_dir / 'verifier-response.jsonl'
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(coordinator_module.write_exclusive, authority_path, sent_authority)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(coordinator_module.write_exclusive, candidate_path, raw)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(os.chmod, authority_path, 0o400)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(os.chmod, candidate_path, 0o400)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            afd = call_fn(coordinator_module.regular_fd, authority_path, os.O_RDONLY)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            open_fds.append(afd)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            cfd = call_fn(coordinator_module.regular_fd, candidate_path, os.O_RDONLY)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            open_fds.append(cfd)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            sfd = call_fn(coordinator_module.regular_fd, checker_path, os.O_RDONLY)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            open_fds.append(sfd)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            rfd = call_fn(coordinator_module.regular_fd, result_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            open_fds.append(rfd)
            _need(len(set(open_fds)) == 4 and all(type(fd) is int and fd >= 3 for fd in open_fds),
                  'distinct readonly authority/candidate/checker FDs and sole outputFD')
            argv = [runtime_record['path'], '-I', '-B', str(verifier_path), str(afd),
                    _pin(sent_authority)['sha256'], str(len(sent_authority)), str(cfd), expected_sha,
                    str(len(raw)), str(sfd), str(rfd), str(joint_began_ns), str(joint_deadline_ns)]
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            child = call_fn(owner.launch, 'verifier', argv, tuple(open_fds), case_dir)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            for fd in open_fds:
                os.close(fd)
            open_fds.clear()
            # Expected verifier validation rejection exits2; Owner.wait instead
            # requires exit0. All wait4 peaks/reaping/sampling are genuine.
            while True:
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                reaped = call_fn(owner.reap, child)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                if reaped:
                    break
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                ignored = call_fn(owner.sample)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                ignored = call_fn(time.sleep, 0.01)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(owner.sample)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            _need(child['reaped'] is True and child['usage'] is not None
                  and type(child['observed_terminal_ns']) is int
                  and child['observed_terminal_ns'] < joint_deadline_ns,
                  'genuine complete timely child terminal/reap')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            stdout_raw = call_fn(coordinator_module.read_small, case_dir / 'verifier-stdout.txt', 1048576)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            stderr_raw = call_fn(coordinator_module.read_small, case_dir / 'verifier-stderr.txt', 1048576)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            response_raw = call_fn(coordinator_module.read_small, result_path, 4 * 1048576 + 1024)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            _need(not stdout_raw, 'clean verifier has no alternate stdout authority')
            evidence.update({'argv': argv, 'fixed_sources': SOURCE_RECORDS,
                'runtime': runtime_pin, 'candidate_actual_pin': _pin(raw),
                'candidate_declared_pin': {'sha256': expected_sha, 'bytes': len(raw)},
                'authority_original_pin': _pin(fixed_authority_raw), 'authority_sent_pin': _pin(sent_authority),
                'authority_edit_control_only': authority_edit, 'transport_intervention_control_only': transport_edit,
                'candidate_complete_raw_hex': raw.hex(), 'authority_sent_complete_raw_hex': sent_authority.hex(),
                'stdout_complete_raw_hex': stdout_raw.hex(), 'stderr_complete_raw_hex': stderr_raw.hex(),
                'response_complete_raw_hex': response_raw.hex(),
                'stdout_pin': _pin(stdout_raw), 'stderr_pin': _pin(stderr_raw), 'response_pin': _pin(response_raw),
                'all_three_output_files_read_to_EOF': True, 'child_exit_code': child['process'].returncode,
                'child_reaped': child['reaped'], 'child_pid': child['process'].pid,
                'observed_terminal_ns': child['observed_terminal_ns'], 'kernel_peak_bytes': child['kernel_peak_bytes'],
                'owned_samples_begin_index': sample_start, 'owned_samples_end_index': len(owner.samples),
                'coordinator_max_combined_bytes_so_far': owner.max_combined,
                'costs_are_actual_if_and_only_if_this_future_callable_completes': True,
                'observed_checker_call_count': None,
                'observed_checker_call_count_scope': 'No private checker call tape. WORD_REJECTED response is API-stage evidence; no inferred physical/math call census.'})
            if prefix in ('W01', 'W05', 'W15'):
                _need(child['process'].returncode == 0 and not stderr_raw, 'real completed verifier exit0; no alternate error')
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                parsed = call_fn(coordinator_module.two_lines, result_path,
                    'Q-clean-verifier-response-body-v1', 'Q-clean-verifier-response-completion-v1', owner)
                if (_function_state is not state_fn or state_fn.__code__ is not state_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original immediate call shim identity/code/default/cells changed')
                response, response_pin = parsed
                _need(response_pin == _pin(response_raw) and response['status'] == 'WORD_REJECTED'
                      and response['independent_word_certificate'] is None and response['ROOT_primary_accepted'] is False
                      and response['ROOT_resource_accepted'] is False and response['binding'] == BINDING
                      and response['coordinator_invocation_id'] == nonce
                      and response['authority_raw_sha256'] == _pin(sent_authority)['sha256']
                      and response['candidate_raw_sha256'] == expected_sha
                      and response['source_bindings'] == authority['source_bindings']
                      and response['joint_began_ns'] == joint_began_ns
                      and response['joint_deadline_ns'] == joint_deadline_ns,
                      'real complete fixed target-rejected response; no certificate/proof acceptance')
                _need(all(response[name] is False for name in ('actual_selected_accepted', 'point_snapshot_accepted',
                      'full24_accepted', 'full_trajectory_accepted', 'native_accepted', 'RL_accepted',
                      'induction_accepted', 'full_PA_accepted')), 'no strong scope promotion')
                evidence['verifier_status'] = response['status']
                evidence['complete_verifier_body'] = response
                observed = True
                if prefix == 'W15':
                    view = response_raw.split(b'\n', 1)[0] + b'\n'
                    view_path = case_dir / 'CONTROL_ONLY-first-body-line.jsonl'
                    if (_function_state is not state_fn or state_fn.__code__ is not state_code
                            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                            or state_fn(call_fn) != call_anchor):
                        raise ValueError('original immediate call shim identity/code/default/cells changed')
                    ignored = call_fn(coordinator_module.write_exclusive, view_path, view)
                    if (_function_state is not state_fn or state_fn.__code__ is not state_code
                            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                            or state_fn(call_fn) != call_anchor):
                        raise ValueError('original immediate call shim identity/code/default/cells changed')
                    caught = None
                    try:
                        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                                or state_fn(call_fn) != call_anchor):
                            raise ValueError('original immediate call shim identity/code/default/cells changed')
                        ignored = call_fn(coordinator_module.two_lines, view_path,
                            'Q-clean-verifier-response-body-v1', 'Q-clean-verifier-response-completion-v1', owner)
                        if (_function_state is not state_fn or state_fn.__code__ is not state_code
                                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                                or state_fn(call_fn) != call_anchor):
                            raise ValueError('original immediate call shim identity/code/default/cells changed')
                    except ValueError as error:
                        caught = {'type': type(error).__name__, 'message': str(error)}
                    observed = caught == {'type': 'ValueError', 'message': 'exact two complete JSON lines/EOF'}
                    evidence.update({'transport_view_is_control_only': True,
                        'original_complete_response_preserved': True, 'transport_view_pin': _pin(view),
                        'transport_view_complete_raw_hex': view.hex(), 'actual_receiver_exception': caught})
            else:
                _need(child['process'].returncode == 2 and not response_raw, 'actual verifier rejects before response, no prefix/certificate')
                message = stderr_raw.decode('utf8', 'strict')
                tokens = {'W02': 'duplicate JSON object key', 'W03': 'JSONDecodeError:',
                    'W04': 'whole single JSON document', 'W06': 'whole single JSON document',
                    'W07': 'literal bounded integer', 'W08': 'floating JSON token prohibited',
                    'W09': 'candidate matches authenticated coordinator context',
                    'W10': 'exact original theory/full occurrence-ordered Gamma',
                    'W11': 'exact candidate schema', 'W12': 'one first submission',
                    'W13': 'literal integer original joint/owned/caller limits',
                    'W14': 'same authenticated complete FD buffer SHA/length/EOF'}
                token = tokens[prefix]
                observed = message.endswith('\n') and token in message and message.startswith(('ValueError:', 'JSONDecodeError:'))
                evidence.update({'verifier_status': 'EARLY_TYPED_OR_PARSE_REJECTION',
                    'expected_error_token': token, 'actual_complete_exception_text': message,
                    'response_absent_after_reaped_EOF': True})
            _need(coordinator_module.canonical(authority) == authority_value_raw,
                  'fixed original authority not mutated by control views')
            observation = {'schema': 'Q-split-neutral-surface-observation-v1', 'case_id': case_id,
                'surface': 'hard-target-protocol', 'completed': True, 'observed_predicate': bool(observed),
                'expected_source': 'frozen-neutral-fixture', 'evidence': evidence,
                'original_Q_theorem_accepted': False, 'selected_accepted': False,
                'point_union_accepted': False, 'full24_accepted': False, 'trajectory_accepted': False,
                'ROOT_resource_accepted': False, 'RL_accepted': False}
            evidence['elapsed_ns_including_case_setup_terminal_receive_so_far'] = clock() - began
            evidence['partial_surface_only'] = True
            evidence['full52_qualification'] = False
            # Serialize the entire returned evidence and save an authenticated
            # whole file inside the original20, BEFORE final qualification.
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            observation_raw = call_fn(coordinator_module.canonical, observation)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            observation_path = case_dir / 'complete-surface-observation.json'
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(coordinator_module.write_exclusive, observation_path, observation_raw)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            saved = call_fn(coordinator_module.read_small, observation_path, len(observation_raw), _pin(observation_raw))
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            _need(saved == observation_raw, 'whole returned evidence serialization/read/EOF pin')
            if prefix == 'W01' and sink is not None:
                if (type(sink) is not list or len(sink) != 0
                        or custody['sink_observation'] is not None):
                    raise ValueError('sole actual W01 sink transition required')
                list.append(sink, observation)
                custody['sink_observation'] = observation
                custody['sink_bytes'] = observation_raw
            custody['next_prefix'] += 1
            custody['busy'] = False
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            ignored = call_fn(owner.check)
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original immediate call shim identity/code/default/cells changed')
            return observation
        except BaseException:
            custody['failed'] = True
            custody['busy'] = False
            if (prefix == 'W01' and sink is not None
                    and custody['sink_observation'] is not None):
                if type(sink) is list and len(sink) == 1 and sink[0] is custody['sink_observation']:
                    list.pop(sink)
                    custody['sink_observation'] = None
                    custody['sink_bytes'] = None
                else:
                    raise ValueError('failed W01 sink cannot be silently replaced or resealed')
            # Failure reserve permits only kill/reap/evidence, never proof or a
            # late successful control. Same Source method remains authenticated.
            for fd in open_fds:
                try:
                    os.close(fd)
                except OSError:
                    pass
            for name, original, code, defaults, kwdefaults, closure in validator_anchors:
                if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                        or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                        or original.__closure__ is not closure):
                    raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or effective_fn(owner.cleanup) != owner_methods['cleanup']):
                raise ValueError('original failure cleanup endpoint changed')
            owner.cleanup()
            for name, original, code, defaults, kwdefaults, closure in validator_anchors:
                if (own_module.__dict__.get(name) is not original or original.__code__ is not code
                        or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                        or original.__closure__ is not closure):
                    raise ValueError('original immediate helper identity/code/default/kwdefault/closure changed')
            if (_function_state is not state_fn or state_fn.__code__ is not state_code
                    or effective_fn(owner.cleanup) != owner_methods['cleanup']):
                raise ValueError('cleanup endpoint changed during failure reserve')
            raise
    # The caller seals this returned function and current module code/effective
    # endpoints before neutralRunner invokes it; no new scope/admission exists.
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    ignored = call_fn(owner.check)
    if (_function_state is not state_fn or state_fn.__code__ is not state_code
            or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
            or state_fn(call_fn) != call_anchor):
        raise ValueError('original immediate call shim identity/code/default/cells changed')
    return surface_adapter
