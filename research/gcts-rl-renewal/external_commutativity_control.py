"""Predeclared six-run external control; immutable existing proof checkers."""
import argparse,json,math,os,re,shutil,signal,subprocess,sys,time
from pathlib import Path
from external_commutativity_inputs import ROOT,DOC,OUT,load,dump,build,encode
from external_prover_inputs import sha
from external_induction_tstp_audit import exact_input

HERE=Path(__file__).resolve().parent
E=Path('/private/tmp/gcts-external-eprover-20261011/PROVER/eprover')
ACTIVE=set()
def cap_alarm(signum,frame):
    for pid in list(ACTIVE):
        try:os.killpg(pid,signal.SIGKILL)
        except ProcessLookupError:pass
    raise TimeoutError('unknown aggregate 180-second E/checking producer cutoff')
def execute(command,wall):
    began=time.perf_counter()
    p=subprocess.Popen([sys.executable,str(HERE/'external_prover_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    ACTIVE.add(p.pid)
    try:
        stdout,stderr=p.communicate(json.dumps(dict(command=command,timeout=wall)),timeout=wall+2)
        if p.returncode:raise ValueError('isolated E worker failed: '+stderr[:500])
        result=json.loads(stdout);result['fresh_worker_wall_seconds']=time.perf_counter()-began;return result
    finally:
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGKILL);p.wait()
        ACTIVE.discard(p.pid)
def preserve():
    manifests=[ROOT/'.gcts-active/external-left-successor-focus-20261011/integration.json',ROOT/'.gcts-active/hilbert-expanded-control-20261011/final-integration.json',ROOT/'.gcts-active/commutativity-receptors-20261011/attempt-02/integration.json']
    files={}
    for p in manifests:
        for e in load(p)['files']:
            if sha((ROOT/e['path']).read_bytes())!=e['sha256']:raise ValueError('prior frozen export changed')
            files[e['path']]=e
    return list(files.values())
def unchanged():
    p=load(OUT/'plan.json')
    for name,h in p['source_sha256'].items():
        if sha((ROOT/name).read_bytes())!=h:raise ValueError('frozen source changed '+name)
    for name,e in p['data_dependencies'].items():
        if sha((ROOT/name).read_bytes())!=e['sha256']:raise ValueError('frozen input changed '+name)
    for e in p['inputs']:
        path=OUT/e['name']
        if sha(path.read_bytes())!=e['input_sha256'] or sha(path.with_suffix('.mapping.json').read_bytes())!=e['mapping_sha256']:raise ValueError('frozen export changed')
    if sha(E.read_bytes())!=p['prover_binary_sha256']:raise ValueError('pinned prover changed')
    if sha((OUT/'inventory.json').read_bytes())!=p['inventory_sha256']:raise ValueError('frozen instance/theorem union changed')
    preserve();return p
def prepare():
    began=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False)
    prior=load(ROOT/'.gcts-active/external-left-successor-focus-20261011/attempt-03/plan.json')
    sources=dict(prior['source_sha256'])
    comm=load(DOC/'commutativity_plan.json');sources.update(comm['source_sha256'])
    for name in ('external_commutativity_inputs.py','external_commutativity_control.py','external_commutativity_audit.py'):
        sources[str((HERE/name).relative_to(ROOT))]=sha((HERE/name).read_bytes())
    deps={}
    names=list(comm['input_sha256'])+['docs/research/gcts-rl-renewal/commutativity_plan.json','docs/research/gcts-rl-renewal/commutativity_audit.json','.gcts-active/external-left-successor-20261011/inventory.json','.gcts-active/external-left-successor-20261011/plan.json','.gcts-active/external-left-successor-focus-20261011/attempt-03/audit.json']
    names+=['docs/research/gcts-rl-renewal/commutativity_'+x['id'].replace('-','_')+'_full_core.json.gz' for x in comm['lanes']]
    for n in sorted(set(names)):
        path=ROOT/n;deps[n]=dict(sha256=sha(path.read_bytes()),bytes=path.stat().st_size)
    for n,h in sources.items():
        if sha((ROOT/n).read_bytes())!=h:raise ValueError('prior source pin mismatch '+n)
    pre=dict(status='frozen_before_input_preparation_or_E',source_sha256=sources,data_dependencies=deps,
        total_producer_cap_seconds=180,preparation_cap_seconds=60,setup_order=['setup-0','setup-1'],
        target_order=[dict(kind=k,repetition=r) for r,ks in [(1,['theory','zero-left','both']),(2,['both','zero-left','theory'])] for k in ks],
        prover_wall_seconds=12,certificate_wall_seconds=20,options=['--auto','--proof-object','--tstp-format','--cpu-limit=10','--memory-limit=1024','--resources-info','--print-statistics'],
        stop_policy='Preserve every returned output/check. First unsupported or budget-unknown setup/target proof halts target execution; all remaining scheduled runs are explicitly unexecuted unknowns. No adapter changes, status-only proof acceptance or supplied target proof.',
        scope='All target lanes receive the full five-instance union, not full PA or exactly the native finite search grammar. E uses broader unbounded first-order instantiation and a different independently replayed certificate language. No native Wang acceptance or fair speed ratio is claimed.',
        cost_policy='Freeze/input preparation, existing fixture reruns, two fresh E lemma setup proofs with complete checking/replay, independent input/native-provenance gate, six fresh target E/check/replay runs and final audit are separate. The 180-second cap covers the producer including setup, fixtures and pre-run gate. Historical primitive theorem discovery/native/full replay are reused inherited costs, not free cold work.',
        preserved_exports=preserve(),prover_binary_sha256=sha(E.read_bytes()),prover_source_commit='3b7afc70fe77d3118bb95144c4735ca45f5f31cf',target_runs=0)
    dump(OUT/'preparation-plan.json',pre)
    bundle=build();dump(OUT/'inventory.json',bundle);inputs=[]
    for kind in ['setup-0','setup-1','theory','zero-left','both']:
        text,mapping=encode(bundle,kind);path=OUT/('commutativity-'+kind+'.p');path.write_text(text);dump(path.with_suffix('.mapping.json'),mapping);count=exact_input(text,mapping)
        if count!=(4 if kind.startswith('setup-') else {'theory':8,'zero-left':9,'both':10}[kind]):raise ValueError('complete exact input census')
        inputs.append(dict(kind=kind,name=path.name,input_sha256=sha(path.read_bytes()),mapping_sha256=sha(path.with_suffix('.mapping.json').read_bytes()),entries=count))
    if time.perf_counter()-began>pre['preparation_cap_seconds']:raise TimeoutError('unknown preparation budget')
    snap=OUT/'source-snapshot';snap.mkdir()
    for name in sources:(snap/Path(name).name).write_bytes((ROOT/name).read_bytes())
    plan=dict(pre,status='frozen_exact_sources_inputs_budgets_before_all_E',inputs=inputs,inventory_sha256=sha((OUT/'inventory.json').read_bytes()),preparation_seconds=time.perf_counter()-began,induction_instances=5,optional_theorem_inputs=2,unadmitted_interface_inputs=0)
    dump(OUT/'plan.json',plan);print(json.dumps(dict(status=plan['status'],plan_sha256=sha((OUT/'plan.json').read_bytes()),inputs=inputs,preparation_seconds=plan['preparation_seconds'])),flush=True)
def operation(payload,stem,wall):
    began=time.perf_counter();inp=OUT/(stem+'.request.json');dest=OUT/(stem+'.worker.json')
    if inp.exists() or dest.exists():raise ValueError('cannot overwrite a completed operation')
    dump(inp,dict(payload,cpu_limit=max(1,math.ceil(wall))))
    with (OUT/(stem+'.stderr')).open('w') as err:
        proc=subprocess.Popen([sys.executable,str(HERE/'external_left_successor_focus_worker.py'),str(inp),str(dest)],stdout=subprocess.DEVNULL,stderr=err,start_new_session=True)
        ACTIVE.add(proc.pid)
        try:proc.wait(timeout=wall)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        finally:
            if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            ACTIVE.discard(proc.pid)
    answer=load(dest) if dest.exists() else dict(status='unknown',result=dict(status='unknown',error='operation budget or missing worker output'))
    answer.update(process_wall_seconds=time.perf_counter()-began,process_exit_code=proc.returncode,request_sha256=sha(inp.read_bytes()))
    dump(OUT/(stem+'.result.json'),answer);return answer
def run():
    plan=unchanged()
    if (OUT/'summary.json').exists():raise ValueError('fresh producer only')
    began=time.perf_counter();result=dict(status='running',plan_sha256=sha((OUT/'plan.json').read_bytes()),setup=[],observations=[],unexecuted=[],fixtures=None)
    signal.signal(signal.SIGALRM,cap_alarm);signal.alarm(plan['total_producer_cap_seconds'])
    def checkpoint():result['seconds']=time.perf_counter()-began;dump(OUT/'summary.json',result)
    def available(wall):
        left=plan['total_producer_cap_seconds']-(time.perf_counter()-began)
        if left<.1:raise TimeoutError('unknown aggregate E/checking producer budget')
        return min(wall,left)
    try:
        import external_left_successor_focus_tests as fixtures
        import external_left_successor_focus_context_tests as context
        stage=time.perf_counter();fixtures.run(OUT/'focus-tests.json');context.PRIVATE=OUT/'shared-context-fixtures';context.main()
        result['fixtures']=dict(status='passed',seconds=time.perf_counter()-stage,focus_sha256=sha((OUT/'focus-tests.json').read_bytes()),context_sha256=sha((context.PRIVATE/'tests.json').read_bytes()));checkpoint()
        def trial(kind,stem):
            path=OUT/('commutativity-'+kind+'.p');mapping=load(path.with_suffix('.mapping.json'))
            measured=execute([str(E),*plan['options'],str(path)],available(plan['prover_wall_seconds']));text=measured['stdout'];(OUT/(stem+'.tstp')).write_text(text);dump(OUT/(stem+'.process.json'),measured)
            status=re.search(r'SZS status (\w+)',text)
            check=operation(dict(operation='proof',output=text,mapping=mapping,input_path=str(path)),stem+'-check',available(plan['certificate_wall_seconds']))
            replay=operation(dict(operation='proof-replay',output=text,mapping=mapping,input_path=str(path),saved=check['result']),stem+'-replay',available(plan['certificate_wall_seconds'])) if check['status']=='complete' else None
            return dict(kind=kind,stem=stem,szs_status=status.group(1) if status else 'missing',e_measurement=measured,proof_check=check,proof_replay=replay,certificate_status='checked_complete_derivation' if check['status']=='complete' and replay['status']=='complete' else 'unknown',output_sha256=sha(text),used_lemma_inputs=check['result'].get('used_lemma_inputs',[]),proof_steps=check['result'].get('steps'))
        for kind in plan['setup_order']:
            obs=trial(kind,kind);result['setup'].append(obs);checkpoint();print('SETUP',kind,obs['certificate_status'],obs['proof_check']['result'].get('error'),flush=True)
            if obs['certificate_status']!='checked_complete_derivation':raise ValueError('unknown setup lemma validation')
        import external_commutativity_audit as audit
        stage=time.perf_counter();audit.before();result['pre_run_gate_seconds']=time.perf_counter()-stage;checkpoint()
        for ordered in plan['target_order']:
            available(.1);kind=ordered['kind'];obs=trial(kind,'commutativity-'+kind+'-r'+str(ordered['repetition']));obs['repetition']=ordered['repetition'];result['observations'].append(obs);checkpoint();print('TARGET',kind,ordered['repetition'],obs['certificate_status'],obs['proof_check']['result'].get('error'),flush=True)
            if obs['certificate_status']!='checked_complete_derivation':raise ValueError('unknown target certificate validation')
        result['status']='complete_six_checked_targets_pending_final_audit'
    except Exception as error:
        result.update(status='unknown_stopped_by_declared_gate',error=type(error).__name__+': '+str(error))
        result['unexecuted']=[dict(x,status='unknown_unexecuted_due_to_declared_stop_gate') for x in plan['target_order'][len(result['observations']):]]
    finally:signal.alarm(0);checkpoint()
    print(json.dumps({k:v for k,v in result.items() if k not in ('setup','observations')}),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','run']);a=parser.parse_args();{'prepare':prepare,'run':run}[a.phase]()
