"""Versioned independent audit after the pre-search API shorthand correction.

Imports no new family producer, worker, runner or search. Full-word placements
are reconstructed one at a time to avoid a multi-gigabyte aggregate model.
The independent native replay may overlap the production admission pipeline.
"""
import collections,copy,gzip,itertools,json,math,subprocess,time
from pathlib import Path
from audit_semantic_inventory import need,packed,same,encode,closure
import audit_semantic_inventory as N
from audit_first_order import domains
from hilbert_receptors_audit import catalog as base_catalog
from audit_catalog_receptors import parse_fields,check_tree
from audit_certificate_boundary import pin,sha,initial_for
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-promotion-family-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-hilbert-promotion-family-audit-v2-20261011')
def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
def changed(v,binding):
    if isinstance(v,list):
        if len(v)==3 and v[0]=='fun' and v[2]==[] and v[1] in binding:return ['fun',binding[v[1]],[]]
        return [changed(x,binding) for x in v]
    return {k:changed(x,binding) for k,x in v.items()} if isinstance(v,dict) else v
def reconstruct(plan,source):
    order=['A','B','C','u','v'];d={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m'],'v':['l','m']}
    need(plan['parameter_order']==order and plan['parameter_domains']==d,'full sorted parameter domain, including coincident bindings')
    basis,base=base_catalog(plan['cases'][0]);byname={x['name']:x['definition'] for x in base};template=source['blocks'][-1];prior=source['blocks'][:-1]
    need(len(prior)==2 and len(template['proof'])==4 and len(template['premises'])==2,'complete actual searched source')
    promoted=[];matches=[];seen={}
    for values in itertools.product(*(d[p] for p in order)):
        binding=dict(zip(order,values));names={};deps=[]
        for dep in prior:
            body=changed({k:v for k,v in dep.items() if k!='name'},binding);name='hilbert-'+pin(body)
            need(byname.get(name)==dict(name=name,**body),'every specialization has its exact independently declared base dependency')
            names[dep['name']]=name;deps.append(name)
        body=changed({k:v for k,v in template.items() if k!='name'},binding)
        for step in body['proof']:
            if step['rule']=='block':step['name']=names[step['name']]
        word=packed(body)
        if word not in seen:
            name='hilbert-promoted-'+pin(body);seen[word]=name
            promoted.append(dict(name=name,level=2,family='searched-incidence-transport',arguments=list(values),dependencies=deps,definition=dict(name=name,**body)))
        matches.append(dict(binding=binding,name=seen[word],decorated_word_hex=word.hex(),dependencies=deps))
    need(len(matches)==48 and len(promoted)==48,'all 48 exact decorated interfaces; no pruning by target or logical equivalence')
    groups={}
    for spec in plan['cases']:
        fs,ds=base_catalog(spec);need(same(ds,base),'same complete 28 baseline interfaces for every recipient')
        if spec['group'] not in groups:groups[spec['group']]=dict(basis=fs,representative=spec)
    theory=copy.deepcopy(plan['cases'][0]['theory']);theory['axioms']={'I.2-uniqueness':theory['axioms']['I.2-uniqueness']}
    actual=load(OUT/'catalog.json.gz')
    need(same(actual['base_definitions'],base) and same(actual['promoted_definitions'],promoted) and same(actual['definitions'],base+promoted) and same(actual['binding_records'],matches),'complete catalog and binding correspondence')
    need(actual['theory']==theory and actual['cases']==plan['cases'] and actual['bindings_before_dedup']==48 and actual['distinct_decorated_interfaces']==48 and actual['source_request_sha256']==pin(source),'retained theory/source/domain')
    for name,g in groups.items():need(actual['groups'][name]['basis']==g['basis'] and actual['groups'][name]['catalog']['basis']==g['basis'] and actual['groups'][name]['catalog']['variables']==[] and actual['groups'][name]['catalog']['schemes']==[],'complete ordinary formula envelope')
    return actual,base,promoted,groups,theory

def stream_model(spec,compiled,inventory,model):
    """Independently enumerate every full-word candidate; compare as a stream."""
    basis=compiled['basis'];ds=inventory['definitions'];defs={x['name']:x['definition'] for x in ds};modes={x['name']:i+1 for i,x in enumerate(ds)};arity=2;rows=[]
    for j in range(spec['length']):
        fs=[spec['target']] if j+1==spec['length'] else basis
        domain=domains(spec,compiled['catalog'],j)+[dict(rule='block',formula=f,name=d['name']) for f in fs for d in ds]
        domain.sort(key=lambda c:(c['rule'],packed(c['formula']),packed(c)));rows.append(domain)
    formula_words=sorted({packed(v) for v in basis+[spec['target']]+[p for d in ds for p in d['definition']['premises']]})
    command_words=sorted({packed(c) for row in rows for c in row})
    expected={kind:[dict(id=i,value=json.loads(w),word_hex=w.hex(),expanded_points=len(w)+1) for i,w in enumerate(words)] for kind,words in [('formula',formula_words),('command',command_words)]}
    ids={kind:{bytes.fromhex(e['word_hex']):e['id'] for e in values} for kind,values in expected.items()}
    def compressed(marks):
        fields,other=parse_fields(marks)
        return sorted(other+[((4*j+2,0 if kind=='formula' else 1),ids[kind][word]) for (j,kind),word in fields.items()])
    need(same(model['catalog'],expected) and same(model['domains'],rows) and model['command_counts']==list(map(len,rows)),'complete injective dictionary and all command domains')
    need(model['arity']==2 and model['mode_ids']==modes and same(model['roots'],[(4*j,r) for j in range(spec['length']) for r in range(4)]) and model['complete_words']==math.prod(map(len,rows)) and model['families_enabled'],'all roots, modes and possible words')
    need(same(model['initial_marks'],compressed(encode(spec['length']-1,'formula',spec['target']))),'fixed target boundary')
    placements=model['placements'];cursor=0;conflicts=[];full_points=compact_points=0;tauts={packed(f) for f in compiled['tautologies']}
    def check(key,entries,cmd,req,kind,**extra):
        nonlocal cursor,full_points,compact_points
        marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:conflicts.append(dict(key=key,reason='internally unequal markings'));return
            marks[p]=v
        full=sorted(marks.items());candidate=dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=compressed(full),slot=key[0],kind=kind,command=cmd,requirements=req,**extra)
        need(cursor<len(placements) and same(candidate,placements[cursor]),'every independently enumerated full-word/compact candidate '+str(key))
        cursor+=1;full_points+=len(full);compact_points+=len(candidate['marks'])
    for j,row in enumerate(rows):
        for k,c in enumerate(row):
            mode=modes[c['name']] if c['rule']=='block' else 0
            check((j,0,k,0),encode(j,'command',c)+encode(j,'formula',c['formula'])+[((4*j+2,90),mode)],c,[],'command')
        for k,c in enumerate(row):
            f=c['formula'];rule=c['rule'];mode=modes[c['name']] if rule=='block' else 0;entries=encode(j,'command',c)+encode(j,'formula',f)+[((4*j+2,90),mode)];req=[]
            if rule=='mp':
                for variant,a in enumerate(basis):
                    if a[0]=='imp' and a[2]==f:
                        req=[(c['antecedent'],a[1]),(c['implication'],a)]
                        check((j,1,k,variant),entries+[e for i,p in req for e in encode(i,'formula',p)],c,req,'guard')
                continue
            if rule=='axiom':valid=spec['theory']['axioms'][c['name']]==f
            elif rule=='refl':valid=f[0]=='eq' and f[1]==f[2]
            elif rule=='tautology':valid=packed(f) in tauts
            elif rule=='generalize':
                valid=f[0]=='all' and f[1]==c['variable']
                if valid:req=[(c['source'],f[2])]
            elif rule=='block':valid=defs[c['name']]['conclusion']==f
            else:valid=False
            if valid:check((j,1,k,0),entries+[e for i,p in req for e in encode(i,'formula',p)],c,req,'guard')
        for r in range(arity):
            check((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for d in ds:
                mode=modes[d['name']];ps=d['definition']['premises']
                if r>=len(ps):check((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):check((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',ps[r]),None,[(source,ps[r])],'lemma_input',input=r,mode=mode,source=source)
    need(cursor==len(placements) and same(model['conflicts'],conflicts),'all candidates and rejected internal conflicts accounted')
    return dict(status='passed',placements=cursor,full_mark_assignments=full_points,compact_mark_assignments=compact_points)

def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['sources'].items():need(sha(ROOT/p)==h,'all frozen sources '+p)
    for p,d in plan['data_dependencies'].items():need(sha(ROOT/p)==d['sha256'] and (ROOT/p).stat().st_size==d['bytes'],'all frozen inputs '+p)
    amendment=json.loads((OUT/'api-token-amendment.json').read_text())
    need(amendment['original_plan_sha256']==sha(OUT/'plan.json') and amendment['normalization']=={'expanded':'expanded-word'} and amendment['completed_observations_at_declaration']==0,'pre-search exact API normalization')
    for p,h in amendment['versioned_sources'].items():need(sha(ROOT/p)==h,'frozen versioned continuation source '+p)
    while True:
        if (OUT/'continuation-prefix.json').exists():
            receipt=json.loads((OUT/'continuation-prefix.json').read_text());live=json.loads((OUT/'progress.json').read_text())
            if live.get('api_token_correction',{}).get('prefix_sha256')==sha(OUT/'continuation-prefix.json'):break
        time.sleep(1)
    need(receipt['original_plan_sha256']==sha(OUT/'plan.json') and receipt['amendment_sha256']==sha(OUT/'api-token-amendment.json'),'continuation bound to original and amended source pins')
    for item in receipt['files'].values():need(sha(ROOT/item['path'])==item['sha256'] and (ROOT/item['path']).stat().st_size==item['bytes'],'exact preserved v1 native/audit/progress prefix')
    prior=load(ROOT/receipt['files']['native.json.gz']['path']);prior_audit=json.loads((ROOT/receipt['files']['audit.json']['path']).read_text())
    need(prior_audit['status']=='passed' and prior_audit['production_outcome']=='failed' and prior_audit['native_queries']==len(prior)==receipt['native_queries'] and receipt['observations']==3,'v1 complete independent native replay, no affected search performed')
    need(sum(r['result']['micro_steps'] for r in prior)==prior_audit['native_micro_steps'],'all preserved replay steps charged')
    while not (OUT/'catalog.json.gz').exists():time.sleep(1)
    source=load(ROOT/plan['source_native_record'])[0];need(source['result']['status']=='accepted' and json.loads((ROOT/plan['source_native_audit']).read_text())['native_outcome']=='accepted','independently replayed searched level-two source')
    catalog,base,promoted,groups,theory=reconstruct(plan,source['request']);taut=['imp',['bot'],['bot']];expected=[]
    def request(t,blocks,proof=None,target=None):return dict(protocol='gcts-fol-1',theory=t,blocks=blocks,proof=proof or [dict(rule='tautology',formula=taut)],target=taut if target is None else target)
    expected.append(('family_theory_admission',request(theory,[])))
    for d in base:expected.append(('family_base_admission',request(theory,[d['definition']])))
    base_byname={d['name']:d['definition'] for d in base}
    for d in promoted:expected.append(('family_promoted_admission',request(theory,[base_byname[n] for n in d['dependencies']]+[d['definition']])))
    for group,item in groups.items():
        expected.append(('recipient_theory_admission',request(item['representative']['theory'],[])))
        for f in item['basis']:expected.append(('recipient_tautology_guard',request(item['representative']['theory'],[],[dict(rule='tautology',formula=f)],f)))
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged palette')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro))
    cursor=steps=0;native_seconds=0.;records=[];fresh_native_seconds=0.;reused_native_queries=len(prior)
    while True:
        if (OUT/'native.json.gz').exists():records=load(OUT/'native.json.gz')
        while cursor<len(records):
            rec=records[cursor];need(rec['id']==cursor and rec['query_target']=='fixed_assertion' and rec['request_sha256']==pin(rec['request']),'exact sequential query binding')
            if cursor<len(expected):
                purpose,req=expected[cursor];need(rec['purpose']==purpose and rec['request']==req and rec['native_limit']==plan['admission_native_steps'],'complete predeclared admission/guard request')
            else:
                need(rec['purpose']=='family_discovered_whole' and rec['native_limit']==plan['whole_native_steps'],'whole-certificate gate')
                checkpoint=OUT/(rec['observation']+'.json.gz');need(sha(checkpoint)==rec['pre_certification_checkpoint_sha256'],'search tree checkpoint precedes whole certification')
                obs=load(checkpoint);spec=next(c for c in plan['cases'] if c['id']==obs['case_id']);ds=base if obs['language']=='level1' else base+promoted;inv=dict(definitions=ds,native_blocks=[d['definition'] for d in ds]);req=request(spec['theory'],closure(inv,obs['search']['proof']),obs['search']['proof'],spec['target']);need(rec['request']==req,'whole actual searched sequence and dependency closure')
            boot=initial_for(micro,boundary['cases'][0]['initial'],req);words=dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]);need(rec['boundary_words']==words,'independent complete tagged words')
            (TMP/'input.bin').write_bytes(input_bytes(boot));need(sha(TMP/'input.bin')==rec['input_sha256'],'all input bands')
            if cursor<len(prior):
                need(rec==prior[cursor],'every preserved native prefix record unchanged')
                response=rec['result'];native_seconds=prior_audit['native_replay_seconds']
            else:
                stage=time.perf_counter();response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['native_limit']));elapsed=time.perf_counter()-stage;fresh_native_seconds+=elapsed;native_seconds=prior_audit['native_replay_seconds']+fresh_native_seconds
            for key in ['status','micro_steps','physical_steps','micro_fnv64']:need(str(response[key])==str(rec['result'][key]),'independent native '+key)
            need(rec['result']['start']==88986,'actual parser start')
            if cursor>=len(prior):need(sha(TMP/'output.bin')==rec['output_sha256'],'all fresh output bands')
            if response['status'] in ['accepted','rejected']:
                try:logical=N.whole_replay(req)['status']
                except ValueError:logical='rejected'
                need(logical==response['status'],'audit-only logical cross-check')
            steps+=response['micro_steps'];cursor+=1
            save(OUT/'native-audit-progress.json',dict(status='running',native_queries=cursor,native_micro_steps=steps,native_replay_seconds=native_seconds,native_reused_queries=min(cursor,len(prior)),fresh_native_replay_seconds=fresh_native_seconds,seconds=time.perf_counter()-began));print('bound prior native replay' if cursor<=len(prior) else 'independent native',cursor,'of',len(records),flush=True)
        progress=json.loads((OUT/'progress.json').read_text()) if (OUT/'progress.json').exists() else {'status':'pending'}
        if progress['status'] in ['complete','failed'] or progress['status'].startswith(('unknown','rejected')):
            latest=load(OUT/'native.json.gz') if (OUT/'native.json.gz').exists() else []
            if cursor==len(latest):records=latest;break
        time.sleep(1)
    totals=collections.Counter();model_cache={};reports=[];cache={}
    if progress['status']=='complete':
        need(len(progress['base_admissions'])==28 and len(progress['promoted_admissions'])==48,'all interfaces admitted before any expanded search')
        compiled=load(OUT/'compiled.json.gz');inventories=load(OUT/'inventories.json.gz')
        for lang,ds in [('level1',base),('promoted',base+promoted)]:need(same(inventories[lang]['definitions'],ds) and inventories[lang]['interfaces']==[d['name'] for d in ds] and inventories[lang]['status']=='native_accepted','equal complete inventories within each language')
        for group,item in groups.items():
            c=compiled[group];need(c['basis']==item['basis'] and c['catalog']['basis']==item['basis'] and c['variables']==[] and c['admitted_schemes']==[] and c['status']=='complete','complete recipient catalog')
            qs=c['queries'];need(len(qs)==len(item['basis']) and c['tautologies']==[f for f,q in zip(item['basis'],qs) if records[q]['result']['status']=='accepted'],'native guards exactly')
        schedule=[(spec,rep,method) for spec in plan['cases'] for rep in plan['repetitions'] for method in plan['schedules'][str(rep)]];need(len(schedule)==len(progress['observations'])==64,'all predeclared recipient/language/policy runs')
        for summary,(spec,rep,method_id) in zip(progress['observations'],schedule):
            method=plan['methods'][method_id];tag=spec['id']+'-'+method_id+'-r'+str(rep);checkpoint=load(OUT/(tag+'.json.gz'));obs=load(OUT/(tag+'-final.json.gz'));r=obs['search'];inv=inventories[method['language']]
            need(summary['tag']==tag and obs['method']==method_id and obs['repetition']==rep and r['mode']==method['mode'] and r['feature_semantics']=={'expanded':'expanded-word'}.get(method['feature_semantics'],method['feature_semantics']) and r['seed']==plan['seed'] and r['limits']==plan['limits'] and not r['stochastic'],'all frozen held-out method settings')
            need(checkpoint['search']==r and checkpoint['model']==obs['model'] and obs['pre_certification_checkpoint_sha256']==sha(OUT/(tag+'.json.gz')),'preserved entire pre-certification checkpoint')
            model_core={k:v for k,v in obs['model'].items() if k!='compile_seconds'};word=packed(model_core);key=(spec['id'],method['language'])
            if key not in model_cache:model_cache[key]=(word,stream_model(spec,compiled[spec['group']],inv,obs['model']))
            else:need(word==model_cache[key][0],'exact same complete model at repeated equal inventory')
            tree=check_tree(spec,obs['model'],r,inv,plan['weights'] if method['mode']=='learned' else None);totals.update(tree)
            if r['proof'] is None:need(obs['native_query'] is None and not obs['cached_native_acceptance'] and obs['certification']=='no_proof','no proof claims from finite exhaustion/cutoff')
            else:
                q=obs['native_query'];req=request(spec['theory'],closure(inv,r['proof']),r['proof'],spec['target']);k=pin(req);need(records[q]['request']==req and obs['certification']==records[q]['result']['status'],'actual whole theorem outcome')
                if obs['cached_native_acceptance']:need(cache.get(k)==q and obs['certification']=='accepted','only exact earlier accepted certificate reuse')
                elif obs['certification']=='accepted':need(k not in cache,'fresh first certificate');cache[k]=q
            reports.append(dict(tag=tag,model=model_cache[key][1],tree=tree,status=r['status'],certification=obs['certification']));print('independent tree',tag,flush=True)
    result=dict(status='passed',version='hilbert-promotion-family-audit-v2',api_token_amendment_sha256=sha(OUT/'api-token-amendment.json'),continuation_prefix_sha256=sha(OUT/'continuation-prefix.json'),native_reused_queries=reused_native_queries,fresh_native_replay_seconds=fresh_native_seconds,prior_native_audit_seconds=prior_audit['seconds'],production_outcome=progress['status'],bindings=48,distinct_promoted_interfaces=48,base_interfaces=28,native_queries=cursor,native_micro_steps=steps,native_replay_seconds=native_seconds,seconds=time.perf_counter()-began,observations=reports,**dict(totals))
    save(OUT/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='observations'}),flush=True)
if __name__=='__main__':main()
