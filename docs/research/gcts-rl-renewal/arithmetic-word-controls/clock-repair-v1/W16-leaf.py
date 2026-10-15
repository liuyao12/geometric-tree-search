"""UNEXECUTED control-only wrapper, never the production verifier launch.

Four trusted extra CLI arguments precede unchanged verifier argv10:
verifier_source_fd verifier_source_path response_read_fd readiness_write_fd.
Authenticate and execute the exact clean verifier in a private module. Only a
genuine complete timely WORD_REJECTED response permits publishing readiness.
After readiness this deliberately remains alive until killed or failure55,
without more checker/Source/model calls. A real original20 Owner.wait MUST
reject the live process. No successful20/full52/proof/resource claim is made.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
import types

VERSION = 'Q-W16-control-only-late-exit-verifier-leaf-Source-v3-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
VERIFIER = {'bytes': 48584, 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}
RESPONSE_CAP = 4 * 1048576 + 1024
FALSE_FLAGS = ('ROOT_primary_accepted', 'ROOT_resource_accepted',
    'actual_selected_accepted', 'point_snapshot_accepted', 'full24_accepted',
    'full_trajectory_accepted', 'native_accepted', 'RL_accepted',
    'induction_accepted', 'full_PA_accepted')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def function_state(fn):
    need(type(fn) is types.FunctionType, 'original exact Python function')
    return (fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__,
            tuple((cell, id(cell.cell_contents)) for cell in fn.__closure__ or ()))


def integer_text(text, low=0, high=(1 << 63) - 1):
    need(type(text) is str and text.isascii() and text.isdecimal()
         and (text == '0' or not text.startswith('0')), 'literal canonical decimal CLI')
    value = int(text)
    need(low <= value <= high, 'bounded CLI integer')
    return value


def pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


def pairs(items):
    value = {}
    for key, member in items:
        need(key not in value, 'duplicate response member')
        value[key] = member
    return value


def no_float(text):
    raise ValueError('no float/nonfinite token in verifier control response')


def signed_integer(text):
    need(len(text) <= 20, 'bounded signed64 token')
    value = int(text)
    need(-(1 << 63) <= value < (1 << 63), 'literal signed64')
    return value


def decode_line(raw):
    decoder = json.JSONDecoder(object_pairs_hook=pairs, parse_int=signed_integer,
        parse_float=no_float, parse_constant=no_float, strict=True)
    text = raw.decode('utf8', 'strict')
    value, end = decoder.raw_decode(text)
    need(end == len(text) and canonical(value) == raw, 'complete canonical line/EOF')
    return value


def read_regular(fd, cap, began_ns, deadline_ns, *, clock, clock_id):
    need(type(fd) is int and fd >= 3, 'trusted regular fd')
    before = os.fstat(fd)
    need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'bounded whole regular snapshot')
    need(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY,
         'genuine readonly channel')
    need(os.lseek(fd, 0, os.SEEK_CUR) == 0, 'whole fd starts at zero')
    chunks, size = [], 0
    while True:
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id):
            raise ValueError('original native global clock callable/ID changed')
        need(began_ns <= clock(clock_id) < deadline_ns, 'original20 during full read')
        block = os.read(fd, min(65536, cap - size + 1))
        if not block:
            break
        size += len(block)
        need(size <= cap, 'whole file bound; no prefix')
        chunks.append(block)
    after = os.fstat(fd)
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
         'stable same regular input through EOF')
    need(size == before.st_size, 'complete raw byte count')
    return b''.join(chunks)


def main(argv):
    clock = time.clock_gettime_ns
    clock_id = time.CLOCK_MONOTONIC
    if (type(clock) is not types.BuiltinFunctionType or clock.__module__ != 'time'
            or clock.__name__ != 'clock_gettime_ns' or type(clock_id) is not int):
        raise ValueError('original native global clock callable/exact integer ID')
    need(len(argv) == 14, 'four control channels plus unchanged verifier argv10')
    source_fd = integer_text(argv[0], 3, 1 << 20)
    source_path = Path(argv[1])
    response_fd = integer_text(argv[2], 3, 1 << 20)
    ready_fd = integer_text(argv[3], 3, 1 << 20)
    original = argv[4:]
    authority_fd = integer_text(original[0], 3, 1 << 20)
    candidate_fd = integer_text(original[3], 3, 1 << 20)
    checker_fd = integer_text(original[6], 3, 1 << 20)
    output_fd = integer_text(original[7], 3, 1 << 20)
    began_ns = integer_text(original[8], 1)
    deadline_ns = integer_text(original[9], began_ns)
    if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
            or time.CLOCK_MONOTONIC != clock_id):
        raise ValueError('original native global clock callable/ID changed')
    need(deadline_ns - began_ns == 20000000000
         and began_ns <= clock(clock_id) < deadline_ns, 'same original20; no reset')
    need(len({source_fd, response_fd, ready_fd, authority_fd,
              candidate_fd, checker_fd, output_fd}) == 7, 'distinct control and original fd numbers')
    for fd in (source_fd, response_fd, authority_fd, candidate_fd, checker_fd):
        need(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY,
             'all original authority/candidate/Source input channels readonly')
    for fd in (ready_fd, output_fd):
        need(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_WRONLY,
             'exclusive write-only result channel')
        need(stat.S_ISREG(os.fstat(fd).st_mode), 'owned regular result/readiness file')
    out_stat, read_stat = os.fstat(output_fd), os.fstat(response_fd)
    need((out_stat.st_dev, out_stat.st_ino) == (read_stat.st_dev, read_stat.st_ino),
         'extra readonly response fd is exact same original result inode')
    need(out_stat.st_size == 0 and os.fstat(ready_fd).st_size == 0,
         'fresh empty result and readiness channels')

    verifier_raw = read_regular(source_fd, VERIFIER['bytes'], began_ns, deadline_ns, clock=clock, clock_id=clock_id)
    need(pin(verifier_raw) == VERIFIER, 'complete exact clean verifier3 Source fd')
    need(source_path.is_absolute() and source_path == source_path.resolve(),
         'canonical Root-owned fixed verifier Source path')
    fixed_fd = os.open(str(source_path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fixed_raw = read_regular(fixed_fd, VERIFIER['bytes'], began_ns, deadline_ns, clock=clock, clock_id=clock_id)
    finally:
        os.close(fixed_fd)
    need(fixed_raw == verifier_raw, 'private __file__ and executed buffer same exact Source')
    module_name = 'Q_W16_pinned_original_clean_verifier'
    need(module_name not in sys.modules, 'fresh private verifier module, no cache reuse')
    module = types.ModuleType(module_name)
    module.__file__ = str(source_path)
    sys.modules[module_name] = module
    try:
        code = compile(verifier_raw, str(source_path), 'exec')
        exec(code, module.__dict__)
        need(module.VERSION == 'Q-clean-original-target-word-verifier-Source-v4-global-clock'
             and module.CLOCK_DOMAIN == CLOCK_DOMAIN
             and type(module.main) is types.FunctionType
             and module.main.__code__.co_filename == str(source_path),
             'original raw-bound unchanged verifier entry')
        entry = module.main
        entry_anchor = function_state(entry)
        state_fn, state_code = function_state, function_state.__code__
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id):
            raise ValueError('original native global clock callable/ID changed')
        need(clock(clock_id) < deadline_ns, 'original20 before actual verifier')
        if function_state is not state_fn or state_fn.__code__ is not state_code:
            raise ValueError('original immediate verifier caller validator changed')
        need(function_state(entry) == entry_anchor and module.main is entry,
             'effective original verifier main before call')
        returned = entry(original)
        if function_state is not state_fn or state_fn.__code__ is not state_code:
            raise ValueError('original immediate verifier caller validator changed')
        need(module.main is entry and function_state(entry) == entry_anchor,
             'original verifier main code/default/cells retained')
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id):
            raise ValueError('original native global clock callable/ID changed')
        need(type(returned) is int and returned == 0
             and clock(clock_id) < deadline_ns, 'genuine timely unchanged verifier main return0')
        response_raw = read_regular(response_fd, RESPONSE_CAP, began_ns, deadline_ns, clock=clock, clock_id=clock_id)
        need(response_raw.endswith(b'\n') and response_raw.count(b'\n') == 2,
             'actual complete two-line verifier response plus EOF')
        body_raw, trailer_raw, empty = response_raw.split(b'\n')
        need(empty == b'' and len(trailer_raw) <= 1024, 'complete bounded trailer')
        body, trailer = decode_line(body_raw), decode_line(trailer_raw)
        need(type(body) is dict and body.get('schema') == 'Q-clean-verifier-response-body-v1'
             and body.get('version') == 'Q-clean-original-target-word-verifier-Source-v4-global-clock'
             and body.get('status') == 'WORD_REJECTED'
             and body.get('independent_word_certificate') is None
             and type(body.get('rejection')) is dict
             and all(body.get(name) is False for name in FALSE_FLAGS),
             'only genuine rejected-word baseline; never a target-positive proof')
        need(body['joint_began_ns'] == began_ns and type(body['joint_began_ns']) is int
             and body['joint_deadline_ns'] == deadline_ns
             and type(body['joint_deadline_ns']) is int, 'original verifier clock copied exactly')
        need(type(trailer) is dict and set(trailer) ==
             {'schema', 'body_sha256', 'body_bytes', 'exit_zero_and_coordinator_deadline_required'}
             and trailer['schema'] == 'Q-clean-verifier-response-completion-v1'
             and type(trailer['body_bytes']) is int and trailer['body_bytes'] == len(body_raw) + 1
             and trailer['body_sha256'] == hashlib.sha256(body_raw + b'\n').hexdigest()
             and trailer['exit_zero_and_coordinator_deadline_required'] is True,
             'whole original hash-linked response')
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id):
            raise ValueError('original native global clock callable/ID changed')
        ready = {'schema': 'Q-W16-ready-for-deliberate-late-exit-v1', 'version': VERSION,
            'control_only_wrapper': True, 'verifier_source': VERIFIER,
            'verifier_main_returned': returned, 'verifier_status': body['status'],
            'actual_response_pin': pin(response_raw),
            'authority_raw_sha256': original[1], 'candidate_raw_sha256': original[4],
            'coordinator_invocation_id': body['coordinator_invocation_id'],
            'binding': body['binding'], 'source_bindings': body['source_bindings'],
            'joint_began_ns': began_ns, 'joint_deadline_ns': deadline_ns,
            'child_ready_claim_ns': clock(clock_id),
            'child_claims_are_not_native_parent_observation': True,
            'intent': 'keep this SAME verifier-role process live for actual original20 Owner.wait rejection',
            'original_Q_theorem_accepted': False, 'actual_selected_accepted': False,
            'point_snapshot_accepted': False, 'full24_accepted': False,
            'trajectory_accepted': False, 'native_accepted': False, 'RL_accepted': False,
            'successful20_stage': False, 'all52_qualified': False, 'ROOT_resource_accepted': False}
        ready_body = canonical(ready) + b'\n'
        completion = {'schema': 'Q-W16-readiness-completion-v1',
            'body_sha256': hashlib.sha256(ready_body).hexdigest(), 'body_bytes': len(ready_body),
            'exit_zero_and_coordinator_deadline_required': True}
        ready_wire = ready_body + canonical(completion) + b'\n'
        need(len(ready_wire) <= 16384, 'complete bounded readiness, never a prefix')
        offset = 0
        while offset < len(ready_wire):
            if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                    or time.CLOCK_MONOTONIC != clock_id):
                raise ValueError('original native global clock callable/ID changed')
            need(clock(clock_id) < deadline_ns, 'actual readiness write stays in original20')
            count = os.write(ready_fd, ready_wire[offset:])
            need(count > 0, 'complete readiness write')
            offset += count
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id):
            raise ValueError('original native global clock callable/ID changed')
        need(clock(clock_id) < deadline_ns, 'complete readiness published before originaldeadline')
        # Deliberate CONTROL-ONLY late phase: no Source/parser/checker/model
        # delegation, no accepted work, no fresh begin. Root must time out at20
        # and kill/reap. Native self55 is only a last failure-cleanup bound.
        sleep = time.sleep
        if type(sleep) is not types.BuiltinFunctionType or sleep.__module__ != 'time' or sleep.__name__ != 'sleep':
            raise ValueError('original native control-only wait')
        while True:
            if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                    or time.CLOCK_MONOTONIC != clock_id):
                raise ValueError('original native global clock callable/ID changed')
            if clock(clock_id) >= began_ns + 55000000000:
                break
            if time.sleep is not sleep:
                raise ValueError('original native control-only wait changed')
            sleep(0.01)
            if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                    or time.CLOCK_MONOTONIC != clock_id):
                raise ValueError('original native global clock callable/ID changed')
            if time.sleep is not sleep:
                raise ValueError('original native control-only wait changed after delegation')
        return 2
    finally:
        # Namespace cleanup on an ordinary Python exit; OS kill is instead
        # evidenced by the parent exact wait4/reap/native ownership ledger.
        if sys.modules.get(module_name) is module:
            del sys.modules[module_name]


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(2)
