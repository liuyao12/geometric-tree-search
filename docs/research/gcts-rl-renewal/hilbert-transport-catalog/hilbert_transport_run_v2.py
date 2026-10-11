"""Separately bounded host recovery; fail-closed owned-child RSS/time monitor."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
CEILING=512*1024*1024
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def run(stage):
    started=time.perf_counter();watch=[];reason=None;error=None;child=None;terminal=None;result=None
    source=HERE/('hilbert_transport_corruption_repair_v2.py' if stage=='produce' else 'hilbert_transport_audit_v2.py');prior=json.loads((HERE/'stage-costs-v1.json').read_text())['stages'][0 if stage=='produce' else 1]['process_wall_seconds'];limit=180-prior
    stdout_path=HERE/(stage+'-stdout-v2.txt');stderr_path=HERE/(stage+'-stderr-v2.txt')
    try:
        with stdout_path.open('wb') as stdout,stderr_path.open('wb') as stderr:
            child=subprocess.Popen([sys.executable,str(source)],cwd=HERE,stdout=stdout,stderr=stderr)
            save(HERE/(stage+'-launch-v2.json'),dict(stage=stage,pid=child.pid,wall_ceiling_seconds=limit,host_ceiling_bytes=CEILING,scope='owned structural host child only'))
            try:
                while child.poll() is None:
                    elapsed=time.perf_counter()-started
                    if elapsed>limit:reason='wall_ceiling';break
                    sample=subprocess.run(['ps','-o','rss=','-p',str(child.pid)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=2,check=False)
                    text=sample.stdout.strip()
                    if sample.returncode==0 and text:
                        resident=int(text)*1024
                        if resident<0:raise ValueError('invalid negative RSS')
                        watch.append(dict(elapsed_seconds=elapsed,rss_bytes=resident))
                        if resident>CEILING:reason='RSS_ceiling';break
                    elif child.poll() is None:
                        raise RuntimeError('process metadata unavailable: '+str(sample.returncode)+' '+sample.stderr.decode(errors='replace'))
                    time.sleep(.05)
            except BaseException as e:
                reason='watchdog_failure';error=type(e).__name__+': '+str(e)
            finally:
                if reason is not None and child.poll() is None:child.kill()
                terminal=child.wait()
    except BaseException as e:
        reason=reason or 'supervisory_failure';error=error or type(e).__name__+': '+str(e)
        if child is not None:
            if child.poll() is None:child.kill()
            terminal=child.wait()
    elapsed=time.perf_counter()-started
    result_path=HERE/('production-v2.json' if stage=='produce' else 'audit-v2.json')
    try:result=json.loads(result_path.read_text()) if result_path.exists() else None
    except BaseException as e:reason=reason or 'invalid_child_result';error=error or type(e).__name__+': '+str(e)
    kernel_peak=result.get('peak_rss_bytes') if result else None
    if elapsed>limit:reason=reason or 'final_wall_ceiling'
    if type(kernel_peak) is not int or kernel_peak<0:reason=reason or 'missing_or_invalid_final_kernel_peak'
    elif kernel_peak>CEILING:reason=reason or 'final_kernel_peak_ceiling'
    if not watch:reason=reason or 'no_external_RSS_samples'
    return dict(stage=stage,process_wall_seconds=elapsed,exit_code=terminal,wall_ceiling_seconds=limit,resource_unknown_reason=reason,
        watchdog_error=error,watchdog_period_seconds=.05,rss_samples=watch,kernel_peak_rss_bytes=kernel_peak,peak_ceiling_bytes=CEILING,
        process_pid=child.pid if child else None,child_wait_reaped=child is not None and terminal is not None,os_limits=result.get('os_limits') if result else None)
def main():
    path=HERE/'plan-v2.json';plan=json.loads(path.read_text());records=[]
    if (HERE/'stage-costs-v2.json').exists():raise ValueError('immutable prior catalog stage evidence')
    for stage in ['produce','audit']:
        record=run(stage);records.append(record)
        data=dict(plan_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),stages=records,
            original_catalog_production_seconds=plan['original_catalog_production_seconds'],failed_audit_process_seconds=plan['failed_audit_process_seconds'],original_failed_audit_kernel_peak='unavailable',
            repair_production_process_seconds=records[0]['process_wall_seconds'],repair_audit_process_seconds=records[1]['process_wall_seconds'] if len(records)>1 else None,charged_production_process_seconds=plan['original_catalog_production_seconds']+records[0]['process_wall_seconds'],charged_audit_process_seconds=plan['failed_audit_process_seconds']+records[1]['process_wall_seconds'] if len(records)>1 else None,
            original_structural_cumulative_production_gate='not_established',scope='versioned wire-corruption repair; actual old wall costs deducted; old failed kernel gate not established',
            status='running' if record['exit_code']==0 and record['resource_unknown_reason'] is None else 'unknown_or_failed',native_queries=0,point_catalogs=1,target_searches=0,existing_native_engine_activation=False)
        save(HERE/'stage-costs-v2.json',data);print(json.dumps({k:v for k,v in record.items() if k!='rss_samples'}),flush=True)
        if data['status']=='unknown_or_failed':return
    data['status']='complete';save(HERE/'stage-costs-v2.json',data)
if __name__=='__main__':main()
