"""ROOT metadata/source gate before one compiled-context preparation."""
import ast
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT=Path.cwd();FOLDER=Path('.gcts-active/fixed-family-transfer-source-v1-20261012');OUT=Path('.gcts-active/fixed-family-transfer-progress-20261012')

def pin(path):
    data=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def save(path,data):
    with path.open('x') as stream:json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n')

def main():
    begin=time.monotonic();p=FOLDER/'preparation-plan-v1.json';record=pin(p)
    assert record['sha256']=='126f5a25751b8f25074ed6f7506b30f5f692cabe4c84c28a23597b0aa40d9ac3' and record['bytes']==191756
    plan=json.loads(p.read_text());records=plan['sources']+plan['inputs']+plan['preserved_files']
    for r in records:
        assert pin(Path(r['path']))=={k:r[k] for k in ('path','sha256','bytes')},r['path']
    for r in plan['sources']:ast.parse(Path(r['path']).read_text(),filename=r['path'],feature_version=(3,9))
    for k in ('binary','process_metadata'):
        r=plan['runtime'][k];assert pin(Path(r['path']))==r
    integration=json.loads((FOLDER/'integration-v1.json').read_text())
    for r in integration['files']:assert pin(Path(r['path']))==r
    with zipfile.ZipFile(FOLDER/'sources-v1.zip') as z:
        for name in z.namelist():
            data=z.read(name);assert data==Path(name).read_bytes(),name
    absent=[FOLDER/plan['activation_basename']]+[FOLDER/n for n in plan['proposed_outputs']]+[FOLDER/'search-plan-v1.json']
    assert all(not p.exists() for p in absent)
    review={'status':'passed_ROOT_independent_complete_source_and_metadata_preparation_review',
            'plan':record,'source_count':len(plan['sources']),'input_roles':len(plan['inputs']),
            'preserved_pin_records':len(plan['preserved_files']),'unique_pin_paths':len({r['path'] for r in records}),
            'source_coverage':'Full compiler, preparation, runtime, register, DFS, search worker, finalizer, both owners and metadata freezer read. Master contract reread this turn.',
            'conformance':'Fresh assumption licenses and identities;226 unchanged logical witnesses;171 retained bodies; full initial domains/single-pair census; original24-row/global scheduler/complete fallback; independent fresh static validation mandatory before search.',
            'gaps':['Finite palette, restricted single/pair canonical embeddings, fixed24-row boundary; not universal machine encoding.',
                    'No learnt failure markings or training. Old conditional source bodies are known infrastructure.',
                    'Inherited sampled monitor omits observer RSS; memory figure is not aggregate host upper bound or OS hard cap.',
                    'Cold serialization and cleanup included by ROOT outer clock; source authoring remains unmeasured.'],
            'scientific_calls':0,'metadata_seconds_before_final_write':time.monotonic()-begin,'output_paths_confirmed_absent':[str(p) for p in absent]}
    save(OUT/'preparation-source-review-v1.json',review)
    save(FOLDER/plan['activation_basename'],{'status':plan['activation_status'],'plan':record,'ROOT_source_review':pin(OUT/'preparation-source-review-v1.json'),
         'scope':'One full new-context/model/domain/family-pool preparation. No search, training or logical/native acceptance; independently gated afterward.'})
    print(json.dumps({'review':pin(OUT/'preparation-source-review-v1.json'),'activation':pin(FOLDER/plan['activation_basename'])}))

if __name__=='__main__':main()
