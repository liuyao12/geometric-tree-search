"""UNEXECUTED control-only profiler envelope, not baseline performance Source.

Actual Python module-entry/function calls and ending module origins are recorded
outside the exact verifier CodeSeal namespace. No preparation/PointGraph parses,
no supplied Q proof, no native-call completeness/hostile OS isolation claim.
"""
import copy
import dataclasses
import fcntl
import gzip
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
import typing

VERSION = 'Q-control-verifier-profile-leaf-v2-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
VERIFIER_SHA = '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'
VERIFIER_BYTES = 48584
MAX_UNIQUE_CALLS = 16384

def main(argv):
    clock_module, clock, clock_id = time, time.clock_gettime_ns, time.CLOCK_MONOTONIC
    if type(clock_id) is not int:raise ValueError('exact native global monotonic clock id')
    if len(argv) != 14:
        raise ValueError('verifierSnapshot/hash/bytes traceFD and unchanged verifier argv10')
    path = Path(argv[0])
    if not path.is_absolute() or path != path.resolve() or path.is_symlink() or argv[1] != VERIFIER_SHA or argv[2] != str(VERIFIER_BYTES):
        raise ValueError('exact canonical Root-authenticated verifier snapshot')
    raw = path.read_bytes()
    if len(raw) != VERIFIER_BYTES or hashlib.sha256(raw).hexdigest() != VERIFIER_SHA:
        raise ValueError('whole actual verifier Source')
    trace_fd = int(argv[3])
    if trace_fd < 3 or trace_fd in [int(argv[i]) for i in (4, 7, 10, 11)]:
        raise ValueError('separate owned profile output FD')
    verifier_arguments = argv[4:]
    began, deadline = int(verifier_arguments[-2]), int(verifier_arguments[-1])
    if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:raise ValueError('original actual native global clock endpoint/id changed')
    if deadline - began != 20000000000 or clock(clock_id) >= deadline:
        raise TimeoutError('same original joint20, no profiler clock reset')
    name = '_Q_control_profiled_exact_verifier'
    if name in sys.modules:
        raise ValueError('fresh registered private verifier module')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    calls, modules_before = {}, tuple(sorted(sys.modules))
    def profile(frame, event, argument):
        if event != 'call':
            return
        code = frame.f_code
        key = (code.co_filename, code.co_name, code.co_firstlineno)
        if key not in calls and len(calls) >= MAX_UNIQUE_CALLS:
            raise ValueError('complete bounded actual profile; never truncate')
        calls[key] = calls.get(key, 0) + 1
    saved_profile = sys.getprofile()
    if saved_profile is not None:
        raise ValueError('fresh profile process, no inherited collector')
    result = None
    try:
        sys.setprofile(profile)
        exec(compile(raw, str(path), 'exec'), module.__dict__)
        del raw
        if module.__dict__.get('CLOCK_DOMAIN') != CLOCK_DOMAIN or module.VERSION != 'Q-clean-original-target-word-verifier-Source-v4-global-clock':raise ValueError('current global-clock verifier version/domain required')
        if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:raise ValueError('original actual native global clock endpoint/id changed')
        result = module.main(verifier_arguments)
    finally:
        sys.setprofile(None)
    if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:raise ValueError('original actual native global clock endpoint/id changed')
    if result != 0 or clock(clock_id) >= deadline:
        raise TimeoutError('profiled verifier did not complete in original joint20')
    origins = []
    for name, item in sorted(sys.modules.items()):
        file = getattr(item, '__file__', None)
        origins.append({'module': name, 'origin': file if type(file) is str else None})
    body = {'schema': 'Q-control-verifier-execution-profile-body-v1', 'control_only': True,
            'profiled_verifier_source': {'sha256': VERIFIER_SHA, 'bytes': VERIFIER_BYTES},
            'profile_started_before_verifier_module_exec': True,
            'actual_calls': [{'filename': key[0], 'name': key[1], 'firstline': key[2], 'count': value}
                             for key, value in sorted(calls.items())],
            'modules_before': list(modules_before), 'modules_after_origins': origins,
            'verifier_returncode': result, 'joint_began_ns': began, 'joint_deadline_ns': deadline,
            'native_call_census_complete': False, 'baseline_performance_evidence': False,
            'proof_accepted': False, 'ROOT_resource_accepted': False}
    body_raw = (json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    if len(body_raw) > 4 * 1048576:
        raise ValueError('complete actual profile body exceeds original wire cap')
    trailer = (json.dumps({'schema': 'Q-control-verifier-execution-profile-completion-v1',
                           'body_sha256': hashlib.sha256(body_raw).hexdigest(), 'body_bytes': len(body_raw),
                           'exit_zero_and_coordinator_deadline_required': True}, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if len(trailer) > 1024:
        raise ValueError('complete profile trailer cap')
    for data in (body_raw, trailer):
        offset = 0
        while offset < len(data):
            if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:raise ValueError('original actual native global clock endpoint/id changed')
            if clock(clock_id) >= deadline:
                raise TimeoutError('profile serialization/whole output included in original joint20')
            wrote = os.write(trace_fd, data[offset:])
            if wrote <= 0:
                raise ValueError('complete trace progress')
            offset += wrote
    if time is not clock_module or time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:raise ValueError('original actual native global clock endpoint/id changed')
    if clock(clock_id) >= deadline:
        raise TimeoutError('complete trace finalized outside original joint20')
    os.close(trace_fd)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
