"""Unexecuted complete right-two preparation producer, one owned process.

Unchanged generic kernel/compiler/point graph/domain oracle. No proof words,
intermediate facts, libraries, backcones, search or donor data. Every original
finite grammar member is retained or the whole stage is UNKNOWN. Producer
controls/epochs do not establish independent mathematical catalogue admission.
"""
import time
_NATIVE_CLOCK_GETTIME_NS=time.clock_gettime_ns
_NATIVE_CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_BEGAN_NS=_NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)
import builtins
import copy
import fcntl
import hashlib
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import resource
import select
import stat
import sys
import types

VERSION='Q-right-two-complete-preparation-intake-Source-v1'
AUTHOR='/root/hilbert_ordering_diagnosis'
REVIEW_SCOPE='Q-right-two-complete-preparation-intake-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
_NATIVE_EXIT=os._exit
MAX_SMALL=1048576
MAX_FILE=64*1048576
MAX_TOTAL=256*1048576
FIXED_SOURCES={'catalogue': {'bytes': 10187,
               'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py',
               'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'},
 'clean_support': {'bytes': 48584,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py',
                   'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'},
 'domain_oracle': {'bytes': 19742,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py',
                   'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638'},
 'kernel': {'bytes': 10323,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py',
            'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}}
FIXED_INPUTS={'declaration': {'bytes': 2925,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json',
                 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'},
 'master': {'bytes': 21657,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md',
            'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}}
RUNTIME={'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
LIMITS={'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def integer(value, low=0, high=(1 << 63) - 1):
    need(type(value) is int and low <= value <= high, 'literal bounded integer')
    return value

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def pin_bytes(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def duplicate_free(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result

def no_constant(token):
    raise ValueError('non-finite JSON token prohibited: ' + token)

def no_float(token):
    raise ValueError('floating token prohibited in semantic/control data')

def signed_integer(token):
    need(len(token) <= 20, 'bounded integer token')
    value = int(token)
    need(-(1 << 63) <= value < (1 << 63), 'signed64 JSON integer')
    return value

def finite_float(token):
    value = float(token)
    need(math.isfinite(value), 'finite diagnostic float')
    return value

def tree(value, depth=0, visits=None):
    if visits is None:
        visits = [0]
    visits[0] += 1
    need(depth <= 64 and visits[0] <= 500000, 'whole bounded data tree')
    if type(value) is dict:
        for key, item in value.items():
            need(type(key) is str and len(key.encode('utf8')) <= 128, 'bounded member')
            tree(item, depth + 1, visits)
    elif type(value) is list:
        for item in value:
            tree(item, depth + 1, visits)
    elif type(value) is str:
        need(len(value.encode('utf8')) <= 4096, 'bounded string')
    else:
        need(type(value) in (int, float, bool, type(None)), 'JSON scalar')
        if type(value) is float:
            need(math.isfinite(value), 'finite scalar')

def decode(raw, cap, *, diagnostic_floats=False):
    need(type(raw) is bytes and len(raw) <= cap, 'complete bounded buffer')
    decoder = json.JSONDecoder(object_pairs_hook=duplicate_free,
        parse_int=signed_integer, parse_float=finite_float if diagnostic_floats else no_float,
        parse_constant=no_constant, strict=True)
    text = raw.decode('utf8', 'strict')
    start = 0
    while start < len(text) and text[start] in ' \t\r\n':
        start += 1
    value, end = decoder.raw_decode(text, start)
    need(all(character in ' \t\r\n' for character in text[end:]), 'one whole JSON plus exact whitespace/EOF')
    tree(value)
    return value

def regular_fd(path, flags):
    path = Path(path)
    need(path.is_absolute() and path == path.resolve(), 'canonical owned/configured path')
    fd = os.open(str(path), flags | os.O_NOFOLLOW)
    try:
        need(stat.S_ISREG(os.fstat(fd).st_mode), 'regular file; no symlink/device')
        return fd
    except BaseException:
        os.close(fd)
        raise

def read_small(path, cap, expected=None):
    fd = regular_fd(path, os.O_RDONLY)
    try:
        before = os.fstat(fd)
        need(before.st_size <= cap, 'whole file bound, never truncate')
        raw = b''
        while True:
            block = os.read(fd, min(65536, cap - len(raw) + 1))
            if not block:
                break
            raw += block
            need(len(raw) <= cap, 'complete bounded file')
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable opened file')
        if expected is not None:
            need(type(expected) is dict and set(expected) in
                 ({'sha256','bytes'}, {'path','sha256','bytes'}), 'exact configured raw pin')
            if 'path' in expected:
                need(expected['path'] == str(path), 'same configured path-bearing raw pin')
            need(pin_bytes(raw) == {key:expected[key] for key in ('sha256','bytes')},
                 'same complete authenticated file buffer')
        return raw
    finally:
        os.close(fd)

def write_exclusive(path, raw):
    fd = regular_fd(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        offset = 0
        while offset < len(raw):
            count = os.write(fd, raw[offset:offset + 65536])
            need(count > 0, 'complete owned write')
            offset += count
    finally:
        os.close(fd)

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

def load_fixed(role, raw):
    name = '_atomic_training_' + role
    need(name not in sys.modules, 'fresh private registered dependency')
    module = types.ModuleType(name)
    module.__file__ = '<authenticated-' + role + '-' + FIXED_SOURCES[role]['sha256'] + '>'
    sys.modules[name] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module

def exact_limits(value):
    need(type(value) is dict and set(value) == set(LIMITS)
         and all(type(value[k]) is int and value[k] == LIMITS[k] for k in LIMITS),
         'literal unchanged20/55/60/512/90+1 limits')

def invoke(fn, args, kwargs, boundary, boundary_anchor, anchor_fn, anchor_code, same_fn, same_code):
    # Both ordinary return and exceptional return pass the same full guard.
    # This prevents a custody/timeout fault from masquerading as a negative.
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
            or same_fn.__code__ is not same_code or anchor_fn.__defaults__ is not None
            or same_fn.__defaults__ is not None or anchor_fn.__kwdefaults__ is not None
            or same_fn.__kwdefaults__ is not None or anchor_fn.__closure__ is not None
            or same_fn.__closure__ is not None):
        raise RuntimeError('original invoking validators changed')
    fn_anchor = anchor_fn(fn)
    if boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor):
        raise RuntimeError('original invoking boundary changed')
    boundary()
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
            or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
            or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
        raise RuntimeError('original pre-delegation callback/endpoint changed')
    try:
        return fn(*args,**kwargs)
    finally:
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
                or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
            raise RuntimeError('actual delegated endpoint or boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
                or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
            raise RuntimeError('post-delegation boundary or endpoint changed')

def json_blockable(value):
    # A C-json block is a bounded existing subtree: at most512 scalar/container
    # visits,32768 total string characters and4096 bits per integer. This test
    # retains references only; oversized containers are streamed recursively.
    stack=[value];visits=0;characters=0
    while stack:
        child=stack.pop();visits+=1
        if visits>512:return False
        if type(child) is str:
            characters+=len(child)
            if characters>32768:return False
        elif type(child) is int:
            if child.bit_length()>4096:return False
        elif child is None or type(child) in (bool,float):pass
        elif type(child) is dict:
            if len(child)>512:return False
            for name,item in child.items():
                if type(name) is not str:return False
                stack.append(name);stack.append(item)
                if len(stack)>512:return False
        elif type(child) in (list,tuple):
            if len(child)>512:return False
            stack.extend(child)
            if len(stack)>512:return False
        else:return False
    return True

def json_chunks(value):
    # Full canonical JSON: C blocks only for bounded existing subtrees. No full
    # model/state copy, JSON string or UTF-8 buffer is constructed here.
    if json_blockable(value):
        yield canonical(value).decode('utf8')
    elif type(value) is dict:
        yield '{'
        for index,name in enumerate(sorted(value)):
            need(type(name) is str,'literal JSON object keys')
            if index:yield ','
            yield canonical(name).decode('utf8')+':'
            yield from json_chunks(value[name])
        yield '}'
    elif type(value) in (list,tuple):
        yield '['
        for start in range(0,len(value),32):
            block=value[start:start+32]
            if start:yield ','
            if json_blockable(block):yield canonical(block).decode('utf8')[1:-1]
            else:
                for offset,item in enumerate(block):
                    if offset:yield ','
                    yield from json_chunks(item)
        yield ']'
    else:yield canonical(value).decode('utf8')


def validate_plan(plan,own):
    need(type(plan) is dict and set(plan)=={'schema','invocation_id','purpose','output_directory','sources',
         'inputs','source_contract','reviews','ROOT_authorization','runtime','limits','resource_rule'}, 'exact12 Root preparation plan')
    need(plan['schema']=='ROOT-Q-right-two-preparation-plan-v1' and plan['purpose']=='complete-right-two-preparation'
         and plan['resource_rule']=='single-owned-process-native-terminal-v1','preparation only/no search')
    name=plan['invocation_id'];need(type(name) is str and 1<=len(name)<=128 and all(c in
         'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name),'bounded invocation')
    need(set(plan['sources'])=={'intake',*FIXED_SOURCES} and all(plan['sources'][r]==p for r,p in FIXED_SOURCES.items())
         and plan['sources']['intake']==dict(own,path=str(Path(__file__).resolve())) and plan['inputs']==FIXED_INPUTS,
         'exact Source6/input2, no supplied model/recipe/lemma/proof')
    exact_limits(plan['limits']);need(plan['runtime']==RUNTIME and sys.platform=='darwin'
         and Path(sys.executable).resolve()==Path(RUNTIME['path']).resolve(),'pinned original runtime')
    need(type(plan['reviews']) is dict and set(plan['reviews'])=={'ROOT','peer'},'current whole-source reviews')


def validate_review(review,plan,reviewer):
    need(review.get('scope')==REVIEW_SCOPE and review.get('source_only') is True
         and review.get('source_review_passed') is True and type(review.get('scientific_calls')) is int
         and review['scientific_calls']==0 and review.get('scientific_acceptance') is False
         and review.get('source')==plan['sources']['intake'] and review.get('sources')==plan['sources']
         and review.get('source_contract')==plan['source_contract'] and review.get('author_identity')==AUTHOR
         and review.get('reviewer_identity')==reviewer and reviewer!=AUTHOR,'genuine current distinct Source6 review')


def write_stream(path,chunks,tick,aggregate):
    # Fixed reviewed pure generator + anchored native budget. Full CodeSeal at
    # complete file entry/exit by invoke, not recursive scans at every JSON item.
    tick_fn=tick;tick_state=anchor(tick_fn);anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    fd=regular_fd(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL);h=hashlib.sha256();count=0;buffer=bytearray()
    try:
        for chunk in chunks:
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                    or same_fn.__code__ is not same_code or tick_fn.__code__ is not tick_state[1] or not same_fn(tick_fn,tick_state)):
                raise RuntimeError('original streaming native budget callback changed')
            tick_fn()
            if (tick_fn.__code__ is not tick_state[1] or not same_fn(tick_fn,tick_state)):
                raise RuntimeError('stream budget callback changed after use')
            need(type(chunk) is str,'complete literal JSON text chunk');raw=chunk.encode('utf8')
            need(len(raw)<=4*1048576,'original bounded encoding block');count+=len(raw);aggregate[0]+=len(raw)
            need(count<=MAX_FILE and aggregate[0]<=MAX_TOTAL,'original64MiB/file and256MiB aggregate, never trim')
            h.update(raw);buffer.extend(raw)
            if len(buffer)>=16384:
                offset=0
                while offset<len(buffer):
                    n=os.write(fd,buffer[offset:offset+65536]);need(n>0,'entire stream block');offset+=n
                buffer.clear()
        offset=0
        while offset<len(buffer):
            n=os.write(fd,buffer[offset:offset+65536]);need(n>0,'complete final stream');offset+=n
        need(os.fstat(fd).st_size==count,'full emitted file size')
    finally:os.close(fd)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':count}


def prepared_chunks(model,graph,decision,domain_module,started_ns):
    # Original payload wire fields with full initial state streamed directly;
    # no giant semantic_state copy, full-state string or preparation reread.
    small={'schema':'Q-complete-catalogue-and-initial-empty-Gamma-domains-preparation-only-v1',
        'census':model['census'],'initial_decision':decision,
        'initial_legal_domain_counts':[d.count for d in graph.domains],
        'initial_legal_candidate_count':sum(d.count for d in graph.domains),
        'graph_constructions':1,'target_searches':0,'native_queries':0,'RL_training_runs':0,
        'independent_catalogue_or_point_admission':False,'whole_proof_accepted':False,
        'universal_theorem_discovered':False,'full_PA_accepted':False,'native_accepted':False,
        'full_trajectory_accepted':False,'cold_payload_seconds_before_final_guards':
             (_NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)-started_ns)/1000000000,
        'cost_scope':'Entire cold setup/compiler/graph/full24 oracle/output/nativeexit inside original20; failure55 only evidence.'}
    yield '{'
    for i,name in enumerate(sorted([*small,'catalogue','initial_state'])):
        if i:yield ','
        yield canonical(name).decode('utf8')+':'
        if name=='catalogue':yield from json_chunks(model)
        elif name=='initial_state':yield from domain_module.state_chunks(graph)
        else:yield from json_chunks(small[name])
    yield '}'


def main(argv,*,joint_began_ns):
    need(len(argv)==1 and type(joint_began_ns) is int and joint_began_ns>0,'soleplan and early native G')
    began,end=joint_began_ns,joint_began_ns+20000000000
    clock,clock_id,usage,self_id,exit_fn=_NATIVE_CLOCK_GETTIME_NS,_NATIVE_CLOCK_ID,resource.getrusage,resource.RUSAGE_SELF,_NATIVE_EXIT
    def tick():
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC is not clock_id
                or resource.getrusage is not usage or resource.RUSAGE_SELF is not self_id or os._exit is not exit_fn or _NATIVE_EXIT is not exit_fn):
            raise RuntimeError('original native global/resource/exit endpoint changed')
        now=clock(clock_id);peak=usage(self_id).ru_maxrss
        if type(now) is not int or not began<=now<end or type(peak) is not int or peak>=524288000:
            raise TimeoutError('right-two whole original20/500MiB unfinished; no accepted prefix')
    tick();own_raw=read_small(str(Path(__file__).resolve()),MAX_SMALL)
    plan_raw=read_small(argv[0],MAX_SMALL);plan=decode(plan_raw,MAX_SMALL);validate_plan(plan,pin_bytes(own_raw));tick()
    meta_records={'contract':plan['source_contract'],'ROOT_review':plan['reviews']['ROOT'],'peer_review':plan['reviews']['peer'],
                  'ROOT_authorization':plan['ROOT_authorization']}
    meta_raw={r:read_small(p['path'],MAX_SMALL,p) for r,p in meta_records.items()}
    metadata={r:decode(b,MAX_SMALL) for r,b in meta_raw.items()}
    for r in ('ROOT','peer'):
        who=metadata[r+'_review'].get('reviewer_identity');need(type(who) is str and (who=='/root' if r=='ROOT' else who not in ('/root',AUTHOR)),'distinct actual reviewer')
        validate_review(metadata[r+'_review'],plan,who)
    grant=metadata['ROOT_authorization']
    need(grant.get('schema')=='ROOT-Q-right-two-preparation-authorization-v1' and grant.get('author_identity')=='/root'
         and grant.get('actual_execution_authorized') is True and grant.get('invocation_id')==plan['invocation_id']
         and grant.get('purpose')==plan['purpose'] and grant.get('sources')==plan['sources'] and grant.get('inputs')==FIXED_INPUTS
         and grant.get('resource_rule')==plan['resource_rule'],'fresh exact Root preparation grant')
    exact_limits(grant['limits']);need(metadata['contract'].get('schema')=='Q-right-two-complete-preparation-Source-contract-v1'
         and metadata['contract'].get('sources')==plan['sources'],'current preparation contract')
    raw_inputs={r:read_small(p['path'],MAX_SMALL,p) for r,p in FIXED_INPUTS.items()}
    declaration=decode(raw_inputs['declaration'],MAX_SMALL);declaration_seal=digest(declaration)
    raw_sources={'intake':own_raw};raw_sources.update({r:read_small(p['path'],MAX_SMALL,p) for r,p in FIXED_SOURCES.items()});tick()
    modules={r:load_fixed(r,raw_sources[r]) for r in ('clean_support','kernel','catalogue','point_graph','domain_oracle')}
    support,kernel,catalogue,point,domains=(modules[r] for r in ('clean_support','kernel','catalogue','point_graph','domain_oracle'))
    decoder=json.JSONDecoder(object_pairs_hook=duplicate_free,parse_int=signed_integer,parse_float=no_float,parse_constant=no_constant,strict=True)
    sealed_modules=(sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,copy,
                    hashlib,itertools,math,os,select,sys,time,types,resource,fcntl,stat)
    seal=support.CodeSeal(sealed_modules,decoder,end)
    functions=[]
    for module in sealed_modules:
        for value in vars(module).values():
            if type(value) is types.FunctionType and value.__module__==module.__name__:functions.append(value)
            elif isinstance(value,type) and value.__module__==module.__name__:
                for cls in value.__mro__:
                    for member in vars(cls).values():
                        if type(member) in (staticmethod,classmethod):member=member.__func__
                        if type(member) is types.FunctionType:functions.append(member)
                        elif type(member) is property:functions.extend(f for f in (member.fget,member.fset,member.fdel) if type(f) is types.FunctionType)
    states=tuple((f,anchor(f)) for f in functions);anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor(tick);method,method_fn,method_code=seal.check,support.CodeSeal.check,support.CodeSeal.check.__code__
    intake_seal=digest({'plan':plan,'metadata':metadata})
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not method_fn or method_fn.__code__ is not method_code or method.__self__ is not seal or method.__func__ is not method_fn):
                raise RuntimeError('original preparation validators changed')
            if any(not same_fn(f,s) for f,s in states) or not same_fn(tick,tick_state):raise RuntimeError('original Source/default/cell changed')
            tick()
            if phase==0:method()
        need(digest(declaration)==declaration_seal and digest({'plan':plan,'metadata':metadata})==intake_seal
             and all(pin_bytes(raw_sources[r])=={k:plan['sources'][r][k] for k in ('sha256','bytes')} for r in raw_sources),'same immutable declaration/intake/raw compiled buffers')
    guard_state=anchor(guard)
    def boundary():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):raise RuntimeError('original preparation boundary changed')
        guard()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):raise RuntimeError('postguard preparation boundary changed')
    boundary_anchor=anchor(boundary);invoke_fn,invoke_code=invoke,invoke.__code__
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical output only');run.mkdir(mode=0o700)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    local_pair=invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair': False},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    local_deadline=local_pair[1]
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    model=invoke_fn(catalogue.prepare,(declaration,),{'kernel_module': kernel, 'source_bindings': plan['sources'], 'deadline': local_deadline},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    def construct_graph():
        return point.PointGraph(height=model['height'],formulas=model['formula_codes'],recipe_data=model['recipes'],
            context=model['context'],authority=model['authority'],fixed_marks=model['boundary']['fixed_marks'],
            roots=model['boundary']['roots'],seed_keys=(),fixture=False,source_bindings=plan['sources'])
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    graph=invoke_fn(construct_graph,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    need(graph.initial_selected==() and graph.order==[] and graph.totals==[0]*24 and graph.roots==(0,)*24
         and all(r.witness['rule']!='assumption' for r in graph.recipes),'complete unseeded emptyGamma24 point model')
    # A class constructor is authenticated by the module seal; invoke's Python
    # function anchor is used only with a tiny fixed Python constructor factory.
    decision_obj=graph.decision();decision={k:getattr(decision_obj,k) for k in ('kind','row','count','generation')}
    binding={'declaration_sha256':FIXED_INPUTS['declaration']['sha256'],'model_epoch':graph.model_epoch,
             'primitive_authority_epoch':model['authority']['epoch'],'formula_registry_sha256':model['formula_registry_sha256']}
    aggregate=[0];outputs=[]
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    state_pin=invoke_fn(write_stream,(run / 'initial-state.json', domains.state_chunks(graph), tick, aggregate),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    outputs.append(state_pin)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    oracle_pin=invoke_fn(write_stream,(run / 'initial-oracle-domains.json', domains.checked_domain_chunks(graph, deadline=local_deadline), tick, aggregate),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    outputs.append(oracle_pin)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    prep_pin=invoke_fn(write_stream,(run / 'preparation.json', prepared_chunks(model, graph, decision, domains, began), tick, aggregate),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    outputs.append(prep_pin)
    summary={'schema':'Q-right-two-complete-preparation-summary-v1','version':VERSION,'invocation_id':plan['invocation_id'],
        'context_binding':binding,'declaration_value_sha256':declaration_seal,'declaration':declaration,
        'census':model['census'],'height':model['height'],'initial_legal_domain_counts':[d.count for d in graph.domains],
        'initial_decision':decision,'sources':plan['sources'],'inputs':FIXED_INPUTS,'outputs':outputs,
        'joint_began_ns':began,'joint_deadline_ns':end,'limits':LIMITS,'graph_constructions':1,
        'all_initial_domain_rows_compared':graph.height,'target_searches':0,'proof_words_supplied':0,
        'library_used':False,'recipe_trimming':False,'independent_catalogue_admitted':False,
        'ROOT_resource_accepted':False,'target_proof_accepted':False,'full24_solution_accepted':False,
        'trajectory_accepted':False,'native_accepted':False,'RL_accepted':False,
        'original_compiler_allocation':'Unchanged catalogue.prepare calls text(result) once; no smaller model substitution.',
        'grammar_limitation':'operand_values freezes before UI rounds; later generated subterms are not automatically added to equality operands.'}
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    unused=invoke_fn(write_exclusive,(run / 'summary.json', canonical(summary) + b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    summary_raw=invoke_fn(read_small,(str(run / 'summary.json'), MAX_SMALL),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    outputs.append(dict(pin_bytes(summary_raw),path=str(run/'summary.json')))
    body={'schema':'Q-right-two-preparation-response-body-v1','status':'COMPLETE_PRODUCER_PREPARATION_PENDING_EXTERNAL',
        'invocation_id':plan['invocation_id'],'plan':pin_bytes(plan_raw),'context_binding':binding,'outputs':outputs,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'sources':plan['sources'],'inputs':FIXED_INPUTS,
        'target_searches':0,'independent_catalogue_admitted':False,'ROOT_resource_accepted':False,
        'target_proof_accepted':False,'recipient_family_accepted':False,'full24_solution_accepted':False,
        'trajectory_accepted':False,'native_accepted':False,'RL_accepted':False}
    fd=regular_fd(run/'response.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate preparation caller changed')
        unused=invoke_fn(support.write_response,(fd, body, boundary),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate preparation caller changed after delegation')
    finally:os.close(fd)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    response_raw=invoke_fn(read_small,(str(run / 'response.jsonl'), MAX_SMALL),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    outputs.append(dict(pin_bytes(response_raw),path=str(run/'response.jsonl')))
    need(sorted(p.name for p in run.iterdir())==sorted(Path(p['path']).name for p in outputs),'complete5 generated files')
    final=canonical({'schema':'Q-right-two-preparation-final-observation-v1','response':pin_bytes(response_raw),
        'outputs':outputs,'pending_external':True,'context_binding':binding,'independent_catalogue_admitted':False,
        'target_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    unused=invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    offset=0
    while offset<len(final):n=os.write(1,final[offset:]);need(n>0,'complete final stdout');offset+=n
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed')
    unused=invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate preparation caller changed after delegation')
    tick()
    if os._exit is not exit_fn or _NATIVE_EXIT is not exit_fn or clock(clock_id)>=end:raise TimeoutError('final original20 gate')
    exit_fn(0)


if __name__=='__main__':
    try:main(sys.argv[1:],joint_began_ns=EARLY_BEGAN_NS)
    except BaseException as error:
        try:
            if (time.clock_gettime_ns is _NATIVE_CLOCK_GETTIME_NS and type(_NATIVE_CLOCK_ID) is int
                    and time.CLOCK_MONOTONIC is _NATIVE_CLOCK_ID and _NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)<EARLY_BEGAN_NS+55000000000):
                os.write(2,('RIGHT_TWO_PREPARATION_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:_NATIVE_EXIT(2)
