"""Fresh-process E comparison, frozen inputs, full independent certificate checks."""
import argparse,hashlib,json,os,pathlib,platform,resource,subprocess,sys,time
from external_prover_inputs import make_input,sha,canonical
from external_prover_check import check_output,native_formula,entails,formula_text,alpha

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def execute(cmd,timeout):
    began=time.perf_counter();worker=pathlib.Path(__file__).with_name('external_prover_worker.py')
    run=subprocess.run([sys.executable,str(worker)],input=json.dumps(dict(command=cmd,timeout=timeout)),capture_output=True,text=True,check=True,timeout=timeout+10)
    result=json.loads(run.stdout);result['fresh_worker_wall_seconds']=time.perf_counter()-began
    return result

def countermodel(spec,library):
    """Independent audit-only interpretation of the disconnected control."""
    if spec['id']!='disconnected-premise-five':return None
    domain=[0,1];constants={n:(1 if n=='isolated' else 0) for n in spec['theory']['functions']}
    def term(t,env):
        if t[0]=='var':return env[t[1]]
        if t[2]:raise ValueError('countermodel function table missing')
        return constants[t[1]]
    def evaluate(f,env=None):
        env={} if env is None else env;h=f[0]
        if h=='bot':return False
        if h=='eq':return term(f[1],env)==term(f[2],env)
        if h=='pred':return f[1]=='Has' and [term(t,env) for t in f[2]]==[1]
        if h=='imp':return not evaluate(f[1],env) or evaluate(f[2],env)
        if h=='and':return evaluate(f[1],env) and evaluate(f[2],env)
        if h=='or':return evaluate(f[1],env) or evaluate(f[2],env)
        if h=='all':return all(evaluate(f[2],{**env,f[1]:v}) for v in domain)
        raise ValueError('countermodel formula')
    axioms={n:evaluate(f) for n,f in spec['theory']['axioms'].items()}
    lemmas={e['name']:evaluate(e['formula']) for e in library if e['role']=='lemma'}
    target=evaluate(spec['target'])
    if not all(axioms.values()) or not all(lemmas.values()) or target:raise ValueError('invalid countermodel')
    return dict(status='independently_checked_countermodel',domain=domain,constants=constants,predicate={'Has':[[1]]},axioms=axioms,lemmas=lemmas,target=target,
                source='Declared finite audit interpretation, independently evaluated against exact input ASTs; not inferred from E status and not supplied to search.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reader',required=True);ap.add_argument('--e',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);plan=json.loads((out/'plan.json').read_text())
    reader_bytes=pathlib.Path(a.reader).read_bytes();x=json.loads(reader_bytes);began=time.perf_counter()
    if plan['case_ids']!=[c['spec']['id'] for c in x['cases']]:raise ValueError('case plan mismatch')
    sources=sorted(pathlib.Path(__file__).parent.glob('external_prover_*.py'))
    closure={str(p):sha(p.read_bytes()) for p in sources}
    plan['reader_sha256']=sha(reader_bytes);plan['source_sha256']=closure;plan['status']='frozen_before_recipient_measurement';dump(out/'plan.json',plan)
    frozen_plan_sha=sha((out/'plan.json').read_bytes())
    version=subprocess.run([a.e,'--version'],capture_output=True,text=True,check=True).stdout.strip()
    inputs=[];setup=[];native={r['id']:r for r in x['native']}
    for c in x['cases']:
        for family in [False,True]:
            t=time.perf_counter();m=make_input(c,family)
            for e in m['entries']:
                # Independently parse emitted formula and compare direct original AST.
                line='fof('+e['name']+','+e['role']+','
                f=m['text'].split(line,1)[1].split(').\n',1)[0]
                if alpha(formula_text(f))!=alpha(native_formula(e['formula'],m)):raise ValueError('input round trip mismatch')
            q=out/(c['spec']['id']+'-'+('library' if family else 'theory')+'.p');q.write_text(m['text']);m['input_path']=str(q);dump(q.with_suffix('.mapping.json'),m)
            library_checks=[]
            if family:
                definitions={d['name']:d for d in c['inventory']['native_blocks']}
                for e in m['entries']:
                    if e['role']!='lemma':continue
                    qn=native[e['native_admission']]
                    if qn['result']['status']!='accepted' or definitions[e['original_name']] not in qn['request']['blocks']:raise ValueError('unbound ground native admission')
                    check=entails([],native_formula(e['formula'],m))
                    if check['status']!='checked':raise ValueError('independent library entailment unknown')
                    library_checks.append(dict(name=e['name'],native_admission=e['native_admission'],**check))
            cm=countermodel(c['spec'],m['entries']);s=dict(case=m['case'],lane=m['lane'],input_sha256=m['sha256'],export_and_library_check_seconds=time.perf_counter()-t,library_checks=library_checks,countermodel=cm)
            setup.append(s);inputs.append((m,c))
    dump(out/'setup.json',setup)
    observations=[]
    for repetition in [1,2]:
        for ci in range(len(x['cases'])):
            order=[0,1] if repetition==1 else [1,0]
            for lane in order:
                m,c=inputs[2*ci+lane];name=c['spec']['id']+'-'+('library' if lane else 'theory')+'-r'+str(repetition)
                cmd=[a.e,*plan['command_options'],m['input_path']];run=execute(cmd,plan['wall_timeout_seconds'])
                stdout=run.pop('stdout');stderr=run.pop('stderr');(out/(name+'.tstp')).write_text(stdout);(out/(name+'.stderr')).write_text(stderr)
                import re
                match=re.findall(r'^% SZS status (\S+)',stdout,re.M);status=match[-1] if match else None
                t=time.perf_counter();check=None
                if status in ('Theorem','Unsatisfiable') and not run['timed_out']:
                    try:check=check_output(stdout,m,m['input_path'])
                    except Exception as e:check=dict(status='certificate_unknown',error=str(e))
                else:check=dict(status='no_refutation_certificate',countermodel=setup[2*ci+lane]['countermodel'])
                verify_seconds=time.perf_counter()-t;dump(out/(name+'.check.json'),check)
                resources={}
                for label in ['User time','System time','Total time','Maximum resident set size']:
                    hits=[ln for ln in stdout.splitlines() if label in ln]
                    if hits:resources[label]=hits[-1]
                obs=dict(case=c['spec']['id'],lane=m['lane'],repetition=repetition,command=cmd,input_sha256=m['sha256'],output_sha256=sha(stdout),stderr_sha256=sha(stderr),szs_status=status,certificate_status=check['status'],verification_seconds=verify_seconds,proof_steps=check.get('steps'),used_lemma_inputs=check.get('used_lemma_inputs',[]),resources=resources,**run)
                observations.append(obs);dump(out/'observations.json',observations);print(c['spec']['id'],m['lane'],repetition,status,check['status'],run['wall_seconds'],flush=True)
    for p in sources:
        if sha(p.read_bytes())!=closure[str(p)]:raise ValueError('source changed during measurement')
    result=dict(version='external-prover-comparison-1',status='complete',plan_sha256=frozen_plan_sha,reader_sha256=sha(reader_bytes),source_sha256=closure,prover_version=version,prover_binary_sha256=sha(pathlib.Path(a.e).read_bytes()),source_commit=plan['prover'],platform=platform.platform(),observations=observations,setup=setup,total_seconds=time.perf_counter()-began,
                successful_checked_derivations=sum(o['certificate_status']=='checked_complete_derivation' for o in observations),certificate_unknown=sum(o['certificate_status']=='certificate_unknown' for o in observations),external_search_seconds=sum(o['wall_seconds'] for o in observations),verification_seconds=sum(o['verification_seconds'] for o in observations),input_and_library_seconds=sum(s['export_and_library_check_seconds'] for s in setup),
                gcts_reference=[dict(case=c['spec']['id'],observations=[{k:o.get(k) for k in ('lane','repetition','status','seconds','setup_seconds','worker_wall_seconds','peak_rss_bytes','metrics')} for o in c['observations']]) for c in x['cases']],
                limits=plan['comparison_limits'],conformance='External specialized control: TPTP first-order saturation, not reference point-value GCTS. No tile/frontier/generation/rollback conformance claim. All GCTS reference observations retain Notebook 68 semantics.')
    dump(out/'summary.json',result)

if __name__=='__main__':main()
