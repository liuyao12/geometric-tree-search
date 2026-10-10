"""Check the explanatory reference view against the frozen independent kernel.

No new search or policy training. The original audited artifact is immutable.
"""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
import check_propositional_receptors as A

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal'
NODE=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
PIN='34b8f4315441f720cdb042b4f1bc610f1bbbb5040dda51b56462ea77ff763b3e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    artifact=DOC/'propositional-receptors-001.json';A.need(sha(artifact)==PIN,'Frozen discovery artifact')
    audit=json.loads((DOC/'propositional-receptors-audit-001.json').read_bytes());A.need(audit['producer_sha256']==PIN,'Original independent audit binding')
    data=A.frozen(json.loads(artifact.read_bytes()));c=next(c for c in data['cases'] if c['id']=='identity-P');r=c['runs']['point']
    cert=A.certificate(data['basis'],c['target'],c['length'],c['hypotheses'],r['placements'],r['point_tiles'])
    tiles=sorted(r['point_tiles'],key=lambda t:t['key'][0]);last=tiles[-1];rule=data['basis']['rules'][last['key'][1]]
    initial={p:v for p,v in r['initial_marks']};prefix=dict(initial)
    for t in tiles[:-1]:prefix.update(t['marks'])
    outcomes=[]
    for reference in range(4):
        assignments={};internal=[]
        for j,a in ((4,rule['output']),(reference,rule['inputs'][0]),(3,rule['inputs'][1])):
            for p,v in [((2*j,1),0)]+[((2*j,2+k),v) for k,v in enumerate(A.word(a)+'e')]:
                if p in assignments and assignments[p]!=v:internal.append(dict(point=p,first=assignments[p],second=v))
                else:assignments[p]=v
        entries=sorted(assignments.items());conflicts=[dict(point=p,actual=prefix[p],demanded=v) for p,v in entries if p in prefix and prefix[p]!=v]
        valid=not internal and not conflicts
        A.need(valid==(reference==0),'Only the actual antecedent fits')
        changed=tuple(dict(t,key=(4,last['key'][1],(reference,3))) if t['key'][0]==4 else t for t in r['point_tiles'])
        if valid:A.need(tuple(entries)==last['marks'],'Actual original final tile')
        else:
            # The original inference inventory binds every mark, not just its caption.
            changed=tuple(dict(t,marks=tuple(entries)) if t['key'][0]==4 else t for t in changed)
            try:A.certificate(data['basis'],c['target'],c['length'],c['hypotheses'],tuple(t['key'] for t in changed),changed)
            except ValueError:pass
            else:raise ValueError('Forged reference accepted by independent kernel')
        outcomes.append(dict(reference=reference,accepted=valid,conflicts=conflicts,internal_conflicts=internal,occupancy=last['occupancy'],marks=entries))
    with tempfile.TemporaryDirectory(prefix='gcts-attention-') as tmp:
        expected=Path(tmp)/'expected.json';expected.write_text(json.dumps(dict(outcomes=outcomes,certificate=cert)))
        checked=subprocess.run([str(NODE),str(ROOT/'research/gcts-rl-renewal/test_propositional_attention.cjs'),str(expected)],check=True,capture_output=True,text=True)
    files=['docs/research/gcts-rl-renewal/propositional-attention.js','docs/research/gcts-rl-renewal/propositional-receptors.html','docs/research/gcts-rl-renewal/index.html','research/gcts-rl-renewal/README.md','research/gcts-rl-renewal/test_propositional_attention.cjs','research/gcts-rl-renewal/validate_propositional_attention.py']
    out=dict(version='propositional-attention-validation-001',status='passed',artifact_sha256=PIN,original_audit_sha256=sha(DOC/'propositional-receptors-audit-001.json'),independent_checker_sha256=sha(ROOT/'research/gcts-rl-renewal/check_propositional_receptors.py'),certificate=cert,reference_trials=4,valid_trials=1,invalid_references_rejected=3,reader=json.loads(checked.stdout),files={p:sha(ROOT/p) for p in files},new_searches=0,new_training_runs=0,scope='Existing five-line primitive certificate and exact original point data independently rechecked. All four reference trials agree with an independent construction; three reject. Browser layout checks are recorded separately; no new speed or trained-attention claim.')
    (DOC/'propositional-attention-validation-001.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
