"""Fresh-process point search; input contains no target certificate or teacher."""
import gzip,json,resource,sys,time
from pathlib import Path
from first_order_receptors import Model
from semantic_inventory_search import search

def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());start=time.perf_counter()
    model=Model(job['case'],job['compiled']);setup=time.perf_counter()-start
    result=search(model,job['mode'],weights=job['weights'] if job['mode']=='learned' else None,
        seed=job['seed'],attempts=job['limits']['attempts'],seconds=job['limits']['seconds'],
        proposal_limit=job['limits']['proposal_limit'],proposal_checks=job['limits']['proposal_checks'])
    out=dict(mode=job['mode'],repetition=job['repetition'],search=result,model=model.record(),
        setup_seconds=setup,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        worker_report_seconds=time.perf_counter()-began)
    # macOS ru_maxrss is bytes. This research runner is pinned to that host.
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0))

if __name__=='__main__':main()
