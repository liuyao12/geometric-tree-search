"""ROOT static-audit source review and metadata only; no activation or calls."""
import ast
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT=Path.cwd();FOLDER=ROOT/'.gcts-active/fixed-family-transfer-independent-source-20261012';OUT=ROOT/'.gcts-active/fixed-family-transfer-progress-20261012'

def pin(path):
    d=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}

def main():
    started=time.monotonic();pp=FOLDER/'static-audit-plan-v1.json';plan=json.loads(pp.read_text());r=pin(pp)
    assert r['sha256']=='43d8ae0fd11ff5616885b77d975dc6d9c85fadf9d4a5125e82ce710779e3bba6' and r['bytes']==255813
    assert plan['stage']=='static' and plan['status']=='frozen_actual_inputs_pending_ROOT_activation'
    assert plan['limits']=={'whole_seconds':180,'supervisor_seconds':175,'child_seconds':170,'peak_bytes':536870912}
    records=plan['sources']+plan['libraries']+plan['inputs']+plan['preserved']
    unique={}
    for rec in records:
        expected={k:rec[k] for k in ('path','sha256','bytes')}
        if rec['path'] not in unique:unique[rec['path']]=pin(Path(rec['path']))
        assert unique[rec['path']]==expected,rec['path']
    assert len(unique)==855
    parsed=[]
    for path in sorted({p['path'] for p in plan['sources']+plan['libraries']}):
        ast.parse(Path(path).read_text(),filename=path,feature_version=(3,9));parsed.append(path)
    assert len(parsed)==15
    for name in ('binary','observer'):
        rec=plan['runtime'][name];assert pin(Path(rec['path']))==rec
    with zipfile.ZipFile(FOLDER/'sources-v1.zip') as z:
        for name in z.namelist():assert z.read(name)==(FOLDER/name).read_bytes(),name
    absent=[plan['activation_path']]+list(plan['outputs'].values());assert all(not Path(p).exists() for p in absent)
    result={'status':'passed_ROOT_source_and_exact_metadata_review_for_static_stage_only','plan':r,
       'unique_verified_paths':len(unique),'Python39_AST_sources':parsed,'prospective_activation_and_outputs_absent':absent,
       'complete_source_coverage':['transfer_context_oracle_v1.py','transfer_independent_worker_v1.py','transfer_independent_owner_v1.py','freeze_transfer_audit_v1.py'],
       'source_scope':'Four static-phase execution/metadata sources read completely. Separate future trace/transaction sources are AST/pin checked only; full future trace review remains mandatory before trace dispatch. Older independent point/symbolic/body/pool kernels retain earlier reviewed authority.',
       'acceptance_scope':'All229 new/retained licenses independently rechecked; all171 conditional bodies recursively expanded; full initial24 raw key/t/m domains and complete171/29241grammar;14 mutated contextual payloads and per-group controls. Static acceptance is not a target proof.',
       'gaps':['Finite known-library context transfer and canonical1/2-component grammar; no universal Wang compiler correspondence.',
               'Known standard pinned JSON; no general hostile duplicate-key parser theorem.',
               'Actual static result/owned resource gate still unexecuted; no proof search, RL training or native query.'],
       'metadata_seconds_before_final_write':time.monotonic()-started,'scientific_imports_or_calls':0,'activation_written':False}
    with (OUT/'static-audit-source-review-v1.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'unique_pins':len(unique),'scientific_calls':0,'metadata_seconds':result['metadata_seconds_before_final_write']}))

if __name__=='__main__':main()
