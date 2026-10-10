"""Read-only projection of audited induction traces and actual proof tiles.

Does not import the grammar generator, point engine, search or producer.
Reconstructs saved placements and marking values with the independent auditor.
"""
import hashlib,json
from pathlib import Path
import audit_induction_proofs as I
import audit_semantic_proofs as A
from audit_serialized_kernel import freeze,replay
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(b):return hashlib.sha256(b).hexdigest()
def tile(c,points,cid,command=None,step=None):
    t=points.tiles[cid];slot,rid,refs=t['members'][0];rule=c['rules'][rid]
    recipe=rule['recipe'];reason={k:v for k,v in recipe.items() if k!='definition'}
    return dict(candidate=cid,slot=slot,rule_id=rid,refs=refs,formula_id=rule['output'],input_ids=rule['inputs'],reason=reason,search_step=step,
      weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items()),root_line=command['final_line'] if command else None)
def main():
    path=DOCS/'induction-proofs-001.json';d=json.loads(path.read_text())
    if d.get('independent_audit',{}).get('status')!='passed':raise ValueError('full independent search audit required')
    for n,pin in d['sources'].items():
        if sha((HERE/n).read_bytes())!=pin:raise ValueError('measured source changed '+n)
    out=dict(parent=dict(file=path.name,sha256=sha(path.read_bytes())),exporter_sha256=sha(Path(__file__).read_bytes()),
      dependencies={n:sha((HERE/n).read_bytes()) for n in ('audit_induction_proofs.py','audit_semantic_proofs.py','audit_serialized_kernel.py','logic.py')},
      scope=d['scope'],comparison=d['comparison'],cases=[],proofs=[])
    audit={x['id']:x for x in d['independent_audit']['cases']}
    folder=DOCS/'induction-proof-certificates-001';folder.mkdir(exist_ok=True)
    for descriptor in d['cases']:
        row=I.load_case(descriptor);p=row['problem'];c=freeze(row['catalog']);reports={x['lane']:x['report'] for x in audit[p['id']]['runs']}
        out['cases'].append(dict(problem=p,inventory=audit[p['id']]['inventory'],source=descriptor,
          runs=[dict(lane=r['lane'],cold_seconds=r['cold_seconds'],catalog_build_seconds=r['catalog_build_seconds'],catalog_validation_seconds=r['catalog_validation_seconds'],
             metrics={k:v for k,v in r['result'].items() if k in ('status','seconds','nodes','branches','forced','backtracks','base_attempts','tile_attempts','candidate_universe','base_universe','build_seconds','graph_seconds','decode_seconds','marking_seconds','support_tests','removed_values','revisions','peak_candidate_nodes','peak_incidences')},
             audit=reports[r['lane']],native={k:r['native'][k] for k in ('status','steps','wall_seconds')} if 'native' in r else None) for r in row['runs']]))
        accepted=[r for lane in ('support-marked','gcts','depth-marked','csp') for r in row['runs'] if r['lane']==lane and r.get('native',{}).get('status')=='accepted']
        if not accepted:continue
        run=accepted[0];r=run['result'];request=r['decoded']['request'];pin=A.pin(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
        expanded=replay(A.packed(request),pin)
        if expanded['status']!='accepted' or any(x['rule'] in ('block','assumption') for x in expanded['proof']):raise ValueError('complete independent primitive proof required')
        points=I.Points(c,p['length'],r.get('marking','none'));lookup={t['members'][0]:i for i,t in enumerate(points.tiles)}
        commands={x['slot']:x for x in r['decoded']['commands']};order=r.get('selected',[lookup[freeze(k)] for k in r['placements']])
        tiles=[tile(c,points,cid,commands[points.tiles[cid]['members'][0][0]],j+1 if run['lane']!='csp' else None) for j,cid in enumerate(order)]
        if run['lane']=='csp':
            # The classical control operates on original formula ports, with
            # no owner/resource channel and no chronological tile placement.
            for t in tiles:
                t['candidate']=(t['slot'],t['rule_id'],t['refs'])
                t['marks']=[(p,v) for p,v in t['marks'] if p[1]==1]
        if sorted(t['slot'] for t in tiles)!=list(range(p['length'])):raise ValueError('actual exact proof strip')
        marked=I.Points(c,p['length'],'support');plain=I.Points(c,p['length'])
        eliminated=set().union(*plain.domains([]).values())-set().union(*marked.domains([]).values())
        preferred=[cid for cid in sorted(eliminated) if c['rules'][marked.tiles[cid]['members'][0][1]]['recipe'].get('operation')=='induction' and marked.tiles[cid]['marks'][(2*marked.tiles[cid]['members'][0][0],4)]==0]
        example=tile(c,marked,(preferred or sorted(eliminated))[0]) if eliminated else None
        filename='induction-proof-certificates-001/'+p['id']+'.json';payload=A.packed(request);(DOCS/filename).write_bytes(payload)
        out['proofs'].append(dict(problem=p,lane=run['lane'],source=descriptor,catalog_sha256=row['catalog_sha256'],formulas=c['formulas'],target_id=c['target_id'],
          request=request,problem_sha256=pin,certificate_sha256=sha(payload),certificate_file=filename,expanded_proof=expanded['proof'],expanded_lines=expanded['expanded_lines'],
          tiles=tiles,marking=r.get('marking','none'),bound=I.support_bounds(c)[0],eliminated_example=example,
          native={k:run['native'][k] for k in ('status','steps','wall_seconds')}))
    target=DOCS/'induction-proofs-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('projection',len(out['cases']),'cases',len(out['proofs']),'proofs',target.stat().st_size,'bytes',flush=True)
if __name__=='__main__':main()
