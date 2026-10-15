"""UNEXECUTED isolated exact-helper controls; no Q/project module execution.

argv6: request_fd request_sha request_bytes result_fd joint_began_ns joint_deadline_ns.
The enclosing reviewed caller owns the original early global begin and all
process/EOF/terminal/resource acceptance. This worker grants no such authority.
"""
import ast
import builtins
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import struct
import sys
import time
import types

VERSION = 'Q-isolated-clock-projection-controls-Source-v1'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
HELPER_AST_SHA = '264c5c2ab7ed0b46830c989c9a564f8b5761b6c7125906391865230785c3fc76'
HELPERS = {
 'bootstrap': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_untrusted_producer_bootstrap_global_clock_v3.py', 'sha256': '5232e8cd3b5763b16e11a092638231234abb4962424ab1026bb7363d7572cb1e', 'bytes': 18802},
 'runner': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_split_neutral_controls_runner_global_clock_v3.py', 'sha256': 'b64e50d800e74c4c0622f78c153a7a7d058c9036d351af1dfa030e4075d65590', 'bytes': 38113},
 'verifier': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba', 'bytes': 48584}}
ORACLE = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clock-projection-oracle-source-20261015/projection_binary64_oracle_v1.py', 'sha256': 'c25bd8d35422a5cb5278f85bcfeb82e0f58cf1df44ea4098d101231c92a3b393', 'bytes': 14789}
RUNTIME = {'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9', 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 'bytes': 102352}
SCALARS = ('global_deadline_ns', 'producer_pair', 'local_before', 'global_after', 'remaining_ns',
 'local_lower', 'numerator', 'denominator', 'bound_numerator', 'bound_denominator',
 'local_deadline', 'local_began', 'deadline_numerator', 'deadline_denominator', 'final_global')
LIMITS = {'joint_ns': 20000000000, 'failure_ns': 55000000000, 'owned_seconds': 60,
 'worker_bytes': 524288000, 'aggregate_owned_bytes': 536870912, 'caller_seconds': 90, 'finish_seconds': 1}
CAP = 1048576
HARNESS_MUTANTS = ('missing-return', 'duplicate-return', 'foreign-code', 'foreign-globals',
 'default-entry-record-mismatch', 'callback-record-mismatch', 'profiler-not-restored', 'late-post-profile')


def need(value, message):
    if value is not True:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def function_state(fn):
    if type(fn) is not types.FunctionType:
        raise ValueError('exact Python endpoint')
    defaults, keywords = fn.__defaults__, fn.__kwdefaults__
    if keywords is not None and (type(keywords) is not dict or not all(type(k) is str for k in keywords)):
        raise ValueError('exact keyword-default names')
    return (fn, fn.__code__, id(defaults), defaults,
        tuple((id(v), v) for v in defaults or ()), id(keywords), keywords,
        tuple((k, id(v), v) for k, v in sorted((keywords or {}).items())),
        tuple((cell, id(cell.cell_contents), cell.cell_contents) for cell in fn.__closure__ or ()))


def data_state(value):
    if type(value) is dict:
        return ('dict', tuple((k, data_state(v)) for k, v in sorted(value.items())))
    if type(value) in (tuple, list):
        return (type(value), tuple(data_state(v) for v in value))
    if type(value) in (set, frozenset):
        return (type(value), frozenset(data_state(v) for v in value))
    if type(value) is float:
        return (float, value.hex())
    if value is None or type(value) in (bool, int, str, bytes):
        return (type(value), value)
    return ('identity', id(value), value)


def class_state(cls):
    rows = []
    for base in cls.__mro__:
        for name, descriptor in sorted(vars(base).items()):
            if type(descriptor) is types.FunctionType:
                row = function_state(descriptor)
            elif type(descriptor) in (staticmethod, classmethod) and type(descriptor.__func__) is types.FunctionType:
                row = (descriptor, function_state(descriptor.__func__))
            elif type(descriptor) is property:
                row = (descriptor, tuple(None if fn is None else function_state(fn)
                                         for fn in (descriptor.fget, descriptor.fset, descriptor.fdel)))
            else:
                row = (id(descriptor), descriptor)
            rows.append((base, name, row))
    return cls, cls.__mro__, tuple(rows)


def module_state(module):
    rows = []
    for name, value in sorted(vars(module).items()):
        if type(value) is types.FunctionType:
            state = function_state(value)
        elif type(value) is type and value.__module__ == module.__name__:
            state = class_state(value)
        elif name == '__builtins__':
            mapping = vars(value) if type(value) is types.ModuleType else value
            state = tuple((k, id(v), v) for k, v in sorted(mapping.items()))
        elif type(value) in (dict, tuple, list, set, frozenset, str, bytes, int, bool, float) or value is None:
            # sys.modules and other changing native data are recorded separately
            # by registry identity. Only authored modules' constants are deep.
            state = data_state(value) if vars(module) is globals() or module.__name__.startswith('_Q_projection_') else (id(value), value)
        else:
            state = (id(value), value)
        rows.append((name, state))
    return module, type(module), tuple(rows)


class Guard:
    __slots__ = ('clock', 'clock_id', 'perf', 'setprofile', 'getprofile', 'usage', 'began', 'deadline',
                 'validators', 'modules', 'states', 'registry', 'buffers', 'entry', 'entry_code', 'sealed')
    def __setattr__(self, name, value):
        if getattr(self, 'sealed', False):
            raise ValueError('immutable control authority')
        object.__setattr__(self, name, value)

    def __init__(self, modules, buffers, began, deadline):
        self.clock, self.clock_id, self.perf = time.clock_gettime_ns, time.CLOCK_MONOTONIC, time.perf_counter
        self.setprofile, self.getprofile, self.usage = sys.setprofile, sys.getprofile, resource.getrusage
        need(type(self.clock_id) is int and type(self.clock) is types.BuiltinFunctionType, 'native global clock')
        self.began, self.deadline = began, deadline
        self.validators = tuple((fn, fn.__code__, function_state(fn)) for fn in
            (need, canonical, function_state, data_state, class_state, module_state, scalar_wire, validate_envelope))
        self.modules = tuple(modules)
        self.states = tuple(module_state(module) for module in self.modules)
        self.registry = tuple((name, id(value), value) for name, value in sorted(sys.modules.items()))
        self.buffers = tuple((raw, hashlib.sha256(raw).digest()) for raw in buffers)
        self.entry, self.entry_code = Guard.check, Guard.check.__code__
        self.sealed = True

    def check(self, *, cleanup=False):
        # Original entry/validator code and native identities BEFORE delegation.
        if (Guard.check is not self.entry or self.entry.__code__ is not self.entry_code
                or time.clock_gettime_ns is not self.clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != self.clock_id or time.perf_counter is not self.perf
                or sys.setprofile is not self.setprofile or sys.getprofile is not self.getprofile
                or resource.getrusage is not self.usage):
            raise RuntimeError('control authority/native endpoint changed')
        for fn, code, state in self.validators:
            if globals().get(fn.__name__) is not fn or fn.__code__ is not code:
                raise RuntimeError('original validator/caller binding changed')
        for fn, code, state in self.validators:
            if function_state(fn) != state:
                raise RuntimeError('original validator default-entry/cell changed')
        if tuple(module_state(module) for module in self.modules) != self.states:
            raise RuntimeError('complete Source/native/global/builtin/default/MRO state changed')
        if tuple((name, id(value), value) for name, value in sorted(sys.modules.items())) != self.registry:
            raise RuntimeError('original module registry changed')
        if any(hashlib.sha256(raw).digest() != sha for raw, sha in self.buffers):
            raise RuntimeError('authenticated immutable Source bytes changed')
        now = self.clock(self.clock_id)
        if type(now) is not int or now < self.began or now >= self.began + (LIMITS['failure_ns'] if cleanup else LIMITS['joint_ns']):
            raise TimeoutError('original global control interval expired')
        if self.usage(resource.RUSAGE_SELF).ru_maxrss >= LIMITS['worker_bytes']:
            raise TimeoutError('original control worker memory reserve exceeded')


def gate(guard, *, cleanup=False):
    fn, code = guard.entry, guard.entry_code
    if Guard.check is not fn or fn.__code__ is not code:
        raise RuntimeError('original direct guard caller changed')
    fn(guard, cleanup=cleanup)


def scalar_wire(value):
    if value is None:return {'kind': 'none'}
    if type(value) is bool:return {'kind': 'bool', 'value': value}
    if type(value) is int:return {'kind': 'int', 'value': value}
    if type(value) is float and math.isfinite(value):
        return {'kind': 'float', 'hex': float.hex(value), 'ratio': list(float.as_integer_ratio(value))}
    raise RuntimeError('declared immutable finite scalar only')


def validate_envelope(row, deadline):
    need(type(row) is dict and row['call_count'] == row['return_count'] == 1
         and row['same_frame'] is True and row['code_matches'] is True and row['globals_match'] is True
         and row['arguments_match'] is True and row['custody_intact'] is True
         and row['callback_intact'] is True and row['profile_restored'] is True
         and type(row['post_profile_ns']) is int and row['post_profile_ns'] < deadline,
         'complete actual profile/custody/original-deadline envelope')


def profiled_call(function, kwargs, guard):
    gate_fn, gate_code, gate_state = gate, gate.__code__, function_state(gate)
    state_fn, state_code, state_state = function_state, function_state.__code__, function_state(function_state)
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    code, namespace, original = function.__code__, function.__globals__, function_state(function)
    expected_deadline, expected_mode = kwargs['global_deadline_ns'], kwargs.get('producer_pair', False)
    state = {'call_count': 0, 'return_count': 0, 'frame_id': None, 'captured': {}, 'returned': None}
    def profile(frame, event, argument):
        if frame.f_code is not code:return
        if frame.f_globals is not namespace:raise RuntimeError('foreign target globals')
        if event == 'call':
            if state['call_count'] or state['return_count']:raise RuntimeError('duplicate/nested target call')
            if (frame.f_locals['global_deadline_ns'] is not expected_deadline
                    or frame.f_locals['producer_pair'] is not expected_mode):
                raise RuntimeError('profile target arguments differ')
            state['frame_id'] = id(frame)
            state['call_count'] = 1
        elif event == 'return':
            if state['call_count'] != 1 or state['return_count'] or state['frame_id'] != id(frame):
                raise RuntimeError('missing/duplicate/foreign target return')
            copied = {}
            for name in SCALARS:
                if name in frame.f_locals:
                    value = frame.f_locals[name]
                    negative_string = (name == 'global_deadline_ns' and type(value) is str
                        and value is expected_deadline and len(value) <= 128)
                    if value is not None and type(value) not in (int, bool, float) and not negative_string:
                        raise RuntimeError('nonscalar observed local')
                    copied[name] = value
            state['captured'] = copied
            state['returned'] = argument
            state['return_count'] = 1
    profile_state = function_state(profile)
    setprofile, getprofile = guard.setprofile, guard.getprofile
    prior = getprofile()
    need(prior is None, 'fresh single-thread worker has no previous profiler')
    result, error = None, None
    try:
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
            raise RuntimeError('original direct guard/state caller authority changed')
        if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
            raise RuntimeError('original direct guard/state default-entry/cell changed')
        gate_fn(guard)
        need(function_state(profile) == profile_state and function_state(function) == original, 'exact callback/helper before profile')
        setprofile(profile)
        need(getprofile() is profile, 'exact installed callback')
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
            raise RuntimeError('original direct guard/state caller authority changed')
        if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
            raise RuntimeError('original direct guard/state default-entry/cell changed')
        gate_fn(guard)
        try:
            result = function(**kwargs)
        except (ValueError, TimeoutError) as failure:
            error = {'type': type(failure).__name__, 'message': str(failure)}
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
            raise RuntimeError('original direct guard/state caller authority changed')
        if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
            raise RuntimeError('original direct guard/state default-entry/cell changed')
        gate_fn(guard)
        # Callback failures unset the profiler; never relabel them as helper rejection.
        need(getprofile() is profile, 'callback remained installed across actual helper')
        need(function_state(profile) == profile_state and function_state(function) == original, 'actual callback/helper after return')
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
            raise RuntimeError('original direct guard/state caller authority changed')
        if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
            raise RuntimeError('original direct guard/state default-entry/cell changed')
        gate_fn(guard)
    finally:
        # Restore exact original profiler even when the callback itself failed.
        endpoints_intact = sys.setprofile is setprofile and sys.getprofile is getprofile
        setprofile(prior)
        restored = getprofile() is prior
        if not endpoints_intact or not restored:
            raise RuntimeError('original profiler was not restored')
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    need(function_state(profile) == profile_state and function_state(function) == original, 'callback/helper custody after restoration')
    envelope = {'call_count': state['call_count'], 'return_count': state['return_count'],
        'same_frame': state['frame_id'] is not None, 'code_matches': True, 'globals_match': True,
        'arguments_match': True, 'custody_intact': True, 'callback_intact': True,
        'profile_restored': getprofile() is prior, 'post_profile_ns': guard.clock(guard.clock_id)}
    validate_envelope(envelope, guard.deadline)
    if error is None:
        need(type(result) is tuple and len(result) == 2 and state['returned'] is result
             and set(state['captured']) == set(SCALARS), 'actual complete successful helper return')
    else:
        need(state['returned'] is None, 'actual exception return hook has no successful value')
    return envelope, state['captured'], result, error


def raw_file(record, maximum=CAP):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}
         and type(record['bytes']) is int and 0 < record['bytes'] <= maximum, 'complete bounded raw pin')
    path = Path(record['path'])
    need(path.is_absolute() and str(path) == str(path.resolve()) and not path.is_symlink(), 'canonical original Source path')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        raw = os.read(fd, maximum + 1)
        need(os.read(fd, 1) == b'', 'whole raw EOF')
        after = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'same complete Source descriptor')
        need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'], 'whole Source SHA/length')
        return raw
    finally:os.close(fd)


def decode(raw):
    def unique(pairs):
        value = {}
        for k, v in pairs:
            need(k not in value, 'duplicate input key'); value[k] = v
        return value
    def reject(token):raise ValueError('no floating/nonfinite metadata token')
    return json.loads(raw.decode('utf8'), object_pairs_hook=unique, parse_float=reject, parse_constant=reject)


def inventory():
    native = []
    for role in sorted(HELPERS):
        for pair in (False, True):native.append({'id': role + '-normal-' + ('producer' if pair else 'checker'), 'role': role, 'kind': 'normal', 'pair': pair})
        for label in ('deadline-bool', 'deadline-float', 'deadline-str', 'deadline-negative', 'deadline-large',
                      'pair-nonbool', 'nonnative-global', 'nonnative-local', 'nonnative-nextafter', 'nonnative-finite',
                      'nonnative-ratio', 'clock-id-bool', 'clock-id-wrong', 'expired', 'foreign'):
            native.append({'id': role + '-' + label, 'role': role, 'kind': label, 'pair': False})
    return native


def load_modules(raws, invocation):
    modules, functions = [], {}
    for role in sorted(HELPERS):
        tree = ast.parse(raws[role], filename=HELPERS[role]['path'])
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'project_local_float_deadline']
        need(len(nodes) == 1 and hashlib.sha256(ast.dump(nodes[0], include_attributes=False).encode()).hexdigest() == HELPER_AST_SHA,
             'exact identical unchanged helper FunctionDef AST')
        name = '_Q_projection_' + invocation + '_' + role
        need(name not in sys.modules, 'fresh registered control-only helper namespace')
        module = types.ModuleType(name); module.__file__ = HELPERS[role]['path']
        module.__dict__.update(time=time, math=math, types=types, __builtins__=dict(vars(builtins)))
        sys.modules[name] = module
        # Only the authenticated identical FunctionDef, never the parent module.
        exec(compile(ast.Module(body=nodes, type_ignores=[]), HELPERS[role]['path'], 'exec'), module.__dict__)
        functions[role] = module.project_local_float_deadline; modules.append(module)
    name = '_Q_projection_' + invocation + '_oracle'
    need(name not in sys.modules, 'fresh exact Root pure oracle namespace')
    module = types.ModuleType(name); module.__file__ = ORACLE['path']
    original_import = builtins.__import__
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        need(level == 0 and name == 'struct', 'oracle may import only declared struct')
        return original_import(name, globals, locals, fromlist, level)
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=imports)
    sys.modules[name] = module
    exec(compile(raws['oracle'], ORACLE['path'], 'exec'), module.__dict__)
    need(module.VERSION == 'Q-isolated-projection-binary64-oracle-Source-v1', 'exact oracle version')
    modules.append(module)
    return modules, functions, module


def main(argv):
    gate_fn, gate_code, gate_state = gate, gate.__code__, function_state(gate)
    state_fn, state_code, state_state = function_state, function_state.__code__, function_state(function_state)
    need(type(argv) is list and len(argv) == 6 and all(type(v) is str for v in argv), 'literal inherited argv6')
    request_fd, request_sha, request_size, result_fd, began, deadline = argv
    need(all(v.isascii() and v.isdecimal() and (v == '0' or not v.startswith('0')) for v in
             (request_fd, request_size, result_fd, began, deadline)), 'canonical decimal interface')
    request_fd, request_size, result_fd, began, deadline = map(int, (request_fd, request_size, result_fd, began, deadline))
    clock, clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
    need(type(clock_id) is int and 0 <= began < deadline < (1 << 63) and deadline - began == LIMITS['joint_ns'], 'mandatory original global interval')
    need(began <= clock(clock_id) < deadline and 3 <= request_fd != result_fd and result_fd >= 3 and 0 < request_size <= CAP, 'original early budget and distinct FDs')
    need(fcntl.fcntl(request_fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY
         and fcntl.fcntl(result_fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_WRONLY
         and stat.S_ISREG(os.fstat(request_fd).st_mode) and os.lseek(request_fd, 0, os.SEEK_CUR) == 0,
         'owned readonly offset0 request and writeonly output')
    raw = os.read(request_fd, CAP + 1)
    need(os.read(request_fd, 1) == b'' and len(raw) == request_size and hashlib.sha256(raw).hexdigest() == request_sha, 'complete request SHA/EOF')
    request = decode(raw)
    need(type(request) is dict and set(request) == {'schema', 'invocation_id', 'worker_source', 'helper_sources',
        'oracle_source', 'runtime', 'reviews', 'preregistration', 'raw_closure'}, 'strict Root request9')
    need(request['schema'] == 'ROOT-Q-isolated-clock-projection-controls-request-v1'
         and request['helper_sources'] == HELPERS and request['oracle_source'] == ORACLE
         and request['runtime'] == RUNTIME and str(Path(sys.executable).resolve()) == RUNTIME['path'],
         'exact current helper/oracle sources and pinned runtime')
    invocation = request['invocation_id']
    need(type(invocation) is str and 1 <= len(invocation) <= 64 and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in invocation), 'bounded Root invocation')
    need(request['worker_source']['path'] == __file__, 'actual caller-compiled worker provenance')
    records = dict(HELPERS, oracle=ORACLE, worker=request['worker_source'])
    raws = {role: raw_file(record) for role, record in records.items()}
    need(set(request['reviews']) == {'worker', 'oracle'}, 'genuine new Source reviews')
    for role in ('worker', 'oracle'):
        review = decode(raw_file(request['reviews'][role]))
        need(review['source'] == records[role] and review['source_only'] is True and review['source_review_passed'] is True
             and review['all_checks_passed'] is True and type(review['scientific_calls']) is int and review['scientific_calls'] == 0
             and review['author_identity'] != review['reviewer_identity'], 'genuine distinct current Source review')
        need(review['scope'] == {'worker': 'Q-isolated-clock-projection-controls-Source',
             'oracle': 'Q-isolated-projection-binary64-oracle-Source'}[role], 'exact consumed Source review scope')
        raw_file(review['source_contract'])
    prereg = decode(raw_file(request['preregistration']))
    need(prereg['schema'] == 'ROOT-Q-isolated-clock-projection-controls-preregistration-v1'
         and prereg['author_identity'] == '/root' and prereg['invocation_id'] == invocation
         and prereg['worker_source'] == records['worker'] and prereg['oracle_source'] == ORACLE
         and prereg['helper_sources'] == HELPERS and prereg['limits'] == LIMITS
         and prereg['inventory'] == inventory() and prereg['controls_execution_authorized'] is True,
         'genuine Root scoped controls authorization, no circular future disposition')
    need(type(request['raw_closure']) is list and len(request['raw_closure']) <= 64, 'bounded named raw closure')
    required = list(records.values()) + list(request['reviews'].values()) + [request['preregistration'], request['runtime']]
    need(all(record in request['raw_closure'] for record in required), 'complete named raw closure')
    for record in request['raw_closure']:raw_file(record)
    modules, functions, oracle = load_modules(raws, invocation)
    native = (time, math, sys, types, builtins, json, json.decoder, json.encoder, json.scanner,
              struct, hashlib, os, resource)
    guard = Guard(tuple(modules) + (sys.modules[__name__],) + native, tuple(raws.values()), began, deadline)
    results, first_good = [], None
    for case in inventory():
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
            raise RuntimeError('original direct guard/state caller authority changed')
        if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
            raise RuntimeError('original direct guard/state default-entry/cell changed')
        gate_fn(guard)
        kind = case['kind']; kwargs = {'global_deadline_ns': deadline, 'producer_pair': case['pair']}
        bad_deadlines = {'deadline-bool': True, 'deadline-float': 1.0, 'deadline-str': '1', 'deadline-negative': -1, 'deadline-large': 1 << 63}
        if kind in bad_deadlines:kwargs['global_deadline_ns'] = bad_deadlines[kind]
        elif kind == 'pair-nonbool':kwargs['producer_pair'] = 0
        elif kind.startswith('nonnative-'):
            kwargs[{'nonnative-global':'_global_clock', 'nonnative-local':'_local_clock', 'nonnative-nextafter':'_nextafter', 'nonnative-finite':'_finite', 'nonnative-ratio':'_ratio'}[kind]] = None
        elif kind == 'clock-id-bool':kwargs['_clock_id'] = True
        elif kind == 'clock-id-wrong':kwargs['_clock_id'] = guard.clock_id + 1
        elif kind == 'expired':kwargs['global_deadline_ns'] = began
        elif kind == 'foreign':kwargs['global_deadline_ns'] = deadline + LIMITS['joint_ns']
        envelope, captured, returned, error = profiled_call(functions[case['role']], kwargs, guard)
        captured_wire = {k: ({'kind': 'negative-string', 'value': v} if type(v) is str
            and k == 'global_deadline_ns' and kind == 'deadline-str' else scalar_wire(v))
            for k, v in captured.items()}
        row = dict(case, envelope=envelope, captured_present=captured_wire, exception=error)
        if kind == 'normal':
            need(error is None, 'normal finite projection unavailable: UNKNOWN, no partial success')
            observation = {'case_id': case['id'], 'global_deadline_ns': deadline, 'producer_pair': case['pair'],
                'captured': row['captured_present'], 'returned': [scalar_wire(v) for v in returned]}
            if (function_state is not state_fn or state_fn.__code__ is not state_code
                    or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                    or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
                raise RuntimeError('original direct guard/state caller authority changed')
            if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
                raise RuntimeError('original direct guard/state default-entry/cell changed')
            gate_fn(guard)
            certificate = oracle.audit_observation(observation)
            if (function_state is not state_fn or state_fn.__code__ is not state_code
                    or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                    or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
                raise RuntimeError('original direct guard/state caller authority changed')
            if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
                raise RuntimeError('original direct guard/state default-entry/cell changed')
            gate_fn(guard)
            row['post_oracle_ns'] = guard.clock(guard.clock_id)
            need(certificate['passed'] is True, 'independent whole scalar oracle')
            row.update(observation=observation, oracle_certificate=certificate)
            if first_good is None:first_good = copy.deepcopy(envelope)
        else:
            expected_error = 'TimeoutError' if kind in ('expired', 'foreign') else 'ValueError'
            need(error is not None and error['type'] == expected_error, 'actual unchanged helper expected input/time rejection')
        row['passed'] = True; results.append(row)
    mechanics = []
    for name in HARNESS_MUTANTS:
        changed = copy.deepcopy(first_good)
        if name == 'missing-return':changed['return_count'] = 0
        elif name == 'duplicate-return':changed['return_count'] = 2
        elif name == 'foreign-code':changed['code_matches'] = False
        elif name == 'foreign-globals':changed['globals_match'] = False
        elif name == 'default-entry-record-mismatch':changed['custody_intact'] = False
        elif name == 'callback-record-mismatch':changed['callback_intact'] = False
        elif name == 'profiler-not-restored':changed['profile_restored'] = False
        else:changed['post_profile_ns'] = deadline
        rejected = False
        try:validate_envelope(changed, deadline)
        except ValueError:rejected = True
        need(rejected, 'declared control-only mutated envelope rejected')
        mechanics.append({'case_id': name, 'rejected': rejected, 'scope': 'mutated record validator only, not a live native/default/callback mutation'})
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    numerical = oracle.run_numerical_controls()
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    need(numerical['passed'] is True and numerical['case_count'] == 26
         and len(numerical['rows']) == 26 and all(row['passed'] is True for row in numerical['rows']), 'whole fixed separate numerical inventory')
    body = {'schema': 'Q-isolated-clock-projection-controls-body-v1', 'version': VERSION, 'CLOCK_DOMAIN': CLOCK_DOMAIN,
        'invocation_id': invocation, 'joint_began_ns': began, 'joint_deadline_ns': deadline,
        'completed': True, 'all_checks_passed': True, 'helper_sources': HELPERS, 'helper_AST_sha256': HELPER_AST_SHA,
        'native_helper_results': results, 'native_case_count': len(results), 'harness_record_negatives': mechanics,
        'pure_numerical_controls': numerical, 'profiler_restored': sys.getprofile() is None,
        'proof_accepted': False, 'model_accepted': False, 'full_pipeline_fit_accepted': False,
        'full52_qualified': False, 'W16_accepted': False, 'ROOT_resource_accepted': False,
        'ROOT_primary_accepted': False, 'original_Q_theorem_accepted': False,
        'full_architecture_qualified': False, 'full24_accepted': False,
        'native_accepted': False, 'RL_accepted': False}
    need(len(results) == 51 and len(mechanics) == 8 and body['profiler_restored'] is True, 'complete fixed controls inventory')
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    body_raw = canonical(body) + b'\n'
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    need(len(body_raw) <= CAP, 'whole complete body cap, no truncation')
    trailer = canonical({'schema': 'Q-isolated-clock-projection-controls-completion-v1',
        'body_sha256': hashlib.sha256(body_raw).hexdigest(), 'body_bytes': len(body_raw),
        'exit_zero_and_caller_deadline_required': True}) + b'\n'
    need(len(trailer) <= 1024, 'whole completion cap')
    for raw in (body_raw, trailer):
        offset = 0
        while offset < len(raw):
            if (function_state is not state_fn or state_fn.__code__ is not state_code
                    or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                    or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
                raise RuntimeError('original direct guard/state caller authority changed')
            if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
                raise RuntimeError('original direct guard/state default-entry/cell changed')
            gate_fn(guard)
            wrote = os.write(result_fd, raw[offset:offset+65536])
            if (function_state is not state_fn or state_fn.__code__ is not state_code
                    or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
                    or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
                raise RuntimeError('original direct guard/state caller authority changed')
            if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
                raise RuntimeError('original direct guard/state default-entry/cell changed')
            gate_fn(guard)
            need(type(wrote) is int and wrote > 0, 'complete output progress'); offset += wrote
    os.close(result_fd)
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None
            or state_fn.__closure__ is not None or gate is not gate_fn or gate_fn.__code__ is not gate_code):
        raise RuntimeError('original direct guard/state caller authority changed')
    if state_fn(gate_fn) != gate_state or state_fn(state_fn) != state_state:
        raise RuntimeError('original direct guard/state default-entry/cell changed')
    gate_fn(guard)
    return 0


if __name__ == '__main__':
    try:raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error)[:2048] + '\n')
        raise SystemExit(2)
