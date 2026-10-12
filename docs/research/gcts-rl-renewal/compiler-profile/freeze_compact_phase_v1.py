"""Metadata-only prospective plan freezer; never imports a scientific module."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def pin(path):
    p=Path(path)
    if not p.is_absolute(): p=ROOT/p
    raw=p.read_bytes()
    try: name=str(p.relative_to(ROOT))
    except ValueError: name=str(p)
    return dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def freeze(spec_path):
    spec=json.loads(Path(spec_path).read_text())
    assert spec['schema']=='ROOT-fresh-cluster-static-prospective-spec-v1'
    assert spec['stage'] in ('preparation','replay') and spec['scientific_calls_by_spec_author']==0
    stage=spec['stage']
    assert spec['instance_count']==1 and spec['declared_fixture_case_count']==9
    review=HERE/'ROOT-source-review-v1.json'
    reviewed=json.loads(review.read_text())
    assert reviewed['source_review_passed'] and reviewed['scientific_calls']==0
    # Every caller-supplied closure pin is exact, including independent review.
    closure={p['path']:p for p in spec['closure']}
    assert len(closure)==len(spec['closure'])
    for name,record in closure.items(): assert pin(name)==record
    for path in (review,Path(__file__),HERE/'run_owned_bridge_v2.py',Path(spec_path)):
        record=pin(path); closure[record['path']]=record
    # The owner compares the executable's lexical invocation path. Hashing
    # follows the symlink, but resolving its name would change that contract.
    runtime=Path(sys.executable)
    closure[str(runtime)]=pin(runtime)
    observer=Path('/bin/ps'); closure[str(observer)]=pin(observer)
    worker=(ROOT/spec['worker']).resolve()
    assert pin(worker)==closure[spec['worker']]
    assert not (HERE/(stage+'-owner-v1')).exists()
    assert not (ROOT/spec['worker_receipt']).exists()
    limits=spec['limits']
    assert limits['whole_seconds']==60 and limits['peak_bytes']==536870912
    assert limits['caller_seconds']>limits['whole_seconds']
    plan=dict(schema='ROOT-guard-native-owned-plan-v1',stage=stage,
        scope=spec['scope'],
        instance_count=1,declared_fixture_case_count=9,closure=list(closure.values()),runtime_binary=pin(runtime),
        worker=spec['worker'],argv=[str(runtime),'-B',str(worker),*spec['worker_arguments']],
        worker_receipt=spec['worker_receipt'],limits=limits,
        prospective_spec=pin(spec_path),ROOT_source_review=pin(review))
    target=HERE/(stage+'-plan-v1.json')
    with target.open('x') as stream: json.dump(plan,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(plan=pin(target),closure_files=len(closure),scientific_calls=0)),flush=True)

if __name__=='__main__':
    assert len(sys.argv)==2
    freeze(sys.argv[1])
