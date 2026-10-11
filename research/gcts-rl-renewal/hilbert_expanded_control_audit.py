"""Independent complete model/tree audit and exact prior full-native reuse.

Imports only the unchanged independent reconstructors and native replay tools;
no control producer, worker, search, or logical search oracle is imported.
"""
import collections,copy,gzip,itertools,json,subprocess,time
from pathlib import Path
from audit_semantic_inventory import need,same,packed,pin,closure
import audit_semantic_inventory as N
from hilbert_receptors_audit import catalog as base_catalog
from hilbert_promotion_family_audit_v3 import stream_model,changed
from audit_catalog_receptors import check_tree,structural_nodes
from audit_certificate_boundary import sha,initial_for
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-expanded-control-20261011'
TMP=Path('/private/tmp/gcts-hilbert-expanded-control-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def family(plan,source,catalog):
    order=['A','B','C','u','v'];domains={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m'],'v':['l','m']}
    need(plan['parameter_order']==order and plan['parameter_domains']==domains,'all exact 48 sorted bindings')
    basis,base=base_catalog(plan['cases'][0]);byname={x['name']:x['definition'] for x in base};template=source['blocks'][-1];deps=source['blocks'][:-1]
    need(len(deps)==2 and len(template['proof'])==4 and len(template['premises'])==2,'actually searched 4-row higher source')
    promoted=[];matches=[];seen={}
    for values in itertools.product(*(domains[k] for k in order)):
        binding=dict(zip(order,values));names={};bounddeps=[]
        for d in deps:
            body=changed({k:v for k,v in d.items() if k!='name'},binding);name='hilbert-'+pin(body)
            need(name in byname and byname[name]==dict(name=name,**body),'native-admitted complete lower dependency')
            names[d['name']]=name;bounddeps.append(name)
        body=changed({k:v for k,v in template.items() if k!='name'},binding)
        for c in body['proof']:
            if c['rule']=='block':c['name']=names[c['name']]
        word=packed(body)
        if word not in seen:
            name='hilbert-promoted-'+pin(body);seen[word]=name
            promoted.append(dict(name=name,level=2,family='searched-incidence-transport',arguments=list(values),dependencies=bounddeps,definition=dict(name=name,**body)))
        matches.append(dict(binding=binding,name=seen[word],decorated_word_hex=word.hex(),dependencies=bounddeps))
    need(len(promoted)==len(matches)==48 and same(catalog['base_definitions'],base) and same(catalog['promoted_definitions'],promoted) and same(catalog['definitions'],base+promoted) and same(catalog['binding_records'],matches),'complete family identity and no omitted binding')
    return base,promoted
def request(spec,inv,proof):return dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(inv,proof),proof=proof,target=spec['target'])
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    need(plan['completed_observations_at_declaration']==0 and plan['mode']=='fixed' and plan['feature_semantics']=='expanded-word','predeclared missing weight control')
    for p,h in plan['sources'].items():need(sha(ROOT/p)==h,'frozen source '+p)
    for p,d in plan['data_dependencies'].items():need(sha(ROOT/p)==d['sha256'] and (ROOT/p).stat().st_size==d['bytes'],'exact complete prior export '+p)
    prefix=ROOT/plan['prior_prefix'];p=lambda suffix:Path(str(prefix)+suffix)
    prior=load(p('native.json.gz'));prior_audit=json.loads(p('audit.json').read_text());oldplan=json.loads(p('plan.json').read_text())
    oldprefix=load(p('resource_v1_native.json.gz'));oldaudit=json.loads(p('resource_v1_audit.json').read_text())
    need(prior_audit['status']=='passed' and prior_audit['production_outcome']=='complete' and len(prior)==prior_audit['native_queries']==142 and prior_audit['native_reused_queries']==128,'actual full prior native replay binding')
    need(oldaudit['status']=='passed' and oldaudit['native_queries']==len(oldprefix)==128 and prior[:128]==oldprefix and oldaudit['native_micro_steps']==sum(q['result']['micro_steps'] for q in oldprefix),'exact independently replayed original native prefix including original unknown')
    need(prior_audit['native_micro_steps']==sum(q['result']['micro_steps'] for q in prior) and prior_audit['native_replay_seconds']==oldaudit['native_replay_seconds']+prior_audit['fresh_native_replay_seconds'],'all original and continuation computation costs retained')
    need(plan['cases']==oldplan['cases'] and plan['seed']==oldplan['seed'] and plan['limits']==oldplan['limits'] and plan['paired_weights']==oldplan['weights'] and plan['whole_native_steps']==oldplan['whole_native_steps'],'only weighting differs from paired frozen run')
    from audit_semantic_inventory import FIXED
    need(plan['fixed_weights']==FIXED,'unchanged fixed weight control')
    source=load(p('source_native.json.gz'))[0];sourceaudit=json.loads(p('source_audit.json').read_text())
    need(source['result']['status']=='accepted' and sourceaudit['native_outcome']=='accepted','fully replayed source promotion')
    catalog=load(p('catalog.json.gz'));base,promoted=family(oldplan,source['request'],catalog)
    inventories=load(p('inventories.json.gz'));compiled=load(p('compiled.json.gz'))
    for lang,ds in [('level1',base),('promoted',base+promoted)]:need(same(inventories[lang]['definitions'],ds) and inventories[lang]['status']=='native_accepted' and len(ds)==(28 if lang=='level1' else 76),'exact complete equal inventory '+lang)
    for group,c in compiled.items():
        spec=next(s for s in oldplan['cases'] if s['group']==group);basis,_=base_catalog(spec)
        need(c['status']=='complete' and c['basis']==basis and c['catalog']['basis']==basis and c['variables']==[] and c['admitted_schemes']==[] and len(c['queries'])==len(basis),'complete formula and guard enumeration')
        need(c['tautologies']==[f for i,f in enumerate(basis) if prior[c['queries'][i]]['result']['status']=='accepted'],'actual native-admitted guards')
        for i,(f,q) in enumerate(zip(basis,c['queries'])):need(prior[q]['request']['target']==f and prior[q]['request']['theory']==spec['theory'] and prior[q]['group']==group and prior[q]['basis_index']==i and prior[q]['result']['status'] in ['accepted','rejected'],'all resolved exact recipient guards')
    expected=[]
    for case in oldplan['cases']:
        for rep in [1,2]:
            for lang in (['level1','promoted'] if rep==1 else ['promoted','level1']):expected.append((case['id'],lang,rep))
    need([(x['case_id'],x['language'],x['repetition']) for x in plan['schedule']]==expected and len(expected)==16,'complete separately declared 16-run schedule')
    micro=load(ROOT/'docs/research/gcts-rl-renewal/proof-boundary-microcode-001.json.gz');boundary=json.loads((ROOT/'docs/research/gcts-rl-renewal/proof-boundary-001.json').read_text())
    need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged primitive palette and checker')
    TMP.mkdir(parents=True,exist_ok=True);stage=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));native_setup=time.perf_counter()-stage
    # Bind every reusable prior whole acceptance to its actual prior searched
    # checkpoint, the complete dependency closure and the audited native input.
    prior_acceptances={};reused_input_seconds=0.
    for rec in prior:
        if rec['purpose']!='family_discovered_whole':continue
        need(rec['result']['status']=='accepted' and rec['native_limit']==plan['whole_native_steps'],'actual prior whole acceptance and unchanged gate')
        name=rec['observation'].replace('-','_');checkpoint=p(name+'.json.gz');obs=load(p(name+'_final.json.gz'));spec=next(s for s in plan['cases'] if s['id']==obs['case_id'])
        need(sha(checkpoint)==rec['pre_certification_checkpoint_sha256'] and obs['native_query']==rec['id'] and not obs['cached_native_acceptance'],'actual fresh prior source proof')
        req=request(spec,inventories[obs['language']],obs['search']['proof']);need(req==rec['request'] and pin(req)==rec['request_sha256'],'exact prior whole request and full dependency closure')
        stage=time.perf_counter();boot=initial_for(micro,boundary['cases'][0]['initial'],req);raw=input_bytes(boot);reused_input_seconds+=time.perf_counter()-stage
        import hashlib
        need(hashlib.sha256(raw).hexdigest()==rec['input_sha256'] and rec['result']['start']==88986,'actual parser, heap and complete prior input bands')
        need(rec['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'all prior tagged boundary words')
        prior_acceptances[rec['request_sha256']]=rec
    need(len(prior_acceptances)==7,'all seven reusable full-replayed whole certificates')
    cursor=steps=0;native_seconds=0.;fresh=[];replayed_bindings=[]
    while True:
        if (OUT/'native.json.gz').exists():fresh=load(OUT/'native.json.gz')
        while cursor<len(fresh):
            rec=fresh[cursor];checkpoint=OUT/(rec['observation']+'.json.gz');obs=load(checkpoint);spec=next(s for s in plan['cases'] if s['id']==obs['case_id']);req=request(spec,inventories[obs['language']],obs['search']['proof'])
            need(rec['id']==cursor and rec['purpose']=='fixed_expanded_discovered_whole' and rec['query_target']=='fixed_assertion' and rec['request']==req and rec['request_sha256']==pin(req) and rec['native_limit']==plan['whole_native_steps'],'exact fresh whole searched request')
            need(sha(checkpoint)==rec['pre_certification_checkpoint_sha256'] and rec['request_sha256'] not in prior_acceptances,'preserved pre-certification tree and no redundant prior computation')
            boot=initial_for(micro,boundary['cases'][0]['initial'],req);need(rec['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'complete fresh tagged words');(TMP/'input.bin').write_bytes(input_bytes(boot));need(sha(TMP/'input.bin')==rec['input_sha256'],'exact fresh heap and input bands')
            stage=time.perf_counter();response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['native_limit']));native_seconds+=time.perf_counter()-stage
            for k in ['status','micro_steps','physical_steps','micro_fnv64']:need(str(response[k])==str(rec['result'][k]),'fresh independent native '+k)
            need(sha(TMP/'output.bin')==rec['output_sha256'] and rec['result']['start']==88986,'every fresh output band and actual native parser')
            if response['status'] in ['accepted','rejected']:need(N.whole_replay(req)['status']==response['status'],'audit-only logical cross-check, never search input')
            replayed_bindings.append(dict(query=cursor,record_sha256=pin(rec),request_sha256=rec['request_sha256'],input_sha256=rec['input_sha256'],output_sha256=rec['output_sha256']))
            steps+=response['micro_steps'];cursor+=1;save(OUT/'native-audit-progress.json',dict(status='running',native_queries=cursor,native_micro_steps=steps,native_replay_seconds=native_seconds,replayed_bindings=replayed_bindings,seconds=time.perf_counter()-began));print('independent fresh native',cursor,flush=True)
        progress=json.loads((OUT/'progress.json').read_text()) if (OUT/'progress.json').exists() else {'status':'pending'}
        if progress['status'] in ['complete','failed'] and cursor==len(load(OUT/'native.json.gz')):break
        time.sleep(1)
    need(progress['status']=='complete' and len(progress['observations'])==16,'all 16 trials completed')
    totals=collections.Counter();models={};reports=[];new_acceptances={};reuse_counts=collections.Counter()
    for summary,item in zip(progress['observations'],plan['schedule']):
        tag=item['tag'];checkpoint=load(OUT/(tag+'.json.gz'));obs=load(OUT/(tag+'-final.json.gz'));r=obs['search'];spec=next(s for s in plan['cases'] if s['id']==item['case_id']);inv=inventories[item['language']];paired=load(ROOT/item['paired_final']);pairedcheckpoint=load(ROOT/item['paired_checkpoint']);pr=paired['search']
        need(all(obs[k]==v and summary[k]==v for k,v in item.items()) and r['mode']=='fixed' and r['feature_semantics']=='expanded-word' and r['weights']==plan['fixed_weights'] and r['seed']==plan['seed'] and r['limits']==plan['limits'] and not r['stochastic'],'actual predeclared fixed-expanded run')
        need(pr['mode']=='learned' and pr['feature_semantics']==r['feature_semantics'] and pr['weights']==plan['paired_weights'] and pr['seed']==r['seed'] and pr['limits']==r['limits'] and not pr['stochastic'],'paired treatment changes only weights')
        need(checkpoint['search']==r and checkpoint['model']==obs['model'] and obs['pre_certification_checkpoint_sha256']==sha(OUT/(tag+'.json.gz')) and pairedcheckpoint['search']==pr and pairedcheckpoint['model']==paired['model'] and paired['pre_certification_checkpoint_sha256']==sha(ROOT/item['paired_checkpoint']),'complete original and new trees saved before certification')
        core=lambda m:{k:v for k,v in m.items() if k!='compile_seconds'};word=packed(core(obs['model']));need(word==packed(core(paired['model'])),'exact same complete problem model across weight treatment')
        key=(spec['id'],item['language'])
        if key not in models:models[key]=(word,stream_model(spec,compiled[spec['group']],inv,obs['model']))
        else:need(word==models[key][0],'same complete model across deterministic repetitions')
        tree=check_tree(spec,obs['model'],r,inv,None);oldtree=check_tree(spec,paired['model'],pr,inv,plan['paired_weights']);totals.update(tree)
        binding=obs['native_binding']
        if r['proof'] is None:need(binding is None and obs['certification']=='no_proof','finite exhaustion or cutoff supplies no native proof')
        else:
            req=request(spec,inv,r['proof']);k=pin(req);need(binding['request_sha256']==k,'whole actual searched certificate binding')
            if binding['origin']=='prior':q=prior[binding['query']];need(k in prior_acceptances and prior_acceptances[k]==q,'reuse only actual full prior native replay')
            else:
                need(binding['origin']=='fresh' and 0<=binding['query']<len(fresh),'fresh native origin');q=fresh[binding['query']]
                if k in new_acceptances:need(new_acceptances[k]==binding['query'] and binding.get('independent_replayed_record_sha256')==pin(q),'reuse only exact independently replayed fresh request')
                elif q['result']['status']=='accepted':need(q['observation']==tag,'first fresh whole acceptance belongs to this observation');new_acceptances[k]=binding['query']
            need(q['request']==req and obs['certification']==q['result']['status'],'complete primitive proof and exact native whole outcome');reuse_counts[binding['origin']]+=1
        fcount=r['metrics'].get('attempts',0);lcount=pr['metrics'].get('attempts',0)
        reports.append(dict(**item,status=r['status'],certification=obs['certification'],fixed_attempts=fcount,learned_attempts=lcount,learned_minus_fixed_attempts=lcount-fcount,model=models[key][1],tree=tree,paired_tree=oldtree,
            identical_structural_tree=same(structural_nodes(r['tree']),structural_nodes(pr['tree'])),identical_proof=r['proof']==pr['proof'],fixed_search_seconds=r['seconds'],learned_search_seconds=pr['seconds'],native_binding=binding))
        print('independent fixed and paired learned trees',tag,flush=True)
    # The old milestone is immutable; no output may have rewritten its evidence.
    for rel,d in plan['data_dependencies'].items():need(sha(ROOT/rel)==d['sha256'],'prior evidence remains byte-exact '+rel)
    result=dict(status='passed',version='hilbert-expanded-control-audit-1',plan_sha256=sha(OUT/'plan.json'),production_outcome=progress['status'],observations=reports,complete_models=len(models),bindings=48,base_interfaces=28,promoted_interfaces=76,
        native_reused_prior_observations=reuse_counts['prior'],native_fresh_origin_observations=reuse_counts['fresh'],fresh_native_queries=cursor,fresh_native_micro_steps=steps,fresh_native_replay_seconds=native_seconds,
        prior_full_replay_binding=dict(native_queries=142,ledger_sha256=sha(p('native.json.gz')),audit_sha256=sha(p('audit.json')),native_micro_steps=prior_audit['native_micro_steps'],native_replay_seconds=prior_audit['native_replay_seconds']),
        native_setup_seconds=native_setup,prior_input_binding_seconds=reused_input_seconds,seconds=time.perf_counter()-began,**dict(totals))
    save(OUT/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='observations'}),flush=True)
if __name__=='__main__':main()
