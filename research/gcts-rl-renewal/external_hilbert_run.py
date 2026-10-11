"""Exact guarded Hilbert I.2 assertions as a separate external E control.

The source snapshots, explicit theory/target, full admitted interfaces and all
budgets are frozen before any E recipient run. Schemas are rejected unless
their logical meaning has been exported as explicit first-order axioms.
"""
import argparse,copy,json,pathlib,platform,re,sys,time
from external_prover_inputs import make_input,sha,canonical
from external_prover_check import native_formula,formula_text,alpha,entails,check_output
from external_prover_run import execute

PIN='3b7afc70fe77d3118bb95144c4735ca45f5f31cf'
EXPECTED={'external-inputs.json':'fbd5dfd7490b251f062e0c9b4a02d650ffdab93d1cbf8ccdc9e83358bf68040e',
          'external-negative-inputs.json':'3b9c26b13449831d5abf7f87b557fc12edb8c089eff9249400d3ff8b1591e894'}

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def validate_theory(spec):
    theory=spec['theory']
    if set(theory)-{'functions','predicates','axioms','schemas'}:raise ValueError('unexported theory feature')
    if theory.get('schemas'):raise ValueError('nonempty theory schemas must be explicitly exported before comparison')
    if any(type(a) is not int or a<0 for s in ('functions','predicates') for a in theory[s].values()):raise ValueError('signature arity')

def evaluate_countermodel(spec,entries,model):
    """Full finite interpretation evaluation, separate from E and search."""
    domain=model['domain'];constants=model['constants'];predicates={n:{tuple(t) if isinstance(t,list) else (t,) for t in model[n]} for n in spec['theory']['predicates']}
    if len(set(domain))!=len(domain) or not domain:raise ValueError('model domain')
    if set(constants)!=set(spec['theory']['functions']) or any(v not in domain for v in constants.values()):raise ValueError('model constants')
    for n,ts in predicates.items():
        if any(len(t)!=spec['theory']['predicates'][n] or any(v not in domain for v in t) for t in ts):raise ValueError('model predicate table')
    def term(t,env):
        if t[0]=='var':return env[t[1]]
        if t[0]!='fun' or t[2]:raise ValueError('model requires function table')
        return constants[t[1]]
    def ev(f,env=None):
        env={} if env is None else env;h=f[0]
        if h=='bot':return False
        if h=='top':return True
        if h=='pred':return tuple(term(t,env) for t in f[2]) in predicates[f[1]]
        if h=='eq':return term(f[1],env)==term(f[2],env)
        if h=='not':return not ev(f[1],env)
        if h=='imp':return not ev(f[1],env) or ev(f[2],env)
        if h=='and':return ev(f[1],env) and ev(f[2],env)
        if h=='or':return ev(f[1],env) or ev(f[2],env)
        if h=='all':return all(ev(f[2],{**env,f[1]:v}) for v in domain)
        raise ValueError('unsupported model formula '+h)
    axioms={n:ev(f) for n,f in spec['theory']['axioms'].items()};lemmas={e['name']:ev(e['formula']) for e in entries if e['role']=='lemma'};target=ev(spec['target'])
    if not all(axioms.values()) or not all(lemmas.values()) or target:raise ValueError('countermodel rejected')
    return dict(status='independently_checked_countermodel',domain=domain,constants=constants,predicates={n:sorted(ts) for n,ts in predicates.items()},axioms=axioms,lemmas=lemmas,target=target,
                scope='The supplied finite audit interpretation is reevaluated against every exact first-order input. It is neither an E proof/model certificate nor a search input.')

def dependencies(definition,spec):
    names=sorted({r['name'] for r in definition['proof'] if r['rule']=='axiom'})
    if any(n not in spec['theory']['axioms'] for n in names):raise ValueError('undeclared lemma axiom')
    if any(r['rule']=='block' for r in definition['proof']):raise ValueError('dependency closures need explicit export for non-leaf lemma definitions')
    return names

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='.gcts-active/hilbert-receptors-20261011');ap.add_argument('--output',default='.gcts-active/external-hilbert-20261011');ap.add_argument('--e',default='/private/tmp/gcts-external-eprover-20261011/PROVER/eprover');a=ap.parse_args()
    out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);source=pathlib.Path(a.source);began=time.perf_counter();snapshots=[]
    for name,expected in EXPECTED.items():
        b=(source/name).read_bytes()
        if sha(b)!=expected:raise ValueError('source snapshot changed '+name)
        (out/name).write_bytes(b);snapshots.append(json.loads(b))
    positive,negative=snapshots
    cases=[dict(spec=positive['positive'],inventory=positive['inventory'],native_records=positive['native_records'],context=positive['status'],countermodel=None),
           dict(spec=negative['spec'],inventory=negative['inventory'],native_records=negative['native_records'],context=negative['status'],countermodel=negative['countermodel'])]
    inputs=[]
    for c in cases:
        validate_theory(c['spec'])
        for family in [False,True]:
            m=make_input(c,family);path=out/(m['case']+'-'+('library' if family else 'theory')+'.p');path.write_text(m['text']);m['input_path']=str(path)
            for e in m['entries']:
                text=m['text'].split('fof('+e['name']+','+e['role']+',',1)[1].split(').\n',1)[0]
                if alpha(formula_text(text))!=alpha(native_formula(e['formula'],m)):raise ValueError('independent AST round trip failed')
            dump(path.with_suffix('.mapping.json'),m);inputs.append((m,c))
    sources=[pathlib.Path(__file__)]+[pathlib.Path(__file__).with_name(n) for n in ['external_prover_inputs.py','external_prover_check.py','external_prover_run.py','external_prover_worker.py']]
    closure={str(p):sha(p.read_bytes()) for p in sources}
    options=['--auto','--proof-object','--tstp-format','--cpu-limit=60','--memory-limit=1024','--resources-info','--print-statistics']
    import subprocess
    version=subprocess.run([a.e,'--version'],capture_output=True,text=True,check=True).stdout.strip()
    plan=dict(version='external-hilbert-plan-1',status='frozen_before_recipient_measurement',source_snapshot_sha256=EXPECTED,source_sha256=closure,
              inputs=[dict(case=m['case'],lane=m['lane'],input_path=m['input_path'],input_sha256=m['sha256'],mapping_sha256=sha(pathlib.Path(m['input_path']).with_suffix('.mapping.json').read_bytes()),lemma_count=sum(e['role']=='lemma' for e in m['entries'])) for m,c in inputs],
              source_commit=PIN,prover_version=version,prover_binary_sha256=sha(pathlib.Path(a.e).read_bytes()),command_options=options,repetitions=2,order='Positive then removed-I.2 control; theory then library in repetition 1, reverse lanes in repetition 2',wall_timeout_seconds=65,memory_limit_MiB=1024,
              theory_policy='Only explicit first-order axioms, exact guarded I.2 with all four quantifiers retained, ordinary constants and uninterpreted predicates. Nonempty schemas and unsupported theory fields fail closed. Full ground library, not the blocks used by a selected proof.',
              verification_policy='Every returned input and preprocessing/inference checked by existing independent finite Herbrand/EUF refutation validator. New scoped witness transformations are required before any unsupported E-introduced symbol can pass; no skipped steps or SZS-only success.',
              comparison_scope='Same first-order assertions and admitted lemma interfaces, different search calculus/certificate language. E has no fixed 4-row boundary and no restriction to GCTS finite point/line ground catalog. Short 3-row geometry is the same logical assertion and is not another logical control.',
              native_context=positive['status'],cost_policy='Preparation and interface checking, fresh E binary and worker timing/RSS, returned-proof checking, audit costs reported separately. Pinned E source/build costs are disclosed reuse from completed external_prover experiment; no fresh build. Geometry native admission is reused, with full native replay provenance supplied by its separately completed audit.')
    dump(out/'plan.json',plan);plan_sha=sha((out/'plan.json').read_bytes());setup=[]
    for m,c in inputs:
        t=time.perf_counter();checks=[];native={r['id']:r for r in c['native_records']};definitions={d['name']:d for d in c['inventory']['native_blocks']}
        for e in m['entries']:
            if e['role']!='lemma':continue
            d=definitions[e['original_name']];q=native[e['native_admission']]
            if q['result']['status']!='accepted' or q['request']['theory']!=c['spec']['theory'] or d not in q['request']['blocks']:raise ValueError('native admission identity')
            if sha(canonical(q['request']))!=q['request_sha256']:raise ValueError('native request digest')
            names=dependencies(d,c['spec']);parents=[native_formula(c['spec']['theory']['axioms'][n],m) for n in names]
            check=entails(parents,native_formula(e['formula'],m))
            if check['status']!='checked':raise ValueError('independent lemma interface validation unknown '+e['original_name'])
            checks.append(dict(name=e['name'],original_name=e['original_name'],native_query=q['id'],native_request_sha256=q['request_sha256'],axiom_dependencies=names,**check))
        cm=evaluate_countermodel(c['spec'],m['entries'],c['countermodel']) if c['countermodel'] else None
        setup.append(dict(case=m['case'],lane=m['lane'],independent_library_and_model_seconds=time.perf_counter()-t,library_checks=checks,countermodel=cm))
    dump(out/'setup.json',setup);observations=[]
    for rep in [1,2]:
        for ci in range(len(cases)):
            for lane in ([0,1] if rep==1 else [1,0]):
                index=2*ci+lane;m,c=inputs[index];base=m['case']+'-'+('library' if lane else 'theory')+'-r'+str(rep);cmd=[a.e,*options,m['input_path']]
                run=execute(cmd,65);stdout=run.pop('stdout');stderr=run.pop('stderr');(out/(base+'.tstp')).write_text(stdout);(out/(base+'.stderr')).write_text(stderr)
                statuses=re.findall(r'^% SZS status (\S+)',stdout,re.M);status=statuses[-1] if statuses else None;t=time.perf_counter()
                if status in ('Theorem','Unsatisfiable') and not run['timed_out']:
                    try:check=check_output(stdout,m,m['input_path'])
                    except Exception as e:check=dict(status='certificate_unknown',error=str(e))
                else:check=dict(status='no_refutation_certificate',countermodel=setup[index]['countermodel'])
                checking_seconds=time.perf_counter()-t;dump(out/(base+'.check.json'),check)
                obs=dict(case=m['case'],lane=m['lane'],repetition=rep,command=cmd,input_sha256=m['sha256'],output_sha256=sha(stdout),stderr_sha256=sha(stderr),szs_status=status,certificate_status=check['status'],checking_seconds=checking_seconds,proof_steps=check.get('steps'),used_lemma_inputs=check.get('used_lemma_inputs',[]),**run)
                observations.append(obs);dump(out/'observations.json',observations);print(base,status,check['status'],run['wall_seconds'],checking_seconds,flush=True)
    for p,h in closure.items():
        if sha(pathlib.Path(p).read_bytes())!=h:raise ValueError('measured source changed')
    result=dict(version='external-hilbert-control-1',status='complete',plan_sha256=plan_sha,plan=plan,source_sha256=closure,observations=observations,setup=setup,total_seconds=time.perf_counter()-began,
                checked_derivations=sum(o['certificate_status']=='checked_complete_derivation' for o in observations),certificate_unknown=sum(o['certificate_status']=='certificate_unknown' for o in observations),external_search_seconds=sum(o['wall_seconds'] for o in observations),fresh_worker_seconds=sum(o['fresh_worker_wall_seconds'] for o in observations),checking_seconds=sum(o['checking_seconds'] for o in observations),library_and_countermodel_seconds=sum(x['independent_library_and_model_seconds'] for x in setup),platform=platform.platform(),
                native_checker_scope='External certificates are independently checked first-order derivations, not native Wang acceptances. All admission provenance is bound to reused exact requests; geometry full native replay remains a separate experiment.')
    dump(out/'summary.json',result)

if __name__=='__main__':main()
