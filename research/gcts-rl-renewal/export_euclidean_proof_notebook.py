"""Read-only projection of audited geometry proofs and exact point values."""
import hashlib,json
from pathlib import Path
from audit_serialized_kernel import freeze
from audit_induction_proofs import Points
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    source=DOCS/'euclidean-proofs-001.json';raw=source.read_bytes();data=json.loads(raw)
    if data.get('independent_audit',{}).get('status')!='passed':raise ValueError('independent search audit required')
    proofs=[]
    for name in ('I.5','I.6','triangle-order'):
        row=next((r for r in data['runs'] if r['id']==name and r['lane']=='gcts' and 'decoded' in r['result']),None)
        if row is None:row=next(r for r in data['runs'] if r['id']==name and 'decoded' in r['result'])
        c=freeze(row['catalog']);r=freeze(row['result']);points=Points(c,row['length'],'support');tiles=[]
        selected=r['selected'] if row['lane']=='gcts' else [i for i,t in enumerate(points.tiles) if t['members'][0] in r['placements']]
        for cid in selected:
            t=points.tiles[cid];slot,rid,refs=t['members'][0];rule=c['rules'][rid]
            tiles.append(dict(candidate=cid,slot=slot,refs=refs,formula_id=rule['output'],formula=c['formulas'][rule['output']],input_ids=rule['inputs'],recipe={k:v for k,v in rule['recipe'].items() if k!='definition'},weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items()),root_line=r['decoded']['commands'][slot]['final_line']))
        tiles.sort(key=lambda t:t['slot'])
        proofs.append(dict(id=name,lane=row['lane'],target=c['target'],hypothesis=row['problem']['hypothesis'],goal=row['problem']['goal'],length=row['length'],tiles=tiles,formulas=c['formulas'],theory=c['theory'],request=r['decoded']['request'],primitive=row['primitive_proof'],primitive_lines=row['primitive_lines'],native=row['native'],metrics={k:r[k] for k in ('nodes','base_attempts','seconds','build_seconds','graph_seconds','candidate_universe') if k in r}))
    view=dict(version='euclidean-reader-001',source=dict(file='euclidean-proofs-001.json',sha256=hashlib.sha256(raw).hexdigest()),audit=data['independent_audit'],proofs=proofs,results=[dict(id=r['id'],lane=r['lane'],length=r['length'],status=r['result']['status'],states=r['result']['nodes'],attempts=r['result']['base_attempts'],seconds=r['result']['seconds']) for r in data['runs']],scope=data['scope'])
    (DOCS/'euclidean-reader-001.json').write_text(json.dumps(view,separators=(',',':'))+'\n');print('exported',len(proofs),'proofs',sum(p['length'] for p in proofs),'cells')
if __name__=='__main__':main()
