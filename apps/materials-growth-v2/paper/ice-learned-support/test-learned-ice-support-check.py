"""Corruption controls for independent learned-support replay."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
coord,dictionary,library,result=sys.argv[1:]
verifier=Path(__file__).with_name('verify-learned-ice-point-support.py')
base=json.loads(Path(result).read_text())
with tempfile.TemporaryDirectory(prefix='gcts-support-controls-') as tmp:
    for kind in ['position','weight','unused-correspondences']:
        data=copy.deepcopy(base)
        if kind=='position':data['anchors'][0]['position'][0]+=1
        elif kind=='weight':data['anchors'][0]['t']*=.9
        else:
            for anchor in data['anchors']:anchor['observations']=[]
        path=Path(tmp)/f'{kind}.json';path.write_text(json.dumps(data))
        run=subprocess.run([sys.executable,str(verifier),coord,dictionary,library,str(path),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        if kind=='unused-correspondences':assert run.returncode==0,run.stderr
        else:assert run.returncode!=0 and 'AssertionError' in run.stderr,run.stderr
        print(kind, 'passed',flush=True)
