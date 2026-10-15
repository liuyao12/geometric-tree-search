"""UNEXECUTED untrusted child bootstrap, ten-argument inherited-FD interface.

All output is untrusted. Coordinator alone supplies immutable read-only buffers,
owns processes/clock/aggregate memory/output EOF, and obtains proof authority in
the separate fresh verifier. No project import or producer checker is used.
"""
import builtins
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import sys
import time
import types

VERSION = 'Q-untrusted-producer-bootstrap-Source-v3-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'

MANIFEST_SCHEMA = 'Q-untrusted-producer-bootstrap-manifest-v1'
SOURCE_PINS = {
    'codec': {'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df', 'bytes': 5806},
    'point_graph': {'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567', 'bytes': 28531},
    'producer': {'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36', 'bytes': 20219}}
PREPARATION = {'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a', 'bytes': 38376960}
BINDING = {'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
    'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
    'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039',
    'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe'}
ALLOWED_IMPORTS = {'__future__', 'copy', 'gzip', 'hashlib', 'json', 'math', 'pathlib',
                   'resource', 'time', 'dataclasses', 'typing'}


def need(value, message):
    if not value:
        raise ValueError(message)


def decimal(text):
    need(type(text) is str and text and len(text) <= 32
         and all(c in '0123456789' for c in text), 'literal nonnegative decimal argument')
    value = int(text)
    need(value <= (1 << 63) - 1, 'signed64 interface integer')
    return value


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


class Budget:
    """Native untrusted guidance; exact integer-ns coordinator clock is authoritative."""
    def __init__(self, began_ns, deadline_ns):
        need(type(began_ns) is int and type(deadline_ns) is int
             and deadline_ns - began_ns == 20000000000, 'same original joint20e9 ns')
        self._clock, self._clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
        self._local_clock = time.perf_counter
        need(type(self._clock_id) is int and type(self._clock) is types.BuiltinFunctionType
             and type(self._local_clock) is types.BuiltinFunctionType, 'original native global/local clock endpoints')
        self.began_ns, self.deadline_ns = began_ns, deadline_ns
        self.check()

    def check(self, *, cleanup=False):
        if (time.clock_gettime_ns is not self._clock or time.CLOCK_MONOTONIC is not self._clock_id
                or type(self._clock_id) is not int or time.perf_counter is not self._local_clock):
            raise ValueError('original bootstrap global/local clock endpoint changed')
        now = self._clock(self._clock_id)
        if (time.clock_gettime_ns is not self._clock or time.CLOCK_MONOTONIC is not self._clock_id
                or time.perf_counter is not self._local_clock or type(now) is not int or now < self.began_ns):
            raise ValueError('bootstrap global clock custody/domain changed')
        if now - self.began_ns >= 55000000000 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 524288000:
            raise TimeoutError('bootstrap failure55/500 reserve exceeded')
        if not cleanup and now >= self.deadline_ns:
            raise TimeoutError('coordinator joint20 unfinished')


def fd_mode(fd, *, writable=False):
    need(type(fd) is int and fd >= 3, 'explicit inherited descriptor, not stdio')
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    need((flags & os.O_ACCMODE) == (os.O_WRONLY if writable else os.O_RDONLY),
         'result write-only and immutable inputs read-only')
    if not writable:
        need(stat.S_ISREG(os.fstat(fd).st_mode) and os.lseek(fd, 0, os.SEEK_CUR) == 0,
             'coordinator snapshot regular input at complete offset0')


def read_exact(fd, record, budget):
    need(type(record) is dict and set(record) == {'sha256', 'bytes'}
         and type(record['bytes']) is int and record['bytes'] >= 0
         and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(c in '0123456789abcdef' for c in record['sha256']), 'exact buffer digest/length')
    budget.check()
    before = os.fstat(fd)
    need(before.st_size == record['bytes'], 'whole regular input length, no prefix')
    data = bytearray()
    digest = hashlib.sha256()
    while len(data) < record['bytes']:
        budget.check()
        block = os.read(fd, min(65536, record['bytes'] - len(data)))
        need(block, 'complete authenticated input, no early EOF')
        data.extend(block)
        digest.update(block)
    need(os.read(fd, 1) == b'', 'complete single input EOF')
    after = os.fstat(fd)
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
         'coordinator-owned snapshot unchanged while read')
    need(digest.hexdigest() == record['sha256'], 'whole input SHA, no subset')
    budget.check()
    result = bytes(data)
    del data
    return result


def unique(pairs):
    value = {}
    for name, child in pairs:
        need(name not in value, 'duplicate manifest field')
        value[name] = child
    return value


def parse_manifest(raw):
    need(type(raw) is bytes and len(raw) <= 1048576, 'manifest complete maximum1MiB')
    def reject(token):
        raise ValueError('nonfinite manifest token: ' + token)
    value = json.loads(raw.decode('utf8'), object_pairs_hook=unique, parse_constant=reject)
    need(type(value) is dict and set(value) == {'schema', 'coordinator_invocation_id', 'authority_sha256',
        'declaration', 'binding', 'original_source_bindings', 'source_bindings', 'event_directory'}, 'strict manifest8 fields')
    need(value['schema'] == MANIFEST_SCHEMA and value['binding'] == BINDING, 'exact original model/manifest schema')
    invocation = value['coordinator_invocation_id']
    need(type(invocation) is str and 1 <= len(invocation) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in invocation), 'coordinator invocation ASCII')
    authority = value['authority_sha256']
    need(type(authority) is str and len(authority) == 64
         and all(c in '0123456789abcdef' for c in authority), 'opaque coordinator authority digest')
    need(type(value['source_bindings']) is dict and set(value['source_bindings']) == {'bootstrap', 'codec', 'point_graph', 'producer'},
         'exact executable source4 manifest binding')
    for role, record in SOURCE_PINS.items():
        need(value['source_bindings'][role] == record, 'literal pinned Source ' + role)
    own = Path(__file__).read_bytes()
    need(value['source_bindings']['bootstrap'] == {'sha256': hashlib.sha256(own).hexdigest(), 'bytes': len(own)},
         'coordinator-invoked bootstrap Source record')
    del own
    need(type(value['declaration']) is dict and type(value['original_source_bindings']) is dict
         and len(value['original_source_bindings']) == 7, 'whole declaration and original7 model Source bindings')
    return value


def load_source(role, raw, invocation, budget):
    budget.check()
    name = '_Q_untrusted_bootstrap_' + role + '_' + hashlib.sha256(invocation.encode()).hexdigest()[:16]
    need(name not in sys.modules, 'fresh private registered Source namespace')
    module = types.ModuleType(name)
    module.__file__ = '<Q-authenticated-FD-' + role + '-' + SOURCE_PINS[role]['sha256'] + '>'
    original_import = builtins.__import__
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        need(level == 0 and name.split('.')[0] in ALLOWED_IMPORTS, 'stdlib-only explicit producer imports')
        return original_import(name, globals, locals, fromlist, level)
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=imports)
    sys.modules[name] = module  # dataclass decorators require real module registration.
    try:
        code = compile(raw, module.__file__, 'exec')
        exec(code, module.__dict__)
    except BaseException:
        del sys.modules[name]
        raise
    budget.check()
    return module


def line(value, maximum):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf8')
    need(len(raw) <= maximum, 'complete response line limit; never truncate')
    return raw


def write_all(fd, raw, budget, *, cleanup):
    view = memoryview(raw)
    try:
        while view:
            budget.check(cleanup=cleanup)
            count = os.write(fd, view[:65536])
            need(count > 0, 'whole response transport progress')
            view = view[count:]
    finally:
        view.release()
    budget.check(cleanup=cleanup)


def main(arguments):
    need(len(arguments) == 10, 'exact argv10 FD/bootstrap interface')
    manifest_fd = decimal(arguments[0])
    manifest_record = {'sha256': arguments[1], 'bytes': decimal(arguments[2])}
    need(manifest_record['bytes'] <= 1048576, 'manifest at most1MiB')
    preparation_fd, codec_fd, point_fd, producer_fd, result_fd = [decimal(v) for v in arguments[3:8]]
    began_ns, deadline_ns = decimal(arguments[8]), decimal(arguments[9])
    budget = Budget(began_ns, deadline_ns)
    fds = [manifest_fd, preparation_fd, codec_fd, point_fd, producer_fd, result_fd]
    need(len(set(fds)) == 6, 'distinct owned inherited FD channels')
    for fd in fds[:-1]:
        fd_mode(fd)
    fd_mode(result_fd, writable=True)
    raw_manifest = read_exact(manifest_fd, manifest_record, budget)
    manifest = parse_manifest(raw_manifest)
    del raw_manifest
    budget.check()
    base = Path(manifest['event_directory'])
    need(type(manifest['event_directory']) is str and base.is_absolute() and base == base.resolve()
         and base.is_dir() and not base.is_symlink() and not any(base.iterdir()), 'coordinator-created empty canonical owned event base')
    events = base / 'producer-events'
    need(not events.exists(), 'fixed initially absent producer event child')
    modules = {}
    for role, fd in (('codec', codec_fd), ('point_graph', point_fd), ('producer', producer_fd)):
        raw_source = read_exact(fd, SOURCE_PINS[role], budget)
        modules[role] = load_source(role, raw_source, manifest['coordinator_invocation_id'], budget)
        del raw_source  # no raw source cache or producer-supplied module crosses verifier.
    raw_preparation = read_exact(preparation_fd, PREPARATION, budget)
    text = modules['codec'].decode_lossless_preparation(raw_preparation, budget)
    del raw_preparation  # sole bootstrap caller raw reference is released BEFORE the one parse.
    preparation = modules['codec'].parse_lossless_preparation_text(text, budget)
    del text
    budget.check()
    catalogue = preparation['catalogue']
    need(catalogue['declaration'] == manifest['declaration'], 'whole original declaration in complete parsed model')
    del preparation  # release original preparation observations; entire parse/EOF was completed.
    # Same-process synthetic local pair only; never reinterpret it as global
    # epoch or authority. Exact original producer2 float equality is preserved.
    began, local_deadline = project_local_float_deadline(deadline_ns, producer_pair=True)
    budget.check()
    result = modules['producer'].run_untrusted_candidate_search(
        point_module=modules['point_graph'], catalogue=catalogue, declaration=manifest['declaration'],
        original_source_bindings=manifest['original_source_bindings'], binding=manifest['binding'],
        coordinator_invocation_id=manifest['coordinator_invocation_id'], authority_sha256=manifest['authority_sha256'],
        event_directory=str(events), shared_began=began, deadline=local_deadline)
    cleanup = result.get('candidate') is None
    budget.check(cleanup=cleanup)
    body = {'schema': 'Q-untrusted-producer-bootstrap-response-body-v1',
        'coordinator_invocation_id': manifest['coordinator_invocation_id'],
        'authority_sha256': manifest['authority_sha256'], 'binding': manifest['binding'],
        'source_bindings': manifest['source_bindings'], 'result': result}
    body_line = line(body, 4 * 1048576)
    completion = {'schema': 'Q-untrusted-producer-bootstrap-response-completion-v1',
        'body_sha256': hashlib.sha256(body_line).hexdigest(), 'body_bytes': len(body_line),
        'exit_zero_and_coordinator_deadline_required': True}
    completion_line = line(completion, 1024)
    budget.check(cleanup=cleanup)
    write_all(result_fd, body_line, budget, cleanup=cleanup)
    write_all(result_fd, completion_line, budget, cleanup=cleanup)
    budget.check(cleanup=cleanup)
    os.close(result_fd)  # exactly two complete lines then EOF, no valid response on partial failure.
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except BaseException as failure:
        if isinstance(failure, SystemExit):
            raise
        print('UNTRUSTED_BOOTSTRAP_FAILURE: ' + type(failure).__name__ + ': ' + str(failure)[:1024], file=sys.stderr, flush=True)
        sys.exit(2)
