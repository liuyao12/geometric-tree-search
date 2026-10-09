"""Composable exact local point responses, used only as continuation proposals.

A response records occupancy on its entire positive support, including zeros,
and an ordered distinct base expansion. It is an affine local operation on a
finite trace, not a single-valued solution operator for all boundary conditions.
Its children are checked by interface composition. The search never uses this
sampled atlas for candidate degrees, pruning, or forcing. Global scheduling can
interrupt any response; all singleton alternatives survive.
"""
import hashlib,json,random,time
from collections import Counter,defaultdict
from dataclasses import dataclass
from turtle import CAPACITY,SYMMETRIES,Graph,Policy,add,sub,transform,compose
from spatial import moved,adjacency
from boundary_macros import singleton
from coverage import hexagon
from region_tiles import Boundary,packed_state,verify_region

def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def declarations(training=False):
    """Externally fixed targets; the atlas cannot choose its evaluation problem."""
    allowed=frozenset(hexagon(18));out=[]
    if training:
        for i,(r,c) in enumerate(((2,(0,0,0)),(3,(2,-2,0)),(4,(-2,2,0)),(5,(0,2,-2)))):
            out.append(Boundary('response-train-'+str(i),frozenset(add(p,c) for p in hexagon(r)),allowed))
    else:
        for r in (4,6,8,10):out.append(Boundary('response-core-'+str(r),frozenset(hexagon(r)),allowed))
        notch={p for p in hexagon(8) if not(p[0]>2 and p[1]>0)}|{(13,-6,-7),(14,-6,-8)}
        out.append(Boundary('response-notch-and-pocket',frozenset(notch),allowed))
        # An explicit fixed exterior, authored from the base tile alone. No
        # previously searched patch or learned marking is supplied.
        from turtle import Model
        fixed=Model().placement((3,(-6,3,3)))
        out.append(Boundary('response-fixed-exterior',frozenset(hexagon(7)),allowed,
                            fixed.occupancy,(),((3,(-6,3,3)),)))
    return tuple(out)

@dataclass(frozen=True)
class Response:
    identity:str
    sequence:tuple
    incoming:tuple
    delta:tuple
    outgoing:tuple
    level:int=0
    children:tuple=()
    pose:tuple=(0,(0,0,0))

    def packed(self):return self.__dict__.copy()

def operation(base,sequence,totals,children=(),level=0):
    """Translate to the first pose's origin; preserve the execution order."""
    if base.marking:raise ValueError('this response implementation declares unmarked base tiles')
    if not sequence or len(set(sequence))!=len(sequence):raise ValueError('distinct nonempty expansion required')
    if any(type(o) is not int or not 0<=o<12 or len(tr)!=3 or any(type(v) is not int for v in tr) or sum(tr) for o,tr in sequence):
        raise ValueError('exact base poses required')
    origin=sequence[0][1];seq=tuple((o,sub(tr,origin)) for o,tr in sequence);delta=Counter()
    for key in sequence:delta.update(dict(base.placement(key).occupancy))
    incoming=tuple(sorted((sub(p,origin),totals.get(p,0)) for p in delta))
    dv=tuple(sorted((sub(p,origin),v) for p,v in delta.items()))
    if any(type(v) is not int or not 0<=v<=12 for p,v in incoming):raise ValueError('integer trace required')
    iv=dict(incoming);outgoing=tuple((p,iv[p]+v) for p,v in dv)
    if any(v>12 for p,v in outgoing):raise ValueError('capacity-incompatible response')
    identity='response-'+digest((seq,incoming))[:24]
    return Response(identity,seq,incoming,dv,outgoing,level,tuple(children))

def relocate(r,g=SYMMETRIES[0],tr=(0,0,0)):
    """A placed local operation, with no change to its certificate identity."""
    def points(values):return tuple(sorted((add(transform(p,g),tr),v) for p,v in values))
    children=tuple((name,SYMMETRIES.index(compose(g,SYMMETRIES[o])),add(transform(p,g),tr)) for name,o,p in r.children)
    pose=(SYMMETRIES.index(compose(g,SYMMETRIES[r.pose[0]])),add(transform(r.pose[1],g),tr))
    return Response(r.identity,moved(r.sequence,g,tr),points(r.incoming),points(r.delta),points(r.outgoing),r.level,children,pose)

def composition(base,a,b):
    """Exact sequential interface law; both operations are already placed.

    On shared support B's input must equal A's output. Outside A's support,
    B's input is the combined input. Disjoint owners prevent double counting.
    The resulting operation is normalized with explicit descending child maps.
    """
    if set(a.sequence)&set(b.sequence):raise ValueError('overlapping response ownership')
    ai,ad,bi=dict(a.incoming),dict(a.delta),dict(b.incoming)
    if any(bi[p]!=ai[p]+ad[p] for p in ai.keys()&bi.keys()):raise ValueError('interface mismatch')
    incoming=ai|{p:v for p,v in bi.items() if p not in ai}
    origin=a.sequence[0][1]
    children=((a.identity,a.pose[0],sub(a.pose[1],origin)),(b.identity,b.pose[0],sub(b.pose[1],origin)))
    return operation(base,a.sequence+b.sequence,incoming,children,1+max(a.level,b.level))

def mine(donors,boundaries,model,per_size=8,sizes=(2,3,4,6,8,12)):
    start=time.monotonic();nodes={};counts=Counter();provenance=defaultdict(list);windows=0
    def tree(sequence,totals):
        if len(sequence)==1:r=operation(model.base,sequence,totals)
        else:
            cut=len(sequence)//2;left=tree(sequence[:cut],totals)
            after=Counter(totals)
            for o,tr in sequence[:cut]:after.update(dict(model.base.placement((o,tr)).occupancy))
            right=tree(sequence[cut:],after)
            left=relocate(left,tr=sequence[0][1]);right=relocate(right,tr=sequence[cut][1])
            r=composition(model.base,left,right)
            direct=operation(model.base,sequence,totals)
            if (r.sequence,r.incoming,r.delta,r.outgoing)!=(direct.sequence,direct.incoming,direct.delta,direct.outgoing):
                raise AssertionError('composition differs from direct expansion')
        nodes.setdefault(r.identity,r);return nodes[r.identity]
    for donor in donors:
        if donor['status']!='finite_exact_region':continue
        boundary=boundaries[donor['problem']];keys=tuple((o,tuple(tr)) for n,o,tr in donor['state']['placements'])
        totals=Counter(dict(boundary.exterior))
        for begin in range(len(keys)):
            for size in sizes:
                seq=keys[begin:begin+size]
                if len(seq)!=size:continue
                adj=adjacency(model.base,seq);seen={0};pending=[0]
                while pending:
                    for j in adj[pending.pop()]-seen:seen.add(j);pending.append(j)
                if len(seen)!=size:continue
                r=tree(seq,totals);counts[r.identity]+=1;windows+=1
                provenance[r.identity].append({'seed':donor['seed'],'problem':donor['problem'],'begin':begin,'size':size})
            totals.update(dict(model.base.placement(keys[begin]).occupancy))
    chosen=[]
    for size in sizes:
        candidates=[name for name in counts if len(nodes[name].sequence)==size]
        candidates.sort(key=lambda name:(-len({p['seed'] for p in provenance[name]}),-counts[name],name))
        chosen.extend(candidates[:per_size])
    keep=set()
    def retain(name):
        if name in keep:return
        keep.add(name)
        for child,o,tr in nodes[name].children:retain(child)
    for name in chosen:retain(name)
    return {'nodes':[nodes[name].packed() for name in sorted(keep)],'selected':chosen,
            'provenance':{name:provenance[name] for name in chosen},'counts':{name:counts[name] for name in chosen},
            'seconds':time.monotonic()-start,'connected_windows':windows,'distinct_responses':len(counts),
            'scope':'finite input traces from fresh local solutions; no complete boundary relation or infinite extension claim'}

def unpack(d):
    return Response(d['identity'],tuple((o,tuple(tr)) for o,tr in d['sequence']),
                    *(tuple((tuple(p),v) for p,v in d[name]) for name in ('incoming','delta','outgoing')),
                    d['level'],tuple((name,o,tuple(tr)) for name,o,tr in d['children']),
                    (d['pose'][0],tuple(d['pose'][1])))

def validate(library,base):
    records={n['identity']:unpack(n) for n in library['nodes']}
    if len(records)!=len(library['nodes']) or len(set(library['selected']))!=len(library['selected']):raise ValueError('duplicate atlas identity')
    for r in records.values():
        if r.pose!=(0,(0,0,0)) or type(r.level) is not int or r.level<0:raise ValueError('normalized finite hierarchy required')
        fresh=operation(base,r.sequence,dict(r.incoming),r.children,r.level)
        if fresh!=r:raise ValueError('altered local operation')
        if len(r.sequence)==1:
            if r.children or r.level:raise ValueError('invalid leaf')
        else:
            if len(r.children)!=2:raise ValueError('binary response composition required')
            a,b=[relocate(records[name],SYMMETRIES[o],tr) for name,o,tr in r.children]
            if any(child.level>=r.level for child in (a,b)) or composition(base,a,b)!=r:raise ValueError('altered child/interface map')
    if any(name not in records or len(records[name].sequence)<2 for name in library['selected']):raise ValueError('invalid offered response')
    return records

@dataclass(frozen=True)
class Action:
    sequence:tuple
    response:str='singleton'
    level:int=0

class Atlas:
    def __init__(self,library,universe,trace=True,max_size=12,limit=8):
        start=time.monotonic();self.universe=universe;self.trace=trace;self.limit=limit
        self.inventory=frozenset(universe.keys);self.index=defaultdict(list);self.by_orientation=defaultdict(list)
        if len(universe.types)!=1 or universe.types[0]!=singleton():raise ValueError('unmarked identity singleton inventory required')
        self.types=universe.types;seen=set();self.records=validate(library,universe.model.base)
        for name in library['selected']:
            r=self.records[name]
            if len(r.sequence)>max_size:continue
            for g in SYMMETRIES:
                t=relocate(r,g);sig=(t.sequence,t.incoming)
                if sig in seen:continue
                seen.add(sig);o=t.sequence[0][0];iv=dict(t.incoming)
                first=tuple(iv[p] for p,v in universe.model.orientations['base'][o])
                self.index[o,first].append(t);self.by_orientation[o].append(t)
        self.seconds=time.monotonic()-start
        self.manifest={'seconds':self.seconds,'templates':len(seen),'input_buckets':len(self.index),
                       'trace_matching':trace,'max_size':max_size,'limit':limit,'library_sha256':digest(library['nodes'])}

    def actions(self,model,state,graph,keys,check=lambda:None):
        start=time.monotonic();actions={Action((key,)) for key in keys};raw={}
        if tuple(model.types.values())!=self.types or state.allowed_points!=self.universe.allowed:raise ValueError('atlas scope mismatch')
        for first in keys:
            o,tr=first[1:];check()
            if self.trace:
                signature=tuple(state.totals.get(add(p,tr),0) for p,v in model.orientations['base'][o])
                candidates=self.index.get((o,signature),())
            else:candidates=self.by_orientation.get(o,())
            model.metrics['response_bucket_candidates']+=len(candidates)
            for r in candidates:
                check();model.metrics['response_trace_tests']+=1
                seq=tuple(('base',q,add(p,tr)) for q,p in r.sequence)
                if any(k not in self.inventory or (k[1],k[2]) in state.owned_base for k in seq):
                    model.metrics['response_inventory_misses']+=1;continue
                if self.trace:
                    valid=all(state.totals.get(add(p,tr),0)==v for p,v in r.incoming)
                else:valid=all(state.totals.get(add(p,tr),0)+v<=12 for p,v in r.delta)
                if not valid:model.metrics['response_trace_misses']+=1;continue
                gain=sum(v for p,v in r.delta if add(p,tr) in state.required)
                raw[seq]=(gain/len(seq),len(seq),r.identity,r.level)
        model.metrics['response_matches']+=len(raw)
        for seq,values in sorted(raw.items(),key=lambda x:(-x[1][0],-x[1][1],x[0]))[:self.limit]:
            actions.add(Action(seq,values[2],values[3]))
        model.metrics['response_offered']+=sum(len(a.sequence)>1 for a in actions)
        model.metrics['proposal_seconds']+=time.monotonic()-start
        return sorted(actions,key=lambda a:(a.sequence,a.response))

def features(model,state,graph,a):
    occ=Counter()
    for key in a.sequence:occ.update(dict(model.placement(key).occupancy))
    req=state.required;filled=sum(state.totals.get(p,0)+v==12 for p,v in occ.items() if p in req)
    return {'bias':1.,'response':float(len(a.sequence)>1),'size':len(a.sequence)/12,'level':a.level/4,
            'fill':filled/40,'required_gain':sum(v for p,v in occ.items() if p in req)/480,
            'optional_gain':sum(v for p,v in occ.items() if p not in req)/480,
            'incoming_contact':sum(state.totals.get(p,0)>0 for p in occ)/100,
            'outgoing_deficit':sum(12-state.totals.get(p,0)-v for p,v in occ.items() if p in req)/480,
            'frontier':len(graph.domains)/200,'orientation:'+str(a.sequence[0][1]):1.}

def search(boundary,universe,seed=0,attempt_limit=4000,seconds=6,atlas=None,policy=None,learn=False,rollout=False):
    """All lanes share the complete base graph and budgets on real base moves.

    Proposals are internally capacity-certified; execution validates the global
    scheduler after every constituent. Mismatches close a response transaction
    at its scheduled prefix. Failed children discard copies of every state and
    incidence field. No proof is claimed from the heuristic duplicate paths.
    """
    start=time.monotonic();model=universe.bind(boundary);state=boundary.initial();graph=Graph(model,state)
    rng=random.Random(seed);attempts=nodes=branches=forced=backs=macro_moves=interruptions=0
    best=state.copy();best_log=[];found=None;execution=[];traces=[];events=[]
    peak_points=len(graph.domains);peak_candidates=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    class Budget(Exception):pass
    def check():
        if attempts>=attempt_limit or (seconds is not None and time.monotonic()-start>=seconds):raise Budget()
    def record(s,log):
        nonlocal best,best_log
        if sum(s.totals.get(p,0)==12 for p in s.required)>sum(best.totals.get(p,0)==12 for p in best.required):
            best=s.copy();best_log=list(log)
    def visit(s,g,log):
        nonlocal attempts,nodes,branches,forced,backs,found,execution,macro_moves,interruptions,peak_points,peak_candidates,peak_incidences
        check();nodes+=1;record(s,log);kind,p,keys=g.decision(s)
        peak_points=max(peak_points,len(g.domains));peak_candidates=max(peak_candidates,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if kind=='dead':return
        if kind=='empty':found=s.copy();execution=list(log);return
        if kind=='forced':actions=[Action((keys[0],))]
        else:
            actions=atlas.actions(model,s,g,keys,check) if atlas else [Action((k,)) for k in keys]
            rng.shuffle(actions)
            if policy:
                fs=[features(model,s,g,a) for a in actions]
                if learn:
                    i,gradient=policy.select(rng,fs);traces.append(gradient);actions=[actions[i]]+actions[:i]+actions[i+1:]
                else:actions=[a for a,f in sorted(zip(actions,fs),key=lambda af:sum(policy.weights[k]*v for k,v in af[1].items()),reverse=True)]
            if rollout:actions=actions[:1]
        for a in actions:
            child=s.copy();cg=g.copy();child_log=list(log);used=0;stop=None
            for key in a.sequence:
                knd,pt,domain=cg.decision(child)
                if knd in ('dead','empty') or key not in domain:stop=knd;break
                check();attempts+=1;forced+=knd=='forced';branches+=knd=='branch'
                cg.update(model,child,child.place(model.placement(key)));used+=1
                child_log.append({'kind':knd,'point':pt,'placement':key,'response':a.response,
                                  'proposal_size':len(a.sequence),'proposal_offset':used-1})
                record(child,child_log)
            if used==0:raise AssertionError('response must begin in the actual selected domain')
            if len(a.sequence)>1:
                macro_moves+=used
                model.metrics['response_used:'+str(used)]+=1
                if used<len(a.sequence):interruptions+=1
                events.append({'response':a.response,'proposed':len(a.sequence),'used':used,'stop':stop})
            visit(child,cg,child_log)
            if found:return
            backs+=1
    try:
        visit(state,graph,[]);status='finite_exact_region' if found else 'dead_rollout' if rollout else 'exhausted_finite_region_uncertified'
    except (Budget,RecursionError):status='unknown_budget'
    result=found or best;log=execution if found else best_log
    if not verify_region(model,boundary,result,bool(found)):raise AssertionError('invalid response result')
    coverage=sum(result.totals.get(p,0)==12 for p in result.required)/len(result.required)
    elapsed=time.monotonic()-start;reward=coverage+(1 if found else -1)-.001*attempts-.01*elapsed
    if policy and learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,
            'nodes':nodes,'branches':branches,'forced':forced,'backtracks':backs,'attempted_base_placements':attempts,
            'explored_response_constituents':macro_moves,'response_interruptions':interruptions,'response_events':events,
            'coverage_fraction':coverage,'accepted_base_tiles':len(result.order),'state':packed_state(result),'execution':log,
            'metrics':dict(model.metrics),'reward':reward,'certificate':None,'verified':True,
            'peak_frontier_points':peak_points,'peak_candidate_nodes':peak_candidates,'peak_incidences':peak_incidences,
            'admissible_placements':model.admissible_placements,'budget':{'base_attempts':attempt_limit,'seconds':seconds}}
