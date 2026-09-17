"""Selected-search witness corruption controls, independent of the engine."""
import copy,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
coord,support,poolpath,resultpath=sys.argv[1:]
pool=json.loads(Path(poolpath).read_text());result=json.loads(Path(resultpath).read_text())
verifier=Path(__file__).with_name('verify-learned-support-gap-repair.py')
with tempfile.TemporaryDirectory(prefix='gcts-gap-controls-') as tmp:
    complete=result['results'][0]['complete']
    for kind in ['omission','duplicate','reflection']+([] if complete else ['false-completion']):
        pp=copy.deepcopy(pool);rr=copy.deepcopy(result);run=rr['results'][0]
        selected=next(k for k in run['selected'] if k.startswith('proposal:'))
        if kind=='omission':run['selected'].remove(selected)
        elif kind=='duplicate':run['selected'].append(selected)
        elif kind=='false-completion':run['complete']=True;run['status']='complete'
        else:
            row=next(p for p in pp['models'] if p['id']==run['id'])
            row['geometry'][selected]['rotationRow'][0]=[-v for v in row['geometry'][selected]['rotationRow'][0]]
        p=Path(tmp)/f'{kind}-pool.json';p.write_text(json.dumps(pp));rr['poolHash']=hashlib.sha256(p.read_bytes()).hexdigest()
        r=Path(tmp)/f'{kind}-result.json';r.write_text(json.dumps(rr))
        child=subprocess.run([sys.executable,str(verifier),'--search',coord,support,str(p),str(r),str(Path(tmp)/f'{kind}-check.json')],capture_output=True,text=True)
        if kind=='omission' and not complete:
            assert child.returncode==0,child.stderr
            receipt=json.loads((Path(tmp)/f'{kind}-check.json').read_text())
            assert len(receipt['rows'])==len(rr['results']) and not receipt['rows'][0]['complete']
            print('partial omission correctly retained as incomplete, not skipped',flush=True)
        else:
            assert child.returncode!=0 and 'AssertionError' in child.stderr,child.stderr
            print(kind,'rejected',flush=True)
