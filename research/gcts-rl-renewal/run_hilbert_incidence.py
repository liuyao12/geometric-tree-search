"""Cold Hilbert incidence searches; reads syntax and code, never proofs."""
import hashlib,json,time
from pathlib import Path
import hilbert_incidence_tiles as B
import induction_proof_tiles as T,induction_clusters as H
import audit_hilbert_incidence as A
from audit_serialized_kernel import replay
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
from run_induction_clusters import SOURCES as BASE
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-hilbert-incidence-native-001')
SOURCES=BASE+('euclidean_proof_tiles.py','hilbert_incidence_tiles.py','audit_hilbert_incidence.py','test_hilbert_incidence.py','run_hilbert_incidence.py')
CASES=[('intersection-unique','intersection-unique',2,()),('incidence-transfer','incidence-transfer',4,()),('intersection-no-I2','intersection-unique',2,('I.2-uniqueness',)),('transfer-no-I2','incidence-transfer',4,('I.2-uniqueness',)),('intersection-short','intersection-unique',1,()),('transfer-short','incidence-transfer',3,()),('wrong-intersection','wrong-intersection',2,())]
def main():
    began=time.perf_counter();pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES};TMP.mkdir(exist_ok=True)
    compile_seconds=tree_native.compile_tool(TMP);code=program();runs=[];problems={}
    for name,base,n,omit in CASES:
        for lane in ('gcts','csp'):
            cold=time.perf_counter();p=B.problem(base);problems[base]=p;c=B.catalog(p,omit)
            r=T.search(c,n,support=True,seconds=3,attempt_limit=5000) if lane=='gcts' else H.csp_search(c,n,(),marked=True,seconds=3,attempt_limit=5000)
            row=dict(id=name,lane=lane,length=n,problem=p,catalog=c,result=r)
            row['catalog_and_search_seconds']=time.perf_counter()-cold
            if 'decoded' in r:
                request=r['decoded']['request'];native=tree_native.check(canonical(request),code,TMP,problem_hash(dict(protocol='gcts-fol-1',theory=c['theory'],target=p['target'])),steps=1000000000)
                if native['status']!='accepted':raise ValueError(native)
                primitive=replay(canonical(request))
                if primitive['status']!='accepted':raise ValueError(primitive)
                row.update(native=native,primitive_proof=primitive['proof'],primitive_lines=primitive['expanded_lines'])
            row['cold_seconds']=time.perf_counter()-cold;runs.append(row)
            print(name,lane,r['status'],r['nodes'],r['base_attempts'],round(row['cold_seconds'],4),flush=True)
            (TMP/'progress.json').write_text(json.dumps(dict(runs=runs),separators=(',',':'))+'\n')
    models=A.model_controls(B.foundation()[0],problems)
    if any(hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pin for n,pin in pins.items()):raise ValueError('source changed during measured run')
    data=dict(version='hilbert-incidence-001',date='2026-10-10',sources=pins,native_program=code,runs=runs,model_controls=models,compile_seconds=compile_seconds,total_seconds=time.perf_counter()-began,limits=dict(seconds_per_lane=3,attempts=5000,native_steps=1000000000),source=B.SOURCE,protocol='Fresh complete finite sorted syntax and point inventories for every lane. No proof witness, development pickle, previous library, RL policy, finite interpretation or coordinate oracle is read by catalog construction/search.',scope='The planar incidence fragment I.1-I.3 and explicit sort presentation. All outer groundings and clause orientations plus finite atomic equality templates are authored compiled rule types. GCTS/CSP select the proof and earlier references. Existential formulas occur in the foundation but witness elimination is not yet searched. One cold trial per solver/control; no performance advantage claim.',development='An initial producer attempt stopped when the incidence-transfer native checker exceeded 100 million interpreter steps. The complete cold matrix was rerun with a fixed one-billion-step native gate. No development proof or previous result is an input; search limits and grammar were unchanged.')
    (DOCS/'hilbert-incidence-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',round(data['total_seconds'],4),flush=True)
if __name__=='__main__':main()
