"""Separate corrected freeze; retains the complete original unknown batch."""
import argparse,json,pathlib,shutil,subprocess,sys,time
import external_left_successor_run as original
import external_left_successor_audit as auditor
from external_left_successor_inputs import ROOT,dump,load
from external_prover_inputs import sha

HERE=pathlib.Path(__file__).resolve().parent
DEVELOPMENT=ROOT/'.gcts-active/external-left-successor-focus-20261011'
OUT=DEVELOPMENT/'attempt-03'
PRIOR=original.OUT
NEW=('external_left_successor_focus.py','external_left_successor_focus_tests.py','external_left_successor_focus_worker.py','external_left_successor_focus_run.py','external_left_successor_focus_audit.py','external_left_successor_focus_context_tests.py','external_induction_tstp_tests.py')

def prepare():
    began=time.perf_counter();p=original.unchanged()
    if load(PRIOR/'audit.json')['successful_checked_derivations']!=0 or load(PRIOR/'audit.json')['unknown_checks']!=4:raise ValueError('complete original unknown batch must be preserved')
    OUT.mkdir(parents=True,exist_ok=False)
    sources=dict(p['source_sha256']);sources.update({str((HERE/n).relative_to(ROOT)):sha((HERE/n).read_bytes()) for n in NEW})
    # The same declared budgets and balanced order, frozen before any corrected
    # interface check, fixture run, full replay or E execution.
    prep=dict(p,status='frozen_corrected_focus_sources_before_all_new_gates_and_E',source_sha256=sources,target_runs=0,
        logical_policy='Exact generic focused universal instantiation proposes finite clauses, then independent reconstruction of every substitution and unchanged EUF relation-closure refutation replay. No finite satisfiability/unrestricted-entailment inference, E-rule trust or target proof.',
        focus_bounds=dict(rounds=5,instances=4000,terms=600),
        retry_scope='Developed after all four original validator unknowns; preserved theory/library traces were calibration inputs, not fresh controlled results. Every corrected target run is a fresh E process after all24 fresh setup/replays and adversarial gates. Native without-transfer has two target templates; both external lanes receive complete three-instance union.',
        tests_policy='Before target runs: independent closure/unsupported-feature gates,12 unrestricted-FOL relations/13 altered-instance/tree tests and all51 shared-context/witness fixtures. Unknown setup blocks all E runs.',
        audit_policy='Independent input/source/native binding and complete24 fresh replay gate before E; exact four-result source/input/check/full-replay audit afterward; corrupt every actually used focused refutation and shared context/witness fields.')
    dump(OUT/'preparation-plan.json',prep)
    shutil.copytree(PRIOR,OUT/'prior-attempt');shutil.copytree(PRIOR/'snapshot',OUT/'snapshot')
    prior_manifest=[dict(path=str(f.relative_to(PRIOR)),sha256=sha(f.read_bytes()),bytes=f.stat().st_size) for f in sorted(PRIOR.rglob('*')) if f.is_file()]
    dump(OUT/'prior-attempt-manifest.json',dict(status='complete_original_four_unknowns_preserved',files=prior_manifest))
    for n in ('inventory.json','snapshot.json'):(OUT/n).write_bytes((PRIOR/n).read_bytes())
    inputs=[]
    for e in p['inputs']:
        src=pathlib.Path(e['path']);dst=OUT/src.name;dst.write_bytes(src.read_bytes());mp=src.with_suffix('.mapping.json');dst.with_suffix('.mapping.json').write_bytes(mp.read_bytes())
        inputs.append(dict(e,path=str(dst)))
    saved=OUT/'source-snapshot';saved.mkdir()
    for name in sources:(saved/pathlib.Path(name).name).write_bytes((ROOT/name).read_bytes())
    plan=dict(prep,status='frozen_corrected_all_sources_inputs_budgets_before_new_gates_and_E',inputs=inputs,
        prior_attempt_manifest_sha256=sha((OUT/'prior-attempt-manifest.json').read_bytes()),
        prior_plan_sha256=sha((PRIOR/'plan.json').read_bytes()),prior_audit_sha256=sha((PRIOR/'audit.json').read_bytes()),
        calibration_files=[dict(path=str(f.relative_to(DEVELOPMENT)),sha256=sha(f.read_bytes()),bytes=f.stat().st_size) for f in sorted(DEVELOPMENT.glob('*.json'))],
        preparation_seconds=time.perf_counter()-began)
    dump(OUT/'plan.json',plan);print('CORRECTED SOURCES/INPUTS FROZEN',plan['preparation_seconds'],flush=True)

def unchanged():
    p=load(OUT/'plan.json');original.preserved()
    for n,h in p['source_sha256'].items():
        if sha((ROOT/n).read_bytes())!=h:raise ValueError('corrected frozen source changed '+n)
    if sha(original.E.read_bytes())!=p['prover_binary_sha256']:raise ValueError('pinned E binary changed')
    for e in p['inputs']:
        path=pathlib.Path(e['path'])
        if sha(path.read_bytes())!=e['input_sha256'] or sha(path.with_suffix('.mapping.json').read_bytes())!=e['mapping_sha256']:raise ValueError('frozen corrected input changed')
    if sha((OUT/'prior-attempt-manifest.json').read_bytes())!=p['prior_attempt_manifest_sha256']:raise ValueError('original unknown manifest changed')
    for e in load(OUT/'prior-attempt-manifest.json')['files']:
        if sha((OUT/'prior-attempt'/e['path']).read_bytes())!=e['sha256']:raise ValueError('original four unknowns changed')
    for e in p['calibration_files']:
        if sha((DEVELOPMENT/e['path']).read_bytes())!=e['sha256']:raise ValueError('post-failure calibration changed')
    return p

def operation(payload,stem,wall):
    began=time.perf_counter();inp=OUT/(stem+'.request.json');dest=OUT/(stem+'.worker.json')
    if inp.exists() or dest.exists():raise ValueError('fresh operation may not overwrite prior evidence')
    dump(inp,dict(payload,cpu_limit=wall));reason=None
    with (OUT/(stem+'.stderr')).open('w') as err:
        proc=subprocess.Popen([sys.executable,str(HERE/'external_left_successor_focus_worker.py'),str(inp),str(dest)],stdout=subprocess.DEVNULL,stderr=err)
        while proc.poll() is None:
            if time.perf_counter()-began>wall:reason='external wall cutoff';proc.kill();break
            time.sleep(.01)
        proc.wait()
    answer=load(dest) if dest.exists() else dict(status='unknown',result=dict(status='unknown',error=reason or 'worker exited without complete output'))
    if reason:answer=dict(status='unknown',result=dict(status='unknown',error=reason))
    answer.update(process_wall_seconds=time.perf_counter()-began,process_exit_code=proc.returncode,request_sha256=sha(inp.read_bytes()))
    dump(OUT/(stem+'.result.json'),answer);return answer

def fixtures():
    unchanged()
    import external_left_successor_tests as inputs
    import external_left_successor_focus_tests as tests
    import external_left_successor_focus_context_tests as context
    import external_left_successor_focus as focused
    inputs.OUT=OUT;inputs.SOURCE=OUT/'snapshot';inputs.main()
    tests.run(OUT/'focus-tests.json')
    context.PRIVATE=OUT/'shared-context-fixtures';context.check_output=focused.check_output
    context.consequence=focused.consequence;context.replay_consequence=focused.replay_consequence
    context.main()
    dump(OUT/'all-tests.json',dict(status='passed',input_sha256=sha((OUT/'tests.json').read_bytes()),focus_sha256=sha((OUT/'focus-tests.json').read_bytes()),context_sha256=sha((context.PRIVATE/'tests.json').read_bytes()),target_runs=0))

def bind():
    original.OUT=OUT;original.unchanged=unchanged;original.op=operation
    auditor.OUT=OUT;auditor.unchanged=unchanged;auditor.op=operation

def setup():
    if load(OUT/'all-tests.json')['status']!='passed':raise ValueError('all adversarial gates remain open')
    bind();original.setup()

def gate():
    bind();auditor.before()

def run():
    if load(OUT/'all-tests.json')['status']!='passed':raise ValueError('all fixture gates remain open')
    bind();original.run()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','fixtures','setup','gate','run']);a=p.parse_args()
    {'prepare':prepare,'fixtures':fixtures,'setup':setup,'gate':gate,'run':run}[a.phase]()
