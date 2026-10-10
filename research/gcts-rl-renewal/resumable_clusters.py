"""Branch-local cluster ordering that survives unrelated scheduler decisions.

Every transition places exactly one original candidate. A suspended family is
only an ordering hint: its missing constituents add no occupancy or markings.
Complete base domains, propagation, generations and fallback are unchanged.
No unfinished family is entered as a checked lemma.
"""
import collections,math,random,time
import adaptive_receptor_clusters as C
import movable_proof_regions as M
import quantified_receptors as Q

FEATURES=C.FEATURES
FIXED_WEIGHTS=(1.,4.,0.,2.,-8.)

def review(model,state,graph,hint,kind,point,keys):
    if hint is None:return None,dict(phase='none',pending=())
    item=hint['item'];members=M.freeze(item['members']);filled={k[0]:k for k in state.order}
    pending=tuple(k for k in members if filled.get(k[0])!=k)
    if any(k[0] in filled and filled[k[0]]!=k for k in members):
        return None,dict(phase='dropped',reason='occupied_differently',pending=pending)
    if not pending:return None,dict(phase='completed',pending=())
    if any(k not in graph.domains.get(Q.cell(k[0]),()) for k in pending):
        return None,dict(phase='dropped',reason='member_no_longer_legal',pending=pending)
    if any(p in state.marks and state.marks[p]!=v for p,v in item['marks']):
        return None,dict(phase='dropped',reason='interface_disagreement',pending=pending)
    eligible=tuple(sorted(k for k in pending if k in keys)) if kind in ('forced','branch') else ()
    phase='resumed' if eligible and hint['waiting'] else 'continuing' if eligible else 'suspended'
    active=dict(hint,waiting=not bool(eligible))
    return active,dict(phase=phase,pending=pending,eligible=eligible)

def ordered(keys,pending):
    # Change preferences only; no original candidate is removed or duplicated.
    preferred=sorted(k for k in pending if k in keys)
    yield from preferred
    yield from (k for k in keys if k not in preferred)

def search(model,library=(),mode='base',weights=None,stochastic=False,seed=0,
           attempts=20000,seconds=10,proposal_limit=32):
    if mode not in ('base','fixed','policy'):raise ValueError('declared search lane')
    if mode=='policy' and (weights is None or len(weights)!=len(FEATURES)):raise ValueError('frozen policy dimension')
    started=time.perf_counter();initial=model.initial();graph=M.Graph(model,initial)
    metrics=collections.Counter();hints=[];events=[];rng=random.Random(seed);found=None;best=initial;solution=()
    def tick():
        if metrics['attempts']>=attempts or time.perf_counter()-started>seconds:raise C.Budget()
        metrics['attempts']+=1
    def visit(state,g,hint,completed):
        nonlocal found,best,solution
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
            before=time.perf_counter();items,work=C.proposals(model,state,g,point,library,proposal_limit)
            tree['proposal_pool']=items
            metrics['proposal_seconds']+=time.perf_counter()-before
            for k,v in work.items():metrics['proposal_'+k]+=v
            if mode=='policy':
                item,event=C.choose(items,model,state,weights,stochastic,rng)
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
    return dict(status='finite_exact_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_region',
        placements=selected.order,tile_generations=selected.tile_generations,proof=proof,endpoint=end,
        metrics=dict(metrics),graph_metrics=dict(model.metrics),seconds=time.perf_counter()-started,
        candidate_universe=model.cardinality(),hints=hints,solution_hints=solution,policy_events=events,
        weights=weights,fixed_weights=FIXED_WEIGHTS,stochastic=stochastic,seed=seed,mode=mode,search_tree=tree,
        limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit))

def promote(spec,catalog,result,library=(),maximum=7):
    learned=C.promote(spec,catalog,result,library,maximum)
    old={t['name']:t for t in library}
    for t in learned:
        window=M.freeze(t['source']['members']);inside={k[0]:i for i,k in enumerate(window)};children=[]
        for done in result.get('solution_hints',()):
            item=done['item'];members=M.freeze(item['members'])
            if item['template'] in old and set(members)<=set(window):
                children.append(dict(template=item['template'],offsets=[inside[k[0]] for k in members],
                    hint_id=done['id'],kind='completed_ordering_hint'))
        t['children']=children;t['level']=1+max((old[c['template']]['level'] for c in children),default=0)
    return learned

def update(weights,baseline,result,rate=.15):
    m=result['metrics'];cost=m.get('attempts',0)+.25*m.get('proposal_scanned',0)+.1*m.get('hint_reviews',0)
    reward=int(result['status']=='finite_exact_proof_region')-math.log1p(cost)/math.log1p(result['limits']['attempts'])
    gs=[e['gradient'] for e in result['policy_events']]
    gradient=[sum(g[j] for g in gs)/max(1,len(gs)) for j in range(len(FEATURES))]
    after=[max(-6,min(6,w+rate*(reward-baseline)*g)) for w,g in zip(weights,gradient)]
    return after,.9*baseline+.1*reward,dict(cost_units=cost,reward=reward,baseline_before=baseline,
        gradient=gradient,rate=rate,weights_after=after,
        scope='Deterministic work proxy: attempts plus one quarter of proposal scans and one tenth of hint reviews; not a wall-time reward.')
