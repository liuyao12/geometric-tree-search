"""One cold request over the unchanged full native inventory."""
import gzip,hashlib,json,resource,sys,time
from pathlib import Path
from native_wang_search import Oracle,Universe,search
from native_wang_cases import projection_certificate
from serialized_kernel import canonical
from check_native_rectangle import Primitive

def main():
    began=time.perf_counter();spec_path,out_path,exe,table,lane=map(str,sys.argv[1:]);spec=json.loads(Path(spec_path).read_text());raw=Path(table).read_bytes();o=Oracle(raw,exe,table);u=Universe(o)
    boundary=spec['boundary'][:];certificate=None
    if lane=='projected':certificate=projection_certificate(spec,o.inventory);boundary.extend(certificate['pins'])
    prepared=time.perf_counter()-began
    result=search(u,spec['pattern'],spec['height'],boundary,extended=lane=='neighbors',projected=lane=='projected',attempts=spec.get('attempts',2000),seconds=60)
    before=time.perf_counter();checker=Primitive(raw);result['point_checks']={name:checker.check(spec,result,decorated) for name,decorated in (('original',False),('decorated',True))};result['verification_seconds']=time.perf_counter()-before
    o.close();total=time.perf_counter()-began
    result.update(preparation_seconds=prepared,total_seconds=total,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    semantic={k:v for k,v in result.items() if k not in ('seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes')}
    row=dict(spec=spec,lane=lane,result=result,certificate=certificate,inventory=dict(fingerprint=o.inventory.fingerprint,tile_types=u.inventory_count,A=o.inventory.A,Q=o.inventory.Q,D=o.inventory.D),
        domain_queries=o.queries,oracle_metrics=dict(o.metrics),domain_metrics=dict(u.metrics),semantic_sha256=hashlib.sha256(canonical(semantic)).hexdigest())
    Path(out_path).write_bytes(gzip.compress(canonical(row)+b'\n',mtime=0));print(json.dumps(dict(case=spec['id'],lane=lane,status=result['status'],attempts=result['attempts'],cold_seconds=total)),flush=True)

if __name__=='__main__':main()
