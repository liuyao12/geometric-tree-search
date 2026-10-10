"""Read-only projection of audited proof families and actual aggregate marks."""
import gzip,hashlib,json
from pathlib import Path
import audit_induction_proofs as I
import audit_induction_clusters as H
from audit_serialized_kernel import freeze
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def load(d):return json.loads(gzip.decompress((DOCS/d['file']).read_bytes()))
def projection(row,run,library,source=False):
    c=freeze(row['catalog']);r=freeze(run['result']);n=row['problem']['length'] if source else row['length']
    points=H.Points(c,n,freeze(library),'support'==r.get('marking') if source else r['marked'])
    if run['native']['status']!='accepted':raise ValueError('complete native gate')
    if source:
        selected=set(r['placements']);ids=[cid for cid,t in enumerate(points.tiles) if len(t['members'])==1 and t['members'][0] in selected]
    else:ids=r['selected']
    if tuple(points.expand(ids))!=tuple(r['placements']):raise ValueError('exact selected macro expansion')
    groups=[];tiles=[];base_lookup={t['members'][0]:t for t in points.tiles[:len(points.base)]}
    for cid in ids:
        t=points.tiles[cid];slots={key[0] for key in t['members']};incoming={};outgoing=[]
        outside_refs={j for slot,rid,refs in r['placements'] if slot not in slots for j in refs}
        for slot,rid,refs in t['members']:
            rule=c['rules'][rid];marks=base_lookup[(slot,rid,refs)]['marks'].copy()
            marks[(2*slot,2)]=cid
            for ref,f in zip(refs,rule['inputs']):
                if ref not in slots:incoming[ref]=f
            if slot in outside_refs or slot==n-1:outgoing.append([slot,rule['output']])
            tiles.append(dict(candidate=cid,slot=slot,rule_id=rid,refs=refs,formula_id=rule['output'],formula=c['formulas'][rule['output']],input_ids=rule['inputs'],recipe={k:v for k,v in rule['recipe'].items() if k!='definition'},weights=[[(2*slot,0),12]],marks=sorted(marks.items()),root_line=r['decoded']['commands'][slot]['final_line']))
        groups.append(dict(candidate=cid,members=t['members'],weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items()),item=t['item'],incoming=sorted(incoming.items()),outgoing=outgoing))
    tiles.sort(key=lambda t:t['slot']);groups.sort(key=lambda g:g['members'][0][0])
    if len(tiles)!=n:raise ValueError('whole proof row')
    p=row['problem']
    return dict(id=row['id'],lane='gcts-source' if source else run['lane'],target=c['target'],hypothesis=p['hypothesis'],goal=p['goal'],variables=p['variables'],length=n,tiles=tiles,groups=groups,formulas=c['formulas'],theory=c['theory'],metadata=c['configuration']['metadata'],request=r['decoded']['request'],primitive=run['primitive_proof'],primitive_lines=run['primitive_lines'],native=run['native'])
def main():
    path=DOCS/'hilbert-witness-clusters-001.json';d=json.loads(path.read_text())
    if d.get('independent_audit',{}).get('status')!='passed':raise ValueError('complete independent audit required')
    donor=load(d['donors'][0]);proofs=[projection(donor,donor['run'],[],True)];results=[]
    for descriptor in d['cases']:
        row=load(descriptor)
        if row['id'] in ('unique-joining-line','joining-exists-reordered'):
            run=next(r for r in row['runs'] if r['lane']=='gcts-motifs' and r['replica']==0)
            proofs.append(projection(row,run,d['library']))
        for run in row['runs']:
            r=run['result'];native=run.get('native',{})
            results.append(dict(id=row['id'],lane=run['lane'],replica=run['replica'],status=r['status'],states=r['nodes'],attempts=r['base_attempts'],macro_attempts=r['macro_attempts'],motif_instances=r['motif_instances'],candidate_universe=r['candidate_universe'],base_universe=r['base_universe'],catalog_seconds=run['catalog_build_seconds'],search_seconds=r['seconds'],build_seconds=r['build_seconds'],instantiation_seconds=r['instantiation_seconds'],decode_seconds=r.get('decode_seconds',0),native_seconds=native.get('wall_seconds',0),native_steps=native.get('steps',0),cold_seconds=run['cold_seconds'],first_query_seconds=run['cold_seconds']+(d['training_seconds'] if run['lane'].endswith('motifs') else 0)))
    # Historical comparison is presentation evidence only; never a search input.
    arithmetic_path=DOCS/'induction-cluster-policy-view-001.json';arithmetic=json.loads(arithmetic_path.read_text());case=next(c for c in arithmetic['cases'] if c['problem']['id']=='ind-add-left-successor')
    history=dict(file=arithmetic_path.name,sha256=hashlib.sha256(arithmetic_path.read_bytes()).hexdigest(),discovery_seconds=arithmetic['discovery_seconds'],rl_learning_seconds=arithmetic['rl_learning_seconds'],training_seconds=arithmetic['training_seconds'],runs=[dict(lane=r['lane'],replica=r['replica'],status=r['metrics']['status'],states=r['metrics']['nodes'],cold_seconds=r['cold_seconds']) for r in case['runs']])
    view=dict(version='hilbert-cluster-reader-001',source=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),archive_descriptors=d['donors']+d['cases'],audit=d['independent_audit'],library=d['library'],library_sha256=d['library_sha256'],training_seconds=d['training_seconds'],compile_seconds=d['compile_seconds'],source_cold_seconds=donor['run']['cold_seconds'],mining_seconds=donor['mining_seconds'],proofs=proofs,results=results,scope=d['scope'],comparison=d['comparison'],development=d['development'],arithmetic=history)
    (DOCS/'hilbert-cluster-reader-001.json').write_text(json.dumps(view,separators=(',',':'))+'\n')
    print('exported',len(proofs),'proofs',sum(p['length'] for p in proofs),'cells',len(d['library']),'families')
if __name__=='__main__':main()
