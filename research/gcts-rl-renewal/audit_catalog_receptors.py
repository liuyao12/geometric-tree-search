"""Independent finite-word/catalog correspondence and complete trace replay.

Imports no new producer, search, worker or runner. The earlier independent
literal syntax and proposal reconstructors supply the original grammar.
"""
import collections,copy,hashlib,json,math,random
from audit_first_order_families import rebuild
from audit_semantic_inventory import (need,same,packed,pin,initial,state_pin,legal,advance,decode,proposals,features,close,FIXED,LiteralDomains)

def parse_fields(marks):
    fields=collections.defaultdict(dict);other=[]
    for point,value in marks:
        x,y=point
        if x%4 in (0,1):
            need(y>=100,'word point domain');kind='command' if x%4==1 else 'formula';j=x//4
            need(y-100 not in fields[j,kind],'unique word position');fields[j,kind][y-100]=value
        else:
            need(x%4==2 and (y==90 or y>=100),'mode/source disjoint domain');other.append((tuple(point),value))
    out={}
    for field,values in fields.items():
        need(sorted(values)==list(range(len(values))),'entire word starts at zero and has no gaps')
        word=[values[i] for i in range(len(values))]
        need(word[-1]==256 and all(type(v) is int and 0<=v<256 for v in word[:-1]),'distinct final terminator')
        b=bytes(word[:-1]);v=json.loads(b);need(packed(v)==b,'canonical complete JSON word');out[field]=b
    return out,other

def dictionary(full):
    words={kind:set() for kind in ('formula','command')}
    for c in full['placements']:
        fs,_=parse_fields(c['marks'])
        for (j,kind),b in fs.items():words[kind].add(b)
    fs,_=parse_fields(full['initial_marks'])
    for (j,kind),b in fs.items():words[kind].add(b)
    return {kind:[dict(id=i,value=json.loads(b),word_hex=b.hex(),expanded_points=len(b)+1) for i,b in enumerate(sorted(pool))] for kind,pool in words.items()}

def compress(marks,catalog):
    fs,other=parse_fields(marks);ids={kind:{bytes.fromhex(e['word_hex']):e['id'] for e in values} for kind,values in catalog.items()}
    return sorted(other+[((4*j+2,0 if kind=='formula' else 1),ids[kind][b]) for (j,kind),b in fs.items()])

def correspondence(full,compact):
    expected=dictionary(full);need(same(compact['catalog'],expected),'total injective catalog bound to all original words')
    for k in ('domains','command_counts','arity','mode_ids','conflicts','roots','complete_words','families_enabled'):
        need(same(full[k],compact[k]),'unchanged complete grammar '+k)
    need(len(full['placements'])==len(compact['placements']),'complete candidate identity bijection')
    count=0;old_points=0;new_points=0
    for a,b in zip(full['placements'],compact['placements']):
        need(same({k:v for k,v in a.items() if k!='marks'},{k:v for k,v in b.items() if k!='marks'}),'occupancy and metadata preserved')
        need(same(b['marks'],compress(a['marks'],expected)),'all distant marking assignments under exact quotient')
        count+=1;old_points+=len(a['marks']);new_points+=len(b['marks'])
    need(same(compact['initial_marks'],compress(full['initial_marks'],expected)),'fixed target boundary transformed exactly')
    return dict(status='passed',placements=count,full_mark_assignments=old_points,compact_mark_assignments=new_points,formula_values=len(expected['formula']),command_values=len(expected['command']))

def model_binding(spec,compiled,inventory,record):
    full=rebuild(spec,compiled,inventory,record['arity'],True)
    if 'catalog' not in record:
        for k,v in full.items():need(same(v,record[k]),'independent original model '+k)
        return dict(status='passed',placements=len(full['placements']))
    return correspondence(full,record)

def expanded_count(item,inventory,state,catalog):
    fresh={}
    for key in item['pending']:
        for point,value in inventory[tuple(key)]['marks']:
            p=tuple(point)
            if p not in state['marks']:fresh[p]=value
    total=0
    for (x,y),value in fresh.items():
        if y in (0,1):
            need(x%4==2,'compact field domain');entries=catalog['formula' if y==0 else 'command']
            need(type(value) is int and 0<=value<len(entries),'bounded scalar value');total+=len(bytes.fromhex(entries[value]['word_hex']))+1
        else:total+=1
    return total

def check_tree(spec,model,result,library,weights):
    inventory={tuple(c['key']):c for c in model['placements']};root=initial(spec,model)
    root['marks']={tuple(p):v for p,v in model['initial_marks']}
    metrics=collections.Counter();events=result['events'];hints=result['hints'];ei=hi=0;found=None;rng=random.Random(result['seed'])
    scoring=[0.]*10 if result['mode']=='zero' else FIXED if result['mode']=='fixed' else weights
    need(result['weights']==scoring and result['mode'] in ('base','zero','fixed','learned','no-family'),'frozen ordering lane');used_library=[] if result['mode']=='no-family' else library;enumerate_domains=LiteralDomains(inventory)
    def review(s,domains,hint,point):
        if hint is None:return None,dict(phase='absent',pending=[],eligible=[])
        pending=[tuple(k) for k in hint['item']['members'] if tuple(k) not in s['selected']]
        if not pending:return None,dict(phase='completed',pending=[],eligible=[])
        bad=[k for k in pending if not legal(inventory[k],s)]
        if bad:return None,dict(phase='invalid',pending=pending,illegal=bad,eligible=[])
        allowed=[k for k in pending if k in domains.get(point,[])];return hint,dict(phase='eligible' if allowed else 'waiting',pending=pending,eligible=allowed)
    def walk(s,t,hint):
        nonlocal ei,hi,found
        metrics['nodes']+=1;domains=enumerate_domains(s);census=[dict(point=p,generation=s['generations'][p],keys=d) for p,d in sorted(domains.items())]
        need(same(t['census'],census) and t['state_sha256']==state_pin(s),'every complete point graph and full state')
        dead=sorted(p for p,d in domains.items() if not d);forced=sorted(p for p,d in domains.items() if len(d)==1)
        if dead:kind,p='dead',dead[0]
        elif forced:kind,p='forced',forced[0]
        elif not domains:kind,p='empty',None
        else:kind,p='branch',min(domains,key=lambda p:(s['generations'][p],len(domains[p]),p))
        need(t['kind']==kind and same(t['point'],p),'global reference scheduler');need(t['hint_in']==(hint['id'] if hint else None),'branch-local hint inheritance');active,trace=review(s,domains,hint,p);need(same(t['review'],trace),'exact hint completion, waiting and retirement')
        if hint:metrics['hint_'+trace['phase']]+=1
        if kind=='dead':metrics['dead']+=1;need(not t['children'] and 'policy_event' not in t,'dead precedes policy');return False
        if kind=='empty':found=s;need(not t['children'] and 'policy_event' not in t,'whole target before success');return True
        metrics[kind]+=1;keys=domains[p]
        if kind=='branch' and active is None and result['mode']!='base':
            need(t['policy_event']==ei and ei<len(events),'every guidance event');event=events[ei];items,work=proposals(inventory,used_library,s,domains,p,result['limits']['proposal_limit'],result['limits']['proposal_checks'])
            for k,v in work.items():metrics[k]+=v
            vectors=[features(item,inventory,spec,s) for item in items]
            if result['feature_semantics']=='expanded-word' and 'catalog' in model:
                for item,v in zip(items,vectors):
                    if item is not None:v[5]=expanded_count(item,inventory,s,model['catalog'])/1000
            need(same(event['items'],items) and all(close(a,b) for a,b in zip(event['features'],vectors)) and len(event['features'])==len(vectors),'entire bounded proposal pool and exact state features');need(event['id']==ei and same(event['chosen'],s['order']) and same(event['point'],p) and event['weights']==scoring,'state-bound policy event')
            scores=[sum(w*x for w,x in zip(scoring,v)) for v in vectors];top=max(scores);raw=[math.exp(x-top) for x in scores];prob=[x/sum(raw) for x in raw];need(close(scores,event['scores']) and close(prob,event['probabilities']),'actual softmax distribution')
            if result['stochastic']:
                u=rng.random();need(event['uniform']==u,'fresh seeded stochastic draw');cumulative=0.;selected=len(prob)-1
                for j,x in enumerate(prob):
                    cumulative+=x
                    if u<cumulative:selected=j;break
            else:selected=max(range(len(scores)),key=lambda j:(scores[j],-j));need(event['uniform'] is None,'greedy held-out policy')
            need(event['index']==selected,'actual chosen cluster/defer');ei+=1;item=items[selected]
            if item is not None:
                need(t['hint_start']==hi and hi<len(hints),'new hint identity');expected=dict(id=hi,chosen=s['order'],point=p,item=item);need(same(hints[hi],expected),'validated original expansion and current interface');active=dict(id=hi,item=item);hi+=1;metrics['hints_started']+=1;active,start=review(s,domains,active,p);need(active is not None and start['eligible'] and same(t['start_review'],start),'new cluster reaches selected point');trace=start
            else:need('hint_start' not in t,'defer leaves all candidates available')
        else:need('policy_event' not in t and 'hint_start' not in t,'forced/waiting precedes new proposals')
        preferred=set(trace['eligible']) if active else set();order=keys if kind=='forced' else [k for k in keys if k in preferred]+[k for k in keys if k not in preferred];need(same(t['alternatives'],order),'complete original fallback, reordered only')
        for index,child in enumerate(t['children']):
            need(index<len(order) and same(child['key'],order[index]) and child['role']==('member' if order[index] in preferred else 'base'),'exact scheduled constituent and fallback role');metrics['attempts']+=1;okay=walk(advance(inventory[order[index]],s),child['tree'],active)
            if okay is not False:need(index+1==len(t['children']),'no siblings after accept/unknown');return okay
            metrics['backtracks']+=1
        if len(t['children'])<len(order):
            need(t.get('cutoff')=='before_placement' and (metrics['attempts']>=result['limits']['attempts'] or result['seconds']>=result['limits']['seconds']),'unfinished remains unknown');return None
        need('cutoff' not in t,'fully exhausted branch');return False
    okay=walk(root,result['tree'],None);status='finite_marked_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_marked_region';need(result['status']==status and result['root_restored'] and result['root_state_sha256']==state_pin(root),'exact terminal result and rollback');expected_metrics={k:v for k,v in result['metrics'].items() if k!='proposal_seconds'};need(expected_metrics==dict(metrics) and ei==len(events) and hi==len(hints),'all placements, proposals, branches and hints');need(result['metrics'].get('proposal_seconds',0)>=0,'reported proposal clock')
    proof=decode(model,found) if found else None;need(result['proof']==proof and same(result['placements'],found['order'] if found else []) and result['tile_generations']==(found['tile_generations'] if found else []),'actual decoded proof and generations');return dict(nodes=metrics['nodes'],events=ei,hints=hi)

def structural_nodes(t):
    out=[dict(kind=t['kind'],point=t['point'],census_sha256=pin(t['census']),hint_in=t['hint_in'],review=t['review'],alternatives=t.get('alternatives'),policy_event=t.get('policy_event'),hint_start=t.get('hint_start'))]
    for child in t['children']:out+=structural_nodes(child['tree'])
    return out

def paired(a,b):
    aa=structural_nodes(a['tree']);bb=structural_nodes(b['tree']);n=min(len(aa),len(bb))
    need(same(aa[:n],bb[:n]),'same structural GCTS traversal until first budget boundary')
    for x,y in zip(a['events'],b['events']):
        for key in ('index','features','scores','probabilities','uniform','chosen','point','weights'):
            need(same(x[key],y[key]),'faithful policy event '+key)
        need(same([None if i is None else {k:i[k] for k in ('members','pending','kind','level','new_occupancy')} for i in x['items']],
                  [None if i is None else {k:i[k] for k in ('members','pending','kind','level','new_occupancy')} for i in y['items']]),'same validated proposal members')
    if a['status']!='unknown_search_budget' and b['status']!='unknown_search_budget':
        need(len(aa)==len(bb) and a['proof']==b['proof'],'same complete traversal and certificate')
        need({k:v for k,v in a['metrics'].items() if k!='proposal_seconds'}=={k:v for k,v in b['metrics'].items() if k!='proposal_seconds'},'same complete work counters')
    return dict(status='passed',common_nodes=n,word_nodes=len(aa),compact_nodes=len(bb),both_terminal=a['status']!='unknown_search_budget' and b['status']!='unknown_search_budget')

def main():
    import gzip,subprocess,time
    from pathlib import Path
    from audit_first_order import compilation
    from audit_first_order_families import registry_binding
    import audit_semantic_inventory as native_audit
    from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
    began=time.perf_counter();here=Path(__file__).resolve().parent;root=here.parents[1];out=root/'.gcts-active/catalog-receptors-20261011';tmp=Path('/private/tmp/gcts-catalog-receptors-audit-20261011');doc=root/'docs/research/gcts-rl-renewal'
    plan=json.loads((out/'plan.json').read_text())
    for f,h in plan['sources'].items():need(hashlib.sha256((root/f).read_bytes()).hexdigest()==h,'frozen source '+f)
    for f,r in plan['data_dependencies'].items():
        p=root/f;need(p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],'pinned reuse '+f)
    reader=json.loads((root/plan['input_reader']).read_text());prior=json.loads(gzip.decompress((root/plan['prior_native']).read_bytes()));old_audit=json.loads((root/plan['prior_audit']).read_text());need(old_audit['status']=='passed','prior full native audit')
    records=json.loads(gzip.decompress((out/'native.json.gz').read_bytes()));requests={};cache={};cases=[];totals=collections.Counter()
    for name in plan['cases']:
        raw=json.loads(gzip.decompress((out/(name+'.json.gz')).read_bytes()));source=next(x for x in reader['cases'] if x['spec']['id']==name)
        need(raw['case']==source['spec'] and raw['compiled']==source['compiled'] and raw['inventory']==source['inventory'],'exact frozen theory, syntax and ground inventory')
        compilation(raw['case'],raw['compiled'],prior);registry_binding(reader['training']['library'],raw['case'],raw['compiled'],raw['inventory'],prior)
        models={r:json.loads(gzip.decompress((out/(name+'-'+r+'-model.json.gz')).read_bytes())) for r in ('word','compact')}
        bindings={r:model_binding(raw['case'],raw['compiled'],raw['inventory'],m) for r,m in models.items()};counts=[]
        need(len(raw['observations'])==len(plan['lanes'])*len(plan['repetitions']),'all declared observations')
        expected=[(r,l) for r in plan['repetitions'] for l in plan['schedules'][str(r)]]
        for obs,(rep,lane) in zip(raw['observations'],expected):
            method=plan['lanes'][lane];result=obs['search'];model=models[method['representation']]
            need(obs['lane']==lane and obs['repetition']==rep and result['mode']==method['mode'] and result['feature_semantics']==method['feature_semantics'] and result['seed']==plan['seed'] and result['limits']==plan['limits'] and not result['stochastic'],'predeclared paired schedule and limits')
            need(obs['model_stats']['model_sha256']==pin({k:v for k,v in model.items() if k!='compile_seconds'}),'complete fresh model identity')
            checked=check_tree(raw['case'],model,result,raw['inventory'],plan['weights'] if method['mode']=='learned' else None);totals.update(checked)
            proof=result['proof'];q=obs['native_query']
            if proof is None:need(q is None and not obs['cached_native_acceptance'],'unknown has no fabricated acceptance')
            else:
                req=dict(protocol='gcts-fol-1',theory=raw['case']['theory'],blocks=native_audit.closure(raw['inventory'],proof),proof=proof,target=raw['case']['target']);key=pin(req)
                need(records[q]['request']==req and records[q]['result']['status']=='accepted','whole searched proof independently bound')
                if obs['cached_native_acceptance']:need(cache.get(key)==q,'only exact earlier new-study cache')
                else:need(q not in requests and key not in cache and records[q]['purpose']=='catalog_receptor_whole','fresh whole native request');requests[q]=req;cache[key]=q
                totals['proof_observations']+=1
            counts.append(dict(lane=lane,repetition=rep,**checked))
        pairs=[]
        for rep in plan['repetitions']:
            observations={o['lane']:o['search'] for o in raw['observations'] if o['repetition']==rep}
            for a,b in [('word-base','compact-base'),('word-learned','compact-expanded')]:pairs.append(dict(repetition=rep,word=a,compact=b,**paired(observations[a],observations[b])))
        cases.append(dict(id=name,bindings=bindings,observations=counts,pairs=pairs))
        print('independent model/tree audit',name,flush=True)
    need(set(requests)==set(range(len(records))),'every new native computation accounted')
    tmp.mkdir(parents=True,exist_ok=True);micro=json.loads(gzip.decompress((doc/'proof-boundary-microcode-001.json.gz').read_bytes()));boundary=json.loads((doc/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native computational palette')
    subprocess.run(['clang++','-O3','-std=c++17',str(here/'audit_tape_micro.cpp'),'-o',str(tmp/'native')],check=True);(tmp/'code.bin').write_bytes(code_bytes(micro));native_audit.TMP=tmp
    steps,accepted=native_audit.replay_native(records,requests,micro,boundary['cases'][0]['initial'],plan['native_steps'])
    result=dict(status='passed',version='catalog-receptors-audit-001',cases=cases,seconds=time.perf_counter()-began,native_queries=len(records),micro_steps=steps,accepted_requests=len(accepted),prior_native_queries_reused=old_audit['native_queries'],**dict(totals))
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True)

if __name__=='__main__':main()

