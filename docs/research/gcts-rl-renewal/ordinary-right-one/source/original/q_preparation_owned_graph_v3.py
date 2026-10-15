"""SOURCE ONLY owned-call payload for one complete Q preparation.

No project imports. Future ROOT cold wrapper injects the exact raw-compiled four
modules and anchored source guard; it owns actual reviews/10leaf/10owner/runtime/
closure/lifecycle. This payload never dispatches a child, search or solver.
It constructs the full declared catalogue and initial graph, checks each graph
candidate's arity encoding, and exports every row domain. These are producer
checks, not an independent mathematical/domain admission.
"""
import copy
import hashlib
import json
import time
import types

VERSION='Q-complete-catalogue-and-initial-empty-Gamma-domains-preparation-only-v1'

def require(ok,label):
    if not ok:raise ValueError(label)

def text(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)

def function_state(fn):
    require(type(fn) is types.FunctionType,'exact zero-argument caller guard')
    return (fn,fn.__code__,tuple(id(v) for v in fn.__defaults__ or ()),
        tuple((k,id(v)) for k,v in sorted((fn.__kwdefaults__ or {}).items())),
        tuple((id(c),id(c.cell_contents)) for c in fn.__closure__ or ()))

def effective_methods(obj):
    rows=[];seen=set();namespace=getattr(obj,'__dict__',{})
    for cls in type(obj).__mro__:
        for name,value in sorted(vars(cls).items()):
            if name in seen:continue
            seen.add(name)
            if isinstance(value,property):
                require(name not in namespace,'no shadowed endpoint property')
                rows.append((cls,name,value,tuple(function_state(fn) for fn in (value.fget,value.fset,value.fdel) if fn is not None)))
            elif type(value) is types.FunctionType:
                require(name not in namespace,'no instance method shadow')
                method=getattr(obj,name)
                require(type(method) is types.MethodType and method.__self__ is obj and method.__func__ is value,'exact effective graph method')
                rows.append((cls,name,value,function_state(value)))
    return tuple(rows)

def prepare_owned(*,declaration,kernel_module,catalogue_module,graph_module,source_bindings,source_guard,deadline):
    started=time.perf_counter();anchor=function_state(source_guard)
    def guard():
        if function_state(source_guard)!=anchor:raise ValueError('original delegated cold-source boundary changed')
        source_guard()
        if function_state(source_guard)!=anchor:raise ValueError('delegated guard changed after use')
        if time.perf_counter()>=deadline:raise TimeoutError('complete Q payload unresolved; no admitted prefix')
    guard()
    model=catalogue_module.prepare(declaration,kernel_module=kernel_module,source_bindings=source_bindings,deadline=deadline)
    guard()
    graph=graph_module.PointGraph(height=model['height'],formulas=model['formula_codes'],recipe_data=model['recipes'],
        context=model['context'],authority=model['authority'],fixed_marks=model['boundary']['fixed_marks'],
        roots=model['boundary']['roots'],seed_keys=(),fixture=False,source_bindings=source_bindings)
    methods=effective_methods(graph);guard()
    require(graph.initial_selected==() and graph.order==[] and graph.totals==[0]*24 and graph.roots==(0,)*24,
        'empty Gamma has no hidden seed/dummy assumption and every root obligation exists')
    require(all(r.witness['rule']!='assumption' for r in graph.recipes),'zero occurrence recipes')
    require(graph_module.MARKING_VERSION==catalogue_module.MARKING,'matching new unary profile marking version')
    # The full factor representation is saved. This does not enumerate/accept a
    # sampled/top-k candidate list as proof of complete initial domains.
    initial=graph.semantic_state();decision=graph.decision()
    require(len(initial['domains'])==24 and len(initial['roots'])==24 and initial['order']==[], 'whole twenty-four-row initial state')
    if effective_methods(graph)!=methods:raise ValueError('effective graph endpoints changed during preparation')
    result={'schema':VERSION,'catalogue':model,'initial_state':initial,'initial_decision':{
        'kind':decision.kind,'row':decision.row,'count':decision.count,'generation':decision.generation},
        'census':copy.deepcopy(model['census']),'initial_legal_domain_counts':[d['count'] for d in initial['domains']],
        'initial_legal_candidate_count':sum(d['count'] for d in initial['domains']),
        'graph_constructions':1,'target_searches':0,'native_queries':0,'RL_training_runs':0,
        'independent_catalogue_or_point_admission':False,'whole_proof_accepted':False,'universal_theorem_discovered':False,
        'full_PA_accepted':False,'native_accepted':False,'full_trajectory_accepted':False,
        'cold_payload_seconds_before_final_guards':time.perf_counter()-started,
        'cost_scope':'Shared20s includes full catalogue/kernel/graph/initial-state serialization and final guards. Cold loading/files/final print/cleanup remain inside separately frozen60s/512MiB/caller90s owned bounds; this payload dispatches nothing.'}
    # Complete strict serialization is deferred to the caller's immediate
    # owned streamed preparation write. No accepted output precedes that full
    # traversal, its raw pin, and the shared deadline/Source guards.
    guard()
    if effective_methods(graph)!=methods:raise ValueError('graph endpoint changed before return')
    guard();return result, graph
