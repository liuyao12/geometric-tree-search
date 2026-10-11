"""Fresh bounded setup, then balanced E runs only after every readiness gate.

Preserves the earlier design gate and all published controls. Original native
admission/audit costs are bound as reuse, not rerun or counted as fresh work.
"""
import argparse,base64,copy,gzip,json,pathlib,platform,re,subprocess,sys,time
from external_prover_inputs import canonical,sha
from external_prover_run import execute

ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'.gcts-active/external-induction-tstp-20261011';GATE=ROOT/'.gcts-active/external-induction-20261011';NATIVE=ROOT/'.gcts-active/induction-receptors-20261011'
E=pathlib.Path('/private/tmp/gcts-external-eprover-20261011/PROVER/eprover')
AUDITS={'recovery-audit.json':'509e12e9f39f5e2c702f02afbe8c634ccf62ab4c59e998227a0088080484bcfe','compaction-audit.json':'715b2b2464d78083dad1372a311e92ab46fb7836d253f99a9a5d68e007534b10','attempt-01/audit.json':'82b1736ed1c19757cd47466627abc5546c9c2eecf5ddc5dd571ab600730fea10'}

def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def preserved():
    results=[]
    for folder in ('external-prover-20261011','external-hilbert-20261011','external-induction-20261011'):
        manifest=load(ROOT/'.gcts-active'/folder/'export.json')
        for e in manifest['files']:
            if sha((ROOT/e['path']).read_bytes())!=e['sha256']:raise ValueError('preserved artifact changed '+e['path'])
            results.append(e)
    if len(results)!=27:raise ValueError('exact twenty-seven preserved artifacts')
    return results

def native_binding(bundle):
    documents={};artifacts={}
    for name,want in AUDITS.items():
        raw=(NATIVE/name).read_bytes()
        if sha(raw)!=want:raise ValueError('authoritative audit changed '+name)
        if json.loads(raw)['status']!='passed':raise ValueError('native audit incomplete')
        documents[name]=json.loads(raw);artifacts[name]=dict(sha256=want,bytes=len(raw),base64=base64.b64encode(raw).decode())
    ledger=json.loads(gzip.decompress(base64.b64decode(bundle['source_files']['native-records.json.gz']['base64'])))
    replay={r['query']:r for r in documents['recovery-audit.json']['native_replays']}
    if set(replay)!=set(range(75)) or len(ledger)!=75:raise ValueError('complete native replay census')
    for r in ledger:
        audited=replay[r['id']]
        if r['result']['status']!=audited['status'] or r['result']['micro_steps']!=audited['micro_steps'] or sha(canonical(r['request']))!=r['request_sha256']:raise ValueError('native replay/query binding')
    if sum(r['result']['micro_steps'] for r in ledger)!=documents['recovery-audit.json']['native_micro_steps']:raise ValueError('recovery steps binding')
    prior=load(NATIVE/'attempt-01/native-records.json.gz');prior_audit=documents['attempt-01/audit.json']
    if len(prior)!=prior_audit['queries'] or sum(r['result']['micro_steps'] for r in prior)!=prior_audit['native_micro_steps'] or prior[-1]['result']['status']!='unknown_step_budget':raise ValueError('prior exact unknown replay binding')
    compact=load(NATIVE/'compaction-native.json.gz');cp=load(NATIVE/'compaction-plan.json');cs=load(NATIVE/'compaction-summary.json')
    if cp['original_request_sha256']!=ledger[74]['request_sha256'] or len(compact)!=2:raise ValueError('compaction original source binding')
    for mode,record,audit,summary in zip(cp['variants'],compact,documents['compaction-audit.json']['variants'],cs['variants']):
        if mode!=audit['mode'] or mode!=summary['mode'] or record['request']['theory']!=ledger[74]['request']['theory'] or record['request']['target']!=ledger[74]['request']['target'] or sha(canonical(record['request']))!=record['request_sha256']:raise ValueError('unchanged compacted theory/target/request')
        if record['result']['status']!=audit['native_status'] or record['result']['micro_steps']!=audit['native_micro_steps'] or not audit['whole_input_output_sha256_matched']:raise ValueError('compaction full native replay binding')
        if summary['request_sha256']!=record['request_sha256']:raise ValueError('compaction summary request binding')
    if compact[1]['result']['status']!='accepted' or len(compact[1]['request']['proof'])!=30:raise ValueError('accepted compacted native target')
    for name in ('attempt-01/native-records.json.gz','compaction-native.json.gz','compaction-plan.json','compaction-summary.json'):
        raw=(NATIVE/name).read_bytes();artifacts[name]=dict(sha256=sha(raw),bytes=len(raw),base64=base64.b64encode(raw).decode())
    return dict(status='completed_authoritative_native_replay_exactly_bound',query_count=92,definition_count=66,
                original_native_seconds=sum(r['seconds'] for rs in (prior,ledger,compact) for r in rs),native_micro_steps=sum(d['native_micro_steps'] for d in documents.values()),independent_native_audit_seconds=sum(d['seconds'] for d in documents.values()),
                accepted_compacted_request_sha256=compact[1]['request_sha256'],exact_artifacts=artifacts,
                scope='Passed source audits are authoritative reused evidence, now bound to every original query status/step count and exact compacted original theory/target/request. No expensive native computation was rerun. Earlier gate-freeze pending wording remains historical.')

def operation(payload,stem,wall=30):
    began=time.perf_counter();input_path=OUT/(stem+'.request.json');output_path=OUT/(stem+'.worker.json');dump(input_path,dict(payload,cpu_limit=wall));stderr=OUT/(stem+'.stderr')
    reason=None
    with stderr.open('w') as err:
        proc=subprocess.Popen([sys.executable,str(HERE/'external_induction_tstp_worker.py'),str(input_path),str(output_path)],stdout=subprocess.DEVNULL,stderr=err)
        while proc.poll() is None:
            if time.perf_counter()-began>wall:reason='external wall cutoff';proc.kill();break
            time.sleep(.01)
        proc.wait()
    answer=load(output_path) if output_path.exists() else dict(status='unknown',result=dict(status='unknown',error=reason or 'worker exited without complete output'))
    if reason:answer=dict(status='unknown',result=dict(status='unknown',error=reason))
    answer.update(process_wall_seconds=time.perf_counter()-began,process_exit_code=proc.returncode,request_sha256=sha(input_path.read_bytes()))
    dump(OUT/(stem+'.result.json'),answer);return answer

def prepare():
    OUT.mkdir(parents=True,exist_ok=True);began=time.perf_counter();old=preserved();bundle=load(ROOT/'docs/research/gcts-rl-renewal/external_induction_gate_inventory.json.gz');authority=native_binding(bundle)
    prior=load(OUT/'attempt-02/preservation.json')
    for entry in prior['files']:
        if sha((OUT/'attempt-02'/entry['path']).read_bytes())!=entry['sha256']:raise ValueError('frozen failed-validation attempt changed')
    inputs=[]
    for item in bundle['proposed_inputs']:
        if sha(item['text'])!=item['sha256'] or len(item['mapping']['entries']) not in (4,70):raise ValueError('exact full proposed inputs')
        kind='library' if len(item['mapping']['entries'])==70 else 'theory';path=OUT/('arithmetic-'+kind+'.p');path.write_text(item['text']);mapping=copy.deepcopy(item['mapping']);mapping.update(case=bundle['plan']['assertion']['id'],lane=item['lane'])
        dump(path.with_suffix('.mapping.json'),mapping);inputs.append(dict(kind=kind,input_path=str(path),input_sha256=sha(path.read_bytes()),mapping_sha256=sha(path.with_suffix('.mapping.json').read_bytes()),entries=len(mapping['entries'])))
    dump(OUT/'bundle.json',bundle);dump(OUT/'native-authority.json',authority);dump(OUT/'preserved.json',old)
    sources=[HERE/n for n in ('external_induction_tstp_check.py','external_induction_tstp_tests.py','external_induction_tstp_worker.py','external_induction_tstp_run.py','external_induction_skolem.py','external_prover_check.py','external_prover_inputs.py','external_prover_run.py','external_prover_worker.py')]
    options=['--auto','--proof-object','--tstp-format','--cpu-limit=60','--memory-limit=1024','--resources-info','--print-statistics']
    plan=dict(version='external-induction-tstp-plan-3',status='frozen_before_all_interface_checks_and_target_execution',source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},inputs=inputs,gate_plan_sha256=sha((GATE/'gate-plan.json').read_bytes()),native_authority_sha256=sha((OUT/'native-authority.json').read_bytes()),preserved_artifacts=old,failed_validation_attempt_preservation_sha256=sha((OUT/'attempt-02/preservation.json').read_bytes()),development_calibration_sha256=sha((OUT/'calibration-theory-r1.json').read_bytes()),
              prover_source_commit='3b7afc70fe77d3118bb95144c4735ca45f5f31cf',prover_binary_sha256=sha(E.read_bytes()),prover_version=subprocess.run([str(E),'--version'],capture_output=True,text=True,check=True).stdout.strip(),options=options,repetitions=2,order=[dict(repetition=r,kind=k) for r,kinds in ((1,['theory','library']),(2,['library','theory'])) for k in kinds],
              interface_wall_cutoff_seconds=30,per_logical_step_wall_cutoff_seconds=30,whole_certificate_worker_wall_cutoff_seconds=300,certificate_worker_RSS_ceiling_bytes=1073741824,certificate_worker_RSS_sampling_seconds=.025,certificate_memory_supervision='Daemon reads own resource.RUSAGE_SELF high-water RSS every25ms and exits after an observed ceiling breach. Process accounting is platform-aware; sampling is not an instantaneous allocation limit.',prover_wall_cutoff_seconds=65,
              interface_policy='Before target execution, all66 explicitly closed interfaces receive fresh independently replayable consequence certificates from their exact exported axiom/schema dependencies. Full native admission/replay is authoritative reused evidence. Unchecked or unknown setup prevents E recipient runs.',
              witness_policy='One shared model-preserving context; all exact original signatures and all earlier introductions reserved. Isolated FOF fof_skolemize or a restricted unary compact annotation may introduce witnesses. Compact annotation requires exactly one esa Skolem node, only thm NNF/rename/quantifier-shift/distribution wrappers and one named parent. A separate explicit parent-NNF / unchanged strict lexical witness extension / independently certified displayed-child derivation establishes the printed compound relation. It does not assert verbatim E unprinted implementation intermediates. At most six existential/name assignments; exact occurrence/arity/dependency census and globally fresh functions. Fresh predicates/definitions, unsupported chains and omitted/vacuous witnesses fail closed.',
              logical_policy='Every ordinary child is independently certified from its actual previous leaf parents, via uniform propositional abstraction, exact alpha-NNF equivalence, or finite Herbrand/EUF refutation. Each returned complete certificate must pass fresh full replay. Unsupported/incomplete checks never count as target proof.',
              theory_scope=bundle['plan']['theory_scope'],search_scope=bundle['plan']['search_scope'],library_scope=bundle['plan']['library_scope'],comparison_scope='Finite declared induction predicates, same exact4/70FOL inputs, broader E calculus and universally closed lemma interfaces than the native fixed seven-row/four-node-term catalog. E proof objects use a separate checker and never claim native Wang acceptance. No formal speed ratio.',
              cost_policy='Charge exact export/provenance setup, every fresh-worker interface check, fresh E binary execution, worker startup/checking and memory, full returned-certificate replay and corruption audit separately. Native admission/audits and pinned E build are explicitly disclosed reuse.',
              preparation_seconds=time.perf_counter()-began,target_executions_at_freeze=0,attempt=3,prior_preparation='attempt-01 preserves ps sandbox-permission failure with unknown parent elapsed time and no E target run. attempt-02 preserves all66 checked interfaces/fresh replays and four balanced E Theorem traces with UNKNOWN independent checks because compact symbol introduction was unsupported. New adapter was developed after those traces; one saved theory trace received a separately retained development calibration, which is not the fresh controlled measurement.')
    dump(OUT/'plan.json',plan);print('PLAN FROZEN',plan['preparation_seconds'],flush=True)

def unchanged():
    plan=load(OUT/'plan.json');preserved()
    for name,want in plan['source_sha256'].items():
        if sha((ROOT/name).read_bytes())!=want:raise ValueError('measurement source changed '+name)
    if sha(E.read_bytes())!=plan['prover_binary_sha256']:raise ValueError('pinned binary changed')
    return plan

def setup():
    plan=unchanged();tests=load(OUT/'tests.json')
    if tests['status']!='passed':raise ValueError('full-adapter fixtures not passed')
    bundle=load(OUT/'bundle.json');mapping=load(OUT/'arithmetic-library.mapping.json');entries={e['name']:e for e in mapping['entries']};schema={s['id']:s['formula'] for s in bundle['schemas']};axioms=bundle['plan']['assertion']['theory']['axioms'];results=[];began=time.perf_counter()
    for entry in bundle['interfaces']:
        parents=[axioms[n] for n in entry['axiom_dependencies']]+[schema[n] for n in entry['induction_dependencies']]
        expected=entries[entry['id']]
        if expected['formula']!=entry['formula']:raise ValueError('exact full interface AST binding')
        answer=operation(dict(operation='interface',parents=parents,child=entry['formula'],mapping=mapping),entry['id']+'-setup',plan['interface_wall_cutoff_seconds'])
        results.append(dict(id=entry['id'],axiom_dependencies=entry['axiom_dependencies'],induction_dependencies=entry['induction_dependencies'],native_binding=entry,request=dict(parents=parents,child=entry['formula'],mapping=mapping),measurement=answer))
        status='complete' if answer['status']=='complete' else 'unknown_setup_gate'
        dump(OUT/'setup.json',dict(status=status if len(results)==66 or status!='complete' else 'running',interfaces=results,seconds=time.perf_counter()-began))
        print('INTERFACE',entry['id'],answer['status'],answer.get('operation_seconds'),flush=True)
        if status!='complete':return
    print('ALL66 INTERFACES CHECKED',time.perf_counter()-began,flush=True)

def run():
    plan=unchanged();setup=load(OUT/'setup.json')
    if setup['status']!='complete' or len(setup['interfaces'])!=66 or any(r['measurement']['status']!='complete' for r in setup['interfaces']):raise ValueError('all-interface gate remains open')
    # Setup certificates are freshly replayed before invoking any target prover.
    began=time.perf_counter();interface_replays=[]
    for r in setup['interfaces']:
        request=dict(r['request'],operation='interface-replay',saved=r['measurement']['result']);answer=operation(request,r['id']+'-pre-run-replay',30)
        interface_replays.append(dict(id=r['id'],measurement=answer))
        dump(OUT/'interface-replays.json',dict(status='running' if answer['status']=='complete' and len(interface_replays)<66 else ('complete' if answer['status']=='complete' else 'unknown'),results=interface_replays,seconds=time.perf_counter()-began))
        if answer['status']!='complete':return
    observations=[];start=time.perf_counter()
    for item in plan['order']:
        kind=item['kind'];path=OUT/('arithmetic-'+kind+'.p');mapping=load(path.with_suffix('.mapping.json'));stem='arithmetic-'+kind+'-r'+str(item['repetition'])
        measured=execute([str(E),*plan['options'],str(path)],plan['prover_wall_cutoff_seconds']);text=measured['stdout'];(OUT/(stem+'.tstp')).write_text(text);dump(OUT/(stem+'.process.json'),measured)
        status=re.search(r'SZS status (\w+)',text);answer=operation(dict(operation='proof',output=text,mapping=mapping,input_path=str(path)),stem+'-check',300)
        if answer['status']=='complete':replay=operation(dict(operation='proof-replay',output=text,mapping=mapping,input_path=str(path),saved=answer['result']),stem+'-replay',300)
        else:replay=None
        observation=dict(kind=kind,lane=mapping['lane'],repetition=item['repetition'],szs_status=status.group(1) if status else 'missing',input_entries=len(mapping['entries']),e_measurement=measured,proof_check=answer,proof_replay=replay,certificate_status='checked_complete_derivation' if answer['status']=='complete' and replay['status']=='complete' else 'unknown',used_lemma_inputs=answer['result'].get('used_lemma_inputs',[]),proof_steps=answer['result'].get('steps',0))
        observations.append(observation);dump(OUT/'summary.json',dict(status='complete' if len(observations)==4 else 'running',observations=observations,run_seconds=time.perf_counter()-start,interface_pre_run_replay_seconds=time.perf_counter()-began-(time.perf_counter()-start),setup_seconds=setup['seconds'],preparation_seconds=plan['preparation_seconds']))
        print('TARGET',kind,item['repetition'],observation['certificate_status'],answer['result'].get('error'),flush=True)
    print('BALANCED RUN COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','setup','run']);args=parser.parse_args()
    {'prepare':prepare,'setup':setup,'run':run}[args.phase]()
