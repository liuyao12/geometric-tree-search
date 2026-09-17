"""Validate frozen-support pose registration and reject corrupt proposals."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
coord,dictionary,library,support,poses=sys.argv[1:]
base=json.loads(Path(poses).read_text());dd={r['id']:r for r in json.loads(Path(dictionary).read_text())['configurations']}
changed=0
for p in base['poses']:
    if p['status']=='unchanged-valid':
        old=dd[p['configuration']]['occurrences'][p['edge']]
        assert p['rotationRow']==old['rotationRow'] and p['translation']==old['translation']
    changed+=p['status']=='locally-recovered'
verifier=Path(__file__).with_name('verify-learned-ice-point-support.py')
with tempfile.TemporaryDirectory(prefix='gcts-pose-controls-') as tmp:
    for kind in ['reflection','type','missing-pose']:
        data=copy.deepcopy(base)
        i=next(i for i,p in enumerate(data['poses']) if p['status']=='unchanged-valid')
        if kind=='reflection':data['poses'][i]['rotationRow'][0]=[-v for v in data['poses'][i]['rotationRow'][0]]
        elif kind=='type':data['poses'][i]['type']=-1
        else:data['poses'].pop()
        path=Path(tmp)/f'{kind}.json';path.write_text(json.dumps(data))
        run=subprocess.run([sys.executable,str(verifier),coord,dictionary,library,support,str(Path(tmp)/f'{kind}-check.json'),str(path)],capture_output=True,text=True)
        assert run.returncode!=0 and 'AssertionError' in run.stderr,run.stderr
        print(kind,'rejected',flush=True)
print(f'Previously valid poses unchanged; {changed} local pose recoveries recorded')
