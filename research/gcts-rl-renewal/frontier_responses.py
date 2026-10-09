"""Current-frontier response resolution with one DFS child per base key.

Responses only order complete base domains. Their suffixes are interrupted by
the real global scheduler. This reformulates the earlier duplicate-action
traversal; it is not a same-path representation optimization or a pruning rule.
"""
import random,time
from collections import Counter
from dataclasses import dataclass
from turtle import Graph,Policy
from boundary_responses import Action,features as action_features,digest
from region_tiles import packed_state,verify_region

MODES=('base','small','hierarchy')

def mode_features(state,graph,keys,mode,feedback):
    """Actual mutable frontier, not only the original requested region."""
    n=len(state.required);filled=sum(state.totals.get(p,0)==12 for p in state.required)
    degrees=[len(v) for v in graph.domains.values()]
    values={'bias':1.,'remaining':1-filled/n,'domain':len(keys)/50,
            'mean_degree':sum(degrees)/max(1,len(degrees))/50,
            'low_degree':sum(d<=2 for d in degrees)/max(1,len(degrees)),
            'frontier':len(degrees)/300,'accepted':len(state.order)/100,
            'contact':sum(state.totals.get(p,0)>0 for p in graph.domains)/max(1,len(degrees)),
            'interruption':feedback[mode,'interrupted']/max(1,feedback[mode,'closed'])}
    return {'mode:'+mode+':'+k:v for k,v in values.items()}

def rank_unique(keys,actions,priority=None):
    """First action for a key wins its hint; all base keys survive exactly once."""
    chosen={}
    for a in actions:
        if a.sequence[0] not in keys:raise ValueError('proposal outside selected base domain')
        chosen.setdefault(a.sequence[0],a)
    if set(chosen)!=set(keys):raise ValueError('missing singleton fallback')
    order=list(chosen)
    if priority in chosen:order.remove(priority);order.insert(0,priority)
    return order,chosen,len(actions)-len(order)

@dataclass(frozen=True)
class Pending:
    action:Action
    offset:int
    mode:str
    context:str

def search(boundary,universe,atlases,seed=0,attempt_limit=4000,seconds=6,
           fixed_mode=None,policy=None,learn=False,rollout=False,observer=None):
    if fixed_mode not in (*MODES,None):raise ValueError('unknown resolution')
    if learn and policy is None:raise ValueError('learning requires policy')
    start=time.monotonic();model=universe.bind(boundary);state=boundary.initial();graph=Graph(model,state)
    rng=random.Random(seed);stats=Counter();feedback=Counter();traces=[];choices=[];events=[];samples=[]
    best=state.copy();best_log=[];found=None;execution=[];boundary_sha=digest(boundary.packed())
    peak_points=len(graph.domains);peak_candidates=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    class Budget(Exception):pass
    def check(move=False):
        if (move and stats['attempts']>=attempt_limit) or (seconds is not None and time.monotonic()-start>=seconds):raise Budget()
    def record(s,log):
        nonlocal best,best_log
        if sum(s.totals.get(p,0)==12 for p in s.required)>sum(best.totals.get(p,0)==12 for p in best.required):best=s.copy();best_log=list(log)
    def close(pending,stop):
        if pending is None:return
        n=len(pending.action.sequence);used=pending.offset
        feedback[pending.mode,'closed']+=1;feedback[pending.mode,'interrupted']+=used<n
        stats['response_interruptions']+=used<n
        events.append({'response':pending.action.response,'proposed':n,'used':used,'stop':stop,
                       'mode':pending.mode,'context':pending.context})
    def pick(fs,kind):
        if learn:
            i,gradient=policy.select(rng,fs);traces.append(gradient)
            choices.append({'kind':kind,'features':fs,'selected':i});return i
        if policy:
            scores=[sum(policy.weights[f]*v for f,v in x.items()) for x in fs]
            top=max(scores);return rng.choice([i for i,v in enumerate(scores) if v==top])
        return rng.randrange(len(fs))
    def visit(s,g,log,pending=None):
        nonlocal found,execution,peak_points,peak_candidates,peak_incidences
        check();stats['nodes']+=1;record(s,log)
        peak_points=max(peak_points,len(g.domains));peak_candidates=max(peak_candidates,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        kind,p,keys=g.decision(s)
        if kind in ('dead','empty'):
            close(pending,kind)
            if kind=='empty':found=s.copy();execution=list(log)
            return
        if pending and pending.action.sequence[pending.offset] not in keys:
            close(pending,'scheduler-'+kind);pending=None
        chosen={};mode='base'
        if kind=='forced':order=keys
        elif pending:
            order=list(keys);rng.shuffle(order);planned=pending.action.sequence[pending.offset]
            order.remove(planned);order.insert(0,planned)
        else:
            stats['resolution_decisions']+=1
            mode=fixed_mode or MODES[pick([mode_features(s,g,keys,m,feedback) for m in MODES],'mode')]
            stats['mode:'+mode]+=1
            actions=[Action((key,)) for key in keys] if mode=='base' else atlases[mode].actions(model,s,g,keys,check)
            rng.shuffle(actions)
            if policy:
                fs=[{'move:'+f:v for f,v in action_features(model,s,g,a).items()} for a in actions]
                if learn:
                    i=pick(fs,'move');actions=[actions[i]]+actions[:i]+actions[i+1:]
                else:actions=[a for a,f in sorted(zip(actions,fs),key=lambda af:sum(policy.weights[k]*v for k,v in af[1].items()),reverse=True)]
            order,chosen,duplicates=rank_unique(keys,actions)
            stats['duplicate_action_children_avoided']+=duplicates
            if len(samples)<8:
                samples.append({'placements':list(s.order),'point':p,'kind':kind,'mode':mode,
                                'domain':keys,'ordered':order,'offered_actions':len(actions),'duplicates':duplicates,
                                'feedback':[(m,k,v) for (m,k),v in sorted(feedback.items())],
                                'mode_features':[mode_features(s,g,keys,m,feedback) for m in MODES]})
        assert len(order)==len(set(order)) and set(order)==set(keys)
        if observer:observer(s,g,kind,p,tuple(keys),tuple(order))
        if rollout:order=order[:1]
        for key in order:
            check(True);child=s.copy();cg=g.copy();stats['attempts']+=1;stats[kind]+=1
            plan=pending if pending and key==pending.action.sequence[pending.offset] else None
            if plan is None and key in chosen and len(chosen[key].sequence)>1:
                plan=Pending(chosen[key],0,mode,digest((boundary_sha,s.order)))
                stats['response_starts']+=1
            a=plan.action if plan else Action((key,));offset=plan.offset if plan else 0
            step={'kind':kind,'point':p,'placement':key,'response':a.response,
                  'proposal_size':len(a.sequence),'proposal_offset':offset}
            cg.update(model,child,child.place(model.placement(key)));child_log=log+[step]
            if plan:
                stats['explored_response_constituents']+=1
                plan=Pending(a,offset+1,plan.mode,plan.context)
                if plan.offset==len(a.sequence):close(plan,'complete');plan=None
            record(child,child_log);visit(child,cg,child_log,plan)
            if found is not None:return
            stats['backtracks']+=1
    try:
        visit(state,graph,[]);status='finite_exact_region' if found is not None else 'dead_rollout' if rollout else 'exhausted_finite_region_uncertified'
    except (Budget,RecursionError):status='unknown_budget'
    result=found if found is not None else best;log=execution if found is not None else best_log
    if not verify_region(model,boundary,result,found is not None):raise AssertionError('invalid frontier result')
    coverage=sum(result.totals.get(p,0)==12 for p in result.required)/len(result.required)
    elapsed=time.monotonic()-start;reward=coverage+(1 if found is not None else -1)-.001*stats['attempts']-.01*elapsed
    if learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,
            'nodes':stats['nodes'],'branches':stats['branch'],'forced':stats['forced'],'backtracks':stats['backtracks'],
            'attempted_base_placements':stats['attempts'],'coverage_fraction':coverage,'accepted_base_tiles':len(result.order),
            'state':packed_state(result),'execution':log,'metrics':dict(model.metrics),'reward':reward,'certificate':None,'verified':True,
            'stats':dict(stats),'response_events':events,'decision_samples':samples,'learning_choices':choices,
            'peak_frontier_points':peak_points,'peak_candidate_nodes':peak_candidates,'peak_incidences':peak_incidences,
            'admissible_placements':model.admissible_placements,'budget':{'base_attempts':attempt_limit,'seconds':seconds},
            'scope':'unique base-key DFS; responses order suffixes; no learned pruning or proof of a negative boundary'}
