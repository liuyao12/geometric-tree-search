"""Saved-input/result audit, fresh full replay and adversarial corruptions.

Does not rerun E or native Wang computations. All proof checks use the separate
bounded certificate workers. Exact completed failed-validation attempt remains
historical evidence, even though the later adapter supports its preprocessing.
"""
import copy,json,pathlib,re,time
from external_prover_check import Parser,tokens,alpha,native_formula,records,formula_text
from external_prover_inputs import canonical,sha
from external_induction_tstp_run import OUT,ROOT,HERE,load,dump,unchanged,native_binding,operation

def exact_input(text,mapping):
    p=Parser(tokens(re.sub(r'^%[^\n]*','',text,flags=re.M)));got=[]
    while p.peek():
        p.take('fof');p.take('(');name=p.take();p.take(',');role=p.take();p.take(',');formula=p.formula();p.take(')');p.take('.')
        got.append((name,role,formula))
    if len(got)!=len(mapping['entries']):raise ValueError('complete original input census')
    for (n,r,f),e in zip(got,mapping['entries']):
        if n!=e['name'] or r!=e['role'] or alpha(f)!=alpha(native_formula(e['formula'],mapping)):raise ValueError('parsed original input AST/order binding')
    return len(got)

def main():
    began=time.perf_counter();plan=unchanged();summary=load(OUT/'summary.json');bundle=load(OUT/'bundle.json')
    if plan['attempt']!=3 or summary['status']!='complete' or len(summary['observations'])!=4:raise ValueError('complete new frozen measurement required')
    fresh_authority=native_binding(bundle)
    if canonical(fresh_authority)!=canonical(load(OUT/'native-authority.json')):raise ValueError('authoritative ninety-two-query binding')
    prior_manifest=load(OUT/'attempt-02/preservation.json')
    if sha((OUT/'attempt-02/preservation.json').read_bytes())!=plan['failed_validation_attempt_preservation_sha256']:raise ValueError('failed-attempt preservation manifest')
    for e in prior_manifest['files']:
        if sha((OUT/'attempt-02'/e['path']).read_bytes())!=e['sha256']:raise ValueError('preserved failed attempt changed')
    failed=load(OUT/'attempt-02/summary.json')
    if len(failed['observations'])!=4 or any(o['certificate_status']!='unknown' or o['szs_status']!='Theorem' or 'unsupported symbol-introducing transformation' not in o['proof_check']['result']['error'] for o in failed['observations']):raise ValueError('historical unknowns changed')
    entries=[]
    for item,original in zip(plan['inputs'],bundle['proposed_inputs']):
        path=pathlib.Path(item['input_path']);mapping=load(path.with_suffix('.mapping.json'))
        if sha(path.read_bytes())!=item['input_sha256'] or sha(path.with_suffix('.mapping.json').read_bytes())!=item['mapping_sha256']:raise ValueError('frozen input byte digest')
        if path.read_text()!=original['text'] or canonical(mapping['entries'])!=canonical(original['mapping']['entries']):raise ValueError('gate exact theory/library input binding')
        entries.append(exact_input(path.read_text(),mapping))
    if entries!=[4,70]:raise ValueError('four theory/seventy complete-library entries')
    tests=load(OUT/'tests.json')
    if tests['status']!='passed' or len(tests['cases'])!=51 or tests['target_prover_runs']!=0:raise ValueError('full scope/freshness/capture development fixtures')
    setup=load(OUT/'setup.json');pre=load(OUT/'interface-replays.json');all_ids=[e['id'] for e in bundle['interfaces']]
    if setup['status']!='complete' or pre['status']!='complete' or [r['id'] for r in setup['interfaces']]!=all_ids or [r['id'] for r in pre['results']]!=all_ids or len(all_ids)!=66:raise ValueError('all-interface check/replay gate')
    schema={s['id']:s['formula'] for s in bundle['schemas']};axioms=bundle['plan']['assertion']['theory']['axioms'];replays=[];mutations=[]
    for r,e,pr in zip(setup['interfaces'],bundle['interfaces'],pre['results']):
        request=r['request'];parents=[axioms[n] for n in e['axiom_dependencies']]+[schema[n] for n in e['induction_dependencies']]
        if request['parents']!=parents or request['child']!=e['formula'] or r['native_binding']!=e or r['measurement']['status']!='complete' or pr['measurement']['status']!='complete':raise ValueError('exact all-interface contextual dependency/native admission binding')
        expected_payload=dict(request,operation='interface',cpu_limit=30)
        if sha((OUT/(r['id']+'-setup.request.json')).read_bytes())!=r['measurement']['request_sha256'] or load(OUT/(r['id']+'-setup.request.json'))!=expected_payload or load(OUT/(r['id']+'-setup.result.json'))!=r['measurement']:raise ValueError('fresh setup original request/result file binding')
        answer=operation(dict(request,operation='interface-replay',saved=r['measurement']['result']),'audit-'+r['id']+'-interface-replay',30)
        if answer['status']!='complete':raise ValueError('independent all-interface certificate replay unknown')
        replays.append(dict(id=r['id'],measurement=answer))
    accepted=0;lines=0;boundaries=0;trees=0
    def reject(stem,payload):
        answer=operation(payload,'audit-corrupt-'+stem,300)
        if answer['status']=='complete':raise ValueError('corrupt proof passed '+stem)
        mutations.append(dict(id=stem,error=answer['result']['error'],measurement=answer))
    for o,ordered in zip(summary['observations'],plan['order']):
        if o['kind']!=ordered['kind'] or o['repetition']!=ordered['repetition'] or o['certificate_status']!='checked_complete_derivation' or o['proof_check']['status']!='complete' or o['proof_replay']['status']!='complete':raise ValueError('fresh complete target check/replay/order binding')
        stem='arithmetic-'+o['kind']+'-r'+str(o['repetition']);path=OUT/('arithmetic-'+o['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(stem+'.tstp')).read_text()
        if load(OUT/(stem+'.process.json'))!=o['e_measurement'] or text!=o['e_measurement']['stdout']:raise ValueError('actual full E stdout/result binding')
        for suffix,measurement in [('check',o['proof_check']),('replay',o['proof_replay'])]:
            request=load(OUT/(stem+'-'+suffix+'.request.json'))
            if sha((OUT/(stem+'-'+suffix+'.request.json')).read_bytes())!=measurement['request_sha256'] or request['output']!=text or request['mapping']!=mapping or request['input_path']!=str(path) or load(OUT/(stem+'-'+suffix+'.result.json'))!=measurement:raise ValueError('original bounded check/replay request/result binding')
        saved=o['proof_check']['result'];request=dict(operation='proof-replay',output=text,mapping=mapping,input_path=str(path),saved=saved)
        replay=operation(request,'audit-'+stem+'-proof-replay',300)
        if replay['status']!='complete':raise ValueError('fresh independent complete target replay unknown')
        if saved['used_lemma_inputs'] or o['used_lemma_inputs'] or o['proof_steps']!=19:raise ValueError('actual unused lemma inventory / displayed-line census')
        accepted+=1;lines+=saved['steps'];boundaries+=sum('reconstruction' in c for c in saved['checks']);replays.append(dict(id=stem,measurement=replay))
        # Actual trace mutations, retaining valid syntax and the real input path.
        rs=records(text);first=next(r for r in rs if r['source']['head']=='file' and r['role']!='conjecture');last=rs[-1]
        pattern=r'((?:fof|cnf)\('+re.escape(first['name'])+r',\s*'+re.escape(first['role'])+r',).*?(,\s*file\()'
        changed,count=re.subn(pattern,r'\g<1> $false\g<2>',text,count=1)
        if count!=1:raise ValueError('input corruption construction')
        last_line=next(line for line in text.splitlines() if line.startswith('cnf('+last['name']+','))
        empty=text.replace(last_line,'cnf('+last['name']+', '+last['role']+', $false, inference(cn,[status(thm)],[])).',1)
        wrong_relation=text.replace('inference(skolemize,[status(esa)]','inference(skolemize,[status(thm)]',1)
        for label,altered in [('changed-original-input',changed),('empty-contradiction-parent',empty),('wrong-compact-Skolem-relation',wrong_relation)]:reject(stem+'-'+label,dict(operation='proof',output=altered,mapping=mapping,input_path=str(path)))
        for i,ch in enumerate(saved['checks']):
            certificates=[]
            if 'proof' in ch:certificates.append(('proof',ch['proof']))
            if 'reconstruction' in ch:certificates.extend(('reconstruction-'+key,ch['reconstruction'][key]) for key in ('normalization','postprocessing'))
            for key,proof in certificates:
                if proof['certificate']['method']=='exact_alpha_NNF_equivalence':continue
                bad=copy.deepcopy(saved);destination=bad['checks'][i]['proof'] if key=='proof' else bad['checks'][i]['reconstruction'][key.split('-',1)[1]]
                destination['certificate']['check']['refutation']['tree']=['clause',999999]
                reject(stem+'-'+ch['name']+'-'+key+'-tree',dict(request,saved=bad));trees+=1
            if 'reconstruction' in ch:
                for label,mutate in [('witness-freshness',lambda b:b['checks'][i]['reconstruction']['witnesses'][0].update(symbol='f2')),('witness-scope',lambda b:b['checks'][i]['reconstruction']['witnesses'][0].update(dependencies=[[2]])),('context-registry',lambda b:b['checks'][i].update(registry_after_sha256='0'*64))]:
                    bad=copy.deepcopy(saved);mutate(bad);reject(stem+'-'+ch['name']+'-'+label,dict(request,saved=bad))
    result=dict(status='passed',successful_derivations=accepted,proof_lines=lines,checked_conservative_boundaries=boundaries,independent_interface_replays=66,exact_native_queries_bound=92,original_input_entry_counts=entries,preserved_unknown_derivations=4,development_fixtures=51,lemma_inputs_used=0,rejected_corruptions=len(mutations),rejected_logical_tree_corruptions=trees,replays=replays,mutations=mutations,seconds=time.perf_counter()-began,plan_sha256=sha((OUT/'plan.json').read_bytes()),summary_sha256=sha((OUT/'summary.json').read_bytes()),setup_sha256=sha((OUT/'setup.json').read_bytes()),failed_attempt_manifest_sha256=sha((OUT/'attempt-02/preservation.json').read_bytes()),source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [HERE/'external_induction_tstp_audit.py']},scope='Fresh bounded saved-certificate replay reconstructs inputs, all contextual interface dependencies, every displayed proof node, exact shared witness context and all semantic refutation trees. Reused authoritative native audits are bound to all92 exact computations; no native Wang execution or acceptance is asserted for E.')
    dump(OUT/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('replays','mutations')},indent=2))

if __name__=='__main__':main()
