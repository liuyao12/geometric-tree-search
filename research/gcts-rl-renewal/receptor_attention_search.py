"""Original resumable scheduler with branch-local receptor attention.

Derived from the frozen quantified search. Only policy preparation and the
policy scoring hook differ; all point domains, joins and fallback are retained.
"""
import collections,random,time
import resumable_clusters as R
import adaptive_receptor_clusters as C
import movable_proof_regions as M
from quantifier_family_join import Join
import receptor_attention as Attention
FEATURES=Attention.FEATURES;FIXED_WEIGHTS=R.FIXED_WEIGHTS
review=R.review;ordered=R.ordered
def search(model,library=(),mode='base',weights=None,stochastic=False,seed=0,
           attempts=20000,seconds=10,proposal_limit=32,indexed=True):
    if mode not in ('base','fixed','policy'):raise ValueError('declared search lane')
    if mode=='policy' and (weights is None or len(weights)!=len(FEATURES)):raise ValueError('frozen policy dimension')
    started=time.perf_counter();join=None
    prep=time.perf_counter();support=Attention.Support(model) if mode=='policy' else None
    prep_seconds=time.perf_counter()-prep
    initial=model.initial();graph=M.Graph(model,initial)
    metrics=collections.Counter();hints=[];events=[];rng=random.Random(seed);found=None;best=initial;solution=()
    def tick():
        if metrics['attempts']>=attempts or time.perf_counter()-started>seconds:raise C.Budget()
        metrics['attempts']+=1
    def visit(state,g,hint,completed):
        nonlocal found,best,solution,join
        metrics['nodes']+=1;kind,point,keys=g.decision(state)
        tree=dict(kind=kind,point=point,hint_in=hint['id'] if hint else None,children=[])
        metrics['peak_candidates']=max(metrics['peak_candidates'],sum(len(d) for d in g.domains.values()))
        if time.perf_counter()-started>seconds:tree['cutoff']='entry_wall';return None,tree
        if len(state.order)>len(best.order) and kind!='dead':best=state
        active,trace=review(model,state,g,hint,kind,point,keys);tree['review']=trace
        if hint:
            metrics['hint_reviews']+=1;metrics['hint_'+trace['phase']]+=1
            if trace['phase']=='completed':
                completed=completed+(dict(id=hint['id'],start=len(hints[hint['id']]['chosen']),end=len(state.order),item=hint['item']),)
        if kind=='dead':metrics['dead']+=1;return False,tree
        if kind=='empty':found=state;solution=completed;return True,tree
        metrics[kind]+=1
        if kind=='branch' and active is None and library and mode!='base':
            before=time.perf_counter()
            if join is None:join=Join(model,library,enumerated=not indexed)
            items,work=join(model,state,g,point,library,proposal_limit)
            tree['proposal_pool']=items
            metrics['proposal_seconds']+=time.perf_counter()-before
            for k,v in work.items():metrics['proposal_'+k]+=v
            if mode=='policy':
                item,event=Attention.choose(items,support,state,g,weights,stochastic,rng)
                event.update(id=len(events),chosen=tuple(state.order),point=point,items=items)
                tree['policy_event']=len(events);events.append(event)
            else:item,_=C.choose(items,model,state,FIXED_WEIGHTS,False,rng)
            if item is not None:
                # Validate the original aggregate once. Missing members remain
                # absent from the state until the ordinary scheduler places them.
                if M.freeze(C.aggregate(model,item['members']))!=M.freeze({k:item[k] for k in ('occupancy','marks')}):raise ValueError('exact original aggregate')
                record=dict(id=len(hints),chosen=tuple(state.order),point=point,item=item)
                hints.append(record);metrics['hint_started']+=1;tree['hint_start']=record['id']
                active=dict(id=record['id'],item=item,waiting=False)
                active,start_review=review(model,state,g,active,kind,point,keys)
                if active is None or not start_review['eligible']:raise ValueError('new hint must fit the selected point')
                tree['start_review']=start_review;trace=start_review
        pending=trace.get('pending',()) if active else ()
        alternatives=keys if kind=='forced' else ordered(keys,pending)
        for key in alternatives:
            try:tick()
            except C.Budget:tree['cutoff']='before_placement';return None,tree
            role='member' if active and key in pending else 'unrelated' if active else 'base'
            metrics['role_'+role]+=1
            child,cg=state.copy(),g.copy();cg.update(model,child,child.place(model.placement(key)))
            okay,sub=visit(child,cg,active,completed);tree['children'].append(dict(key=key,role=role,tree=sub))
            if okay is not False:return okay,tree
            metrics['backtracks']+=1
        return False,tree
    okay,tree=visit(initial,graph,None,())
    selected=found or best;proof,end=M.decode(model,selected.order) if found else (None,None)
    index_record=join.finish() if join else None
    return dict(index=index_record,status='finite_exact_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_region',
        placements=selected.order,tile_generations=selected.tile_generations,proof=proof,endpoint=end,
        metrics=dict(metrics),graph_metrics=dict(model.metrics),seconds=time.perf_counter()-started,
        candidate_universe=model.cardinality(),hints=hints,solution_hints=solution,policy_events=events,
        weights=weights,fixed_weights=FIXED_WEIGHTS,stochastic=stochastic,seed=seed,mode=mode,search_tree=tree,
        attention_support=support.record() if support else None,attention_prep_seconds=prep_seconds,
        limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit))
