"""One fixed-Source finite-Horn closed-set certificate stage.

No original producer compiler, kernel or point-graph module executes. The current whole preparation is
raw-authenticated before the existing generic lossless parser; the old codec's
fixed original-buffer decode endpoint is never used. Fixed synchronous Sources,
not a hostile VM/OS guarantee. Generic closure generation and full-relation certificate checking only; no arithmetic nonprovability or positive theorem acceptance.
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
VERSION='right-two-finite-Horn-closed-set-intake-v1'
SCOPE='right-two-finite-Horn-closed-set-intake-Source'
FIXED={'checker': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/finite-horn-closed-set-certificate-source-20261015/finite_horn_closed_set_checker_v1.py', 'sha256': 'f4411df325e0ae2994335458e2e2d27955748c82fd3c36cdd49cc056744d2857', 'bytes': 12589}, 'saturation': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/finite-horn-closed-set-certificate-source-20261015/untrusted_finite_horn_closure_v1.py', 'sha256': '3f7b0c69ce17659bcfd2ae52f31e205318cb6ef45f7751d559149685d080cc13', 'bytes': 3498}, 'codec': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py', 'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df', 'bytes': 5806}, 'clean_support': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba', 'bytes': 48584}}
FIXED_INPUTS={'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'preparation': {'bytes': 38957245, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-ROOT-20261015/preparation-owned-v1/preparation.json', 'sha256': '1573da45b4f3671efd04197791385e5be1a81cefc83338c61f7a3bd63fbbad1e'}, 'producer_plan': {'bytes': 4464, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-ROOT-20261015/ROOT-plan-v1.json', 'sha256': '3ee0d610ae18b2738e6203d4ccd1834e670094e39fa97a45e08aa6add774b389'}, 'catalogue_admission': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/right-two-independent-audit-ROOT-20261015/ROOT-audit-disposition-v1.json', 'sha256': '14ad69316169c62445700940024e90150cb5172d44998a5b5f71313cb233b564', 'bytes': 9778}, 'audit_plan': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/right-two-independent-audit-ROOT-20261015/ROOT-plan-v1.json', 'sha256': 'c591627430d4aad3f5381baa4af968658013725ff14c5feee0daf4d47db12935', 'bytes': 7052}, 'audit_result': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/right-two-independent-audit-ROOT-20261015/audit-owned-v1/audit-result.json', 'sha256': '848f67a03c16f681bd2587f4155b84382fe4f6d88d10c835a8ac98e349f69066', 'bytes': 5595}}
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
    need(plan['schema']=='ROOT-right-two-finite-Horn-closed-set-plan-v1' and plan['purpose']=='right-two-finite-Horn-closed-set-certificate'
         and plan['resource_rule']=='single-owned-process-native-terminal-v1' and plan['limits']==LIMITS
         and all(type(v) is int for v in plan['limits'].values()),'unchanged actual purpose/budgets')
    need(set(plan['sources'])=={'intake',*FIXED} and all(plan['sources'][r]==p for r,p in FIXED.items()),'exact fixed closed-set Source5')
    need(plan['sources']['intake']['path']==str(Path(__file__).resolve()),'same actual intake path')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'original Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw={r:read_pinned(ref) for r,ref in plan['sources'].items()}
    need(plan['inputs']==FIXED_INPUTS,'exact current complete closed-set input6')
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='right-two-finite-Horn-closed-set-intake-Source-contract-v1' and contract['sources']==plan['sources'] and contract['inputs']==plan['inputs'],'current Source contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'current complete reviews')
    for role,ref in plan['reviews'].items():
        review=decode(read_pinned(ref));who=review['reviewer_identity']
        need(review['scope']==SCOPE and review['author_identity']=='/root' and review['source']==plan['sources']['intake']
            and review['source_contract']==plan['source_contract'] and review['sources']==plan['sources']
            and review['source_only'] is True and review['source_review_passed'] is True and review['scientific_calls']==0
            and review['scientific_acceptance'] is False and (who=='/root' if role=='ROOT' else who!='/root'),'current author/peer Source4 review')
    grant=decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-right-two-finite-Horn-closed-set-authorization-v1' and grant['author_identity']=='/root'
        and grant['actual_execution_authorized'] is True and grant['invocation_id']==plan['invocation_id']
        and grant['purpose']==plan['purpose'] and grant['sources']==plan['sources'] and grant['inputs']==plan['inputs']
        and grant['producer_sources']==plan['producer_sources'] and grant['limits']==LIMITS,'fresh exact once-only audit grant')
    declaration_raw=read_pinned(plan['inputs']['declaration']);declaration=decode(declaration_raw)
    producer_plan=decode(read_pinned(plan['inputs']['producer_plan']))
    admission=decode(read_pinned(plan['inputs']['catalogue_admission']))
    audit_plan=decode(read_pinned(plan['inputs']['audit_plan']));audit_result=decode(read_pinned(plan['inputs']['audit_result']))
    need(admission['schema']=='ROOT-right-two-independent-audit-disposition-v1' and admission['independent_catalogue_admitted'] is True
        and admission['all24_initial_domains_admitted'] is True and admission['resource_accepted'] is True,'current independent catalogue admission')
    need(admission['plan']==plan['inputs']['audit_plan'] and audit_plan['inputs']['preparation']==plan['inputs']['preparation']
        and audit_plan['inputs']['declaration']==plan['inputs']['declaration'] and audit_plan['inputs']['producer_plan']==plan['inputs']['producer_plan']
        and audit_plan['producer_sources']==producer_plan['sources']==plan['producer_sources'],'whole current model/declaration/provenance chain')
    prior_outputs={Path(r['path']).name:r for r in admission['evidence']}
    need(prior_outputs['audit-result.json']==plan['inputs']['audit_result'] and audit_result['completed'] is True
        and audit_result['all_catalogue_primitive_and_initial_domains_accepted'] is True and audit_result['source_bindings']==plan['producer_sources']
        and audit_result['census']==admission['census'],'same complete independent relation audit result')
    expected_binding=copy.deepcopy(admission['context_binding'])
    need(expected_binding['declaration_sha256']==plan['inputs']['declaration']['sha256']
        and audit_result['declaration_sha256']==admission['declaration_value_sha256']==hashlib.sha256(canonical(declaration)).hexdigest()
        and all(audit_result[k]==expected_binding[k] for k in ('model_epoch','formula_registry_sha256','primitive_authority_epoch')),'distinct raw/value declaration and complete current epochs')
    modules={role:load_module(role,source_raw[role]) for role in ('clean_support','codec','saturation','checker')}
    support,codec,saturation,checker=(modules[r] for r in ('clean_support','codec','saturation','checker'))
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
        raise RuntimeError('original immediate audit caller changed')
    del text
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate audit caller changed')
    original_binding_raw=canonical(expected_binding);target_raw=canonical(declaration['target'])
    declared_target=decode(target_raw)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    view=invoke_fn(checker.prepare_view,(),{'catalogue':prepared['catalogue'],'declaration_raw':declaration_raw,'expected_binding':expected_binding,'declared_target':declared_target,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    # Retain only the checker-owned immutable graph through the producer boundary.
    immutable_nodes=[view];inspected=0
    while immutable_nodes:
        node=immutable_nodes.pop();inspected+=1
        if type(node) is tuple:immutable_nodes.extend(node)
        else:need(type(node) in (str,int),'deeply immutable exact builtin view')
        if inspected%1024==0:tick()
    original_view=view
    del prepared
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    proposal=invoke_fn(saturation.propose_least_closure,(),{'view':original_view,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    need(view is original_view and canonical(expected_binding)==original_binding_raw and canonical(declared_target)==target_raw,
         'same private original view/binding/target after untrusted generator')
    proposal_raw=canonical(proposal);need(len(proposal_raw)<=1048576,'whole bounded untrusted proposal')
    proposal=decode(proposal_raw)
    need(proposal['schema']=='untrusted-finite-horn-least-closure-result-v1','honest proposal schema, no producer authority')
    candidate=decode(canonical(proposal['closed_set_candidate']))
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    checked=invoke_fn(checker.check_closed_set,(),{'view':original_view,'expected_binding':expected_binding,'declared_target':declared_target,'candidate':candidate,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    need(checked['schema']=='finite-horn-closed-set-check-result-v1' and checked['closed_set_verified'] is True
        and checked['target_excluded'] is True and checked['finite_horn_unreachable'] is True
        and checked['whole_supplied_recipe_array_checked'] is True,'complete independent relation closure and target exclusion')
    need(checked['binding']==expected_binding and checked['formula_count']==admission['census']['formulas']
        and checked['recipe_count']==checked['closure_relations_checked']==admission['census']['recipes']
        and checked['candidate_sha256']==hashlib.sha256(canonical(candidate)).hexdigest(),'same complete audited graph and actual certificate')
    for flag in ('original_target_proved','arithmetic_nonprovability_accepted','point_state_accepted','trajectory_accepted',
                 'full24_accepted','native_accepted','ROOT_resource_accepted','RL_accepted'):
        need(checked[flag] is False,'no enlarged certificate claim:'+flag)
    # Actual-data mutation controls, no authored proof route or expected closure.
    cases=[]
    changed=decode(canonical(candidate));changed['bits_hex']=changed['bits_hex'][:-2];cases.append(('truncated-bits',changed))
    changed=decode(canonical(candidate));changed['binding']['model_epoch']='0'*64;cases.append(('stale-binding',changed))
    changed=decode(canonical(candidate));changed['formula_count']=True;cases.append(('boolean-formula-count',changed))
    bits=bytearray.fromhex(candidate['bits_hex']);n=candidate['formula_count'];target=candidate['target_code']
    changed=decode(canonical(candidate));mutated=bytearray(bits);mutated[target//8]|=1<<(target%8)
    changed['bits_hex']=bytes(mutated).hex();cases.append(('target-included',changed))
    roots=[output for identifier,output,ports in original_view[4] if not ports]
    need(roots,'actual zero-input records for missing-root control')
    changed=decode(canonical(candidate));mutated=bytearray(bits);r=roots[0];mutated[r//8]&=255^(1<<(r%8))
    changed['bits_hex']=bytes(mutated).hex();cases.append(('missing-zero-input-output',changed))
    if n%8:
        changed=decode(canonical(candidate));mutated=bytearray(bits);mutated[-1]|=1<<(n%8)
        changed['bits_hex']=bytes(mutated).hex();cases.append(('nonzero-padding',changed))
    root_codes=set(roots);derived=None
    for identifier,output,ports in original_view[4]:
        tick()
        if ports and output not in root_codes and output not in ports and all((bits[p//8]>>(p%8))&1 for p in ports):
            derived=output;break
    if derived is not None:
        changed=decode(canonical(candidate));mutated=bytearray(bits);mutated[derived//8]&=255^(1<<(derived%8))
        changed['bits_hex']=bytes(mutated).hex();cases.append(('nonzero-input-closure-violation',changed))
    controls=[]
    for label,changed in cases:
        rejected=False
        try:
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate closed-set caller changed')
            invoke_fn(checker.check_closed_set,(),{'view':original_view,'expected_binding':expected_binding,'declared_target':declared_target,'candidate':changed,'tick':tick},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate closed-set caller changed')
        except ValueError:
            rejected=True
        need(rejected,'actual malformed/invalid certificate accepted:'+label)
        controls.append({'control':label,'rejected':True})
    if derived is None:controls.append({'control':'nonzero-input-closure-violation','not_applicable':True,'reason':'No suitable actual nonroot noncyclic derivation edge; no fixture substituted.'})
    need(canonical(expected_binding)==original_binding_raw and canonical(declared_target)==target_raw,'original private checker authority remains unchanged')
    result={'schema':'right-two-finite-Horn-closed-set-result-v1','invocation_id':plan['invocation_id'],
        'context_binding':expected_binding,'checker_result':checked,'producer_observations_untrusted':{k:v for k,v in proposal.items() if k!='closed_set_candidate'},
        'controls':controls,'all_applicable_controls_rejected':True,'immutable_view_only_exposed_to_producer':True,
        'scope':'Checked finite-Horn closed set only; any-length recipe-word exclusion, not arithmetic nonprovability, point search exhaustion or a positive theorem.',
        'ROOT_resource_accepted':False,'ROOT_finite_Horn_unreachability_admitted':False,'target_proof_accepted':False,
        'recipient_family_accepted':False,'GCTS_marking_activated':False,'GCTS_advantage_claimed':False,'RL_accepted':False,
        'full24_accepted':False,'trajectory_accepted':False,'native_Wang_palette_accepted':False}
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical closed-set output');run.mkdir(mode=0o700)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    certificate_pin=invoke_fn(write_new,(run/'closed-set-certificate.json',canonical(candidate)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    result_pin=invoke_fn(write_new,(run/'closed-set-result.json',canonical(result)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    body={'schema':'right-two-finite-Horn-closed-set-response-body-v1','version':VERSION,'status':'COMPLETE_CLOSED_SET_PENDING_EXTERNAL',
        'invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),'sources':plan['sources'],'inputs':plan['inputs'],
        'producer_sources':plan['producer_sources'],'context_binding':expected_binding,'outputs':[certificate_pin,result_pin],
        'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'limits':LIMITS,'resource_rule':plan['resource_rule'],
        'ROOT_resource_accepted':False,'ROOT_finite_Horn_unreachability_admitted':False,'target_proof_accepted':False,
        'arithmetic_nonprovability_accepted':False,'GCTS_marking_activated':False,'GCTS_advantage_claimed':False,'RL_accepted':False}
    body_raw=canonical(body)+b'\n'
    completion={'schema':'Q-clean-verifier-response-completion-v1','body_sha256':hashlib.sha256(body_raw).hexdigest(),
        'body_bytes':len(body_raw),'exit_zero_and_coordinator_deadline_required':True}
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    response_pin=invoke_fn(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    receipt=canonical({'schema':'right-two-finite-Horn-closed-set-final-observation-v1','response':response_pin,
        'outputs':[certificate_pin,result_pin,response_pin],'pending_external':True,'ROOT_finite_Horn_unreachability_admitted':False,
        'ROOT_resource_accepted':False})+b'\n'
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    need(sorted(p.name for p in run.iterdir())==['closed-set-certificate.json','closed-set-result.json','response.jsonl'],'complete three-file output')
    offset=0
    while offset<len(receipt):
        n=os.write(1,receipt[offset:]);need(n>0,'whole final receipt');offset+=n
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
    invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate closed-set caller changed')
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
                os.write(2,('RIGHT_TWO_CLOSED_SET_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:EXIT(2)
