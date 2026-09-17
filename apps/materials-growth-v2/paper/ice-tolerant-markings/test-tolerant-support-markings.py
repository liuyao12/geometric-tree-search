"""Corruption and common-interval controls for tolerant markings."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
coord,dictionary,library,support,mark=sys.argv[1:]
base=json.loads(Path(mark).read_text());data=json.loads(Path(support).read_text())
verifier=Path(__file__).with_name('verify-tolerant-support-markings.py')
index=next(i for i,a in enumerate(data['anchors']) if a['t']==.5)
with tempfile.TemporaryDirectory(prefix='gcts-tolerant-controls-') as tmp:
    for kind in ['disagreement','radius','wrong-support']:
        mutated=copy.deepcopy(base)
        if kind=='disagreement':mutated['runs'][0]['values'][index][0]+=100
        elif kind=='radius':mutated['radius']=10
        else:mutated['sourceHashes'][Path(support).name]='0'*64
        path=Path(tmp)/f'{kind}.json';path.write_text(json.dumps(mutated))
        run=subprocess.run([sys.executable,str(verifier),coord,dictionary,library,support,str(path),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        assert run.returncode!=0 and 'AssertionError' in run.stderr,run.stderr
        print(kind,'rejected',flush=True)
# Adjacent intervals overlap along a chain, but all three have no common value.
intervals=[(-.5,.5),(.5,1.5),(1.5,2.5)]
assert all(max(a[0],b[0])<=min(a[1],b[1]) for a,b in zip(intervals,intervals[1:]))
assert max(a for a,b in intervals)>min(b for a,b in intervals)
print('Chain agreement is not common-value agreement: passed')
