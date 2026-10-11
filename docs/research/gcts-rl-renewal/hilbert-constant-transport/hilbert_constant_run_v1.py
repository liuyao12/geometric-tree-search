"""Only two bounded host structural children; never launch a native program."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    plan=json.loads((HERE/'plan-v1.json').read_text());records=[]
    for stage in ['produce','audit']:
        started=time.perf_counter();source=HERE/('hilbert_constant_'+stage+'_v1.py')
        try:
            p=subprocess.run([sys.executable,str(source)],cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
            record=dict(stage=stage,process_wall_seconds=time.perf_counter()-started,exit_code=p.returncode,timeout=False)
            (HERE/(stage+'-stdout-v1.txt')).write_bytes(p.stdout);(HERE/(stage+'-stderr-v1.txt')).write_bytes(p.stderr)
        except subprocess.TimeoutExpired as e:
            record=dict(stage=stage,process_wall_seconds=time.perf_counter()-started,exit_code=None,timeout=True)
            (HERE/(stage+'-stdout-v1.txt')).write_bytes(e.stdout or b'');(HERE/(stage+'-stderr-v1.txt')).write_bytes(e.stderr or b'')
        records.append(record);(HERE/'stage-costs-v1.json').write_text(json.dumps(dict(plan_sha256=hashlib.sha256((HERE/'plan-v1.json').read_bytes()).hexdigest(),stages=records,status='running' if record['exit_code']==0 else 'unknown_or_failed',native_queries=0,point_models=0,target_searches=0),indent=2)+'\n')
        print(json.dumps(record),flush=True)
        if record['exit_code']!=0:return
    data=json.loads((HERE/'stage-costs-v1.json').read_text());data['status']='complete';(HERE/'stage-costs-v1.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
