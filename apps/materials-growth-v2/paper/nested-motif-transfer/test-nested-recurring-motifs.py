"""Corruption controls for the nested dictionary evidence checker."""
import copy,importlib.util,json,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('checker',Path(__file__).with_name('verify-nested-recurring-motifs.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
coord,meta,result=map(Path,sys.argv[1:]);original=json.loads(result.read_text())
checker.verify(coord,meta,result)
def corrupt(name,edit):
    data=copy.deepcopy(original);edit(data)
    with tempfile.TemporaryDirectory(prefix='gcts-nested-control-') as directory:
        path=Path(directory)/'corrupt.json';path.write_text(json.dumps(data))
        try:checker.verify(coord,meta,path)
        except (AssertionError,ValueError,KeyError,IndexError):print('Rejected:',name)
        else:raise AssertionError('Accepted corruption: '+name)
corrupt('inflated training recurrence',lambda d:d['trainingFrameUsage'].__setitem__('0',9999))
corrupt('evaluation template leakage',lambda d:d['types'][0].__setitem__('sourceConfiguration',next(r['id'] for r in d['rows'] if not r['training'])))
corrupt('missing covered atom',lambda d:d['rows'][0]['clusters'].pop())
corrupt('shifted positive pose',lambda d:d['rows'][0]['proposals'][0]['fit']['translation'].__setitem__(0,d['rows'][0]['proposals'][0]['fit']['translation'][0]+.7))
corrupt('reflected pose',lambda d:d['rows'][0]['proposals'][0]['fit']['rotationRow'][0].__setitem__(0,-1))
print('All nested evidence controls passed')
