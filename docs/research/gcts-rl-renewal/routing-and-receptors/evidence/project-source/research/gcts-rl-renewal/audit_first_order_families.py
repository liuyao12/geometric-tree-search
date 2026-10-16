"""Independent typed-family extraction, finite matching and full point inventory.

Does not import the new miner, point producer, case registry, worker or search.
The existing independent first-order syntax and literal graph auditors are used.
Full measured native computations are replayed from the true parser start.
"""
import collections,copy,gzip,hashlib,itertools,json,math,subprocess,time
from pathlib import Path
from audit_first_order import syntax,domains,compilation
from audit_semantic_inventory import need,packed,same,encode,verify_model,replay_native,close
from audit_prefix_failure_markings import extended_tree
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_certificate_boundary import pin,sha

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/first-order-families-20261011';TMP=Path('/private/tmp/gcts-first-order-families-audit-20261011')

def abstract(request,inventory,provenance):
    defs={d['name']:d for d in inventory['definitions']} if inventory else {};premises=[];commands=[];deps=set()
    for r in request['proof']:
        c=copy.deepcopy(r)
        if c['rule']=='axiom':
            f=request['theory']['axioms'][c['name']];need(f==c['formula'],'donor axiom identity')
            if f not in premises:premises.append(f)
            c=dict(rule='assumption',formula=f,index=premises.index(f))
        elif c['rule']=='block':
            d=defs[c.pop('name')];deps.add(d['family']);c['call']=dict(family=d['family'],arguments=d['arguments'])
        commands.append(c)
    params=[];values=[]
    def identify(kind,value,arity=None):
        descriptor=dict(kind=kind,**({'arity':arity} if kind=='predicate' else {}))
        i=next((i for i,(p,v) in enumerate(zip(params,values)) if p==descriptor and v==value),None)
        if i is None:i=len(params);params.append(descriptor);values.append(copy.deepcopy(value))
        return ['term_meta',i] if kind=='term' else ['predicate_meta',i,arity]
    def walk(v):
        if isinstance(v,dict):return {k:walk(a) for k,a in v.items()}
        if not isinstance(v,list):return v
        if len(v)==3 and v[0]=='fun' and not v[2]:return identify('term',v)
        if len(v)==3 and v[0]=='pred':return ['pred',identify('predicate',v[1],len(v[2])),[walk(t) for t in v[2]]]
        if len(v)==3 and v[0]=='predicate_argument':return ['predicate_argument',identify('predicate',v[1],v[2]),v[2]]
        return [walk(a) for a in v]
    template=walk(dict(premises=premises,conclusion=request['target'],proof=commands));body=dict(parameters=params,template=template,dependencies=sorted(deps))
    return dict(id=pin(body),**body,donor_values=values,provenance=provenance)

def substitute(v,args):
    if isinstance(v,dict):return {k:substitute(x,args) for k,x in v.items()}
    if not isinstance(v,list):return v
    if v and v[0] in ('term_meta','predicate_meta'):
        need(type(v[1]) is int and 0<=v[1]<len(args),'typed parameter index');a=args[v[1]]
        need(a[0]==('term_argument' if v[0]=='term_meta' else 'predicate_argument'),'parameter kind')
        if v[0]=='predicate_meta':need(a[2]==v[2],'predicate arity')
        return copy.deepcopy(a[1])
    return [substitute(x,args) for x in v]

def ground_inventory(library,spec,catalog):
    families={f['id']:f for f in library};need(len(families)==len(library),'unique families')
    defs={};order=[];active=set();interfaces=[]
    pools=lambda f:[[['term_argument',t] for t in catalog['equality_terms']] if p['kind']=='term' else
                     [['predicate_argument',n,a] for n,a in sorted(spec['theory']['predicates'].items()) if a==p['arity']] for p in f['parameters']]
    def unify(p,v,b,f,ps):
        if isinstance(p,list) and p and p[0] in ('term_meta','predicate_meta'):
            i=p[1];a=['term_argument',v] if p[0]=='term_meta' else ['predicate_argument',v,p[2]]
            if a not in ps[i]:return None
            if i in b:return b if b[i]==a else None
            return {**b,i:a}
        if isinstance(p,list):
            if not isinstance(v,list) or len(p)!=len(v):return None
            for a,z in zip(p,v):
                b=unify(a,z,b,f,ps)
                if b is None:return None
            return b
        return b if p==v else None
    def build(fid,args):
        need(fid in families,'known family dependency');f=families[fid];ps=pools(f)
        need(len(args)==len(ps) and all(a in p for a,p in zip(args,ps)),'complete typed ground argument')
        name='lemma'+pin(dict(family=fid,arguments=args))
        if name in defs:need(defs[name]['family']==fid and defs[name]['arguments']==args,'ground identity');return name
        need(name not in active,'acyclic dependency');active.add(name);g=substitute(f['template'],args);proof=[];level=1
        for row in g['proof']:
            c=copy.deepcopy(row)
            if c['rule']=='block':
                call=c.pop('call');dep=build(call['family'],call['arguments']);c['name']=dep;level=max(level,defs[dep]['level']+1)
            proof.append(c)
        native=dict(name=name,premises=g['premises'],conclusion=g['conclusion'],proof=proof)
        defs[name]=dict(name=name,family=fid,arguments=args,level=level,definition=native)
        active.remove(name);order.append(name);return name
    for f in library:
        ps=pools(f);matches=[{}]
        for pattern in f['template']['premises']+[f['template']['conclusion']]:
            following={}
            for b,v in itertools.product(matches,catalog['basis']):
                c=unify(pattern,v,b,f,ps)
                if c is not None:following[packed(sorted(c.items()))]=c
            matches=list(following.values())
        found={}
        for b in matches:
            missing=[i for i in range(len(ps)) if i not in b]
            for choices in itertools.product(*(ps[i] for i in missing)):
                complete={**b,**dict(zip(missing,choices))};args=[complete[i] for i in range(len(ps))];found[packed(args)]=args
        for k in sorted(found):interfaces.append(build(f['id'],found[k]))
    return dict(definitions=[defs[n] for n in order],interfaces=list(dict.fromkeys(interfaces)),native_blocks=[defs[n]['definition'] for n in order])

def closure(inventory,proof):
    defs={d['name']:d['definition'] for d in inventory['definitions']};needed=set();active=set()
    def visit(name):
        if name in needed:return
        need(name in defs and name not in active,'known acyclic call');active.add(name)
        for c in defs[name]['proof']:
            if c['rule']=='block':visit(c['name'])
        active.remove(name);needed.add(name)
    for c in proof:
        if c['rule']=='block':visit(c['name'])
    selected=[copy.deepcopy(d) for d in inventory['native_blocks'] if d['name'] in needed];seen=set()
    for d in selected:need(all(c['name'] in seen for c in d['proof'] if c['rule']=='block'),'dependency before call');seen.add(d['name'])
    need(seen==needed,'exact native call closure');return selected

def registry_binding(library,spec,compiled,inventory,records):
    expected=ground_inventory(library,spec,compiled['catalog'])
    for k in ('definitions','interfaces','native_blocks'):need(same(expected[k],inventory[k]),'complete typed inventory '+k)
    need(inventory['status']=='native_accepted' and len(inventory['admissions'])==len(expected['definitions']),'every matched definition admitted')
    requests={};taut=['imp',['bot'],['bot']]
    for d,a in zip(expected['definitions'],inventory['admissions']):
        need(a['name']==d['name'],'ground admission order');q=a['query'];rec=records[q]
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(expected,[dict(rule='block',name=d['name'])]),proof=[dict(rule='tautology',formula=taut)],target=taut)
        need(rec['purpose']=='first_order_family_definition' and rec['result']['status']=='accepted' and same(rec['request'],request),'whole ground definition native admission');requests[q]=request
    return requests

def rebuild(spec,compiled,inventory,arity,families):
    catalog=syntax(spec);need(same(catalog,compiled['catalog']),'independent syntax closure')
    defs={d['name']:d for d in inventory['definitions']};interfaces=[defs[n] for n in inventory['interfaces']] if families else []
    need(max([len(d['definition']['premises']) for d in interfaces]+[0])<=arity,'declared receptor count')
    modes={d['name']:i+1 for i,d in enumerate(interfaces)};ps=[];bad=[];ds=[]
    tauts={packed(f) for f in compiled['tautologies']};schemes={packed(c) for c in compiled['admitted_schemes']}
    def add(key,entries,c,req,kind,**extra):
        marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:bad.append(dict(key=key,reason='internally unequal markings'));return
            marks[p]=v
        ps.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(marks.items()),slot=key[0],kind=kind,command=c,requirements=req,**extra))
    for j in range(spec['length']):
        formulas=[spec['target']] if j+1==spec['length'] else catalog['basis'];rows=domains(spec,catalog,j)
        rows += [dict(rule='block',formula=f,name=d['name']) for f in formulas for d in interfaces]
        rows.sort(key=lambda c:(c['rule'],packed(c['formula']),packed(c)));ds.append(rows)
        for k,c in enumerate(rows):
            f=c['formula'];r=c['rule'];mode=modes[c['name']] if r=='block' else 0
            entries=encode(j,'command',c)+encode(j,'formula',f)+[((4*j+2,90),mode)];add((j,0,k,0),entries,c,[],'command')
            if r=='mp':
                for v,a in enumerate(catalog['basis']):
                    if a[0]=='imp' and a[2]==f:
                        req=[(c['antecedent'],a[1]),(c['implication'],a)];add((j,1,k,v),entries+[e for i,p in req for e in encode(i,'formula',p)],c,req,'guard')
            else:
                valid=False;req=[]
                if r=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif r=='tautology':valid=packed(f) in tauts
                elif r=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:req=[(c['source'],f[2])]
                elif r=='block':valid=defs[c['name']]['definition']['conclusion']==f
                else:valid=packed(c) in schemes
                if valid:add((j,1,k,0),entries+[e for i,a in req for e in encode(i,'formula',a)],c,req,'guard')
        for r in range(arity):
            add((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for d in interfaces:
                mode=modes[d['name']];premises=d['definition']['premises']
                if r>=len(premises):add((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):
                        req=[(source,premises[r])];add((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',premises[r]),None,req,'lemma_input',input=r,mode=mode,source=source)
    return dict(domains=ds,command_counts=list(map(len,ds)),arity=arity,mode_ids=modes,placements=sorted(ps,key=lambda p:p['key']),conflicts=bad,roots=[(4*j,r) for j in range(spec['length']) for r in range(2+arity)],complete_words=math.prod(map(len,ds)),initial_marks=encode(spec['length']-1,'formula',spec['target']),families_enabled=families)

def model_binding(spec,compiled,inventory,record,arity,families):
    r=rebuild(spec,compiled,inventory,arity,families);verify_model(record,r)
    for k in ('complete_words','initial_marks','families_enabled'):need(same(record[k],r[k]),'complete family model '+k)
    return r

def learning(before,events,value,baseline):
    gradient=[sum(e['features'][e['index']][k]-sum(p*v[k] for p,v in zip(e['probabilities'],e['features'])) for e in events)/max(1,len(events)) for k in range(10)]
    advantage=value-baseline
    return [w+.4*advantage*g for w,g in zip(before,gradient)],.9*baseline+.1*value,dict(reward=value,baseline_before=baseline,advantage=advantage,gradient=gradient)

def audit_observation(spec,compiled,inventory,obs,records,arity,families,weights,requests,cache,purpose,limits,mode,seed,stochastic=False):
    need(obs['search']['limits']==limits and obs['search']['mode']==mode and obs['search']['seed']==seed and obs['search']['stochastic']==stochastic,'predeclared budget, ordering and randomness')
    rebuilt=model_binding(spec,compiled,inventory,obs['model'],arity,families)
    checked=extended_tree(spec,rebuilt,obs['search'],inventory if families else [],weights if obs['search']['mode'] in ('learned','no-family') else None,rebuilt['initial_marks'])
    proof=obs['search']['proof'];q=obs['native_query']
    if proof is None:need(q is None and not obs['cached_native_acceptance'],'unknown has no acceptance');return checked
    request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(inventory,proof),proof=proof,target=spec['target']);key=pin(request)
    need(q is not None and records[q]['result']['status']=='accepted' and same(records[q]['request'],request),'whole searched certificate native acceptance')
    if obs['cached_native_acceptance']:need(cache.get(key)==q,'only earlier exact acceptance reused')
    else:need(q not in requests and key not in cache and records[q]['purpose']==purpose,'fresh whole searched certificate');requests[q]=request;cache[key]=q
    checked['proofs']=1;return checked

def main():
    started=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    for f,h in plan['source_sha256'].items():need(sha(ROOT/f)==h,'predeclared measured source '+f)
    for f,h in plan['prior_source_closure'].items():need(sha(ROOT/f)==h,'unchanged earlier source '+f)
    for f,r in plan['data_dependencies'].items():need(sha(ROOT/f)==r['sha256'] and (ROOT/f).stat().st_size==r['bytes'],'data binding '+f)
    records=json.loads(gzip.decompress((OUT/'native-records.json.gz').read_bytes()));training=json.loads(gzip.decompress((OUT/'training.json.gz').read_bytes()));requests={};cache={};library=[];totals=collections.Counter();old=json.loads(gzip.decompress((DOC/'first-order-native-001.json.gz').read_bytes()))
    need(len(training['donors'])==len(plan['donors']),'all declared reused donors')
    for donor,descriptor in zip(training['donors'],plan['donors']):
        need(donor['source_artifact']==descriptor['artifact'],'declared donor origin')
        source=json.loads(gzip.decompress((ROOT/descriptor['artifact']).read_bytes()));observation=next(o for o in source['observations'] if o['mode']=='base' and o['repetition']==1)
        need(observation['native_query']==donor['source_query'] and same(observation['search']['proof'],donor['request']['proof']),'donor actually found by prior GCTS')
        from audit_first_order import model_binding as prior_model_binding
        prior_model_binding(source['case'],source['compiled'],source['model']);extended_tree(source['case'],source['model'],observation['search'],[],None,source['model']['initial_marks'])
        q=old[donor['source_query']];need(q['result']['status']=='accepted' and same(q['request'],donor['request']),'audited prior native donor')
        expected=abstract(q['request'],None,donor['family']['provenance'])
        for k,v in expected.items():need(same(v,donor['family'][k]),'independently extracted seed family '+k)
        library.append(donor['family'])
    promotion=training['promotion'];spec=plan['promotion'];need(same(promotion['case'],spec),'predeclared promotion assertion')
    requests.update(compilation(spec,promotion['compiled'],records));requests.update(registry_binding(library,spec,promotion['compiled'],promotion['inventory'],records))
    counts=audit_observation(spec,promotion['compiled'],promotion['inventory'],promotion['observation'],records,plan['arity'],True,None,requests,cache,'first_order_family_promotion',plan['search_limits'],'fixed',plan['seed']);totals.update(counts)
    proof=promotion['observation']['search']['proof'];need(proof is not None,'dependent family requires discovered proof');q=records[promotion['observation']['native_query']]
    expected=abstract(q['request'],promotion['inventory'],promotion['family']['provenance'])
    for k,v in expected.items():need(same(v,promotion['family'][k]),'independent dependent-family extraction '+k)
    need(expected['dependencies'],'promoted family actually calls lower families');library.append(promotion['family']);need(same(library,training['library']),'exact learned family library')
    for item,spec in zip(training['cases'],plan['training_cases']):
        need(same(item['case'],spec),'predeclared training assertion');requests.update(compilation(spec,item['compiled'],records));requests.update(registry_binding(library,spec,item['compiled'],item['inventory'],records))
    need(len(training['cases'])==len(plan['training_cases']) and len(training['episodes'])==plan['episodes'],'all training cases and episodes')
    weights=[0.]*10;baseline=0.
    for i,episode in enumerate(training['episodes']):
        item=training['cases'][i%len(training['cases'])];spec=item['case'];need(episode['id']==i and episode['case']==spec['id'] and close(episode['weights_before'],weights),'fresh zero-start training order')
        counts=audit_observation(spec,item['compiled'],item['inventory'],episode['observation'],records,plan['arity'],True,weights,requests,cache,'first_order_family_training',plan['training_limits'],'learned',plan['seed']+i,True);totals.update(counts)
        search=episode['observation']['search'];accepted=search['proof'] is not None;growth=(2+plan['arity'])*len(search['proof']) if accepted else 0
        work=search['metrics'].get('validation_checks',0)+search['metrics'].get('sample_pair_tests',0);value=growth/max(1,search['metrics'].get('attempts',0))-.25*min(1.,work/100000)
        after,baseline,update=learning(weights,search['events'],value,baseline)
        need(close(after,episode['weights_after']) and abs(baseline-episode['baseline_after'])<=1e-12,'exact REINFORCE update')
        for k in ('reward','baseline_before','advantage'):need(abs(update[k]-episode['learning'][k])<=1e-12,'actual policy '+k)
        need(close(update['gradient'],episode['learning']['gradient']),'policy gradient');weights=after
    need(close(weights,training['weights']) and abs(baseline-training['baseline'])<=1e-12,'frozen learned policy')
    cases=[]
    for spec in plan['cases']:
        raw=json.loads(gzip.decompress((OUT/(spec['id']+'.json.gz')).read_bytes()));need(same(raw['case'],spec),'predeclared recipient assertion')
        requests.update(compilation(spec,raw['compiled'],records));requests.update(registry_binding(library,spec,raw['compiled'],raw['inventory'],records));seen=set()
        need([(o['lane'],o['repetition']) for o in raw['observations']]==[(l,r) for r in plan['repetitions'] for l in plan['schedules'][str(r)]],'predeclared rotated method order')
        for saved in raw['observations']:
            obs=dict(saved,model=raw['models'][saved['model_id']])
            lane=obs['lane'];rep=obs['repetition'];need((lane,rep) not in seen,'unique isolated recipient');seen.add((lane,rep));method=plan['lanes'][lane]
            need(obs['search']['mode']==method['mode'],'declared ordering control')
            checked=audit_observation(spec,raw['compiled'],raw['inventory'],obs,records,plan['arity'],method['families'],weights,requests,cache,'first_order_family_final',plan['search_limits'],method['mode'],plan['seed']);totals.update(checked)
        need(seen=={(l,r) for l in plan['lanes'] for r in plan['repetitions']},'all paired recipient lanes')
        cases.append(dict(id=spec['id'],observations=len(seen),ground_definitions=len(raw['inventory']['definitions']),interfaces=len(raw['inventory']['interfaces'])))
    countermodels={}
    for identifier,model in plan.get('countermodels',{}).items():
        spec=next(s for s in plan['cases'] if s['id']==identifier);domain=model['domain'];need(domain and len(set(domain))==len(domain),'finite nonempty interpretation')
        def term(t,env):
            if t[0]=='var':return env[t[1]]
            value=model['functions'][t[1]];need(spec['theory']['functions'][t[1]]==0 and not t[2] and value in domain,'total constant interpretation');return value
        def truth(f,env):
            if f[0]=='bot':return False
            if f[0]=='eq':return term(f[1],env)==term(f[2],env)
            if f[0]=='pred':
                args=[term(t,env) for t in f[2]];rows=model['predicates'][f[1]];need(all(len(r)==spec['theory']['predicates'][f[1]] and all(v in domain for v in r) for r in rows),'predicate interpretation');return args in rows
            if f[0]=='all':return all(truth(f[2],{**env,f[1]:v}) for v in domain)
            if f[0]=='not':return not truth(f[1],env)
            if f[0]=='imp':return not truth(f[1],env) or truth(f[2],env)
            if f[0]=='and':return truth(f[1],env) and truth(f[2],env)
            if f[0]=='or':return truth(f[1],env) or truth(f[2],env)
            raise ValueError('unknown logical connective')
        need(all(truth(a,{}) for a in spec['theory']['axioms'].values()) and not truth(spec['target'],{}),'all axioms true and target false in supplied finite model')
        countermodels[identifier]=dict(domain_size=len(domain),axioms_true=True,target_false=True)
    need(set(requests)==set(range(len(records))),'every new native computation exactly bound')
    TMP.mkdir(parents=True,exist_ok=True);micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native palette')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro))
    import audit_semantic_inventory as native_audit
    native_audit.TMP=TMP;steps,accepted=replay_native(records,requests,micro,boundary['cases'][0]['initial'],plan['native_steps'])
    result=dict(status='passed',version='first-order-families-audit-001',cases=cases,countermodels=countermodels,families=len(library),levels=sorted({d['level'] for item in training['cases'] for d in item['inventory']['definitions']}),episodes=len(training['episodes']),native_queries=len(records),micro_steps=steps,accepted_requests=len(accepted),seconds=time.perf_counter()-started,**dict(totals))
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
