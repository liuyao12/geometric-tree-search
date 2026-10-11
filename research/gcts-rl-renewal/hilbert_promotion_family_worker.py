"""Fresh isolated complete point model; no host proof oracle or binding sampler."""
import gzip,json,resource,sys,time
from pathlib import Path
from catalog_receptor_points import Model
from catalog_receptor_search import search
def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text())
    model=Model(job['case'],job['compiled'],job['inventory'],arity=2,families=True);setup=time.perf_counter()-began
    result=search(model,job['mode'],weights=job['weights'] if job['mode']=='learned' else None,
                  seed=job['seed'],feature_semantics=job['feature_semantics'],**job['limits'])
    output=dict(search=result,model=model.record(),setup_seconds=setup,worker_seconds=time.perf_counter()-began,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(output,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':main()
