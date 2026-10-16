"""Unexecuted finite Q controls; ROOT supplies cold authenticated endpoints.

The original empty-Gamma right-one catalogue is untouched. Local synthetic
prior formulas and opaque scheduling fixtures are side-condition/state tests,
not proofs, hypotheses or proposals for the scientific target. No search runs.
"""
import copy
import itertools
import json
import time
import types

VERSION='arithmetic-Q-streamed-complete-domain-controls-v2'


def require(value,label):
    if not value:raise ValueError(label)


def text(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def function_state(fn):
    require(type(fn) is types.FunctionType,'exact caller callback function')
    return (fn,fn.__code__,tuple(id(v) for v in fn.__defaults__ or ()),
        tuple((k,id(v)) for k,v in sorted((fn.__kwdefaults__ or {}).items())),
        tuple((id(c),id(c.cell_contents)) for c in fn.__closure__ or ()))


def methods(obj):
    seen=set();rows=[];namespace=getattr(obj,'__dict__',{})
    for cls in type(obj).__mro__:
        for name,descriptor in sorted(vars(cls).items()):
            if name in seen:continue
            seen.add(name)
            if isinstance(descriptor,property):
                require(name not in namespace,'no instance property shadow')
                rows.append((cls,name,descriptor,tuple(function_state(f) for f in (descriptor.fget,descriptor.fset,descriptor.fdel) if f is not None)))
            elif type(descriptor) is types.FunctionType:
                require(name not in namespace,'no instance function shadow')
                effective=getattr(obj,name)
                require(type(effective) is types.MethodType and effective.__self__ is obj
                        and effective.__func__ is descriptor,'same effective bound endpoint')
                rows.append((cls,name,descriptor,function_state(descriptor)))
    return tuple(rows)


def literal_domain_rows(graph,*,deadline):
    """Independent complete parametric relation, no production factors/legality.

    Reads literal recipe input/output integers, current totals/marks/exclusions.
    Builds every reference mask directly; binary Cartesian counts subtract only
    incompatible shared rows. This compact census represents every candidate,
    rather than materializing a potentially huge full placement list.
    """
    def tick():
        if time.perf_counter()>=deadline:raise TimeoutError('whole Q domain census unfinished')
    for row in range(graph.height):
        tick();factors=[];mask_cache={}
        def source_mask(code,port):
            k=(code,port)
            if k not in mask_cache:
                refs=[s for s in range(row) if (1,s) not in graph.marks or graph.marks[1,s]==code]
                if (2+port,row) in graph.marks:
                    chosen=row+graph.marks[2+port,row];refs=[s for s in refs if s==chosen]
                mask_cache[k]=sum(1<<s for s in refs)
            return mask_cache[k]
        if graph.totals[row]==0:
            for recipe in graph.recipes:
                tick()
                if (1,row) in graph.marks and graph.marks[1,row]!=recipe.output:continue
                a=len(recipe.inputs)
                if a==0:left=right=0;different=False;count=1
                elif a==1:
                    left=source_mask(recipe.inputs[0],0);right=0;different=False;count=bin(left).count('1')
                elif a==2:
                    left=source_mask(recipe.inputs[0],0);right=source_mask(recipe.inputs[1],1)
                    different=recipe.inputs[0]!=recipe.inputs[1]
                    count=bin(left).count('1')*bin(right).count('1')-(bin(left&right).count('1') if different else 0)
                else:raise ValueError('outside literal zero/unary/binary grammar')
                if count:factors.append([recipe.index,left,right,different,count])
        by_recipe={f[0]:f for f in factors};removed=[]
        for key in sorted(graph.excluded[row]):
            tick();f=by_recipe.get(key.recipe)
            if f is None:continue
            recipe=graph.recipes[key.recipe]
            if len(key.refs)!=len(recipe.inputs) or any(type(s) is not int or not 0<=s<row for s in key.refs):continue
            allowed=(not key.refs or ((f[1]>>key.refs[0])&1 and (len(key.refs)==1 or
                ((f[2]>>key.refs[1])&1 and (not f[3] or key.refs[0]!=key.refs[1])))))
            if allowed:removed.append(key.data())
        base=sum(f[4] for f in factors)
        yield dict(factors=factors,base_count=base,excluded_legal=removed,count=base-len(removed))
    tick()


def literal_domains(graph,*,deadline):
    # Tiny nonlogical fixtures only; production callers consume every row below.
    return list(literal_domain_rows(graph,deadline=deadline))


def production_domain(graph,row):
    d=graph.domains[row]
    return dict(factors=[[f.recipe,f.left,f.right,f.different,f.count] for f in d.factors],
        base_count=d.base_count,excluded_legal=[k.data() for k in d.excluded_legal],count=d.count)


def state_chunks(graph):
    # Exactly canonical(PointGraph.semantic_state()), without a full24 copy.
    small={'totals':list(graph.totals),'marks':[[*p,v,graph.mark_refs[p]] for p,v in sorted(graph.marks.items())],
        'order':[k.data() for k in graph.order],'selected_generations':[[k.data(),graph.selected[k]] for k in sorted(graph.selected)],
        'roots':list(graph.roots),'excluded':[[k.data() for k in sorted(s)] for s in graph.excluded],'model_epoch':graph.model_epoch}
    yield '{'
    for index,name in enumerate(sorted([*small,'domains'])):
        if index:yield ','
        yield text(name)+':'
        if name=='domains':
            yield '['
            for row in range(graph.height):
                if row:yield ','
                yield text(production_domain(graph,row))
            yield ']'
        else:yield text(small[name])
    yield '}'


def compare_snapshot(chunks,record):
    # Complete byte equality, not only a hash; record must be a caller-owned pin.
    from pathlib import Path
    import hashlib
    require(set(record)=={'path','sha256','bytes'},'exact owned snapshot pin')
    path=Path(record['path']);require(path.is_absolute() and path==path.resolve(),'canonical owned witness path')
    count=0;h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in chunks:
            raw=chunk.encode('utf8')
            require(stream.read(len(raw))==raw,'complete streamed state bytes match owned snapshot')
            count+=len(raw);h.update(raw)
        require(stream.read(1)==b'','no omitted state field or trailing prefix')
    require(count==record['bytes'] and h.hexdigest()==record['sha256'],'same whole snapshot bytes/pin')


def checked_domain_chunks(graph,*,deadline):
    # Every row and factor is checked before its full witness is streamed.
    yield '['
    rows=0
    for row,independent in enumerate(literal_domain_rows(graph,deadline=deadline)):
        require(independent==production_domain(graph,row),'every complete production domain equals separate literal relation')
        if row:yield ','
        yield text(independent);rows+=1
    require(rows==graph.height,'all required domains covered, never a shortlist')
    yield ']'


def current_decision_data(graph):
    d=graph.decision()
    return dict(kind=d.kind,row=d.row,count=d.count,generation=d.generation)


def literal_decision(graph,domains):
    frontier=[r for r,t in enumerate(graph.totals) if t<1]
    dead=[r for r in frontier if domains[r]['count']==0]
    forced=[r for r in frontier if domains[r]['count']==1]
    def generation(row):return min([graph.roots[row]]+[g for k,g in graph.selected.items() if k.row==row])
    if dead:row=min(dead);kind='dead'
    elif forced:row=min(forced);kind='forced'
    elif not frontier:return dict(kind='complete',row=None,count=0,generation=None)
    else:row=min(frontier,key=lambda r:(generation(r),domains[r]['count'],r));kind='branch'
    return dict(kind=kind,row=row,count=domains[row]['count'],generation=generation(row))


def run_controls(*,declaration,model,owned_graph,initial_record,initial_decision,kernel_module,graph_module,source_bindings,source_guard,write_snapshot,deadline):
    began=time.perf_counter();anchor=function_state(source_guard);sink_anchor=function_state(write_snapshot);tests=[];objects=[];snapshots=[]
    def guard():
        if function_state(source_guard)!=anchor:raise ValueError('original delegated callback changed')
        if function_state(write_snapshot)!=sink_anchor:raise ValueError('original owned snapshot writer changed')
        source_guard()
        if function_state(source_guard)!=anchor:raise ValueError('callback changed during delegation')
        for obj,state in objects:
            require(methods(obj)==state,'same actual constructed checker/graph/executor effective methods')
        if time.perf_counter()>=deadline:raise TimeoutError('complete Q controls unfinished, no accepted prefix')
    def track(obj):objects.append((obj,methods(obj)));guard();return obj
    def check(value,label):guard();require(value,label);tests.append(label)
    def reject(call,classes,label):
        guard()
        try:call()
        except classes as exc:guard();tests.append(label);return dict(type=type(exc).__name__,message=str(exc))
        raise ValueError(label)
    theory=declaration['theory'];parameters=declaration['parameters']
    def checker(gamma=()):return track(kernel_module.QChecker(theory,parameters,list(gamma),deadline=deadline))
    guard();check(declaration['ordered_Gamma']==[] and model['declaration']==declaration,
        'exact original empty context and declared quantified right-one grammar')
    z=['fun','zero',[]];n=['var',parameters[0]];x=['var','x']
    universal=['all','x',['all',parameters[0],['eq',x,n]]]
    capture_free=['all','fresh0',['eq',n,['var','fresh0']]]
    kernel=checker()
    require(kernel.substitute(universal[2],'x',n)==capture_free,'capture-avoiding literal fresh0 result')
    check(kernel.command(dict(rule='instantiate',universal=universal,term=n,formula=['imp',universal,capture_free]),[])==['imp',universal,capture_free],
          'open-parameter instantiation schema uses exact capture-safe renaming')
    reject(lambda:kernel.command(dict(rule='instantiate',universal=universal,term=n,
        formula=['imp',universal,['all',parameters[0],['eq',n,n]]]),[]),ValueError,'captured wrong instantiation formula rejected')
    shadow=['all','x',['eq',x,n]]
    check(kernel.substitute(shadow,'x',z)==shadow,'shadowed substitution binder stops free substitution')
    other=['all','fresh0',['eq',x,n]]
    check(kernel.substitute(['all',parameters[0],other],'x',n)==['all','fresh1',['all','fresh0',['eq',n,['var','fresh1']]]],
          'occupied fresh0 selects exact next unused fresh suffix')
    deep=['eq',x,n]
    for i in reversed(range(32)):deep=['all','fresh'+str(i),deep]
    reject(lambda:kernel.substitute(['all',parameters[0],deep],'x',n),kernel_module.BudgetExceeded,
        'full deterministic fresh namespace overflow is UNKNOWN, no partial result')
    partial_prior=[['eq',n,n]]
    closure=['all',parameters[0],partial_prior[0]]
    check(kernel.command(dict(rule='generalize',variable=parameters[0],source=0,formula=closure),partial_prior)==closure,
          'generalization has one genuine source, synthetic prior is not a proof')
    unused=['eq',n,z];full_context=checker([unused])
    reject(lambda:full_context.command(dict(rule='generalize',variable=parameters[0],source=0,
        formula=['all',parameters[0],['eq',z,z]]),[['eq',z,z]]),ValueError,
        'free generalization variable in unused original hypothesis rejects')
    repeated=checker([unused,unused])
    check(repeated.gamma==[unused,unused],'duplicate original context occurrences remain ordered')
    reject(lambda:repeated.command(dict(rule='generalize',variable=parameters[0],source=0,formula=closure),partial_prior),
        ValueError,'duplicate free-context occurrences do not weaken generalization condition')
    reject(lambda:kernel.command(dict(rule='generalize',variable=parameters[0],source=0,formula=closure),[]),ValueError,
        'self-or-future unary source rejected')
    reject(lambda:kernel.command(dict(rule='generalize',variable=parameters[0],source=True,formula=closure),partial_prior),ValueError,
        'boolean unary source is not an integer prior index')
    reject(lambda:kernel.command(dict(rule='assumption',index=0,formula=['eq',z,z]),[]),ValueError,
        'empty original Gamma has no hidden assumption')
    reject(lambda:kernel.command(dict(rule='axiom',name='AZ',formula=['eq',['var','foreign'],z]),[]),ValueError,
        'foreign free parameter rejected')
    reject(lambda:kernel.command(dict(rule='nat_induction',formula=closure),partial_prior),ValueError,
        'induction and additional proof rules remain unsupported')
    graph=track(owned_graph)
    check(type(graph) is graph_module.PointGraph and graph.height==model['height'] and graph.context==model['context']
          and graph.authority==model['authority'] and graph.formulas==model['formula_codes'] and graph.source_bindings==source_bindings,
          'same actual payload-owned complete production graph, no second construction')
    check(graph.order==[] and graph.initial_selected==() and graph.totals==[0]*24,
          'production graph has no selected hypothesis, proof seed or dummy row')
    compare_snapshot(state_chunks(graph),initial_record);guard()
    initial_domains=write_snapshot('Q-initial-oracle-domains-v2.json',checked_domain_chunks(graph,deadline=deadline));guard()
    check(True,'every full initial24 parametric domain independently reconstructed')
    # The domain oracle checked every row; small scalar records suffice to
    # evaluate priority without duplicating factor arrays.
    counts=[{'count':d.count} for d in graph.domains]
    check(literal_decision(graph,counts)==initial_decision, 'complete initial global scheduler agrees with literal reference')
    snapshots.append(dict(label='complete-original-initial',state=initial_record,independent_domains=initial_domains,decision=initial_decision))
    unary=next((r for r in graph.recipes if len(r.inputs)==1),None)
    check(unary is not None and unary.witness['rule']=='generalize','declared complete inventory exposes genuine unary generalization')
    unary_key=graph_module.Key(unary.index,1,(0,));t,m=graph.point_data(unary_key);guard()
    expected_m=sorted([[1,1,unary.output],[1,0,unary.inputs[0]],[2,1,-1]])
    check(t==[[0,1,1]] and m==expected_m and not any(p[0]==3 for p in m),
          'actual unary positive output/source mark/one offset; second port absent, not zero')
    check(graph.decorate(unary_key)['command']['source']==0,'unary decorated primitive command uses genuine source index')
    reject(lambda:graph.point_data(graph_module.Key(unary.index,0,(0,))),ValueError,'nonprior unary point reference rejected')
    reject(lambda:graph.point_data(graph_module.Key(unary.index,1,(0,0))),ValueError,'duplicated second unary port rejected')
    root=graph.checkpoint();root_record=initial_record;executor=track(graph_module.Executor(graph))
    try:
        d=graph.decision();check(d.kind in ('branch','forced'),'actual full model has nonempty initial chosen domain')
        first=next(graph.candidates(d.row));executor.step(first);guard()
        after_record=write_snapshot('Q-after-one-step-state-v2.json',state_chunks(graph));guard()
        after_domains=write_snapshot('Q-after-one-step-oracle-domains-v2.json',checked_domain_chunks(graph,deadline=deadline));guard()
        check(True,'full24 domains after one generic scheduler primitive reconstructed')
        snapshots.append(dict(label='one-canonical-scheduler-step-not-a-proof',placement=first.data(),state=after_record,
            independent_domains=after_domains,decision=literal_decision(graph,[{'count':d.count} for d in graph.domains])))
    finally:
        graph.rollback(root);guard();compare_snapshot(state_chunks(graph),root_record);guard()
    check(True,'exact full production marks/refcounts/generations/exclusions/domain rollback')
    # Tiny synthetic scheduling fixtures. Their opaque recipes are explicitly
    # outside the mathematical Q inventory; no kernel or target endpoint uses them.
    fixture_formulas=[['eq',z,z],['eq',['fun','succ',[z]],z],['eq',z,['fun','succ',[z]]]]
    raw=[dict(id='nonlogical-fixture-'+str(i),primitive_witness=dict(rule='fixture_zero',formula=fixture_formulas[code]),
              ordered_premise_formulas=[]) for i,code in enumerate((0,0,1))]
    auth={'activated':False,'native_accepted':False,'scope':'nonlogical-Q-scheduler-controls-only'}
    auth['epoch']=graph_module.digest(auth)
    def fixture(height,fixed=(),roots=None):
        return track(graph_module.PointGraph(height=height,formulas=fixture_formulas,recipe_data=raw,
            context={'theory':theory,'ordered_local_premises':[]},authority=auth,fixed_marks=fixed,
            roots=roots,fixture=True,source_bindings=source_bindings))
    fixture_records=[]
    for label,height,fixed,roots,expected in (
        ('global-dead-before-forced',3,[(1,0,1),(1,2,2)],[0,0,0],('dead',2)),
        ('global-forced-before-branch',3,[(1,0,1)],[0,0,0],('forced',0)),
        ('earlier-generation-before-smaller-degree',2,[(1,1,0)],[0,1],('branch',0))):
        tiny=fixture(height,fixed,roots);tiny_oracle=literal_domains(tiny,deadline=deadline);decision=tiny.decision();guard()
        check(tiny_oracle==tiny.semantic_state()['domains'] and (decision.kind,decision.row)==expected,
              label+' specialized nonlogical complete fixture')
        check(''.join(state_chunks(tiny))==text(tiny.semantic_state()),
              label+' complete streaming state protocol equals unchanged full scalar snapshot')
        fixture_records.append(dict(label=label,state=tiny.semantic_state(),decision=literal_decision(tiny,tiny_oracle),
            independently_reconstructed_domains=tiny_oracle,mathematical_recipe_inventory=False))
    zero=fixture(1,[(1,0,0)]);absent=fixture(1)
    check(zero.domains[0].count==2 and absent.domains[0].count==3 and zero.marks[1,0]==0,
          'synthetic assigned-zero mark differs from absent point')
    forced=fixture(1,[(1,0,1)]);cp=forced.checkpoint();before=text(forced.semantic_state());sole=next(forced.candidates(0))
    try:
        forced.exclude_failed_child(sole);guard()
        check(forced.decision().kind=='dead' and literal_domains(forced,deadline=deadline)==forced.semantic_state()['domains'],
              'temporary unproved sole-key exclusion tests actual global dead bookkeeping')
    finally:forced.rollback(cp);guard()
    check(text(forced.semantic_state())==before,'specialized exclusion transaction restores full state exactly')
    result=dict(schema=VERSION,completed=True,tests=tests,control_count=len(tests),
        complete_production_snapshots=snapshots,unary_placement=graph.decorate(unary_key),
        specialized_nonlogical_fixtures=fixture_records,original_ordered_Gamma=[],
        synthetic_prior_is_a_proof=False,fixture_recipes_enter_production=False,induction_supported=False,
        target_searches=0,DFS_search_calls=0,native_queries=0,RL_training_runs=0,
        independent_mathematical_catalogue_admission=False,universal_theorem_discovered=False,
        full_PA_accepted=False,native_accepted=False,full24_board_accepted=False,full_trajectory_accepted=False,
        complete_controls_seconds_before_final_guards=time.perf_counter()-began,
        scope='Producer-authored separate literal parametric domain/finite controls, not distinct-author semantic replay or theorem discovery.')
    text(result);guard();return result
