"""Rehashed corruptions must fail cohort membership or coordinate replay."""
import copy,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
manifestp,targetp=map(Path,sys.argv[1:]);manifest=json.loads(manifestp.read_text());target=json.loads(targetp.read_text())
verify=Path(__file__).with_name('verify-frozen-frame-cohort.py')
with tempfile.TemporaryDirectory(prefix='gcts-cohort-controls-') as tmp:
    for kind in ['changed-coordinate','repeated-frame','wrong-source-index']:
        m=copy.deepcopy(manifest);t=copy.deepcopy(target)
        if kind=='changed-coordinate':t['configurations'][0]['positions'][0][0]+=.01
        elif kind=='repeated-frame':t['configurations'][0]=copy.deepcopy(t['configurations'][1]);m['targets'][0]=copy.deepcopy(m['targets'][1])
        else:m['targets'][0]['sourceFrame']=49
        p=Path(tmp)/'targets.json';p.write_text(json.dumps(t));m['targetHash']=hashlib.sha256(p.read_bytes()).hexdigest()
        mp=Path(tmp)/'manifest.json';mp.write_text(json.dumps(m))
        child=subprocess.run([sys.executable,str(verify),str(mp),str(p),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        assert child.returncode!=0 and 'AssertionError' in child.stderr,child.stderr
        print(kind,'rejected',flush=True)
