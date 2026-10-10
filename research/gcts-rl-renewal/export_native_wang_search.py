"""Digest-bound primary native leaves and literal table rows for the reader."""
import gzip,hashlib,json,struct
from pathlib import Path
from check_native_rectangle import Primitive
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def project(data,audit):
    raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());p=Primitive(raw)
    cases=[];states=set()
    for c in data['cases']:
        runs={}
        for lane in data['lanes']:
            ref=next(r for r in c['runs'] if r['lane']==lane and r['repetition']==0);path=DOC/ref['file']
            if sha(path)!=ref['sha256']:raise ValueError('raw primary digest')
            row=json.loads(gzip.decompress(path.read_bytes()));r=row['result']
            fields=('status','attempts','forced','branches','backtracks','width','height','extended','projected','boundary','tiles','tile_generations','initial_census','initial_candidate_nodes','point_checks','root_rollback_verified','limits','seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes')
            runs[lane]={k:r[k] for k in fields};runs[lane].update(certificate=row['certificate'],raw=ref,first_event=r['events'][0] if r['events'] else None,selector_queries=len(row['domain_queries']))
            for tile in r['tiles']:
                states.update((v-p.A)//p.A for v in tile['triple'] if v>=p.A)
        cases.append(dict(spec=c['spec'],runs=runs,timings=c['timings']))
    rows=[]
    for q in sorted(states):
        offset=p.offsets[q];fallback,direction,_,_,n=struct.unpack_from('<5I',raw,offset)
        actions=[list(struct.unpack_from('<5I',raw,offset+20+20*j)[:4]) for j in range(n)]
        rows.append(dict(q=q,fallback=fallback,direction=direction,actions=actions))
    labels=json.loads((DOC/'shared-wang-reader-001.json').read_text())['inventory']['alphabet']
    return dict(version='native-wang-search-reader-001',input_sha256=sha(DOC/'native-wang-search-001.json'),audit=audit,cases=cases,lanes=data['lanes'],repetitions=data['repetitions'],inventory=dict(A=p.A,Q=p.Q,D=p.D,start=p.start,accept=p.accept,reject=p.reject,space=p.space,defined=17899987,tile_types=data['tile_types'],fingerprint=data['inventory_fingerprint'],literal_table_sha256=data['literal_table_sha256'],alphabet=labels,rows=rows),compile_seconds=data['compile_seconds'],seconds=data['seconds'],timing_scope=data['timing_scope'],scope=data['scope'],projection_scope='Every displayed tile and partial state is copied from a digest-bound primary observation. Literal transitions for all heads in those leaves are copied from the pinned raw table. The browser checks original/decorated point agreement and clock summaries; the separate raw-table audit replays all 54 complete trees and counted domains.')
def main():
    data=json.loads((DOC/'native-wang-search-001.json').read_text());audit=json.loads((DOC/'native-wang-search-audit-001.json').read_text())
    if audit['status']!='passed' or audit['input_sha256']!=sha(DOC/'native-wang-search-001.json'):raise ValueError('passed audit binding')
    (DOC/'native-wang-search-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
