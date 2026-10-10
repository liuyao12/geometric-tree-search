"""Read-only projection of audited Hilbert searches and exact marked cells."""
import hashlib,json
from pathlib import Path
from audit_serialized_kernel import freeze
from audit_induction_proofs import Points
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    source=DOCS/'hilbert-incidence-001.json';raw=source.read_bytes();data=json.loads(raw)
    if data.get('independent_audit',{}).get('status')!='passed':raise ValueError('complete independent audit required')
    proofs=[]
    for name in ('intersection-unique','incidence-transfer'):
        row=next(r for r in data['runs'] if r['id']==name and r['lane']=='gcts');c=freeze(row['catalog']);r=freeze(row['result']);points=Points(c,row['length'],'support');tiles=[]
        if 'decoded' not in r or row['native']['status']!='accepted':raise ValueError('complete native-gated GCTS proof required')
        for cid in r['selected']:
            t=points.tiles[cid];slot,rid,refs=t['members'][0];rule=c['rules'][rid]
            tiles.append(dict(candidate=cid,slot=slot,refs=refs,formula_id=rule['output'],formula=c['formulas'][rule['output']],input_ids=rule['inputs'],recipe={k:v for k,v in rule['recipe'].items() if k!='definition'},weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items()),root_line=r['decoded']['commands'][slot]['final_line']))
        tiles.sort(key=lambda t:t['slot'])
        proofs.append(dict(id=name,lane=row['lane'],target=c['target'],hypothesis=row['problem']['hypothesis'],goal=row['problem']['goal'],variables=row['problem']['variables'],length=row['length'],tiles=tiles,formulas=c['formulas'],theory=c['theory'],metadata=c['configuration']['metadata'],request=r['decoded']['request'],primitive=row['primitive_proof'],primitive_lines=row['primitive_lines'],native=row['native']))
    results=[dict(id=r['id'],lane=r['lane'],length=r['length'],status=r['result']['status'],states=r['result']['nodes'],attempts=r['result']['base_attempts'],search_seconds=r['result']['seconds'],catalog_seconds=r['catalog']['build_seconds'],native_seconds=r.get('native',{}).get('wall_seconds',0),native_steps=r.get('native',{}).get('steps',0),cold_seconds=r['cold_seconds']) for r in data['runs']]
    view=dict(version='hilbert-reader-001',source=dict(file=source.name,sha256=hashlib.sha256(raw).hexdigest()),audit=data['independent_audit'],proofs=proofs,results=results,model_controls=data['model_controls'],scope=data['scope'],development=data['development'])
    (DOCS/'hilbert-reader-001.json').write_text(json.dumps(view,separators=(',',':'))+'\n');print('exported',len(proofs),'proofs',sum(p['length'] for p in proofs),'cells')
if __name__=='__main__':main()
