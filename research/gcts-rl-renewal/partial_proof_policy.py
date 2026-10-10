"""Retain the actually executed DFS prefix; learn without relabeling cutoffs.

The frozen notebook-31 features and controller only order proposals. A local
progress return uses independently replayable viable point states, not a claim
that a partial proof extends. All primitive alternatives remain unchanged.
"""
import collections,copy,math,time
import proof_cluster_policy as R
import proof_clusters as H
from turtle import Graph
S=H.S;FEATURES=R.FEATURES;Policy=R.Policy

def trace_tree(result):
    return result['search_tree'] if result['search_tree'] is not None else result['partial_tree']

def local_returns(result,native,length):
    verified=native is not None and native['status']=='accepted';records=[]
    def visit(tree):
        peak=tree['depth'] if tree['viable'] else -1
        if tree['kind'] in ('empty','dead','cutoff'):
            return 0,tree['kind']=='empty',peak
        total=0;solved=False;own=[]
        for j,trial in enumerate(tree['proposals']):
            cost=len(trial['trace']['steps']);okay=False;high=tree['depth']
            if trial['trace']['status']=='accepted_cluster':
                extra,okay,child_peak=visit(trial['tree']);cost+=extra
                high=max(high,tree['depth']+len(trial['trace']['steps']),child_peak)
            # An interrupted transaction is rolled back. Its partial occupancy
            # is not committed progress; zero-step interruptions get no credit.
            if trial['trace']['status']!='unknown_transaction_budget' or cost:
                own.append((j,cost,okay,high,trial['trace']['status']))
            total+=cost;solved|=okay;peak=max(peak,high)
        work=0;success=False;high=tree['depth']
        for child in tree['children']:
            extra,okay,child_peak=visit(child['tree']);work+=1+extra
            success|=okay;high=max(high,child_peak)
        total+=work;solved|=success;peak=max(peak,high)
        if 'policy_event' in tree:
            event=result['policy_events'][tree['policy_event']]
            j=len(tree['proposals'])
            if tree['children'] and len(event['draws'])>j and event['draws'][j]['action']=='defer':own.append((j,work,success,high,'base_fallback'))
            for j,cost,okay,high,status in own:
                gain=max(0,high-tree['depth'])
                records.append(dict(event=event['id'],draw=j,base_attempts=cost,viable_gain=gain,verified_continuation=verified and okay,action_status=status,value=float(verified and okay)+gain/length-math.log1p(cost)/math.log1p(result['limits']['base_attempts'])))
        return total,solved,peak
    cost,solved,peak=visit(trace_tree(result))
    if cost!=result['base_attempts']:raise ValueError('entire executed prefix work must agree before local credit')
    return sorted(records,key=lambda x:(x['event'],x['draw']))

def update(weights,baseline,result,native,length,signal='local',rate=.2):
    if signal=='complete':return R.update(weights,baseline,result,native,rate)
    if signal!='local':raise ValueError('declared return signal required')
    credits=local_returns(result,native,length);total=[0.0]*len(FEATURES);b=baseline
    for item in credits:
        advantage=item['value']-b;item.update(baseline_before=b,advantage=advantage)
        b=.9*b+.1*item['value'];item['baseline_after']=b
        for k,g in enumerate(result['policy_events'][item['event']]['draws'][item['draw']]['gradient']):total[k]+=advantage*g
    return dict(reward=R.reward(result,native),baseline_before=baseline,baseline_after=b,credits=credits,gradient=total,weights_before=list(weights),weights_after=[max(-6,min(6,w+rate*g)) for w,g in zip(weights,total)],updated=bool(credits),rate=rate)

def search(c,length,library=(),policy=None,seconds=5,attempt_limit=50000,proposal_limit=8,index_limit=50000,diagnostics=12):
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
        if time.perf_counter()-began>seconds:
            return None,dict(kind='cutoff',reason='entry_wall',depth=len(s.order),viable=g.decision(s)[0]!='dead')
        kind,p,keys=g.decision(s);peak_nodes=max(peak_nodes,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if len(samples)<diagnostics:samples.append(dict(order=list(s.order),kind=kind,point=p,degrees={str(q):len(v) for q,v in g.domains.items()}))
        leaf=dict(kind=kind,depth=len(s.order),viable=kind!='dead')
        if kind=='dead':return False,dict(leaf,point=p)
        if len(s.order)>len(best.order):best=s.copy()
        if kind=='empty':found=s;found_transactions=transactions;return True,leaf
        tree=dict(leaf,point=p,proposals=[],children=[]);stats['forced' if kind=='forced' else 'branches']+=1
        if kind=='branch' and library:
            t=time.perf_counter();offered,count=index.offered(model,s,g,p,None if policy else proposal_limit);stats['proposal_enumeration_seconds']+=time.perf_counter()-t;stats['compatible_proposals']+=count
            if policy is not None:offered,tree['policy_event']=policy.choose(model,s,g,p,offered)
            for item in offered:
                stats['proposal_trials']+=1;t=time.perf_counter();trace,child,cg=H.execute(model,s,g,item,tick);stats['proposal_validation_seconds']+=time.perf_counter()-t
                stats['constituent_branch_steps']+=sum(step['kind']=='branch' for step in trace['steps']);stats['constituent_forced_steps']+=sum(step['kind']=='forced' for step in trace['steps']);stats['validation_placements']+=len(trace['steps'])
                trial=dict(item=item,trace=trace);tree['proposals'].append(trial)
                if len(transaction_samples)<20:transaction_samples.append(dict(order=list(s.order),**trial))
                if trace['status']=='unknown_transaction_budget':return None,tree
                if child is None:stats['proposal_rejections']+=1;continue
                stats['accepted_proposal_trials']+=1;okay,sub=visit(child,cg,transactions+[dict(item,steps=trace['steps'])]);trial['tree']=sub
                if okay is not False:return okay,tree
                stats['backtracks']+=1
        for key in keys:
            try:tick()
            except H.Budget:return None,dict(tree,cutoff='base_before_placement')
            child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(key)));stats['singleton_attempts']+=1
            okay,sub=visit(child,cg,transactions);tree['children'].append(dict(key=key,tree=sub))
            if okay is not False:return okay,tree
            stats['backtracks']+=1
        return False,tree
    okay,tree=visit(state,graph,[]);status='finite_exact_proof_tiling' if okay is True else 'exhausted_finite_proof_envelope' if okay is False else 'unknown_search_budget'
    selected=found or best
    if not S.point_check(model,selected.order,found is not None):raise ValueError('saved partial-policy state failed exact point check')
    result=dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,nodes=stats['nodes'],base_attempts=stats['base_attempts'],stats=dict(stats),seconds=time.perf_counter()-began,build_seconds=build_seconds,graph_seconds=graph_seconds,index_seconds=index.seconds,index_instances=len(index.instances),index_complete=index.complete,library_sha256=library_sha,mode='clusters',candidate_universe=len(model.cache),peak_candidate_nodes=peak_nodes,peak_incidences=peak_incidences,metrics=dict(model.metrics),samples=samples,transaction_samples=transaction_samples,solution_transactions=found_transactions,search_tree=tree if okay is not None else None,partial_tree=tree if okay is None else None,limits=dict(seconds=seconds,base_attempts=attempt_limit,proposal_limit=proposal_limit,index_instances=index_limit),scope='unchanged primitive graph and proposal transaction; complete or partial executed prefix retained; cutoffs remain unknown; viable occupancy is a local reward proxy, never proof or pruning',policy_events=policy.events if policy else [],policy_seconds=policy.seconds if policy else 0,policy_weights=list(policy.weights) if policy else None,policy_stochastic=policy.stochastic if policy else False,random_state=policy.random.state if policy else None)
    if found:
        before=time.perf_counter();result['decoded']=S.decode(c,selected.order,length);result['decode_seconds']=time.perf_counter()-before
    return result
