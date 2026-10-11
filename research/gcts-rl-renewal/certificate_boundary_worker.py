"""One fresh process and full machine reset for a declared assertion/control."""
import gzip,hashlib,json,sys,time
from pathlib import Path
from certificate_boundary_search import Oracle,search,digest
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    started=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());tmp=Path(job['directory']);tmp.mkdir(exist_ok=True,parents=True)
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()));old=json.loads((DOCS/'proof-boundary-001.json').read_text())
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM:raise ValueError('fixed native machine binding')
    (tmp/'code.bin').write_bytes(code_bytes(micro));oracle=Oracle(micro,old['cases'][0]['initial'],job['executable'],tmp/'code.bin',tmp)
    try:result=search(job['case'],oracle,job['mode'],**job['limits']);result['records']=oracle.records
    finally:oracle.close()
    result.update(case=job['case'],repetition=job['repetition'],method_order=job['method_order'],cold_seconds=time.perf_counter()-started)
    Path(sys.argv[2]).write_text(json.dumps(result,separators=(',',':'))+'\n')
if __name__=='__main__':main()
