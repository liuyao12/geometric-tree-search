"""Read-only, exact square/point view of the selected notebook33 proof tiles.

No new search or fabricated edge colors. Independently reconstructed point
types are projected from the audited run which supplied each shown proof.
Square bodies draw occupancy; longer-range markings keep their actual points.
"""
import hashlib,json
from pathlib import Path
import audit_semantic_proofs as A
import audit_coarse_proofs as V
from audit_serialized_kernel import freeze

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def file_sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def root_links(c,r,hierarchy):
    by_slot={key[0]:key for key in r['placements']};last=max(by_slot);path=[];slot=last
    while True:
        key=by_slot[slot];path.append(key)
        if not key[2]:break
        if len(key[2])!=1:raise ValueError('current equation proof path requires unary references')
        slot=key[2][0]
    path.reverse();mapping={};cursor=0;i=0;root=hierarchy['request']['proof'];transactions=hierarchy['transactions_used']
    while i<len(path):
        key=path[i];matches=[t for t in transactions if tuple(t['members'])==tuple(path[i:i+len(t['members'])])]
        if matches:
            t=max(matches,key=lambda t:len(t['members']));j=t['root_line']
            if j!=cursor or root[j]['name']!=t['definition'] or root[j]['formula']!=c['formulas'][c['rules'][t['members'][-1][1]]['output']]:raise ValueError('actual metatile/root line binding')
            for member in t['members']:mapping[member[0]]=j
            cursor+=1;i+=len(t['members']);continue
        rule=c['rules'][key[1]];cursor+=2 if rule['recipe']['kind']=='copy' else 1
        if root[cursor-1]['formula']!=c['formulas'][rule['output']]:raise ValueError('actual base tile/root line binding')
        mapping[key[0]]=cursor-1;i+=1
    if cursor+len(c['close_variables'])!=len(root):raise ValueError('complete root path and quantified closure')
    return mapping

def record(problem,run,c,library,proof_record):
    r=run['result'];request=run['hierarchy']['request']
    if r['status']!='finite_exact_proof_tiling' or run['native']['status']!='accepted':raise ValueError('actual exact/native-positive run required')
    if hashlib.sha256(A.packed(request)).hexdigest()!=proof_record['certificate_sha256']:raise ValueError('reader certificate/run binding')
    if A.pin(request)!=proof_record['problem_sha256']:raise ValueError('external theorem binding')
    links=root_links(c,r,run['hierarchy']);n=problem['length'];tiles=[]
    if run.get('lane'):
        points=V.Points(c,n,r['width'],library)
        if r['width']!=1:raise ValueError('reader selects fine cells for square display')
        for step,cid in enumerate(r['selected']):
            t=points.tiles[cid];tiles.append(dict(candidate=cid,search_step=step+1,kind='searched cluster' if t['item'] else 'base search tile',members=t['members'],item=t['item'],weights=sorted(t['weights'].items()),marks=sorted(t['marks'].items())))
        inventory=r['candidate_universe'];base_inventory=r['base_universe'];owner_marks=True
    else:
        universe=A.candidates(c,n)
        for step,key in enumerate(r['placements']):
            slot=key[0];tiles.append(dict(candidate=key,search_step=step+1,kind='base search tile',members=(key,),item=None,weights=[((2*slot,0),12)],marks=[((2*j,1),v) for j,v in sorted(universe[key].items())]))
        inventory=len(universe);base_inventory=inventory;owner_marks=False
    for tile in tiles:
        tile['root_lines']=sorted({links[k[0]] for k in tile['members'] if k[0] in links})
        tile['outputs']=[dict(slot=k[0],formula_id=c['rules'][k[1]]['output'],rule_id=k[1],references=k[2],label=c['rules'][k[1]]['recipe'].get('axiom',c['rules'][k[1]]['recipe'].get('witness',{}).get('rule',c['rules'][k[1]]['recipe']['kind']))) for k in tile['members']]
    totals={};marks={(2*(n-1),1):c['target_id']}
    for tile in tiles:
        for p,v in tile['weights']:totals[p]=totals.get(p,0)+v
        for p,v in tile['marks']:
            if p in marks and marks[p]!=v:raise ValueError('selected marking conflict')
            marks[p]=v
    if totals!={(2*i,0):12 for i in range(n)}:raise ValueError('all proof cells covered exactly')
    return dict(id=problem['id'],length=n,target_id=c['target_id'],formulas=c['formulas'],tiles=tiles,owner_marks=owner_marks,candidate_universe=inventory,base_universe=base_inventory,formula_count=len(c['formulas']),rule_count=len(c['rules']),certificate_sha256=proof_record['certificate_sha256'],problem_sha256=proof_record['problem_sha256'],root_lines=len(request['proof']),scope='Actual selected fine-point types and saved placement order; every displayed square denotes one full-capacity proof cell. Extended marks include formula ports and, in the coarse-model fine lane, ownership ports. Not a uniform four-edge Wang inventory.')

def main():
    evidence=DOCS/'coarse-proofs-001.json';reader=DOCS/'wang-proofs-001.json';data=json.loads(evidence.read_text());proofs=json.loads(reader.read_text())
    if data['independent_audit']['status']!='passed' or proofs['parent']['sha256']!=file_sha(evidence):raise ValueError('audited parent and exact reader binding required')
    for name,pin in data['sources'].items():
        if file_sha(HERE/name)!=pin:raise ValueError('measured source changed '+name)
    d=freeze(data);rows={r['problem']['id']:r for r in d['evaluation']};donors={r['problem']['id']:r for r in d['donors']};out=[]
    for proof in proofs['theorems']:
        if proof['discovered_by']=='donor-gcts':
            row=donors[proof['id']];run=row;library=()
        else:
            row=rows[proof['id']];run=next(r for r in row['runs'] if r['lane']==proof['discovered_by'] and r['replica']==proof['replica']);library=d['library'] if run['library'] else ()
        out.append(record(row['problem'],run,row['catalog'],library,proof))
    result=dict(parent=dict(file=evidence.name,sha256=file_sha(evidence)),proof_reader=dict(file=reader.name,sha256=file_sha(reader)),exporter_sha256=file_sha(Path(__file__)),dependencies={n:file_sha(HERE/n) for n in ('audit_semantic_proofs.py','audit_coarse_proofs.py','audit_proof_clusters.py','audit_serialized_kernel.py')},theorems=out)
    target=DOCS/'wang-tiles-001.json';target.write_text(json.dumps(result,separators=(',',':'))+'\n');print('exact tile views',len(out),'proofs',sum(len(r['tiles']) for r in out),'selected tiles',target.stat().st_size,'bytes')

if __name__=='__main__':main()
