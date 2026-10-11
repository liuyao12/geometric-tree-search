"""Outer full lifetime gate, including worker and supervisor receipt serialization."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def peak(kind):
    return resource.getrusage(kind).ru_maxrss * (1 if sys.platform=='darwin' else 1024)


def main():
    start=time.perf_counter(); path=HERE/'fixtures-lifetime-v1.json'
    if path.exists(): raise ValueError('immutable outer lifetime exists')
    planpath=HERE/'plan-v1.json'; plan=json.loads(planpath.read_text())
    for p in plan['sources']+plan['inputs']+plan['preserved_files']:
        source=ROOT/p['path']; h=hashlib.sha256()
        with source.open('rb') as stream:
            for block in iter(lambda:stream.read(65536),b''): h.update(block)
        if source.stat().st_size!=p['bytes'] or h.hexdigest()!=p['sha256']:
            raise ValueError('frozen pin mismatch: '+p['path'])
    child=subprocess.run([sys.executable,str(HERE/'hilbert_cluster_run_v1.py')],check=False)
    wall=time.perf_counter()-start
    innerpath=HERE/'fixtures-supervision-v1.json'
    inner=json.loads(innerpath.read_text()) if innerpath.exists() else None
    own,children=peak(resource.RUSAGE_SELF),peak(resource.RUSAGE_CHILDREN)
    conservative=own+max(children,inner['conservative_host_peak_bytes'] if inner else 0)
    passed=(child.returncode==0 and inner is not None and inner['status']=='passed_bounded_authored_tiny_lifecycle'
            and wall<=60 and conservative<=536870912)
    receipt={'status':'passed_authored_tiny_lifecycle_full_lifetime' if passed else 'unknown_or_failed',
             'full_supervisor_process_seconds_including_receipt_write':wall,'process_return_code':child.returncode,
             'supervisor_wait_reaped':True,'outer_own_peak_bytes':own,'outer_children_kernel_peak_bytes':children,
             'conservative_host_peak_bytes':conservative,'host_ceiling_bytes':536870912,'wall_ceiling_seconds':60,
             'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),
             'supervision_sha256':hashlib.sha256(innerpath.read_bytes()).hexdigest() if inner else None,
             'own_receipt_serialization':'outside pre-write measurement; all worker/supervisor serialization included',
             'actual_geometry_model_execution':False,'geometry_target_searches':0,'native_queries':0,
             'native_authority_activated':False,'independent_lifecycle_audit':'pending'}
    path.write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps(receipt),flush=True)
    return 0 if passed else 1

if __name__=='__main__': sys.exit(main())
