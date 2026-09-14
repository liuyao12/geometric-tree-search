"""Small solver controls and mutation rejection for stored six-model evidence."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load('precheck','boron-face-precheck.py');v=load('verify','verify-boron-face-precheck.py')
types=[{'id':0,'offset':0,'positions':[[0,0,0],[1,0,0]],'ties':[[0,1]]}]
c={'file':'triangle','atoms':3,'occurrences':[{'type':0,'ids':ids} for ids in ([0,1],[1,2],[2,0])]}
r=p.solve(types,[c]);assert r['weights']==['1/2','1/2'] and r['activeScalarClasses']==1
types=[{'id':0,'offset':0,'positions':[[0,0,0]],'ties':[]}]
c={'file':'inconsistent-incidences','atoms':2,'occurrences':[{'type':0,'ids':[i]} for i in (0,1,1)]}
r=p.solve(types,[c]);assert r['status']=='exact restricted nonnegative filling obstruction'
if len(sys.argv)>2:
    folder,path=sys.argv[1:3];original=json.loads(Path(path).read_text())
    mutations=[]
    bad=copy.deepcopy(original);good=next(r for r in bad['results'] if 'weights' in r)
    good['weights'][next(i for i,x in enumerate(good['weights']) if x is not None)]='0';mutations.append(bad)
    bad=copy.deepcopy(original);proof=next(r for r in bad['results'] if 'farkasRows' in r)
    proof['farkasRhs']='1';mutations.append(bad)
    bad=copy.deepcopy(original);bad['configurations'][0]['occurrences'].pop();mutations.append(bad)
    with tempfile.TemporaryDirectory(prefix='gcts-face-mutations-') as scratch:
        for i,bad in enumerate(mutations):
            path=Path(scratch)/f'{i}.json';path.write_text(json.dumps(bad))
            try:
                with contextlib.redirect_stdout(io.StringIO()):v.verify(folder,path)
            except AssertionError:continue
            raise AssertionError(f'Mutation {i} was accepted')
print('Exact half-weight control, inconsistent-incidence proof, and requested artifact mutations passed.')
