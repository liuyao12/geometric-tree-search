"""Negative controls for the independent proof-DAG checker."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
modelp,resultp=map(Path,sys.argv[1:]);original=json.loads(resultp.read_text());checker=Path(__file__).with_name('verify-composed-geometry-cores.py')
def missing_blocker(d):d['cores'][0]['blockers'].pop()
def missing_owner(d):d['cores'][0]['owners'].pop()
def cycle(d):
    i=next(i for i,c in enumerate(d['cores']) if c['dependencies']);b=next(b for b in d['cores'][i]['blockers'] if b['reason']=='prior-core');b['dependency']=i
def wrong_model(d):d['sourceHash']='0'*64
with tempfile.TemporaryDirectory(prefix='gcts-composed-proof-test-') as tmp:
    for mutate in [missing_blocker,missing_owner,cycle,wrong_model]:
        d=copy.deepcopy(original);mutate(d);path=Path(tmp)/f'{mutate.__name__}.json';path.write_text(json.dumps(d))
        r=subprocess.run([sys.executable,str(checker),str(modelp),str(path),str(Path(tmp)/f'{mutate.__name__}-check.json')],capture_output=True,text=True)
        assert r.returncode!=0 and 'AssertionError' in r.stderr,(mutate.__name__,r.stderr)
        print(f'{mutate.__name__}: rejected',flush=True)
