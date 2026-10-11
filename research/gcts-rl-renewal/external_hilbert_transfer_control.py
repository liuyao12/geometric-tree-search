"""Fresh two-assertion Hilbert comparison; unchanged external proof adapter."""
import argparse,json,math,os,re,signal,subprocess,sys,time,platform
from pathlib import Path
from external_hilbert_transfer_inputs import ROOT,DOC,OUT,load,dump,build,encode
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

def prepare():
    began=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False)
    native=load(ROOT/'.gcts-active/hilbert-boundary-transfer-20261011/plan.json')
    adapter=load(ROOT/'.gcts-active/external-commutativity-20261011/plan.json')
    sources={**adapter['source_sha256'],**native['sources']}
    for name in ('external_hilbert_transfer_inputs.py','external_hilbert_transfer_control.py','external_hilbert_transfer_audit.py','external_hilbert_run.py'):
        sources[str((HERE/name).relative_to(ROOT))]=sha((HERE/name).read_bytes())
    deps={}
    for name in ('plan.json','declared-catalog.json.gz','catalog.json.gz','audit.json','progress.json','native.json.gz'):
        path=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'/name
        deps[str(path.relative_to(ROOT))]=dict(sha256=sha(path.read_bytes()),bytes=path.stat().st_size)
    for path,entry in native['data_dependencies'].items():deps[path]=entry
    for o in load(ROOT/'.gcts-active/hilbert-boundary-transfer-20261011/audit.json')['observations']:
        if o['certification']=='accepted':
            for suffix in ('.json.gz','-final.json.gz'):
                path=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'/(o['tag']+suffix)
                deps[str(path.relative_to(ROOT))]=dict(sha256=sha(path.read_bytes()),bytes=path.stat().st_size)
    for path in ('docs/research/gcts-rl-renewal/proof-boundary-microcode-001.json.gz','docs/research/gcts-rl-renewal/proof-boundary-001.json'):
        p=ROOT/path;deps[path]=dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
    for name,h in sources.items():
        if sha((ROOT/name).read_bytes())!=h:raise ValueError('existing pinned source changed '+name)
    preserved=[]
    for name in ('external-commutativity-20261011','external-left-successor-focus-20261011','external-induction-tstp-20261011'):
        p=ROOT/'.gcts-active'/name/'integration.json'
        for e in load(p)['files']:
            if sha((ROOT/e['path']).read_bytes())!=e['sha256']:raise ValueError('frozen export changed')
            preserved.append(e)
    pre=dict(status='frozen_before_input_preparation_or_E',source_sha256=sources,data_dependencies=deps,
      preserved_exports=preserved,preparation_cap_seconds=60,total_producer_cap_seconds=180,
      target_order=[dict(kind=k,repetition=r) for r in (1,2) for k in ('delayed-common','coupled-reverse')],
      options=['--auto','--proof-object','--tstp-format','--cpu-limit=10','--memory-limit=1024','--resources-info','--print-statistics'],
      prover_wall_seconds=12,certificate_wall_seconds=20,prover_binary_sha256=sha(E.read_bytes()),
      prover_source_commit='3b7afc70fe77d3118bb95144c4735ca45f5f31cf',target_runs=0,
      stop_policy='No checker changes. Stop on the first unsupported or budget-unknown proof; preserve the output/check and all remaining unexecuted unknowns. A theorem status alone is never acceptance.',
      scope='Two distinct exact assertions; short/sufficient row variants are the same theorem. Each input contains the original signature, guarded universally quantified I.2 and all three closed hypotheses, plus the unchanged conjecture. No theorem library or target proof path. E uses broader first-order inference/instantiation without a fixed row bound; external certificate checking is separate from native Wang acceptance, so no formal speed ratio.',
      cost_policy='Preparation and independent exact input/native provenance, fixture reruns, E/check/replay process costs, capped producer and independent final audit are separate. The180second producer includes fixtures and input gate. Complete native preparation/search/checking/replay and inherited inventory/policy are disclosed reused costs, not fresh operations; manual development remains unmeasured.',
      platform=platform.platform())
    dump(OUT/'preparation-plan.json',pre);bundle=build();dump(OUT/'inventory.json',bundle);entries=[]
    for c in bundle['cases']:
        text,mapping=encode(c);path=OUT/('hilbert-'+c['group']+'.p');path.write_text(text);dump(path.with_suffix('.mapping.json'),mapping)
        if exact_input(text,mapping)!=5:raise ValueError('all4axioms plus conjecture')
        entries.append(dict(kind=c['group'],name=path.name,input_sha256=sha(path.read_bytes()),mapping_sha256=sha(path.with_suffix('.mapping.json').read_bytes()),entries=5,lemma_inputs=0))
    if time.perf_counter()-began>60:raise TimeoutError('unknown preparation budget')
    snap=OUT/'source-snapshot';snap.mkdir()
    for name in sources:(snap/Path(name).name).write_bytes((ROOT/name).read_bytes())
    version=subprocess.run([str(E),'--version'],capture_output=True,text=True,check=True).stdout.strip()
    plan=dict(pre,status='frozen_exact_sources_inputs_budgets_before_all_E',inputs=entries,inventory_sha256=sha((OUT/'inventory.json').read_bytes()),preparation_seconds=time.perf_counter()-began,prover_version=version)
    dump(OUT/'plan.json',plan);print(json.dumps(dict(plan_sha256=sha((OUT/'plan.json').read_bytes()),inputs=entries,preparation_seconds=plan['preparation_seconds'])),flush=True)
def unchanged():
    p=load(OUT/'plan.json')
    for name,h in p['source_sha256'].items():
        if sha((ROOT/name).read_bytes())!=h:raise ValueError('frozen source '+name)
    for name,e in p['data_dependencies'].items():
        if sha((ROOT/name).read_bytes())!=e['sha256']:raise ValueError('frozen data '+name)
    for e in p['preserved_exports']:
        if sha((ROOT/e['path']).read_bytes())!=e['sha256']:raise ValueError('preserved export '+e['path'])
    for e in p['inputs']:
        f=OUT/e['name']
        if sha(f.read_bytes())!=e['input_sha256'] or sha(f.with_suffix('.mapping.json').read_bytes())!=e['mapping_sha256']:raise ValueError('frozen input')
    if sha(E.read_bytes())!=p['prover_binary_sha256'] or sha((OUT/'inventory.json').read_bytes())!=p['inventory_sha256']:raise ValueError('binary/inventory pin')
    return p
def run():
    plan=unchanged()
    if (OUT/'summary.json').exists():raise ValueError('fresh producer only')
    began=time.perf_counter();result=dict(status='running',plan_sha256=sha((OUT/'plan.json').read_bytes()),observations=[],unexecuted=[],fixtures=None)
    signal.signal(signal.SIGALRM,cap_alarm);signal.alarm(180)
    def checkpoint():result['seconds']=time.perf_counter()-began;dump(OUT/'summary.json',result)
    def available(wall):
        left=180-(time.perf_counter()-began)
        if left<.1:raise TimeoutError('unknown aggregate producer budget')
        return min(wall,left)
    try:
        import external_left_successor_focus_tests as fixtures
        import external_left_successor_focus_context_tests as context
        stage=time.perf_counter();fixtures.run(OUT/'focus-tests.json');context.PRIVATE=OUT/'shared-context-fixtures';context.main()
        result['fixtures']=dict(status='passed',seconds=time.perf_counter()-stage,focus_sha256=sha((OUT/'focus-tests.json').read_bytes()),context_sha256=sha((context.PRIVATE/'tests.json').read_bytes()));checkpoint()
        import external_hilbert_transfer_audit as audit
        stage=time.perf_counter();audit.dump(OUT/'pre-run-audit.json',audit.binding());result['pre_run_gate_seconds']=time.perf_counter()-stage;checkpoint()
        for ordered in plan['target_order']:
            kind=ordered['kind'];stem='hilbert-'+kind+'-r'+str(ordered['repetition']);path=OUT/('hilbert-'+kind+'.p');mapping=load(path.with_suffix('.mapping.json'))
            measured=execute([str(E),*plan['options'],str(path)],available(12));text=measured['stdout'];(OUT/(stem+'.tstp')).write_text(text);dump(OUT/(stem+'.process.json'),measured)
            status=re.search(r'SZS status (\w+)',text)
            check=operation(dict(operation='proof',output=text,mapping=mapping,input_path=str(path)),stem+'-check',available(20))
            replay=operation(dict(operation='proof-replay',output=text,mapping=mapping,input_path=str(path),saved=check['result']),stem+'-replay',available(20)) if check['status']=='complete' else None
            obs=dict(**ordered,stem=stem,szs_status=status.group(1) if status else 'missing',e_measurement=measured,proof_check=check,proof_replay=replay,certificate_status='checked_complete_derivation' if check['status']=='complete' and replay['status']=='complete' else 'unknown',output_sha256=sha(text),used_lemma_inputs=check['result'].get('used_lemma_inputs',[]),proof_steps=check['result'].get('steps'))
            result['observations'].append(obs);checkpoint();print('HILBERT TARGET',kind,ordered['repetition'],obs['certificate_status'],check['result'].get('error'),flush=True)
            if obs['certificate_status']!='checked_complete_derivation':raise ValueError('unknown target certificate')
        result['status']='complete_four_checked_targets_pending_final_audit'
    except Exception as error:
        result.update(status='unknown_stopped_by_declared_gate',error=type(error).__name__+': '+str(error));result['unexecuted']=[dict(x,status='unknown_unexecuted_due_to_declared_stop_gate') for x in plan['target_order'][len(result['observations']):]]
    finally:signal.alarm(0);checkpoint()
    print(json.dumps({k:v for k,v in result.items() if k!='observations'}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.phase]()
