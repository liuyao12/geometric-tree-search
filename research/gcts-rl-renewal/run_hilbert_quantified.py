"""Cold matched searches in a declared quantified Hilbert syntax grammar."""
import hashlib,json,time
from pathlib import Path
import hilbert_quantified_tiles as B
import hilbert_incidence_tiles as F
import induction_proof_tiles as T,induction_clusters as H
import audit_hilbert_quantified as A
from audit_serialized_kernel import replay
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
from run_induction_clusters import SOURCES as BASE
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-hilbert-quantified-native-001')
SOURCES=BASE+('euclidean_proof_tiles.py','hilbert_incidence_tiles.py','quantified_proof_rules.py','hilbert_quantified_tiles.py','audit_hilbert_incidence.py','audit_hilbert_quantified.py','test_hilbert_quantified.py','run_hilbert_quantified.py')
CASES=[('line-has-point','line-has-point',10,(),True),('unique-joining-line','unique-joining-line',12,(),False),('line-no-I3','line-has-point',10,('I.3-line-points',),True),('joining-no-I1','unique-joining-line',12,('I.1-existence',),False),('joining-no-I2','unique-joining-line',12,('I.2-uniqueness',),False),('line-short','line-has-point',9,(),True),('joining-short','unique-joining-line',11,(),False)]
def main():
    began=time.perf_counter();pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES};TMP.mkdir(exist_ok=True)
    compile_seconds=tree_native.compile_tool(TMP);code=program();runs=[];problems={}
    for name,base,n,omit,transport in CASES:
        for lane in ('gcts','csp'):
            cold=time.perf_counter();p=B.problem(base);problems[base]=p;c=B.catalog(p,omit,context_transport=transport)
            r=T.search(c,n,support=True,seconds=30,attempt_limit=10000) if lane=='gcts' else H.csp_search(c,n,(),marked=True,seconds=30,attempt_limit=10000)
            row=dict(id=name,lane=lane,length=n,problem=p,catalog=c,result=r,catalog_and_search_seconds=time.perf_counter()-cold)
            if 'decoded' in r:
                request=r['decoded']['request'];primitive=replay(canonical(request))
                if primitive['status']!='accepted':raise ValueError(primitive)
                native=tree_native.check(canonical(request),code,TMP,problem_hash(request),steps=1000000000)
                if native['status']!='accepted':raise ValueError(native)
                row.update(native=native,primitive_proof=primitive['proof'],primitive_lines=primitive['expanded_lines'])
            row['cold_seconds']=time.perf_counter()-cold;runs.append(row)
            print(name,lane,r['status'],r['nodes'],r['base_attempts'],round(row['cold_seconds'],3),flush=True)
            (TMP/'progress.json').write_text(json.dumps(dict(runs=runs),separators=(',',':'))+'\n')
    foundation,metadata=F.foundation();models=A.models(foundation,problems)
    if any(hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pin for n,pin in pins.items()):raise ValueError('source changed during measured run')
    data=dict(version='hilbert-quantified-001',date='2026-10-10',sources=pins,foundation=foundation,foundation_metadata=metadata,problem_pins={n:A.digest(p) for n,p in problems.items()},native_program=code,runs=runs,model_controls=models,compile_seconds=compile_seconds,total_seconds=time.perf_counter()-began,limits=dict(search_seconds=30,attempts=10000,native_steps=1000000000),source=F.SOURCE,
        protocol='Fresh syntax inventory, exact point candidates and zero learned library for each lane. No proof, prior policy, finite model, coordinates or development result is read by search.',
        scope='Authored quantified logic calculus; search discovers actual rule choices and backward references. Planar Hilbert incidence I.1-I.3 only. No rotations/reflections. Complete finite positional translation-only tile envelope, not a uniform four-edge Wang set or a complete first-order prover. No RL in this experiment.',
        development='Development probes calibrated finite lengths and one generic context-transport option: enabled for the line/point target, disabled for the unique-joining target. Early probes exposed redundant implication nesting, now excluded by the declared grammar. The formal matrix uses fixed budgets and a fresh catalog for every lane; no calibration proof is an input. Single cold trials, not a speed claim.')
    (DOCS/'hilbert-quantified-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',round(data['total_seconds'],3),flush=True)
if __name__=='__main__':main()
