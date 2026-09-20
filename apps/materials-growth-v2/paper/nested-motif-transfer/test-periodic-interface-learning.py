"""Corruption controls, especially periodic image identities."""
import copy,importlib.util,json,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('checker',Path(__file__).with_name('verify-periodic-interface-learning.py'));checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
coord,meta,motif,result=map(Path,sys.argv[1:]);original=json.loads(result.read_text());checker.verify(coord,meta,motif,result)
def self_edge(d):return next(o for o in d['observations'] if o['clusterA']==o['clusterB'])
def corrupt(name,edit):
    data=copy.deepcopy(original);edit(data)
    with tempfile.TemporaryDirectory(prefix='gcts-periodic-interface-control-') as directory:
        p=Path(directory)/'bad.json';p.write_text(json.dumps(data))
        try:checker.verify(coord,meta,motif,p)
        except (AssertionError,ValueError,KeyError,IndexError):print('Rejected:',name,flush=True)
        else:raise AssertionError('Accepted corruption: '+name)
corrupt('self image collapsed to same cell',lambda d:self_edge(d).__setitem__('imageShift',[0,0,0]))
corrupt('periodic displacement erased',lambda d:self_edge(d).__setitem__('d',[0.,0.,0.]))
corrupt('invented recurrence',lambda d:d['models'][0].__setitem__('trainingFrames',999))
corrupt('altered learned marking',lambda d:d['models'][0]['valueA'].__setitem__(0,999.))
corrupt('missing evaluation observation',lambda d:d['observations'].pop())
print('All periodic interface corruption controls passed')
