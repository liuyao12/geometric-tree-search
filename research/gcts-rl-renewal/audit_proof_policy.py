"""Independent policy draws, delayed credit, updates and complete GCTS replay.

No policy, miner, search graph, catalog producer or measured driver imports.
The frozen notebook-30 independent auditor supplies syntax and point replay.
"""
import copy,hashlib,json,math,time
from pathlib import Path
import logic as L
import audit_proof_clusters as G
import audit_semantic_proofs as A
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
sha=G.sha;goal_path=G.goal_path;run_audit=G.run_audit;hierarchy_audit=G.hierarchy_audit
FEATURES=('defer','defer_multiplication','defer_progress','defer_degree','members','level','target_member','direction','context_depth','term_shrink','input_already_placed','member_degrees')

def external_training():
    donors,evaluation=G.external();theory=donors['donor-1']['theory'];mul_theory=evaluation['mul-one']['theory'];z=L.F('zero');s=lambda t:L.F('succ',t);a=lambda x,y:L.F('add',x,y);m=lambda x,y:L.F('mul',x,y)
    def num(n):return z if n==0 else s(num(n-1))
    def record(target,n,bound,t=theory):return dict(theory=t,target=target,length=n,term_bound=bound)
    out={f'train-add-{x}-{y}':record(L.Eq(a(num(x),num(y)),num(x+y)),y+2,x+y+3) for x,y in ((0,1),(2,1),(1,2))}
    out.update({'train-successor':record(L.Eq(s(a(z,num(1))),num(2)),3,5),'train-inner-right':record(L.Eq(a(z,a(z,num(1))),num(1)),5,6),'train-inner-left':record(L.Eq(a(a(z,num(1)),z),num(1)),4,6),'train-mul-successor':record(L.Eq(s(m(num(1),num(1))),num(2)),5,8,mul_theory),'train-mul-zero':record(L.Eq(m(num(2),z),z),3,6,mul_theory)})
    return out

def close(x,y,label):
    if isinstance(x,(list,tuple)):
        A.need(isinstance(y,(list,tuple)) and len(x)==len(y),label+' dimensions')
        for a,b in zip(x,y):close(a,b,label)
    else:A.need(math.isfinite(x) and math.isfinite(y) and abs(x-y)<=1e-10*(1+abs(y)),label)
def term_nodes(t):return sum(1 for _ in A.locations(t))
def has_mul(t):return any(sub[0]=='fun' and sub[1]=='mul' for _,sub in A.locations(t))
def vector(c,n,order,ds,p,item):
    progress=len(order)/n;degree=math.log1p(len(ds[p]))/6;target=c['formulas'][c['target_id']];multiplication=any(has_mul(t) for t in target[1:]);bound=c['configuration']['term_bound']
    if item is None:return (1,float(multiplication),progress,degree)+(0,)*8
    keys=item['members'];inst=item['instance'];placed={k[0] for k in order}
    return (0,0,0,0,len(keys)/4,item['level']/2,float(any(k[0]==n-1 for k in keys)),float(inst['direction']),len(inst['context'])/bound,(term_nodes(inst['before'])-term_nodes(inst['after']))/bound,float(keys[0][2][0] in placed),sum(math.log1p(len(ds[k[0]])) for k in keys)/(6*len(keys)))

def policy_events(c,n,r,library,points,weights,start_state,stochastic):
    items,complete=G.index(c,n,library,r['limits']['index_instances']);state=start_state;offers=[]
    A.need(r['policy_weights']==tuple(weights) and r['policy_stochastic']==stochastic,'frozen episode policy')
    for k,event in enumerate(r['policy_events']):
        A.need(event['id']==k,'contiguous policy events');ds=points.domains(event['order']);kind,p,keys=A.decision(ds);A.need(kind=='branch' and event['point']==(2*p,0),'policy only after global propagation at selected point')
        pool,count=points.offered(items,event['order'],p,None);pool=sorted(pool,key=sha);A.need(event['pool_count']==count==len(pool) and event['pool_sha256']==sha(pool),'entire compatible proposal pool')
        options=pool+[None];ids=[sha(item) if item is not None else 'defer' for item in options];fs=[vector(c,n,event['order'],ds,p,item) for item in options];remaining=list(range(len(options)));chosen_items=[];draws=event['draws']
        for j,draw in enumerate(draws):
            A.need(j<r['limits']['proposal_limit'] and remaining,'bounded sampling without replacement');scores=[sum(w*x for w,x in zip(weights,fs[i])) for i in remaining];exps=[math.exp(x-max(scores)) for x in scores];prob=[x/sum(exps) for x in exps]
            if stochastic:
                state=(1664525*state+1013904223)%(2**32);u=(state+.5)/(2**32);close(draw['uniform'],u,'declared random variate');acc=0;pos=len(remaining)-1
                for z,v in enumerate(prob):
                    acc+=v
                    if u<acc:pos=z;break
            else:A.need(draw['uniform'] is None,'deterministic evaluation');pos=max(range(len(scores)),key=lambda j:scores[j])
            selected=remaining[pos];A.need(draw['action']==ids[selected],'selected softmax action');close(draw['probability'],prob[pos],'actual action probability');grad=[fs[selected][h]-sum(pr*fs[i][h] for pr,i in zip(prob,remaining)) for h in range(len(FEATURES))];close(draw['gradient'],grad,'actual log probability gradient');remaining.pop(pos)
            if options[selected] is None:A.need(j==len(draws)-1,'stop sampling on deferral');break
            chosen_items.append(options[selected])
        if draws and draws[-1]['action']!='defer':A.need(len(draws)==min(r['limits']['proposal_limit'],len(options)),'complete capped sample prefix')
        else:A.need(draws or r['limits']['proposal_limit']==0,'defer or zero cap')
        A.need(event['offered']==tuple(sha(i) for i in chosen_items),'exact offered sequence');offers.append(chosen_items)
    A.need(r['random_state']==state,'complete exported random stream')
    return offers

class PolicyPoints(G.Points):
    def __init__(self,base,events,offers):self.c=base.c;self.n=base.n;self.universe=base.universe;self.cache=base.cache;self.samples=0;self.events=events;self.offers=offers;self.cursor=0
    def offered(self,items,order,point,limit):
        A.need(self.cursor<len(self.events),'tree policy event exists');event=self.events[self.cursor];A.need(event['order']==tuple(order) and event['point']==(2*point,0),'DFS event order and context');out=self.offers[self.cursor];self.cursor+=1;return out,event['pool_count']

def run(c,n,r,library,weights=None,start_state=None,stochastic=False,points=None):
    base=points or G.Points(c,n)
    if weights is None:
        A.need(r['policy_weights'] is None and not r['policy_events'],'plain or authored fixed prior');return G.run_audit(c,n,r,library,base)
    offers=policy_events(c,n,r,library,base,weights,start_state,stochastic);replay=PolicyPoints(base,r['policy_events'],offers);report=G.run_audit(c,n,r,library,replay)
    if r['search_tree'] is not None:
        A.need(replay.cursor==len(r['policy_events']),'every event belongs to complete DFS');ids=[]
        def visit(tree):
            if 'policy_event' in tree:ids.append(tree['policy_event'])
            for trial in tree.get('proposals',()):
                if trial['trace']['status']=='accepted_cluster':visit(trial['tree'])
            for child in tree.get('children',()):visit(child['tree'])
        visit(r['search_tree']);A.need(ids==list(range(len(r['policy_events']))),'literal tree event identities')
    report.update(policy_events=len(r['policy_events']),policy_draws=sum(len(e['draws']) for e in r['policy_events']));return report

def credits(r,native):
    if r['search_tree'] is None:return []
    checked=native is not None and native['status']=='accepted';out=[]
    def subtree(t):
        if t['kind']=='dead':return (0,False)
        if t['kind']=='empty':return (0,True)
        counts=[];total=0;found=False
        for j,trial in enumerate(t['proposals']):
            cost=len(trial['trace']['steps']);success=False
            if trial['trace']['status']=='accepted_cluster':work,success=subtree(trial['tree']);cost+=work
            total+=cost;found|=success;counts.append((j,cost,success))
        work=0;success=False
        for child in t['children']:
            cost,okay=subtree(child['tree']);work+=1+cost;success|=okay
        total+=work;found|=success
        if 'policy_event' in t:
            event=r['policy_events'][t['policy_event']]
            if t['children'] and len(event['draws'])>len(counts) and event['draws'][len(counts)]['action']=='defer':counts.append((len(counts),work,success))
            for j,cost,success in counts:out.append(dict(event=event['id'],draw=j,base_attempts=cost,verified_continuation=checked and success,value=float(checked and success)-math.log1p(cost)/math.log1p(r['limits']['base_attempts'])))
        return total,found
    total,found=subtree(r['search_tree']);A.need(total==r['base_attempts'],'independent delayed credit counts');return sorted(out,key=lambda x:(x['event'],x['draw']))
def update_audit(weights,baseline,r,native,u):
    expected=credits(r,native);A.need(len(expected)==len(u['credits']),'no credit for unexecuted sampled suffixes');gradient=[0.0]*len(FEATURES);b=baseline
    for actual,x in zip(u['credits'],expected):
        for k in ('event','draw','base_attempts','verified_continuation'):A.need(actual[k]==x[k],'literal delayed credit '+k)
        close(actual['value'],x['value'],'delayed return');close(actual['baseline_before'],b,'action independent running baseline');advantage=x['value']-b;close(actual['advantage'],advantage,'actual advantage');b=.9*b+.1*x['value'];close(actual['baseline_after'],b,'baseline update')
        for k,g in enumerate(r['policy_events'][x['event']]['draws'][x['draw']]['gradient']):gradient[k]+=advantage*g
    close(u['gradient'],gradient,'full reached-choice projected policy gradient');expected_weights=[max(-6,min(6,w+.2*g)) for w,g in zip(weights,gradient)];close(u['weights_before'],weights,'zero-start update chain input');close(u['weights_after'],expected_weights,'projected update chain output');close(u['baseline_before'],baseline,'episode baseline input');close(u['baseline_after'],b,'episode baseline output');A.need(u['updated']==(r['search_tree'] is not None) and u['rate']==.2,'complete-tree update gate and rate')
    global_reward=float(native is not None and native['status']=='accepted')-math.log1p(r['base_attempts'])/math.log1p(50000)-(native.get('steps',0)/100000000/10 if native else 0);close(u['reward'],global_reward,'reported work reward');return expected_weights,b

def discoveries(data,code):
    donors,evaluation=G.external();library=[];donor_reports=[]
    def bind_problem(p,external):A.need(all(p[k]==freeze(v) for k,v in external.items()),'independent external statement')
    for row in data['donors']:
        p=row['problem'];bind_problem(p,donors[p['id']]);c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'],'donor base grammar');inventory=A.equation_inventory(c);A.need(row['input_library']==tuple(t['name'] for t in library),'earlier-only donor library');r=row['result'];run=run_audit(c,p['length'],r,library);hierarchy=hierarchy_audit(c,p['length'],r,row['hierarchy'],library);native_binding(code,json.loads(A.packed(row['hierarchy']['request'])),json.loads(A.packed(row['native'])))
        A.need(row['native']['status']=='accepted','promotion gate is a complete machine check');moves=[];keys=[]
        for key in goal_path(c,r['placements'],p['length']):
            recipe=c['rules'][key[1]]['recipe']
            if recipe['kind']=='block':moves.append(dict(recipe['move'],rule=recipe['axiom']));keys.append(key)
        known={sha([t['before'],t['after'],t['actions']]) for t in library};expected=[]
        for i in range(len(moves)):
            for size in range(2,min(4,len(moves)-i)+1):
                fragment=moves[i:i+size];identity=sha([fragment[0]['before'],fragment[-1]['after'],fragment])
                if identity not in known:expected.append((i,i+size,fragment));known.add(identity)
        promoted=row['promotion']['templates'];A.need(len(promoted)==len(expected),'every eligible mined window')
        for t,(i,j,fragment) in zip(promoted,expected):
            A.need(t['actions']==tuple(fragment) and t['before']==fragment[0]['before'] and t['after']==fragment[-1]['after'],'literal searched fragment');A.need(t['source']==dict(problem=p['id'],certificate_sha256=sha(r['decoded']['request']),window=(i,j),members=tuple(keys[i:j])),'literal discovery provenance');vars=sorted(set().union(*(L.term_free(a['before'])|L.term_free(a['after'])|set().union(*(L.term_free(v) for v in a['bindings'].values())) for a in fragment)));A.need(t['variables']==tuple(vars),'all fragment parameters');formula=L.Eq(t['before'],t['after'])
            for x in reversed(vars):formula=L.All(x,formula)
            A.need(t['definition']['premises']==() and t['definition']['conclusion']==formula,'universally closed fragment interface');children=[];k=0;old={x['name']:x for x in library}
            while k<j-i:
                choices=[tr for tr in r['solution_transactions'] if tr['template'] in old and tr['members']==tuple(keys[i+k:i+k+len(tr['members'])]) and k+len(tr['members'])<=j-i]
                if choices:tr=max(choices,key=lambda x:len(x['members']));children.append(tr['template']);k+=len(tr['members'])
                else:k+=1
            A.need(t['children']==tuple(children) and t['level']==1+max((old[x]['level'] for x in children),default=0),'actual lower-level calls define hierarchy');A.need([l['name'] for l in t['definition']['proof'] if l['rule']=='block']==children,'real child calls in primitive proof');A.need(t['name']==t['definition']['name']=='proof-cluster-'+sha([formula,t['actions'],children])[:20],'checked type name')
        library+=list(promoted);target=L.Imp(('bot',),('bot',));probe=dict(protocol='gcts-fol-1',theory=c['theory'],target=target,blocks=[t['definition'] for t in library],proof=[dict(rule='tautology',formula=target)]);A.need(A.whole_replay(json.loads(A.packed(probe)),A.pin(probe))['status']=='accepted','every promoted type, including unused types, independently expands');donor_reports.append(dict(id=p['id'],inventory=inventory,search=run,hierarchy=hierarchy,promoted=len(promoted)))
    A.need(tuple(library)==data['library'],'exact freshly mined library');return library,donor_reports

def audit(path=DOCS/'proof-policy-001.json'):
    began=time.perf_counter();path=Path(path);raw=json.loads(path.read_text());data=freeze(raw);donors,evaluation=G.external();training=external_training();code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];config=data['configuration']
    for n,pin in raw['sources'].items():A.need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==pin,'producer source '+n)
    expected=dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000,seeds=(1,7,19),epochs=4,native_steps=100000000,rate=.2,weight_clip=6,baseline_decay=.9);A.need(config==expected,'declared experiment and learning budgets');A.need(data['features']==FEATURES and not data['initial_library'] and len(data['donors'])==2,'declared features and empty library');A.need(data['program_sha256']==sha(code),'frozen full kernel program')
    library,donor_reports=discoveries(data,code);probe=data['whole_library_native'];A.need(probe['request']['blocks']==tuple(t['definition'] for t in library) and probe['request']['theory']==freeze(donors['donor-1']['theory']) and probe['request']['target']==('imp',('bot',),('bot',)),'complete newly mined library native input');native_binding(code,json.loads(A.packed(probe['request'])),json.loads(A.packed(probe['result'])));A.need(probe['result']['status']=='accepted','full library native gate')
    def bind(p,decl):A.need(all(p[k]==freeze(v) for k,v in decl.items()),'independently reconstructed external theory, target and envelope')
    def catalog(row,decl):
        p=row['problem'];bind(p,decl);c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'],'exact base grammar');A.need(sha(c)==row['catalog_sha256'],'catalog declaration binding');return c
    A.need([r['problem']['id'] for r in data['training_catalogs']]==list(training),'exact training statement set and order');catalogs={};train_reports=[]
    for row in data['training_catalogs']:
        p=row['problem'];c=catalog(row,training[p['id']]);inventory=A.equation_inventory(c);catalogs[p['id']]=(p,c,G.Points(c,p['length']));train_reports.append(dict(id=p['id'],inventory=inventory));print('audited training inventory',p['id'],flush=True)
    def problem_pin(p):return A.pin(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    A.need(not {problem_pin(p) for p in training.values()}&{problem_pin(p) for p in evaluation.values()},'training/evaluation disjoint even when cell envelopes differ')
    seeds=[];weights_by_seed={};A.need([r['seed'] for r in data['seeds']]==[1,7,19],'exact independent seed trials')
    for row in data['seeds']:
        weights=[0.0]*len(FEATURES);baseline=0.0;state=row['seed'];A.need(row['initial_weights']==tuple(weights) and row['initial_baseline']==0,'zero-start parameters');ids=list(training);expected_order=[(epoch,id) for epoch in range(4) for id in ids[epoch:]+ids[:epoch]];A.need([(e['epoch'],e['problem_id']) for e in row['episodes']]==expected_order,'all training episodes; no evaluation supplied to learner');reports=[]
        for i,e in enumerate(row['episodes']):
            p,c,points=catalogs[e['problem_id']];r=e['result'];A.need(e['input_random_state']==state,'continuous fresh-seed random stream');report=dict(problem_id=p['id'],epoch=e['epoch'],search=run(c,p['length'],r,library,weights,state,True,points));state=r['random_state'];native=e.get('native')
            if 'decoded' in r:
                report['hierarchy']=G.hierarchy_audit(c,p['length'],r,e['hierarchy'],library);native_binding(code,json.loads(A.packed(e['hierarchy']['request'])),json.loads(A.packed(native)));report['native_status']=native['status']
            else:A.need('hierarchy' not in e and native is None,'unknown training has no proof certificate')
            weights,baseline=update_audit(weights,baseline,r,native,e['update']);report['credited_actions']=len(e['update']['credits']);reports.append(report)
        close(row['weights'],weights,'final learned parameters');close(row['baseline'],baseline,'final baseline');A.need(row['random_state']==state,'final training random stream');weights_by_seed[row['seed']]=weights;seeds.append(dict(seed=row['seed'],episodes=reports,weights=weights));print('audited seed',row['seed'],flush=True)
    A.need([r['problem']['id'] for r in data['evaluation']]==list(evaluation),'exact held-out evaluation set');eval_reports=[]
    for i,row in enumerate(data['evaluation']):
        p=row['problem'];c=catalog(row,evaluation[p['id']]);inventory=A.equation_inventory(c);points=G.Points(c,p['length']);reports=[]
        for index,seed in enumerate((1,7,19)):
            lanes=['base','level1','prior','zero','trained'];shift=(i+index)%5;expected=lanes[shift:]+lanes[:shift];runs=[r for r in row['runs'] if r['seed']==seed];A.need([r['lane'] for r in runs]==expected,'rotated matched lane order')
            for case in runs:
                lane=case['lane'];selected=[] if lane=='base' else [t for t in library if t['level']==1] if lane=='level1' else library;A.need(case['library']==tuple(t['name'] for t in selected) and case['catalog_sha256']==row['catalog_sha256'],'same base grammar and declared library');weights=weights_by_seed[seed] if lane=='trained' else [0.0]*len(FEATURES) if lane=='zero' else None;r=case['result'];A.need(r['limits']==dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000),'equal evaluation budgets');report=dict(seed=seed,lane=lane,search=run(c,p['length'],r,selected,weights,1,False,points))
                if 'decoded' in r:
                    report['hierarchy']=G.hierarchy_audit(c,p['length'],r,case['hierarchy'],selected);native_binding(code,json.loads(A.packed(case['hierarchy']['request'])),json.loads(A.packed(case['native'])));report['native_status']=case['native']['status']
                else:A.need('native' not in case and 'hierarchy' not in case,'unknown/finite failure never receives a proof verdict')
                reports.append(report)
        eval_reports.append(dict(id=p['id'],inventory=inventory,runs=reports));print('audited evaluation',p['id'],flush=True)
    result=dict(status='passed',donors=donor_reports,training_inventories=train_reports,seeds=seeds,evaluation=eval_reports,seconds=time.perf_counter()-began,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dependencies={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('logic.py','audit_proof_clusters.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py')},scope='Independent complete base inventories, fresh mined windows, all policy pools/features/probabilities/random draws, all reached-choice delayed returns and projected updates, every complete tree and positive primitive expansion, and every native input/program binding. Unknown trees remain unproved; no native-instruction replay or general soundness theorem.')
    raw['independent_audit']=result;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return result
if __name__=='__main__':
    r=audit();print(json.dumps({k:v for k,v in r.items() if k not in ('donors','training_inventories','seeds','evaluation')},indent=2))
