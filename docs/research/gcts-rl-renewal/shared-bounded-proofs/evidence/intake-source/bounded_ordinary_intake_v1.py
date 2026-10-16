"""UNEXECUTED: one-process implicit-language ordinary positive endpoint.

The sole authenticated Root plan selects exact Sources and only original
logical declaration plus frozen language policy. No catalogue, saved proof,
library, receptor binding or target route is consumed. Ordinary proposals are
untrusted. A fresh raw-authenticated private language checks EVERY expanded
primitive, then unchanged1717 independently checks the original closed target.
Negative search is UNKNOWN. There is no complete carrier/count/legacy/GCTS,
point-board/trajectory/native-Wang/marking/RL or resource admission here.
Earliest native G precedes all further imports/setup. All delegates are fully
Source guarded before/after, with original resource-only ticks inside language
and proposer; original1717 retains full Source guard callback. Exact true
terminal/postprobe and owned/caller/resource admission remain external/Root.
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
VERSION='shared-bounded-ordinary-positive-cold-intake-v1'
SCOPE='shared-bounded-ordinary-positive-cold-intake-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
FIXED={'membership': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v1.py', 'sha256': 'ffce8882b0bb676cc517cf13ef13339dbcb34fb99464f0c0db69dd33487b9596', 'bytes': 20073}, 'proposer': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/untrusted_bounded_forward_producer_v1.py', 'sha256': '887ee06e6f771524d5ab9df88cce27c6100c17ba7c069f14f4b6028d6208f34e', 'bytes': 15446}, 'kernel': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9', 'bytes': 10323}, 'checker': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py', 'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3', 'bytes': 46514}, 'clean_support': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba', 'bytes': 48584}}
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
    need(__name__=='__main__' and len(argv)==1,'TOP early-clock worker and sole exact Root plan path')
    end=EARLY_G+20000000000
    usage,self_id,clock,clock_id,exit_fn=resource.getrusage,resource.RUSAGE_SELF,CLOCK,CLOCK_ID,EXIT
    def tick():
        if (time.clock_gettime_ns is not clock or time.CLOCK_MONOTONIC is not clock_id or type(clock_id) is not int
                or type(clock) is not types.BuiltinFunctionType or resource.getrusage is not usage
                or resource.RUSAGE_SELF is not self_id or os._exit is not exit_fn or EXIT is not exit_fn):
            raise RuntimeError('original native clock/resource/exit endpoints changed')
        peak=usage(self_id).ru_maxrss
        now=clock(clock_id)
        if CANCELLED or not EARLY_G<=now<end or peak>=524288000:
            raise TimeoutError('whole cold setup/proposal/membership/check/output original20/500 reserve unfinished')
        return now
    tick()
    signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
    plan_path=Path(argv[0]);need(plan_path.is_absolute() and plan_path==plan_path.resolve(),'canonical actual plan path')
    plan_raw=plan_path.read_bytes();need(len(plan_raw)<=1048576,'complete bounded Root plan');plan=decode(plan_raw);tick()
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract',
        'reviews','ROOT_authorization','runtime','limits','resource_rule'},'exact current sole plan12')
    need(plan['schema']=='ROOT-shared-bounded-ordinary-positive-plan-v1' and plan['purpose']=='shared-bounded-ordinary-positive-word'
        and plan['resource_rule']=='single-owned-process-native-terminal-v1' and plan['limits']==LIMITS
        and all(type(v) is int for v in plan['limits'].values()),'same profile/purpose and inherited six caps')
    need(type(plan['invocation_id']) is str and 1<=len(plan['invocation_id'])<=128
        and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']),'strict current nonce')
    need(set(plan['sources'])=={'intake',*FIXED} and all(plan['sources'][k]==v for k,v in FIXED.items()),'exact frozen Source6')
    need(plan['sources']['intake']['path']==str(Path(__file__).resolve()) and plan['inputs']==FIXED_INPUTS,'same actual intake and original input2')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'exact native Darwin runtime')
    read_pinned(plan['runtime']);tick()
    source_raw={}
    for role,ref in plan['sources'].items():source_raw[role]=read_pinned(ref);tick()
    contract=decode(read_pinned(plan['source_contract']));tick()
    need(contract['schema']=='shared-bounded-ordinary-positive-cold-Source-contract-v1' and contract['sources']==plan['sources']
        and contract['inputs']==FIXED_INPUTS and contract['limits']==LIMITS,'current complete Source/input contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'genuine distinct current complete Source reviews')
    for role,ref in plan['reviews'].items():
        review=decode(read_pinned(ref));tick();who=review['reviewer_identity']
        need(review['scope']==SCOPE and review['author_identity']=='/root/hilbert_ordering_diagnosis'
            and review['source']==plan['sources']['intake'] and review['sources']==plan['sources']
            and review['source_contract']==plan['source_contract'] and review['source_only'] is True
            and review['source_review_passed'] is True and type(review['scientific_calls']) is int and review['scientific_calls']==0
            and review['scientific_acceptance'] is False
            and (who=='/root' if role=='ROOT' else who not in ('/root','/root/hilbert_ordering_diagnosis')),'actual current complete author/Root/peer Source binding')
    grant=decode(read_pinned(plan['ROOT_authorization']));tick()
    need(grant['schema']=='ROOT-shared-bounded-ordinary-positive-authorization-v1' and grant['author_identity']=='/root'
        and grant['actual_execution_authorized'] is True and grant['invocation_id']==plan['invocation_id']
        and all(grant[k]==plan[k] for k in ('purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory')),
        'fresh exact Root Source/input once-only grant')
    declaration_raw=read_pinned(FIXED_INPUTS['declaration']);profile_raw=read_pinned(FIXED_INPUTS['profile']);tick()
    declaration,profile=decode(declaration_raw),decode(profile_raw)
    need(profile['schema']=='ROOT-shared-bounded-six-rule-language-policy-v2' and profile['profile_name']=='shared-bounded-six-rule-B12-N44-v2',
        'selected frozen language policyV2 only; no old count-policy relabel')
    need(type(declaration['height']) is int and declaration['height']==24,'original word24 boundary')
    authority={'schema':'shared-bounded-original-authority-v1','declaration_raw_sha256':FIXED_INPUTS['declaration']['sha256'],
        'profile_raw_sha256':FIXED_INPUTS['profile']['sha256'],'declaration':copy.deepcopy(declaration),'profile':copy.deepcopy(profile)}
    authority_raw=canonical(authority);authority_hash=hashlib.sha256(authority_raw).hexdigest()
    modules={role:load_module(role,source_raw[role]) for role in ('clean_support','kernel','membership','proposer','checker')}
    support,kernel,membership,proposer,checker=(modules[k] for k in ('clean_support','kernel','membership','proposer','checker'))
    decoder=json.JSONDecoder(object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)
    sealed_modules=(sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,
        copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types)
    seal=support.CodeSeal(sealed_modules,decoder,end)
    plan_value=hashlib.sha256(canonical(plan)).hexdigest()
    anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor_fn(tick);method,method_fn=seal.check,support.CodeSeal.check;method_state=anchor_fn(method_fn)
    strong_functions=all_function_anchors(sealed_modules)
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not method_fn or not same_fn(method_fn,method_state)
                    or method.__self__ is not seal or method.__func__ is not method_fn
                    or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
                raise RuntimeError('original complete Source/native guard changed')
            tick()
            if phase==0:method()
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                    or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)
                    or any(not same_fn(fn,state) for fn,state in strong_functions)):
                raise RuntimeError('strong original code/default-entry/cell custody changed')
        need(hashlib.sha256(canonical(plan)).hexdigest()==plan_value and canonical(authority)==authority_raw,
             'same private plan and separately held original input authority')
    guard_state=anchor_fn(guard)
    def boundary():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original immediate boundary changed')
        guard()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original boundary changed after direct call')
    boundary_anchor=anchor_fn(boundary);invoke_fn,invoke_code=invoke,invoke.__code__
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    local_deadline=invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair':False},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)[1]
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    language=invoke_fn(membership.make_language,(),{'declaration_raw':declaration_raw,'expected_declaration_sha256':FIXED_INPUTS['declaration']['sha256'],'profile_raw':profile_raw,'source_bindings':copy.deepcopy(plan['sources']),'kernel_module':kernel,'local_deadline':local_deadline,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    need(type(language.binding) is dict and set(language.binding)=={'profile_name','profile_sha256','declaration_sha256','logical_input_sha256','source_bindings_sha256','language_epoch'}
        and language.binding['profile_name']==profile['profile_name'] and language.binding['profile_sha256']==FIXED_INPUTS['profile']['sha256']
        and language.binding['declaration_sha256']==FIXED_INPUTS['declaration']['sha256'] and type(language.binding['language_epoch']) is str,'complete original language binding')
    language_binding_raw=canonical(language.binding)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    proposal=invoke_fn(proposer.propose_word,(),{'language':language,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    # Only the return is untrusted. No producer-held language or context object
    # is reused for final authority. All internal budget callbacks were native
    # guidance; full immutable Source/plan/authority seals enclose delegates.
    del language
    proposal_raw=canonical(proposal);need(len(proposal_raw)<=2*1048576,'whole bounded proposal/diagnostics; no accepted prefix')
    proposal=decode(proposal_raw)
    need(type(proposal) is dict and proposal['schema']=='shared-bounded-ordinary-proposal-v1'
        and proposal['status'] in ('CANDIDATE_NOT_VERIFIED','UNKNOWN'),'untrusted positive-or-UNKNOWN proposal only')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    fresh_declaration_raw=invoke_fn(read_pinned,(FIXED_INPUTS['declaration'],),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    fresh_profile_raw=invoke_fn(read_pinned,(FIXED_INPUTS['profile'],),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    need(fresh_declaration_raw==declaration_raw and fresh_profile_raw==profile_raw,'same complete raw original inputs after untrusted search')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    validator=invoke_fn(membership.make_language,(),{'declaration_raw':fresh_declaration_raw,'expected_declaration_sha256':FIXED_INPUTS['declaration']['sha256'],'profile_raw':fresh_profile_raw,'source_bindings':copy.deepcopy(plan['sources']),'kernel_module':kernel,'local_deadline':local_deadline,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    need(canonical(validator.binding)==language_binding_raw,'fresh private validator is the identical original language')
    candidate=proposal['candidate'];membership_receipt=None;word_receipt=None
    if candidate is not None:
        need(proposal['status']=='CANDIDATE_NOT_VERIFIED' and type(candidate) is dict
            and candidate['schema']=='shared-bounded-ordinary-word-candidate-v1' and canonical(candidate['binding'])==language_binding_raw
            and candidate['origin']=='untrusted-on-demand-known-fact-search' and candidate['full_word_not_prefix'] is True
            and type(candidate['commands']) is list and 1<=len(candidate['commands'])<=24,'one complete original-language primitive word')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        invoke_fn(support.inspect_json_tree,(candidate['commands'],),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        membership_receipt=invoke_fn(membership.check_word,(),{'language':validator,'commands':candidate['commands'],'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        need(membership_receipt['schema']=='shared-bounded-six-rule-word-membership-v1' and membership_receipt['completed'] is True
            and membership_receipt['all_commands_in_language'] is True and membership_receipt['original_Gamma_preserved'] is True
            and membership_receipt['exact_target'] is True and membership_receipt['logical_acceptance'] is False
            and membership_receipt['command_count']==len(candidate['commands']) and len(membership_receipt['rows'])==len(candidate['commands'])
            and membership_receipt['commands_sha256']==hashlib.sha256(canonical(candidate['commands'])).hexdigest()
            and canonical(membership_receipt['binding'])==language_binding_raw,'whole current bounded-language membership independently enforced')
        # Fresh original context comes from authenticated raw bytes after producer,
        # separately from both the producer instance and membership receipt.
        original=decode(fresh_declaration_raw)
        need(canonical(original)==canonical(authority['declaration']),'exact whole original declaration after search/membership')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        word_receipt=invoke_fn(checker.check_primitive_word,(),{'theory':original['theory'],'parameters':original['parameters'],'original_Gamma':original['ordered_Gamma'],'commands':candidate['commands'],'target':original['target'],'source_guard':boundary,'deadline':local_deadline,'maximum_visits':5000000},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate positive caller changed')
        need(word_receipt['completed'] is True and word_receipt['original_Gamma_target_sequent_accepted'] is True
            and word_receipt['original_ordered_Gamma']==original['ordered_Gamma'] and word_receipt['parameters']==original['parameters']
            and word_receipt['target']==original['target'] and word_receipt['theory_sha256']==hashlib.sha256(canonical(original['theory'])).hexdigest()
            and word_receipt['commands_sha256']==hashlib.sha256(canonical(candidate['commands'])).hexdigest(),
            'fresh unchanged1717 complete word acceptance for exact original closed target')
    else:
        need(proposal['status']=='UNKNOWN','missing candidate remains UNKNOWN, never exhaustive failure')
    del validator
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical output directory')
    run.mkdir(mode=0o700)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    proposal_pin=invoke_fn(write_new,(run/'search-result.json',proposal_raw+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    check_result={'schema':'shared-bounded-ordinary-word-check-result-v1','language_binding':decode(language_binding_raw),
        'profile_source':FIXED_INPUTS['profile'],'declaration_source':FIXED_INPUTS['declaration'],
        'word_membership':membership_receipt,'independent_word':word_receipt,'word_checked':word_receipt is not None,
        'target_proof_accepted':False,'complete_ground_counts_accepted':False,'complete_legacy_embedding_accepted':False,
        'complete_GCTS_model_accepted':False,'GCTS_marking_activated':False,'GCTS_advantage_claimed':False,
        'full24_accepted':False,'trajectory_accepted':False,'native_Wang_palette_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    check_pin=invoke_fn(write_new,(run/'word-check.json',canonical(check_result)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    body={'schema':'shared-bounded-ordinary-response-body-v1','version':VERSION,'status':'COMPLETE_WORKER_PENDING_EXTERNAL',
        'invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
        'language_binding':decode(language_binding_raw),'logical_authority_sha256':authority_hash,'search_status':proposal['status'],
        'word_membership_checked':membership_receipt is not None,'independent_word_checked':word_receipt is not None,'outputs':[proposal_pin,check_pin],
        'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,'limits':LIMITS,
        'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,'target_proof_accepted':False,
        'recipient_family_accepted':False,'complete_ground_counts_accepted':False,'complete_legacy_embedding_accepted':False,
        'complete_GCTS_model_accepted':False,'GCTS_marking_activated':False,'full24_accepted':False,'full_trajectory_accepted':False,
        'native_Wang_palette_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'finite_exhaustion_accepted':False}
    body_raw=canonical(body)+b'\n'
    completion={'schema':'Q-clean-verifier-response-completion-v1','body_sha256':hashlib.sha256(body_raw).hexdigest(),
        'body_bytes':len(body_raw),'exit_zero_and_coordinator_deadline_required':True}
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    response_pin=invoke_fn(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    need(sorted(p.name for p in run.iterdir())==['response.jsonl','search-result.json','word-check.json'],'complete owned output3')
    receipt=canonical({'schema':'shared-bounded-ordinary-final-observation-v1','response':response_pin,
        'outputs':[proposal_pin,check_pin,response_pin],'pending_external':True,'target_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    offset=0
    while offset<len(receipt):
        n=os.write(1,receipt[offset:]);need(n>0,'whole final receipt');offset+=n
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate positive caller changed')
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
            or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
        raise RuntimeError('original final native tick changed')
    tick()
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
            or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
        raise RuntimeError('original final native tick changed during call')
    if (os._exit is not exit_fn or EXIT is not exit_fn or time.clock_gettime_ns is not clock
            or time.CLOCK_MONOTONIC is not clock_id or CANCELLED or clock(clock_id)>=end):
        raise TimeoutError('final original20/cancel/exit gate')
    exit_fn(0)


if __name__=='__main__':
    try:main(sys.argv[1:])
    except BaseException as error:
        try:
            if (os._exit is EXIT and time.clock_gettime_ns is CLOCK and time.CLOCK_MONOTONIC is CLOCK_ID
                    and type(CLOCK_ID) is int and CLOCK(CLOCK_ID)<EARLY_G+55000000000):
                os.write(2,('SHARED_BOUNDED_ORDINARY_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:EXIT(2)


