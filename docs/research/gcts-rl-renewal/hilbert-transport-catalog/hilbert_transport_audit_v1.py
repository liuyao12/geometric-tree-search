"""Independent tuple-source and point catalog reconstruction; no adapter imports."""
import copy,gzip,hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'.gcts-active/hilbert-constant-certificates-20261011'
sys.path.insert(0,str(OLD));import hilbert_constant_audit_v3 as A
class Budget(Exception):pass
def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def gate():
    if peak()>512*1024*1024:raise Budget('audit kernel peak above512MiB')
def read(p):
    gate();b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(sha256=hashfile(p),bytes=p.stat().st_size)
def enc(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(enc(x)).hexdigest()
def eq(a,b,why):A.require(enc(a)==enc(b),why)
def setup():
    out=[]
    for typ in [resource.RLIMIT_DATA,resource.RLIMIT_AS]:
        old=resource.getrlimit(typ);target=min([512*1024*1024]+[v for v in old if v!=resource.RLIM_INFINITY])
        try:resource.setrlimit(typ,(target,old[1]));out.append(dict(kind=typ,status='set_soft',prior=old,requested=target,actual=resource.getrlimit(typ)))
        except (ValueError,OSError) as e:out.append(dict(kind=typ,status='unsupported',prior=old,requested=target,reason=str(e)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Budget('180s audit ceiling')));signal.alarm(180);return out

def auth(plan):
    h=lambda key:plan['inputs'][plan[key]]['sha256']
    return dict(kind='certified_transport',scope='exact_finite_six_rule_symbolic_relation_only',certificate_sha256=h('certificate'),structural_audit_sha256=h('structural_audit'),source_native_record_sha256=h('source_record'),argument_sha256=h('argument'),ledger_sha256=h('ledger'),argument_review_sha256=h('argument_review'),source_request_sha256=plan['source_request_sha256'],epoch=plan['authority_epoch'],native_accepted=False,existing_engine_activated=False)
def incidence(p,l):return ('pred','Incident',(('fun',p,()),('fun',l,())))
def hypothesis(u,v):
    p=('fun','P',());q=('fun','Q',());s=('fun',u,());t=('fun',v,())
    xs=[('pred','Point',(p,)),('pred','Point',(q,)),('pred','Line',(s,)),('pred','Line',(t,)),('not',('eq',p,q)),('pred','Incident',(p,s)),('pred','Incident',(q,s)),('pred','Incident',(p,t)),('pred','Incident',(q,t))]
    tree=xs.pop()
    while xs:tree=('and',xs.pop(),tree)
    return tree

def lower(descriptors,rows,target=None):
    symbols={}
    for d in descriptors:
        for f in (*d['premises'],d['conclusion']):symbols[enc(f)]=f
    if target is not None:symbols[enc(target)]=target
    alphabet=[symbols[x] for x in sorted(symbols)];lookup={enc(x):j for j,x in enumerate(alphabet)}
    tiles=[];invalid=[];bindings={}
    for d in descriptors:
        inputs=[lookup[enc(f)] for f in d['premises']];result=lookup[enc(d['conclusion'])]
        for ds in itertools.product(tuple(range(-(rows-1),0)),repeat=len(inputs)):
            assignments=[(1,0,result)]+[(1,ds[k],inputs[k]) for k in range(len(inputs))]+[(2+k,0,ds[k]) for k in range(len(inputs))]
            grouped={};bad=False
            for x,y,val in assignments:
                at=(x,y)
                if at in grouped and grouped[at]!=val:bad=True
                grouped[at]=val
            if bad:
                invalid.append(dict(interface=d['name'],input_offsets=list(ds),reason='inconsistent_local_mark_function'));bindings[(d['name'],ds)]=None;continue
            body=dict(interface=d['name'],kind=d['kind'],family=d['family'],premise_codes=inputs,conclusion_code=result,input_offsets=list(ds),dependencies=d['dependencies'],authority=d.get('authority'),t=[[0,0,1]],m=[[x,y,grouped[(x,y)]] for x,y in sorted(grouped)])
            ident='prototype-'+sha(body);tiles.append(dict(**body,id=ident));bindings[(d['name'],ds)]=ident
    all_aligned=[]
    # Independent boundary-first alignment order, then canonical prototype order.
    bytile={d['id']:d for d in tiles};aligned={}
    for row in range(rows):
        for tile in tiles:
            k=tile['id']+'@'+str(row);aligned[k]=dict(id=k,prototype=tile['id'],interface=tile['interface'],family=tile['family'],kind=tile['kind'],row=row,inputs=[row+a for a in tile['input_offsets']],premise_codes=tile['premise_codes'],conclusion_code=tile['conclusion_code'],t=[[0,row,1]],m=[[x,y+row,z] for x,y,z in tile['m']])
    for tile in tiles:
        all_aligned.extend(aligned[tile['id']+'@'+str(row)] for row in range(rows))
    syntax=[]
    for row in range(rows):
        for d in descriptors:
            for refs in itertools.product(range(row),repeat=len(d['premises'])):
                ident=bindings[(d['name'],tuple(j-row for j in refs))]
                syntax.append(dict(row=row,interface=d['name'],inputs=list(refs),placement=ident+'@'+str(row) if ident else None,reason='inconsistent_local_mark_function' if ident is None else None))
    fixed=[[1,j,-1] for j in range(-(rows-1),0)]
    if target is not None:fixed.append([1,rows-1,lookup[enc(target)]])
    return dict(version='finite-symbolic-row-point-catalog-1',orientations=['identity'],translations_only=True,formula_codes=alphabet,rows=rows,required=[[0,i] for i in range(rows)],root_generations=[[0,i,0] for i in range(rows)],fixed_m=fixed,prototypes=tiles,rejected_prototypes=invalid,placements=all_aligned,ordered_bindings=syntax,descriptors=descriptors,scope='Declared finite symbolic row grammar; neither full first-order grammar nor aggregate cluster expansion.')

def rebuild(request,plan):
    theory,records,aliases=A.reconstruct(request);authority=auth(plan);interfaces=[]
    for j,r in enumerate(records):
        d=r['definition'];interfaces.append(dict(name=d['name'],family=r['family'],premises=d['premises'],conclusion=d['conclusion'],dependencies=r['dependencies'],definition_sha256=sha(d),source_record_index=j,authority=authority))
    seed=[dict(name='local-common-lm',kind='assumption',family='seed',premises=[],conclusion=hypothesis('l','m'),dependencies=[],authority=None),dict(name='local-common-mn',kind='assumption',family='seed',premises=[],conclusion=hypothesis('m','n'),dependencies=[],authority=None),dict(name='local-incidence',kind='assumption',family='seed',premises=[],conclusion=incidence('R','l'),dependencies=[],authority=None),dict(name='I.2-uniqueness',kind='axiom',family='seed',premises=[],conclusion=theory['axioms']['I.2-uniqueness'],dependencies=[],authority=None)]
    descriptors=seed+[dict(name=r['name'],kind='block',family=r['family'],premises=r['premises'],conclusion=r['conclusion'],dependencies=r['dependencies'],authority=authority) for r in interfaces]
    model=lower(descriptors,plan['rows'],incidence('R','n'));model['interfaces']=interfaces;model['authority']=authority;return model

def point_view(model,chosen):
    pool={p['id']:p for p in model['placements']};amount={tuple(p):0 for p in model['required']};values={tuple(v[:2]):v[2] for v in model['fixed_m']}
    for key in chosen:
        if key is None or key not in pool:return None
        p=pool[key]
        for x,y,v in p['t']:amount[(x,y)]+=v
        for x,y,v in p['m']:
            if (x,y) in values and values[(x,y)]!=v:return None
            values[(x,y)]=v
    if any(v>1 for v in amount.values()):return None
    holes=sorted(q for q in amount if amount[q]<1);domains={str(q):[] for q in holes}
    for p in model['placements']:
        if p['id'] in chosen:continue
        if any(amount.get((x,y),0)+v>1 for x,y,v in p['t']):continue
        if any((x,y) in values and values[(x,y)]!=v for x,y,v in p['m']):continue
        for x,y,v in p['t']:
            if v>0 and (x,y) in holes:domains[str((x,y))].append(p['id'])
    for d in domains.values():d.sort()
    action='exact';point=None
    if holes:
        action='branch'
        if any(len(d)==0 for d in domains.values()):action='dead'
        elif any(len(d)==1 for d in domains.values()):action='forced'
        if action in ['branch','forced']:
            possible=[q for q in holes if action!='forced' or len(domains[str(q)])==1];point=min(possible,key=lambda q:(0,len(domains[str(q)]),q))
    return dict(frontier=[list(q) for q in holes],edges=domains,nodes=sorted(set(x for d in domains.values() for x in d)),action=action,selected_point=list(point) if point else None,root_generations=[[q[0],q[1],0] for q in sorted(amount)])

def tiny_rebuild():
    zero=('atom',0);one=('atom',1)
    raw=[('zero',[],zero,'assumption'),('one',[],one,'assumption'),('same0',[zero],zero,'block'),('same1',[one],one,'block'),('duplicate',[zero,zero],one,'block'),('ordered',[zero,one],zero,'block')]
    ds=[dict(name=name,kind=kind,family='seed' if kind=='assumption' else 'tiny',premises=ps,conclusion=out,dependencies=[],authority=None) for name,ps,out,kind in raw]
    return lower(ds,3)
def full_symbolic(model,choices):
    if any(c is None for c in choices):return False
    ds={d['name']:d for d in model['descriptors']};history=[]
    for row,b in enumerate(choices):
        d=ds[b['interface']]
        if [history[j] for j in b['inputs']]!=list(d['premises']):return False
        history.append(d['conclusion'])
    return True

def main():
    os_limits=setup();began=time.perf_counter();plan=read(HERE/'plan-v1.json');stage=time.perf_counter();entries=0
    for rel,p in {**plan['source_pins'],**plan['inputs']}.items():eq(pin(ROOT/rel),p,'audit exact source/input')
    for rel,p in plan['preserved_manifests'].items():
        eq(pin(ROOT/rel),p,'old manifest pin')
        for r in read(ROOT/rel)['files']:eq(pin(ROOT/r['path']),{k:r[k] for k in ['sha256','bytes']},'every earlier raw file');entries+=1
    source=read(ROOT/plan['source_record'])[0];receipt=read(ROOT/plan['source_receipt']);request=source['request'];cert=read(ROOT/plan['certificate']);eq(sha(request),plan['source_request_sha256'],'donor request identity')
    A.require(source['result']['status']==receipt['native_outcome']=='accepted' and receipt['status']=='passed' and source['result']['micro_steps']==receipt['native_micro_steps'],'exact donor accepted and replayed')
    binding=dict(request_sha256=source['request_sha256'],input_sha256=source['input_sha256'],output_sha256=source['output_sha256'],native_record_file_sha256=plan['inputs'][plan['source_record']]['sha256'],native_receipt_file_sha256=plan['inputs'][plan['source_receipt']]['sha256'],native_micro_steps=source['result']['micro_steps']);A.verify(cert,request,binding)
    for rel,p in read(ROOT/plan['ledger'])['sources'].items():eq(pin(ROOT/rel),p,'argument source branch')
    A.require(read(ROOT/plan['argument_review'])['status']=='passed_independent_read_only_source_level_argument_review','argument review')
    binding_seconds=time.perf_counter()-stage;stage=time.perf_counter();expected=rebuild(request,plan);actual=read(HERE/'catalog-v1.json.gz');eq(actual,expected,'every interface prototype raw alignment and syntactic binding independently reconstructed');construction=time.perf_counter()-stage;gate()
    counts=dict(definitions=len(expected['interfaces']),formula_codes=len(expected['formula_codes']),prototypes=len(expected['prototypes']),rejected_prototypes=len(expected['rejected_prototypes']),raw_alignments=len(expected['placements']),strict_prior_bindings=len(expected['ordered_bindings']),inconsistent_strict_prior=sum(b['placement'] is None for b in expected['ordered_bindings']),consistent_strict_prior=sum(b['placement'] is not None for b in expected['ordered_bindings']),initial_point_candidates=len(point_view(expected,[])['nodes']));eq(counts,plan['predicted_counts'],'analytic declarations independently measured')
    stage=time.perf_counter();report=read(HERE/'graph-probes-v1.json');initial=point_view(expected,[]);eq(report['initial_view'],initial,'complete initial graph');probes=[]
    for k in initial['nodes']:
        v=point_view(expected,[k]);probes.append(dict(placement=k,view_sha256=sha(v),action=v['action'],nodes=len(v['nodes'])));gate()
    eq(probes,report['probes'],'all actual1492 graph/proof-domain probes');graph_seconds=time.perf_counter()-stage
    stage=time.perf_counter();tiny=tiny_rebuild();eq(tiny,read(HERE/'tiny-model-v1.json'),'independent full tiny lowering');choices=[[None]+[b for b in tiny['ordered_bindings'] if b['row']==i] for i in range(3)];records=[];valid=full=orders=0
    for selected in itertools.product(*choices):
        ids=[b['placement'] for b in selected if b is not None];v=point_view(tiny,ids)
        if v is not None:valid+=1;full+=int(len(ids)==3);orders+=1 if len(ids)<2 else 2 if len(ids)==2 else 6
        if all(b is not None for b in selected):A.require((v is not None)==full_symbolic(tiny,selected),'every full tiny point assignment iff exact ordered symbolic derivation')
        records.append(dict(choices=[b['placement'] if b else '-' for b in selected],legal=v is not None,view_sha256=sha(v) if v else None))
    tiny_report=read(HERE/'tiny-checks-v1.json');eq(records,tiny_report['records'],'all315 actual partial records');eq([valid,full,orders],[tiny_report['legal_partial_selections'],tiny_report['exact_full_selections'],tiny_report['permutation_rollback_checks']],'tiny full census')
    # Zero is an assigned value, not absence; opposite seed at that reference
    # point is a literal incompatibility, while removing it restores freedom.
    alphabet=tiny['formula_codes'];eq(alphabet[0],['atom',0],'zero code exact')
    pairs=0
    for row in range(3):
        ids=[p['id'] for p in tiny['placements'] if p['row']==row and point_view(tiny,[p['id']]) is not None]
        for a,b in itertools.combinations(ids,2):A.require(point_view(tiny,[a,b]) is None,'all same-row t-overlap pairs');pairs+=1
    eq(pairs,tiny_report['same_row_capacity_rejections'],'pair census');tiny_seconds=time.perf_counter()-stage
    stage=time.perf_counter();reports=read(HERE/'corruptions-v1.json');rejections=[]
    for case in plan['corruptions']:
        mutant=copy.deepcopy(actual if case['target']=='model' else cert);part=mutant
        for field in case['path'][:-1]:part=part[field]
        k=case['path'][-1]
        if case['operation']=='delete':part.pop(k)
        elif case['operation']=='append':part[k].append(copy.deepcopy(part[k][case['copy_index']]))
        else:part[k]=copy.deepcopy(case['value'])
        try:
            if case['target']=='certificate':A.verify(mutant,request,binding)
            else:eq(mutant,expected,'exact independent compiled model')
        except (A.Bad,KeyError,IndexError,TypeError):rejections.append(dict(name=case['name'],mutant_sha256=sha(mutant),status='rejected'))
        else:raise A.Bad('corruption passed '+case['name'])
    eq(rejections,[{k:r[k] for k in ['name','mutant_sha256','status']} for r in reports],'all actual corruptions independently reproduced');corruption_seconds=time.perf_counter()-stage
    result=dict(status='passed_independent_finite_catalog_audit',plan_sha256=hashfile(HERE/'plan-v1.json'),catalog_sha256=hashfile(HERE/'catalog-v1.json.gz'),counts=counts,all_single_placement_graph_probes=len(probes),tiny={k:v for k,v in tiny_report.items() if k!='records'},rejected_corruptions=len(rejections),preserved_file_entries=entries,binding_seconds=binding_seconds,construction_seconds=construction,graph_probe_seconds=graph_seconds,tiny_seconds=tiny_seconds,corruption_seconds=corruption_seconds,audit_seconds_before_final_write=time.perf_counter()-began,peak_rss_bytes=peak(),os_limits=os_limits,native_queries=0,target_searches=0,existing_native_engine_activation=False,formal_native_compiler_correspondence='open',aggregate_cluster_t_expansion_correspondence='open',authority='certified_transport_exact_finite_symbolic_relation')
    (HERE/'audit-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);signal.alarm(0)
if __name__=='__main__':main()
