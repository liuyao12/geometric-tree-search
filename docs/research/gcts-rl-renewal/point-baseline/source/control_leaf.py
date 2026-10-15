"""NONLOGICAL fixed memory/reaping control; no Q/producer/checker execution."""
import os
import resource
import sys
import time

VERSION = 'Q-ordinary-inert-memory-control-leaf-v1'


def main(argv):
    if len(argv) != 3 or argv[0] not in ('a','b'):
        raise ValueError('fixed inert control mode')
    began, end = int(argv[1]), int(argv[2])
    if end-began != 20000000000 or not began <= time.clock_gettime_ns(time.CLOCK_MONOTONIC) < end:
        raise TimeoutError('same original global20')
    size = (6 if argv[0] == 'a' else 10)*1048576
    live = bytearray(size)
    for i in range(0,size,4096): live[i] = 1
    time.sleep(.02)
    if time.clock_gettime_ns(time.CLOCK_MONOTONIC) >= end:
        raise TimeoutError('control completed late')
    os.write(1,(str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)+'\n').encode('ascii'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
