"""Independent family bindings, full point trees, policy updates and native I/O.

Does not import the new producer, policy, family miner, join, search or cases.
Point inventory reconstruction is reused from the independently written
Notebook 61 auditor; all new guidance and learning is replayed here.
"""
import collections,copy,gzip,hashlib,itertools,json,math,random,subprocess,time
from pathlib import Path
from audit_tree_kernel import need,packed
from audit_certificate_boundary import grammar,initial_for,artifact,sha,pin
from audit_native_receptor_points import rebuild,initial,advance,legal,state_pin,point_tree as donor_tree
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_semantic_proofs import whole_replay
from audit_logical_wang_clusters import checked_chain
from micro_cert import run,write_cuts
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-native-inventory-policy-audit-001')
FEATURES=['family','base_growth','internal_refs','already_justified_inputs','target_output','mark_extension','shape_density','completed_pairs','level','defer'];FIXED=[.5,.4,.6,.7,.1,-.1,.1,.3,.2,0.]
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def same(a,b):return packed(a)==packed(b)
def close(a,b):return len(a)==len(b) and all(abs(x-y)<=1e-12 for x,y in zip(a,b))
def corpus_inventory(donors):
    unique={}
    for d in donors:
        placements=d['search']['placements'];guards={k[0]:k for k in placements if k[1]==1};meta={tuple(c['key']):c for c in d['model']['placements']}
        for size in range(1,min(3,len(guards))+1):
            for chosen in itertools.combinations(sorted(guards),size):
                labels={slot:i for i,slot in enumerate(chosen)};neighbors=[set() for _ in chosen];external={};nodes=[]
                for slot in chosen:
                    c=meta[tuple(guards[slot])];ports=[]
                    for source,_ in c['requirements']:
                        if source in labels:
                            ports.append({'node':labels[source]});neighbors[labels[slot]].add(labels[source]);neighbors[labels[source]].add(labels[slot])
                        else:ports.append({'hole':external.setdefault(source,len(external))})
                    nodes.append(dict(rule=c['command']['rule'],inputs=ports))
                visited={0}
                while True:
                    nxt=visited|set().union(*(neighbors[i] for i in visited))
                    if nxt==visited:break
                    visited=nxt
                if len(visited)!=size:continue
                template=dict(nodes=nodes,holes=len(external));key=pin(template);origin=dict(case=d['case']['id'],slots=chosen,placements=[k for j in chosen for k in ((j,0,guards[j][2],0),guards[j])])
                if key not in unique:unique[key]=dict(id=key,template=template,level=max(1,sum(n['rule'] in ('mp','generalize') for n in nodes)),donors=[])
                need(same(unique[key]['template'],template),'family identifier is unambiguous for actual corpus');unique[key]['donors'].append(origin)
    return sorted(unique.values(),key=lambda f:(-len(f['template']['nodes']),f['id']))
def cluster(inventory,members,state,summary=True):
    keys=sorted({tuple(k) for k in members});pending=[k for k in keys if k not in state['selected']];totals=collections.Counter();marks={}
    for k in pending:
        if k not in inventory:return None
        for p,v in inventory[k]['occupancy']:totals[tuple(p)]+=v
        for p,v in inventory[k]['marks']:
            p=tuple(p)
            if p in marks and marks[p]!=v:return None
            marks[p]=v
    if any(p not in state['roots'] or state['totals'].get(p,0)+v>12 for p,v in totals.items()) or any(p in state['marks'] and state['marks'][p]!=v for p,v in marks.items()):return None
    if not summary:return True
    return dict(members=keys,pending=pending,aggregate_sha256=pin(dict(totals=sorted(totals.items()),marks=sorted(marks.items()))),new_occupancy=sum(totals.values()),new_marks=sum(p not in state['marks'] for p in marks))
def features(item,inventory,spec,state):
    if item is None:return [0.]*9+[1.]
    slots={k[0] for k in item['members']};guards=[inventory[tuple(k)] for k in item['members'] if k[1]==1];sources=[j for c in guards for j,a in c['requirements']];known=set();commands={k[0]:k for k in state['selected'] if k[1]==0};selected={k[0]:k for k in state['selected'] if k[1]==1}
    for j,k in sorted(selected.items()):
        if j in commands and commands[j][2]==k[2] and all(i in known for i,a in inventory[k]['requirements']):known.add(j)
    return [float(item['kind']=='family'),item['new_occupancy']/72,sum(j in slots for j in sources)/max(1,len(sources)),sum(j in known for j in sources)/max(1,len(sources)),float(any(c['command']['formula']==spec['target'] for c in guards)),item['new_marks']/1000,len(slots)/(max(slots)-min(slots)+1),len(guards)/3,item['level']/2,0.]
def proposals(inventory,library,state,domains,point,limit,check_limit):
    rules=collections.defaultdict(list)
    for k,c in sorted(inventory.items()):
        if k[1]==1:rules[c['command']['rule']].append(k)
    anchors=domains[point];pool=[];seen=set();work=collections.Counter();global_stop=False;family_stop=False;family_end=limit;family_checks=check_limit
    def test(members,summary=False):
        nonlocal global_stop,family_stop
        if work['validation_checks']>=check_limit:global_stop=True;return None
        if work['validation_checks']>=family_checks:family_stop=True;return None
        work['validation_checks']+=1;return cluster(inventory,members,state,summary)
    def emit(family,assignment,holes,members):
        record=test(members,True)
        if record is None:return
        key=tuple(record['members'])
        if key in seen or not any(k in anchors for k in record['pending']):return
        seen.add(key);record.update(kind='family',family=family['id'],bindings=dict(nodes=sorted(assignment.items()),holes=sorted(holes.items())),level=family['level']);record['id']=pin(dict(kind='family',members=record['members'],family=family['id']));pool.append(record)
    def instantiate(family,root_node,root_guard):
        nodes=family['template']['nodes'];order=[root_node]+[i for i in range(len(nodes)) if i!=root_node]
        def walk(depth,assignment,holes,members):
            if global_stop or family_stop or len(pool)>=family_end:return
            if depth==len(order):emit(family,assignment,holes,members);return
            node=order[depth];descriptor=nodes[node];expected=[]
            for other,k in assignment.items():
                for r,p in enumerate(nodes[other]['inputs']):
                    if p.get('node')==node:expected.append(inventory[k]['requirements'][r])
            if expected and len({p[0] for p in expected})!=1:return
            for k in [root_guard] if depth==0 else rules[descriptor['rule']]:
                if global_stop or family_stop or len(pool)>=family_end:return
                c=inventory[k];slot=k[0]
                if expected and slot!=expected[0][0] or any(f!=c['command']['formula'] for _,f in expected):continue
                if slot in [g[0] for g in assignment.values()] or slot in holes.values() or len(c['requirements'])!=len(descriptor['inputs']):continue
                if any('node' in port and port['node'] in assignment and (c['requirements'][r][0]!=assignment[port['node']][0] or c['requirements'][r][1]!=inventory[assignment[port['node']]]['command']['formula']) for r,port in enumerate(descriptor['inputs'])):continue
                external=holes.copy();okay=True
                for r,port in enumerate(descriptor['inputs']):
                    if 'hole' not in port:continue
                    source=c['requirements'][r][0];label=port['hole']
                    if label in external and external[label]!=source or source==slot or source in [g[0] for g in assignment.values()] or any(h!=label and j==source for h,j in external.items()):okay=False;break
                    external[label]=source
                if not okay:continue
                pair=[(slot,0,k[2],0),k]
                if test(members+pair) is None:continue
                walk(depth+1,{**assignment,node:k},external,members+pair)
        walk(0,{}, {},[])
    for anchor in anchors[:limit]:
        anchor_end=min(limit,len(pool)+max(1,limit//max(1,min(len(anchors),limit))));anchor_checks=min(check_limit,work['validation_checks']+max(1,check_limit//max(1,min(len(anchors),limit))))
        for family in library:
            family_stop=False;family_end=min(anchor_end,len(pool)+1);family_checks=min(anchor_checks,work['validation_checks']+max(1,(check_limit//max(1,min(len(anchors),limit)))//max(1,len(library))))
            for rows in rules.values():
                for k in rows:
                    if k[0]!=anchor[0] or k[2]!=anchor[2] or anchor[1]==1 and k!=anchor:continue
                    for i,n in enumerate(family['template']['nodes']):
                        if n['rule']==inventory[k]['command']['rule']:instantiate(family,i,k)
                        if global_stop or family_stop or len(pool)>=family_end:break
                    if global_stop or family_stop or len(pool)>=family_end:break
                if global_stop or family_stop or len(pool)>=family_end:break
            work['family_budget_stops']+=int(family_stop);work['family_quota_stops']+=int(len(pool)>=family_end)
            if global_stop or len(pool)>=anchor_end or work['validation_checks']>=anchor_checks:break
        if global_stop or len(pool)>=limit:break
    work['family_pool']=len(pool);work['family_truncated']=int(global_stop or work['family_budget_stops'] or work['family_quota_stops'] or len(pool)>=limit);tests=0;all_keys=sorted({k for rows in domains.values() for k in rows})
    for anchor in anchors[:4]:
        ordering=sorted(all_keys,key=lambda k:hashlib.sha256(packed(dict(anchor=anchor,key=k,chosen=state['order']))).digest())
        for wanted in (1,3):
            chosen=[anchor]
            if wanted>1:
                for k in ordering:
                    if tests>=64:break
                    if k in chosen:continue
                    tests+=1
                    if cluster(inventory,chosen+[k],state,False) is not None:chosen.append(k)
                    if len(chosen)>=wanted:break
            record=cluster(inventory,chosen,state);work['sample_validation_checks']+=1
            if record is not None and tuple(record['members']) not in seen:
                seen.add(tuple(record['members']));record.update(kind='sampled',family=None,bindings=None,level=0);record['id']=pin(dict(kind='sampled',members=record['members'],family=None));pool.append(record)
        if len(pool)-work['family_pool']>=8:break
    work['sample_pair_tests']=tests;work['items']=len(pool);return [None]+pool,dict(work)
def guided_tree(spec,model,result,library,weights):
    inventory={tuple(c['key']):c for c in model['placements']};root=initial(spec,model);metrics=collections.Counter();events=result['events'];hints=result['hints'];ei=hi=0;found=None;rng=random.Random(result['seed'])
    scoring=[0.]*10 if result['mode']=='zero' else FIXED if result['mode']=='fixed' else weights
    need(result['weights']==scoring and result['mode'] in ('base','zero','fixed','learned','no-family'),'frozen ordering lane');used_library=[] if result['mode']=='no-family' else library
    def review(s,domains,hint,point):
        if hint is None:return None,dict(phase='absent',pending=[],eligible=[])
        pending=[tuple(k) for k in hint['item']['members'] if tuple(k) not in s['selected']]
        if not pending:return None,dict(phase='completed',pending=[],eligible=[])
        bad=[k for k in pending if not legal(inventory[k],s)]
        if bad:return None,dict(phase='invalid',pending=pending,illegal=bad,eligible=[])
        allowed=[k for k in pending if k in domains.get(point,[])];return hint,dict(phase='eligible' if allowed else 'waiting',pending=pending,eligible=allowed)
    def walk(s,t,hint):
        nonlocal ei,hi,found
        metrics['nodes']+=1;domains={p:sorted(k for k,c in inventory.items() if tuple(c['occupancy'][0][0])==p and legal(c,s)) for p in s['roots'] if s['totals'].get(p,0)<12};census=[dict(point=p,generation=s['generations'][p],keys=d) for p,d in sorted(domains.items())]
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
            vectors=[features(item,inventory,spec,s) for item in items];need(same(event['items'],items) and all(close(a,b) for a,b in zip(event['features'],vectors)) and len(event['features'])==len(vectors),'entire bounded proposal pool and exact state features');need(event['id']==ei and same(event['chosen'],s['order']) and same(event['point'],p) and event['weights']==scoring,'state-bound policy event')
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
    proof=[inventory[k]['command'] for k in sorted(found['order']) if k[1]==0] if found else None;need(result['proof']==proof and same(result['placements'],found['order'] if found else []) and result['tile_generations']==(found['tile_generations'] if found else []),'actual decoded proof and generations');return dict(nodes=metrics['nodes'],events=ei,hints=hi)
def catalog(spec,compiled,records,requests):
    basis,variables,domains=grammar(spec);need(compiled['status']=='complete' and (compiled['basis'],compiled['variables'])==(basis,variables) and len(compiled['queries'])==len(basis),'complete fixed native catalog');accepted=[]
    for j,q in enumerate(compiled['queries']):
        rec=records[q];request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[dict(rule='tautology',formula=basis[j])],target=basis[j]);need(rec['purpose']=='tautology_instance' and rec['basis_index']==j and rec['request']==request and rec['result']['status'] in ('accepted','rejected'),'each compiler query');need(q not in requests,'query has one declared origin');requests[q]=request
        if rec['result']['status']=='accepted':accepted.append(basis[j])
    need(compiled['tautologies']==accepted,'all and only accepted tautology guards');return rebuild(spec,compiled)
def verify_model(raw,rebuilt):
    for k in ('domains','command_counts','complete_words','placements','conflicts','roots'):need(same(raw[k],rebuilt[k]),'unchanged complete base inventory '+k)
def command_request(spec,model,proof):
    # Rebuild each command in the independently declared insertion order.
    commands=[next(c for c in model['domains'][j] if c==row) for j,row in enumerate(proof)];return dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=commands,target=spec['target'])
def training_replay(training):
    need(training['features']==FEATURES and training['rate']==.4 and len(training['episodes'])==24,'fresh policy protocol');records=training['records'];requests={};models={};cache={};nodes=events=hints=0;next_query=0
    for d in training['donors']:
        m=catalog(d['case'],d['compiled'],records,requests);verify_model(d['model'],m);nodes+=donor_tree(dict(case=d['case'],search=d['search'],proof=d['search']['proof']),m);q=d['verification_query'];need(d['compiled']['queries']==list(range(next_query,next_query+len(d['compiled']['basis']))) and q==next_query+len(d['compiled']['basis']),'donor compilation precedes new native acceptance');next_query=q+1;request=command_request(d['case'],m,d['search']['proof']);rec=records[q];need(rec['purpose']=='new_inventory_donor' and rec['request']==request and rec['result']['status']=='accepted','new native donor only');need(q not in requests,'unique donor query');requests[q]=request;cache[pin(request)]=q;models[d['case']['id']]=(d['case'],m)
    library=corpus_inventory(training['donors']);need(same(library,training['library']),'all mined, name-free typed dependency families');weights=[0.]*10;baseline=0.
    for index,episode in enumerate(training['episodes']):
        spec,m=models[episode['case']];need(episode['id']==index and episode['case']==training['donors'][index%3]['case']['id'] and episode['weights_before']==weights,'fresh zero start and declared donor schedule');result=episode['search'];need(result['mode']=='learned' and result['stochastic'] is True and result['seed']==10000+index,'fresh exploration seed');work=guided_tree(spec,m,result,library,weights);nodes+=work['nodes'];events+=work['events'];hints+=work['hints'];accepted=False
        if result['proof']:
            request=command_request(spec,m,result['proof']);key=pin(request);q=episode['verification_query']
            if key in cache:need(episode['cached_native_acceptance'] and q==cache[key],'training-only exact acceptance cache');accepted=True
            else:
                need(not episode['cached_native_acceptance'] and q not in requests and q==next_query,'new training feedback query');next_query+=1;rec=records[q];need(rec['purpose']=='training_feedback' and rec['request']==request,'whole-native training feedback');requests[q]=request;accepted=rec['result']['status']=='accepted'
                if accepted:cache[key]=q
        else:need(episode['verification_query'] is None and not episode['cached_native_acceptance'],'unfinished search has no native success')
        need(episode['accepted']==accepted,'native reward binding');growth=2*len(result['proof']) if accepted else 0;value=growth/max(1,result['metrics'].get('attempts',0))-.25*min(1.,(result['metrics'].get('validation_checks',0)+result['metrics'].get('sample_pair_tests',0))/100000);gradient=[0.]*10
        for e in result['events']:
            for k in range(10):gradient[k]+=e['features'][e['index']][k]-sum(p*v[k] for p,v in zip(e['probabilities'],e['features']))
        gradient=[g/max(1,len(result['events'])) for g in gradient];advantage=value-baseline;need(close(episode['learning']['gradient'],gradient) and abs(episode['learning']['reward']-value)<=1e-12 and episode['learning']['baseline_before']==baseline and abs(episode['learning']['advantage']-advantage)<=1e-12,'actual reward and REINFORCE gradient');weights=[w+.4*advantage*g for w,g in zip(weights,gradient)];baseline=.9*baseline+.1*value;need(close(episode['weights_after'],weights) and abs(episode['baseline_after']-baseline)<=1e-12,'every policy update')
    need(close(training['weights'],weights) and abs(training['baseline']-baseline)<=1e-12 and set(requests)==set(range(len(records))) and training['queries']==len(records),'all training queries and final frozen policy');return dict(requests=requests,library=library,weights=weights,nodes=nodes,events=events,hints=hints)
def evaluation_replay(raw,library,weights,policy_sha):
    requests={};model=catalog(raw['case'],raw['compiled'],raw['records'],requests);verify_model(raw['model'],model);need(raw['policy_sha256']==policy_sha and raw['search']['mode']==raw['mode'] and raw['search']['stochastic'] is False,'frozen cold lane');work=guided_tree(raw['case'],model,raw['search'],library,weights)
    if raw['search']['proof']:
        q=raw['verification_query'];rec=raw['records'][q];request=command_request(raw['case'],model,raw['search']['proof']);need(rec['purpose']=='frozen_evaluation_without_search_hints' and rec['request']==request and rec['result']['status']=='accepted' and raw['status']=='native_proof_discovered','fresh whole-native held-out acceptance');need(q not in requests,'one final native query');requests[q]=request
    else:need(raw['status']==raw['search']['status'] and raw['proof'] is None and 'verification_query' not in raw,'no invented unknown/exhausted proof')
    need(raw['proof']==raw['search']['proof'] and raw['queries']==len(raw['records']) and set(requests)==set(range(len(raw['records']))),'complete cold query coverage');return dict(requests=requests,model=model,**work)
def replay_native(records,requests,micro,template):
    steps=0;accepted={}
    for q,rec in enumerate(records):
        request=requests[q];need(rec['id']==q and rec['request']==request and rec['request_sha256']==pin(request) and rec['query_target']=='fixed_assertion','exact native request identity and target role');boot=initial_for(micro,template,request);words=dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]);need(rec['boundary_words']==words,'independent tagged byte-word encoder');(TMP/'input.bin').write_bytes(input_bytes(boot));need(sha(TMP/'input.bin')==rec['input_sha256'],'complete native boot frame');response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',10**9))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'all-native independent replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'],'actual start and entire output');steps+=response['micro_steps']
        try:logical=whole_replay(request)['status']
        except ValueError:logical='rejected'
        if response['status'] in ('accepted','rejected'):need(response['status']==logical,'logical cross-check, audit only')
        if response['status']=='accepted':accepted[pin(request)]=request
    return steps,accepted
def mutations(training,raw,library,weights,policy_sha):
    rejected=[]
    def changed(name,document,edit,check):
        b=copy.deepcopy(document);edit(b)
        try:check(b)
        except (ValueError,KeyError,IndexError,TypeError,StopIteration):rejected.append(name)
        else:raise ValueError('corruption admitted '+name)
    cold=lambda b:evaluation_replay(b,library,weights,policy_sha)
    changed('missing-original-command',raw,lambda b:b['model']['domains'][0].pop(),cold)
    changed('missing-remote-value',raw,lambda b:b['model']['placements'][-1]['marks'].pop(),cold)
    changed('false-census',raw,lambda b:b['search']['tree']['census'][0]['keys'].pop(),cold)
    changed('wrong-generation',raw,lambda b:b['search']['tree']['census'][0].update(generation=7),cold)
    changed('lost-full-fallback',raw,lambda b:b['search']['tree']['alternatives'].pop(),cold)
    changed('false-rollback',raw,lambda b:b['search'].update(root_restored=False),cold)
    changed('wrong-chosen-cluster',raw,lambda b:b['search']['events'][0].update(index=(b['search']['events'][0]['index']+1)%len(b['search']['events'][0]['items'])),cold)
    changed('changed-cluster-expansion',raw,lambda b:b['search']['events'][0]['items'][-1]['members'].pop(),cold)
    changed('changed-probability',raw,lambda b:b['search']['events'][0]['probabilities'].__setitem__(0,0.9),cold)
    changed('changed-source-justification',raw,lambda b:b['search']['events'][0]['features'][1].__setitem__(3,9.),cold)
    changed('lost-hint-receptor',raw,lambda b:b['search']['hints'][0]['item']['pending'].pop(),cold)
    changed('changed-final-assertion',raw,lambda b:b['records'][-1]['request'].update(target=['bot']),cold)
    changed('false-cached-feedback',training,lambda b:b['episodes'][0].update(verification_query=0),training_replay)
    changed('seeded-policy-start',training,lambda b:b['episodes'][0]['weights_before'].__setitem__(0,1.),training_replay)
    changed('invented-family-topology',training,lambda b:b['library'][0]['template']['nodes'][0].update(rule='induction'),training_replay)
    changed('altered-training-gradient',training,lambda b:b['episodes'][0]['learning']['gradient'].__setitem__(0,9.),training_replay)
    changed('altered-native-reward',training,lambda b:b['episodes'][0]['learning'].update(reward=0.),training_replay)
    changed('altered-final-policy',training,lambda b:b['weights'].__setitem__(0,9.),training_replay)
    return rejected
def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);data=load('native-inventory-001.json.gz');need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed universal native authority')
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOCS)):
        for n,p in data[field].items():need(sha(root/n)==p,'frozen producer dependency '+n)
    micro=load('proof-boundary-microcode-001.json.gz');template=json.loads((DOCS/'proof-boundary-001.json').read_text())['cases'][0]['initial'];(TMP/'code.bin').write_bytes(code_bytes(micro))
    for source,name in (('audit_tape_micro.cpp','native'),('micro_line_check.cpp','checker')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    training=json.loads(artifact(data['training']));t=training_replay(training);steps,requests=replay_native(training['records'],t['requests'],micro,template);queries=training['queries'];nodes=t['nodes'];events=t['events'];hints=t['hints'];print('fresh training, inventory and all native feedback checked',queries,flush=True)
    policy_path=DOCS/data['policy']['name'];need(sha(policy_path)==data['policy']['sha256'],'frozen policy artifact');policy=json.loads(policy_path.read_text());need(policy['features']==FEATURES and policy['weights']==training['weights'] and same(policy['library'],t['library']) and policy['training']==data['training'],'policy has precisely this fresh training provenance')
    methods=['base','zero','fixed','learned','no-family'];expected={(c['id'],m,r) for c in data['cases'] for m in methods for r in (1,2)};need(len(data['observations'])==len(expected) and {(o['case'],o['mode'],o['repetition']) for o in data['observations']}==expected,'all two-repetition cold controls');summaries=[];first=None
    for obs in data['observations']:
        raw=json.loads(artifact(obs['artifact']));spec=next(c for c in data['cases'] if c['id']==obs['case']);need(raw['case']==spec and (raw['mode'],raw['repetition'])==(obs['mode'],obs['repetition']),'external assertion and lane');index=data['cases'].index(spec);rotated=methods[index%5:]+methods[:index%5];order=rotated if obs['repetition']==1 else list(reversed(rotated));need(raw['method_order']==order and raw['search']['seed']==20000+100*index+obs['repetition']-1,'balanced method order and fresh seed');need(raw['search']['limits']==dict(attempts=spec.get('attempts',2000),seconds=30,proposal_limit=24,proposal_checks=2048),'same declared point budget')
        work=evaluation_replay(raw,t['library'],t['weights'],data['policy']['sha256']);n,accepted=replay_native(raw['records'],work['requests'],micro,template);steps+=n;requests.update(accepted);queries+=raw['queries'];nodes+=work['nodes'];events+=work['events'];hints+=work['hints']
        for k in ('status','queries','cold_seconds','verification_query'):need(raw.get(k)==obs.get(k),'cold observation summary '+k)
        need(raw['search']['metrics']==obs['metrics'],'all cold point/proposal counters');summaries.append(dict(case=obs['case'],mode=obs['mode'],repetition=obs['repetition'],status=raw['status'],queries=raw['queries'],nodes=work['nodes'],events=work['events'],hints=work['hints']))
        if first is None and raw['mode']=='learned' and raw['status']=='native_proof_discovered' and raw['search']['events']:first=raw
        print(obs['case'],obs['mode'],obs['repetition'],'all graph, guidance and native queries checked',flush=True)
    certificates=[]
    for row in data['certificates']:
        request=requests[row['request_sha256']];need(row['request']==request,'displayed certificate was discovered');boot=initial_for(micro,template,request);need(boot==row['initial'],'full accepting constructor');(TMP/'input.bin').write_bytes(input_bytes(boot));(TMP/'grammar.bin').write_bytes(artifact(row['grammar']));log=[json.loads(v) for v in artifact(row['events']).splitlines()];write_cuts([e['node'] for e in log if e['kind']=='fragment'],TMP/'observed.bin');checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
        need(checked['status']=='checked_response' and checked['result']=='accepted' and sha(TMP/'output.bin')==row['output_sha256'],'all full response derivations');root=json.loads((TMP/'root.json').read_text());need(root==json.loads(artifact(row['responses'])),'complete derived interfaces');chain=checked_chain(row,micro,log,root);need(chain['final']==row['output'],'actual native line contexts');certificates.append(dict(name=row['name'],case_id=row['case_id'],role=row['role'],request_sha256=row['request_sha256'],lines=chain['lines'],contexts=chain['contexts'],fragments=chain['fragments'],checked=checked));print(row['name'],'full accepting response derived',len(chain['lines']),flush=True)
    result=dict(version='native-inventory-audit-001',status='passed',producer_sha256=sha(DOCS/'native-inventory-001.json.gz'),source_sha256=sha(HERE/'audit_native_inventory_policy.py'),queries=queries,micro_steps=steps,point_nodes=nodes,policy_events=events,hints=hints,training=dict(episodes=24,families=len(t['library']),nodes=t['nodes'],events=t['events'],hints=t['hints'],weights=t['weights']),observations=summaries,certificates=certificates,mutations_rejected=mutations(training,first,t['library'],t['weights'],data['policy']['sha256']),seconds=time.perf_counter()-began,scope='Independent complete point graphs and original fallback, every bounded proposal pool and its exact expansions, every stochastic action/probability and all fresh policy updates; every recorded native computation rerun; every displayed accepting response DAG derived again. No universal compiler theorem or primitive-square GCTS claim.')
    (DOCS/'native-inventory-audit-001.json.gz').write_bytes(gzip.compress(packed(result),mtime=0));print('audit passed',queries,nodes,events,round(result['seconds'],3),flush=True)
if __name__=='__main__':main()
