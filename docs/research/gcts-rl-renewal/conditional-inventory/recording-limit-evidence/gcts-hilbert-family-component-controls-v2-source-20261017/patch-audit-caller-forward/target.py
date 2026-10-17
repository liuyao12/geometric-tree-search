"""SOURCE ONLY: one original Hilbert context, native COMPONENT CONTROLS.

Catalogue-generated local placements are API controls, never discovered proofs.
All setup/admission/controls/output share original native20; Root alone may grant.
"""
import time
CLOCK=time.clock_gettime_ns
CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_G=CLOCK(CLOCK_ID)
import base64
import binascii
import builtins
import copy
import dataclasses
import functools
import gzip
import hashlib
import io
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import re
import resource
import select
import signal
import stat
import struct
import sys
import types
import typing
import zlib
from collections.abc import Mapping,Sequence
EXIT=os._exit
VERSION='ROOT-Hilbert-shared-family-component-controls-cold-v2-child-unknown'
SCOPE='ROOT-Hilbert-shared-family-component-controls-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
LIMITS={'joint_seconds':20,'aggregate_owned_bytes':536870912,'failure_only_seconds':55,'owned_seconds':60,'caller_seconds':90,'caller_finish_reserve_seconds':1}
FIXED={'point_core': {'bytes': 31300, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py', 'sha256': 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'}, 'compact_graph': {'bytes': 42946, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/reversible-classification-row-mask-source-20261013/compact_point_graph_reversible_v4.py', 'sha256': 'c7af8a415670dd54a3177fda823a0c3fb0bbcc582e59125a974ea19de06748e6'}, 'compact_decoder': {'bytes': 14720, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-compiler-source-20261012/compact_catalog_decoder_v1.py', 'sha256': '46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293'}, 'dynamic_graph_adapter': {'bytes': 35568, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-batched-membership-source-20261013/compact_dynamic_graph_batched_v7.py', 'sha256': '4ff74a120327ed7e75ff844038e1c75650530c4434a2054b3c956264ea279423'}, 'dynamic_lifecycle_adapter': {'bytes': 29230, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-dynamic-source-20261012/compact_cluster_lifecycle_v2.py', 'sha256': '677c48c7aebfecf0c83c8daa8bf8e873d0be1e415906afa6687f0b9652e33719'}, 'logical_oracle': {'bytes': 24588, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-independent-oracles-source-20261013/hilbert_fresh_catalog_oracle_v2.py', 'sha256': '3b6aee8d9b0c1668f2ccf4e0d3b5e7e87dc9e0dd6579e55308e74c3992d6b3cc'}, 'context_checker': {'bytes': 64540, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/fresh-equality-first-proof-runtime-source-20261013/fresh_equality_context_and_final24_certificate_v3.py', 'sha256': '5d03d088c2d1b7f90e98fb7e28819ab0643b74f6786953c6107d4d2535c2377b'}, 'clean_support': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba', 'bytes': 48584}, 'host_adapter': {'path': '/private/tmp/gcts-hilbert-shared-family-adapter-v3-source-20261017/hilbert_shared_family_admission_adapter_v3.py', 'sha256': 'cb20ac2b95a8c84b3c0230065dd13c9fa1b1f9945e329f5ecbfa2bd38d674296', 'bytes': 31330}, 'collector': {'path': '/private/tmp/gcts-hilbert-shared-family-collector-v2-source-20261017/hilbert_shared_family_selected_dag_collector_v2.py', 'sha256': '7160d774e3026fadf4ad959931ad0847028ad47308a57c2ac5480a3f39bf260a', 'bytes': 21800}, 'consumer': {'path': '/private/tmp/gcts-hilbert-shared-family-consumer-source-20261017/hilbert_shared_family_preference_consumer_v1.py', 'sha256': '7819736573d25c4937a82afdee2e2c8b7187039c15606eb3fe37d1715bdf0c74', 'bytes': 19341}, 'miner': {'path': '/private/tmp/gcts-interface-coupled-miner-source-20261017/receptor_family_miner_v3.py', 'sha256': '7873c8a071079726151020191d574fcc3289a7e56b6ef91ccac244a1d003013c', 'bytes': 37218}, 'producer': {'path': '/private/tmp/gcts-hilbert-shared-family-adapter-source-20261017/dependencies/generic_family_expander.py', 'sha256': 'f32e069a65ba21903cb6211772334e5b36ea8598bd189ca06800a8d9030d12a2', 'bytes': 51898}, 'expansion_checker': {'path': '/private/tmp/gcts-hilbert-shared-family-adapter-source-20261017/dependencies/generic_family_checker.py', 'sha256': '4358026b3eeb9c96366d522c65b5f6d6d4acd7336a0816360da5cd44233a93b1', 'bytes': 56670}, 'component_controls': {'path': '/private/tmp/gcts-hilbert-family-component-controls-v2-source-20261017/hilbert_family_component_controls_v2.py', 'sha256': '1de9e74e177ad52bf085e4d37ddd7de7a0a7d3c47e9c3d37ef3cf33a9ff4fdcf', 'bytes': 18467}}
QUALIFICATIONS={'fresh-inc-point-chain-w': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/fresh-equality-first-proof-progress-20261013/fresh-inc-point-chain-w/qualified-context-v1.json', 'sha256': '3cbd8b500eb73a412af010ad5f09e6b54d525a63bc2e4849806627b743f76c56', 'bytes': 10586}, 'fresh-inc-reversed-line-chain': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/fresh-equality-first-proof-progress-20261013/fresh-inc-reversed-line-chain/qualified-context-v1.json', 'sha256': '47690792ccabca60caaf2e54409ca30d9d5dfeb51b33bad0664139fa5a2e60ef', 'bytes': 10652}}

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


def load_module(role,raw,pin):
    # Native source-origin joins require the real frozen source filename.
    name='_hilbert_component_'+role;need(name not in sys.modules,'fresh private module')
    module=types.ModuleType(name);module.__file__=pin['path']
    sys.modules[name]=module;exec(compile(raw,pin['path'],'exec'),module.__dict__)
    return module


def stdlib_gate(runtime,sources):
    need(type(runtime)is dict and set(runtime)=={'binary','python_version','stdlib_root','stdlib_closure'},
        'exact Root-owned native runtime and loaded stdlib byte closure')
    need(sys.platform=='darwin' and sys.flags.isolated==1 and sys.flags.no_site==1
        and 'sitecustomize'not in sys.modules and 'usercustomize'not in sys.modules,
        'fresh isolated no-site native Darwin process')
    need(type(runtime['python_version'])is list and runtime['python_version']==list(sys.version_info[:3])
        and Path(sys.executable).resolve()==Path(runtime['binary']['path']).resolve(),
        'actual pinned interpreter/version')
    read_pinned(runtime['binary'],256*1048576)
    root=Path(runtime['stdlib_root']);need(root.is_absolute()and root==root.resolve()and root==Path(os.__file__).resolve().parent, 'actual interpreter stdlib root')
    closure=runtime['stdlib_closure'];need(type(closure)is list,'whole loaded stdlib closure')
    refs={}
    for pin in closure:
        need(type(pin)is dict and set(pin)=={'path','sha256','bytes'}and pin['path']not in refs,'unique stdlib raw pins')
        refs[pin['path']]=pin
        p=Path(pin['path']);need(root in p.parents,'stdlib files stay in declared interpreter stdlib tree')
        read_pinned(pin,32*1048576)
    allowed={v['path']for v in sources.values()}
    used=[]
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=str(Path(filename).resolve())
        if path in allowed:continue
        need(path in refs,'no unpinned transitive code/module outside exact stdlib closure')
        used.append(path)
    return sorted(set(used))


def encode_result_transport(expanded_raw):
    need(type(expanded_raw)is bytes and len(expanded_raw)<=16*1048576,'whole expanded component result cap')
    compressed=zlib.compress(expanded_raw,6)
    envelope={'schema':'ROOT-Hilbert-family-component-lossless-envelope-v1',
        'encoding':'zlib+base64','expanded_bytes':len(expanded_raw),
        'expanded_sha256':hashlib.sha256(expanded_raw).hexdigest(),
        'compressed_bytes':len(compressed),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
        'payload_base64':base64.b64encode(compressed).decode('ascii')}
    encoded=canonical(envelope)+b'\n';need(len(encoded)<=4*1048576,'whole encoded component result cap')
    return encoded


def main(argv):
    need(__name__=='__main__'and len(argv)==1,'one once-granted Root component-control data plan')
    end=EARLY_G+20000000000
    usage,self_id,clock,clock_id,exit_fn=resource.getrusage,resource.RUSAGE_SELF,CLOCK,CLOCK_ID,EXIT
    def tick():
        if (time.clock_gettime_ns is not clock or time.CLOCK_MONOTONIC is not clock_id
            or type(clock_id)is not int or type(clock)is not types.BuiltinFunctionType
            or resource.getrusage is not usage or resource.RUSAGE_SELF is not self_id
            or os._exit is not exit_fn or EXIT is not exit_fn):
            raise RuntimeError('original native clock/resource/exit endpoints changed')
        peak=usage(self_id).ru_maxrss;now=clock(clock_id)
        if CANCELLED or not EARLY_G<=now<end or peak>=524288000:
            raise TimeoutError('whole Hilbert component original20/500 reserve unfinished')
        return now
    tick();signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
    path=Path(argv[0]);need(path.is_absolute()and path==path.resolve(),'canonical Root plan path')
    plan_raw=path.read_bytes();need(len(plan_raw)<=1048576,'whole bounded Root plan');plan=decode(plan_raw)
    need(type(plan)is dict and set(plan)=={'schema','invocation_id','purpose','context_id',
        'output_directory','sources','inputs','source_contract','reviews','ROOT_authorization','runtime','limits','resource_rule'},
        'exact separately named current component plan')
    need(plan['schema']=='ROOT-Hilbert-family-component-controls-plan-v1'
        and plan['purpose']=='hilbert-shared-family-component-controls'
        and type(plan['context_id'])is str and plan['context_id']in QUALIFICATIONS
        and plan['resource_rule']=='single-owned-process-native-terminal-v1'
        and plan['limits']==LIMITS and all(type(v)is int for v in plan['limits'].values()), 'same whole native budget/model')
    need(type(plan['invocation_id'])is str and 1<=len(plan['invocation_id'])<=128
        and all(c.isascii()and(c.isalnum()or c in '-_.:')for c in plan['invocation_id']),'strict actual nonce')
    need(set(plan['sources'])=={'intake',*FIXED}and all(plan['sources'][k]==v for k,v in FIXED.items())
        and plan['sources']['intake']['path']==str(Path(__file__).resolve())
        and plan['inputs']=={'qualified_context':QUALIFICATIONS[plan['context_id']]}, 'exact current source/context map')
    source_raw={role:read_pinned(pin)for role,pin in plan['sources'].items()};tick()
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='ROOT-Hilbert-family-component-controls-Source-contract-v2'
        and contract['sources']==plan['sources']and contract['qualified_contexts']==QUALIFICATIONS
        and contract['limits']==LIMITS,'whole current source contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'Root and distinct whole current composition review')
    for role,pin in plan['reviews'].items():
        review=decode(read_pinned(pin))
        need(review['scope']==SCOPE and review['author_identity']=='/root/hilbert_advice_controls'
            and review['source']==plan['sources']['intake']
            and review['sources']==plan['sources']and review['source_contract']==plan['source_contract']
            and review['source_only']is True and review['source_review_passed']is True
            and type(review['scientific_calls'])is int and review['scientific_calls']==0
            and review['scientific_acceptance']is False
            and(review['reviewer_identity']=='/root'if role=='ROOT'else review['reviewer_identity']not in('/root','/root/hilbert_advice_controls')),
            'genuine exact current Source reviews, no component/runtime substitution')
    grant=decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-Hilbert-family-component-controls-authorization-v1'
        and grant['author_identity']=='/root'and grant['actual_execution_authorized']is True
        and type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1
        and all(grant[k]==plan[k]for k in('invocation_id','purpose','context_id','sources','inputs',
            'source_contract','reviews','runtime','limits','resource_rule','output_directory')),
        'separate Root once/native actual grant required')
    stdlib_before=stdlib_gate(plan['runtime'],plan['sources']);tick()
    # Context/code filenames preserve original native ROOT and source authority.
    modules={role:load_module(role,source_raw[role],FIXED[role])for role in FIXED};tick()
    support=modules['clean_support'];context_checker=modules['context_checker']
    decoder=json.JSONDecoder(object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)
    # Preserve the existing cold guard's exact critical stdlib set. Other
    # admitted stdlib modules can maintain ordinary implementation caches.
    sealed_modules=(sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,
        copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types,base64,binascii,zlib)
    seal=support.CodeSeal(sealed_modules,decoder,end)
    plan_value=canonical(plan);authority_value=canonical({'sources':FIXED,'qualifications':QUALIFICATIONS})
    anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor_fn(tick);method,method_fn=seal.check,support.CodeSeal.check;method_state=anchor_fn(method_fn)
    strong_functions=all_function_anchors(sealed_modules);generated=[]
    def guard():
        for phase in (0,1):
            if(anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                or same_fn.__code__ is not same_code or support.CodeSeal.check is not method_fn
                or not same_fn(method_fn,method_state)or method.__self__ is not seal
                or method.__func__ is not method_fn or not same_fn(tick,tick_state)):
                raise RuntimeError('original complete native Source guard changed')
            tick()
            if phase==0:method()
            if any(not same_fn(fn,state)for fn,state in strong_functions):
                raise RuntimeError('original Source code/defaults/cells changed')
            if any(support.class_state(cls)!=snapshot for cls,snapshot in generated):
                raise RuntimeError('actual generated graph/catalog MRO endpoint changed')
        need(canonical(plan)==plan_value and canonical({'sources':FIXED,'qualifications':QUALIFICATIONS})==authority_value,
            'same full plan and original context pins')
    guard_state=anchor_fn(guard)
    def boundary():
        if not same_fn(guard,guard_state):raise RuntimeError('immediate boundary guard changed')
        guard()
        if not same_fn(guard,guard_state):raise RuntimeError('immediate boundary changed after delegation')
    boundary_anchor=anchor_fn(boundary);invoke_fn,invoke_code=invoke,invoke.__code__
    def call(fn,args=(),kwargs=None):
        return invoke_fn(fn,args,{}if kwargs is None else kwargs,boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    stdlib_after=call(stdlib_gate,(plan['runtime'],plan['sources']))
    closed=call(context_checker.ClosedInputs)
    qualification=call(closed.json,(plan['inputs']['qualified_context'],))
    need(qualification['instance_id']==plan['context_id'],'exact declared static context')
    admitted=call(context_checker.admitted_context,(closed,qualification));header=admitted[0]
    need(header['boundary']['required']==[[0,row]for row in range(24)],'full original24 required rows')
    runtime_roles=('point_core','compact_graph','compact_decoder','dynamic_graph_adapter','dynamic_lifecycle_adapter')
    runtime_sources=[{'role':role,**FIXED[role]}for role in runtime_roles]
    graph_type=call(modules['dynamic_graph_adapter'].make_dynamic_graph_type,
        (modules['point_core'],modules['compact_graph'],modules['compact_decoder']),{'runtime_sources':runtime_sources})
    graph=call(graph_type,kwargs={'header_pin':qualification['catalog']})
    generated.extend((cls,support.class_state(cls))for cls in (graph_type,type(graph.catalog)))
    wire=call(context_checker.SelectedWire,(header,))
    need(call(wire.model_epoch)==graph.model_epoch and canonical(graph.catalog.header)==canonical(header),
        'complete unchanged catalogue/original epoch')
    result=call(modules['component_controls'].run_component_controls,kwargs={
        'graph':graph,'point_core':modules['point_core'],'host_adapter':modules['host_adapter'],
        'collector':modules['collector'],'miner':modules['miner'],'producer':modules['producer'],
        'expansion_checker':modules['expansion_checker'],'consumer':modules['consumer'],
        'context_checker':context_checker,'logical_oracle':modules['logical_oracle'],
        'closed_inputs':closed,'qualification':qualification,'tick':tick})
    need(result['schema']=='hilbert-shared-family-component-controls-v1'
        and result['version']==modules['component_controls'].VERSION
        and result['status']in('CHECKED_COMPONENT_CONTROLS','UNKNOWN')
        and result['full_root_semantic_rollback_checked']is True, 'whole returned native COMPONENT-control record')
    call(closed.close);call(stdlib_gate,(plan['runtime'],plan['sources']))
    payload={'schema':'ROOT-Hilbert-family-component-controls-result-v1','purpose':plan['purpose'],
        'context_id':plan['context_id'],'sources':plan['sources'],'inputs':plan['inputs'],
        'original_static_qualification':qualification,'original_header':header,
        'model_epoch':graph.model_epoch,'component_controls':result,
        'authenticated_input_closure':list(closed.pins.values()),'loaded_stdlib_before':stdlib_before,
        'loaded_stdlib_after':stdlib_after,'discovered_proof':False,'logical_proof_accepted':False,
        'all_five_rules_qualified':False,'whole_engine_qualified':False,'complete_GCTS_model_accepted':False,
        'trajectory_accepted':False,'runtime_qualified':False,'ROOT_resource_accepted':False}
    expanded=call(canonical,(payload,))+b'\n';encoded=call(encode_result_transport,(expanded,))
    run=Path(plan['output_directory']);need(run.is_absolute()and run==run.resolve()and not run.exists(), 'fresh canonical Root-owned outputs')
    run.mkdir(mode=0o700);output=call(write_new,(run/'component-result.json',encoded))
    body={'schema':'ROOT-Hilbert-family-component-controls-response-v1','version':VERSION,
        'status':'COMPLETE_WORKER_PENDING_EXTERNAL','invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],'outputs':[output],'component_status':result['status'],
        'model_epoch':graph.model_epoch,'joint_began_ns':EARLY_G,'joint_deadline_ns':end,
        'CLOCK_DOMAIN':CLOCK_DOMAIN,'limits':LIMITS,'resource_rule':plan['resource_rule'],
        'logical_proof_accepted':False,'whole_engine_qualified':False,'ROOT_resource_accepted':False}
    body_raw=canonical(body)+b'\n'
    completion={'schema':'ROOT-Hilbert-family-component-response-completion-v1',
        'body_sha256':hashlib.sha256(body_raw).hexdigest(),'body_bytes':len(body_raw),
        'exit_zero_and_external_native_terminal_required':True}
    response=call(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'))
    need(sorted(p.name for p in run.iterdir())==['component-result.json','response.jsonl'],'whole owned output2')
    final=canonical({'schema':'ROOT-Hilbert-family-component-controls-final-observation-v1',
        'outputs':[output,response],'pending_external':True,'logical_proof_accepted':False,
        'whole_engine_qualified':False,'ROOT_resource_accepted':False})+b'\n'
    boundary();offset=0
    while offset<len(final):
        count=os.write(1,final[offset:]);need(count>0,'whole final output receipt');offset+=count
    boundary()
    if(invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code
        or not same_fn(tick,tick_state)or os._exit is not exit_fn or EXIT is not exit_fn):
        raise RuntimeError('original final native/Source endpoint changed')
    tick();exit_fn(0)


if __name__=='__main__':
    try:main(sys.argv[1:])
    except BaseException as error:
        try:
            if(os._exit is EXIT and time.clock_gettime_ns is CLOCK
                and time.CLOCK_MONOTONIC is CLOCK_ID and CLOCK(CLOCK_ID)<EARLY_G+55000000000):
                os.write(2,('HILBERT_COMPONENT_CONTROLS_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:EXIT(2)
