"""Frozen bounded union-theory/control; all setup and audit gates precede E."""
import argparse,json,pathlib,re,resource,time
from external_prover_inputs import canonical,sha
from external_left_successor_inputs import OUT,ROOT,snapshot,inventory,inputs,dump,load
import external_induction_tstp_run as worker
from external_induction_tstp_audit import exact_input

HERE=pathlib.Path(__file__).resolve().parent
E=pathlib.Path('/private/tmp/gcts-external-eprover-20261011/PROVER/eprover')
SOURCE_NAMES=('external_left_successor_inputs.py','external_left_successor_run.py','external_left_successor_audit.py','external_left_successor_tests.py','external_induction_tstp_check.py','external_induction_tstp_worker.py','external_induction_tstp_run.py','external_induction_tstp_audit.py','external_induction_skolem.py','external_prover_check.py','external_prover_inputs.py','external_prover_run.py','external_prover_worker.py')

def preserved():
    entries={}
    for folder,name in [('external-prover-20261011','export.json'),('external-hilbert-20261011','export.json'),('external-induction-20261011','export.json'),('external-induction-tstp-20261011','integration.json')]:
        for e in load(ROOT/'.gcts-active'/folder/name)['files']:
            if sha((ROOT/e['path']).read_bytes())!=e['sha256']:raise ValueError('previous completed artifact changed '+e['path'])
            if e['path'] in entries and entries[e['path']]!=e:raise ValueError('previous manifests disagree')
            entries[e['path']]=e
    return list(entries.values())

def unchanged():
    p=load(OUT/'plan.json');preserved()
    for n,want in p['source_sha256'].items():
        if sha((ROOT/n).read_bytes())!=want:raise ValueError('frozen source changed '+n)
    if sha(E.read_bytes())!=p['prover_binary_sha256']:raise ValueError('pinned binary changed')
    for e in p['inputs']:
        if sha(pathlib.Path(e['path']).read_bytes())!=e['input_sha256'] or sha(pathlib.Path(e['path']).with_suffix('.mapping.json').read_bytes())!=e['mapping_sha256']:raise ValueError('frozen exact input bytes changed')
    return p

def op(payload,stem,wall):
    worker.OUT=OUT
    return worker.operation(payload,stem,wall)

def prepare():
    began=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False);sources={str((HERE/n).relative_to(ROOT)):sha((HERE/n).read_bytes()) for n in SOURCE_NAMES};saved=OUT/'source-snapshot';saved.mkdir()
    for n in SOURCE_NAMES:(saved/n).write_bytes((HERE/n).read_bytes())
    pre=dict(status='frozen_before_preparation_and_any_E_target_run',source_sha256=sources,preparation_wall_seconds=180,preparation_peak_RSS_bytes=1073741824,setup_aggregate_seconds=300,interface_worker_wall_seconds=30,whole_certificate_worker_wall_seconds=300,per_logical_step_wall_seconds=30,certificate_worker_sampled_RSS_bytes=1073741824,options=['--auto','--proof-object','--tstp-format','--cpu-limit=60','--memory-limit=1024','--resources-info','--print-statistics'],prover_wall_seconds=65,repetitions=2,order=[dict(kind=k,repetition=r) for r,ks in [(1,['theory','library']),(2,['library','theory'])] for k in ks],scope='Complete mechanically derived three-instance union in both lanes; all24 actual admitted interfaces checked from contextual dependencies and all setup certificates independently replayed before E. No supplied target derivation or winning induction choice. Native without-transfer finite grammar differs from this union control. No native Wang acceptance for E.')
    dump(OUT/'preparation-plan.json',pre)
    try:
        prior=preserved();snap=snapshot();bundle=inventory(snap)
        if time.perf_counter()-began>pre['preparation_wall_seconds'] or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>pre['preparation_peak_RSS_bytes']:raise TimeoutError('unknown preparation budget')
        dump(OUT/'inventory.json',bundle);input_info=[]
        for library in (False,True):
            kind='library' if library else 'theory';text,m=inputs(bundle,library);path=OUT/('left-successor-'+kind+'.p');path.write_text(text);dump(path.with_suffix('.mapping.json'),m)
            count=exact_input(text,m)
            if count!=(30 if library else 6):raise ValueError('complete six/thirty entry inventory')
            input_info.append(dict(kind=kind,path=str(path),input_sha256=sha(path.read_bytes()),mapping_sha256=sha(path.with_suffix('.mapping.json').read_bytes()),entries=count))
        plan=dict(pre,status='frozen_exact_union_inputs_before_setup_checks_and_E_execution',inputs=input_info,snapshot_manifest_sha256=sha((OUT/'snapshot.json').read_bytes()),inventory_sha256=sha((OUT/'inventory.json').read_bytes()),prover_source_commit='3b7afc70fe77d3118bb95144c4735ca45f5f31cf',prover_binary_sha256=sha(E.read_bytes()),prover_version=__import__('subprocess').run([str(E),'--version'],capture_output=True,text=True,check=True).stdout.strip(),preserved_artifacts=prior,preparation_seconds=time.perf_counter()-began,target_runs=0,induction_instances=3,complete_admitted_interfaces=24)
        dump(OUT/'plan.json',plan);print('EXACT UNION INPUTS FROZEN',plan['preparation_seconds'],flush=True)
    except Exception as e:
        dump(OUT/'preparation-outcome.json',dict(status='unknown_preparation',error=type(e).__name__+': '+str(e),seconds=time.perf_counter()-began,target_runs=0));raise

def setup():
    plan=unchanged();test=load(OUT/'tests.json')
    if test['status']!='passed':raise ValueError('input/unsupported-feature tests incomplete')
    bundle=load(OUT/'inventory.json');mapping=load(OUT/'left-successor-library.mapping.json');schemas={s['id']:s['formula'] for s in bundle['schemas']};axioms=bundle['spec']['theory']['axioms'];began=time.perf_counter();results=[]
    for e in bundle['interfaces']:
        if time.perf_counter()-began>plan['setup_aggregate_seconds']:
            dump(OUT/'setup.json',dict(status='unknown_aggregate_setup_budget',interfaces=results,seconds=time.perf_counter()-began,target_runs=0));return
        parents=[axioms[n] for n in e['axiom_dependencies']]+[schemas[n] for n in e['induction_dependencies']];request=dict(operation='interface',parents=parents,child=e['formula'],mapping=mapping)
        answer=op(request,e['id']+'-setup',plan['interface_worker_wall_seconds']);results.append(dict(id=e['id'],request=request,native_binding=e,measurement=answer));status='complete' if len(results)==24 and answer['status']=='complete' else ('running' if answer['status']=='complete' else 'unknown_interface_setup')
        dump(OUT/'setup.json',dict(status=status,interfaces=results,seconds=time.perf_counter()-began,target_runs=0));print('SETUP',e['id'],answer['status'],answer['result'].get('error'),flush=True)
        if answer['status']!='complete':return

def run():
    plan=unchanged();gate=load(OUT/'pre-run-audit.json');setup=load(OUT/'setup.json')
    if gate['status']!='passed_exact_source_input_inventory_setup_and_full_replay_gate' or gate['plan_sha256']!=sha((OUT/'plan.json').read_bytes()) or gate['setup_sha256']!=sha((OUT/'setup.json').read_bytes()) or len(setup['interfaces'])!=24:raise ValueError('independent complete pre-run audit gate open')
    observations=[];began=time.perf_counter()
    for ordered in plan['order']:
        kind=ordered['kind'];path=OUT/('left-successor-'+kind+'.p');mapping=load(path.with_suffix('.mapping.json'));stem='left-successor-'+kind+'-r'+str(ordered['repetition']);measured=worker.execute([str(E),*plan['options'],str(path)],plan['prover_wall_seconds']);text=measured['stdout'];(OUT/(stem+'.tstp')).write_text(text);dump(OUT/(stem+'.process.json'),measured)
        status=re.search(r'SZS status (\w+)',text);answer=op(dict(operation='proof',output=text,mapping=mapping,input_path=str(path)),stem+'-check',plan['whole_certificate_worker_wall_seconds'])
        replay=op(dict(operation='proof-replay',output=text,mapping=mapping,input_path=str(path),saved=answer['result']),stem+'-replay',plan['whole_certificate_worker_wall_seconds']) if answer['status']=='complete' else None
        observations.append(dict(kind=kind,repetition=ordered['repetition'],szs_status=status.group(1) if status else 'missing',e_measurement=measured,proof_check=answer,proof_replay=replay,certificate_status='checked_complete_derivation' if answer['status']=='complete' and replay['status']=='complete' else 'unknown',output_sha256=sha(text),used_lemma_inputs=answer['result'].get('used_lemma_inputs',[]),proof_steps=answer['result'].get('steps')))
        dump(OUT/'summary.json',dict(status='complete' if len(observations)==4 else 'running',observations=observations,seconds=time.perf_counter()-began,plan_sha256=sha((OUT/'plan.json').read_bytes()),pre_run_gate_sha256=sha((OUT/'pre-run-audit.json').read_bytes())));print('TARGET',kind,ordered['repetition'],observations[-1]['certificate_status'],answer['result'].get('error'),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','setup','run']);args=ap.parse_args();{'prepare':prepare,'setup':setup,'run':run}[args.phase]()
