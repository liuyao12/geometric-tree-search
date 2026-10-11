"""Fresh isolated point search, with native-admitted rules only."""
import gzip,json,resource,sys,time
from pathlib import Path
from catalog_receptor_points import Model
from catalog_receptor_search import search
def main():
    started=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());m=Model(job['case'],job['compiled'],job['inventory'],arity=2,families=True)
    setup=time.perf_counter()-started;r=search(m,job['mode'],weights=job['weights'] if job['mode']=='learned' else None,seed=job['seed'],feature_semantics=job['feature_semantics'],**job['limits'])
    result=dict(search=r,model=m.record(),setup_seconds=setup,worker_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':main()
