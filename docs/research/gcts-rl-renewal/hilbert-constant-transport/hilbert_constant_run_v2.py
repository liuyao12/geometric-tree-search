"""Bounded host-only children with external RSS/time watchdog, no native calls."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    plan=json.loads((HERE/'plan-v2.json').read_text());old=plan['resource_only_v2_amendment']['failed_stage']['process_wall_seconds'];records=[];peak_ceiling=512*1024*1024
    for stage in ['produce','audit']:
        started=time.perf_counter();limit=180-old if stage=='produce' else 180;source=HERE/('hilbert_constant_'+stage+'_v2.py');watch=[];reason=None
        with (HERE/(stage+'-stdout-v2.txt')).open('wb') as stdout,(HERE/(stage+'-stderr-v2.txt')).open('wb') as stderr:
            child=subprocess.Popen([sys.executable,str(source)],cwd=HERE,stdout=stdout,stderr=stderr)
            while child.poll() is None:
                elapsed=time.perf_counter()-started
                if elapsed>limit:reason='wall_ceiling';child.kill();break
                sample=subprocess.run(['ps','-o','rss=','-p',str(child.pid)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=2)
                text=sample.stdout.strip()
                if sample.returncode==0 and text:
                    resident=int(text)*1024;watch.append(dict(elapsed_seconds=elapsed,rss_bytes=resident))
                    if resident>peak_ceiling:reason='RSS_ceiling';child.kill();break
                time.sleep(.05)
            child.wait()
        result_path=HERE/('production-v2.json' if stage=='produce' else 'audit-v2.json');result=json.loads(result_path.read_text()) if result_path.exists() else None
        kernel_peak=result.get('peak_rss_bytes') if result else None
        if kernel_peak is not None and kernel_peak>peak_ceiling:reason='final_kernel_peak_ceiling'
        record=dict(stage=stage,process_wall_seconds=time.perf_counter()-started,exit_code=child.returncode,wall_ceiling_seconds=limit,
            resource_unknown_reason=reason,watchdog_period_seconds=.05,rss_samples=watch,kernel_peak_rss_bytes=kernel_peak,peak_ceiling_bytes=peak_ceiling,
            process_pid=child.pid,os_limits=result.get('os_limits') if result else None)
        records.append(record);data=dict(plan_sha256=hashlib.sha256((HERE/'plan-v2.json').read_bytes()).hexdigest(),stages=records,
            failed_v1_production_process_seconds=old,production_total_process_seconds=old+records[0]['process_wall_seconds'],status='running' if child.returncode==0 and reason is None else 'unknown_or_failed',native_queries=0,point_models=0,target_searches=0)
        (HERE/'stage-costs-v2.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='rss_samples'}),flush=True)
        if child.returncode!=0 or reason is not None:return
    data['status']='complete';(HERE/'stage-costs-v2.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
