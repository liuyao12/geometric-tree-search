"""Browser projection of the audited fragment experiment; no search or mining."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    source=DOCS/'proof-clusters-001.json';d=json.loads(source.read_text())
    if d['independent_audit']['status']!='passed':raise ValueError('audit required')
    for name,pin in d['sources'].items():
        if sha(HERE/name)!=pin:raise ValueError('producer source changed: '+name)
    out={k:d[k] for k in ('configuration','scope','comparison','compile_seconds','total_seconds','peak_driver_memory_bytes','program_sha256')}
    out.update(parent=dict(file=source.name,sha256=sha(source)),exporter_sha256=sha(Path(__file__)),library=[],donors=[],cases=[],totals={},
        independent_audit={k:v for k,v in d['independent_audit'].items() if k not in ('donors','evaluation')})
    for t in d['library']:
        v={k:t[k] for k in ('name','level','before','after','actions','children','source','check')};v['conclusion']=t['definition']['conclusion'];v['child_spans']=[]
        donor=next(r for r in d['donors'] if r['problem']['id']==t['source']['problem'])
        for tx in donor['result']['solution_transactions']:
            if all(key in t['source']['members'] for key in tx['members']):
                v['child_spans'].append(dict(template=tx['template'],indices=[t['source']['members'].index(key) for key in tx['members']],instance=tx['instance']))
        if [c['template'] for c in v['child_spans']]!=t['children']:raise ValueError('source child spans changed')
        out['library'].append(v)
    for donor in d['donors']:
        out['donors'].append(dict(problem=donor['problem'],cold_seconds=donor['cold_seconds'],input_library=donor['input_library'],nodes=donor['result']['nodes'],native_status=donor.get('native',{}).get('status'),promoted=[t['name'] for t in donor.get('promotion',{}).get('templates',[])]))
    out['learning_seconds']=sum(r['cold_seconds'] for r in d['donors'])+d['whole_library_native']['result']['wall_seconds']
    for row in d['evaluation']:
        cat=row['catalog'];v=dict(problem=row['problem'],catalog_sha256=row['catalog_sha256'],catalog={k:cat[k] for k in ('formulas','target_id')},rules=[],runs=[])
        for rule in cat['rules']:
            recipe=rule['recipe'];v['rules'].append(dict(inputs=rule['inputs'],output=rule['output'],label=recipe['witness']['rule'] if recipe['kind']=='primitive' else recipe.get('axiom',recipe['kind'])))
        for run in row['runs']:
            r=run['result'];result={k:r[k] for k in ('status','placements','nodes','base_attempts','stats','seconds','build_seconds','graph_seconds','index_seconds','index_instances','index_complete','candidate_universe','peak_candidate_nodes','solution_transactions','transaction_samples')}
            z={k:run[k] for k in ('lane','replica','cold_seconds','catalog_build_seconds','catalog_validation_seconds')};z['result']=result
            if 'native' in run:z['native']={k:run['native'][k] for k in ('status','steps','wall_seconds','peak_native_memory_bytes')}
            if 'hierarchy' in run:
                h=run['hierarchy'];z['hierarchy']={k:h[k] for k in ('root_lines','original_root_lines','definitions','seconds','transactions_used')};z['hierarchy']['proof']=h['request']['proof']
                a=next(a for a in d['independent_audit']['evaluation'] if a['id']==row['problem']['id']);b=next(b for b in a['runs'] if b['lane']==run['lane'] and b['replica']==run['replica']);z['hierarchy']['expanded_lines']=b['hierarchy']['expanded_lines']
            v['runs'].append(z)
        out['cases'].append(v)
    for lane in ('base','level1','hierarchy','rank-only'):
        runs=[r for row in out['cases'] for r in row['runs'] if r['lane']==lane]
        out['totals'][lane]=dict(requests=len(runs),found=sum(r['result']['status']=='finite_exact_proof_tiling' for r in runs),exhausted=sum(r['result']['status']=='exhausted_finite_proof_envelope' for r in runs),unknown=sum(r['result']['status']=='unknown_search_budget' for r in runs),nodes=sum(r['result']['nodes'] for r in runs),attempts=sum(r['result']['base_attempts'] for r in runs),search_seconds=sum(r['result']['seconds'] for r in runs),cold_seconds=sum(r['cold_seconds'] for r in runs),native_seconds=sum(r.get('native',{}).get('wall_seconds',0) for r in runs),index_seconds=sum(r['result']['index_seconds'] for r in runs))
    target=DOCS/'proof-cluster-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print(target.name,target.stat().st_size)
if __name__=='__main__':main()
