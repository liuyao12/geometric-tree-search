"""Unexecuted ordinary-only fresh checker leaf; no producer or Q parse.

Reuse the exact reviewed clean verifier's FD/parser/CodeSeal/writer helpers;
never call its selected-point main. The unchanged ordinary adapter invokes
only unchanged independent checker1717 in this fresh process.
"""
import builtins
import fcntl
import hashlib
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
import resource
import select
import stat
import sys
import time
import types

VERSION = 'Q-ordinary-clean-checker-leaf-v2'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
PINS = {
 'support': {'sha256':'464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba','bytes':48584},
 'adapter': {'sha256':'e65a456f133807919e7d61cca55af782fbee32d62d8603684dae907841be8850','bytes':22226},
 'checker': {'sha256':'1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3','bytes':46514}}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def decimal(value):
    need(type(value) is str and value.isascii() and value.isdecimal()
         and (value == '0' or not value.startswith('0')), 'canonical decimal')
    return int(value)


def anchor(fn):
    need(type(fn) is types.FunctionType, 'original Python function')
    return (fn, fn.__code__, fn.__globals__, fn.__defaults__, fn.__kwdefaults__,
            tuple((cell, cell.cell_contents) for cell in fn.__closure__ or ()),
            tuple((key, id(value), value) for key, value in sorted((fn.__kwdefaults__ or {}).items())))


def same(fn, state):
    return (fn is state[0] and fn.__code__ is state[1] and fn.__globals__ is state[2]
        and fn.__defaults__ is state[3] and fn.__kwdefaults__ is state[4]
        and len(fn.__closure__ or ()) == len(state[5])
        and all(a is b and a.cell_contents is value for a, (b, value)
                in zip(fn.__closure__ or (), state[5]))
        and tuple((k, id(v)) for k, v in sorted((fn.__kwdefaults__ or {}).items()))
            == tuple((k, token) for k, token, value in state[6])
        and all(fn.__kwdefaults__[k] is v for k, token, v in state[6]))


def read_fixed(fd, pin, tick):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    need((flags & os.O_ACCMODE) == os.O_RDONLY and stat.S_ISREG(os.fstat(fd).st_mode)
         and os.lseek(fd, 0, os.SEEK_CUR) == 0, 'read-only whole regular Source FD')
    before = os.fstat(fd)
    need(before.st_size == pin['bytes'], 'complete Source size')
    chunks, count, digest = [], 0, hashlib.sha256()
    while True:
        tick()
        raw = os.read(fd, 65536)
        if not raw:
            break
        count += len(raw)
        need(count <= pin['bytes'], 'Source no suffix')
        digest.update(raw); chunks.append(raw)
    after = os.fstat(fd)
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
         == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
         and count == pin['bytes'] and digest.hexdigest() == pin['sha256'], 'same immutable Source buffer/EOF')
    return b''.join(chunks)


def load(role, raw):
    name = '_Q_ordinary_clean_' + role
    need(name not in sys.modules, 'fresh private registered clean module')
    module = types.ModuleType(name)
    module.__file__ = '<authenticated-' + role + '-' + PINS[role]['sha256'] + '>'
    sys.modules[name] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def main(argv):
    need(len(argv) == 12, 'ordinary checker exact CLI12')
    afd, asha, abytes, cfd, csha, cbytes, sfd, xfd, kfd, rfd, began, end = argv
    afd, abytes, cfd, cbytes, sfd, xfd, kfd, rfd, began, end = [decimal(x) for x in
        (afd,abytes,cfd,cbytes,sfd,xfd,kfd,rfd,began,end)]
    fds = [afd,cfd,sfd,xfd,kfd,rfd]
    need(len(set(fds)) == 6 and all(x >= 3 for x in fds), 'distinct inherited channels')
    need(end - began == 20000000000, 'original inherited integer joint20')
    clock, clock_id, usage, usage_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC, resource.getrusage, resource.RUSAGE_SELF
    need(type(clock) is types.BuiltinFunctionType and type(clock_id) is int, 'native global clock')
    def tick():
        if (time.clock_gettime_ns is not clock or time.CLOCK_MONOTONIC is not clock_id
                or resource.getrusage is not usage or resource.RUSAGE_SELF is not usage_id):
            raise RuntimeError('original native endpoint changed')
        now = clock(clock_id)
        if not began <= now < end or usage(usage_id).ru_maxrss >= 524288000:
            raise TimeoutError('original20/500MiB clean leaf incomplete')
    tick()
    support = load('support', read_fixed(sfd,PINS['support'],tick))
    adapter = load('adapter', read_fixed(xfd,PINS['adapter'],tick))
    checker = load('checker', read_fixed(kfd,PINS['checker'],tick))
    need(checker.VERSION == 'independent-complete-finite-Q-semantics-v1', 'unchanged checker')
    need((fcntl.fcntl(rfd,fcntl.F_GETFL) & os.O_ACCMODE) == os.O_WRONLY, 'write-only response')
    decoder = json.JSONDecoder(object_pairs_hook=support.unique_pairs, parse_int=support.parse_integer,
        parse_float=support.no_float, parse_constant=support.no_constant, strict=True)
    modules = (sys.modules[__name__],support,adapter,checker,json,json.decoder,json.encoder,
               json.scanner,hashlib,itertools,math,os,select,sys,time,types,resource,fcntl,stat)
    seal = support.CodeSeal(modules,decoder,end)
    functions = []
    for module in modules:
        for value in vars(module).values():
            if type(value) is types.FunctionType and value.__module__ == module.__name__:
                functions.append(value)
            elif isinstance(value,type) and value.__module__ == module.__name__:
                for cls in value.__mro__:
                    for member in vars(cls).values():
                        if type(member) in (staticmethod,classmethod): member = member.__func__
                        if type(member) is types.FunctionType: functions.append(member)
                        elif type(member) is property:
                            functions.extend(f for f in (member.fget,member.fset,member.fdel)
                                             if type(f) is types.FunctionType)
    states = tuple((fn,anchor(fn)) for fn in functions)
    anchor_fn, anchor_code, same_fn, same_code = anchor,anchor.__code__,same,same.__code__
    check_method, check_function, check_code = seal.check,support.CodeSeal.check,support.CodeSeal.check.__code__
    tick_state = anchor(tick)
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                    or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not check_function or check_function.__code__ is not check_code
                    or check_method.__self__ is not seal or check_method.__func__ is not check_function):
                raise RuntimeError('original immediate clean validators changed')
            if any(not same_fn(fn,state) for fn,state in states) or not same_fn(tick,tick_state):
                raise RuntimeError('original full default-entry/function/closure state changed')
            tick()
            if phase == 0: check_method()
    guard_state = anchor(guard)
    def boundary():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original invoking clean guard changed')
        guard()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original invoking clean guard changed after delegation')
    boundary_state = anchor(boundary)
    # The reused exact helpers precheck this callback before delegated use.
    authority_raw = support.read_fd(afd,abytes,asha,1048576,boundary)
    authority = support.decode_complete(authority_raw,decoder,boundary)
    candidate_raw = support.read_fd(cfd,cbytes,csha,2*1048576,boundary)
    candidate = support.decode_complete(candidate_raw,decoder,boundary)
    endpoint = adapter.validate_first_ready_candidate
    endpoint_state = anchor(endpoint)
    authority_value = support.value_digest(authority)
    candidate_value = support.value_digest(candidate)
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
            or same is not same_fn or same_fn.__code__ is not same_code
            or boundary.__code__ is not boundary_state[1] or not same_fn(boundary,boundary_state)
            or adapter.validate_first_ready_candidate is not endpoint or not same_fn(endpoint,endpoint_state)):
        raise RuntimeError('original pre-adapter invoking boundary changed')
    boundary()
    try:
        result = endpoint(candidate=candidate,fixed_authority=authority,fixed_authority_sha256=asha,
            checker_module=checker,source_guard=boundary,joint_began_ns=began,joint_deadline_ns=end)
    except ValueError as error:
        # Strict decoded ordinary intake rejection, not a mathematical
        # refutation. Native/source/callback failures remain UNKNOWN faults.
        result = {'schema':'Q-ordinary-intake-rejection-v1','status':'INTAKE_REJECTED',
                  'word_logically_accepted':False,'certificate':None,
                  'error':{'type':type(error).__name__,'message':str(error)[:2048]},
                  'ROOT_primary_accepted':False,'ROOT_resource_accepted':False}
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
            or same is not same_fn or same_fn.__code__ is not same_code
            or boundary.__code__ is not boundary_state[1] or not same_fn(boundary,boundary_state)
            or adapter.validate_first_ready_candidate is not endpoint or not same_fn(endpoint,endpoint_state)):
        raise RuntimeError('actual adapter/caller endpoint changed')
    boundary()
    need(support.value_digest(authority) == authority_value
         and support.value_digest(candidate) == candidate_value
         and hashlib.sha256(authority_raw).hexdigest() == asha
         and hashlib.sha256(candidate_raw).hexdigest() == csha, 'complete raw authority/candidate provenance')
    body = {'schema':'Q-ordinary-clean-response-body-v1','version':VERSION,
        'coordinator_invocation_id':authority['coordinator_invocation_id'],
        'authority_raw_sha256':asha,'candidate_raw_sha256':csha,'binding':authority['binding'],
        'source_bindings':authority['source_bindings'],'validation':result,
        'joint_began_ns':began,'joint_deadline_ns':end,
        'ROOT_primary_accepted':False,'ROOT_resource_accepted':False}
    support.write_response(rfd,body,boundary)
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
            or same is not same_fn or same_fn.__code__ is not same_code
            or boundary.__code__ is not boundary_state[1] or not same_fn(boundary,boundary_state)):
        raise RuntimeError('final invoking boundary changed')
    boundary()
    os.close(rfd)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        print('ORDINARY_CLEAN_UNKNOWN: '+type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)
