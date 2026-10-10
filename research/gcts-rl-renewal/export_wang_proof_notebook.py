"""Dedicated statement-first reader of actually searched and audited proofs.

Reads the current fresh experiment only. Expands each accepted certificate with
the independent serialized auditor; root lines have global primitive references.
"""
import hashlib,json,re
from pathlib import Path
import audit_semantic_proofs as A
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha_bytes(x):return hashlib.sha256(x).hexdigest()
def proof_record(problem,run,origin,parent):
    if run.get('native',{}).get('status')!='accepted':raise ValueError('complete native acceptance required')
    if run['result']['status']!='finite_exact_proof_tiling':raise ValueError('search must actually find the exact proof')
    request=run['hierarchy']['request'];expected=dict(protocol='gcts-fol-1',theory=problem['theory'],target=problem['target'])
    if A.pin(request)!=A.pin(expected):raise ValueError('external theorem/theory binding')
    independently=replay(A.packed(request),A.pin(expected))
    if independently['status']!='accepted':raise ValueError('full primitive expansion required')
    proof=independently['proof']
    if not proof or A.packed(proof[-1]['formula'])!=A.packed(problem['target']):raise ValueError('expanded terminal theorem')
    if any(line['rule'] in ('block','assumption') for line in proof):raise ValueError('expanded root must have only primitive lines')
    for i,line in enumerate(proof):
        for field in ('source','antecedent','implication'):
            if field in line and not 0<=line[field]<i:raise ValueError('earlier primitive reference')
    return dict(id=problem['id'],label=problem['label'],target=problem['target'],theory=request['theory'],origin=origin,discovered_by=run.get('lane','donor-gcts'),replica=run.get('replica'),length=problem['length'],term_bound=problem['term_bound'],
        search={k:run['result'][k] for k in ('status','nodes','base_attempts')},cold_seconds=run['cold_seconds'],native={k:run['native'][k] for k in ('status','steps','wall_seconds')},
        source_artifact=parent,problem_sha256=A.pin(request),certificate_sha256=sha_bytes(A.packed(request)),request=request,expanded_proof=proof,expanded_lines=len(proof),independent_status=independently['status'],
        root_lines=len(request['proof']),definition_count=len(request['blocks']),transactions_used=run['hierarchy']['transactions_used'])
def main():
    path=DOCS/'coarse-proofs-001.json';d=json.loads(path.read_text())
    if d.get('independent_audit',{}).get('status')!='passed':raise ValueError('full search and native-binding audit required')
    for name,pin in d['sources'].items():
        if sha_bytes((HERE/name).read_bytes())!=pin:raise ValueError('measured source changed '+name)
    parent=dict(file=path.name,sha256=sha_bytes(path.read_bytes()));out=dict(title='Wang-style proof notebook',parent=parent,exporter_sha256=sha_bytes(Path(__file__).read_bytes()),dependencies={n:sha_bytes((HERE/n).read_bytes()) for n in ('audit_semantic_proofs.py','audit_serialized_kernel.py','logic.py')},
        scope='Only actual positive point-tile searches from the fresh audited experiment. Eight held-out arithmetic statements and two parameterized donor statements. Fully expanded primitive root proofs are independently checked; no human proof sequence is input. Specialized bounded contextual equations, no searched induction or Euclid theorem yet.',theorems=[],controls=[],pending=[])
    for row in d['evaluation']:
        accepted=[r for lane in ('fine-meta','base','coarse2-meta','coarse3-meta','coarse2-base') for r in row['runs'] if r['lane']==lane and r.get('native',{}).get('status')=='accepted']
        if accepted:out['theorems'].append(proof_record(row['problem'],accepted[0],'held-out statement',parent))
        else:
            entry=dict(problem=row['problem'],runs=[dict(lane=r['lane'],replica=r['replica'],status=r['result']['status']) for r in row['runs']]);(out['controls'] if all(r['result']['status']=='exhausted_finite_proof_envelope' for r in row['runs']) else out['pending']).append(entry)
    for row in d['donors']:out['theorems'].append(proof_record(row['problem'],row,'parameterized donor statement',parent))
    folder=DOCS/'wang-proof-certificates-001';folder.mkdir(exist_ok=True)
    for record in out['theorems']:
        if not re.fullmatch('[a-z0-9-]+',record['id']):raise ValueError('safe external statement id')
        filename=f"wang-proof-certificates-001/{record['id']}.json";payload=A.packed(record['request']);(DOCS/filename).write_bytes(payload);record['certificate_file']=filename
    out.update(held_out_verified=sum(t['origin']=='held-out statement' for t in out['theorems']),donors_verified=sum(t['origin']=='parameterized donor statement' for t in out['theorems']),expanded_primitive_lines=sum(t['expanded_lines'] for t in out['theorems']))
    target=DOCS/'wang-proofs-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print('proof reader',len(out['theorems']),'theorems',out['expanded_primitive_lines'],'primitive lines',target.stat().st_size,'bytes')
if __name__=='__main__':main()
