"""Cold PA theorem searches, lemma promotion and exact proof compaction."""
import hashlib,json,resource,time
from pathlib import Path
import proof_block_search as search
import peano_problems as problems
from proof_compaction import compact
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-peano')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);theory=problems.theory();library=[];data=dict(theory=theory,initial_library=[],cases=[],
        sources={n:digest(HERE/n) for n in ('peano_problems.py','run_peano.py','proof_block_search.py','proof_compaction.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')},
        configuration=dict(node_limit_per_attempt=5000,term_slack=3,max_inductions=3),
        scope='fresh proof witnesses in an explicit first-order Peano theory; authored statements and induction tactic; no imported witness library or new RL training; bounded contextual equational proposer, not a complete PA prover',
        conformance='semantic proof-proposal adaptation; GCTS base candidates, markings, generations, global scheduling and rollback unchanged')
    code=program();data['compile_seconds']=tree_native.compile_tool(TMP)
    for problem in problems.statements():
        found=search.prove(theory,problem['target'],library,node_limit=5000,slack=3,max_inductions=3)
        row=dict(problem=problem,proposal=found)
        if found['status']=='accepted_proposal':
            c=compact(canonical(found['request']),problem_hash(found['request']))
            if c['status']!='accepted_compaction':raise ValueError('PA compaction '+c['status'])
            row['compaction']=c;request=c['request'];native=tree_native.check(canonical(request),code,TMP,problem_hash(found['request']),steps=100000000)
            row['native']=native
            if native['status']=='accepted':
                # Promotion is from the searched proof, retaining its real
                # discovery provenance; the compact representation is audited
                # separately rather than silently changing the saved library.
                row['promoted']=search.promote(found,library)['name']
            else:row['promoted']=None
        data['cases'].append(row);print(problem['id'],found['status'],found.get('root_lines'),row.get('native',{}).get('status'),flush=True)
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(library=library,total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'peano-theorems-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
