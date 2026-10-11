"""Frozen native admission, automatic point search, and explicit unknowns."""
import copy,gzip,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from induction_receptors_catalog import catalog,freeze,thaw,Proof,deduce
from induction_receptors_points import Model
from native_receptor_points import search
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/induction-receptors-20261011';TMP=Path('/private/tmp/gcts-induction-receptors-20261011')
def save(path,v):path.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def used(definitions,proof):
    names={r['name'] for r in proof if r['rule']=='block'}
    return [d for d in definitions if d['name'] in names]
def probes(theory):
    """Generic scope/guard tests, authored fixtures and explicitly not search."""
    import logic as L
    z=L.F('zero');n=L.V('n');H=L.Eq(z,z);p=L.Eq(n,n);out=Proof()
    i=out.emit('assumption',H,index=0);out.emit('generalize',L.All('n',H),variable='n',source=i)
    proof=deduce(out.lines,H);target=proof[-1]['formula']
    yield 'deduction-safe-generalize',dict(protocol='gcts-fol-1',theory=theory,blocks=[],proof=proof,target=target),'accepted'
    x='n';bad=dict(rule='distribute',formula=thaw(L.Imp(L.All(x,L.Imp(p,H)),L.Imp(p,L.All(x,H)))),variable=x,antecedent=thaw(p),consequent=thaw(H))
    yield 'distribution-free-antecedent-rejected',dict(protocol='gcts-fol-1',theory=theory,blocks=[],proof=[bad],target=bad['formula']),'rejected'
    badblock=dict(name='illegalEigenvariable',premises=[thaw(p)],conclusion=thaw(L.All('n',p)),proof=[dict(rule='assumption',formula=thaw(p),index=0),dict(rule='generalize',formula=thaw(L.All('n',p)),variable='n',source=0)])
    yield 'open-premise-generalization-rejected',dict(protocol='gcts-fol-1',theory=theory,blocks=[badblock],proof=[dict(rule='refl',formula=thaw(H))],target=thaw(H)),'rejected'
    from induction_receptors_catalog import induction_schema
    bare=copy.deepcopy(theory);bare['schemas']=[];command=dict(rule='induction',formula=thaw(induction_schema('n',p)),variable='n',template=thaw(p))
    yield 'induction-without-authorization-rejected',dict(protocol='gcts-fol-1',theory=bare,blocks=[],proof=[command],target=command['formula']),'rejected'
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());TMP.mkdir(parents=True,exist_ok=True)
    for path,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:raise ValueError('frozen source changed '+path)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));original=oracle.request
    def request(r,purpose):
        q=original(r,plan['native_steps'],purpose);fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free);q['limit']=plan['native_steps']
        save(OUT/'native-records.json.gz',oracle.records);print('native',q['id'],purpose,q['result']['status'],round(q['seconds'],3),flush=True);return q
    oracle.request=request;summary=dict(status='running',observations=[],probes=[])
    try:
        spec=plan['case'];c=catalog(spec);save(OUT/'catalog.json.gz',c);stage=time.perf_counter();admission=dict(status='checking',definitions=[],primitive=[],native_queries=[])
        taut=['imp',['bot'],['bot']]
        for d in c['definitions']:
            q=request(dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut),'induction_receptor_definition')
            admission['definitions'].append(dict(name=d['name'],query=q['id'],status=q['result']['status']));admission['native_queries'].append(q['id'])
            if q['result']['status']!='accepted':
                admission['status']='unknown_or_rejected_native_inventory';save(OUT/'admission.json.gz',admission);summary['status']=admission['status'];return
        # Primitive reflexivity is structural; each root generalization guard
        # requires a preceding formula exactly and the ambient theory is closed.
        # Exposed primitive schema compilation is deliberately budgeted and
        # remains unknown until every declared scheme has been natively resolved.
        for command in c['primitive_schemes'][:plan['primitive_query_budget']]:
            q=request(dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[command],target=command['formula']),'induction_receptor_primitive_scheme')
            admission['primitive'].append(dict(command=command,query=q['id'],status=q['result']['status']));admission['native_queries'].append(q['id'])
            if q['result']['status']!='accepted':raise ValueError('primitive scheme not accepted')
        admission.update(status='native_accepted',primitive_status='complete' if len(admission['primitive'])==len(c['primitive_schemes']) else 'unknown_compile_budget',primitive_catalog_count=len(c['primitive_schemes']),seconds=time.perf_counter()-stage)
        save(OUT/'admission.json.gz',admission)
        for label,r,expect in probes(spec['theory']):
            q=request(r,'induction_receptor_probe_'+label)
            if q['result']['status']!=expect:raise ValueError('native probe mismatch '+label)
            summary['probes'].append(dict(label=label,query=q['id'],expected=expect))
        for observation in plan['observations']:
            s=copy.deepcopy(spec);s['length']=observation['length'];s['id']=observation['id'];model=Model(s,c,admission)
            stage=time.perf_counter();r=search(model,**plan['search_limits']);r['command_skeleton']=r['proof']
            if r['proof'] is not None:r['proof']=model.decode(r['placements'])
            q=None
            if r['proof'] is not None:
                q=request(dict(protocol='gcts-fol-1',theory=s['theory'],blocks=used(c['definitions'],r['proof']),proof=r['proof'],target=s['target']),'induction_receptor_discovered_whole')
                if q['result']['status']!='accepted':raise ValueError('whole discovered certificate not native accepted')
            raw=dict(case=s,search=r,model=model.record(),native_query=q['id'] if q else None,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            save(OUT/(s['id']+'.json.gz'),raw)
            summary['observations'].append(dict(id=s['id'],length=s['length'],status=r['status'],native_query=raw['native_query'],attempts=r['metrics'].get('attempts',0),search_seconds=r['seconds'],whole_seconds=time.perf_counter()-stage,model_setup_seconds=model.compile_seconds,placements=len(model.cache),peak_rss_bytes=raw['peak_rss_bytes']))
            print('SEARCH',summary['observations'][-1],flush=True);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        summary.update(status='complete',native_queries=len(oracle.records),total_seconds=time.perf_counter()-began,admission_seconds=admission['seconds'],catalog_seconds=c['build_seconds'],primitive_status=admission['primitive_status'])
    finally:
        (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');oracle.close()

if __name__=='__main__':main()
