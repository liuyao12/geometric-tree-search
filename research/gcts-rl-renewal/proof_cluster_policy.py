"""Zero-weight sequential softmax policy for checked proof-cluster proposals.

Ordering and deferral only: no inferred constraints, degree changes or theorem
labels enter legality. Float policy scores never enter exact point checking.
All bounded contextual instances are eligible; each branch retains base fallback.
"""
import collections,copy,math,time
import proof_clusters as H
from turtle import Graph
S=H.S
FEATURES=('defer','defer_multiplication','defer_progress','defer_degree','members','level','target_member','direction','context_depth','term_shrink','input_already_placed','member_degrees')

def nodes(t):return 1 if t[0]=='var' else 1+sum(nodes(a) for a in t[2])
def has_function(t,name):return t[0]=='fun' and (t[1]==name or any(has_function(a,name) for a in t[2]))
def features(model,state,graph,point,item):
    n=model.length;progress=len(state.order)/n;degree=math.log1p(len(graph.domains[point]))/6
    body=model.catalog['formulas'][model.catalog['target_id']];mul=any(has_function(t,'mul') for t in body[1:]);bound=model.catalog['configuration']['term_bound']
    if item is None:return [1,float(mul),progress,degree]+[0]*8
    keys=item['members'];inst=item['instance'];input_slot=keys[0][2][0];placed={k[0] for k in state.order}
    return [0,0,0,0,len(keys)/4,item['level']/2,float(any(k[0]==n-1 for k in keys)),float(inst['direction']),len(inst['context'])/bound,(nodes(inst['before'])-nodes(inst['after']))/bound,float(input_slot in placed),sum(math.log1p(len(graph.domains[S.cell(k[0])])) for k in keys)/(6*len(keys))]

class Random:
    """Declared 32-bit LCG; export every uniform variate used by sampling."""
    def __init__(self,seed):self.state=seed%(2**32)
    def draw(self):self.state=(1664525*self.state+1013904223)%(2**32);return (self.state+.5)/(2**32)

def softmax(weights,fs):
    scores=[sum(w*x for w,x in zip(weights,f)) for f in fs];top=max(scores);xs=[math.exp(s-top) for s in scores];den=sum(xs);return [x/den for x in xs]

class Policy:
    def __init__(self,seed=1,weights=None,stochastic=False,limit=8):
        self.weights=[0.0]*len(FEATURES) if weights is None else list(weights)
        if len(self.weights)!=len(FEATURES) or not all(math.isfinite(w) for w in self.weights):raise ValueError('finite declared policy vector required')
        self.random=Random(seed);self.stochastic=stochastic;self.limit=limit;self.events=[];self.seconds=0.0
    def choose(self,model,state,graph,point,items):
        began=time.perf_counter();ordered=sorted(items,key=H.digest);options=ordered+[None];ids=[H.digest(item) if item is not None else 'defer' for item in options];fs=[features(model,state,graph,point,item) for item in options];available=list(range(len(options)));draws=[];offered=[]
        for _ in range(min(self.limit,len(options))):
            vectors=[fs[i] for i in available];prob=softmax(self.weights,vectors);u=None
            if self.stochastic:
                u=self.random.draw();total=0;chosen=len(available)-1
                for j,p in enumerate(prob):
                    total+=p
                    if u<total:chosen=j;break
            else:
                # Equal-score tie preserves identity order; deferral is last.
                scores=[sum(w*x for w,x in zip(self.weights,f)) for f in vectors];chosen=max(range(len(scores)),key=lambda j:scores[j])
            selected=available[chosen];expected=[sum(p*f[k] for p,f in zip(prob,vectors)) for k in range(len(FEATURES))];gradient=[fs[selected][k]-expected[k] for k in range(len(FEATURES))]
            draws.append(dict(action=ids[selected],uniform=u,probability=prob[chosen],gradient=gradient));available.pop(chosen)
            if options[selected] is None:break
            offered.append(options[selected])
        event=dict(id=len(self.events),order=list(state.order),point=point,pool_sha256=H.digest(ordered),pool_count=len(ordered),draws=draws,offered=[H.digest(i) for i in offered]);self.events.append(event);self.seconds+=time.perf_counter()-began;return offered,event['id']

def used_gradients(result):
    """Only choices actually reached by the completed DFS are credited.

    Pre-sampled suffix choices after a successful child are censored. Deferral
    counts only when base fallback actually executes. Unknown trees supply no
    update because their reached-choice prefix is not fully exported.
    """
    if result['search_tree'] is None:return [],[]
    used=[];gradients=[]
    def visit(tree):
        if 'policy_event' in tree:
            e=result['policy_events'][tree['policy_event']];trials=len(tree['proposals']);count=trials
            if tree['children'] and len(e['draws'])>trials and e['draws'][trials]['action']=='defer':count+=1
            used.append(dict(event=e['id'],draws=count))
            gradients.extend(d['gradient'] for d in e['draws'][:count])
        for trial in tree.get('proposals',[]):
            if trial['trace']['status']=='accepted_cluster':visit(trial['tree'])
        for child in tree.get('children',[]):visit(child['tree'])
    visit(result['search_tree']);return gradients,used

def reward(result,native,attempt_limit=50000,native_limit=100000000):
    verified=native is not None and native['status']=='accepted'
    return float(verified)-math.log1p(result['base_attempts'])/math.log1p(attempt_limit)-(native.get('steps',0)/native_limit/10 if native else 0)

def branch_returns(result,native):
    """Delayed continuation outcome and actual constituent/base attempt cost.

    Only complete exported subtrees supply credit. Success requires the entire
    episode's native acceptance; a failed proposal is never a pruning rule.
    """
    if result['search_tree'] is None:return []
    verified=native is not None and native['status']=='accepted';records=[];limit=result['limits']['base_attempts']
    def visit(tree):
        if tree['kind']=='empty':return 0,True
        if tree['kind']=='dead':return 0,False
        own=[];total=0;success=False
        for j,trial in enumerate(tree['proposals']):
            cost=len(trial['trace']['steps']);okay=False
            if trial['trace']['status']=='accepted_cluster':extra,okay=visit(trial['tree']);cost+=extra
            total+=cost;success=success or okay;own.append((j,cost,okay))
        base_cost=0;base_success=False
        for child in tree['children']:
            extra,okay=visit(child['tree']);base_cost+=1+extra;base_success=base_success or okay
        total+=base_cost;success=success or base_success
        if 'policy_event' in tree:
            e=result['policy_events'][tree['policy_event']]
            if tree['children'] and len(e['draws'])>len(own) and e['draws'][len(own)]['action']=='defer':own.append((len(own),base_cost,base_success))
            for draw,cost,okay in own:
                records.append(dict(event=e['id'],draw=draw,base_attempts=cost,verified_continuation=verified and okay,value=float(verified and okay)-math.log1p(cost)/math.log1p(limit)))
        return total,success
    cost,success=visit(result['search_tree'])
    if cost!=result['base_attempts']:raise ValueError('complete tree work agrees before credit assignment')
    return sorted(records,key=lambda r:(r['event'],r['draw']))

def update(weights,baseline,result,native,rate=.2):
    credits=branch_returns(result,native);r=reward(result,native);total=[0.0]*len(FEATURES);next_baseline=baseline
    for item in credits:
        advantage=item['value']-next_baseline;gradient=result['policy_events'][item['event']]['draws'][item['draw']]['gradient'];item.update(baseline_before=next_baseline,advantage=advantage)
        next_baseline=.9*next_baseline+.1*item['value'];item['baseline_after']=next_baseline
        for k,g in enumerate(gradient):total[k]+=advantage*g
    next_weights=[max(-6,min(6,w+rate*g)) for w,g in zip(weights,total)]
    return dict(reward=r,baseline_before=baseline,baseline_after=next_baseline,credits=credits,gradient=total,weights_before=list(weights),weights_after=next_weights,updated=result['search_tree'] is not None,rate=rate)

def search(c,length,library=(),policy=None,seconds=5,attempt_limit=50000,proposal_limit=8,index_limit=50000,diagnostics=12):
    """Notebook-30 DFS with one isolated hook for policy ordering/deferral.

    Frozen historical source is preserved. Transaction validation and exact
    model/graph code are reused; all complete domains and decisions are audited.
    """
    began=time.perf_counter();library=copy.deepcopy(library);library_sha=H.digest(library);model=S.Model(c,length);build_seconds=time.perf_counter()-began;state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began-build_seconds
    index=H.Index(c,length,library,index_limit);stats=collections.Counter();samples=[];transaction_samples=[];found=None;found_transactions=[];best=state.copy();peak_nodes=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    if policy is not None:
        if policy.events:raise ValueError('fresh episode controller required')
        if policy.limit!=proposal_limit:raise ValueError('policy and search proposal caps agree')
    def tick():
        if stats['base_attempts']>=attempt_limit or time.perf_counter()-began>seconds:raise H.Budget()
        stats['base_attempts']+=1
    def visit(s,g,transactions):
        nonlocal found,best,found_transactions,peak_nodes,peak_incidences
        stats['nodes']+=1
        if time.perf_counter()-began>seconds:raise H.Budget()
        kind,p,keys=g.decision(s);peak_nodes=max(peak_nodes,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if len(samples)<diagnostics:samples.append(dict(order=list(s.order),kind=kind,point=p,degrees={str(q):len(v) for q,v in g.domains.items()}))
        if kind=='dead':return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s.copy()
        if kind=='empty':found=s;found_transactions=transactions;return True,dict(kind=kind)
        tree=dict(kind=kind,point=p,proposals=[],children=[]);stats['forced' if kind=='forced' else 'branches']+=1
        if kind=='branch' and library:
            t=time.perf_counter();offered,count=index.offered(model,s,g,p,None if policy else proposal_limit);stats['proposal_enumeration_seconds']+=time.perf_counter()-t;stats['compatible_proposals']+=count
            if policy is not None:offered,tree['policy_event']=policy.choose(model,s,g,p,offered)
            for item in offered:
                stats['proposal_trials']+=1;t=time.perf_counter();trace,child,cg=H.execute(model,s,g,item,tick);stats['proposal_validation_seconds']+=time.perf_counter()-t
                stats['constituent_branch_steps']+=sum(step['kind']=='branch' for step in trace['steps']);stats['constituent_forced_steps']+=sum(step['kind']=='forced' for step in trace['steps']);stats['validation_placements']+=len(trace['steps'])
                trial=dict(item=item,trace=trace)
                if len(transaction_samples)<20:transaction_samples.append(dict(order=list(s.order),**trial))
                tree['proposals'].append(trial)
                if trace['status']=='unknown_transaction_budget':raise H.Budget()
                if child is None:stats['proposal_rejections']+=1;continue
                stats['accepted_proposal_trials']+=1;okay,sub=visit(child,cg,transactions+[dict(item,steps=trace['steps'])]);trial['tree']=sub
                if okay:return True,tree
                stats['backtracks']+=1
        for key in keys:
            tick();child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(key)));stats['singleton_attempts']+=1
            okay,sub=visit(child,cg,transactions);tree['children'].append(dict(key=key,tree=sub))
            if okay:return True,tree
            stats['backtracks']+=1
        return False,tree
    tree=None
    try:okay,tree=visit(state,graph,[]);status='finite_exact_proof_tiling' if okay else 'exhausted_finite_proof_envelope'
    except H.Budget:status='unknown_search_budget'
    selected=found or best
    if not S.point_check(model,selected.order,found is not None):raise ValueError('saved policy state failed exact point check')
    result=dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,nodes=stats['nodes'],base_attempts=stats['base_attempts'],stats=dict(stats),seconds=time.perf_counter()-began,build_seconds=build_seconds,graph_seconds=graph_seconds,index_seconds=index.seconds,index_instances=len(index.instances),index_complete=index.complete,library_sha256=library_sha,mode='clusters',candidate_universe=len(model.cache),peak_candidate_nodes=peak_nodes,peak_incidences=peak_incidences,metrics=dict(model.metrics),samples=samples,transaction_samples=transaction_samples,solution_transactions=found_transactions,search_tree=tree,limits=dict(seconds=seconds,base_attempts=attempt_limit,proposal_limit=proposal_limit,index_instances=index_limit),scope='same complete base graph and scheduler; policy orders checked cluster proposals or defers; all base alternatives remain; specialized contextual arithmetic, no learned pruning',policy_events=policy.events if policy else [],policy_seconds=policy.seconds if policy else 0,policy_weights=list(policy.weights) if policy else None,policy_stochastic=policy.stochastic if policy else False,random_state=policy.random.state if policy else None)
    if found:
        before=time.perf_counter();result['decoded']=S.decode(c,selected.order,length);result['decode_seconds']=time.perf_counter()-before
    return result
