"""One fresh process: cold fixed palette, optional family join, point checks."""
import gzip,hashlib,json,resource,sys,time
from pathlib import Path
from native_wang_search import Oracle,Universe
from native_wang_cases import projection_certificate
from native_family_search import search
from check_native_family_points import check
from serialized_kernel import canonical
def main():
    began=time.perf_counter();input_path,out_path,exe,table=map(str,sys.argv[1:]);payload=json.loads(Path(input_path).read_text());spec=payload['spec'];raw=Path(table).read_bytes();oracle=Oracle(raw,exe,table);universe=Universe(oracle);cert=projection_certificate(spec,oracle.inventory);boundary=spec['boundary']+cert['pins'];prepared=time.perf_counter()-began
    r=search(universe,spec['pattern'],spec['height'],boundary,payload['library'],payload['mode'],payload['weights'],payload['stochastic'],payload['seed'],spec.get('attempts',350),60)
    before=time.perf_counter();r['point_checks'],r['cluster_checks']=check(raw,spec,r);r['verification_seconds']=time.perf_counter()-before;oracle.close();r.update(preparation_seconds=prepared,total_seconds=time.perf_counter()-began,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    semantic={k:v for k,v in r.items() if k not in ('seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes','metrics')};semantic['metrics']={k:v for k,v in r['metrics'].items() if k!='proposal_seconds'}
    row=dict(spec=spec,result=r,certificate=cert,library_sha256=hashlib.sha256(canonical(payload['library'])).hexdigest(),domain_queries=oracle.queries,oracle_metrics=dict(oracle.metrics),semantic_sha256=hashlib.sha256(canonical(semantic)).hexdigest())
    Path(out_path).write_bytes(gzip.compress(canonical(row)+b'\n',mtime=0));print(json.dumps(dict(case=spec['id'],mode=r['mode'],status=r['status'],attempts=r['attempts'],hints=len(r['hints']),actions=len(r['policy_events']),cold_seconds=r['total_seconds'])),flush=True)
if __name__=='__main__':main()
