import copy,importlib.util,json,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('check',Path(__file__).with_name('verify-reposed-interfaces.py'));check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
coord,meta,motif,interface,result=map(Path,sys.argv[1:]);original=json.loads(result.read_text());check.verify(coord,meta,motif,interface,result)
def witness(d):return next(r['witness'] for r in d['rows'] if r['witness'])
def corrupt(name,edit):
    d=copy.deepcopy(original);edit(d)
    with tempfile.TemporaryDirectory(prefix='gcts-pose-check-') as directory:
        p=Path(directory)/'bad.json';p.write_text(json.dumps(d))
        try:check.verify(coord,meta,motif,interface,p)
        except (AssertionError,ValueError,KeyError,IndexError):print('Rejected:',name)
        else:raise AssertionError(name)
corrupt('missing evaluation pair',lambda d:d['rows'].pop())
corrupt('changed pose translation',lambda d:witness(d)['poseA']['translation'].__setitem__(0,1000.))
corrupt('nonproper rotation',lambda d:witness(d)['poseA']['rotationRow'][0].__setitem__(0,20.))
corrupt('nonbijective correspondence',lambda d:witness(d)['poseA']['permutation'].__setitem__(0,witness(d)['poseA']['permutation'][1]))
corrupt('invented error',lambda d:witness(d)['errors'].__setitem__(0,999.))
print('All continuous-pose witness controls passed')
