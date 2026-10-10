"""Read-only audited projection; independent identities describe actual selected tiles."""
import hashlib,json
from pathlib import Path
import audit_coarse_proofs as V
from audit_serialized_kernel import freeze
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=DOCS/'coarse-proofs-001.json';d=json.loads(path.read_text())
    if d['independent_audit']['status']!='passed':raise ValueError('passed independent audit required')
    for name,pin in d['sources'].items():
        if sha(HERE/name)!=pin:raise ValueError('measured source changed '+name)
    out={k:d[k] for k in ('configuration','scope','comparison','compile_seconds','library_seconds','total_seconds','peak_driver_memory_bytes','program_sha256')};out.update(parent=dict(file=path.name,sha256=sha(path)),exporter_sha256=sha(Path(__file__)),library=d['library'],cases=[],totals={})
    out['independent_audit']={k:d['independent_audit'][k] for k in ('status','seconds','source_sha256','scope')}
    for row in d['evaluation']:
        c=row['catalog'];record=dict(problem=row['problem'],formulas=c['formulas'],target_id=c['target_id'],rules=[dict(output=r['output'],inputs=r['inputs'],label=r['recipe']['witness']['rule'] if r['recipe']['kind']=='primitive' else r['recipe'].get('axiom',r['recipe']['kind'])) for r in c['rules']],runs=[])
        for run in row['runs']:
            r=run['result'];slim={k:run[k] for k in ('lane','replica','catalog_build_seconds','catalog_validation_seconds','cold_seconds')};slim['result']={k:v for k,v in r.items() if k not in ('search_tree','partial_tree','decoded','solution_transactions')};nodes=[]
            points=V.Points(freeze(c),row['problem']['length'],r['width'],freeze(d['library']) if run['library'] else ()) if run['lane']!='csp' else None
            def visit(t,parent=None):
                i=len(nodes);selected=t.get('selected',[]);entry=dict(id=i,parent=parent,kind=t['kind'],cutoff=t.get('cutoff'),depth=len(points.expand(selected)) if points else 0)
                if not points:entry.update(domains_before=[bin(int(x,16)).count('1') for x in t['incoming']],domains_after=[bin(int(x,16)).count('1') for x in t['domains']])
                nodes.append(entry)
                for child in t.get('children',[]):visit(child['tree'],i)
            visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree']);slim['prefix_nodes']=nodes
            if points:
                slim['selected_tiles']=[]
                for cid in r['selected']:
                    t=points.tiles[cid];slim['selected_tiles'].append(dict(candidate=cid,members=t['members'],item=t['item'],weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items())))
            if 'native' in run:slim['native']={k:run['native'][k] for k in ('status','steps','wall_seconds')}
            if 'hierarchy' in run:
                h=run['hierarchy'];slim['hierarchy']={k:h[k] for k in ('root_lines','original_root_lines','definitions','seconds','transactions_used')};slim['hierarchy']['proof']=h['request']['proof']
            record['runs'].append(slim)
        out['cases'].append(record)
    for replica in range(2):
        totals={}
        for lane in d['configuration']['lanes']:
            runs=[r for row in d['evaluation'] for r in row['runs'] if r['replica']==replica and r['lane']==lane]
            sums={key:sum(r['result'].get(key,0) for r in runs) for key in ('nodes','base_attempts','tile_attempts','branches','forced','backtracks','support_tests','removed_values','seconds','build_seconds','graph_seconds','index_seconds')}
            totals[lane]=dict(verified=sum(r.get('native',{}).get('status')=='accepted' for r in runs),exhausted=sum(r['result']['status']=='exhausted_finite_proof_envelope' for r in runs),unknown=sum(r['result']['status']=='unknown_search_budget' for r in runs),cold_seconds=sum(r['cold_seconds'] for r in runs),lifecycle_seconds=sum(r['cold_seconds'] for r in runs)+d['compile_seconds']+(d['library_seconds'] if lane in ('fine-meta','coarse2-meta','coarse3-meta') else 0),**sums)
        out['totals'][str(replica)]=totals
    target=DOCS/'coarse-proofs-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print(target.name,target.stat().st_size)
if __name__=='__main__':main()
