"""Independent policy features, sampled permutations, all point/AC prefixes and updates.

No policy, miner, model, solver or producer is imported. Frozen independent
inventory/cluster auditors supply exact primitive semantics and complete joins.
Greedy ranking uses integer dot products. Float tolerances apply only to learning
probabilities/gradients, never formula equality, capacity or proof acceptance.
"""
import collections,hashlib,json,math,random,time
from fractions import Fraction
from pathlib import Path
import audit_induction_clusters as H
import audit_induction_proofs as I
import audit_semantic_proofs as A
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding
Points=H.Points
instances=H.instances
sha=H.sha
NAMES=('additional_cells','goal_cell','mean_slot','span','internal_premises',
       'resolved_external_premises','mean_premise_gap','conditional_steps',
       'generalization_steps','induction_steps','progress_times_size')
def features(c,n,members,filled):
    locations=[m[0] for m in members];links=[(m[0],j) for m in members for j in m[2]]
    inside=sum(j in locations for _,j in links);outside=[j for _,j in links if j not in locations]
    kinds=[]
    for _,rid,_ in members:
        p=c['rules'][rid]['recipe'];kinds.append(p['witness']['rule'] if p['kind']=='primitive' else p.get('operation','copy'))
    counts=collections.Counter(kinds);width=max(locations)-min(locations)+1
    rational=(Fraction(len(locations)-1,2),Fraction(n-1 in locations),Fraction(sum(locations),len(locations)*n),
              Fraction(width,n),Fraction(inside,len(links) or 1),Fraction(sum(j in filled for j in outside),len(outside) or 1),
              Fraction(sum(a-b for a,b in links),(len(links) or 1)*n),Fraction(sum(v for k,v in counts.items() if k.startswith('conditional-')),len(locations)),
              Fraction(counts['generalize'],len(locations)),Fraction(counts['induction'],len(locations)),Fraction(len(filled)*(len(locations)-1),2*n))
    return tuple(math.floor(1024*x) for x in rational)
def close_vectors(a,b):
    A.need(len(a)==len(b) and all(abs(x-y)<1e-12 for x,y in zip(a,b)),'independent numerical score gradient')
def header(r,library):
    policy=r['policy'];A.need(r['policy_sha256']==sha(policy),'frozen policy binding')
    A.need(type(r['stochastic']) is bool and type(r['seed']) is int,'declared policy mode and RNG seed')
    if policy is None:A.need(not r['stochastic'],'no stochastic ordering without policy')
    else:
        A.need(policy['version']=='induction-cluster-policy-1' and policy['initialization']=='zero' and policy['feature_names']==NAMES and policy['feature_scale']==1024 and policy['weight_scale']==1000000,'declared learned features and integer scales')
        A.need(len(policy['weights'])==len(NAMES) and all(type(w) is int and abs(w)<=2000000 for w in policy['weights']) and policy['library_sha256']==sha(library),'frozen bounded integer weights and source library')
    return random.Random(r['seed']),dict(orders=0,feature_evaluations=0,sampled_draws=0),[]
def arrange(c,n,macros,members,filled,tree,r,rng,work):
    if r['policy'] is None:A.need('policy' not in tree,'fixed control has no hidden ordering');return list(macros),{}
    f={k:features(c,n,members[k],filled) for k in macros};w=r['policy']['weights'];dot=lambda k:sum(x*y for x,y in zip(f[k],w))
    details=tree['policy'];A.need(set(details)=={'order','draws','features_sha256'} and details['features_sha256']==sha([(k,f[k]) for k in macros]),'every proposal feature from actual parent state')
    work['orders']+=1;work['feature_evaluations']+=len(macros);work['sampled_draws']+=len(details['draws']);grads={}
    if not r['stochastic']:
        expected=sorted(macros,key=lambda k:(-dot(k),macros.index(k)));A.need(details['order']==tuple(expected) and details['draws']==(),'exact greedy complete ordering');return expected,grads
    pool=list(macros);out=[];A.need(len(details['draws'])==len(pool),'one recorded draw per sampled proposal')
    for draw in details['draws']:
        A.need(type(draw) is float and draw==rng.random(),'actual seeded sampling sequence');logits=[dot(k)/1024000000 for k in pool]
        weights=[math.exp(x-max(logits)) for x in logits];p=[x/sum(weights) for x in weights];cumulative=0;selected=len(pool)-1
        for i,q in enumerate(p):
            cumulative+=q
            if draw<cumulative:selected=i;break
        k=pool[selected];grads[k]=[f[k][j]/1024-sum(q*f[m][j]/1024 for q,m in zip(p,pool)) for j in range(len(NAMES))];out.append(k);pool.pop(selected)
    A.need(details['order']==tuple(out),'full sampled permutation from exact probabilities');return out,grads
def finish_policy(r,work,gradients,n):
    A.need(r['proof_cells']==n and r['policy_work']==work and len(r['executed_score_gradients'])==len(gradients),'all policy evaluations and only executed score events')
    for actual,wanted in zip(r['executed_score_gradients'],gradients):close_vectors(actual,wanted)
    A.need(r['ranking_seconds']>=0,'ranking costs reported')
def update(policy,r,record):
    A.need(record['rate']==0.2 and record['before_sha256']==sha(policy),'declared fresh episode update')
    reward=(1 if r['status']=='finite_exact_proof_tiling' else 0)+len(r['placements'])/(10*r['proof_cells'])-min(1,r['base_attempts']/r['limits']['base_attempts'])
    gradients=r['executed_score_gradients'];mean=[sum(g[j] for g in gradients)/max(1,len(gradients)) for j in range(len(NAMES))]
    A.need(abs(record['reward']-reward)<1e-12 and record['events']==len(gradients),'reward charges expanded work and satisfied base obligations');close_vectors(record['mean_gradient'],mean)
    weights=[max(-2000000,min(2000000,math.floor(w+200000*reward*g+0.5))) for w,g in zip(policy['weights'],mean)]
    A.need(record['after_weights']==tuple(weights),'every quantized policy parameter update');return dict(policy,weights=tuple(weights))

def point_run(c,n,r,library):
    points=Points(c,n,library,r['marked']);A.need(r['base_universe']==len(points.base) and r['candidate_universe']==len(points.tiles) and r['motif_instances']==len(points.instances) and r['library_sha256']==sha(library),'whole primitive and motif inventory')
    if r['marked']:I.support_certificate(c,r['support_certificate'])
    else:A.need(r['support_certificate'] is None,'unmarked control')
    rng,policy_work,gradients=header(r,library);initial=points.domains([]);stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0,macro_attempts=0);best=[];leaf=None;cuts=0
    peaks=[n,len(set().union(*initial.values())),sum(map(len,initial.values()))]
    def visit(tree,ids):
        nonlocal best,leaf,cuts
        stats['nodes']+=1;A.need(tree['selected']==tuple(ids),'actual motif prefix');ds=points.domains(ids)
        if tree['kind']=='cutoff':A.need(set(tree)=={'kind','selected','cutoff'} and tree['cutoff']=='wall_entry' and r['seconds']>=r['limits']['seconds'],'entry wall');cuts+=1;return None
        kind,p,choices=points.decision(ds);A.need(tree['kind']==kind and tree['point']==p,'global dead/forced/generation order')
        candidates=set().union(*ds.values()) if ds else set();edges={cid:tuple(sorted(p for p,values in ds.items() if cid in values)) for cid in candidates}
        A.need(tree['graph_sha256']==sha((tuple(sorted((p,tuple(sorted(v))) for p,v in ds.items())),tuple(sorted(edges.items())))),'every complete motif graph')
        peaks[1]=max(peaks[1],len(candidates));peaks[2]=max(peaks[2],sum(map(len,ds.values())))
        if kind=='dead':A.need('children' not in tree and 'cutoff' not in tree,'closed dead leaf');return False
        if len(points.expand(ids))>len(points.expand(best)):best=list(ids)
        if kind=='empty':A.need('children' not in tree and 'cutoff' not in tree,'closed solution leaf');leaf=list(ids);return True
        stats['forced' if kind=='forced' else 'branches']+=1
        macros=[cid for cid in choices if len(points.tiles[cid]['members'])>1];filled={k[0] for cid in ids for k in points.tiles[cid]['members']}
        arranged,grads=arrange(c,n,macros,{cid:points.tiles[cid]['members'] for cid in macros},filled,tree,r,rng,policy_work)
        choices=arranged+[cid for cid in choices if cid not in set(macros)];children=tree['children'];A.need(tuple(x['candidate'] for x in children)==tuple(choices[:len(children)]),'every executed ordering prefix')
        for j,child in enumerate(children):
            cid=child['candidate']
            if r['stochastic'] and cid in grads:gradients.append(grads[cid])
            cost=len(points.tiles[cid]['members']);stats['base_attempts']+=cost;stats['tile_attempts']+=1;stats['macro_attempts']+=int(cost>1)
            ok=visit(child['tree'],ids+[cid])
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in tree,'stop at open/successful child');return ok
            stats['backtracks']+=1
        if 'cutoff' in tree:
            A.need(len(children)<len(choices),'open unexecuted suffix');reason=tree['cutoff'];A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'declared cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']+len(points.tiles[choices[len(children)]]['members'])>r['limits']['base_attempts'],'actual budget');cuts+=1;return None
        A.need(len(children)==len(choices),'all closed branches covered');return False
    ok=visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],[])
    expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope';A.need(r['status']==expected and cuts==int(ok is None),'tri-state result')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'complete/open distinction')
    A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'all expanded attempts and backtracks')
    selected=leaf if ok else best;A.need(r['selected']==tuple(selected) and r['placements']==points.expand(selected),'exact motif expansion');A.need(r['tile_generations']==(1,)*len(selected),'generation-zero roots')
    A.need((r['peak_frontier_points'],r['peak_candidate_nodes'],r['peak_incidences'])==tuple(peaks),'complete graph peaks');A.domains(points.base,n,c['target_id'],r['placements'])
    if ok:
        expected=tuple(dict(candidate=cid,members=points.tiles[cid]['members'],item=points.tiles[cid]['item']) for cid in selected if points.tiles[cid]['item'])
        A.need(r['solution_motifs']==freeze(list(expected)),'only actually placed motifs');proof=A.check_decoded(c,n,r)
    else:A.need('decoded' not in r,'no proof at cutoff');proof=None
    finish_policy(r,policy_work,gradients,n)
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True,proof=proof)


def csp_run(c,n,r,library):
    points=I.Points(c,n,'support' if r['marked'] else 'none');universe=points.base;keys=[sorted(k for k in universe if k[0]==i) for i in range(n)];maps=[[universe[k] for k in row] for row in keys]
    full=[(1<<len(row))-1 for row in keys];index=[]
    for row in maps:
        present={};values={}
        for k,m in enumerate(row):
            for p,v in m.items():present[p]=present.get(p,0)|(1<<k);values[p,v]=values.get((p,v),0)|(1<<k)
        index.append((present,values))
    def support(i,k,j):
        mask=full[j];present,values=index[j]
        for p,v in maps[i][k].items():mask&=(full[j]^present.get(p,0))|values.get((p,v),0)
        return mask
    if r['marked']:I.support_certificate(c,r['support_certificate'])
    else:A.need(r['support_certificate'] is None,'unmarked classical control')
    initial_candidates=set().union(*points.domains([]).values());cid={t['members'][0]:i for i,t in enumerate(points.tiles)}
    initial=[sum(1<<j for j,k in enumerate(row) if cid[k] in initial_candidates) for row in keys]
    motifs=instances(c,n,library);lookup={key:(i,j) for i,row in enumerate(keys) for j,key in enumerate(row)};assignments=[tuple(lookup[k] for k in item['members']) for item in motifs]
    A.need(r['motif_instances']==len(motifs) and r['base_universe']==len(universe) and r['candidate_universe']==len(universe) and r['library_sha256']==sha(library),'same complete classical envelope and motifs')
    rng,policy_work,gradients=header(r,library);stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,macro_attempts=0,support_tests=0,removed_values=0,revisions=0);leaf=None;used=None;cuts=0
    def visit(t,incoming,path):
        nonlocal leaf,used,cuts
        stats['nodes']+=1;A.need(t['incoming']==tuple(hex(x) for x in incoming),'exact incoming classical domains');ds=list(incoming)
        queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        if not all(ds):A.need(t['kind']=='dead' and not t['revisions'] and not t['children'] and 'cutoff' not in t and t['domains']==tuple(hex(x) for x in ds),'initial dead domain');return False
        for revision,(i,j,removed) in enumerate(t['revisions']):
            A.need(queue and queue.popleft()==(i,j),'actual AC queue');expected=0
            for k in I.B.bits(ds[i]):
                stats['support_tests']+=1
                if not support(i,k,j)&ds[j]:expected|=1<<k
            A.need(removed==hex(expected),'every independently reconstructed support deletion');stats['revisions']+=1;stats['removed_values']+=I.B.count(expected);ds[i]&=~expected
            if not ds[i]:A.need(revision==len(t['revisions'])-1 and not t['children'] and 'cutoff' not in t and t['kind']=='dead' and t['domains']==tuple(hex(x) for x in ds),'dead after propagation');return False
            if expected:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        A.need(t['domains']==tuple(hex(x) for x in ds),'complete exported classical domains')
        if queue:A.need(t['kind']=='ac' and not t['children'] and t['cutoff']=='wall_ac' and r['seconds']>=r['limits']['seconds'],'only wall may leave AC queue open');cuts+=1;return None
        if all(I.B.count(x)==1 for x in ds):A.need(t['kind']=='empty' and not t['children'] and 'cutoff' not in t,'classical singleton witness');leaf=tuple(keys[i][next(I.B.bits(mask))] for i,mask in enumerate(ds));used=tuple(path);return True
        i=min((i for i in range(n) if I.B.count(ds[i])>1),key=lambda i:(I.B.count(ds[i]),i));A.need(t['kind']=='branch' and t['slot']==i,'classical MRV');stats['branches']+=1
        offered=[mid for mid,ass in enumerate(assignments) if any(j==i for j,k in ass) and all(ds[j]&(1<<k) for j,k in ass)]
        offered.sort(key=lambda mid:(-int(any(k[0]==n-1 for k in motifs[mid]['members'])),-len(motifs[mid]['members']),mid))
        filled={j for j,mask in enumerate(ds) if I.B.count(mask)==1}
        offered,grads=arrange(c,n,offered,{mid:motifs[mid]['members'] for mid in offered},filled,t,r,rng,policy_work)
        choices=[('motif',mid,assignments[mid]) for mid in offered]+[('base',k,((i,k),)) for k in I.B.bits(ds[i])];children=t['children']
        A.need(tuple((x['mode'],x['choice']) for x in children)==tuple((a,b) for a,b,ass in choices[:len(children)]),'complete macro plus base fallback ordering prefix')
        for j,child in enumerate(children):
            mode,choice,ass=choices[j]
            if r['stochastic'] and mode=='motif':gradients.append(grads[choice])
            stats['base_attempts']+=len(ass);stats['macro_attempts']+=int(mode=='motif');following=list(ds)
            for p,v in ass:following[p]=1<<v
            ok=visit(child['tree'],following,path+([choice] if mode=='motif' else []))
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'stop at open/successful child');return ok
            stats['backtracks']+=1
        if 'cutoff' in t:
            A.need(len(children)<len(choices),'remaining classical suffix');reason=t['cutoff'];A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'classical cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']+len(choices[len(children)][2])>r['limits']['base_attempts'],'actual classical budget');cuts+=1;return None
        A.need(len(children)==len(choices),'closed classical search covers all choices');return False
    ok=visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],initial,[])
    expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope';A.need(r['status']==expected and cuts==int(ok is None),'classical tri-state outcome')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'classical complete/open distinction');A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'all classical work')
    if ok:A.need(r['placements']==leaf and r['used_motif_proposals']==used,'actual classical witness and proposal path');proof=A.check_decoded(c,n,r)
    else:A.need(r['placements']==() and 'decoded' not in r,'no classical witness at cutoff');proof=None
    finish_policy(r,policy_work,gradients,n)
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True,proof=proof)

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
MEASURED_SOURCES=H.MEASURED_SOURCES+('induction_cluster_policy.py','audit_induction_cluster_policy.py','run_induction_cluster_policy.py','test_induction_cluster_policy.py','run_induction_cluster_policy_tests.py')
def audit(path=DOCS/'induction-cluster-policy-001.json'):
    path=Path(path);raw=json.loads(path.read_text());d=freeze(raw);began=time.perf_counter()
    A.need(set(d['sources'])==set(MEASURED_SOURCES),'entire frozen measured dependency set')
    for name,pin in d['sources'].items():A.need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'measured source '+name)
    lanes=('gcts-fixed','gcts-rl','csp-fixed','csp-rl')
    expected=dict(seconds=20,donor_seconds=20,base_attempts=50000,training_seconds=3,training_attempts=2000,episodes=20,seed_base=36100,rate=0.2,native_steps=100000000,replicas=2,lanes=lanes,marked=True,motif_sizes=(2,3))
    A.need(d['configuration']==expected and d['initial_library']==() and d['imported_policy'] is None,'fixed cold learning experiment')
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];A.need(d['program_sha256']==sha(code),'fixed complete checker program')
    external=I.external_cases();donors={};source_reports=[]
    def bound(row):
        p=row['problem'];c=row['catalog'];A.need(p['id'] in external and {k:p[k] for k in external[p['id']]}==external[p['id']],'nominated external statement and envelope')
        A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'] and c['configuration']['enable_induction']==p['enable_induction'] and sha(c)==row['catalog_sha256'],'complete grammar binding')
        return I.inventory(c)
    A.need(tuple(x['problem']['id'] for x in d['donors'])==('ind-add-left-zero','ind-add-left-one'),'fresh source statements')
    for desc in raw['donors']:
        pid=desc['problem']['id'];A.need(desc['file']=='induction-cluster-policy-donors-001/'+pid+'.json.gz','lossless source shard')
        row=freeze(I.load_case(desc));language=bound(row);r=row['run']['result']
        A.need(r['limits']==dict(seconds=20,base_attempts=50000) and r['marking']=='support' and row['run']['catalog_sha256']==row['catalog_sha256'],'cold exact source search')
        report=I.point_run(row['catalog'],row['problem']['length'],r);A.need(report['exact_solution'] and row['run']['native']['status']=='accepted','checked newly discovered source')
        native_binding(code,json.loads(A.packed(r['decoded']['request'])),json.loads(A.packed(row['run']['native'])))
        donors[pid]=row;source_reports.append(dict(id=pid,inventory=language,report=report));print('audited fresh source',pid,flush=True)
    library=H.provenance(list(donors.values()),d['library']);A.need(d['library_sha256']==sha(d['library']),'entire fresh learned library')
    policy=d['initial_policy'];A.need(policy['weights']==(0,)*len(NAMES) and len(d['episodes'])==20,'zero initialization and all training episodes')
    reports=[];names=('ind-add-left-zero','ind-add-left-one')
    for i,desc in enumerate(raw['episodes']):
        pid=names[i%2];A.need(desc['episode']==i and desc['problem_id']==pid and desc['file']==f'induction-cluster-policy-training-001/episode-{i:02d}.json.gz','only donor statements in training, fixed order')
        row=freeze(I.load_case(desc));donor=donors[pid];r=row['run']['result']
        A.need(row['episode']==i and row['problem']==donor['problem'] and row['problem_id']==pid and row['catalog_sha256']==donor['catalog_sha256'] and r['policy']==policy and r['stochastic'] is True and r['seed']==36100+i and r['limits']==dict(seconds=3,base_attempts=2000),'frozen within-episode policy and fresh seeded source trial')
        report=point_run(donor['catalog'],donor['problem']['length'],r,d['library'])
        if report['exact_solution']:
            A.need(row['run']['native']['status']=='accepted','native check before positive reward update')
            native_binding(code,json.loads(A.packed(r['decoded']['request'])),json.loads(A.packed(row['run']['native'])))
        else:A.need('native' not in row['run'],'no proof acceptance for an open or exhausted source trial')
        policy=update(policy,r,row['run']['update']);reports.append(dict(episode=i,problem_id=pid,report=report,reward=row['run']['update']['reward']))
        print('audited learning',i,r['status'],r['base_attempts'],flush=True)
    A.need(d['policy']==policy and d['policy_sha256']==sha(policy),'complete fresh parameter history binds evaluation')
    case_reports=[];ids=('ind-mul-left-zero','ind-add-left-successor','ind-no-schema','ind-too-short','ind-wrong-target')
    A.need(tuple(x['problem']['id'] for x in d['cases'])==ids,'all held-out positive and negative-envelope cases')
    for i,desc in enumerate(raw['cases']):
        pid=ids[i];A.need(desc['file']=='induction-cluster-policy-cases-001/'+pid+'.json.gz','lossless recipient shard')
        row=freeze(I.load_case(desc));language=bound(row);p=row['problem'];order=[]
        for replica in range(2):
            shift=(i+replica)%4;order.extend((replica,lane) for lane in lanes[shift:]+lanes[:shift])
        A.need(tuple((run['replica'],run['lane']) for run in row['runs'])==tuple(order),'all matched rotated recipient requests')
        runs=[]
        for run in row['runs']:
            r=run['result'];lane=run['lane'];wanted=policy if lane.endswith('rl') else None
            A.need(run['catalog_sha256']==row['catalog_sha256'] and r['policy']==wanted and r['stochastic'] is False and r['seed']==0 and r['marked'] is True and r['limits']==dict(seconds=20,base_attempts=50000),'identical held-out constraints and frozen shared policy')
            report=(csp_run if lane.startswith('csp') else point_run)(row['catalog'],p['length'],r,d['library'])
            if report['exact_solution']:
                A.need(run['native']['status']=='accepted','complete native recipient acceptance')
                native_binding(code,json.loads(A.packed(r['decoded']['request'])),json.loads(A.packed(run['native'])))
            else:A.need('native' not in run,'no accepted proof claimed at cutoff or exhaustion')
            runs.append(dict(lane=lane,replica=run['replica'],report=report));print('audited recipient',pid,lane,run['replica'],r['status'],flush=True)
        case_reports.append(dict(id=pid,inventory=language,runs=runs))
    result=dict(status='passed',seconds=time.perf_counter()-began,donors=source_reports,library=library,learning=reports,cases=case_reports,
      scope='Every independently rebuilt grammar, source fragment and complete recipient instance; every point graph/global decision and classical AC deletion; all seeded sampling draws, integer feature bindings, executed gradients, rewards and quantized parameter updates; all open/closed prefixes, expanded attempts, exact proof expansions and native bindings. No imported solver, policy or producer. Numerical tolerance applies only to gradients, never integer evaluation ranks or proof semantics.')
    raw['independent_audit']=result;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return result
if __name__=='__main__':print('passed',audit()['seconds'])
