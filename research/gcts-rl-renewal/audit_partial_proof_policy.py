"""Independent replay of every executed node, including the open DFS suffix.

No search, graph, policy, miner or catalog-generator imports. Complete domains
and policy draws come from the frozen independent auditors, not the producer.
"""
import collections,hashlib,json,math,time
from pathlib import Path
import audit_proof_policy as B
import audit_proof_clusters as G
import audit_semantic_proofs as A
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'

def replay(c,n,r,library,weights=None,start_state=None,stochastic=False,points=None):
    points=points or G.Points(c,n)
    # The old metadata audit is intentionally called without a claimed result.
    # The recursion below independently establishes the actual tri-state result.
    shadow=dict(r,status='unknown_search_budget',search_tree=None)
    G.run_audit(c,n,shadow,library,points)
    items,complete=G.index(c,n,library,r['limits']['index_instances'])
    if weights is None:
        A.need(r['policy_weights'] is None and not r['policy_events'],'plain/prior has no policy');offers=[]
    else:offers=B.policy_events(c,n,r,library,points,weights,start_state,stochastic)
    stats=collections.Counter();cursor=0;best=[];solution=[];solution_transactions=[];open_nodes=0
    def visit(t,order,transactions):
        nonlocal cursor,best,solution,solution_transactions,open_nodes
        stats['nodes']+=1;ds=points.domains(order);kind,p,keys=A.decision(ds)
        A.need(t['depth']==len(order) and t['viable']==(kind!='dead'),'literal viable occupancy at every executed node')
        peak=len(order) if kind!='dead' else -1
        if t['kind']=='cutoff':
            A.need(t==dict(kind='cutoff',reason='entry_wall',depth=len(order),viable=kind!='dead'),'open entry has no inferred decision or descendants');open_nodes+=1;return None,peak
        A.need(t['kind']==kind and 'reason' not in t,'complete observed global decision')
        if p is not None:A.need(t['point']==(2*p,0),'earliest generation and degree tie')
        if kind=='dead':A.need('cutoff' not in t,'a dead node is closed');return False,peak
        if len(order)>len(best):best=list(order)
        if kind=='empty':solution=list(order);solution_transactions=transactions;return True,peak
        stats['forced' if kind=='forced' else 'branches']+=1;offered=[]
        if kind=='branch' and library:
            if weights is not None:
                A.need(t.get('policy_event')==cursor and cursor<len(r['policy_events']),'literal DFS event identity');event=r['policy_events'][cursor]
                A.need(event['order']==tuple(order) and event['point']==(2*p,0),'actual event context');offered=offers[cursor];stats['compatible_proposals']+=event['pool_count'];cursor+=1
            else:offered,count=points.offered(items,order,p,r['limits']['proposal_limit']);stats['compatible_proposals']+=count
        else:A.need('policy_event' not in t,'no event outside a genuine proposal branch')
        trials=t['proposals'];A.need(tuple(x['item'] for x in trials)==tuple(offered[:len(trials)]),'actually reached preference prefix')
        for j,trial in enumerate(trials):
            trace=trial['trace'];current=points.transaction(order,trial['item'],trace);steps=trace['steps'];stats['proposal_trials']+=1;stats['base_attempts']+=len(steps);stats['validation_placements']+=len(steps);stats['constituent_branch_steps']+=sum(x['kind']=='branch' for x in steps);stats['constituent_forced_steps']+=sum(x['kind']=='forced' for x in steps)
            if trace['status']=='unknown_transaction_budget':
                A.need(j==len(trials)-1 and not t['children'] and 'tree' not in trial and 'cutoff' not in t,'stop immediately on interrupted transaction');open_nodes+=1;return None,peak
            if trace['status']!='accepted_cluster':A.need('tree' not in trial,'rejected transaction has no committed child');stats['proposal_rejections']+=1;continue
            stats['accepted_proposal_trials']+=1;transaction=dict(trial['item'],steps=steps);okay,high=visit(trial['tree'],current,transactions+[transaction]);peak=max(peak,len(current),high)
            if okay is not False:
                A.need(j==len(trials)-1 and not t['children'] and 'cutoff' not in t,'stop on successful or open child');return okay,peak
            stats['backtracks']+=1
        A.need(len(trials)==len(offered),'all offered proposals tried before ordinary fallback')
        children=t['children'];A.need(tuple(x['key'] for x in children)==tuple(keys[:len(children)]),'entire original base order retained')
        for j,child in enumerate(children):
            stats['base_attempts']+=1;stats['singleton_attempts']+=1;okay,high=visit(child['tree'],order+[child['key']],transactions);peak=max(peak,high)
            if okay is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'open/successful base child is last');return okay,peak
            stats['backtracks']+=1
        if 'cutoff' in t:
            A.need(t['cutoff']=='base_before_placement' and len(children)<len(keys),'budget cuts off before a remaining base alternative');open_nodes+=1;return None,peak
        A.need(len(children)==len(keys),'closed node exhausts every base alternative');return False,peak
    complete_tree=r['search_tree'];partial=r['partial_tree'];A.need((complete_tree is None)!=(partial is None),'one complete or partial tree, never both')
    okay,peak=visit(complete_tree if complete_tree is not None else partial,[],[])
    expected='finite_exact_proof_tiling' if okay is True else 'exhausted_finite_proof_envelope' if okay is False else 'unknown_search_budget'
    A.need(r['status']==expected and (complete_tree is None)==(okay is None),'literal tri-state DFS result')
    A.need(open_nodes==(1 if okay is None else 0),'exactly one open suffix; no post-cutoff work')
    A.need(r['base_attempts']<=r['limits']['base_attempts'],'declared placement budget respected')
    if okay is None:A.need(r['base_attempts']==r['limits']['base_attempts'] or r['seconds']>=r['limits']['seconds'],'recorded resource threshold reached')
    A.need(cursor==len(r['policy_events']),'every draw belongs to an actually visited node')
    A.need(stats['nodes']==r['nodes'] and stats['base_attempts']==r['base_attempts'],'all executed recursive and constituent work')
    for k in ('branches','forced','backtracks','proposal_trials','proposal_rejections','accepted_proposal_trials','singleton_attempts','validation_placements','constituent_branch_steps','constituent_forced_steps','compatible_proposals'):A.need(stats[k]==r['stats'].get(k,0),'prefix counter '+k)
    A.need(tuple(solution if okay is True else best)==r['placements'],'first deepest saved state or actual solution')
    if okay is True:
        A.need(tuple(solution_transactions)==r['solution_transactions'],'actual solution transactions');A.check_decoded(c,n,r)
    else:A.need('decoded' not in r and not r['solution_transactions'],'no certificate for an open/exhausted trace')
    return dict(status='passed',executed_nodes=stats['nodes'],base_attempts=stats['base_attempts'],open_suffixes=open_nodes,observed_viable_depth=max(0,peak),policy_events=cursor,policy_draws=sum(len(e['draws']) for e in r['policy_events']),solved=okay is True)

def local_credits(r,native,n):
    accepted=native is not None and native['status']=='accepted';out=[]
    def walk(t):
        high=t['depth'] if t['viable'] else -1
        if t['kind'] in ('dead','empty','cutoff'):return 0,t['kind']=='empty',high
        work=0;found=False;records=[]
        for j,x in enumerate(t['proposals']):
            attempts=len(x['trace']['steps']);good=False;peak=t['depth'];status=x['trace']['status']
            if status=='accepted_cluster':
                extra,good,child_peak=walk(x['tree']);attempts+=extra;peak=max(peak,t['depth']+len(x['trace']['steps']),child_peak)
            work+=attempts;found|=good;high=max(high,peak)
            if status!='unknown_transaction_budget' or attempts:records.append((j,attempts,good,peak,status))
        attempts=0;good=False;peak=t['depth']
        for child in t['children']:
            extra,success,child_peak=walk(child['tree']);attempts+=1+extra;good|=success;peak=max(peak,child_peak)
        work+=attempts;found|=good;high=max(high,peak)
        if 'policy_event' in t:
            e=r['policy_events'][t['policy_event']];j=len(t['proposals'])
            if t['children'] and len(e['draws'])>j and e['draws'][j]['action']=='defer':records.append((j,attempts,good,peak,'base_fallback'))
            for j,attempts,good,peak,status in records:
                gain=max(0,peak-t['depth']);verified=accepted and good
                out.append(dict(event=e['id'],draw=j,base_attempts=attempts,viable_gain=gain,verified_continuation=verified,action_status=status,value=int(verified)+gain/n-math.log1p(attempts)/math.log1p(r['limits']['base_attempts'])))
        return work,found,high
    work,good,high=walk(r['search_tree'] if r['search_tree'] is not None else r['partial_tree']);A.need(work==r['base_attempts'],'independent full-prefix return work');return sorted(out,key=lambda x:(x['event'],x['draw']))

def update_audit(weights,baseline,r,native,n,u,signal):
    if signal=='complete':return B.update_audit(weights,baseline,r,native,u)
    A.need(signal=='local','declared partial-progress signal');expected=local_credits(r,native,n);A.need(len(expected)==len(u['credits']),'only actually reached choices credited');gradient=[0.0]*len(B.FEATURES);b=baseline
    for actual,x in zip(u['credits'],expected):
        for k in ('event','draw','base_attempts','viable_gain','verified_continuation','action_status'):A.need(actual[k]==x[k],'literal partial credit '+k)
        B.close(actual['value'],x['value'],'observed progress return');B.close(actual['baseline_before'],b,'baseline input');a=x['value']-b;B.close(actual['advantage'],a,'actual advantage');b=.9*b+.1*x['value'];B.close(actual['baseline_after'],b,'baseline output')
        for k,g in enumerate(r['policy_events'][x['event']]['draws'][x['draw']]['gradient']):gradient[k]+=a*g
    w=[max(-6,min(6,x+.2*g)) for x,g in zip(weights,gradient)]
    for key,value in (('weights_before',weights),('weights_after',w),('gradient',gradient),('baseline_before',baseline),('baseline_after',b)):B.close(u[key],value,'partial projected update '+key)
    A.need(u['updated']==bool(expected) and u['rate']==.2,'local update gate')
    global_reward=int(native is not None and native['status']=='accepted')-math.log1p(r['base_attempts'])/math.log1p(50000)-(native.get('steps',0)/100000000/10 if native else 0);B.close(u['reward'],global_reward,'same displayed whole-episode reward');return w,b

def audit(path=DOCS/'partial-policy-001.json'):
    began=time.perf_counter();path=Path(path);raw=json.loads(path.read_text());d=freeze(raw);donors,evaluation=G.external();training=B.external_training();code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    for name,pin in raw['sources'].items():A.need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'frozen producer/gate source '+name)
    expected=dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000,seeds=(1,7,19),signals=('complete','local'),epochs=4,native_steps=100000000,rate=.2,weight_clip=6,baseline_decay=.9,online_prefix_gate=True)
    A.need(d['configuration']==expected and d['features']==B.FEATURES,'exact matched signal experiment');A.need(not d['initial_library'] and d['program_sha256']==G.sha(code),'empty library and frozen kernel')
    library,donor_reports=B.discoveries(d,code);probe=d['whole_library_native'];A.need(probe['request']['blocks']==tuple(t['definition'] for t in library) and probe['request']['theory']==freeze(donors['donor-1']['theory']) and probe['request']['target']==('imp',('bot',),('bot',)),'whole fresh library binding');native_binding(code,json.loads(A.packed(probe['request'])),json.loads(A.packed(probe['result'])));A.need(probe['result']['status']=='accepted','fresh full library machine gate')
    def catalog(row,external):
        p=row['problem'];A.need(all(p[k]==freeze(v) for k,v in external.items()),'independent external declaration');c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'] and G.sha(c)==row['catalog_sha256'],'exact base grammar binding');return c
    A.need([r['problem']['id'] for r in d['training_catalogs']]==list(training),'all independent training statements');catalogs={};inventories=[]
    for row in d['training_catalogs']:
        p=row['problem'];c=catalog(row,training[p['id']]);inventory=A.equation_inventory(c);A.need(row['inventory_gate']['report']==inventory,'online independent inventory gate');catalogs[p['id']]=(p,c);inventories.append(dict(id=p['id'],inventory=inventory));print('audited inventory',p['id'],flush=True)
    pin=lambda p:A.pin(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    A.need(not {pin(p) for p in training.values()}&{pin(p) for p in evaluation.values()},'training/evaluation external statement separation')
    order=[(seed,signal) for i,seed in enumerate((1,7,19)) for signal in (('complete','local') if i%2==0 else ('local','complete'))];A.need([(r['seed'],r['signal']) for r in d['learners']]==order,'declared alternating learner order');learners=[];learned={}
    for row in d['learners']:
        weights=[0.0]*12;baseline=0.;state=row['seed'];signal=row['signal'];A.need(row['initial_weights']==tuple(weights) and row['initial_baseline']==0,'fresh zero-start controller');ids=list(training);A.need([(e['epoch'],e['problem_id']) for e in row['episodes']]==[(epoch,id) for epoch in range(4) for id in ids[epoch:]+ids[:epoch]],'all matched training episodes');reports=[]
        for e in row['episodes']:
            p,c=catalogs[e['problem_id']];r=e['result'];A.need(e['input_random_state']==state,'continuous independent learner stream');points=G.Points(c,p['length']);report=replay(c,p['length'],r,library,weights,state,True,points);A.need(e['prefix_gate']['report']==report and e['prefix_gate']['source_sha256']==raw['sources']['audit_partial_proof_policy.py'],'online complete/partial replay before credit');native=e.get('native')
            if 'decoded' in r:
                G.hierarchy_audit(c,p['length'],r,e['hierarchy'],library);native_binding(code,json.loads(A.packed(e['hierarchy']['request'])),json.loads(A.packed(native)))
            else:A.need('hierarchy' not in e and native is None,'unknown training receives no final proof certificate')
            weights,baseline=update_audit(weights,baseline,r,native,p['length'],e['update'],signal);state=r['random_state'];reports.append(dict(problem_id=p['id'],epoch=e['epoch'],trace=report,credited_actions=len(e['update']['credits'])));points.cache.clear()
        B.close(row['weights'],weights,'final trained weights');B.close(row['baseline'],baseline,'final baseline');A.need(row['random_state']==state,'final training stream');learned[row['seed'],signal]=weights;learners.append(dict(seed=row['seed'],signal=signal,episodes=reports));print('audited learner',row['seed'],signal,flush=True)
    A.need([row['problem']['id'] for row in d['evaluation']]==list(evaluation),'all held-out evaluation statements');evaluation_reports=[]
    for i,row in enumerate(d['evaluation']):
        p=row['problem'];c=catalog(row,evaluation[p['id']]);inventory=A.equation_inventory(c);reports=[]
        for index,seed in enumerate((1,7,19)):
            lanes=['base','prior','zero','complete','local'];shift=(i+index)%5;runs=[x for x in row['runs'] if x['seed']==seed];A.need([x['lane'] for x in runs]==lanes[shift:]+lanes[:shift],'balanced evaluation order')
            for x in runs:
                lane=x['lane'];selected=[] if lane=='base' else library;weights=learned[seed,lane] if lane in ('complete','local') else [0.0]*12 if lane=='zero' else None;r=x['result'];A.need(x['library']==tuple(t['name'] for t in selected) and x['catalog_sha256']==row['catalog_sha256'],'same external grammar and declared library');A.need(r['limits']==dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000),'equal frozen evaluation budgets');report=replay(c,p['length'],r,selected,weights,1,False)
                if 'decoded' in r:
                    G.hierarchy_audit(c,p['length'],r,x['hierarchy'],selected);native_binding(code,json.loads(A.packed(x['hierarchy']['request'])),json.loads(A.packed(x['native'])))
                else:A.need('hierarchy' not in x and 'native' not in x,'unknown/exhausted evaluation has no proof certificate')
                reports.append(dict(seed=seed,lane=lane,trace=report))
        evaluation_reports.append(dict(id=p['id'],inventory=inventory,runs=reports));print('audited evaluation',p['id'],flush=True)
    result=dict(status='passed',donors=donor_reports,training_inventories=inventories,learners=learners,evaluation=evaluation_reports,seconds=time.perf_counter()-began,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dependencies={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_proof_policy.py','audit_proof_clusters.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py','logic.py')},scope='All complete and open executed DFS prefixes, literal cutoff boundaries, complete base inventories and global scheduling, all policy draws, online prefix gates, both reward/update chains, every positive primitive expansion and native input/program binding. Viable partial occupancy is not a theorem or extension guarantee; native instructions and general compiler soundness are not independently proved.')
    raw['independent_audit']=result;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return result

if __name__=='__main__':
    r=audit();print(json.dumps({k:v for k,v in r.items() if k not in ('donors','training_inventories','learners','evaluation')},indent=2))
