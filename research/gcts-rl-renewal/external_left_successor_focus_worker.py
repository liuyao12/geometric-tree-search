"""One independently accounted focused certificate operation."""
import json,os,pathlib,platform,resource,sys,threading,time,traceback

def main():
    began=time.perf_counter();request=json.loads(pathlib.Path(sys.argv[1]).read_text())
    resource.setrlimit(resource.RLIMIT_CPU,(request['cpu_limit'],request['cpu_limit']+1))
    def supervise():
        while True:
            usage=resource.getrusage(resource.RUSAGE_SELF)
            rss=usage.ru_maxrss if platform.system()=='Darwin' else usage.ru_maxrss*1024
            if rss>1073741824:
                pathlib.Path(sys.argv[2]).write_text(json.dumps(dict(status='unknown',result=dict(status='unknown',error='one-GiB sampled self-RSS cutoff'),peak_rss_bytes=rss,operation_seconds=time.perf_counter()-began))+'\n');os._exit(3)
            time.sleep(.025)
    threading.Thread(target=supervise,daemon=True).start()
    from external_prover_check import native_formula
    from external_left_successor_focus import check_output,consequence,replay_consequence
    try:
        op=request['operation']
        if op in ('interface','interface-replay'):
            parents=[native_formula(f,request['mapping']) for f in request['parents']]
            child=native_formula(request['child'],request['mapping'])
            if op=='interface':result=consequence(parents,child)
            else:replay_consequence(parents,child,request['saved']);result=dict(status='replayed_complete_interface_certificate')
        elif op in ('proof','proof-replay'):
            result=check_output(request['output'],request['mapping'],request['input_path'],saved=request.get('saved') if op=='proof-replay' else None)
        else:raise ValueError('unknown focused operation')
        status='complete'
    except Exception as error:
        status='unknown';result=dict(status='unknown',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc(limit=5))
    usage=resource.getrusage(resource.RUSAGE_SELF)
    rss=usage.ru_maxrss if platform.system()=='Darwin' else usage.ru_maxrss*1024
    pathlib.Path(sys.argv[2]).write_text(json.dumps(dict(status=status,result=result,operation_seconds=time.perf_counter()-began,user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,peak_rss_bytes=rss),indent=2)+'\n')
    if status!='complete':sys.exit(2)

if __name__=='__main__':main()
