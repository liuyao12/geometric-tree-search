"""UNEXECUTED disposable NONLOGICAL O04/O06 child, never a proof checker."""
import hashlib
import json
import os
import sys
import time

def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()

def main(argv):
    if len(argv) != 2 or argv[0] not in ('callable-shadow', 'partial-wire') or not argv[1].isascii() or not argv[1].isdigit():
        raise ValueError('exact mode and inherited output FD')
    fd = int(argv[1])
    if type(fd) is not int or fd < 3:
        raise ValueError('owned output FD, not stdio')
    if argv[0] == 'partial-wire':
        os.write(fd, b'{"disposable_partial_control":')
        # Parent must observe prefix, cancel/reap this owned process, retain bytes,
        # and reject it. No completion line, response or mathematical word exists.
        time.sleep(55)
        raise TimeoutError('parent did not cancel disposable partial-wire child')
    def endpoint():
        return 'toy-original'
    def replacement():
        return 'toy-mutated'
    saved = (endpoint, endpoint.__code__, endpoint.__defaults__, endpoint.__kwdefaults__, endpoint.__closure__)
    rejected = False
    try:
        endpoint.__code__ = replacement.__code__
        # Direct caller validates actual live function BEFORE delegation.
        if (endpoint is not saved[0] or endpoint.__code__ is not saved[1]
                or endpoint.__defaults__ is not saved[2] or endpoint.__kwdefaults__ is not saved[3]
                or endpoint.__closure__ is not saved[4]):
            raise ValueError('toy original delegated endpoint changed')
        endpoint()
    except ValueError:
        rejected = True
    finally:
        endpoint.__code__ = saved[1]
    restored = (endpoint is saved[0] and endpoint.__code__ is saved[1]
                and endpoint.__defaults__ is saved[2] and endpoint.__kwdefaults__ is saved[3]
                and endpoint.__closure__ is saved[4])
    if not rejected or not restored:
        raise ValueError('calibration failed; entire process discarded')
    body = encode({'schema': 'Q-disposable-callable-calibration-body-v1', 'same_object_code_change_rejected': rejected,
                   'original_endpoint_restored': restored, 'production_module_mutated': False,
                   'toy_endpoint_delegations': 0, 'NONLOGICAL': True, 'proof_accepted': False})
    completion = encode({'schema': 'Q-disposable-callable-calibration-completion-v1',
                         'body_sha256': hashlib.sha256(body).hexdigest(), 'body_bytes': len(body),
                         'exit_zero_and_coordinator_deadline_required': True})
    for data in (body, completion):
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise ValueError('whole calibration output write')
            offset += count
    os.close(fd)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
