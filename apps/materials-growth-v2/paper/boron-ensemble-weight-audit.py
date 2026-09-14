"""Conditional t identifiability after adding verified alternative fillings."""
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

spec=importlib.util.spec_from_file_location('weights',Path(__file__).with_name('boron-weight-identifiability.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
inp,learned,alternatives,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];a=json.loads(alternatives.read_text())
assert a['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert a['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
expanded=copy.deepcopy(d);labels=copy.deepcopy(r)
for run in a['runs']:
    if run['status']=='exact connected filling':
        expanded['configurations'].append(d['configurations'][run['fold']])
        labels['selected'].append(run['selected'])
result=w.audit(expanded,labels)
result['scope']='Conditional audit of original and alternative fillings of the same six coordinate configurations; not additional material samples.'
result['alternativesHash']=hashlib.sha256(alternatives.read_bytes()).hexdigest()
result['inputHash']=a['inputHash'];result['learningHash']=a['learningHash']
dest.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('roles','uniqueEquations','rank','nullity')}))
