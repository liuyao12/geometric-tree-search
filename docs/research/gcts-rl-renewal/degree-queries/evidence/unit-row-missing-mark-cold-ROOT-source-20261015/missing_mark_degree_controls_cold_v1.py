"""Cold local-degree controls only. Reuses existing native measurement/helpers.
No proof word, donor or library is an input. Not a GCTS search engine.
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
VERSION='unit-row-missing-mark-degree-controls-cold-v1'
SCOPE='unit-row-missing-mark-degree-controls-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'controls': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-controls-source-20261015/missing_mark_degree_controls_v2.py', 'sha256': '4fc9e409aad995a4b7eea2afbf11d447b75a7e70d4b2d58ffc9dad1cc10c59d5', 'bytes': 20072}}
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
    need(plan['schema'] == 'ROOT-unit-row-degree-controls-plan-v1'
        and plan['purpose'] == 'unit-row-local-degree-controls'
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
    need(contract['schema'] == 'unit-row-degree-controls-cold-Source-contract-v1'
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
                 else review['reviewer_identity'] not in ('/root',)), 'genuine current scoped Source reviews')
    grant = decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema'] == 'ROOT-unit-row-degree-controls-authorization-v1'
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
    def checker_adapter(*,language,state,row,proposal,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'fresh private checker epoch unchanged')
        return invoke_fn(modules['degree_checker'].check_degree_evidence,(),{'language':private,
            'state':copy.deepcopy(state),'row':row,'proposal':copy.deepcopy(proposal),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def carrier_adapter(*,language,maximum_nodes,tick):
        need(type(maximum_nodes) is int and maximum_nodes in (1,2), 'direct control carrier bounds1or2 only')
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'fresh private control carrier epoch unchanged')
        values = []
        for formula in modules['proposer'].iter_bounded_formulas(
                language=private,maximum_nodes=maximum_nodes,tick=step):
            step()
            if len(values) >= 1000:
                raise TimeoutError('direct tiny control carrier output incomplete')
            values.append(copy.deepcopy(formula))
        return values
    controls = invoke_fn(modules['controls'].run_controls,(),{'language':fixture_language,
        'proposer':proposer_adapter,'checker':checker_adapter,'carrier':carrier_adapter,'tick':tick},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    need(type(controls) is dict and controls['schema'] == 'unit-row-degree-controls-v1'
        and controls['all_declared_cases_completed'] is True and type(controls['cases']) is list,
        'complete local control record, not GCTS search')
    result_raw = canonical({'schema':'ROOT-unit-row-local-degree-control-result-v1',
        'controls':controls,'language_binding':decode(binding_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False}) + b'\n'
    need(len(result_raw) <= 4*1048576, 'whole bounded local control output')
    run = Path(plan['output_directory'])
    need(run.is_absolute() and run == run.resolve() and not run.exists(), 'fresh canonical owned output')
    run.mkdir(mode=0o700)
    result_pin = invoke_fn(write_new,(run/'degree-controls.json',result_raw),{},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    body = {'schema':'ROOT-unit-row-degree-controls-response-body-v1','version':VERSION,
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
    need(sorted(p.name for p in run.iterdir()) == ['degree-controls.json','response.jsonl'], 'whole output2')
    receipt = canonical({'schema':'ROOT-unit-row-degree-controls-final-observation-v1',
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
                os.write(2,('UNIT_ROW_DEGREE_CONTROLS_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:
            EXIT(2)
