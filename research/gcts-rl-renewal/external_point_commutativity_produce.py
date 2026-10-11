"""Cold Boolean SAT control for the exact complete scalar t/m universe.

No target word, induction path, ordinary closure or proof tactic is an input.
UNSAT remains an unchecked solver assertion. Unit occupancy is the exact
arithmetic model's declared restriction, not a general fractional-t encoder.
"""
import copy,gzip,hashlib,json,resource,signal,sys,time
from pathlib import Path
import z3
from commutativity_cluster_points import Model

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.gcts-active/external-point-commutativity-20261011'
class Unknown(Exception):pass
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def rss():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def guard(start):
    if time.perf_counter()-start>180:raise Unknown('producer wall budget')
    if rss()>536870912:raise Unknown('producer peak RSS budget')
def load(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def save(p,x):
    b=canonical(x);p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)
def exact_model(model):
    placements=[]
    for key,c in sorted(model.cache.items()):
        placements.append(dict(key=list(key),occupancy=c.occupancy,marks=c.marks,**model.metadata[key]))
    state=model.initial()
    return json.loads(canonical(dict(length=model.spec['length'],roots=sorted(model.align_cache),
        initial_marks=sorted(model.initial().marks.items()),placements=placements,
        rules=model.rules,rule_modes=[model.rule_modes[i] for i in range(len(model.rules))],
        semantic=dict(schema='exact-scalar-point-model-v1',length=model.spec['length'],
            required_points=[dict(point=p,generation=0) for p in sorted(model.align_cache)],
            initial=dict(roots=sorted(state.roots.items()),generations=sorted(state.generations.items()),
                         marks=sorted(state.marks.items()),totals=[],allowed_points=sorted(state.allowed_points)),
            placements=placements,injective_catalog=model.catalog.record(),inference_rules=model.rules,
            rule_modes=[model.rule_modes[i] for i in range(len(model.rules))],row_domains=model.domains,
            arity=2,capacity=12,registry_sha256=model.registry_sha256),
        capacity=12,scope='Full unit-capacity scalar point adaptation; fixed orientations, all distant assigned marks.')))

def encode(model):
    variables=[];clauses=[];occupancy={tuple(p):[] for p in model['roots']}
    marking={};assignments=[];groups=[]
    def variable(v):variables.append(v);return len(variables)
    for c in model['placements']:
        if len(c['occupancy'])!=1 or c['occupancy'][0][1]!=12 or tuple(c['occupancy'][0][0]) not in occupancy:
            raise ValueError('encoder supports exactly this unit center model')
        i=variable(dict(kind='placement',key=c['key']))
        occupancy[tuple(c['occupancy'][0][0])].append(i)
        seen={}
        for p,value in c['marks']:
            if type(value) is not int:raise ValueError('exact integer mark')
            t=tuple(p)
            if t in seen and seen[t]!=value:raise ValueError('internally unequal assigned mark')
            seen[t]=value;marking.setdefault((t,value),None);assignments.append((i,t,value))
    for p,value in model['initial_marks']:marking.setdefault((tuple(p),value),None)
    for (p,value) in sorted(marking):marking[p,value]=variable(dict(kind='mark',point=list(p),value=value))
    def at_most_one(ids,family,point):
        groups.append(dict(family=family,point=list(point),variables=ids))
        if len(ids)<2:return
        prefix=[variable(dict(kind='prefix',family=family,point=list(point),prefix_length=i+1)) for i in range(len(ids)-1)]
        clauses.append([-ids[0],prefix[0]])
        for i in range(1,len(ids)-1):
            clauses.extend([[-ids[i],prefix[i]],[-prefix[i-1],prefix[i]],[-ids[i],-prefix[i-1]]])
        clauses.append([-ids[-1],-prefix[-1]])
    for p,ids in sorted(occupancy.items()):
        clauses.append(ids.copy());at_most_one(ids,'occupancy',p)
    bypoint={}
    for (p,value),i in sorted(marking.items()):bypoint.setdefault(p,[]).append(i)
    for p,ids in sorted(bypoint.items()):at_most_one(ids,'mark',p)
    for i,p,value in assignments:clauses.append([-i,marking[p,value]])
    for p,value in model['initial_marks']:clauses.append([marking[tuple(p),value]])
    return dict(variables=variables,clauses=clauses,groups=groups,
        equivalence='Exactly-one occupancy and optional at-most-one assigned value per marking point; each selected placement implies every original marking assignment. Prefix auxiliaries have a constructive existential extension. Missing marking stays unconstrained; zero is assigned.')

def dimacs(cnf):
    return ('p cnf '+str(len(cnf['variables']))+' '+str(len(cnf['clauses']))+'\n'+
        ''.join(' '.join(map(str,c))+' 0\n' for c in cnf['clauses'])).encode()

def solve(cnf,seconds,start):
    before=time.perf_counter();ctx=z3.Context(proof=True);solver=z3.Solver(ctx=ctx)
    solver.set(random_seed=0,timeout=int(seconds*1000),max_memory=430)
    xs=[z3.Bool('v'+str(i+1),ctx=ctx) for i in range(len(cnf['variables']))]
    batch=[]
    for clause in cnf['clauses']:
        batch.append(z3.Or(*[(xs[l-1] if l>0 else z3.Not(xs[-l-1])) for l in clause]))
        if len(batch)==1024:solver.add(*batch);batch=[];guard(start)
    if batch:solver.add(*batch)
    preparation=time.perf_counter()-before;guard(start)
    remaining=min(seconds,180-(time.perf_counter()-start)-5)
    if remaining<=0:raise Unknown('no remaining complete solver budget')
    solver.set(timeout=max(1,int(remaining*1000)))
    check=time.perf_counter();status=solver.check();query=time.perf_counter()-check;guard(start)
    result=dict(solver_result=str(status),solver_setup_seconds=preparation,solver_seconds=query,
                configured_query_seconds=remaining,z3_statistics={k:str(solver.statistics().get_key_value(k)) for k in solver.statistics().keys()})
    if status==z3.sat:
        t=time.perf_counter();m=solver.model()
        result['assignment']=[z3.is_true(m.eval(x,model_completion=True)) for x in xs]
        result['assignment_extraction_seconds']=time.perf_counter()-t
        result['status']='sat_assignment_pending_independent_point_and_encoding_audit'
    elif status==z3.unsat:
        t=time.perf_counter();proof=solver.proof().sexpr()
        result.update(status='solver_unsat_assertion_unchecked_certificate',unchecked_solver_proof=proof,
                      proof_serialization_seconds=time.perf_counter()-t,
                      unsat_authority='No independently checked refutation; not finite exhaustion or theorem nonprovability.')
    else:result.update(status='unknown_solver',reason_unknown=solver.reason_unknown())
    guard(start);return result

def main():
    start=time.perf_counter();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Unknown('producer alarm')))
    mode=sys.argv[1] if len(sys.argv)>1 else '--prepare'
    if mode not in ['--prepare','--solve']:raise ValueError('explicit stage required')
    prior=load(OUT/'stage-costs.json').get('producer_seconds',0) if (OUT/'stage-costs.json').exists() else 0
    start-=prior;signal.alarm(max(1,int(180-prior)))
    summary=dict(status='running',observations=[],native_queries=0,target_word_seed=False,new_RL_training=False)
    try:
        plan=load(OUT/'plan.json')
        for rel,p in {**plan['sources'],**plan['inputs']}.items():
            if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=p['sha256']:raise ValueError('frozen input/source '+rel)
        for absolute,p in plan['runtime'].items():
            if hashlib.sha256(Path(absolute).read_bytes()).hexdigest()!=p['sha256']:raise ValueError('frozen solver runtime')
        source=load(ROOT/plan['inputs_role']['spec']);catalog=load(ROOT/plan['inputs_role']['catalog'])
        registry_path=ROOT/plan['inputs_role']['registry'];registry=load(registry_path);receipt=load(ROOT/plan['inputs_role']['registry_audit'])
        encoded=[];encoding_began=time.perf_counter()
        for length in (plan['lengths'] if mode=='--prepare' else []):
            spec=copy.deepcopy(source['case']);spec['length']=length
            point_began=time.perf_counter();model=Model(spec,catalog,registry,receipt,registry_path.read_bytes());record=exact_model(model)
            point_seconds=time.perf_counter()-point_began;guard(start)
            point_path=OUT/('point-'+str(length)+'.json.gz');save(point_path,record)
            cnf_began=time.perf_counter();cnf=encode(record);cnf_path=OUT/('encoding-'+str(length)+'.json.gz');save(cnf_path,cnf)
            raw=dimacs(cnf);dimacs_path=OUT/('point-'+str(length)+'.cnf.gz');dimacs_path.write_bytes(gzip.compress(raw,mtime=0));guard(start)
            encoded.append(dict(length=length,point_seconds=point_seconds,encoding_serialization_seconds=time.perf_counter()-cnf_began,
                placements=len(record['placements']),roots=len(record['roots']),variables=len(cnf['variables']),clauses=len(cnf['clauses']),
                point_file_sha256=hashlib.sha256(point_path.read_bytes()).hexdigest(),encoding_file_sha256=hashlib.sha256(cnf_path.read_bytes()).hexdigest(),
                dimacs_file_sha256=hashlib.sha256(dimacs_path.read_bytes()).hexdigest(),dimacs_raw_sha256=hashlib.sha256(raw).hexdigest(),
                semantic_sha256=digest(record['semantic'])))
            del cnf,record,model,raw
        if mode=='--prepare':
            save(OUT/'encoding-freeze.json',dict(status='complete_both_encodings_frozen_before_any_solver_query',plan_sha256=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest(),
                models=encoded,preparation_seconds=time.perf_counter()-encoding_began,order=plan['lengths'],no_solver_calls_yet=True))
            summary['status']='prepared_no_solver_queries';return
        frozen=load(OUT/'encoding-freeze.json');encoded=frozen['models']
        if frozen['plan_sha256']!=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest():raise ValueError('encoding plan binding')
        cross=load(OUT/'cross-track.json')
        if cross['status']!='passed_exact_12_and_13_semantic_hash_agreement':raise ValueError('independent cross-track hash gate')
        for item in encoded:
            n=item['length']
            if cross['semantic_sha256'][str(n)]!=item['semantic_sha256']:raise ValueError('cross-track hash')
            for label,name in [('point_file_sha256','point-'+str(n)+'.json.gz'),('encoding_file_sha256','encoding-'+str(n)+'.json.gz'),('dimacs_file_sha256','point-'+str(n)+'.cnf.gz')]:
                if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=item[label]:raise ValueError('frozen encoding altered')
        save(OUT/'query-freeze.json',dict(status='exact_encoding_and_cross_track_gate_frozen_before_queries',
            plan_sha256=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest(),
            encoding_freeze_sha256=hashlib.sha256((OUT/'encoding-freeze.json').read_bytes()).hexdigest(),
            cross_track_sha256=hashlib.sha256((OUT/'cross-track.json').read_bytes()).hexdigest(),
            prior_producer_process_seconds=prior,order=plan['lengths'],no_solver_calls_yet=True))
        for item in encoded:
            length=item['length'];cnf=load(OUT/('encoding-'+str(length)+'.json.gz'));guard(start)
            t=time.perf_counter();result=solve(cnf,plan['per_query_seconds'],start)
            result.update(length=length,encoding=item,query_and_certificate_seconds=time.perf_counter()-t,
                          point_model_authority='Same finite t/m region; solver assertion alone is not a proof theorem/native acceptance.')
            if 'assignment' in result:
                selected=[v['key'] for v,value in zip(cnf['variables'],result['assignment']) if value and v['kind']=='placement']
                result['placements']=selected
                spec=copy.deepcopy(source['case']);spec['length']=length
                model=Model(spec,catalog,registry,receipt,registry_path.read_bytes());result['producer_decoded_word']=model.decode([tuple(k) for k in selected]);del model
            save(OUT/('result-'+str(length)+'.json.gz'),result);guard(start)
            compact={k:v for k,v in result.items() if k not in ['assignment','placements','producer_decoded_word','unchecked_solver_proof']}
            summary['observations'].append(compact);save(OUT/'production.json',summary);print(json.dumps(compact),flush=True)
            del result,cnf
        summary['status']='complete_solver_observations_pending_independent_audit'
    except (Unknown,MemoryError,z3.Z3Exception) as e:summary.update(status='unknown_producer_resource_or_solver',reason=type(e).__name__+': '+str(e))
    finally:
        signal.alarm(0);summary.update(process_seconds_before_final_result_write=time.perf_counter()-start,peak_rss_bytes=rss())
        if summary['process_seconds_before_final_result_write']>180 or summary['peak_rss_bytes']>536870912:summary['status']='unknown_producer_resource'
        save(OUT/('preparation.json' if mode=='--prepare' else 'production.json'),summary);print(json.dumps({k:v for k,v in summary.items() if k!='observations'}),flush=True)
if __name__=='__main__':main()
