"""Read-only audited proof/motif projection; no catalog, search or miner imports."""
import collections,hashlib,json
from pathlib import Path
import audit_induction_clusters as H,audit_induction_proofs as I,audit_semantic_proofs as A
from audit_serialized_kernel import freeze,replay
from export_induction_proofs import tile
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(b):return hashlib.sha256(b).hexdigest()
def metrics(run):
    return dict(lane=run.get('lane','source-gcts'),replica=run.get('replica',0),cold_seconds=run['cold_seconds'],catalog_build_seconds=run['catalog_build_seconds'],catalog_validation_seconds=run['catalog_validation_seconds'],native={k:run['native'][k] for k in ('status','steps','wall_seconds')} if 'native' in run else None,
      metrics={k:v for k,v in run['result'].items() if k in ('status','seconds','nodes','branches','forced','backtracks','base_attempts','tile_attempts','macro_attempts','motif_instances','candidate_universe','base_universe','build_seconds','graph_seconds','decode_seconds','support_tests','removed_values','revisions','peak_candidate_nodes','peak_incidences','ranking_seconds','policy_work')})
def record(row,run,descriptor,library):
    p=row['problem'];c=freeze(row['catalog']);r=freeze(run['result']);lane=run.get('lane','source-gcts');request=r['decoded']['request'];pin=A.pin(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    expanded=replay(A.packed(request),pin)
    A.need(expanded['status']=='accepted' and all(x['rule'] not in ('block','assumption') for x in expanded['proof']),'full primitive expansion')
    base=I.Points(c,p['length'],'support');lookup={t['members'][0]:cid for cid,t in enumerate(base.tiles)};commands={x['slot']:x for x in r['decoded']['commands']}
    cells=[];atomic=[];proposals=[]
    if lane.startswith('csp'):
        for key in r['placements']:
            t=tile(c,base,lookup[key],commands[key[0]])
            t.update(parent_candidate=None);t['candidate']=key;t['marks']=[(p,v) for p,v in t['marks'] if p[1]!=2];cells.append(t)
        available=H.instances(c,p['length'],freeze(library))
        witness=set(r['placements'])
        for mid in r['used_motif_proposals']:
            proposal=available[mid];A.need(all(k in witness for k in proposal['members']),'classical proposal belongs to the accepted assignment')
            proposals.append(dict(instance=mid,**proposal))
    else:
        points=H.Points(c,p['length'],freeze(library),True)
        for step,cid in enumerate(r['selected'],1):
            part=points.tiles[cid];weights=collections.Counter();marks={}
            for key in part['members']:
                t=tile(c,base,lookup[key],commands[key[0]],step);t.update(parent_candidate=cid)
                t['marks']=[(p,cid if p[1]==2 else v) for p,v in t['marks']]
                for point,v in t['weights']:weights[tuple(point)]+=v
                for point,v in t['marks']:
                    point=tuple(point);A.need(point not in marks or marks[point]==v,'compatible constituent marking');marks[point]=v
                cells.append(t)
            A.need(dict(weights)==part['weights'] and marks==part['marks'],'exact actual metatile expansion')
            atomic.append(dict(candidate=cid,search_step=step,members=part['members'],item=part['item'],weights=sorted(part['weights'].items()),marks=sorted(part['marks'].items())))
    filename='induction-cluster-policy-certificates-001/'+p['id']+'--'+lane+'.json';payload=A.packed(request);(DOCS/filename).write_bytes(payload)
    return dict(problem=p,lane=lane,replica=run.get('replica',0),source=descriptor,catalog_sha256=row['catalog_sha256'],formulas=c['formulas'],target_id=c['target_id'],request=request,problem_sha256=pin,certificate_sha256=sha(payload),certificate_file=filename,expanded_proof=expanded['proof'],expanded_lines=expanded['expanded_lines'],tiles=cells,atomic_tiles=atomic,classical_proposals=proposals,initial_marks=sorted(base.initial_marks.items()),native={k:run['native'][k] for k in ('status','steps','wall_seconds')},bound=I.support_bounds(c)[0],marking='support',policy_sha256=r.get('policy_sha256',H.sha(None)))
def main():
    path=DOCS/'induction-cluster-policy-001.json';d=json.loads(path.read_text());A.need(d.get('independent_audit',{}).get('status')=='passed','full independent experiment audit required')
    for n,pin in d['sources'].items():A.need(sha((HERE/n).read_bytes())==pin,'frozen measured source '+n)
    out=dict(parent=dict(file=path.name,sha256=sha(path.read_bytes())),exporter_sha256=sha(Path(__file__).read_bytes()),dependencies={n:sha((HERE/n).read_bytes()) for n in ('audit_induction_clusters.py','audit_induction_proofs.py','audit_semantic_proofs.py','audit_serialized_kernel.py','export_induction_proofs.py','logic.py')},scope=d['scope'],comparison=d['comparison'],library=d['library'],training_seconds=d['training_seconds'],discovery_seconds=d['discovery_seconds'],rl_learning_seconds=d['rl_learning_seconds'],policy=d['policy'],initial_policy=d['initial_policy'],episodes=[],cases=[],donors=[],proofs=[])
    (DOCS/'induction-cluster-policy-certificates-001').mkdir(exist_ok=True)
    for descriptor in d['donors']:
        row=I.load_case(descriptor);out['donors'].append(dict(problem=row['problem'],source=descriptor,run=metrics(row['run']),mining_seconds=row['mining_seconds']))
    for descriptor in d['episodes']:
        row=I.load_case(descriptor);run=row['run'];r=run['result']
        out['episodes'].append(dict(episode=row['episode'],problem_id=row['problem_id'],source=descriptor,status=r['status'],base_attempts=r['base_attempts'],covered_cells=len(r['placements']),proof_cells=r['proof_cells'],nodes=r['nodes'],policy_work=r['policy_work'],update=run['update'],before_weights=r['policy']['weights'],cold_seconds=run['cold_seconds'],native=run.get('native')))
    for descriptor in sorted(d['cases'],key=lambda x:(x['problem']['id']!='ind-add-left-successor',x['problem']['id'])):
        row=I.load_case(descriptor);out['cases'].append(dict(problem=row['problem'],source=descriptor,runs=[metrics(r) for r in row['runs']]))
        primary=True
        for lane in ('gcts-rl','gcts-fixed','csp-rl','csp-fixed'):
            accepted=[r for r in row['runs'] if r['lane']==lane and r.get('native',{}).get('status')=='accepted']
            if accepted:
                proof=record(row,accepted[0],descriptor,d['library']);proof['primary']=primary;primary=False;out['proofs'].append(proof)
    for descriptor in d['donors']:
        row=I.load_case(descriptor);proof=record(row,row['run'],descriptor,[]);proof['primary']=True;proof['source_donor']=True;out['proofs'].append(proof)
    donor_rows={desc['problem']['id']:I.load_case(desc) for desc in d['donors']}
    for descriptor in d['episodes']:
        episode=I.load_case(descriptor);run=episode['run']
        if run.get('native',{}).get('status')!='accepted':continue
        row=donor_rows[episode['problem_id']];actual=dict(run,lane=f"source-rl-{episode['episode']:02d}")
        proof=record(row,actual,descriptor,d['library']);proof.update(primary=False,source_donor=True,training_episode=episode['episode']);out['proofs'].append(proof)
    target=DOCS/'induction-cluster-policy-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print('projection',len(out['proofs']),'proof records',target.stat().st_size,'bytes',flush=True)
if __name__=='__main__':main()
