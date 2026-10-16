"""One fresh fixed-Source complete right-two catalogue/domain audit.

No producer mathematical module executes. The current whole preparation is
raw-authenticated before the existing generic lossless parser; the old codec's
fixed original-buffer decode endpoint is never used. Fixed synchronous Sources,
not a hostile VM/OS guarantee. No proof search, library use or theorem acceptance.
"""
import time
CLOCK=time.clock_gettime_ns
CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_G=CLOCK(CLOCK_ID)
import copy
import hashlib
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import resource
import stat
import sys
import types

EXIT=os._exit
VERSION='right-two-complete-independent-audit-intake-v2'
SCOPE='right-two-complete-independent-audit-intake-Source'
FIXED={
 'auditor':{'path':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/goal-attached-receptors-independent-source-20261015/right-two-auditor/independent_right_two_semantics_v2.py','sha256':'cf7c5fc0482e41f05221d075087eb962a1faa877f1c7c63493f4090f8cc86afa','bytes':46327},
 'codec':{'path':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py','sha256':'d0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df','bytes':5806},
 'clean_support':{'path':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py','sha256':'464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba','bytes':48584}}
LIMITS={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,
        'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}


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


class ParseBudget:
    def __init__(self,boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code):
        self.boundary,self.boundary_anchor=boundary,boundary_anchor
        self.anchor_fn,self.anchor_code,self.same_fn,self.same_code=anchor_fn,anchor_code,same_fn,same_code
    def check(self):
        anchor_fn,anchor_code,same_fn,same_code=self.anchor_fn,self.anchor_code,self.same_fn,self.same_code
        fn,state=self.boundary,self.boundary_anchor
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or fn.__code__ is not state[1] or not same_fn(fn,state)):
            raise RuntimeError('original parser boundary changed before direct call')
        fn()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or fn.__code__ is not state[1] or not same_fn(fn,state)):
            raise RuntimeError('original parser boundary changed after direct call')


def main(argv):
    need(len(argv)==1,'sole exact Root plan path')
    end=EARLY_G+20000000000;usage,self_id,clock,clock_id,exit_fn=resource.getrusage,resource.RUSAGE_SELF,CLOCK,CLOCK_ID,EXIT
    def tick():
        need(time.clock_gettime_ns is clock and time.CLOCK_MONOTONIC is clock_id and resource.getrusage is usage
             and resource.RUSAGE_SELF is self_id and os._exit is exit_fn and EXIT is exit_fn,'original native endpoints')
        now=clock(clock_id)
        if not EARLY_G<=now<end or usage(self_id).ru_maxrss>=524288000:raise TimeoutError('whole cold20/500 reserve unfinished')
        return now
    tick()
    plan_raw=Path(argv[0]).read_bytes();need(len(plan_raw)<=1048576,'whole small Root plan');plan=decode(plan_raw)
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract','reviews',
        'ROOT_authorization','runtime','limits','resource_rule','producer_sources'},'exact current audit plan13')
    need(plan['schema']=='ROOT-right-two-independent-audit-plan-v1' and plan['purpose']=='complete-right-two-independent-audit'
         and plan['resource_rule']=='single-owned-process-native-terminal-v1' and plan['limits']==LIMITS
         and all(type(v) is int for v in plan['limits'].values()),'unchanged actual purpose/budgets')
    need(set(plan['sources'])=={'intake',*FIXED} and all(plan['sources'][r]==p for r,p in FIXED.items()),'exact fixed audit Source4')
    need(plan['sources']['intake']['path']==str(Path(__file__).resolve()),'same actual intake path')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'original Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw={r:read_pinned(ref) for r,ref in plan['sources'].items()}
    need(set(plan['inputs'])=={'declaration','preparation','initial_state','initial_oracle','producer_plan','producer_admission'},'complete current audit input6')
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='right-two-independent-audit-intake-Source-contract-v1' and contract['sources']==plan['sources'],'current Source contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'current complete reviews')
    for role,ref in plan['reviews'].items():
        review=decode(read_pinned(ref));who=review['reviewer_identity']
        need(review['scope']==SCOPE and review['author_identity']=='/root' and review['source']==plan['sources']['intake']
            and review['source_contract']==plan['source_contract'] and review['sources']==plan['sources']
            and review['source_only'] is True and review['source_review_passed'] is True and review['scientific_calls']==0
            and review['scientific_acceptance'] is False and (who=='/root' if role=='ROOT' else who!='/root'),'current author/peer Source4 review')
    grant=decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-right-two-independent-audit-authorization-v1' and grant['author_identity']=='/root'
        and grant['actual_execution_authorized'] is True and grant['invocation_id']==plan['invocation_id']
        and grant['purpose']==plan['purpose'] and grant['sources']==plan['sources'] and grant['inputs']==plan['inputs']
        and grant['producer_sources']==plan['producer_sources'] and grant['limits']==LIMITS,'fresh exact once-only audit grant')
    declaration=decode(read_pinned(plan['inputs']['declaration']))
    producer_plan=decode(read_pinned(plan['inputs']['producer_plan']));admission=decode(read_pinned(plan['inputs']['producer_admission']))
    need(admission['producer_preparation_accepted'] is True and admission['resource_accepted'] is True
        and admission['independent_catalogue_admitted'] is False and producer_plan['sources']==plan['producer_sources']
        and producer_plan['inputs']['declaration']==plan['inputs']['declaration'],'current admitted producer provenance, not old target admission')
    prior_outputs={Path(r['path']).name:r for r in admission['evidence']}
    for role,name in (('preparation','preparation.json'),('initial_state','initial-state.json'),('initial_oracle','initial-oracle-domains.json')):
        need(prior_outputs[name]==plan['inputs'][role],'actual complete producer output pin')
    modules={role:load_module(role,source_raw[role]) for role in ('clean_support','codec','auditor')}
    support,codec,auditor=(modules[r] for r in ('clean_support','codec','auditor'))
    need(auditor.FROZEN_PRODUCER_BINDINGS==plan['producer_sources'] and auditor.DECLARATION_RAW_SHA256==plan['inputs']['declaration']['sha256'],
         'fixed current independent declaration and honest producer Source6')
    decoder=json.JSONDecoder(object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)
    seal=support.CodeSeal((sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,
                          copy,hashlib,math,os,resource,stat,sys,time,types),decoder,end)
    plan_value=hashlib.sha256(canonical(plan)).hexdigest()
    anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor_fn(tick);method,method_fn,method_code=seal.check,support.CodeSeal.check,support.CodeSeal.check.__code__
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not method_fn or method_fn.__code__ is not method_code
                    or method.__self__ is not seal or method.__func__ is not method_fn or tick.__code__ is not tick_state[1]
                    or not same_fn(tick,tick_state)):
                raise RuntimeError('original whole audit guard endpoints changed')
            tick()
            if phase==0:method()
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                    or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
                raise RuntimeError('original native tick changed during direct call')
        need(hashlib.sha256(canonical(plan)).hexdigest()==plan_value,'same current private plan value')
    guard_state=anchor_fn(guard)
    def boundary():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original immediate audit boundary changed')
        guard()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('audit boundary changed after direct call')
    boundary_anchor=anchor_fn(boundary);invoke_fn,invoke_code=invoke,invoke.__code__
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    deadline=invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair':False},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)[1]
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    parser_budget=ParseBudget(boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    raw=read_pinned(plan['inputs']['preparation'],64*1048576)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    text=raw.decode(json.detect_encoding(raw),'surrogatepass');del raw
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    prepared=invoke_fn(codec.parse_lossless_preparation_text,(text,parser_budget),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed');del text
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    result=invoke_fn(auditor.audit_saved_profile,(),{'declaration':declaration,'preparation':prepared,
        'expected_source_bindings':plan['producer_sources'],'source_guard':boundary,'deadline':deadline,
        'initial_state_record':plan['inputs']['initial_state'],'initial_oracle_record':plan['inputs']['initial_oracle']},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    need(result['completed'] is True and result['all_catalogue_primitive_and_initial_domains_accepted'] is True,'whole completed independent result')
    need(result['declaration_sha256']==admission['declaration_value_sha256'] and result['model_epoch']==admission['context_binding']['model_epoch']
        and result['formula_registry_sha256']==admission['context_binding']['formula_registry_sha256']
        and result['primitive_authority_epoch']==admission['context_binding']['primitive_authority_epoch'],'same fresh raw/value/model epochs')
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical audit output');run.mkdir(mode=0o700)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    result_pin=invoke_fn(write_new,(run/'audit-result.json',canonical(result)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    body={'schema':'right-two-independent-audit-response-body-v1','version':VERSION,'status':'COMPLETE_INDEPENDENT_AUDIT_PENDING_EXTERNAL',
        'invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
        'producer_sources':plan['producer_sources'],'result':result_pin,'joint_began_ns':EARLY_G,'joint_deadline_ns':end,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,'ROOT_catalogue_admitted':False,
        'target_proof_accepted':False,'recipient_family_accepted':False,'RL_accepted':False}
    body_raw=canonical(body)+b'\n'
    completion={'schema':'Q-clean-verifier-response-completion-v1','body_sha256':hashlib.sha256(body_raw).hexdigest(),
        'body_bytes':len(body_raw),'exit_zero_and_coordinator_deadline_required':True}
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    response_pin=invoke_fn(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    receipt=canonical({'schema':'right-two-independent-audit-final-observation-v1','response':response_pin,
        'outputs':[result_pin,response_pin],'pending_external':True,'ROOT_catalogue_admitted':False,'ROOT_resource_accepted':False})+b'\n'
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    need(sorted(p.name for p in run.iterdir())==['audit-result.json','response.jsonl'],'complete two-file output')
    offset=0
    while offset<len(receipt):
        n=os.write(1,receipt[offset:]);need(n>0,'whole final receipt');offset+=n
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
            or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
        raise RuntimeError('original final native tick changed')
    tick()
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code
            or tick.__code__ is not tick_state[1] or not same_fn(tick,tick_state)):
        raise RuntimeError('original final native tick changed')
    if os._exit is not exit_fn or EXIT is not exit_fn or clock(clock_id)>=end:raise TimeoutError('final original20 gate')
    exit_fn(0)


if __name__=='__main__':
    try:main(sys.argv[1:])
    except BaseException as error:
        try:
            if time.clock_gettime_ns is CLOCK and time.CLOCK_MONOTONIC is CLOCK_ID and CLOCK(CLOCK_ID)<EARLY_G+55000000000:
                os.write(2,('RIGHT_TWO_AUDIT_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:EXIT(2)
