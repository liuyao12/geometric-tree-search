"""Unexecuted point-only FD bootstrap; unchanged point graph, no checker executes.

Uses the unchanged reviewed codec and compact untrusted point producer. Full original Q
input is read/authenticated/decoded once; only catalogue retained after EOF.
This process has no proof/resource authority and creates no other child.
"""
import builtins
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import select
import stat
import sys
import time
import types
VERSION = 'Q-point-compact-producer-bootstrap-v2'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
SOURCE_PINS = {'codec': {'bytes': 5806, 'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 30988, 'sha256': 'e45336591a3b1ef8624fb5c004de7cf21cbe6b81f577ec55503123468758403c'}}
PREPARATION = {'sha256':'0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a','bytes':38376960}
ALLOWED_IMPORTS = {'__future__',
 'copy',
 'dataclasses',
 'gzip',
 'hashlib',
 'itertools',
 'json',
 'math',
 'pathlib',
 'resource',
 'sys',
 'time',
 'types',
 'typing'}

def need(value, message):
    if not value:
        raise ValueError(message)

def decimal(text):
    need(type(text) is str and text and len(text) <= 32
         and all(c in '0123456789' for c in text), 'literal nonnegative decimal argument')
    value = int(text)
    need(value <= (1 << 63) - 1, 'signed64 interface integer')
    return value

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

def parse_manifest(raw):
    need(type(raw) is bytes and len(raw) <= 1048576, 'whole manifest maximum1MiB')
    def reject(token):
        raise ValueError('non-integer/nonfinite manifest value: ' + token)
    value = json.loads(raw.decode('utf8'), object_pairs_hook=unique,
                       parse_constant=reject, parse_float=reject)
    need(type(value) is dict and set(value) == {'schema','coordinator_invocation_id',
         'authority_sha256','declaration','binding','original_source_bindings','source_bindings','event_directory'},
         'point manifest exact eight fields')
    need(value['schema'] == 'Q-point-compact-producer-manifest-v1', 'point-only purpose')
    need(type(value['source_bindings']) is dict and set(value['source_bindings']) ==
         {'bootstrap','codec','point_graph','producer'}, 'point executed Source four')
    for role, pin in SOURCE_PINS.items():
        need(value['source_bindings'][role] == pin, 'unchanged exact Source ' + role)
    own = Path(__file__).read_bytes()
    need(value['source_bindings']['bootstrap'] ==
         {'sha256':hashlib.sha256(own).hexdigest(),'bytes':len(own)}, 'own authenticated launch Source')
    need(type(value['original_source_bindings']) is dict and
         len(value['original_source_bindings']) == 7, 'whole original source7')
    event = Path(value['event_directory'])
    need(event.is_absolute() and event == event.resolve() and not event.exists()
         and event.name == 'producer-events' and event.parent.name == 'producer-event-base'
         and event.parent.is_dir() and not any(event.parent.iterdir()),
         'exact parent-owned empty event base, initially absent fixed producer directory')
    return value


def journal(phase, budget, *, cleanup=False):
    """Bounded charged stdout diagnosis, never proof/resource authority."""
    budget.check(cleanup=cleanup)
    observed=budget._clock(budget._clock_id)
    raw=line({'schema':'Q-point-bootstrap-phase-journal-v1','phase':phase,
        'observed_native_ns':observed,'joint_began_ns':budget.began_ns,
        'joint_deadline_ns':budget.deadline_ns,'producer_claim_only':True},4096)
    write_all(1,raw,budget,cleanup=cleanup)
    budget.check(cleanup=cleanup)


def main(argv):
    need(len(argv) == 10, 'point bootstrap exact CLI10')
    manifest_fd, manifest_sha, manifest_size, preparation_fd, codec_fd, graph_fd, producer_fd, result_fd, began_ns, deadline_ns = argv
    manifest_fd, manifest_size, preparation_fd, codec_fd, graph_fd, producer_fd, result_fd, began_ns, deadline_ns = [
        decimal(x) for x in (manifest_fd,manifest_size,preparation_fd,codec_fd,graph_fd,producer_fd,result_fd,began_ns,deadline_ns)]
    need(manifest_size <= 1048576, 'bounded manifest')
    budget = Budget(began_ns, deadline_ns)
    fds = [manifest_fd,preparation_fd,codec_fd,graph_fd,producer_fd,result_fd]
    need(len(set(fds)) == 6, 'distinct read-only inputs and write-only result')
    for fd in fds[:-1]: fd_mode(fd)
    fd_mode(result_fd,writable=True)
    manifest = parse_manifest(read_exact(manifest_fd,{'sha256':manifest_sha,'bytes':manifest_size},budget))
    modules = {}
    for role,fd in (('codec',codec_fd),('point_graph',graph_fd),('producer',producer_fd)):
        raw = read_exact(fd,SOURCE_PINS[role],budget)
        modules[role] = load_source(role,raw,manifest['coordinator_invocation_id'],budget)
        del raw
    journal('preparation_read_begin',budget)
    raw = read_exact(preparation_fd,PREPARATION,budget)
    journal('parse_begin',budget)
    text = modules['codec'].decode_lossless_preparation(raw,budget)
    del raw
    preparation = modules['codec'].parse_lossless_preparation_text(text,budget)
    del text
    journal('parse_end',budget)
    catalogue = preparation['catalogue']
    need(catalogue['declaration'] == manifest['declaration'], 'exact entire original declaration')
    del preparation
    budget.check()
    journal('point_call_begin',budget)
    result = modules['producer'].run_untrusted_candidate_search(
        point_module=modules['point_graph'],
        catalogue=catalogue,declaration=manifest['declaration'],
        original_source_bindings=manifest['original_source_bindings'],binding=manifest['binding'],
        coordinator_invocation_id=manifest['coordinator_invocation_id'],
        authority_sha256=manifest['authority_sha256'],event_directory=manifest['event_directory'],
        joint_began_ns=began_ns,joint_deadline_ns=deadline_ns)
    cleanup = result.get('candidate') is None
    journal('point_call_return',budget,cleanup=cleanup)
    budget.check(cleanup=cleanup)
    body = {'schema':'Q-point-compact-producer-response-body-v1',
        'coordinator_invocation_id':manifest['coordinator_invocation_id'],
        'authority_sha256':manifest['authority_sha256'],'binding':manifest['binding'],
        'source_bindings':manifest['source_bindings'],'result':result}
    body_line = line(body,4*1048576)
    trailer = line({'schema':'Q-point-compact-producer-response-completion-v1',
        'body_sha256':hashlib.sha256(body_line).hexdigest(),'body_bytes':len(body_line),
        'exit_zero_and_coordinator_deadline_required':True},1024)
    write_all(result_fd,body_line,budget,cleanup=cleanup)
    write_all(result_fd,trailer,budget,cleanup=cleanup)
    budget.check(cleanup=cleanup)
    os.close(result_fd)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        print('POINT_BOOTSTRAP_UNKNOWN: '+type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)
