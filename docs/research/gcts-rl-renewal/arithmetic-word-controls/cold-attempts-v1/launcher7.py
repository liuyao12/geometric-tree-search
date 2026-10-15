# UNEXECUTED SOURCE. Exact immutable controls worker Source proposal; Root-only actual activation.
# The native begin intentionally precedes every import except time itself.
import time
_NATIVE_CLOCK_GETTIME_NS = time.clock_gettime_ns
_NATIVE_CLOCK_ID = time.CLOCK_MONOTONIC
if type(_NATIVE_CLOCK_ID) is not int:raise ValueError('exact integer native CLOCK_MONOTONIC ID')
JOINT_BEGAN_NS = _NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)

import hashlib
import os
from pathlib import Path
import stat
import sys
import types

VERSION = 'Q-neutral-controls-early-launcher-Source-v7-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
# Exact controls-worker Source is independently reviewed; no baseline main call.
# ROOT actual closure pins this launcher independently; no circular hardpin.
WORKER_SOURCE = {'bytes': 75506,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_split_neutral_cold_worker_global_clock_v7.py',
 'sha256': '1c27732c7ec7d0815e8b5e4e35467c1e9fe52eff061eee214d652cef1bb40bc5'}
JOINT_SECONDS_NS = 20_000_000_000
MAX_WORKER_SOURCE_BYTES = 1024 * 1024


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical_regular_path(value):
    need(type(value) is str and value and '\x00' not in value,
         'literal canonical absolute file path')
    path = Path(value)
    need(path.is_absolute() and str(path) == value and path == path.resolve(),
         'canonical absolute path without symbolic components')
    metadata = path.lstat()
    need(stat.S_ISREG(metadata.st_mode), 'regular file without symbolic link')
    return path


def authenticated_worker_buffer(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'},
         'exact hardliteral worker Source record')
    size = record['bytes']
    need(type(size) is int and 0 < size <= MAX_WORKER_SOURCE_BYTES,
         'bounded positive Source byte count')
    digest = record['sha256']
    need(type(digest) is str and len(digest) == 64
         and all(char in '0123456789abcdef' for char in digest),
         'literal lowercase Source SHA256')
    path = canonical_regular_path(record['path'])
    flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptor = os.open(str(path), flags)
    try:
        before = os.fstat(descriptor)
        need(stat.S_ISREG(before.st_mode) and before.st_size == size,
             'regular exact-length immutable-custody Source snapshot')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            raw = stream.read(size + 1)
            need(stream.read(1) == b'', 'complete Source EOF')
        after = os.fstat(descriptor)
        identity = lambda item: (item.st_dev, item.st_ino, item.st_mode,
                                 item.st_size, item.st_mtime_ns, item.st_ctime_ns)
        need(identity(before) == identity(after),
             'Source snapshot identity and metadata unchanged across full read')
        need(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
             'same complete immutable Source buffer authenticated')
        return path, raw
    finally:
        os.close(descriptor)


def launch(argv, *, joint_began_ns, worker_source):
    clock,clock_id,clock_module=_NATIVE_CLOCK_GETTIME_NS,_NATIVE_CLOCK_ID,time
    usage_import = __import__
    helpers = tuple((fn,fn.__code__,fn.__defaults__,fn.__kwdefaults__,tuple((cell,cell.cell_contents) for cell in fn.__closure__ or ())) for fn in (need,canonical_regular_path,authenticated_worker_buffer,launch,main))
    builtin_table = tuple(sorted(vars(__builtins__ if type(__builtins__) is types.ModuleType else sys.modules['builtins']).items()))
    need(type(joint_began_ns) is int and joint_began_ns == JOINT_BEGAN_NS,
         'required original first native kernel CLOCK_MONOTONIC begin; no reset')
    need(type(argv) is list and len(argv) == 1,
         'one canonical frozen plan argument')
    plan_path = canonical_regular_path(argv[0])
    source_path, raw = authenticated_worker_buffer(worker_source)
    # compile receives precisely the immutable bytes just authenticated. No
    # importlib loader, source cache, pyc or preparation/checker is used here.
    code = compile(raw, str(source_path), 'exec', dont_inherit=True)
    name = '_Q_trusted_worker_' + worker_source['sha256']
    need(name not in sys.modules, 'fresh private once-only trusted namespace')
    module = types.ModuleType(name)
    module.__file__ = str(source_path)
    module.__package__ = ''
    module.__loader__ = None
    module.__spec__ = None
    sys.modules[name] = module
    exec(code, module.__dict__)
    entry = module.__dict__.get('main')
    need(type(entry) is types.FunctionType and entry.__globals__ is module.__dict__
         and entry.__code__.co_filename == str(source_path)
         and module.CLOCK_DOMAIN == CLOCK_DOMAIN,
         'exact Source-compiled worker entry in its own namespace')
    need(module.__file__ == str(source_path) and sys.modules.get(name) is module,
         'original canonical executable Source origin and registry binding')
    # The controls worker requires this keyword and rejects its direct CLI. It
    # owns neutral controls subprocesses and all internal receipt/resource
    # checks; this parent performs no mathematical or untrusted Source call.
    entry_state=(entry,entry.__code__,entry.__defaults__,entry.__kwdefaults__,tuple((cell,cell.cell_contents) for cell in entry.__closure__ or ()))
    # Direct original caller/validator/native seals immediately before the actual
    # entry, with no unguarded callback helper carrying independent authority.
    if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id or __import__ is not usage_import:raise ValueError('original launcher clock/import endpoint')
    if any(vars(sys.modules[__name__]).get(fn.__name__) is not fn or fn.__code__ is not code or fn.__defaults__ is not defaults or fn.__kwdefaults__ is not kwdefaults for fn,code,defaults,kwdefaults,cells in helpers):raise ValueError('original launcher helper/caller code')
    if any(len(fn.__closure__ or ())!=len(cells) or any(cell is not old or cell.cell_contents is not value for cell,(old,value) in zip(fn.__closure__ or (),cells)) for fn,code,defaults,kwdefaults,cells in helpers):raise ValueError('original launcher caller closure')
    if module.main is not entry or entry.__code__ is not entry_state[1] or entry.__defaults__ is not entry_state[2] or entry.__kwdefaults__ is not entry_state[3]:raise ValueError('original actual worker entry')
    if tuple(sorted(vars(sys.modules['builtins']).items()))!=builtin_table:raise ValueError('original launcher builtin name resolution')
    returned = entry_state[0]([str(plan_path)], joint_began_ns=joint_began_ns)
    if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id or __import__ is not usage_import:raise ValueError('original launcher native endpoint after worker')
    if any(vars(sys.modules[__name__]).get(fn.__name__) is not fn or fn.__code__ is not code or fn.__defaults__ is not defaults or fn.__kwdefaults__ is not kwdefaults for fn,code,defaults,kwdefaults,cells in helpers):raise ValueError('launcher caller changed during worker')
    if any(len(fn.__closure__ or ())!=len(cells) or any(cell is not old or cell.cell_contents is not value for cell,(old,value) in zip(fn.__closure__ or (),cells)) for fn,code,defaults,kwdefaults,cells in helpers):raise ValueError('launcher caller closure changed during worker')
    if module.main is not entry_state[0] or entry.__code__ is not entry_state[1] or entry.__defaults__ is not entry_state[2] or entry.__kwdefaults__ is not entry_state[3]:raise ValueError('actual worker entry changed during delegation')
    if len(entry.__closure__ or ())!=len(entry_state[4]) or any(cell is not old or cell.cell_contents is not value for cell,(old,value) in zip(entry.__closure__ or (),entry_state[4])):raise ValueError('actual worker entry closure changed during delegation')
    if tuple(sorted(vars(sys.modules['builtins']).items()))!=builtin_table:raise ValueError('launcher builtins changed during worker')
    need(type(returned) is int and returned in (0, 2),
         'literal worker terminal return code')
    # This is a pre-exit sample, not an external terminal or complete finish
    # claim. ROOT's same-isolate actual caller must charge and observe exit.
    if returned == 0 and clock(clock_id) >= joint_began_ns + JOINT_SECONDS_NS:
        raise TimeoutError('complete trusted launcher returned after joint20')
    return returned


def main(argv):
    need(WORKER_SOURCE is not None, 'exact immutable controls worker; genuine current Root request required')
    return launch(argv, joint_began_ns=JOINT_BEGAN_NS,
                  worker_source=WORKER_SOURCE)


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(2)
