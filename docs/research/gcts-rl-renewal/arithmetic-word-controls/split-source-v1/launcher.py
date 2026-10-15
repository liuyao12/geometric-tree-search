# UNEXECUTED SOURCE. ROOT frozen coordinator V2 is pinned exactly below.
# The native begin intentionally precedes every import except time itself.
import time
JOINT_BEGAN_NS = time.perf_counter_ns()

import hashlib
import os
from pathlib import Path
import stat
import sys
import types

VERSION = 'Q-trusted-early-perf-cold-launcher-Source-v1'
# This selected immutable Source record is ROOT-authored coordinator V2.
# ROOT actual closure pins this launcher independently; no circular hardpin.
COORDINATOR_SOURCE = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-coordinator-source-20261014/Q_split_owned_coordinator_v2.py', 'sha256': 'dfb8c4bddb17368aa6553274c48a28c8d42aa7ed5b83d4ce1b880afe816762be', 'bytes': 44921}
JOINT_SECONDS_NS = 20_000_000_000
MAX_COORDINATOR_SOURCE_BYTES = 1024 * 1024


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


def authenticated_coordinator_buffer(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'},
         'exact hardliteral coordinator Source record')
    size = record['bytes']
    need(type(size) is int and 0 < size <= MAX_COORDINATOR_SOURCE_BYTES,
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


def launch(argv, *, joint_began_ns, coordinator_source):
    need(type(joint_began_ns) is int and joint_began_ns == JOINT_BEGAN_NS,
         'required original first native perf_counter_ns begin; no reset')
    need(type(argv) is list and len(argv) == 1,
         'one canonical frozen plan argument')
    plan_path = canonical_regular_path(argv[0])
    source_path, raw = authenticated_coordinator_buffer(coordinator_source)
    # compile receives precisely the immutable bytes just authenticated. No
    # importlib loader, source cache, pyc or preparation/checker is used here.
    code = compile(raw, str(source_path), 'exec', dont_inherit=True)
    name = '_Q_trusted_coordinator_' + coordinator_source['sha256']
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
         and entry.__code__.co_filename == str(source_path),
         'exact Source-compiled coordinator entry in its own namespace')
    need(module.__file__ == str(source_path) and sys.modules.get(name) is module,
         'original canonical executable Source origin and registry binding')
    # Coordinator V2 must require this keyword and reject its direct CLI. It
    # owns producer/verifier subprocesses and all internal receipt/resource
    # checks; this parent performs no mathematical or untrusted Source call.
    returned = entry([str(plan_path)], joint_began_ns=joint_began_ns)
    need(type(returned) is int and returned in (0, 2),
         'literal coordinator terminal return code')
    # This is a pre-exit sample, not an external terminal or complete finish
    # claim. ROOT's same-isolate actual caller must charge and observe exit.
    if returned == 0 and time.perf_counter_ns() >= joint_began_ns + JOINT_SECONDS_NS:
        raise TimeoutError('complete trusted launcher returned after joint20')
    return returned


def main(argv):
    need(COORDINATOR_SOURCE is not None,
         'disabled scaffold: genuine frozen coordinator V2 Source pin pending')
    return launch(argv, joint_began_ns=JOINT_BEGAN_NS,
                  coordinator_source=COORDINATOR_SOURCE)


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(2)
