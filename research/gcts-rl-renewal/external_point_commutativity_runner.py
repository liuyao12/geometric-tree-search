"""Frozen, staged local-only control. No installation or native queries."""
import ast,gzip,hashlib,json,os,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'.gcts-active/external-point-commutativity-20261011'
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def entry(p):b=p.read_bytes();return dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(p.read_bytes())
def save(p,x):p.write_bytes(packed(x))
def freeze():
    began=time.perf_counter();OUT.mkdir(exist_ok=True)
    if (OUT/'plan.json').exists():raise ValueError('immutable plan already exists')
    roots=[HERE/('external_point_commutativity_'+s+'.py') for s in ['produce','audit','runner','export']]
    pending=roots[:];sources=set()
    while pending:
        path=pending.pop()
        if path in sources:continue
        sources.add(path);tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            names=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.level==0 and node.module else []
            for name in names:
                dep=HERE/(name.split('.')[0]+'.py')
                if dep.exists():pending.append(dep)
    master=ROOT/'docs/basic-tiling-algorithm.md';sources.add(master)
    roles=dict(spec='.gcts-active/commutativity-cluster-search-20261011/plan.json',catalog='.gcts-active/commutativity-receptors-20261011/attempt-02/two-lemmas-retained-core.json.gz',registry='.gcts-active/commutativity-receptors-20261011/native-complete/registry.json.gz',registry_audit='.gcts-active/commutativity-receptors-20261011/native-complete/registry-audit.json',baseline='.gcts-active/commutativity-cluster-search-20261011/preflight-model.json.gz')
    inputpaths=list(roles.values())+['.gcts-active/commutativity-cluster-search-20261011/preflight-audit.json','.gcts-active/commutativity-cluster-search-20261011/execution-freeze.json','.gcts-active/commutativity-receptors-20261011/native-complete/integration.json']
    import z3
    package=Path(z3.__file__).parent;runtime=[Path(sys.executable).resolve()]+sorted(package.glob('*.py'))+sorted((package/'lib').glob('*.dylib'))
    plan=dict(id='external-point-commutativity-20261011',status='frozen_before_encoding_or_solver_queries',lengths=[12,13],per_query_seconds=60,
        budgets=dict(producer_cumulative_wall_seconds=180,audit_cumulative_wall_seconds=180,peak_rss_bytes=536870912,z3_max_memory_MiB=430,soft_OS_limits='Not relied upon; kernel peak admission and parent kill/wait timeout plus internal alarms. Peak checks may reject after overshoot.'),
        stages=['freeze','prepare both complete encodings','independent cross-track semantic hash gate','cold12 query','cold13 query','independent full encoding and SAT audit','export'],
        runtime_version=dict(python=sys.version,executable=sys.executable,z3=z3.get_version_string(),z3_package=str(package),seed=0,proof_output=True),
        sources={str(p.relative_to(ROOT)):entry(p) for p in sorted(sources)},inputs={p:entry(ROOT/p) for p in inputpaths},runtime={str(p):entry(p) for p in runtime},inputs_role=roles,
        semantic_schema='exact-scalar-point-model-v1; canonical JSON sort_keys=True,separators=(comma,colon),ensure_ascii=False; placements numeric4-key, points numeric lexicographic, supports original sorted point support; dictionaries sorted full canonical word bytes; rules/row domains original order.',
        scope='Same finite94-admitted/153-interface scalar t/m grammar, all4 roots/row and all distant assigned marks. SAT solver is a specialized constraint control, not GCTS scheduler or RL. No target word seeds or target proof tactic. Twelve/thirteen row bounds are resource languages, not mathematics.',
        input_exclusions=['ordinary extracted target proof words','whole target request/capacity evidence','prior SAT assignments','prior target traces containing solutions'],
        unsat_scope='Any UNSAT output remains a solver assertion with unchecked proof text; no finite impossibility or theorem nonprovability claim.',
        independent_audit='Plain-data regeneration of entire candidate model/CNF/DIMACS; exhaustive tiny auxiliary-projection fixtures; explicit all-clause SAT valuation; original t/m and strict-prior decode; independent full serialized logical replay; actual saved corruptions. No native Wang query.',
        preparation_accounting='Freeze/runtime/source inspection measured separately. All producer encoding/setup/query/assignment/proof serialization plus child startup/final writes charged against cumulative180s; audit separately capped180s. Human development, reading and inter-track waiting not benchmarked.')
    with zipfile.ZipFile(OUT/'frozen-inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(sources):z.write(p,'project/'+str(p.relative_to(ROOT)))
        for p in inputpaths:z.write(ROOT/p,'project/'+p)
    plan['frozen_inputs_zip']=entry(OUT/'frozen-inputs.zip');plan['freeze_seconds_before_final_plan_write']=time.perf_counter()-began
    save(OUT/'plan.json',plan);print(json.dumps(dict(plan=entry(OUT/'plan.json'),sources=len(sources),inputs=len(inputpaths),runtime=len(runtime),freeze_seconds=plan['freeze_seconds_before_final_plan_write'])))
def run_stage(stage):
    plan=load(OUT/'plan.json');costpath=OUT/'stage-costs.json';costs=load(costpath) if costpath.exists() else dict(producer_seconds=0,audit_seconds=0,stages=[])
    category='audit' if stage=='audit' else 'producer';used=costs[category+'_seconds'];remaining=180-used
    if remaining<=0:raise ValueError('cumulative stage budget exhausted')
    if any(x['stage']==stage for x in costs['stages']):raise ValueError('immutable stage already run')
    file='audit' if stage=='audit' else 'produce';args=[sys.executable,str(HERE/('external_point_commutativity_'+file+'.py'))]+([] if stage=='audit' else ['--'+stage])
    began=time.perf_counter();out=OUT/(stage+'-stdout.txt');err=OUT/(stage+'-stderr.txt')
    with out.open('wb') as stdout,err.open('wb') as stderr:
        child=subprocess.Popen(args,cwd=HERE,stdout=stdout,stderr=stderr);timed_out=False
        try:child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:timed_out=True;child.kill();child.wait()
    duration=time.perf_counter()-began;costs[category+'_seconds']+=duration
    receipt=dict(stage=stage,command=args,duration_seconds=duration,exit_code=child.returncode,timed_out=timed_out,child_reaped=True,remaining_budget_at_start=remaining,
        gate='unknown_resource_or_process' if timed_out or child.returncode!=0 or costs[category+'_seconds']>180 else 'within_process_wall_gate',stdout=entry(out),stderr=entry(err))
    costs['stages'].append(receipt);save(costpath,costs);print(json.dumps(receipt))
if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1] in ['prepare','solve','audit']:run_stage(sys.argv[1])
    else:raise ValueError('explicit frozen stage')
