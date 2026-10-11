"""Bounded complete catalog construction and conformance probes, no target search."""
import copy,gzip,hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
import hilbert_transport_adapter_v1 as T
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'.gcts-active/hilbert-constant-certificates-20261011'
sys.path.insert(0,str(OLD));import hilbert_constant_checker_v3 as C
class Budget(Exception):pass
def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def guard():
    if peak()>512*1024*1024:raise Budget('kernel peak above512MiB')
def load(p):
    guard();b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def pin(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def save(p,x):
    b=(json.dumps(x,separators=(',',':'),ensure_ascii=False)+'\n').encode();guard();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b);guard()
def setup():
    out=[]
    for typ in [resource.RLIMIT_DATA,resource.RLIMIT_AS]:
        old=resource.getrlimit(typ);target=min([512*1024*1024]+[v for v in old if v!=resource.RLIM_INFINITY])
        try:resource.setrlimit(typ,(target,old[1]));out.append(dict(kind=typ,status='set_soft',prior=old,requested=target,actual=resource.getrlimit(typ)))
        except (ValueError,OSError) as e:out.append(dict(kind=typ,status='unsupported',prior=old,requested=target,reason=str(e)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Budget('180s ceiling')));signal.alarm(180);return out

def bind(plan):
    for rel,p in {**plan['source_pins'],**plan['inputs']}.items():T.require(pin(ROOT/rel)==p,'exact frozen file '+rel)
    entries=0
    for rel,p in plan['preserved_manifests'].items():
        T.require(pin(ROOT/rel)==p,'preserved manifest')
        for r in load(ROOT/rel)['files']:T.require(pin(ROOT/r['path'])==dict(sha256=r['sha256'],bytes=r['bytes']),'preserved raw evidence');entries+=1
    record=load(ROOT/plan['source_record'])[0];receipt=load(ROOT/plan['source_receipt']);source=load(ROOT/plan['source_snapshot']);cert=load(ROOT/plan['certificate'])
    T.require(record['request_sha256']==receipt['request_sha256']==source['source_request_sha256']==plan['source_request_sha256'],'exact donor request')
    T.require(record['result']['status']==receipt['native_outcome']=='accepted' and receipt['status']=='passed' and record['result']['micro_steps']==receipt['native_micro_steps'],'actual full native replay binding')
    binding=dict(request_sha256=record['request_sha256'],input_sha256=record['input_sha256'],output_sha256=record['output_sha256'],native_record_file_sha256=plan['inputs'][plan['source_record']]['sha256'],native_receipt_file_sha256=plan['inputs'][plan['source_receipt']]['sha256'],native_micro_steps=record['result']['micro_steps'])
    C.check(cert,source,binding)
    previous=load(ROOT/plan['structural_audit']);T.require(previous['status']=='passed_finite_structural_audit' and previous['certificate_sha256']==plan['inputs'][plan['certificate']]['sha256'],'exact finite audit receipt')
    ledger=load(ROOT/plan['ledger']);review=load(ROOT/plan['argument_review']);T.require(review['status']=='passed_independent_read_only_source_level_argument_review','argument independently reviewed')
    for rel,p in ledger['sources'].items():T.require(pin(ROOT/rel)==p,'literal source argument branch pin')
    return cert,source,binding,entries

def build(cert,plan):
    rules=T.registry(cert,T.authority(plan));seeds=[dict(name='local-common-lm',kind='assumption',formula=T.guard('P','Q','l','m')),dict(name='local-common-mn',kind='assumption',formula=T.guard('P','Q','m','n')),dict(name='local-incidence',kind='assumption',formula=T.incident('R','l')),dict(name='I.2-uniqueness',kind='axiom',formula=cert['recipient_theory']['axioms']['I.2-uniqueness'])]
    model=T.compile_rows(rules,seeds,plan['rows'],T.incident('R','n'));model['interfaces']=rules;model['authority']=T.authority(plan);return model

def verify(model,cert,plan,source,binding):
    C.check(cert,source,binding);T.require(model==build(cert,plan),'literal complete catalog and authority correspondence')

def raw_view(model,selected):
    totals={tuple(q):0 for q in model['required']};marks={tuple(q[:2]):q[2] for q in model['fixed_m']};byid={c['id']:c for c in model['placements']};chosen=set(selected)
    for k in selected:
        c=byid[k]
        for x,y,v in c['t']:totals[(x,y)]+=v
        for x,y,v in c['m']:
            if (x,y) in marks and marks[(x,y)]!=v:return None
            marks[(x,y)]=v
    if any(v>1 for v in totals.values()):return None
    frontier=sorted(q for q,v in totals.items() if v<1);edges={str(q):[] for q in frontier}
    for c in model['placements']:
        if T.compatible(c,totals,marks,chosen) is None:
            for x,y,v in c['t']:
                if (x,y) in frontier and v>0:edges[str((x,y))].append(c['id'])
    for values in edges.values():values.sort()
    nodes=sorted(set(itertools.chain.from_iterable(edges.values())))
    action='dead' if any(not a for a in edges.values()) else 'forced' if any(len(a)==1 for a in edges.values()) else 'branch' if frontier else 'exact'
    point=None
    if action in ['forced','branch']:
        candidates=[q for q in frontier if action!='forced' or len(edges[str(q)])==1];point=min(candidates,key=lambda q:(0,len(edges[str(q)]),q))
    return dict(frontier=[list(q) for q in frontier],edges=edges,nodes=nodes,action=action,selected_point=list(point) if point else None,root_generations=[[q[0],q[1],0] for q in sorted(totals)])

def tiny_checks():
    model=T.tiny();byrow=[[None]+[b for b in model['ordered_bindings'] if b['row']==i] for i in range(3)];records=[];valid=0;full=0;orders=0
    for choices in itertools.product(*byrow):
        ids=[b['placement'] for b in choices if b is not None];out=None if None in ids else raw_view(model,ids)
        if out is not None:
            valid+=1;full+=int(len(ids)==3)
            for order in itertools.permutations(ids):
                graph=T.Graph(model);before=graph.snapshot()
                for k in order:graph.place(k)
                T.require(graph.view()==out,'tiny complete graph')
                while graph.trail:graph.undo()
                T.require(graph.snapshot()==before,'tiny exact rollback');orders+=1
        records.append(dict(choices=[b['placement'] if b else '-' for b in choices],legal=out is not None,view_sha256=T.digest(out) if out else None))
    T.require(len(records)==315,'all capacity-legal tiny symbolic selections')
    # Every subset outside the row-selection enumeration has >=2 unit tiles
    # at one required point and is rejected by t capacity. Pair census checks it.
    pairs=0
    for i in range(3):
        ids=[c['id'] for c in model['placements'] if c['row']==i and T.compatible(c,{}, {tuple(q[:2]):q[2] for q in model['fixed_m']},set()) is None]
        for a,b in itertools.combinations(ids,2):T.require(raw_view(model,[a,b]) is None,'overlap pair');pairs+=1
    return model,dict(selections=315,legal_partial_selections=valid,exact_full_selections=full,permutation_rollback_checks=orders,same_row_capacity_rejections=pairs,records=records)

def main():
    os_limits=setup();began=time.perf_counter();plan=load(HERE/'plan-v1.json');stage=time.perf_counter();cert,source,binding,entries=bind(plan);binding_seconds=time.perf_counter()-stage
    stage=time.perf_counter();model=build(cert,plan);construction=time.perf_counter()-stage;guard();graph=T.Graph(model);initial=graph.view();T.require(initial==raw_view(model,[]),'complete initial graph')
    syntax=model['ordered_bindings'];counts=dict(definitions=len(model['interfaces']),formula_codes=len(model['formula_codes']),prototypes=len(model['prototypes']),rejected_prototypes=len(model['rejected_prototypes']),raw_alignments=len(model['placements']),strict_prior_bindings=len(syntax),inconsistent_strict_prior=sum(b['placement'] is None for b in syntax),consistent_strict_prior=sum(b['placement'] is not None for b in syntax),initial_point_candidates=len(initial['nodes']))
    T.require(counts==plan['predicted_counts'],'all frozen count predictions')
    stage=time.perf_counter();probes=[];before=graph.snapshot()
    for k in initial['nodes']:
        graph.place(k);view=graph.view();T.require(view==raw_view(model,[k]),'all single-placement full graph domains');probes.append(dict(placement=k,view_sha256=T.digest(view),action=view['action'],nodes=len(view['nodes'])));graph.undo();T.require(graph.snapshot()==before,'full recipient exact rollback');guard()
    graph_seconds=time.perf_counter()-stage;stage=time.perf_counter();tiny_model,tiny=tiny_checks();tiny_seconds=time.perf_counter()-stage
    stage=time.perf_counter();corruptions=[]
    for case in plan['corruptions']:
        target=copy.deepcopy(model if case['target']=='model' else cert);part=target
        for k in case['path'][:-1]:part=part[k]
        key=case['path'][-1]
        if case['operation']=='delete':part.pop(key)
        elif case['operation']=='append':part[key].append(copy.deepcopy(part[key][case['copy_index']]))
        else:part[key]=copy.deepcopy(case['value'])
        try:verify(target if case['target']=='model' else model,target if case['target']=='certificate' else cert,plan,source,binding)
        except (C.Invalid,T.Invalid,KeyError,IndexError,TypeError) as e:corruptions.append(dict(name=case['name'],mutant_sha256=T.digest(target),status='rejected',reason=str(e)))
        else:raise T.Invalid('corruption accepted '+case['name'])
    corruption_seconds=time.perf_counter()-stage;save(HERE/'catalog-v1.json.gz',model);save(HERE/'graph-probes-v1.json',dict(initial_view=initial,probes=probes));save(HERE/'tiny-checks-v1.json',tiny);save(HERE/'tiny-model-v1.json',tiny_model);save(HERE/'corruptions-v1.json',corruptions)
    reader=dict(descriptors=model['descriptors'],interfaces=model['interfaces'],prototypes=model['prototypes'],formula_codes=model['formula_codes'],counts=counts,initial=initial,source_binding=binding);save(HERE/'reader-data-v1.json',reader);guard()
    result=dict(status='passed_finite_point_catalog_production',plan_sha256=pin(HERE/'plan-v1.json')['sha256'],catalog_sha256=pin(HERE/'catalog-v1.json.gz')['sha256'],counts=counts,all_single_placement_graph_probes=len(probes),tiny={k:v for k,v in tiny.items() if k!='records'},rejected_corruptions=len(corruptions),preserved_file_entries=entries,binding_seconds=binding_seconds,construction_seconds=construction,graph_probe_seconds=graph_seconds,tiny_seconds=tiny_seconds,corruption_seconds=corruption_seconds,production_seconds_before_final_write=time.perf_counter()-began,peak_rss_bytes=peak(),os_limits=os_limits,native_queries=0,target_searches=0,existing_native_engine_activation=False,formal_native_compiler_correspondence='open',aggregate_cluster_t_expansion_correspondence='open',authority='certified_transport_exact_finite_symbolic_relation')
    save(HERE/'production-v1.json',result);print(json.dumps(result),flush=True);signal.alarm(0)
if __name__=='__main__':main()
