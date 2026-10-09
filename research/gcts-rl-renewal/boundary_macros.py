"""Local solution proposals in an unchanged, complete singleton point graph.

Clusters are heuristics, not candidates for degree/forcing calculations. Each
constituent must obey the base scheduler; every singleton alternative survives.
No inherited failure marking, completion witness or policy is imported.
"""
import random,time
from collections import Counter,defaultdict
from turtle import Model,Graph,CAPACITY,SYMMETRIES,Policy,add,sub
from cluster_tiles import make_type
from spatial import canonical,moved,adjacency,interface,keys_tuple
from region_tiles import Boundary,RegionModel,verify_region,packed_state
from coverage import hexagon

def singleton():return make_type(Model(),'base',0,((0,(0,0,0)),))

def problems(training=False):
    allowed=frozenset(hexagon(14));out=[]
    if training:
        for i,center in enumerate(((0,0,0),(2,-2,0),(-2,2,0),(0,2,-2))):
            required=frozenset(add(p,center) for p in hexagon(2+i%2))
            out.append(Boundary('local-'+str(i),required,allowed))
    else:
        for r in (4,6,8):out.append(Boundary('core-'+str(r),frozenset(hexagon(r)),allowed))
        notch={p for p in hexagon(6) if not(p[0]>2 and p[1]>0)}|{(10,-5,-5),(11,-5,-6)}
        out.append(Boundary('notch-and-pocket',frozenset(notch),allowed))
    return tuple(out)

def mine(donors,model,limit=24):
    """Connected temporal windows of fresh successful local completions."""
    start=time.monotonic();counts=Counter();seeds=defaultdict(set);windows=0
    for donor in donors:
        if donor['status']!='finite_exact_region':continue
        keys=tuple(model.placement((n,o,tuple(tr))).expansion[0] for n,o,tr in donor['state']['placements'])
        for size in range(2,7):
            for i in range(len(keys)-size+1):
                patch=keys[i:i+size];adj=adjacency(model.base,patch);seen={0};pending=[0]
                while pending:
                    for j in adj[pending.pop()]-seen:seen.add(j);pending.append(j)
                if len(seen)!=size:continue
                sig=canonical(patch);counts[sig]+=1;seeds[sig].add(donor['seed']);windows+=1
    # Reserve capacity at each size rather than letting one size dominate.
    selected=[]
    for size in range(2,7):
        candidates=sorted((s for s in counts if len(s)==size),key=lambda s:(-len(seeds[s]),-counts[s],s))
        selected.extend(candidates[:limit//5])
    library=[{'id':i,'expansion':s,'count':counts[s],'donor_seeds':sorted(seeds[s]),
              'interface':interface(model.base,s)} for i,s in enumerate(selected)]
    return library,{'seconds':time.monotonic()-start,'connected_windows':windows,'distinct_shapes':len(counts),
                    'selected':len(library),'sizes':dict(Counter(len(m['expansion']) for m in library)),
                    'selection':'up to four highest-recurrence connected windows at each size two through six'}

class Proposer:
    def __init__(self,library,limit=8):
        start=time.monotonic();self.library=library;self.limit=limit;self.aligned=defaultdict(set)
        for motif in library:
            for g in SYMMETRIES:
                patch=moved(keys_tuple(motif['expansion']),g)
                for o,tr in patch:
                    self.aligned[o].add(tuple(sorted((q,sub(p,tr)) for q,p in patch)))
        self.seconds=time.monotonic()-start

    def actions(self,model,state,graph,keys,check=lambda:None):
        start=time.monotonic();actions={(k,) for k in keys};raw={};by_base={}
        for key in keys:by_base[model.placement(key).expansion[0]]=key
        for base_key,key in by_base.items():
            for relative in sorted(self.aligned[base_key[0]]):
                check();patch=tuple((o,add(tr,base_key[1])) for o,tr in relative)
                pending=tuple(k for k in patch if k not in state.owned_base)
                if len(pending)<2:continue
                wrapped=tuple(('base',o,tr) for o,tr in pending)
                # Singleton authoring uses the identity prototype; verify mapping.
                if any(model.placement(k).expansion!=(b,) for k,b in zip(wrapped,pending)):
                    raise AssertionError('base wrapper action changed')
                if any(not state.legal(model.placement(k)) for k in wrapped):continue
                gain=sum(v for k in wrapped for p,v in model.placement(k).occupancy if p in state.required)
                raw[(key,wrapped)]=(gain,len(wrapped))
        # This bounded proposal pool never supplies graph degrees or exclusions.
        chosen=sorted(raw,key=lambda x:(-raw[x][0]/len(x[1]),-raw[x][1],x))[:self.limit]
        model.metrics['macro_raw_proposals']+=len(raw)
        for first,pending in chosen:
            check();model.metrics['macro_validations']+=1
            trial=state.copy()
            try:
                for key in pending:trial.place(model.placement(key))
            except ValueError:continue
            child=state.copy();cg=graph.copy();remaining=set(pending);seq=[]
            while remaining:
                check();kind,_,domain=cg.decision(child)
                if kind in ('dead','empty'):break
                available=remaining.intersection(domain)
                key=first if not seq else min(available) if available else None
                if key not in available:break
                cg.update(model,child,child.place(model.placement(key)));remaining.remove(key);seq.append(key)
                model.metrics['macro_validation_moves']+=1
            if len(seq)>1:actions.add(tuple(seq))
        model.metrics['proposal_seconds']+=time.monotonic()-start
        model.metrics['macro_offered']+=sum(len(a)>1 for a in actions)
        return sorted(actions)

def features(model,state,graph,action):
    occ=Counter()
    for k in action:occ.update(dict(model.placement(k).occupancy))
    required=state.required;gain=sum(v for p,v in occ.items() if p in required)
    fill=sum(state.totals.get(p,0)+v==CAPACITY for p,v in occ.items() if p in required)
    out={'bias':1.,'size':len(action)/6,'fill':fill/28,'required_gain':gain/240,
         'optional_gain':sum(v for p,v in occ.items() if p not in required)/240,
         'frontier':len(graph.domains)/100,'first_orientation:'+str(action[0][1]):1.}
    for deficit in range(1,13):
        out['trace:'+str(deficit)]=sum(p in required and CAPACITY-state.totals.get(p,0)==deficit for p in occ)/28
    return out

def search(boundary,universe,seed=0,attempt_limit=8000,seconds=6,policy=None,proposer=None,learn=False,rollout=False):
    """Identical base inventory/scheduler/budget accounting in every lane.

    Budget counts real explored base placements, including macro constituents.
    Cooperative wall checks include proposal construction and validation. The
    returned best state is independently flattened. This heuristic DFS does not
    export a negative certificate (macro duplicates are not proof premises).
    """
    start=time.monotonic();model=universe.bind(boundary);state=boundary.initial();graph=Graph(model,state)
    rng=random.Random(seed);attempts=nodes=branches=forced=backtracks=macro_moves=0
    found=None;best=state.copy();traces=[];best_log=[];execution=[]
    class Budget(Exception):pass
    def check():
        if attempts>=attempt_limit or (seconds is not None and time.monotonic()-start>=seconds):raise Budget()
    def record(s,log):
        nonlocal best,best_log
        if sum(s.totals.get(p,0)==12 for p in s.required)>sum(best.totals.get(p,0)==12 for p in best.required):
            best=s.copy();best_log=list(log)
    def visit(s,g,log):
        nonlocal attempts,nodes,branches,forced,backtracks,found,macro_moves,execution
        check();nodes+=1;record(s,log);kind,p,keys=g.decision(s)
        if kind=='dead':return
        if kind=='empty':found=s.copy();execution=list(log);return
        if kind=='forced':forced+=1;actions=[(keys[0],)]
        else:
            branches+=1;actions=proposer.actions(model,s,g,keys,check) if proposer else [(k,) for k in keys]
            rng.shuffle(actions)
            if policy:
                fs=[features(model,s,g,a) for a in actions]
                if learn:
                    i,gradient=policy.select(rng,fs);traces.append(gradient);actions=[actions[i]]+actions[:i]+actions[i+1:]
                else:actions=sorted(zip(actions,fs),key=lambda af:sum(policy.weights[k]*v for k,v in af[1].items()),reverse=True);actions=[a for a,f in actions]
            if rollout:actions=actions[:1]
        for action in actions:
            child=s.copy();cg=g.copy();child_log=list(log);used=[]
            for key in action:
                check();knd,pt,domain=cg.decision(child)
                if knd in ('dead','empty') or key not in domain:raise AssertionError('unscheduled macro constituent')
                attempts+=1;cg.update(model,child,child.place(model.placement(key)));used.append(key)
                child_log.append({'kind':knd,'point':pt,'placement':key,'macro_length':len(action),'macro_offset':len(used)-1})
                record(child,child_log)
            if len(action)>1:macro_moves+=len(action)
            visit(child,cg,child_log)
            if found:return
            backtracks+=1
    try:
        visit(state,graph,[]);status='finite_exact_region' if found else 'dead_rollout' if rollout else 'exhausted_finite_region_uncertified'
    except (Budget,RecursionError):status='unknown_budget'
    result=found or best;log=execution if found else best_log
    if not verify_region(model,boundary,result,bool(found)):raise AssertionError('invalid local solution')
    coverage=sum(result.totals.get(p,0)==12 for p in result.required)/len(result.required)
    reward=coverage+(1 if found else -1)-.001*attempts-.01*(time.monotonic()-start)
    if policy and learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,
            'nodes':nodes,'branches':branches,'forced':forced,'backtracks':backtracks,'attempted_base_placements':attempts,
            'explored_macro_constituents':macro_moves,'coverage_fraction':coverage,'accepted_base_tiles':len(result.order),
            'state':packed_state(result),'execution':log,'metrics':dict(model.metrics),'reward':reward,'certificate':None,
            'admissible_placements':model.admissible_placements,'budget':{'base_attempts':attempt_limit,'seconds':seconds},
            'verified':True}
