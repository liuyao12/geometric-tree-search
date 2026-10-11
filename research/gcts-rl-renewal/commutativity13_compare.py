"""Byte-pinned full semantic model correspondence with independent external track."""
import gzip
import hashlib
import json
import resource
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.gcts-active/commutativity13-20261011';OTHER=ROOT/'.gcts-active/external-point-commutativity-20261011'
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    began=time.perf_counter();path=OUT/'external-model-correspondence-plan.json'
    if path.exists():raise ValueError('immutable exact correspondence plan already exists')
    plan=dict(source_sha256={str(Path(__file__).relative_to(ROOT)):h(Path(__file__))},input_sha256={},seconds=5,rss_bytes=536870912,
              scope='All fields under exact-scalar-point-model-v1 canonical sorted-key compactUTF8JSON, exact array order. No target proof word, SAT query or GCTS ordering input.')
    for p in [OUT/'binding13.json.gz',OUT/'preflight-plan.json',OUT/'preflight-summary.json',OTHER/'point-13.json.gz',OTHER/'plan.json',OTHER/'encoding-freeze.json']:
        plan['input_sha256'][str(p.relative_to(ROOT))]=h(p)
    path.write_text(json.dumps(plan,indent=2)+'\n')
    with gzip.open(OUT/'binding13.json.gz','rt') as f:a=json.load(f)
    with gzip.open(OTHER/'point-13.json.gz','rt') as f:b=json.load(f)['semantic']
    sha=hashlib.sha256(packed(a)).hexdigest();other=hashlib.sha256(packed(b)).hexdigest()
    if sha!=other or a!=b:raise ValueError('complete model mismatch')
    result=dict(status='passed_exact_independent13point_model_hash',schema=a['schema'],complete_model_sha256=sha,external_complete_model_sha256=other,
                component_sha256={k:hashlib.sha256(packed(v)).hexdigest() for k,v in a.items()},plan_sha256=h(path),
                seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if result['seconds']>5 or result['peak_rss_bytes']>536870912:result['status']='unknown_model_correspondence_resource_budget'
    (OUT/'external-model-correspondence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
