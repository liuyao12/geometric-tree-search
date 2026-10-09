"""Cold generic Horn searches for guarded Euclid-style sample propositions."""
import hashlib,json,resource,time
from pathlib import Path
import euclid_problems as problems
import horn_proof_search as search
from proof_compaction import compact
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-euclid')
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);library=[];theory=problems.theory();code=program()
    files=('euclid_problems.py','horn_proof_search.py','run_euclid.py','proof_block_search.py','proof_compaction.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
    data=dict(theory=theory,initial_library=[],sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files},cases=[],compile_seconds=tree_native.compile_tool(TMP),
        previous_pilot={n:hashlib.sha256((DOCS/n).read_bytes()).hexdigest() for n in ('euclid-pilot-001.json','euclid-pilot-source-001.json','euclid-interface-pilot-001.json','euclid-interface-pilot-source-001.json')},
        configuration=dict(max_rounds=12,max_facts=1500,max_matches=200000),scope='Guarded first-order construction/congruence fragment, with explicit intersection and SAS axioms. Generic Horn/equality saturation; no coordinate oracle, imported proof witnesses or new RL training. Not an implementation of the full E system or all of Euclid.',
        conformance='Semantic proof-proposal adaptation; GCTS point graph, global scheduling, generations, markings and rollback unchanged')
    for p in problems.statements():
        found=search.prove(theory,p['target'],library);row=dict(problem=p,proposal=found)
        if found['status']=='accepted_proposal':
            c=compact(canonical(found['request']),problem_hash(found['request']));row['compaction']=c
            if c['status']!='accepted_compaction':raise ValueError(c['status'])
            native=tree_native.check(canonical(c['request']),code,TMP,problem_hash(found['request']),steps=100000000);row['native']=native
            row['promoted']=search.promote(found,library) if native['status']=='accepted' else None
        data['cases'].append(row);print(p['id'],found['status'],found.get('root_lines'),row.get('native',{}).get('status'),flush=True)
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(library=library,total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'euclid-theorems-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
