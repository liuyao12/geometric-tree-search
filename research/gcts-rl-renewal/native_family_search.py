"""Native families order original choices; every member obeys the scheduler."""
import random,time
from collections import Counter
from native_wang_search import Graph
from native_family_catalog import Matcher
from native_family_policy import FEATURES,FIXED,choose

def review(g,hint,kind,point):
    if hint is None:return None,dict(phase='none',pending=[],eligible=[])
    pending=[];item=hint['item']
    for p,key in item['members']:
        p,key=tuple(p),tuple(key)
        if p in g.selected:
            if g.selected[p]!=key:return None,dict(phase='dropped',reason='occupied_differently',pending=[],eligible=[])
        elif p not in g.domains or not g.domains[p].contains(key):return None,dict(phase='dropped',reason='member_no_longer_legal',pending=[],eligible=[])
        else:pending.append([list(p),list(key)])
    for p,v in item['marks']:
        p=tuple(p);v=tuple(v) if isinstance(v,list) else v
        if p in g.marks and g.marks[p]!=v:return None,dict(phase='dropped',reason='interface_disagreement',pending=pending,eligible=[])
    if not pending:return None,dict(phase='completed',pending=[],eligible=[])
    eligible=[key for p,key in pending if tuple(p)==point] if kind in ('branch','forced') else []
    return dict(hint,waiting=not bool(eligible)),dict(phase=('resumed' if hint['waiting'] else 'continuing') if eligible else 'suspended',pending=pending,eligible=eligible)
def ordered(domain,preferred):
    preferred=sorted(set(tuple(k) for k in preferred));yield from preferred
    yield from (k for k in domain.options() if k not in preferred)
def search(universe,pattern,height,boundary,library=(),mode='base',weights=None,stochastic=False,seed=0,attempts=350,seconds=60,proposal_limit=8,trace_limit=30000):
    if mode not in ('base','fixed','policy'):raise ValueError('native family lane')
    if mode=='policy' and (weights is None or len(weights)!=len(FEATURES)):raise ValueError('policy weights')
    started=time.perf_counter();g=Graph(universe,pattern,height,boundary,projected=True);initial=g.fingerprint();matcher=Matcher(library,g) if library and mode!='base' else None;events=[];hints=[];policy=[];frames=[];rng=random.Random(seed);agenda=();completed=();steps=forced=branches=backtracks=0;metrics=Counter();status='unknown_search_budget'
    def place(p,key,kind):
        nonlocal steps,forced,branches
        g.place(p,key);steps+=1;forced+=kind=='forced';branches+=kind=='branch'
    def alternative():
        nonlocal agenda,completed,backtracks
        while frames:
            token,p,options,parent_agenda,parent_completed,preferred_id=frames[-1];g.rollback(token);agenda=parent_agenda;completed=parent_completed;active=next((h for h in agenda if h['id']==preferred_id),None)
            try:key=next(options)
            except StopIteration:frames.pop();backtracks+=1;continue
            role='member' if active and any(tuple(q)==p and tuple(v)==key for q,v in active['item']['members']) else 'unrelated' if active else 'base';events.append(dict(kind='alternative',point=list(p),key=list(key),depth=len(g.order),hint=active['id'] if active else None,role=role));metrics['role_'+role]+=1;place(p,key,'alternative');backtracks+=1;return True
        return False
    while steps<attempts and time.perf_counter()-started<seconds:
        if len(events)>=trace_limit:raise ValueError('native family trace budget')
        kind,p,d=g.decision();incoming=agenda;kept=[];reviews=[];active=None;r=dict(phase='none',pending=[],eligible=[])
        for hint in incoming:
            current,trace=review(g,hint,kind,p);reviews.append(dict(id=hint['id'],**trace));metrics['hint_reviews']+=1;metrics['hint_'+trace['phase']]+=1
            if trace['phase']=='completed':completed+=(hint['id'],)
            if current is not None:
                kept.append(current)
                if active is None and trace['eligible']:active=current;r=trace
        agenda=tuple(kept)
        e=dict(kind=kind,point=None if p is None else list(p),count=None if d is None else d.count,census=g.census(),depth=len(g.order),agenda_in=[h['id'] for h in incoming],reviews=reviews);events.append(e)
        if kind=='empty':status='finite_exact_native_rectangle';break
        if kind=='dead':
            if not alternative():status='exhausted_finite_native_rectangle';break
            continue
        if kind=='branch' and active is None and matcher:
            before=time.perf_counter();items,work=matcher.proposals(p,proposal_limit);metrics['proposal_seconds']+=time.perf_counter()-before
            for k,v in work.items():metrics['proposal_'+k]+=v
            e['proposal_pool']=items
            item,decision=choose(items,g,FIXED if mode=='fixed' else weights,stochastic if mode=='policy' else False,rng)
            decision.update(id=len(policy),depth=len(g.order),point=list(p),items=items);e['policy_event']=len(policy);policy.append(decision)
            if item is not None:
                h=dict(id=len(hints),chosen=[[list(q),list(g.selected[q])] for q in g.order],point=list(p),item=item);hints.append(h);active=dict(id=h['id'],item=item,waiting=False);e['hint_start']=h['id'];active,r=review(g,active,kind,p);e['start_review']=r
                if active is None or not r['eligible']:raise ValueError('family must contain the scheduled point')
                agenda=agenda+(active,);metrics['hint_started']+=1
        preferred=r.get('eligible',()) if active else ();options=iter(d.options()) if kind=='forced' else iter(ordered(d,preferred));key=next(options);e['key']=list(key);role='member' if active and list(key) in preferred else 'unrelated' if active else 'base';e['role']=role;e['hint_used']=active['id'] if active else None;metrics['role_'+role]+=1
        if kind=='branch':frames.append((len(g.trail),p,options,agenda,completed,active['id'] if active else None))
        place(p,key,kind)
    tiles=[dict(x=x,y=y,**universe.tile(g.selected[x,y])) for x,y in g.order]
    result=dict(status=status,attempts=steps,forced=forced,branches=branches,backtracks=backtracks,seconds=time.perf_counter()-started,width=g.width,height=height,extended=False,projected=True,pattern=pattern,boundary=boundary,events=events,tiles=tiles,tile_generations=g.tile_generations.copy(),initial_census=g.initial,initial_candidate_nodes=g.initial_candidate_count,metrics=dict(metrics),graph_metrics=dict(g.metrics),limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit),mode=mode,weights=weights,stochastic=stochastic,seed=seed,hints=hints,policy_events=policy,solution_hints=list(completed))
    g.rollback(0)
    if g.fingerprint()!=initial:raise ValueError('complete native family rollback')
    result['root_rollback_verified']=True;return result
