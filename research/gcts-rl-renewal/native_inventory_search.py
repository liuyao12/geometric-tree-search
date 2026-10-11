"""Branch-local inventory guidance over the unchanged complete point graph."""
import collections,random,time
from native_receptor_points import fingerprint
from turtle import Graph
from native_inference_inventory import Join,aggregate
from native_inventory_policy import vector,choose,FEATURES,FIXED
def search(model,library,mode='base',weights=None,stochastic=False,seed=0,attempts=2000,seconds=30,proposal_limit=24,proposal_checks=2048):
    if mode not in ('base','zero','fixed','learned','no-family'):raise ValueError('ordering control')
    if mode in ('learned','no-family') and (weights is None or len(weights)!=len(FEATURES)):raise ValueError('frozen policy dimension')
    scoring=[0.]*len(FEATURES) if mode=='zero' else list(FIXED) if mode=='fixed' else list(weights) if weights is not None else None
    began=time.perf_counter();initial=model.initial();g=Graph(model,initial);root_state=fingerprint(initial);root_graph=g.fingerprint();metrics=collections.Counter();events=[];hints=[];found=None;rng=random.Random(seed);join=None
    def review(state,graph,hint,point):
        if hint is None:return None,dict(phase='absent',pending=[],eligible=[])
        members=hint['item']['members'];pending=[k for k in members if k not in state.selected]
        if not pending:return None,dict(phase='completed',pending=[],eligible=[])
        illegal=[k for k in pending if not state.legal(model.placement(k))]
        if illegal:return None,dict(phase='invalid',pending=pending,illegal=illegal,eligible=[])
        eligible=[k for k in pending if k in graph.domains.get(point,set())]
        return hint,dict(phase='eligible' if eligible else 'waiting',pending=pending,eligible=eligible)
    def visit(state,graph,hint):
        nonlocal found,join
        kind,p,keys=graph.decision(state);metrics['nodes']+=1
        active,trace=review(state,graph,hint,p);tree=dict(kind=kind,point=p,census=[dict(point=q,generation=state.generations[q],keys=sorted(cs)) for q,cs in sorted(graph.domains.items())],state_sha256=fingerprint(state),hint_in=hint['id'] if hint else None,review=trace,children=[])
        if hint:metrics['hint_'+trace['phase']]+=1
        if kind=='dead':metrics['dead']+=1;return False,tree
        if kind=='empty':found=state;return True,tree
        metrics[kind]+=1
        if kind=='branch' and active is None and mode!='base':
            stage=time.perf_counter()
            if join is None:join=Join(model,() if mode=='no-family' else library)
            items,work=join(state,graph,p,proposal_limit,proposal_checks)
            for k,v in work.items():metrics[k]+=v
            features=[vector(item,model,state,graph) for item in items];item,event=choose(items,features,scoring,rng,stochastic)
            event.update(id=len(events),point=p,chosen=list(state.order),items=items,weights=scoring);tree['policy_event']=event['id'];events.append(event);metrics['proposal_seconds']+=time.perf_counter()-stage
            if item is not None:
                if aggregate(model,item['members'],state)!= {k:item[k] for k in ('members','pending','aggregate_sha256','new_occupancy','new_marks')}:raise ValueError('validated original aggregate')
                active=dict(id=len(hints),item=item);hints.append(dict(id=active['id'],chosen=list(state.order),point=p,item=item));tree['hint_start']=active['id'];metrics['hints_started']+=1
                active,start=review(state,graph,active,p);tree['start_review']=start
                if active is None or not start['eligible']:raise ValueError('new cluster must reach selected point')
                trace=start
        preferred=set(trace['eligible']) if active else set();alternatives=keys if kind=='forced' else [k for k in keys if k in preferred]+[k for k in keys if k not in preferred];tree['alternatives']=alternatives
        for key in alternatives:
            if metrics['attempts']>=attempts or time.perf_counter()-began>=seconds:tree['cutoff']='before_placement';return None,tree
            metrics['attempts']+=1;child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(key)));okay,sub=visit(child,cg,active);tree['children'].append(dict(key=key,role='member' if key in preferred else 'base',tree=sub))
            if okay is not False:return okay,tree
            metrics['backtracks']+=1
        return False,tree
    okay,tree=visit(initial,g,None);proof=[model.metadata[k]['command'] for k in sorted(found.order) if k[1]==0] if found else None;restored=fingerprint(initial)==root_state and g.fingerprint()==root_graph
    if not restored:raise ValueError('root and graph rollback')
    return dict(status='finite_marked_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_marked_region',proof=proof,placements=found.order if found else [],tile_generations=found.tile_generations if found else [],tree=tree,metrics=dict(metrics),graph_metrics=dict(model.metrics),events=events,hints=hints,seconds=time.perf_counter()-began,mode=mode,weights=scoring,stochastic=stochastic,seed=seed,root_state_sha256=root_state,root_restored=restored,limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit,proposal_checks=proposal_checks),scope='Reference point scheduler with validated branch-local clusters, complete original fallback and unchanged problem-defining logical markings. Compact positional proof model; not primitive-square GCTS or learned pruning.')
