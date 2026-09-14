"""Small joint-learning control and corruption rejection of full witnesses."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
j=module('joint','boron-face-joint-selection.py');v=module('verify','verify-boron-face-joint-selection.py')
d={'types':[{'id':0,'offset':0,'positions':[[0,0,0],[1,0,0]],'ties':[[0,1]],'kind':'finite-face'}],
   'configurations':[{'file':'triangle','atoms':3,'occurrences':[{'type':0,'ids':ids} for ids in ([0,1],[1,2],[2,0])]}]}
r=j.train(d,4,5);assert r['weightsByRole']==[2] and r['selected']==[[0,1,2]] and r['checks'][0]['positiveComponents']==1
if len(sys.argv)>2:
    original=json.loads(Path(sys.argv[2]).read_text());mutations=[]
    bad=copy.deepcopy(original);bad['result']['weightsByRole'][0]=0;mutations.append(bad)
    bad=copy.deepcopy(original);bad['result']['selected'][0].pop();mutations.append(bad)
    bad=copy.deepcopy(original);bad['result']['selected'][0].append(bad['result']['selected'][0][0]);mutations.append(bad)
    bad=copy.deepcopy(original);bad['result']['checks'][0]['positiveComponents']=100;mutations.append(bad)
    with tempfile.TemporaryDirectory(prefix='gcts-face-joint-tests-') as scratch:
        for i,bad in enumerate(mutations):
            p=Path(scratch)/f'{i}.json';p.write_text(json.dumps(bad))
            try:
                with contextlib.redirect_stdout(io.StringIO()):v.verify(sys.argv[1],p)
            except AssertionError:continue
            raise AssertionError(f'Corruption {i} accepted')
print('Joint half-weight control and requested weight/selection/connectivity corruption tests passed.')
