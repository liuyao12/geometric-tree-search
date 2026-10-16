"""Cold original unit-row global engine endpoints. Reuses existing native helpers.
Controls or a separate fresh target search; no supplied proof word/donor/library.
"""
import time
CLOCK=time.clock_gettime_ns
CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_G=CLOCK(CLOCK_ID)
import copy
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
import signal
import stat
import sys
import types
EXIT=os._exit
VERSION='unit-row-retained-domain-cold-v1'
SCOPE='unit-row-retained-domain-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'fallback': {'bytes': 24227, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-all-six-fallback-source-20261015/unit_row_all_six_fallback_v1.py', 'sha256': '69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae'}, 'engine': {'bytes': 39803, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-retained-domain-engine-source-20261015/lazy_unit_row_global_engine_v3.py', 'sha256': 'ca6151724b61e4fc3f8a2ba9ffa4a77c03e516898d7970eb275a6fc70a435c6f'}, 'controls': {'bytes': 21896, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-lazy-engine-controls-source-20261015/lazy_engine_adversarial_controls_v1.py', 'sha256': 'd7b0c0f6776e6b383e92e270f559e9b8978523a5ac5cfd91ec283996e214e4d7'}, 'transition': {'bytes': 8134, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-retained-domain-engine-source-20261015/unit_row_domain_transition_checker_v1.py', 'sha256': '2e2d66c3c5843ef086f073df09e2eda7a50d3972fa1900a8ecf33f5c92ab3491'}, 'retained_controls': {'bytes': 25338, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-retained-domain-controls-source-20261015/retained_domain_controls_v2.py', 'sha256': 'd1dcdfa9230ab1653c601ee2d769c64722d9ab0d0f292682bda214d8984488eb'}}
FIXED_INPUTS={'declaration': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df', 'bytes': 2925}, 'profile': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02', 'bytes': 8773}}
LIMITS={'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

def need(value,message):
    if not value:raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def raw_pin(raw):return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key');result[key]=value
    return result

def reject_constant(value):raise ValueError('nonfinite JSON constant')

def finite_float(value):
    result=float(value);need(math.isfinite(result),'finite diagnostic float');return result

def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)

def read_pinned(ref,cap=1048576):
    p=Path(ref['path']);need(p.is_absolute() and p==p.resolve(),'canonical current input')
    fd=os.open(str(p),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and info.st_size==ref['bytes']<=cap,'complete regular bounded input')
        blocks=[];total=0
        while True:
            block=os.read(fd,65536)
            if not block:break
            blocks.append(block);total+=len(block);need(total<=cap,'no truncated input')
        raw=b''.join(blocks)
        need(raw_pin(raw)=={k:ref[k] for k in ('sha256','bytes')},'whole current raw input SHA/EOF')
        return raw
    finally:os.close(fd)

def load_module(role,raw):
    name='_right_two_independent_'+role;need(name not in sys.modules,'fresh private module')
    module=types.ModuleType(name);module.__file__='<authenticated-'+role+'>'
    sys.modules[name]=module;exec(compile(raw,module.__file__,'exec'),module.__dict__)
    return module

def write_new(path,raw):
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        offset=0
        while offset<len(raw):
            n=os.write(fd,raw[offset:offset+65536]);need(n>0,'whole owned output');offset+=n
    finally:os.close(fd)
    return dict(raw_pin(raw),path=str(path))

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

def cancel(signum,frame):
    global CANCELLED
    CANCELLED=True

def all_function_anchors(modules):
    """Strong refs and identity tokens supplement unchanged CodeSeal snapshots."""
    functions=[];seen=set()
    def retain(fn):
        if type(fn) is types.FunctionType and id(fn) not in seen:
            seen.add(id(fn));functions.append((fn,anchor(fn)))
    for module in modules:
        for value in vars(module).values():
            if type(value) is types.FunctionType and value.__module__==module.__name__:retain(value)
            elif isinstance(value,type) and value.__module__==module.__name__:
                for base in value.__mro__:
                    for member in vars(base).values():
                        if isinstance(member,(staticmethod,classmethod)):member=member.__func__
                        if type(member) is property:
                            for fn in (member.fget,member.fset,member.fdel):retain(fn)
                        else:retain(member)
    return tuple(functions)

def save_failure_diagnostic(output_path, context_raw, capture, failure_kind, began_ns, *,
        _clock=CLOCK, _clock_id=CLOCK_ID, _usage=resource.getrusage, _self_id=resource.RUSAGE_SELF,
        _open=os.open, _mkdir=os.mkdir, _write=os.write, _close=os.close,
        _escape=json.encoder.encode_basestring_ascii, _hash=hashlib.sha256,
        _flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW):
    """Best-effort raw builtin data ONLY. No late authority or scientific calls.

    This helper never supplies a positive result. A complete two-file diagnostic
    still requires Root's separate terminal/failure-window reconciliation.
    """
    def failure_gate():
        # Captured native endpoints; no original20 Source callback is invoked.
        peak = _usage(_self_id).ru_maxrss
        now = _clock(_clock_id)
        if (type(_clock) is not types.BuiltinFunctionType or type(_clock_id) is not int
                or type(_escape) is not types.BuiltinFunctionType
                or peak >= 524288000 or not began_ns <= now < began_ns+55000000000):
            raise TimeoutError('failure-only diagnostic window/resource unfinished')
        return now
    def encoded(value, maximum):
        # Exact builtin containers only: no arbitrary iterator/property/default
        # hook, repr, __str__, or project encoder can execute on this path.
        chunks = []; size = 0; nodes = 0
        def append(raw):
            nonlocal size
            size += len(raw)
            if size > maximum: raise ValueError('diagnostic byte bound')
            chunks.append(raw)
        def visit(item, depth):
            nonlocal nodes
            nodes += 1
            if nodes > 200000 or depth > 128: raise ValueError('diagnostic structure bound')
            if nodes % 64 == 1: failure_gate()
            kind = type(item)
            if item is None: append(b'null')
            elif kind is bool: append(b'true' if item else b'false')
            elif kind is int:
                if item.bit_length() > 4096: raise ValueError('diagnostic integer bound')
                append(str(item).encode('ascii'))
            elif kind is str:
                if len(item) > 262144: raise ValueError('diagnostic string bound')
                append(_escape(item).encode('ascii'))
            elif kind is list or kind is dict:
                append(b'[' if kind is list else b'{')
                for index, entry in enumerate(item if kind is list else item.items()):
                    if index: append(b',')
                    if kind is dict:
                        key, child = entry
                        if type(key) is not str: raise ValueError('diagnostic string key required')
                        visit(key, depth+1); append(b':'); visit(child, depth+1)
                    else: visit(entry, depth+1)
                append(b']' if kind is list else b'}')
            else: raise ValueError('non-builtin diagnostic value')
        visit(value, 0); failure_gate()
        return b''.join(chunks)
    failure_gate()
    # context_raw was encoded before the untrusted search delegation.
    if type(context_raw) is not bytes or len(context_raw) > 65536:
        raise ValueError('bounded predelegation diagnostic context')
    available = capture['returned'] is True
    value = capture['payload'] if available else None
    metadata = None; metadata_saved = False; total_events = None; event_raw = []
    prefix_reason = 'NO_RETURNED_RECORD'; metadata_reason = None
    if type(value) is dict and all(type(key) is str for key in value):
        try:
            metadata = encoded({key: item for key,item in value.items() if key != 'events'}, 1048576)
            metadata_saved = True
        except ValueError:
            metadata_reason = 'BUILTIN_METADATA_OUTPUT_BOUND_OR_TYPE'
        events = value.get('events')
        if type(events) is list:
            total_events = len(events); used = 0; prefix_reason = 'ALL_RETURNED_EVENTS_SAVED'
            for event in events:
                if len(event_raw) >= 2000:
                    prefix_reason = 'DIAGNOSTIC_EVENT_PREFIX_LIMIT'; break
                try: raw = encoded(event, 262144)
                except ValueError:
                    prefix_reason = 'NEXT_EVENT_OUTPUT_BOUND_OR_TYPE'; break
                if used+len(raw)+1 > 3*1048576:
                    prefix_reason = 'DIAGNOSTIC_EVENT_BYTE_LIMIT'; break
                event_raw.append(raw); used += len(raw)+1
        else: prefix_reason = 'RETURNED_EVENTS_NOT_BUILTIN_LIST'
    elif available: metadata_reason = 'RETURNED_VALUE_NOT_BUILTIN_STRING_KEY_DICT'
    # These labels are caller observations, never claims trusted from the payload.
    labels = encoded({'schema':'unit-row-search-failure-diagnostic-v1',
        'diagnostic_only':True,'qualification':'UNQUALIFIED_UNKNOWN_RAW_PREFIX',
        'capture_available':available,'capture_is_builtin_dict':type(value) is dict,
        'engine_return_observed_ns':capture['returned_ns'], 'failure_kind':failure_kind,
        'metadata_saved':metadata_saved,'metadata_omission_reason':metadata_reason,
        'returned_event_count':total_events,'saved_event_count':len(event_raw),
        'omitted_event_count':None if total_events is None else total_events-len(event_raw),
        'event_prefix_reason':prefix_reason,'may_include_post_deadline_unwind':True,
        'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
        'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
        'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}, 65536)
    raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"returned_metadata":'
           +(metadata if metadata_saved else b'null')+b',"events_prefix":['
           +b','.join(event_raw)+b']}\n')
    if len(raw) > 4*1048576+131072: raise ValueError('whole diagnostic output bound')
    def write(name, content):
        failure_gate()
        fd = _open(output_path+'/'+name, _flags, 0o600)
        try:
            offset = 0
            while offset < len(content):
                failure_gate()
                count = _write(fd,content[offset:offset+65536])
                if count <= 0: raise OSError('diagnostic output unfinished')
                offset += count
        finally: _close(fd)
        failure_gate()
    failure_gate(); _mkdir(output_path, 0o700)
    write('unknown-diagnostic.json',raw)
    marker = encoded({'schema':'unit-row-search-failure-diagnostic-completion-v1',
        'file':'unknown-diagnostic.json','sha256':_hash(raw).hexdigest(),'bytes':len(raw),
        'diagnostic_only':True,'positive_joint_gate_accepted':False,
        'ROOT_resource_accepted':False,'terminal_exit2_and_external_failure_closure_required':True}, 1024)+b'\n'
    write('diagnostic-completion.json',marker)
    failure_gate()

def main(argv):
    need(__name__ == '__main__' and len(argv) == 1, 'one Root actual plan')
    end = EARLY_G + 20000000000
    usage, self_id, clock, clock_id, exit_fn = resource.getrusage, resource.RUSAGE_SELF, CLOCK, CLOCK_ID, EXIT
    def tick():
        if (time.clock_gettime_ns is not clock or time.CLOCK_MONOTONIC is not clock_id
                or type(clock_id) is not int or type(clock) is not types.BuiltinFunctionType
                or resource.getrusage is not usage or resource.RUSAGE_SELF is not self_id
                or os._exit is not exit_fn or EXIT is not exit_fn):
            raise RuntimeError('original native clock/resource/exit endpoints changed')
        peak = usage(self_id).ru_maxrss
        now = clock(clock_id)
        if CANCELLED or not EARLY_G <= now < end or peak >= 524288000:
            raise TimeoutError('complete local-degree controls original20/500 reserve unfinished')
        return now
    tick()
    signal.signal(signal.SIGINT, cancel)
    signal.signal(signal.SIGTERM, cancel)
    plan_path = Path(argv[0])
    need(plan_path.is_absolute() and plan_path == plan_path.resolve(), 'canonical Root plan path')
    plan_raw = plan_path.read_bytes()
    need(len(plan_raw) <= 1048576, 'whole bounded Root plan')
    plan = decode(plan_raw)
    need(set(plan) == {'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract',
        'reviews','ROOT_authorization','runtime','limits','resource_rule'}, 'exact current plan12')
    need(plan['schema'] == 'ROOT-unit-row-global-engine-plan-v1'
        and plan['purpose'] in ('unit-row-retained-original-controls','unit-row-retained-domain-controls','unit-row-retained-target-search')
        and plan['resource_rule'] == 'single-owned-process-native-terminal-v1'
        and plan['limits'] == LIMITS and all(type(v) is int for v in plan['limits'].values()), 'original six limits')
    need(type(plan['invocation_id']) is str and 1 <= len(plan['invocation_id']) <= 128
        and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']), 'strict actual nonce')
    need(set(plan['sources']) == {'intake', *FIXED}
        and all(plan['sources'][k] == v for k,v in FIXED.items())
        and plan['sources']['intake']['path'] == str(Path(__file__).resolve())
        and plan['inputs'] == FIXED_INPUTS, 'exact frozen Source and original input2')
    need(sys.platform == 'darwin' and Path(sys.executable).resolve() == Path(plan['runtime']['path']).resolve(), 'native Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw = {role: read_pinned(ref) for role,ref in plan['sources'].items()}
    contract = decode(read_pinned(plan['source_contract']))
    need(contract['schema'] == 'unit-row-retained-domain-cold-Source-contract-v1'
        and contract['sources'] == plan['sources'] and contract['inputs'] == FIXED_INPUTS
        and contract['limits'] == LIMITS, 'whole exact current Source contract')
    need(set(plan['reviews']) == {'ROOT','peer'}, 'author review and distinct whole-Source peer')
    for role,ref in plan['reviews'].items():
        review = decode(read_pinned(ref))
        need(review['scope'] == SCOPE and review['author_identity'] == '/root'
            and review['source'] == plan['sources']['intake'] and review['sources'] == plan['sources']
            and review['source_contract'] == plan['source_contract'] and review['source_only'] is True
            and review['source_review_passed'] is True and type(review['scientific_calls']) is int
            and review['scientific_calls'] == 0 and review['scientific_acceptance'] is False
            and (review['reviewer_identity'] == '/root' if role == 'ROOT'
                 else review['reviewer_identity'] != '/root'), 'genuine current scoped Source reviews')
    grant = decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema'] == 'ROOT-unit-row-global-engine-authorization-v1'
        and grant['author_identity'] == '/root' and grant['actual_execution_authorized'] is True
        and grant['maximum_actual_invocations'] == 1
        and all(grant[k] == plan[k] for k in ('invocation_id','purpose','sources','inputs','source_contract',
            'reviews','runtime','limits','resource_rule','output_directory')), 'exact once-only Root actual grant')
    declaration_raw = read_pinned(FIXED_INPUTS['declaration'])
    profile_raw = read_pinned(FIXED_INPUTS['profile'])
    authority_raw = canonical({'declaration': decode(declaration_raw), 'profile': decode(profile_raw)})
    authority = decode(authority_raw)
    need(authority['profile']['profile_name'] == 'shared-bounded-six-rule-B12-N44-v2'
        and type(authority['declaration']['height']) is int and authority['declaration']['height'] == 24,
        'same original bounded profile and fixed24 boundary')
    modules = {role: load_module(role,source_raw[role]) for role in FIXED}
    support, kernel, membership = (modules[k] for k in ('clean_support','kernel','membership'))
    decoder = json.JSONDecoder(object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)
    sealed_modules = (sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,
        copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types)
    seal = support.CodeSeal(sealed_modules,decoder,end)
    plan_raw_value = canonical(plan)
    anchor_fn, anchor_code, same_fn, same_code = anchor, anchor.__code__, same, same.__code__
    tick_state = anchor_fn(tick)
    method, method_fn = seal.check, support.CodeSeal.check
    method_state = anchor_fn(method_fn)
    strong_functions = all_function_anchors(sealed_modules)
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                    or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not method_fn or not same_fn(method_fn,method_state)
                    or method.__self__ is not seal or method.__func__ is not method_fn
                    or not same_fn(tick,tick_state)):
                raise RuntimeError('original complete Source/native guard changed')
            tick()
            if phase == 0:
                method()
            if any(not same_fn(fn,state) for fn,state in strong_functions):
                raise RuntimeError('original Source code/defaults/cells changed')
        need(canonical(plan) == plan_raw_value and canonical(authority) == authority_raw,
             'complete original plan and private input authority')
    guard_state = anchor_fn(guard)
    def boundary():
        if not same_fn(guard,guard_state):
            raise RuntimeError('original immediate boundary guard changed')
        guard()
        if not same_fn(guard,guard_state):
            raise RuntimeError('original immediate boundary guard changed on return')
    boundary_anchor = anchor_fn(boundary)
    invoke_fn, invoke_code = invoke, invoke.__code__
    local_deadline = invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair':False},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)[1]
    def fresh_language(endpoint_tick):
        # Re-authenticate original full inputs; never reuse proposer-mutated language.
        d, p = read_pinned(FIXED_INPUTS['declaration']), read_pinned(FIXED_INPUTS['profile'])
        need(d == declaration_raw and p == profile_raw, 'same complete original raw inputs')
        value = invoke_fn(membership.make_language,(),{'declaration_raw':d,
            'expected_declaration_sha256':FIXED_INPUTS['declaration']['sha256'],'profile_raw':p,
            'source_bindings':copy.deepcopy(plan['sources']),'kernel_module':kernel,
            'local_deadline':local_deadline,'tick':endpoint_tick},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        need(value.binding['profile_name'] == authority['profile']['profile_name']
            and value.binding['declaration_sha256'] == FIXED_INPUTS['declaration']['sha256']
            and value.binding['profile_sha256'] == FIXED_INPUTS['profile']['sha256'], 'fresh original language binding')
        return value
    fixture_language = fresh_language(tick)
    binding_raw = canonical(fixture_language.binding)
    native_tick = tick
    def proposer_adapter(*,language,state,row,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private proposer epoch unchanged')
        return invoke_fn(modules['proposer'].propose_degree,(),{'language':private,'state':copy.deepcopy(state),
            'row':row,'tick':step},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def fallback_adapter(*,language,state,row,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original fallback epoch')
        return invoke_fn(modules['fallback'].open_fallback,(),{'language':private,
            'state':copy.deepcopy(state),'row':row,'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def certify_adapter(*,language,state,row,completion,checked_candidates,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original completion-check epoch')
        return invoke_fn(modules['engine'].certify_by_current_cover,(),{
            'language':private,'state':copy.deepcopy(state),'row':row,
            'completion':copy.deepcopy(completion),'checked_candidates':copy.deepcopy(checked_candidates),
            'degree_proposer':proposer_adapter,'semantics':modules['degree_checker'],'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def engine_factory(*,initial_state=None,degree_proposer=proposer_adapter,
            fallback=fallback_adapter,certify_fallback=certify_adapter,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private per-engine original semantics authority')
        # Construction/methods/cursor iteration remain inside the surrounding
        # guarded endpoint. No per-method or per-yield Source seal is claimed.
        return modules['engine'].LazyUnitRowEngine(language=private,
            degree_proposer=degree_proposer,semantics=modules['degree_checker'],
            transition_checker=modules['transition'],
            fallback=fallback,certify_fallback=certify_fallback,tick=step,
            initial_state=copy.deepcopy(initial_state),maximum_nodes=128,maximum_events=2000)
    def transition_adapter(*,before,after,rows,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original transition authority')
        snapshot = invoke_fn(modules['transition'].authority_snapshot,(),{
            'language':private,'semantics':modules['degree_checker'],'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        return invoke_fn(modules['transition'].check_transition,(),{
            'language':private,'semantics':modules['degree_checker'],
            'before':copy.deepcopy(before),'after':copy.deepcopy(after),'rows':copy.deepcopy(rows),
            'authority':canonical(snapshot).decode('utf8'),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def refresh_adapter(*,state,candidates,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original known-packet refresh authority')
        return invoke_fn(modules['transition'].refresh_candidates,(),{
            'language':private,'semantics':modules['degree_checker'],
            'state':copy.deepcopy(state),'candidates':copy.deepcopy(candidates),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def scheduler_adapter(*,evidence,generations,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        return invoke_fn(modules['engine'].select_schedule,(),{
            'evidence':copy.deepcopy(evidence),'generations':copy.deepcopy(generations),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    search_capture = {'returned':False,'payload':None,'returned_ns':None}
    def run_original_search():
        engine = engine_factory(initial_state=None,tick=tick)
        value = engine.search()
        # Save ONLY an actual returned payload before invoke's unchanged
        # postboundary may reject it. Never call engine methods after failure.
        search_capture['payload'] = value
        search_capture['returned'] = True
        search_capture['returned_ns'] = clock(clock_id)
        return value
    is_controls = plan['purpose'] != 'unit-row-retained-target-search'
    if is_controls:
        is_original = plan['purpose'] == 'unit-row-retained-original-controls'
        selected_controls = modules['controls'] if is_original else modules['retained_controls']
        control_kwargs = {'language':fixture_language,'engine_factory':engine_factory,
            'degree_proposer':proposer_adapter,'fallback':fallback_adapter,
            'certify_fallback':certify_adapter,'tick':tick}
        if is_original:
            control_kwargs['scheduler'] = scheduler_adapter
        else:
            control_kwargs.update(transition=transition_adapter,refresh=refresh_adapter)
        payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        expected_schema = ('unit-row-lazy-global-controls-v1' if is_original
                           else 'unit-row-retained-domain-controls-v1')
        need(type(payload) is dict and payload['schema'] == expected_schema
            and payload['all_declared_cases_completed'] is True and type(payload['cases']) is list,
            'complete selected original or retained control record; scopes remain distinct')
    else:
        diagnostic_run = Path(plan['output_directory'])
        need(diagnostic_run.is_absolute() and diagnostic_run == diagnostic_run.resolve()
            and not diagnostic_run.exists(), 'fresh canonical search output before delegation')
        diagnostic_path = str(diagnostic_run)
        diagnostic_context = canonical({'purpose':plan['purpose'],'invocation_id':plan['invocation_id'],
            'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
            'language_binding':decode(binding_raw),'joint_began_ns':EARLY_G,
            'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,'limits':LIMITS})
        failure_writer = save_failure_diagnostic
        failure_writer_state = anchor_fn(failure_writer)
        try:
            payload = invoke_fn(run_original_search,(),{},
                boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
            need(type(payload) is dict and payload['schema'] == 'unit-row-lazy-global-search-result-v1'
                and payload['status'] in ('POINT_BOARD_PROPOSAL','EXHAUSTED','UNKNOWN')
                and payload['root_restored'] is True and payload['stack_restored'] is True,
                'fresh original-root search result, not an accepted proof')
        except BaseException as search_error:
            # Failure-only raw retention never replaces the original fault,
            # original20 gate, or exit2. Any partial diagnostic is inventory only.
            failure_kind = 'TimeoutError' if type(search_error) is TimeoutError else 'SOURCE_OR_RUNTIME_FAILURE'
            try:
                if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                        or same is not same_fn or same_fn.__code__ is not same_code
                        or not same_fn(failure_writer,failure_writer_state)):
                    raise RuntimeError('original raw diagnostic writer changed')
                failure_writer(diagnostic_path,diagnostic_context,search_capture,failure_kind,EARLY_G)
            except BaseException:
                pass
            raise
    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1',
        'purpose':plan['purpose'],'controls':payload if is_controls else None,
        'search':None if is_controls else payload,'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},
        'language_binding':decode(binding_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False}) + b'\n'
    need(len(result_raw) <= 4*1048576, 'whole bounded global engine output')
    run = Path(plan['output_directory'])
    need(run.is_absolute() and run == run.resolve() and not run.exists(), 'fresh canonical owned output')
    run.mkdir(mode=0o700)
    result_pin = invoke_fn(write_new,(run/'engine-result.json',result_raw),{},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1','version':VERSION,
        'status':'COMPLETE_WORKER_PENDING_EXTERNAL','invocation_id':plan['invocation_id'],
        'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
        'language_binding':decode(binding_raw),'outputs':[result_pin],
        'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'logical_proof_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False}
    body_raw = canonical(body)+b'\n'
    completion = {'schema':'Q-clean-verifier-response-completion-v1',
        'body_sha256':hashlib.sha256(body_raw).hexdigest(),'body_bytes':len(body_raw),
        'exit_zero_and_coordinator_deadline_required':True}
    response_pin = invoke_fn(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'),{},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    need(sorted(p.name for p in run.iterdir()) == ['engine-result.json','response.jsonl'], 'whole output2')
    receipt = canonical({'schema':'ROOT-unit-row-global-engine-final-observation-v1',
        'outputs':[result_pin,response_pin],'response':response_pin,'pending_external':True,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False}) + b'\n'
    boundary()
    offset = 0
    while offset < len(receipt):
        count = os.write(1,receipt[offset:])
        need(count > 0, 'whole final output receipt')
        offset += count
    boundary()
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code
            or not same_fn(tick,tick_state) or os._exit is not exit_fn or EXIT is not exit_fn):
        raise RuntimeError('original final native/Source endpoint changed')
    tick()
    exit_fn(0)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except BaseException as error:
        try:
            if (os._exit is EXIT and time.clock_gettime_ns is CLOCK
                    and time.CLOCK_MONOTONIC is CLOCK_ID and CLOCK(CLOCK_ID) < EARLY_G+55000000000):
                os.write(2,('UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:
            EXIT(2)
