"""Cold finite geometry searches. Reads no proof witnesses or learned library."""
import hashlib,json,time
from pathlib import Path
import euclidean_proof_tiles as E
import induction_proof_tiles as T,induction_clusters as H
from serialized_kernel import canonical,problem_hash
from audit_serialized_kernel import replay
from tree_kernel import program
import tree_native
from run_induction_clusters import SOURCES as BASE
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-euclidean-proof-native-001')
SOURCES=BASE+('euclidean_proof_tiles.py','run_euclidean_proofs.py','audit_euclidean_proofs.py','test_euclidean_proofs.py')
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);compile_seconds=tree_native.compile_tool(TMP);code=program();runs=[]
    cases=[('I.5',10,()),('I.6',10,()),('triangle-order',3,()),('I.5-no-SAS',10,('SAS',)),('I.6-no-ASA',10,('ASA',)),('I.5-short',9,())]
    for name,n,omit in cases:
        base='I.5' if name.startswith('I.5') else 'I.6' if name.startswith('I.6') else name
        p=E.problem(base);c=E.catalog(p,omit)
        for lane in ('gcts','csp'):
            r=T.search(c,n,support=True,seconds=3,attempt_limit=5000) if lane=='gcts' else H.csp_search(c,n,(),marked=True,seconds=3,attempt_limit=5000)
            row=dict(id=name,lane=lane,length=n,problem=p,catalog=c,result=r)
            if 'decoded' in r:
                request=r['decoded']['request'];native=tree_native.check(canonical(request),code,TMP,problem_hash(request),steps=100000000)
                if native['status']!='accepted':raise ValueError(native)
                primitive=replay(canonical(request))
                if primitive['status']!='accepted':raise ValueError(primitive)
                row['native']=native;row['primitive_proof']=primitive['proof'];row['primitive_lines']=primitive['expanded_lines']
            runs.append(row);print(name,lane,r['status'],r['nodes'],round(r['seconds'],4),flush=True)
    data=dict(version='euclidean-proofs-001',date='2026-10-09',protocol='cold finite geometry pilot; no proof input, no imported library, no RL',sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},runs=runs,compile_seconds=compile_seconds,total_seconds=time.perf_counter()-began,limits=dict(seconds_per_lane=3,attempts=5000),scope='same finite point inventory, rule grammar and certified resource marks in each matched pair; one cold trial per lane, not a statistical performance benchmark')
    (DOCS/'euclidean-proofs-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
if __name__=='__main__':main()
