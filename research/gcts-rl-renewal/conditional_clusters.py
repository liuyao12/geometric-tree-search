"""Parametric capacity responses and scheduler-adaptive constituent ordering.

This unmarked pilot derives interval preconditions analytically from the
aggregate occupancy. They are proposal interfaces, never point m-values or
candidate eliminations. The complete base graph retains every alternative.
"""
import hashlib,json,random,time
from collections import Counter,defaultdict
from dataclasses import dataclass
from turtle import Graph,Policy,SYMMETRIES,add,sub
from boundary_responses import Action,features as old_features,validate,relocate,digest
from boundary_macros import singleton
from frontier_responses import MODES,mode_features,rank_unique
from region_tiles import Boundary,packed_state,verify_region
from coverage import hexagon

def boundaries(training=False):
    """Frozen before official evaluation; no solution patches author targets."""
    allowed=frozenset(hexagon(18));out=[]
    if training:
        for i,(length,width) in enumerate(((5,3),(7,4),(9,2))):
            out.append(Boundary('conditional-train-strip-'+str(i),frozenset(p for p in allowed if abs(p[0])<=length and abs(2*p[1]+p[0])<=width),allowed))
        for i,(outer,inner) in enumerate(((5,2),(7,3))):out.append(Boundary('conditional-train-ring-'+str(i),frozenset(set(hexagon(outer))-set(hexagon(inner))),allowed))
        pts=set(add(p,(-3,2,1)) for p in hexagon(4))|set(add(p,(3,-2,-1)) for p in hexagon(4))
        out.append(Boundary('conditional-train-lobes',frozenset(pts),allowed))
        fixed=__import__('turtle').Model().placement((2,(5,-3,-2)))
        out.append(Boundary('conditional-train-exterior',frozenset(add(p,(-1,1,0)) for p in hexagon(4)),allowed,fixed.occupancy,(),((2,(5,-3,-2)),)))
    else:
        out.append(Boundary('conditional-long-strip',frozenset(p for p in allowed if abs(p[0])<=11 and abs(2*p[1]+p[0])<=6),allowed))
        out.append(Boundary('conditional-annulus',frozenset(set(hexagon(9))-set(hexagon(4))),allowed))
        pts=set(add(p,(-5,3,2)) for p in hexagon(5))|set(add(p,(5,-3,-2)) for p in hexagon(5))
        out.append(Boundary('conditional-two-lobes',frozenset(pts),allowed))
        fixed=__import__('turtle').Model().placement((5,(7,-4,-3)))
        pts=set(add(p,(1,0,-1)) for p in hexagon(6))|{(-12,6,6),(-11,6,5)}
        out.append(Boundary('conditional-fixed-and-pocket',frozenset(pts),allowed,fixed.occupancy,(),((5,(7,-4,-3)),)))
    return tuple(out)

def moving_families():
    """Existential finite authored choices, not continuous shape optimization."""
    allowed=frozenset(hexagon(18));families=[]
    for direction in (0,1):
        members=[]
        for shift in (-2,0,2):
            pts={p for p in allowed if abs(p[direction])<=9 and abs(2*p[(direction+1)%3]+p[direction]-shift)<=5}
            members.append(Boundary('conditional-moving-'+str(direction)+'-'+str(shift),frozenset(pts),allowed))
        families.append(tuple(members))
    return tuple(families)

@dataclass(frozen=True)
class Proposal:
    sequence:tuple
    response:str='singleton'
    level:int=0
    pose:tuple=(0,(0,0,0))

class CompiledAtlas:
    """Complete placements of this sampled library, indexed by every member.

    No graph degree uses this index. Per-query scan limits only bound proposal
    cost, with round-robin scans across the selected complete base domain.
    """
    def __init__(self,library,universe):
        start=time.monotonic();self.universe=universe
        if universe.types!=(singleton(),):raise ValueError('unmarked singleton inventory required')
        records=validate(library,universe.model.base);self.records=records;self.templates=[];self.poses=[];self.index=defaultdict(list)
        canonical={k:k for k in universe.keys};by_o=defaultdict(set)
        for n,o,tr in universe.keys:by_o[o].add(tr)
        hasher=hashlib.sha256();size_counts=Counter()
        for name in sorted(library['selected']):
            for o,g in enumerate(SYMMETRIES):
                r=relocate(records[name],g);upper=tuple((p,12-v) for p,v in r.delta)
                if any(u<0 for p,u in upper):raise ValueError('internally overfull cluster')
                ti=len(self.templates);self.templates.append((r,upper,o))
                translations=None
                for q,p in r.sequence:
                    possible={sub(tr,p) for tr in by_o[q]}
                    translations=possible if translations is None else translations&possible
                    if not translations:break
                for tr in sorted(translations):
                    members=tuple(canonical['base',q,add(p,tr)] for q,p in r.sequence)
                    pi=len(self.poses);self.poses.append((ti,tr,members));size_counts[len(members)]+=1
                    for k in members:self.index[k].append(pi)
                    hasher.update((json.dumps((name,o,tr,members),separators=(',',':'))+'\n').encode())
        # Interleave sizes before bounded scans; no scale monopolizes the quota.
        for k,ids in self.index.items():
            buckets=defaultdict(list)
            for i in ids:buckets[len(self.poses[i][2])].append(i)
            self.index[k]=[i for j in range(max(map(len,buckets.values()))) for size in sorted(buckets) for i in buckets[size][j:j+1]]
        self.manifest={'seconds':time.monotonic()-start,'templates':len(self.templates),'placements':len(self.poses),
            'member_incidences':sum(map(len,self.index.values())),'indexed_base_keys':len(self.index),
            'sizes':dict(size_counts),'placement_sha256':hasher.hexdigest(),'library_sha256':digest(library['nodes']),
            'scope':'complete sampled-library pose index; proposals only; base graph independent'}

    def actions(self,model,state,graph,keys,condition='interval',max_size=12,scan_limit=256,limit=8,check=lambda:None):
        if condition not in ('trace','interval'):raise ValueError('unknown interface')
        if state.allowed_points!=self.universe.allowed or tuple(model.types.values())!=self.universe.types:raise ValueError('atlas scope mismatch')
        start=time.monotonic();out=[Proposal((k,)) for k in keys];raw={};scanned=0
        streams=[(k,iter(i for i in self.index.get(k,()) if len(self.poses[i][2])<=max_size)) for k in keys]
        while streams and scanned<scan_limit:
            keep=[]
            for first,it in streams:
                if scanned>=scan_limit:break
                try:pi=next(it)
                except StopIteration:continue
                keep.append((first,it));check();scanned+=1;ti,tr,members=self.poses[pi];r,upper,o=self.templates[ti]
                if any((k[1],k[2]) in state.owned_base for k in members):model.metrics['conditional_owner_misses']+=1;continue
                values=r.incoming if condition=='trace' else upper
                valid=all(state.totals.get(add(p,tr),0)==v for p,v in values) if condition=='trace' else all(state.totals.get(add(p,tr),0)<=u for p,u in upper)
                if not valid:model.metrics['conditional_input_misses']+=1;continue
                # Same offered placement pool in the fixed/adaptive comparison.
                sequence=(first,)+tuple(k for k in members if k!=first)
                a=Proposal(sequence,r.identity,r.level,(o,tr));gain=sum(v for p,v in r.delta if add(p,tr) in state.required)
                sig=(first,frozenset(members));score=(gain/len(members),len(members),r.identity)
                if sig not in raw or score>raw[sig][0]:raw[sig]=(score,a)
            streams=keep
        chosen=sorted(raw.values(),key=lambda x:(-x[0][0],-x[0][1],x[1].sequence,x[1].response))[:limit]
        out.extend(a for score,a in chosen);model.metrics['conditional_scans']+=scanned;model.metrics['conditional_matches']+=len(raw)
        model.metrics['conditional_offered']+=len(chosen);model.metrics['proposal_seconds']+=time.monotonic()-start
        return sorted(out,key=lambda a:(a.sequence,a.response,a.pose))

@dataclass(frozen=True)
class Pending:
    proposal:Proposal
    remaining:tuple
    used:int
    mode:str

def permitted(pending,keys,adaptive):
    if pending is None:return ()
    return tuple(k for k in pending.remaining if k in keys) if adaptive else pending.remaining[:1] if pending.remaining[0] in keys else ()

def move_features(model,state,graph,a,keys):
    f={'move:'+k:v for k,v in old_features(model,state,graph,Action(a.sequence,a.response,a.level)).items()}
    f['move:available_fraction']=sum(k in graph.edges for k in a.sequence)/len(a.sequence)
    f['move:eligible_fraction']=sum(k in keys for k in a.sequence)/len(a.sequence)
    return f

def search(boundary,universe,atlas,seed=0,attempt_limit=4000,seconds=5,condition='interval',adaptive=True,
           fixed_mode=None,policy=None,learn=False,rollout=False,scan_limit=256,observer=None):
    if condition not in ('trace','interval') or fixed_mode not in (*MODES,None):raise ValueError('unknown configuration')
    if learn and policy is None:raise ValueError('learning requires policy')
    start=time.monotonic();model=universe.bind(boundary);state=boundary.initial();graph=Graph(model,state);rng=random.Random(seed)
    stats=Counter();feedback=Counter();events=[];traces=[];choices=[];samples=[];best=state.copy();best_log=[];found=None;execution=[]
    peak_points=len(graph.domains);peak_candidates=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    class Budget(Exception):pass
    def check(move=False):
        if (move and stats['attempts']>=attempt_limit) or (seconds is not None and time.monotonic()-start>=seconds):raise Budget()
    def record(s,log):
        nonlocal best,best_log
        if sum(s.totals.get(p,0)==12 for p in s.required)>sum(best.totals.get(p,0)==12 for p in best.required):best=s.copy();best_log=list(log)
    def close(plan,stop):
        if plan is None:return
        feedback[plan.mode,'closed']+=1;feedback[plan.mode,'interrupted']+=bool(plan.remaining)
        stats['response_interruptions']+=bool(plan.remaining)
        events.append({'response':plan.proposal.response,'pose':plan.proposal.pose,'proposed':len(plan.proposal.sequence),
                       'used':plan.used,'stop':stop,'mode':plan.mode})
    def pick(fs,kind):
        if learn:
            i,gradient=policy.select(rng,fs);traces.append(gradient);choices.append({'kind':kind,'features':fs,'selected':i});return i
        if policy:
            scores=[sum(policy.weights[k]*v for k,v in f.items()) for f in fs];return rng.choice([i for i,s in enumerate(scores) if s==max(scores)])
        return rng.randrange(len(fs))
    def visit(s,g,log,pending=None):
        nonlocal found,execution,peak_points,peak_candidates,peak_incidences
        check();stats['nodes']+=1;record(s,log);peak_points=max(peak_points,len(g.domains));peak_candidates=max(peak_candidates,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        kind,p,keys=g.decision(s)
        if kind in ('dead','empty'):
            close(pending,kind)
            if kind=='empty':found=s.copy();execution=list(log)
            return
        eligible=permitted(pending,keys,adaptive)
        if pending and not eligible:close(pending,'scheduler-'+kind);pending=None
        chosen={};mode='base';fs_mode=None
        if kind=='forced':order=keys
        elif pending:
            order=list(keys);rng.shuffle(order);order=[k for k in eligible]+[k for k in order if k not in eligible]
        else:
            stats['resolution_decisions']+=1;fs_mode=[mode_features(s,g,keys,m,feedback) for m in MODES]
            mode=fixed_mode or MODES[pick(fs_mode,'mode')];stats['mode:'+mode]+=1
            actions=[Proposal((k,)) for k in keys] if mode=='base' else atlas.actions(model,s,g,keys,condition,4 if mode=='small' else 12,scan_limit,check=check)
            rng.shuffle(actions)
            if policy:
                fs=[move_features(model,s,g,a,keys) for a in actions]
                if learn:i=pick(fs,'move');actions=[actions[i]]+actions[:i]+actions[i+1:]
                else:actions=[a for a,f in sorted(zip(actions,fs),key=lambda af:sum(policy.weights[k]*v for k,v in af[1].items()),reverse=True)]
            order,chosen,duplicates=rank_unique(keys,actions);stats['duplicate_action_children_avoided']+=duplicates
        assert set(order)==set(keys) and len(order)==len(set(order))
        if len(samples)<6:
            samples.append({'placements':list(s.order),'kind':kind,'point':p,'domain':keys,'ordered':order,
                'mode':mode,'mode_features':fs_mode,'feedback':[(m,k,v) for (m,k),v in sorted(feedback.items())],
                'pending':None if pending is None else {'response':pending.proposal.response,'pose':pending.proposal.pose,
                    'members':pending.proposal.sequence,'remaining':pending.remaining,'used':pending.used}})
        if observer:observer(s,g,kind,p,tuple(keys),tuple(order),pending)
        if rollout:order=order[:1]
        for key in order:
            check(True);child=s.copy();cg=g.copy();stats['attempts']+=1;stats[kind]+=1
            plan=pending if pending and key in eligible else None
            if plan is None and key in chosen and len(chosen[key].sequence)>1:
                a=chosen[key];plan=Pending(a,a.sequence,0,mode);stats['response_starts']+=1
            a=plan.proposal if plan else Proposal((key,));offset=plan.used if plan else 0
            step={'kind':kind,'point':p,'placement':key,'response':a.response,'proposal_pose':a.pose,
                  'proposal_size':len(a.sequence),'proposal_offset':offset,'condition':condition,'adaptive':adaptive}
            if plan and key!=plan.remaining[0]:stats['reordered_constituents']+=1
            cg.update(model,child,child.place(model.placement(key)));child_log=log+[step]
            if plan:
                stats['explored_response_constituents']+=1;remaining=tuple(k for k in plan.remaining if k!=key)
                plan=Pending(a,remaining,offset+1,plan.mode)
                if not remaining:close(plan,'complete');plan=None
            record(child,child_log);visit(child,cg,child_log,plan)
            if found is not None:return
            stats['backtracks']+=1
    try:
        visit(state,graph,[]);status='finite_exact_region' if found is not None else 'dead_rollout' if rollout else 'exhausted_finite_region_uncertified'
    except (Budget,RecursionError):status='unknown_budget'
    result=found if found is not None else best;log=execution if found is not None else best_log
    if not verify_region(model,boundary,result,found is not None):raise AssertionError('invalid conditional result')
    coverage=sum(result.totals.get(p,0)==12 for p in result.required)/len(result.required);elapsed=time.monotonic()-start
    reward=coverage+(1 if found is not None else -1)-.001*stats['attempts']-.01*elapsed
    if learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,
        'nodes':stats['nodes'],'branches':stats['branch'],'forced':stats['forced'],'backtracks':stats['backtracks'],
        'attempted_base_placements':stats['attempts'],'coverage_fraction':coverage,'accepted_base_tiles':len(result.order),
        'state':packed_state(result),'execution':log,'metrics':dict(model.metrics),'reward':reward,'reward_elapsed_seconds':elapsed,
        'certificate':None,'verified':True,'stats':dict(stats),'response_events':events,'decision_samples':samples,'learning_choices':choices,
        'condition':condition,'adaptive':adaptive,'peak_frontier_points':peak_points,'peak_candidate_nodes':peak_candidates,'peak_incidences':peak_incidences,
        'admissible_placements':model.admissible_placements,'budget':{'base_attempts':attempt_limit,'seconds':seconds,'proposal_scans':scan_limit},
        'scope':'complete base-key DFS; analytic interval interfaces and adaptive response ordering are proposals only; no learned marking or plane proof'}

def movable(family,universe,atlas,seed=0,**kwargs):
    start=time.monotonic();attempts=[]
    for i,b in enumerate(family):
        r=search(b,universe,atlas,seed+i,**kwargs);attempts.append({'boundary':b.identity,'result':r})
        if r['status']=='finite_exact_region':return {'status':'finite_exact_movable_region','selected':b.identity,'attempts':attempts,'seconds':time.monotonic()-start}
    return {'status':'exhausted_finite_family_uncertified' if all(a['result']['status']=='exhausted_finite_region_uncertified' for a in attempts) else 'unknown_budget',
            'selected':None,'attempts':attempts,'seconds':time.monotonic()-start}
