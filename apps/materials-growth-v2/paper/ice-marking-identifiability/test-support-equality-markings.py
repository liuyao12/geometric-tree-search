"""Reject split/merged classes and fabricated equality evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
coord,dictionary,library,support,mark=sys.argv[1:]
base=json.loads(Path(mark).read_text());verifier=Path(__file__).with_name('verify-support-equality-markings.py')
with tempfile.TemporaryDirectory(prefix='gcts-marking-controls-') as tmp:
    for kind in ['split','merge','missing-edge']:
        data=copy.deepcopy(base)
        if kind=='split':data['values'][data['observedEqualityEdges'][0][0]]=max(data['values'])+1
        elif kind=='merge':data['values']=[0]*len(data['values'])
        else:data['observedEqualityEdges'].pop()
        p=Path(tmp)/f'{kind}.json';p.write_text(json.dumps(data))
        run=subprocess.run([sys.executable,str(verifier),coord,dictionary,library,support,str(p),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        assert run.returncode!=0 and 'AssertionError' in run.stderr,run.stderr
        print(kind,'rejected',flush=True)
