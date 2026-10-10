"""Small source-bound projection of the audited policy experiment; no learning."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def slim(run):
    out={k:run[k] for k in ('lane','seed','cold_seconds','catalog_build_seconds','catalog_validation_seconds') if k in run};r=run['result'];out['result']={k:r[k] for k in ('status','nodes','base_attempts','seconds','build_seconds','graph_seconds','index_seconds','index_instances','candidate_universe','placements','policy_events','policy_seconds','stats')};events={};fallbacks={}
    def tree(t):
        solved=t['kind']=='empty';trials=[]
        for x in t.get('proposals',[]):
            child=tree(x['tree']) if x['trace']['status']=='accepted_cluster' else None
            solved=solved or bool(child);trials.append(dict(item=x['item'],trace=x['trace'],continuation_solved=child))
        for x in t.get('children',[]):solved=tree(x['tree']) or solved
        if 'policy_event' in t:events[t['policy_event']]=trials;fallbacks[t['policy_event']]=bool(t['children'])
        return solved
    if r['search_tree'] is not None:tree(r['search_tree'])
    out['event_trials']={str(k):v for k,v in events.items()};out['event_fallbacks']={str(k):v for k,v in fallbacks.items()}
    if 'native' in run:out['native']={k:run['native'][k] for k in ('status','steps','wall_seconds')}
    if 'hierarchy' in run:
        h=run['hierarchy'];out['hierarchy']={k:h[k] for k in ('root_lines','original_root_lines','definitions','seconds')};out['hierarchy']['proof']=h['request']['proof']
    if 'update' in run:out['update']=run['update'];out['problem_id']=run['problem_id'];out['epoch']=run['epoch']
    return out

def main():
    p=DOCS/'proof-policy-001.json';d=json.loads(p.read_text())
    if d['independent_audit']['status']!='passed':raise ValueError('passed audit required')
    for n,pin in d['sources'].items():
        if sha(HERE/n)!=pin:raise ValueError('producer source changed: '+n)
    out={k:d[k] for k in ('features','configuration','scope','comparison','compile_seconds','library_seconds','training_catalog_seconds','total_seconds','peak_driver_memory_bytes','program_sha256')};out.update(parent=dict(file=p.name,sha256=sha(p)),exporter_sha256=sha(Path(__file__)),library=[{k:t[k] for k in ('name','level','before','after','children')} for t in d['library']],training=[dict(problem=r['problem'],build_seconds=r['build_seconds']) for r in d['training_catalogs']],seeds=[],cases=[],totals={})
    out['independent_audit']={k:v for k,v in d['independent_audit'].items() if k not in ('donors','training_inventories','seeds','evaluation')}
    for row in d['seeds']:out['seeds'].append(dict(seed=row['seed'],weights=row['weights'],training_seconds=row['training_seconds'],episodes=[slim(e) for e in row['episodes']]))
    for row in d['evaluation']:
        c=row['catalog'];out['cases'].append(dict(problem=row['problem'],formulas=c['formulas'],target_id=c['target_id'],rules=[dict(output=r['output'],inputs=r['inputs'],label=r['recipe']['witness']['rule'] if r['recipe']['kind']=='primitive' else r['recipe'].get('axiom',r['recipe']['kind'])) for r in c['rules']],runs=[slim(r) for r in row['runs']]))
    for seed in (1,7,19):
        out['totals'][str(seed)]={}
        for lane in ('base','level1','prior','zero','trained'):
            rs=[r for row in d['evaluation'] for r in row['runs'] if r['seed']==seed and r['lane']==lane]
            out['totals'][str(seed)][lane]=dict(verified=sum(r.get('native',{}).get('status')=='accepted' for r in rs),exhausted=sum(r['result']['status']=='exhausted_finite_proof_envelope' for r in rs),unknown=sum(r['result']['status']=='unknown_search_budget' for r in rs),cold_seconds=sum(r['cold_seconds'] for r in rs),search_seconds=sum(r['result']['seconds'] for r in rs),attempts=sum(r['result']['base_attempts'] for r in rs),nodes=sum(r['result']['nodes'] for r in rs),policy_seconds=sum(r['result']['policy_seconds'] for r in rs))
    target=DOCS/'proof-policy-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print(target.name,target.stat().st_size)
if __name__=='__main__':main()
