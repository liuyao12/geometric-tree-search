"""Read-only projection of audited witness proofs and equivalent point rows."""
import gzip,hashlib,json
from pathlib import Path
from audit_serialized_kernel import freeze
from audit_induction_proofs import Points
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    source=DOCS/'hilbert-quantified-001.json';raw=source.read_bytes();data=json.loads(raw)
    if data.get('independent_audit',{}).get('status')!='passed':raise ValueError('full independent audit required')
    proofs=[]
    for name,lane in [('line-has-point','gcts'),('unique-joining-line','csp')]:
        row=next(r for r in data['runs'] if r['id']==name and r['lane']==lane);c=freeze(row['catalog']);r=freeze(row['result']);points=Points(c,row['length'],'support');tiles=[]
        if 'decoded' not in r or row['native']['status']!='accepted':raise ValueError('complete native-gated selected proof required')
        selected=set(r['placements'])
        for cid,t in enumerate(points.tiles):
            key=t['members'][0]
            if key not in selected:continue
            slot,rid,refs=key;rule=c['rules'][rid]
            tiles.append(dict(candidate=cid,slot=slot,refs=refs,formula_id=rule['output'],formula=c['formulas'][rule['output']],input_ids=rule['inputs'],recipe={k:v for k,v in rule['recipe'].items() if k!='definition'},weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items()),root_line=r['decoded']['commands'][slot]['final_line']))
        tiles.sort(key=lambda t:t['slot'])
        if len(tiles)!=row['length']:raise ValueError('complete row')
        proofs.append(dict(id=name,lane=lane,target=c['target'],hypothesis=row['problem']['hypothesis'],goal=row['problem']['goal'],variables=row['problem']['variables'],length=row['length'],tiles=tiles,formulas=c['formulas'],theory=c['theory'],metadata=c['configuration']['metadata'],request=r['decoded']['request'],primitive=row['primitive_proof'],primitive_lines=row['primitive_lines'],native=row['native'],encoding='Exact GCTS point encoding. For CSP this is an independently reconstructed equivalent marked row, not the internal CSP representation. Ownership is redundant for single-cell base tiles.'))
    results=[dict(id=r['id'],lane=r['lane'],length=r['length'],status=r['result']['status'],states=r['result']['nodes'],attempts=r['result']['base_attempts'],search_seconds=r['result']['seconds'],catalog_seconds=r['catalog']['build_seconds'],native_seconds=r.get('native',{}).get('wall_seconds',0),native_steps=r.get('native',{}).get('steps',0),cold_seconds=r['cold_seconds']) for r in data['runs']]
    archive=source.with_suffix('.json.gz');archive.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    view=dict(version='hilbert-quantified-reader-001',source=dict(file=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),uncompressed_file=source.name,uncompressed_sha256=hashlib.sha256(raw).hexdigest(),uncompressed_bytes=len(raw)),audit=data['independent_audit'],proofs=proofs,results=results,model_controls=data['model_controls'],scope=data['scope'],development=data['development'])
    (DOCS/'hilbert-quantified-reader-001.json').write_text(json.dumps(view,separators=(',',':'))+'\n');print('exported',len(proofs),'proofs',sum(p['length'] for p in proofs),'cells')
if __name__=='__main__':main()
