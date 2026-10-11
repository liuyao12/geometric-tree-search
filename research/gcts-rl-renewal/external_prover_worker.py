"""One external command per fresh measurement process; per-child rusage."""
import json,platform,resource,subprocess,sys,time

def main():
    request=json.load(sys.stdin);before=resource.getrusage(resource.RUSAGE_CHILDREN);began=time.perf_counter()
    p=subprocess.Popen(request['command'],cwd=request.get('cwd'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    timedout=False
    try:stdout,stderr=p.communicate(timeout=request['timeout'])
    except subprocess.TimeoutExpired:
        timedout=True;p.kill();stdout,stderr=p.communicate()
    wall=time.perf_counter()-began;after=resource.getrusage(resource.RUSAGE_CHILDREN)
    scale=1 if sys.platform=='darwin' else 1024
    json.dump(dict(returncode=p.returncode,wall_seconds=wall,timed_out=timedout,
                   stdout=stdout.decode('utf8'),stderr=stderr.decode('utf8'),
                   user_seconds=after.ru_utime-before.ru_utime,system_seconds=after.ru_stime-before.ru_stime,
                   peak_rss_bytes=int(after.ru_maxrss*scale),rusage_rss_raw=after.ru_maxrss,
                   rusage_rss_units='bytes' if scale==1 else 'KiB',platform=platform.platform()),sys.stdout)

if __name__=='__main__':main()
