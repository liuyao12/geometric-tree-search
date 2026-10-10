"""Fresh episodic cluster ranking; exact inventory and point constraints are unchanged.

RL learns only ordering of certified metatile proposals. All primitive fallback
and global dead/forced/generation scheduling remain. Integer features and frozen
integer parameters make evaluation ordering exact. Sampling/gradient arithmetic
is approximate and cannot supply a proof or candidate exclusion.
"""
import collections,math,random,time
import induction_clusters as H
import induction_proof_tiles as T,semantic_proof_tiles as S,coarse_proof_tiles as M
from proof_clusters import digest
from turtle import Graph
FEATURE_SCALE=1024
WEIGHT_SCALE=1000000
FEATURES=('additional_cells','goal_cell','mean_slot','span','internal_premises',
          'resolved_external_premises','mean_premise_gap','conditional_steps',
          'generalization_steps','induction_steps','progress_times_size')
def initial_policy(library):
    return dict(version='induction-cluster-policy-1',feature_names=list(FEATURES),
                feature_scale=FEATURE_SCALE,weight_scale=WEIGHT_SCALE,
                weights=[0]*len(FEATURES),library_sha256=digest(library),initialization='zero')
def feature_vector(c,n,members,filled):
    slots={k[0] for k in members};refs=[(slot,j) for slot,rid,js in members for j in js]
    external=[j for slot,j in refs if j not in slots]
    ops=[]
    for slot,rid,js in members:
        recipe=c['rules'][rid]['recipe']
        ops.append(recipe['witness']['rule'] if recipe['kind']=='primitive' else recipe.get('operation','copy'))
    values=((len(members)-1,2),(int(n-1 in slots),1),(sum(slots),len(slots)*n),
            (max(slots)-min(slots)+1,n),(sum(j in slots for slot,j in refs),max(1,len(refs))),
            (sum(j in filled for j in external),max(1,len(external))),
            (sum(slot-j for slot,j in refs),max(1,len(refs))*n),
            (sum(op.startswith('conditional-') for op in ops),len(ops)),
            (ops.count('generalize'),len(ops)),(ops.count('induction'),len(ops)),
            (len(filled)*(len(members)-1),2*n))
    return tuple(FEATURE_SCALE*a//b for a,b in values)
def score(features,policy):return sum(a*b for a,b in zip(features,policy['weights']))
def validate(policy,library,stochastic):
    if policy is None:
        if stochastic:raise ValueError('sampling requires a frozen policy')
        return
    expected=initial_policy(library)
    if set(policy)!=set(expected) or any(policy[k]!=expected[k] for k in expected if k!='weights'):
        raise ValueError('declared policy features and fresh library binding')
    if len(policy['weights'])!=len(FEATURES) or any(type(w) is not int or abs(w)>2*WEIGHT_SCALE for w in policy['weights']):
        raise ValueError('bounded integer policy weights')
def probabilities(pool,features,policy):
    logits=[score(features[k],policy)/(FEATURE_SCALE*WEIGHT_SCALE) for k in pool]
    maximum=max(logits);weights=[math.exp(x-maximum) for x in logits];total=sum(weights)
    return [w/total for w in weights]
def ordered(macros,features,policy,stochastic,rng):
    if policy is None:return list(macros),None,{}
    details=dict(order=[],draws=[],features_sha256=digest([(k,features[k]) for k in macros]))
    if not stochastic:
        out=sorted(macros,key=lambda k:(-score(features[k],policy),macros.index(k)))
        details['order']=out;return out,details,{}
    pool=list(macros);out=[];grads={}
    while pool:
        probs=probabilities(pool,features,policy);draw=rng.random();cumulative=0;chosen=len(pool)-1
        for i,p in enumerate(probs):
            cumulative+=p
            if draw<cumulative:chosen=i;break
        key=pool[chosen];grads[key]=[features[key][j]/FEATURE_SCALE-sum(p*features[k][j]/FEATURE_SCALE for p,k in zip(probs,pool)) for j in range(len(FEATURES))]
        out.append(key);details['draws'].append(draw);pool.pop(chosen)
    details['order']=out;return out,details,grads
def update(policy,result,rate=0.2):
    # Policy stays frozen throughout a complete/open search. No supplied path.
    covered=len(result['placements']);reward=int(result['status']=='finite_exact_proof_tiling')+0.1*covered/result['proof_cells']-min(1,result['base_attempts']/result['limits']['base_attempts'])
    gradients=result['executed_score_gradients'];count=max(1,len(gradients))
    mean=[sum(g[j] for g in gradients)/count for j in range(len(FEATURES))]
    weights=[max(-2*WEIGHT_SCALE,min(2*WEIGHT_SCALE,math.floor(w+rate*WEIGHT_SCALE*reward*g+0.5))) for w,g in zip(policy['weights'],mean)]
    return dict(policy,weights=weights),dict(reward=reward,mean_gradient=mean,rate=rate,events=len(gradients),before_sha256=digest(policy),after_weights=weights)

def point_search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True,policy=None,stochastic=False,seed=0):
    validate(policy,library,stochastic)
    rng=random.Random(seed);gradients=[];policy_work=collections.Counter(orders=0,feature_evaluations=0,sampled_draws=0);ranking_seconds=0
    began=time.perf_counter();model=H.Model(c,n,library,marked);build=time.perf_counter()-began
    state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began-build
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0,macro_attempts=0);found=None;best=[]
    peaks=[len(graph.domains),len(graph.edges),sum(map(len,graph.domains.values()))]
    def visit(s,g):
        nonlocal found,best,ranking_seconds
        stats['nodes']+=1;t=dict(kind='cutoff',selected=list(s.order))
        if time.perf_counter()-began>seconds:t['cutoff']='wall_entry';return None,t
        kind,p,choices=g.decision(s);t.update(kind=kind,point=p,graph_sha256=digest(g.fingerprint()))
        peaks[1]=max(peaks[1],len(g.edges));peaks[2]=max(peaks[2],sum(map(len,g.domains.values())))
        if kind=='dead':return False,t
        if len(model.expansion(s.order))>len(model.expansion(best)):best=list(s.order)
        if kind=='empty':found=list(s.order);return True,t
        stats['forced' if kind=='forced' else 'branches']+=1;t['children']=[]
        rank_start=time.perf_counter();base_order=sorted(choices,key=model.ordering)
        macros=[cid for cid in base_order if len(model.descriptions[cid]['members'])>1]
        filled={p[0]//2 for p,v in s.totals.items() if p[1]==0 and v==12}
        features={cid:feature_vector(c,n,model.descriptions[cid]['members'],filled) for cid in macros} if policy else {}
        arranged,details,grads=ordered(macros,features,policy,stochastic,rng)
        if details is not None:
            t['policy']=details;policy_work['orders']+=1;policy_work['feature_evaluations']+=len(macros);policy_work['sampled_draws']+=len(details['draws'])
        ranked=arranged+[cid for cid in base_order if cid not in set(macros)];ranking_seconds+=time.perf_counter()-rank_start
        for cid in ranked:
            cost=len(model.descriptions[cid]['members'])
            if stats['base_attempts']+cost>attempt_limit:t['cutoff']='attempts_before_candidate';return None,t
            if time.perf_counter()-began>seconds:t['cutoff']='wall_before_candidate';return None,t
            if stochastic and cid in grads:gradients.append(grads[cid])
            stats['base_attempts']+=cost;stats['tile_attempts']+=1;stats['macro_attempts']+=int(cost>1)
            child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(cid)))
            ok,sub=visit(child,cg);t['children'].append(dict(candidate=cid,tree=sub))
            if ok is not False:return ok,t
            stats['backtracks']+=1
        return False,t
    ok,tree=visit(state,graph);selected=found if found is not None else best;placements=model.expansion(selected)
    if not S.point_check(model.base,placements,ok is True):raise ValueError('motifs expand to the original exact point model')
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,
      selected=selected,placements=placements,tile_generations=[1]*len(selected),search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,
      build_seconds=build,graph_seconds=graph_seconds,seconds=time.perf_counter()-began,base_universe=len(model.base.cache),candidate_universe=len(model.cache),motif_instances=len(model.instances),
      support_certificate=model.support_certificate,library_sha256=digest(library),peak_frontier_points=peaks[0],peak_candidate_nodes=peaks[1],peak_incidences=peaks[2],metrics=dict(model.metrics),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    r.update(proof_cells=n,policy=policy,policy_sha256=digest(policy),stochastic=stochastic,seed=seed,policy_work=dict(policy_work),ranking_seconds=ranking_seconds,executed_score_gradients=gradients)
    if ok:
        start=time.perf_counter();r['decoded']=S.decode(c,placements,n);r['decode_seconds']=time.perf_counter()-start
        r['solution_motifs']=[dict(candidate=cid,**model.descriptions[cid]) for cid in selected if model.descriptions[cid]['item'] is not None]
    return r

def csp_search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True,policy=None,stochastic=False,seed=0):
    """Same resource constraints and learned motifs offered to classical AC/MRV.

    Complete original variable domains are retained. A motif simultaneously
    assigns its original constituent values; every ordinary value is still tried
    after failed proposals. Motifs do not change classical support semantics.
    """
    validate(policy,library,stochastic)
    rng=random.Random(seed);gradients=[];policy_work=collections.Counter(orders=0,feature_evaluations=0,sampled_draws=0);ranking_seconds=0
    began=time.perf_counter();binary=M.Binary(c,n);certificate=T.supports(c) if marked else None
    if certificate is not None:
        bounds=certificate['bound']
        for i,row in enumerate(binary.keys):
            for j,key in enumerate(row):
                slot,rid,refs=key;r=c['rules'][rid]
                contacts=((slot,r['output']),)+tuple(zip(refs,r['inputs']))
                if any(bounds[f] is None or bounds[f]>p+1 for p,f in contacts):binary.initial[i]&=~(1<<j)
    motifs=H.instances(c,n,library);index={key:(i,j) for i,row in enumerate(binary.keys) for j,key in enumerate(row)}
    values=[tuple(index[key] for key in item['members']) for item in motifs];by_slot=collections.defaultdict(list)
    for mid,assignment in enumerate(values):
        for i,j in assignment:by_slot[i].append(mid)
    build=time.perf_counter()-began
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,macro_attempts=0,support_tests=0,removed_values=0,revisions=0);found=None;used=[]
    def order(mid):
        item=motifs[mid];return (-int(any(k[0]==n-1 for k in item['members'])),-len(item['members']),mid)
    def visit(incoming,path):
        nonlocal found,used,ranking_seconds
        stats['nodes']+=1;ds=list(incoming);tree=dict(kind='ac',incoming=[hex(x) for x in incoming],revisions=[],children=[])
        if not all(ds):tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
        queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        while queue:
            if time.perf_counter()-began>seconds:tree.update(cutoff='wall_ac',domains=[hex(x) for x in ds]);return None,tree
            i,j=queue.popleft();removed=0
            for k in M.indices(ds[i]):
                stats['support_tests']+=1
                if not binary.support(i,k,j)&ds[j]:removed|=1<<k
            stats['revisions']+=1;stats['removed_values']+=M.count(removed);tree['revisions'].append((i,j,hex(removed)));ds[i]&=~removed
            if not ds[i]:tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
            if removed:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        tree['domains']=[hex(x) for x in ds]
        if all(M.count(x)==1 for x in ds):
            found=[binary.keys[i][next(M.indices(mask))] for i,mask in enumerate(ds)];used=list(path);tree['kind']='empty';return True,tree
        i=min((i for i in range(n) if M.count(ds[i])>1),key=lambda i:(M.count(ds[i]),i));tree.update(kind='branch',slot=i);stats['branches']+=1
        offered=sorted((mid for mid in by_slot[i] if all(ds[j]&(1<<k) for j,k in values[mid])),key=order)
        rank_start=time.perf_counter();filled={j for j,mask in enumerate(ds) if M.count(mask)==1}
        features={mid:feature_vector(c,n,motifs[mid]['members'],filled) for mid in offered} if policy else {}
        arranged,details,grads=ordered(offered,features,policy,stochastic,rng)
        if details is not None:
            tree['policy']=details;policy_work['orders']+=1;policy_work['feature_evaluations']+=len(offered);policy_work['sampled_draws']+=len(details['draws'])
        ranking_seconds+=time.perf_counter()-rank_start
        choices=[('motif',mid,values[mid]) for mid in arranged]+[('base',k,((i,k),)) for k in M.indices(ds[i])]
        for kind,choice,assignment in choices:
            cost=len(assignment)
            if stats['base_attempts']+cost>attempt_limit:tree['cutoff']='attempts_before_candidate';return None,tree
            if time.perf_counter()-began>seconds:tree['cutoff']='wall_before_candidate';return None,tree
            if stochastic and kind=='motif':gradients.append(grads[choice])
            stats['base_attempts']+=cost;stats['macro_attempts']+=int(kind=='motif');child=list(ds)
            for j,k in assignment:child[j]=1<<k
            okay,sub=visit(child,path+([choice] if kind=='motif' else []));tree['children'].append(dict(mode=kind,choice=choice,tree=sub))
            if okay is not False:return okay,tree
            stats['backtracks']+=1
        return False,tree
    ok,tree=visit(binary.initial,[])
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,support_certificate=certificate,
      placements=found or [],search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,build_seconds=build,seconds=time.perf_counter()-began,
      base_universe=len(binary.model.cache),candidate_universe=len(binary.model.cache),motif_instances=len(motifs),library_sha256=digest(library),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    r.update(proof_cells=n,policy=policy,policy_sha256=digest(policy),stochastic=stochastic,seed=seed,policy_work=dict(policy_work),ranking_seconds=ranking_seconds,executed_score_gradients=gradients)
    if ok:
        if not S.point_check(binary.model,found,True):raise ValueError('classical witness expands to exact original points')
        start=time.perf_counter();r['decoded']=S.decode(c,found,n);r['decode_seconds']=time.perf_counter()-start;r['used_motif_proposals']=used
    return r
