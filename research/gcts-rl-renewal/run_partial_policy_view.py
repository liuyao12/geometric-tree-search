"""Read-only, SHA-bound browser projection of the audited partial-credit run."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def slim(run):
    out={k:run[k] for k in ('lane','seed','cold_seconds','catalog_build_seconds','catalog_validation_seconds','problem_id','epoch','update','prefix_gate') if k in run};r=run['result'];out['result']={k:r[k] for k in ('status','nodes','base_attempts','seconds','index_instances','candidate_universe','placements','policy_events','policy_seconds','stats')};nodes=[];events={};fallbacks={}
    def visit(t,order,parent=None,via='root'):
        number=len(nodes);nodes.append(dict(id=number,parent=parent,via=via,kind=t['kind'],depth=t['depth'],viable=t['viable'],cutoff=t.get('cutoff'),event=t.get('policy_event'),order=order));trials=[];found=t['kind']=='empty';unknown=t['kind']=='cutoff' or bool(t.get('cutoff'))
        for x in t.get('proposals',[]):
            status=x['trace']['status'];continuation=None
            if status=='accepted_cluster':continuation=visit(x['tree'],order+[s['key'] for s in x['trace']['steps']],number,'checked sequence');found=found or continuation is True;unknown=unknown or continuation is None
            elif status=='unknown_transaction_budget':unknown=True;nodes[number]['cutoff']='transaction_budget'
            trials.append(dict(item=x['item'],trace=x['trace'],continuation=continuation))
        for x in t.get('children',[]):
            okay=visit(x['tree'],order+[x['key']],number,'base placement');found=found or okay is True;unknown=unknown or okay is None
        if 'policy_event' in t:events[str(t['policy_event'])]=trials;fallbacks[str(t['policy_event'])]=bool(t['children'])
        nodes[number]['outcome']='solved' if found else 'open' if unknown else 'exhausted'
        return True if found else None if unknown else False
    visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],[])
    out.update(prefix_nodes=nodes,event_trials=events,event_fallbacks=fallbacks)
    if 'native' in run:out['native']={k:run['native'][k] for k in ('status','steps','wall_seconds')}
    if 'hierarchy' in run:
        h=run['hierarchy'];out['hierarchy']={k:h[k] for k in ('root_lines','original_root_lines','definitions','seconds')};out['hierarchy']['proof']=h['request']['proof']
    return out
def main():
    path=DOCS/'partial-policy-001.json';d=json.loads(path.read_text())
    if d['independent_audit']['status']!='passed':raise ValueError('passed independent audit required')
    for n,h in d['sources'].items():
        if sha(HERE/n)!=h:raise ValueError('measured source changed: '+n)
    out={k:d[k] for k in ('features','configuration','scope','comparison','compile_seconds','library_seconds','training_catalog_seconds','total_seconds','peak_driver_memory_bytes','program_sha256')};out.update(parent=dict(file=path.name,sha256=sha(path)),exporter_sha256=sha(Path(__file__)),training=[],learners=[],cases=[],totals={})
    for row in d['training_catalogs']:
        c=row['catalog'];out['training'].append(dict(problem=row['problem'],build_seconds=row['build_seconds'],inventory_gate=row['inventory_gate'],formulas=c['formulas'],target_id=c['target_id'],rules=[dict(output=x['output'],inputs=x['inputs'],label=x['recipe']['witness']['rule'] if x['recipe']['kind']=='primitive' else x['recipe'].get('axiom',x['recipe']['kind'])) for x in c['rules']]))
    out['independent_audit']={k:v for k,v in d['independent_audit'].items() if k not in ('donors','training_inventories','learners','evaluation')}
    for row in d['learners']:out['learners'].append(dict(seed=row['seed'],signal=row['signal'],weights=row['weights'],training_seconds=row['training_seconds'],episodes=[slim(e) for e in row['episodes']]))
    for row in d['evaluation']:
        c=row['catalog'];out['cases'].append(dict(problem=row['problem'],formulas=c['formulas'],target_id=c['target_id'],rules=[dict(output=x['output'],inputs=x['inputs'],label=x['recipe']['witness']['rule'] if x['recipe']['kind']=='primitive' else x['recipe'].get('axiom',x['recipe']['kind'])) for x in c['rules']],runs=[slim(r) for r in row['runs']]))
    for seed in (1,7,19):
        out['totals'][str(seed)]={}
        for lane in ('base','prior','zero','complete','local'):
            runs=[r for row in d['evaluation'] for r in row['runs'] if r['seed']==seed and r['lane']==lane]
            out['totals'][str(seed)][lane]=dict(verified=sum(r.get('native',{}).get('status')=='accepted' for r in runs),exhausted=sum(r['result']['status']=='exhausted_finite_proof_envelope' for r in runs),unknown=sum(r['result']['status']=='unknown_search_budget' for r in runs),cold_seconds=sum(r['cold_seconds'] for r in runs),attempts=sum(r['result']['base_attempts'] for r in runs),nodes=sum(r['result']['nodes'] for r in runs),policy_seconds=sum(r['result']['policy_seconds'] for r in runs))
    target=DOCS/'partial-policy-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print(target.name,target.stat().st_size)
if __name__=='__main__':main()
