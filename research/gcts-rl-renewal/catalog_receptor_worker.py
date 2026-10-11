"""Fresh-process representation study. Only assertions and frozen inputs enter."""
import gzip,json,resource,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from first_order_family_points import Model as WordModel
from catalog_receptor_points import Model as CompactModel
from catalog_receptor_search import search

def main():
    started=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text())
    m=(WordModel if job['representation']=='word' else CompactModel)(job['case'],job['compiled'],job['inventory'],arity=3,families=True)
    setup=time.perf_counter()-started
    r=search(m,job['mode'],weights=job['weights'] if job['mode']=='learned' else None,seed=job['seed'],feature_semantics=job['feature_semantics'],**job['limits'])
    stage=time.perf_counter();record=m.record();identity=digest({k:v for k,v in record.items() if k!='compile_seconds'})
    model_stats=dict(placements=len(m.cache),mark_assignments=sum(len(t.marks) for t in m.cache.values()),dependency_points=len(m.dependencies),model_sha256=identity)
    if job.get('save_model'):
        Path(job['save_model']).write_bytes(gzip.compress(json.dumps(record,separators=(',',':')).encode(),mtime=0))
    result=dict(search=r,setup_seconds=setup,model_stats=model_stats,model_reporting_seconds=time.perf_counter()-stage,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0))

if __name__=='__main__':main()
