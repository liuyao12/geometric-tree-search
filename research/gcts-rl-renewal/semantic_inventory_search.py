"""Same complete reference scheduler, with branch-local exact cluster ordering."""
import collections,random,time
from native_receptor_points import fingerprint
from native_inventory_policy import choose
from native_inference_inventory import aggregate
from semantic_inventory_guidance import Join,vector,FEATURES,FIXED
from turtle import Graph

def search(model,mode='base',weights=None,stochastic=False,seed=0,attempts=20000,seconds=60,proposal_limit=24,proposal_checks=2048):
    if mode not in ('base','zero','fixed','learned','no-family'):raise ValueError('ordering lane')
    if mode in ('learned','no-family') and (weights is None or len(weights)!=len(FEATURES)):raise ValueError('policy dimension')
    scoring=[0.]*len(FEATURES) if mode=='zero' else list(FIXED) if mode=='fixed' else list(weights) if weights is not None else None
    began=time.perf_counter();initial=model.initial();graph=Graph(model,initial);root_state=fingerprint(initial);root_graph=graph.fingerprint();metrics=collections.Counter();events=[];hints=[];found=None;rng=random.Random(seed);join=Join(model,mode!='no-family')
    def review(state,g,hint,p):
        if hint is None:return None,dict(phase='absent',pending=[],eligible=[])
        pending=[k for k in hint['item']['members'] if k not in state.selected]
        if not pending:return None,dict(phase='completed',pending=[],eligible=[])
        illegal=[k for k in pending if not state.legal(model.placement(k))]
        if illegal:return None,dict(phase='invalid',pending=pending,illegal=illegal,eligible=[])
        eligible=[k for k in pending if k in g.domains.get(p,set())]
        return hint,dict(phase='eligible' if eligible else 'waiting',pending=pending,eligible=eligible)
    def visit(state,g,hint):
        nonlocal found
        kind,p,keys=g.decision(state);metrics['nodes']+=1
        active,trace=review(state,g,hint,p);tree=dict(kind=kind,point=p,census=[dict(point=q,generation=state.generations[q],keys=sorted(cs)) for q,cs in sorted(g.domains.items())],state_sha256=fingerprint(state),hint_in=hint['id'] if hint else None,review=trace,children=[])
        if hint:metrics['hint_'+trace['phase']]+=1
        if kind=='dead':metrics['dead']+=1;return False,tree
        if kind=='empty':found=state;return True,tree
        metrics[kind]+=1
        if kind=='branch' and active is None and mode!='base':
            stage=time.perf_counter();items,work=join(state,g,p,proposal_limit,proposal_checks)
            for k,v in work.items():metrics[k]+=v
            features=[vector(item,model,state,g) for item in items];item,event=choose(items,features,scoring,rng,stochastic)
            event.update(id=len(events),point=p,chosen=list(state.order),items=items,weights=scoring);tree['policy_event']=event['id'];events.append(event);metrics['proposal_seconds']+=time.perf_counter()-stage
            if item is not None:
                if aggregate(model,item['members'],state)!={k:item[k] for k in ('members','pending','aggregate_sha256','new_occupancy','new_marks')}:raise ValueError('invalid row aggregate')
                active=dict(id=len(hints),item=item);hints.append(dict(id=active['id'],chosen=list(state.order),point=p,item=item));tree['hint_start']=active['id'];metrics['hints_started']+=1
                active,start=review(state,g,active,p);tree['start_review']=start
                if active is None or not start['eligible']:raise ValueError('cluster does not reach selected point')
                trace=start
        preferred=set(trace['eligible']) if active else set();alternatives=keys if kind=='forced' else [k for k in keys if k in preferred]+[k for k in keys if k not in preferred];tree['alternatives']=alternatives
        for k in alternatives:
            if metrics['attempts']>=attempts or time.perf_counter()-began>=seconds:tree['cutoff']='before_placement';return None,tree
            metrics['attempts']+=1;child=state.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(k)));ok,sub=visit(child,cg,active);tree['children'].append(dict(key=k,role='member' if k in preferred else 'base',tree=sub))
            if ok is not False:return ok,tree
            metrics['backtracks']+=1
        return False,tree
    ok,tree=visit(initial,graph,None);restored=fingerprint(initial)==root_state and graph.fingerprint()==root_graph
    if not restored:raise ValueError('state/graph rollback')
    return dict(status='finite_marked_proof_region' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_marked_region',
                proof=model.decode(found.order) if found else None,placements=found.order if found else [],tile_generations=found.tile_generations if found else [],
                tree=tree,metrics=dict(metrics),graph_metrics=dict(model.metrics),events=events,hints=hints,mode=mode,weights=scoring,
                stochastic=stochastic,seed=seed,seconds=time.perf_counter()-began,root_state_sha256=root_state,root_restored=restored,
                limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit,proposal_checks=proposal_checks),
                scope='Reference global dead/forced/earliest-generation point search. Semantic row and open arbitrary cluster hints only reorder original alternatives. No learned candidate pruning or primitive-square GCTS.')
