"""Independent complete recipient/model/tree and budgeted native replay audit.

No transfer author, producer, worker, search or logical oracle is imported.
The finite countermodel and host logical replay are audit-only diagnostics.
"""
import collections,copy,gzip,json,subprocess,time
from pathlib import Path
from audit_semantic_inventory import need,same,packed,pin,closure,FIXED
import audit_semantic_inventory as N
from hilbert_receptors_audit import catalog as base_catalog
from hilbert_expanded_control_audit import family
from hilbert_promotion_family_audit_v3 import stream_model
from audit_catalog_receptors import check_tree
from audit_certificate_boundary import sha,initial_for
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'
TMP=Path('/private/tmp/gcts-hilbert-boundary-transfer-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def recipients():
    """Literal recipient reconstruction, independent of transfer authoring."""
    const=lambda s:['fun',s,[]]
    pred=lambda s,*ts:['pred',s,list(ts)]
    imp=lambda a,b:['imp',a,b]
    def common(a,b,u,v):
        ps=[pred('Point',a),pred('Point',b),pred('Line',u),pred('Line',v),['not',['eq',a,b]],pred('Incident',a,u),pred('Incident',b,u),pred('Incident',a,v),pred('Incident',b,v)]
        out=ps[-1]
        for p in reversed(ps[:-1]):out=['and',p,out]
        return out
    a,b,u,v=[['var',s] for s in ['point0','point1','line0','line1']]
    i2=imp(common(a,b,u,v),['eq',u,v])
    for s in reversed(['point0','point1','line0','line1']):i2=['all',s,i2]
    p,q,r,l,m=map(const,['P','Q','R','l','m']);ready=pred('Point',r);out=[]
    for group,left,right,short,enough in [('delayed-common',l,m,5,6),('coupled-reverse',m,l,6,7)]:
        h=common(p,q,left,right);inc=pred('Incident',r,left)
        axioms={'I.2-uniqueness':i2,'readiness':ready,'common-from-readiness':imp(ready,h)}
        axioms['extra-incidence' if group=='delayed-common' else 'incidence-from-common']=inc if group=='delayed-common' else imp(h,inc)
        theory=dict(functions={s:0 for s in ['P','Q','R','l','m']},predicates=dict(Point=1,Line=1,Incident=2),schemas=[],axioms=axioms)
        for boundary,length in [('short',short),('sufficient',enough)]:out.append(dict(id='transfer-'+group+'-'+boundary,group=group,boundary=boundary,length=length,theory=copy.deepcopy(theory),sorts={'point':['P','Q','R'],'line':['l','m']},uniqueness_points=['P','Q'],target=pred('Incident',r,right),receptor_common=h,receptor_incidence=inc))
    return out
def countermodel(spec):
    """Removing I.2 invalidates the implication; never a producer input."""
    domain=list(range(5));constants={'P':0,'Q':1,'R':2,'l':3,'m':4};points={0,1,2};lines={3,4}
    left=3 if spec['group']=='delayed-common' else 4
    incident={(0,3),(1,3),(0,4),(1,4),(2,left)}
    def term(t,e):return e[t[1]] if t[0]=='var' else constants[t[1]]
    def truth(f,e):
        k=f[0]
        if k=='all':return all(truth(f[2],{**e,f[1]:x}) for x in domain)
        if k=='eq':return term(f[1],e)==term(f[2],e)
        if k=='pred':
            ts=tuple(term(t,e) for t in f[2]);return ts[0] in points if f[1]=='Point' else ts[0] in lines if f[1]=='Line' else ts in incident
        if k=='not':return not truth(f[1],e)
        if k=='and':return truth(f[1],e) and truth(f[2],e)
        if k=='imp':return not truth(f[1],e) or truth(f[2],e)
        raise ValueError('unexpected countermodel syntax')
    values={n:truth(f,{}) for n,f in spec['theory']['axioms'].items()};target=truth(spec['target'],{})
    need(not values['I.2-uniqueness'] and all(v for n,v in values.items() if n!='I.2-uniqueness') and not target,'I.2-independent exact premise countermodel')
    return dict(status='passed',domain=domain,constants=constants,Point=sorted(points),Line=sorted(lines),Incident=sorted(incident),axiom_values=values,target=target,scope='Audit-only removed-I.2 interpretation; no negative search or altered inventory.')
def request(spec,inv,proof):return dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(inv,proof),proof=proof,target=spec['target'])
def dependencies(proof,i):
    c=proof[i];refs=[]
    if c['rule']=='mp':refs=[c['antecedent'],c['implication']]
    elif c['rule']=='block':refs=c['inputs']
    elif c['rule']=='generalize':refs=[c['source']]
    need(all(0<=j<i for j in refs),'strict earlier source indices')
    return {i}|set().union(*(dependencies(proof,j) for j in refs))
def derived_inputs(spec,inv,proof):
    """Describe actual searched derivations without requiring a proof path."""
    byname={d['name']:d for d in inv['definitions']};reports=[]
    need(spec['receptor_common'] not in spec['theory']['axioms'].values(),'common receptor input is not supplied as an axiom')
    if spec['group']=='coupled-reverse':need(spec['receptor_incidence'] not in spec['theory']['axioms'].values(),'second reverse receptor input is not supplied as an axiom')
    for i,c in enumerate(proof):
        if c['rule']!='block' or byname[c['name']]['level']!=2:continue
        d=byname[c['name']];ps=d['definition']['premises'];sources=c['inputs']
        need(len(sources)==len(ps) and [proof[j]['formula'] for j in sources]==ps,'actual higher receptor source boundary')
        exact=ps==[spec['receptor_common'],spec['receptor_incidence']] and c['formula']==spec['target']
        row=dict(row=i,name=c['name'],arguments=d['arguments'],inputs=sources,exact_recipient_receptor=exact,input_derivations=[])
        for j in sources:row['input_derivations'].append(dict(row=j,rule=proof[j]['rule'],ancestor_rows=sorted(dependencies(proof,j))))
        if exact:
            need(proof[sources[0]]['rule']=='mp','fresh actual common input derived by primitive MP')
            if spec['group']=='coupled-reverse':need(proof[sources[1]]['rule']=='mp' and sources[0] in dependencies(proof,sources[1]),'second reverse input derived from first common input')
        reports.append(row)
    return reports
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    need(plan['completed_observations_at_declaration']==0 and plan['seed']==72000 and plan['limits']==dict(attempts=600,seconds=15,proposal_limit=24,proposal_checks=2048),'fresh declared bounded searches')
    need(plan['guard_native_steps']==20_000_000_000 and plan['whole_native_steps']==10_000_000_000 and plan['native_production_seconds_ceiling']==1200 and plan['fixed_weights']==FIXED,'exact native/ordering gates')
    for p,h in plan['sources'].items():need(sha(ROOT/p)==h,'frozen source '+p)
    for p,d in plan['data_dependencies'].items():need(sha(ROOT/p)==d['sha256'] and (ROOT/p).stat().st_size==d['bytes'],'frozen input '+p)
    fresh_specs=recipients()
    need(len(plan['cases'])==4 and all(all(s[k]==v for k,v in t.items()) for s,t in zip(plan['cases'],fresh_specs)),'exact new theories/targets/derived-premise boundaries')
    schedule=[]
    for ci,s in enumerate(fresh_specs):
        methods=[(l,m) for l in ['level1','promoted'] for m in ['base','fixed','learned']];methods=methods[ci:]+methods[:ci]
        for lang,mode in methods:schedule.append(dict(tag=s['id']+'-'+lang+'-'+mode+'-expanded',case_id=s['id'],language=lang,mode=mode,feature_semantics='expanded-word'))
    need(plan['schedule']==schedule and len(schedule)==24,'all complete predeclared controls')
    p=lambda suffix:ROOT/(plan['prior_prefix']+suffix);cp=lambda suffix:ROOT/(plan['prior_control_prefix']+suffix)
    oldplan=json.loads(p('plan.json').read_text());prior=load(p('native.json.gz'));prior_audit=json.loads(p('audit.json').read_text());oldprefix=load(p('resource_v1_native.json.gz'));prefixaudit=json.loads(p('resource_v1_audit.json').read_text())
    controls=load(cp('native.json.gz'));controlaudit=json.loads(cp('audit.json').read_text())
    need(prior_audit['status']=='passed' and prior_audit['production_outcome']=='complete' and prior_audit['native_queries']==len(prior)==142 and prior_audit['native_reused_queries']==128,'actual prior complete family replay')
    need(prefixaudit['status']=='passed' and len(oldprefix)==prefixaudit['native_queries']==128 and prior[:128]==oldprefix and prefixaudit['native_micro_steps']==sum(q['result']['micro_steps'] for q in oldprefix),'preserved original replay including resource unknown')
    need(prior_audit['native_micro_steps']==sum(q['result']['micro_steps'] for q in prior) and prior_audit['native_replay_seconds']==prefixaudit['native_replay_seconds']+prior_audit['fresh_native_replay_seconds'],'exact full replay cost binding')
    need(controlaudit['status']=='passed' and controlaudit['fresh_native_queries']==len(controls)==2 and controlaudit['fresh_native_micro_steps']==sum(q['result']['micro_steps'] for q in controls),'all prior fixed-control whole replay')
    need(plan['weights']==oldplan['weights'],'same frozen transferred policy, no training')
    policy=json.loads((DOC/'first-order-families-reader-001.json').read_text());need(policy['training']['weights']==plan['weights'] and len(policy['training']['episodes'])==plan['prior_cost_provenance']['inherited_policy_episodes'],'actual inherited training provenance')
    source=load(p('source_native.json.gz'))[0];sourceaudit=json.loads(p('source_audit.json').read_text())
    need(source['result']['status']=='accepted' and sourceaudit['native_outcome']=='accepted','actual searched source promotion native replay')
    prior_catalog=load(p('catalog.json.gz'));base,promoted=family(oldplan,source['request'],prior_catalog);inventories=load(p('inventories.json.gz'))
    for lang,ds in [('level1',base),('promoted',base+promoted)]:need(same(inventories[lang]['definitions'],ds) and inventories[lang]['native_blocks']==[d['definition'] for d in ds] and inventories[lang]['interfaces']==[d['name'] for d in ds] and inventories[lang]['status']=='native_accepted','all complete unchanged interfaces '+lang)
    declared=load(OUT/'declared-catalog.json.gz');need(declared['cases']==plan['cases'] and declared['bindings']==48 and not declared['inventory_change'] and same(declared['definitions'],base+promoted) and same(declared['binding_records'],prior_catalog['binding_records']),'complete unchanged family and declaration')
    groups={}
    for s in fresh_specs:
        fs,ds=base_catalog(s);need(same(ds,base),'all complete base interfaces under new recipient')
        if s['group'] not in groups:groups[s['group']]=dict(basis=fs,representative=s)
    for group,g in groups.items():
        actual=declared['groups'][group];need(actual['basis']==g['basis'] and actual['catalog']['basis']==g['basis'] and actual['catalog']['variables']==[] and actual['catalog']['schemes']==[],'complete independently reconstructed formula envelope')
    library_theory=copy.deepcopy(fresh_specs[0]['theory']);library_theory['axioms']={'I.2-uniqueness':library_theory['axioms']['I.2-uniqueness']}
    need(prior_catalog['theory']==library_theory,'unchanged I.2-only library signature/theory')
    taut=['imp',['bot'],['bot']]
    def admission(t,ds,f=taut):return dict(protocol='gcts-fol-1',theory=t,blocks=ds,proof=[dict(rule='tautology',formula=f)],target=f)
    admission_requests=[admission(library_theory,[])]+[admission(library_theory,[d['definition']]) for d in base]
    byname={d['name']:d['definition'] for d in base}
    admission_requests += [admission(library_theory,[byname[n] for n in d['dependencies']]+[d['definition']]) for d in promoted]
    library=prior[:77];need(len(admission_requests)==77 and all(q['request']==req and q['result']['status']=='accepted' and q['request_sha256']==pin(req) for q,req in zip(library,admission_requests)),'every reused full inventory admission, no sampled bindings')
    costs=plan['prior_cost_provenance'];need(costs['library_native_queries']==77 and costs['library_native_micro_steps']==sum(q['result']['micro_steps'] for q in library) and costs['library_native_production_seconds']==sum(q['seconds'] for q in library),'all inherited library admissions charged')
    need(costs['source_promotion_native_seconds']==source['seconds'] and costs['source_promotion_replay_seconds']==sourceaudit['seconds'],'separate actual source promotion costs')
    for outkey,inkey in [('inherited_policy_discovery_and_matching_seconds','discovery_and_matching_seconds'),('inherited_policy_training_seconds','training_seconds')]:need(costs[outkey]==policy['training'][inkey],'inherited policy component cost')
    need(costs['inherited_policy_full_pilot_seconds']==policy['pilot_seconds'] and costs['inherited_policy_full_audit_seconds']==policy['audit']['seconds'],'overlapping aggregate policy costs retained')
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged checker/palette/heap')
    TMP.mkdir(parents=True,exist_ok=True);stage=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));native_setup=time.perf_counter()-stage
    def boot_binding(q):
        boot=initial_for(micro,boundary['cases'][0]['initial'],q['request']);raw=input_bytes(boot)
        import hashlib
        need(hashlib.sha256(raw).hexdigest()==q['input_sha256'] and q['result']['start']==88986,'exact native input heap/parser bands')
        need(q['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'all exact tagged native boundary words')
        return raw
    stage=time.perf_counter()
    for q in library:boot_binding(q)
    prior_acceptances={}
    for origin,records,path in [('prior-family',prior,p),('prior-control',controls,cp)]:
        for q in records:
            if q['purpose'] not in ['family_discovered_whole','fixed_expanded_discovered_whole']:continue
            need(q['result']['status']=='accepted' and q['native_limit']==plan['whole_native_steps'],'actual whole prior acceptance')
            tag=q['observation'].replace('-','_');checkpoint=path(tag+'.json.gz');obs=load(path(tag+'_final.json.gz'));spec=next(s for s in oldplan['cases'] if s['id']==obs['case_id'])
            need(sha(checkpoint)==q['pre_certification_checkpoint_sha256'],'actual preserved prior search checkpoint')
            need(request(spec,inventories[obs['language']],obs['search']['proof'])==q['request'] and q['request_sha256']==pin(q['request']),'actual full prior certificate and dependency closure')
            boot_binding(q);prior_acceptances[(origin,q['id'])]=q
    prior_input_seconds=time.perf_counter()-stage;need(len(prior_acceptances)==9,'all seven family and two fixed-control replayed whole inputs')
    expected=[]
    for group,g in groups.items():
        expected.append(dict(purpose='transfer_theory_admission',group=group,request=admission(g['representative']['theory'],[])))
        for i,f in enumerate(g['basis']):expected.append(dict(purpose='transfer_tautology_guard',group=group,basis_index=i,request=admission(g['representative']['theory'],[],f)))
    cursor=steps=0;native_seconds=logical_seconds=0.;fresh=[];replayed=[];production_bill=0.;overshoots=[]
    while True:
        if (OUT/'native.json.gz').exists():fresh=load(OUT/'native.json.gz')
        while cursor<len(fresh):
            q=fresh[cursor];need(q['id']==cursor and q['query_target']=='fixed_assertion' and q['request_sha256']==pin(q['request']),'sequential actual native request')
            if cursor<len(expected):
                e=expected[cursor];need(all(q[k]==v for k,v in e.items()) and q['native_limit']==plan['guard_native_steps'],'entire declared guard prefix')
            else:
                need(q['purpose']=='transfer_discovered_whole' and q['native_limit']==plan['whole_native_steps'],'whole searched certificate gate')
                checkpoint=OUT/(q['observation']+'.json.gz');obs=load(checkpoint);spec=next(s for s in fresh_specs if s['id']==obs['case_id'])
                need(sha(checkpoint)==q['pre_certification_checkpoint_sha256'] and request(spec,inventories[obs['language']],obs['search']['proof'])==q['request'],'saved actual search before complete native certification')
            budget=q['production_budget'];after=production_bill+q['seconds'];overshoot=max(0.,after-plan['native_production_seconds_ceiling'])
            need(production_bill<plan['native_production_seconds_ceiling'] and budget==dict(prior_native_seconds=production_bill,query_seconds=q['seconds'],after_native_seconds=after,ceiling_seconds=1200,overshoot_seconds=overshoot,checked_before_query=True),'ceiling checked before every actual query and overshoot charged')
            if overshoot:overshoots.append(dict(query=q['id'],**budget))
            production_bill=after;(TMP/'input.bin').write_bytes(boot_binding(q));stage=time.perf_counter();response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',q['native_limit']));native_seconds+=time.perf_counter()-stage
            for k in ['status','micro_steps','physical_steps','micro_fnv64']:need(str(response[k])==str(q['result'][k]),'full fresh native replay '+k)
            need(sha(TMP/'output.bin')==q['output_sha256'],'every native output band including unknown')
            if response['status'] in ['accepted','rejected']:
                stage=time.perf_counter()
                try:logical=N.whole_replay(q['request'])['status']
                except ValueError:logical='rejected'
                logical_seconds+=time.perf_counter()-stage;need(logical==response['status'],'independent audit-only logical cross-check')
            replayed.append(dict(query=cursor,record_sha256=pin(q),request_sha256=q['request_sha256'],input_sha256=q['input_sha256'],output_sha256=q['output_sha256']))
            steps+=response['micro_steps'];cursor+=1;save(OUT/'native-audit-progress.json',dict(status='running',native_queries=cursor,native_micro_steps=steps,native_replay_seconds=native_seconds,replayed_bindings=replayed,seconds=time.perf_counter()-began));print('independent transfer native',cursor,flush=True)
        progress=json.loads((OUT/'progress.json').read_text()) if (OUT/'progress.json').exists() else {'status':'pending'}
        if progress['status'] in ['complete','failed','unknown_preparation','rejected_theory'] and cursor==len(load(OUT/'native.json.gz')):break
        time.sleep(1)
    need(progress['plan_sha256']==sha(OUT/'plan.json') and progress['native_queries']==cursor and progress['native_production_seconds']==production_bill and progress['native_budget_overshoots']==overshoots,'all actual production costs and overshoots preserved')
    for block in progress['native_budget_blocks']:need(block['prior_native_seconds']>=1200 and block['ceiling_seconds']==1200,'every refused query recorded as budget unknown')
    totals=collections.Counter();models={};reports=[];acceptances={};reuse=collections.Counter()
    need(progress['status'] in ['complete','unknown_preparation','rejected_theory'],'meaningful terminal outcome, never silently failed')
    if progress['status']=='complete':
        need(len(progress['observations'])==24 and cursor>=len(expected),'all guards before all 24 searches');compiled=load(OUT/'compiled.json.gz')
        need(load(OUT/'catalog.json.gz')==declared and load(OUT/'inventories.json.gz')==inventories,'no post-declaration grammar or inventory mutation')
        for group,g in groups.items():
            c=compiled[group];qs=c['queries'];need(c['basis']==g['basis'] and c['catalog']==declared['groups'][group]['catalog'] and c['status']=='complete' and c['variables']==[] and c['admitted_schemes']==[] and len(qs)==len(g['basis']),'complete actual native compiled grammar')
            need(c['tautologies']==[f for f,q in zip(g['basis'],qs) if fresh[q]['result']['status']=='accepted'] and fresh[c['theory_query']]['result']['status']=='accepted','exact accepted complete guards')
            for i,(f,q) in enumerate(zip(g['basis'],qs)):need(fresh[q]['group']==group and fresh[q]['basis_index']==i and fresh[q]['request']['target']==f and fresh[q]['result']['status'] in ['accepted','rejected'],'all native guards resolved before searching')
        for summary,item in zip(progress['observations'],schedule):
            tag=item['tag'];checkpoint=load(OUT/(tag+'.json.gz'));obs=load(OUT/(tag+'-final.json.gz'));r=obs['search'];spec=next(s for s in fresh_specs if s['id']==item['case_id']);inv=inventories[item['language']]
            need(all(obs[k]==v and summary[k]==v for k,v in item.items()) and r['mode']==item['mode'] and r['feature_semantics']=='expanded-word' and r['seed']==plan['seed'] and r['limits']==plan['limits'] and not r['stochastic'],'exact unchanged reference search policy/settings')
            need(r['weights']==(None if item['mode']=='base' else plan['fixed_weights'] if item['mode']=='fixed' else plan['weights']),'only declared policy weights')
            need(checkpoint['search']==r and checkpoint['model']==obs['model'] and sha(OUT/(tag+'.json.gz'))==obs['pre_certification_checkpoint_sha256'],'complete exact tree checkpoint before certificate work')
            core={k:v for k,v in obs['model'].items() if k!='compile_seconds'};word=packed(core);key=(spec['id'],item['language'])
            if key not in models:models[key]=(word,stream_model(spec,compiled[spec['group']],inv,obs['model']))
            else:need(word==models[key][0],'same complete inventory/model across equal-policy controls')
            tree=check_tree(spec,obs['model'],r,inv,plan['weights'] if item['mode']=='learned' else None);totals.update(tree);binding=obs['native_binding'];inputs=[]
            if r['proof'] is None:need(binding is None and obs['certification']=='no_proof','finite exhaustion/cutoff is no certificate')
            else:
                req=request(spec,inv,r['proof']);k=pin(req);inputs=derived_inputs(spec,inv,r['proof'])
                if binding is None:need(obs['certification']=='unknown_native_cost_ceiling' and any(b.get('observation')==tag for b in progress['native_budget_blocks']),'point proof remains unknown if whole native budget unavailable')
                else:
                    need(binding['request_sha256']==k,'exact searched whole request binding')
                    if binding['origin'] in ['prior-family','prior-control']:
                        need((binding['origin'],binding['query']) in prior_acceptances,'only actual prior full-replay acceptance');q=prior_acceptances[(binding['origin'],binding['query'])]
                    else:
                        need(binding['origin']=='fresh' and 0<=binding['query']<len(fresh),'fresh exact native origin');q=fresh[binding['query']]
                        if k in acceptances:need(acceptances[k]==binding['query'] and binding.get('independent_replayed_record_sha256')==pin(q),'fresh acceptance reuse follows actual independent full replay')
                        elif q['result']['status']=='accepted':need(q['observation']==tag,'first fresh acceptance belongs to this searched observation');acceptances[k]=binding['query']
                    need(q['request']==req and obs['certification']==q['result']['status'],'actual full proof and native acceptance or unknown');reuse[binding['origin']]+=1
            need(summary['status']==r['status'] and summary['certification']==obs['certification'] and summary['attempts']==r['metrics'].get('attempts',0),'authoritative observation ledger')
            reports.append(dict(**item,status=r['status'],certification=obs['certification'],attempts=r['metrics'].get('attempts',0),model=models[key][1],tree=tree,derived_receptors=inputs,native_binding=binding));print('independent complete transfer tree',tag,flush=True)
    else:
        need(not progress['observations'] and cursor<=len(expected),'incomplete guards stop before any search')
        if progress['native_outcome']=='unknown_native_cost_ceiling':need(production_bill>=1200 and progress['native_budget_blocks'],'preparation cost-ceiling unknown is preserved')
        else:need(fresh[-1]['result']['status']==progress['native_outcome'] and (progress['native_outcome'].startswith('unknown') or progress['status']=='rejected_theory'),'actual unresolved native preparation remains unknown')
    for rel,d in plan['data_dependencies'].items():need(sha(ROOT/rel)==d['sha256'],'all earlier frozen evidence remains unchanged '+rel)
    result=dict(status='passed',version='hilbert-boundary-transfer-audit-1',plan_sha256=sha(OUT/'plan.json'),production_outcome=progress['status'],observations=reports,complete_models=len(models),bindings=48,base_interfaces=28,promoted_interfaces=76,
        complete_guard_queries=len(expected),fresh_native_queries=cursor,fresh_native_micro_steps=steps,fresh_native_production_seconds=production_bill,native_budget_overshoots=overshoots,fresh_native_replay_seconds=native_seconds,audit_only_logical_crosscheck_seconds=logical_seconds,
        native_setup_seconds=native_setup,prior_input_binding_seconds=prior_input_seconds,prior_cost_provenance=costs,native_observation_origins=dict(reuse),
        prior_full_replay_binding=dict(family_ledger_sha256=sha(p('native.json.gz')),family_audit_sha256=sha(p('audit.json')),family_native_queries=142,family_native_micro_steps=prior_audit['native_micro_steps'],family_native_replay_seconds=prior_audit['native_replay_seconds'],control_ledger_sha256=sha(cp('native.json.gz')),control_audit_sha256=sha(cp('audit.json')),control_native_queries=2,control_native_micro_steps=controlaudit['fresh_native_micro_steps'],control_native_replay_seconds=controlaudit['fresh_native_replay_seconds']),
        removed_I2_countermodels={g:countermodel(v['representative']) for g,v in groups.items()},seconds=time.perf_counter()-began,**dict(totals))
    save(OUT/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['observations','removed_I2_countermodels']}),flush=True)
if __name__=='__main__':main()
