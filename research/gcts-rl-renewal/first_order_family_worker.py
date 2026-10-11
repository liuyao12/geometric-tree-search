"""Isolated search with statements, admitted inventories and policy only."""
import gzip,json,resource,sys,time
from pathlib import Path
from first_order_family_points import Model
from semantic_inventory_search import search

def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());stage=time.perf_counter()
    model=Model(job['case'],job['compiled'],job['inventory'],job['arity'],job['families']);setup=time.perf_counter()-stage
    result=search(model,job['mode'],weights=job['weights'] if job['mode'] in ('learned','no-family') else None,
                  stochastic=job.get('stochastic',False),seed=job['seed'],**job['limits'])
    data=dict(search=result,model=model.record(),setup_seconds=setup,worker_report_seconds=time.perf_counter()-began,
              peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))

if __name__=='__main__':main()
