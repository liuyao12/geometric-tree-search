"""Bind saved searches to the certified static exclusions and reconstruct fillings."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

inp,learned,proofpath,folder,dest=map(Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('filling',Path(__file__).with_name('verify-boron-face-search.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
result=v.verify(inp,learned,folder)
proof=json.loads(proofpath.read_text());proofhash=hashlib.sha256(proofpath.read_bytes()).hexdigest()
for fold,record in enumerate(proof['results']):
    excluded=set(record['certificate']['excluded']) if record['certificate'] else set()
    for marked in ('false','true'):
        run=json.loads((folder/f'{fold}-{marked}.json').read_text())
        assert run['result']['supportHash']==proofhash
        assert run['result']['staticCertifiedExclusions']==len(excluded)
        assert not {int(j) for j in run['result']['selected']}.intersection(excluded)
        for name,digest in run['researchSourceHashes'].items():
            assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==digest
result['supportHash']=proofhash
result['allSelectionsRespectCertifiedExclusions']=True
dest.write_text(json.dumps(result,indent=2)+'\n')
