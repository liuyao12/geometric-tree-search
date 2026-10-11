"""One fresh process for each complete point search or chronological control."""
import gzip,hashlib,json,sys,time
from pathlib import Path
from certificate_boundary_search import Oracle,canonical,digest,search as chronological
from native_receptor_points import compile_guards,Model,search
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());spec=job['case'];directory=Path(job['directory']);directory.mkdir(parents=True,exist_ok=True)
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));old=json.loads((DOC/'proof-boundary-001.json').read_text())
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM:raise ValueError('unchanged checker')
    (directory/'code.bin').write_bytes(code_bytes(micro));oracle=Oracle(micro,old['cases'][0]['initial'],job['executable'],directory/'code.bin',directory)
    try:
        if job['mode']=='points':
            compiled=compile_guards(spec,oracle,micro_steps=spec.get('micro_steps',10**9))
            if compiled['status']!='complete':result=dict(status=compiled['status'],proof=None,compiled=compiled,model=None,search=None)
            else:
                model=Model(spec,compiled);out=search(model,attempts=spec.get('attempts',10000));result=dict(status=out['status'],proof=out['proof'],compiled=compiled,model=model.record(),search=out)
                if out['proof']:
                    record=oracle.query(spec,out['proof'],True,spec.get('micro_steps',10**9));record['purpose']='searched_certificate_without_point_markings';result['verification_query']=record['id']
                    if record['result']['status']=='accepted':result['status']='native_proof_discovered'
                    elif record['result']['status']=='rejected':raise ValueError('marked model generated an invalid certificate')
                    else:result['status']='unknown_native_verification'
        elif job['mode']=='prefix':
            out=chronological(spec,oracle,'prefix',queries=128,seconds=120,micro_steps=spec.get('micro_steps',10**9));result=dict(status=out['status'],proof=out['found']['proof'] if out['found'] else None,chronological=out)
            if out['found']:result['verification_query']=out['found']['query']
            for r in oracle.records:r['purpose']='chronological_query'
        else:raise ValueError('mode')
        # Save original boundary words, so wire-object ordering is not inferred
        # from a later canonical JSON rendering of the artifact.
        for r in oracle.records:
            fixed,free=boundary_words(r['request']);r['boundary_words']=dict(fixed=fixed,free=free)
        result.update(case=spec,mode=job['mode'],records=oracle.records,queries=len(oracle.records))
    finally:
        oracle.close()
        for stream in (oracle.process.stdin,oracle.process.stdout,oracle.process.stderr):stream.close()
    result['cold_seconds']=time.perf_counter()-began;Path(sys.argv[2]).write_text(json.dumps(result,separators=(',',':'))+'\n');print(spec['id'],job['mode'],result['status'],result['queries'],round(result['cold_seconds'],3),flush=True)
if __name__=='__main__':main()
